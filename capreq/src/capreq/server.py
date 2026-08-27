"""능력 라우팅 웹 UI. JSON·multipart 모두 Request 로 직접 읽는다."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from capreq.adapters.capnet import CapNetAdapter, CapNetUploadError
from capreq.adapters.static import StaticCatalog
from capreq.config import api_key, ollama_model, ollama_url
from capreq.media import check_media_for_capability
from capreq.ollama import OllamaClient
from capreq.router import CapabilityRouter

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ChatIn(BaseModel):
    message: str
    execute: bool = False
    dataset_id: str | None = None
    case_id: str | None = None


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
    result_label: str | None = None
    model: str = ""


def _result_label(detail: dict[str, Any]) -> str | None:
    ref = detail.get("result_ref")
    if isinstance(ref, str):
        import json

        try:
            ref = json.loads(ref)
        except json.JSONDecodeError:
            return None
    if isinstance(ref, dict):
        lab = ref.get("label")
        return str(lab) if lab is not None else None
    return None


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

    def _chat_response(
        decision: Any,
        exe: Any | None,
        *,
        input_id: str | None = None,
    ) -> dict[str, Any]:
        task_id: str | None = None
        label: str | None = None
        if exe is not None and exe.ok and isinstance(exe.detail, dict):
            task_id = exe.detail.get("id")
            if task_id is not None:
                task_id = str(task_id)
            label = _result_label(exe.detail)
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
            result_label=label,
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
        do_exec = execute
        input_id: str | None = None

        if not do_exec:
            return _chat_response(decision, None)

        if not decision.ok or decision.capability_code is None:
            return _chat_response(
                decision,
                type(
                    "R",
                    (),
                    {"ok": False, "detail": {}, "message": "라우팅 실패 — 실행하지 않음"},
                )(),
            )

        if file_bytes:
            if capnet is None:
                return _chat_response(
                    decision,
                    type(
                        "R",
                        (),
                        {"ok": False, "detail": {}, "message": "파일 실행은 Core 연결 필요"},
                    )(),
                )
            code = decision.capability_code
            ver = int(decision.capability_version or 1)
            mime = (file_mime or "").split(";")[0].strip()
            err = check_media_for_capability(code, mime)
            if err:
                return _chat_response(
                    decision,
                    type("R", (), {"ok": False, "detail": {}, "message": err})(),
                )
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
                    type(
                        "R",
                        (),
                        {
                            "ok": False,
                            "detail": {"upload": exc.body},
                            "message": f"입력 업로드 실패 HTTP {exc.status_code}",
                        },
                    )(),
                )
            exe = capnet.execute(
                capability_code=code,
                capability_version=ver,
                input_id=input_id,
            )
            return _chat_response(decision, exe, input_id=input_id)

        _, exe = router.route_and_maybe_execute(
            prompt,
            dataset_id=dataset_id or dataset,
            case_id=case_id_val or case_id,
            execute=True,
        )
        return _chat_response(decision, exe)

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
        )

    return app
