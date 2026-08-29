"""능력 라우팅 웹 UI. JSON·multipart 모두 Request 로 직접 읽는다."""

from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from capreq.adapters.base import ExecutionResult
from capreq.adapters.capnet import (
    CapNetAdapter,
    CapNetTaskError,
    CapNetUploadError,
    TERMINAL_STATUSES,
)
from capreq.adapters.static import StaticCatalog
from capreq.config import api_key, ollama_model, ollama_url
from capreq.media import check_media_for_capability
from capreq.ollama import OllamaClient
from capreq.results import summarize_result
from capreq.router import CapabilityRouter

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ChatIn(BaseModel):
    message: str
    execute: bool = False
    dataset_id: str | None = None
    case_id: str | None = None
    # False 면 Task 만 만들고 즉시 돌려준다 — 상태는 GET /api/tasks/{id} 로 본다.
    wait: bool = True


class ChatOut(BaseModel):
    ok: bool
    capability_code: str | None = None
    capability_version: int | None = None
    confidence: float = 0.0
    reason: str = ""
    rejected: bool = False
    execution_ok: bool | None = None
    execution_message: str | None = None
    input_id: str | None = None
    task_id: str | None = None
    task_status: str | None = None
    task_done: bool = False
    result_label: str | None = None
    result: dict[str, Any] | None = None
    model: str = ""


def create_app(
    *,
    core: str | None,
    catalog_json: str | None,
    execute_default: bool = False,
    dataset: str = "eurosat-rgb",
    case_id: str = "ic1-0001",
) -> Any:
    from fastapi import FastAPI, Request, UploadFile
    from fastapi.responses import FileResponse, HTMLResponse

    llm = OllamaClient(base_url=ollama_url(), model=ollama_model())
    capnet: CapNetAdapter | None = None
    if catalog_json:
        catalog: Any = StaticCatalog.from_json_file(catalog_json)
        executor = None
    else:
        if not core:
            raise ValueError("core 또는 catalog_json 필요")
        capnet = CapNetAdapter(core, api_key=api_key())
        catalog = capnet
        executor = capnet

    router = CapabilityRouter(catalog=catalog, llm=llm, executor=executor)
    app = FastAPI(title="capreq", version="0.1.0")

    def _fail(message: str, detail: dict[str, Any] | None = None) -> ExecutionResult:
        return ExecutionResult(ok=False, detail=detail or {}, message=message)

    def _chat_response(
        decision: Any,
        exe: ExecutionResult | None,
        *,
        input_id: str | None = None,
    ) -> dict[str, Any]:
        """실행 결과에서 task 상태·결과 요약을 꺼낸다.

        실패한 실행도 detail 이 task dict 면 상태를 보여 준다 — FAILED 를 침묵으로
        덮으면 「증적이 조회된다」가 거짓이 된다.
        """
        task_id: str | None = None
        status: str | None = None
        summary: dict[str, Any] | None = None
        detail = exe.detail if exe is not None else None
        if isinstance(detail, dict):
            tid = detail.get("id")
            if tid is not None:
                task_id = str(tid)
            st = detail.get("status")
            if st is not None:
                status = str(st)
            # 오류 detail(`{"upload": …}` 등)을 결과로 그리지 않는다.
            if "result_ref" in detail:
                summary = summarize_result(detail) or None
        return ChatOut(
            ok=decision.ok,
            capability_code=decision.capability_code,
            capability_version=decision.capability_version,
            confidence=decision.confidence,
            reason=decision.reason,
            rejected=decision.rejected,
            execution_ok=None if exe is None else exe.ok,
            execution_message=None if exe is None else exe.message,
            input_id=input_id,
            task_id=task_id,
            task_status=status,
            task_done=status in TERMINAL_STATUSES if status else False,
            result_label=(summary or {}).get("label"),
            result=summary,
            model=ollama_model(),
        ).model_dump()

    async def _run_chat(
        *,
        message: str,
        execute: bool,
        dataset_id: str | None,
        case_id_val: str | None,
        file_bytes: bytes | None,
        file_mime: str | None,
        file_name: str | None,
        wait: bool = True,
    ) -> dict[str, Any]:
        prompt = message.strip()
        if file_bytes:
            hint = file_mime or "application/octet-stream"
            name = file_name or "file"
            prompt = (
                f"[첨부: {name} · {hint}]\n{prompt}"
                if prompt
                else f"[첨부: {name} · {hint}] 이 파일에 맞는 능력으로 처리해줘"
            )

        decision = router.route(prompt)
        input_id: str | None = None

        if not execute:
            return _chat_response(decision, None)

        if not decision.ok or decision.capability_code is None:
            return _chat_response(decision, _fail("라우팅 실패 — 실행하지 않음"))

        if capnet is None:
            return _chat_response(decision, _fail("실행은 Core 연결이 필요하다"))

        code = decision.capability_code
        ver = int(decision.capability_version or 1)

        if file_bytes:
            mime = (file_mime or "").split(";")[0].strip()
            err = check_media_for_capability(code, mime)
            if err:
                return _chat_response(decision, _fail(err))
            try:
                input_id = capnet.upload_input(
                    capability_code=code,
                    capability_version=ver,
                    data=file_bytes,
                    media_type=mime,
                )
            except CapNetUploadError as exc:
                return _chat_response(
                    decision,
                    _fail(
                        f"입력 업로드 실패 HTTP {exc.status_code}",
                        {"upload": exc.body},
                    ),
                )
            except httpx.HTTPError as exc:
                return _chat_response(decision, _fail(f"Core 통신 실패: {exc}"))
            target: dict[str, Any] = {"input_id": input_id}
        else:
            # allowlist 데모 경로 (D8′ · 카탈로그 보조).
            target = {
                "dataset_id": dataset_id or dataset,
                "case_id": case_id_val or case_id,
            }

        if wait:
            exe = capnet.execute(
                capability_code=code, capability_version=ver, **target
            )
            return _chat_response(decision, exe, input_id=input_id)

        try:
            created = capnet.create_task(
                capability_code=code, capability_version=ver, **target
            )
        except CapNetTaskError as exc:
            if exc.status_code == 0:
                return _chat_response(decision, _fail(str(exc.body)), input_id=input_id)
            return _chat_response(
                decision,
                _fail(
                    f"Task 생성 실패 HTTP {exc.status_code}",
                    {"status_code": exc.status_code, "body": exc.body},
                ),
                input_id=input_id,
            )
        except httpx.HTTPError as exc:
            return _chat_response(
                decision, _fail(f"Core 통신 실패: {exc}"), input_id=input_id
            )
        return _chat_response(
            decision,
            ExecutionResult(
                ok=True,
                detail=created,
                message=f"제출됨 status={created.get('status')}",
            ),
            input_id=input_id,
        )

    @app.get("/", response_class=HTMLResponse)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "chat.html")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        caps = catalog.list_capabilities()
        return {
            "ok": True,
            "model": ollama_model(),
            "capabilities": len(caps),
            "executor": executor is not None,
            "input_upload": capnet is not None,
        }

    @app.get("/api/capabilities")
    def capabilities() -> dict[str, Any]:
        items = [
            {
                "code": c.code,
                "version": c.version,
                "name": c.name,
                "description": c.description,
            }
            for c in catalog.list_capabilities()
        ]
        return {"items": items}

    @app.get("/api/tasks/{task_id}")
    def task_state(task_id: str) -> dict[str, Any]:
        """Task 상태 폴링. Core 의 응답을 요약해 옮길 뿐 새로 판정하지 않는다."""
        if capnet is None:
            return {"ok": False, "error": "Core 미연결", "task_id": task_id}
        try:
            got = capnet.get_task(task_id)
        except CapNetTaskError as exc:
            return {
                "ok": False,
                "task_id": task_id,
                "error": f"Task 조회 실패 HTTP {exc.status_code}",
                "detail": exc.body,
            }
        except httpx.HTTPError as exc:
            return {"ok": False, "task_id": task_id, "error": f"Core 통신 실패: {exc}"}
        status = got.get("status")
        status = str(status) if status is not None else None
        summary = summarize_result(got) or None
        assignment = got.get("assignment") if isinstance(got.get("assignment"), dict) else None
        return {
            "ok": True,
            "task_id": task_id,
            "status": status,
            "done": status in TERMINAL_STATUSES if status else False,
            "result": summary,
            "result_label": (summary or {}).get("label"),
            # 증적 — 어느 Node·어느 Agent 로 갔는지. Core 가 준 값 그대로다.
            "assignment": (
                {
                    "id": str(assignment.get("id")),
                    "status": assignment.get("status"),
                    "node_id": str(assignment.get("node_id")) if assignment.get("node_id") else None,
                    "agent_id": str(assignment.get("agent_id")) if assignment.get("agent_id") else None,
                    "node_trust_domain": assignment.get("node_trust_domain"),
                    "capability_tier": assignment.get("capability_tier"),
                }
                if assignment
                else None
            ),
        }

    @app.post("/api/chat")
    async def chat(request: Request) -> dict[str, Any]:
        ct = (request.headers.get("content-type") or "").lower()
        if "multipart/form-data" in ct:
            form = await request.form()
            message = str(form.get("message") or "")
            execute_raw = form.get("execute")
            do_exec = execute_default
            if execute_raw is not None:
                do_exec = str(execute_raw).lower() in ("1", "true", "on", "yes")
            ds = form.get("dataset_id")
            cs = form.get("case_id")
            wait_raw = form.get("wait")
            wait = True
            if wait_raw is not None:
                wait = str(wait_raw).lower() in ("1", "true", "on", "yes")
            up = form.get("file")
            file_bytes: bytes | None = None
            file_mime: str | None = None
            file_name: str | None = None
            if isinstance(up, UploadFile) and up.filename:
                file_bytes = await up.read()
                file_mime = up.content_type
                file_name = up.filename
            return await _run_chat(
                message=message,
                execute=do_exec,
                dataset_id=str(ds) if ds else None,
                case_id_val=str(cs) if cs else None,
                file_bytes=file_bytes,
                file_mime=file_mime,
                file_name=file_name,
                wait=wait,
            )

        try:
            raw = await request.json()
        except Exception:
            return ChatOut(
                ok=False, reason="JSON 또는 multipart 본문 필요", model=ollama_model()
            ).model_dump()
        payload = ChatIn.model_validate(raw if isinstance(raw, dict) else {})
        do_exec = payload.execute or execute_default
        return await _run_chat(
            message=payload.message,
            execute=do_exec,
            dataset_id=payload.dataset_id,
            case_id_val=payload.case_id,
            file_bytes=None,
            file_mime=None,
            file_name=None,
            wait=payload.wait,
        )

    return app
