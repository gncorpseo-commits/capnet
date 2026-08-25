from __future__ import annotations

import os


def ollama_url() -> str:
    return os.environ.get("CAPREQ_OLLAMA_URL", "http://127.0.0.1:11434")


def ollama_model() -> str:
    # Qwen2.5 = 기본 (한국어·JSON). Gemma 는 CAPREQ_OLLAMA_MODEL=gemma2:2b
    return os.environ.get("CAPREQ_OLLAMA_MODEL", "qwen2.5:3b")


def core_url() -> str:
    return os.environ.get("CAPREQ_CORE_URL", "http://127.0.0.1:8000")


def api_key() -> str | None:
    return os.environ.get("CAPREQ_API_KEY") or None
