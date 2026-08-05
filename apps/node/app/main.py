"""dummy Node — lease 페이로드를 받아 safetensors만 로드하고 고정 라벨을 보고한다.

EuroSAT scratch 학습이 아니다. 품질 주장이 아니라 claim→로드→보고 E2E.
Node는 큐를 claim하지 않는다. Core가 고른 lease만 실행한다.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from safetensors import safe_open

app = FastAPI(title="CapNet dummy Node", version="0.1.0-dummy")

CORE_URL = os.environ.get("CORE_URL", "http://127.0.0.1:8000").rstrip("/")
WEIGHTS_PATH = os.environ.get("WEIGHTS_PATH", "/weights/placeholder.safetensors")

# closed-set 계약 라벨. dummy는 caseId 해시로 고를 뿐 분류기가 아니다.
_LABELS = (
    "annual_crop",
    "forest",
    "herbaceous_vegetation",
    "highway",
    "industrial",
    "pasture",
    "permanent_crop",
    "residential",
    "river",
    "sea_lake",
)


class ExecuteBody(BaseModel):
    id: uuid.UUID
    weights_sha256: str
    input_ref: str | None = None


def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_safetensors(path: str) -> list[str]:
    keys: list[str] = []
    with safe_open(path, framework="np") as fh:
        keys = list(fh.keys())
        if not keys:
            raise ValueError("empty safetensors")
        _ = fh.get_tensor(keys[0])
    return keys


def _dummy_label(input_ref: str | None) -> str:
    raw = input_ref or ""
    try:
        payload = json.loads(raw)
        case_id = str(payload.get("caseId") or raw)
    except json.JSONDecodeError:
        case_id = raw
    idx = int(hashlib.sha256(case_id.encode()).hexdigest(), 16) % len(_LABELS)
    return _LABELS[idx]


def _post_complete(assignment_id: uuid.UUID, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{CORE_URL}/v1/internal/assignments/{assignment_id}/complete"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise HTTPException(status_code=502, detail=f"core complete {exc.code}: {detail}") from exc


@app.get("/health")
def health() -> dict[str, Any]:
    exists = os.path.isfile(WEIGHTS_PATH)
    digest = _file_sha256(WEIGHTS_PATH) if exists else None
    return {"ok": exists, "weights_path": WEIGHTS_PATH, "weights_sha256": digest}


@app.post("/v1/execute")
def execute(body: ExecuteBody) -> dict[str, Any]:
    if not os.path.isfile(WEIGHTS_PATH):
        raise HTTPException(status_code=500, detail="placeholder weights missing")

    digest = _file_sha256(WEIGHTS_PATH)
    if digest != body.weights_sha256:
        raise HTTPException(
            status_code=409,
            detail="weights_sha256 mismatch (file vs lease)",
        )

    started = time.perf_counter()
    try:
        keys = _load_safetensors(WEIGHTS_PATH)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"safetensors load failed: {exc}") from exc

    label = _dummy_label(body.input_ref)
    duration_ms = int((time.perf_counter() - started) * 1000)

    reported = _post_complete(
        body.id,
        {
            "weights_sha256": digest,
            "label": label,
            "confidence": 0.0,
            "dummy": True,
            "duration_ms": duration_ms,
        },
    )
    return {
        "assignment_id": str(body.id),
        "label": label,
        "dummy": True,
        "tensor_keys": keys,
        "weights_sha256": digest,
        "core": reported,
    }
