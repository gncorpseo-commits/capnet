"""능력 라우팅 웹 UI. JSON 본문은 Request 로 직접 읽는다."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from capreq.adapters.capnet import CapNetAdapter
from capreq.adapters.static import StaticCatalog
from capreq.config import api_key, ollama_model, ollama_url
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
    model: str = ""


def create_app(
    *,
    core: str | None,
    catalog_json: str | None,
    execute_default: bool = False,
    dataset: str = "eurosat-rgb",
    case_id: str = "ic1-0001",
) -> Any:
    from fastapi import FastAPI, Request
    from fastapi.responses import FileResponse, HTMLResponse

    llm = OllamaClient(base_url=ollama_url(), model=ollama_model())
    if catalog_json:
        catalog: Any = StaticCatalog.from_json_file(catalog_json)
        executor = None
    else:
        if not core:
            raise ValueError("core 또는 catalog_json 필요")
        adapter = CapNetAdapter(core, api_key=api_key())
        catalog = adapter
        executor = adapter

    router = CapabilityRouter(catalog=catalog, llm=llm, executor=executor)
    app = FastAPI(title="capreq", version="0.1.0")

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
        try:
            raw = await request.json()
        except Exception:
            return ChatOut(
                ok=False, reason="JSON 본문 필요", model=ollama_model()
            ).model_dump()
        payload = ChatIn.model_validate(raw if isinstance(raw, dict) else {})
        do_exec = payload.execute or execute_default
        decision, exe = router.route_and_maybe_execute(
            payload.message,
            dataset_id=payload.dataset_id or dataset,
            case_id=payload.case_id or case_id,
            execute=do_exec,
        )
        return ChatOut(
            ok=decision.ok,
            capability_code=decision.capability_code,
            capability_version=decision.capability_version,
            confidence=decision.confidence,
            reason=decision.reason,
            rejected=decision.rejected,
            execution_ok=None if exe is None else exe.ok,
            execution_message=None if exe is None else exe.message,
            model=ollama_model(),
        ).model_dump()

    return app
