from __future__ import annotations

import json
from typing import Any

import httpx


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    """Ollama /api/chat 래퍼."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:3b",
        *,
        timeout: float = 180.0,
        temperature: float = 0.1,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.temperature = temperature

    def chat(self, *, system: str, user: str) -> str:
        """라우팅용 — JSON format 강제."""
        return self.chat_messages(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            json_format=True,
        )

    def chat_messages(
        self,
        messages: list[dict[str, str]],
        *,
        json_format: bool = False,
        temperature: float | None = None,
    ) -> str:
        """일반 대화(멀티턴) 또는 JSON 라우팅."""
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "options": {
                "temperature": self.temperature if temperature is None else temperature
            },
            "messages": messages,
        }
        if json_format:
            payload["format"] = "json"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(f"{self.base_url}/api/chat", json=payload)
                if r.status_code >= 400:
                    raise OllamaError(
                        f"Ollama HTTP {r.status_code}: {r.text[:300]} "
                        f"(model={self.model!r} — ollama pull 했는지 확인)"
                    )
                data = r.json()
        except httpx.ConnectError as exc:
            raise OllamaError(
                f"Ollama 에 연결할 수 없다 ({self.base_url}). "
                "`ollama serve` 와 모델 pull 을 확인한다."
            ) from exc
        msg = (data.get("message") or {}).get("content") or ""
        if not msg:
            raise OllamaError(f"빈 응답: {json.dumps(data)[:200]}")
        return msg
