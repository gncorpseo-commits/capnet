"""Gemma 일반 대화 챗봇 — CapNet/라우팅 없음. 대화만 테스트."""

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from capreq import __version__
from capreq.config import ollama_url
from capreq.ollama import OllamaClient, OllamaError

STATIC_DIR = Path(__file__).resolve().parent / "static"

_SYSTEM = (
    "당신은 친절한 한국어 비서입니다. 짧고 자연스럽게 대화하세요. "
    "모르는 것은 모른다고 말하세요."
)

DEFAULT_GEMMA = "gemma2:2b"


class TurnIn(BaseModel):
    message: str = ""
    reset: bool = False


class TurnOut(BaseModel):
    ok: bool
    reply: str = ""
    error: str = ""
    model: str = ""
    turns: int = 0


def gemma_model() -> str:
    return os.environ.get("CAPREQ_GEMMA_MODEL") or os.environ.get(
        "CAPREQ_OLLAMA_MODEL", DEFAULT_GEMMA
    )


def create_gemma_app(*, model: str | None = None) -> Any:
    from fastapi import FastAPI, Request
    from fastapi.responses import FileResponse, HTMLResponse

    use_model = model or gemma_model()
    llm = OllamaClient(
        base_url=ollama_url(),
        model=use_model,
        temperature=0.7,
    )
    history: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM}]

    app = FastAPI(title="capreq-gemma-chat", version=__version__)

    @app.get("/", response_class=HTMLResponse)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "gemma_chat.html")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "model": use_model, "mode": "gemma-conversation"}

    @app.post("/api/chat")
    async def chat(request: Request) -> dict[str, Any]:
        # Annotated/Body 가 future annotations 와 겹치면 query 로 오인된다.
        # JSON 본문을 직접 읽는다.
        try:
            raw = await request.json()
        except Exception:
            return TurnOut(
                ok=False, error="JSON 본문 필요", model=use_model, turns=len(history)
            ).model_dump()
        payload = TurnIn.model_validate(raw if isinstance(raw, dict) else {})

        if payload.reset:
            history.clear()
            history.append({"role": "system", "content": _SYSTEM})
            if not payload.message.strip():
                return TurnOut(
                    ok=True,
                    reply="대화를 초기화했습니다.",
                    model=use_model,
                    turns=len(history),
                ).model_dump()

        text = payload.message.strip()
        if not text:
            return TurnOut(
                ok=False, error="빈 메시지", model=use_model, turns=len(history)
            ).model_dump()

        history.append({"role": "user", "content": text})
        try:
            reply = llm.chat_messages(history, json_format=False, temperature=0.7)
        except OllamaError as exc:
            history.pop()
            return TurnOut(
                ok=False, error=str(exc), model=use_model, turns=len(history)
            ).model_dump()

        history.append({"role": "assistant", "content": reply})
        if len(history) > 41:
            history[:] = [history[0]] + history[-40:]
        return TurnOut(
            ok=True, reply=reply, model=use_model, turns=len(history)
        ).model_dump()

    return app
