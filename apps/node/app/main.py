"""Node 실행 — Core가 준 lease만 처리. 큐 pull 금지."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from safetensors import safe_open

app = FastAPI(title="CapNet Node", version="0.2.0")

CORE_URL = os.environ.get("CORE_URL", "http://127.0.0.1:8000").rstrip("/")
WEIGHTS_DIR = os.environ.get("WEIGHTS_DIR", "/weights")
WEIGHTS_PATH = os.environ.get("WEIGHTS_PATH", os.path.join(WEIGHTS_DIR, "placeholder.safetensors"))
CASES_DIR = os.environ.get("GOLDEN_CASES_DIR", "/golden/cases")

# 이 Node의 신원. Core가 배정한 lease만 가져오고 실행한다.
NODE_ID = os.environ.get("NODE_ID") or None
POLL_ENABLED = os.environ.get("NODE_POLL", "1") != "0"
POLL_INTERVAL_S = float(os.environ.get("NODE_POLL_INTERVAL_S", "1.0"))

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


def _list_weight_files() -> list[str]:
    if not os.path.isdir(WEIGHTS_DIR):
        return []
    return [
        os.path.join(WEIGHTS_DIR, name)
        for name in sorted(os.listdir(WEIGHTS_DIR))
        if name.endswith(".safetensors")
    ]


def _resolve_weights(digest: str) -> str:
    candidates = _list_weight_files()
    if os.path.isfile(WEIGHTS_PATH):
        candidates = [WEIGHTS_PATH] + [p for p in candidates if p != WEIGHTS_PATH]
    for path in candidates:
        if _file_sha256(path) == digest:
            return path
    raise HTTPException(status_code=409, detail="weights_sha256 not found on node")


def _is_placeholder(path: str) -> bool:
    return os.path.basename(path).startswith("placeholder")


def _dummy_label(input_ref: str | None) -> str:
    raw = input_ref or ""
    try:
        payload = json.loads(raw)
        case_id = str(payload.get("caseId") or raw)
    except json.JSONDecodeError:
        case_id = raw
    idx = int(hashlib.sha256(case_id.encode()).hexdigest(), 16) % len(_LABELS)
    return _LABELS[idx]


def _case_id(input_ref: str | None) -> str | None:
    if not input_ref:
        return None
    try:
        return json.loads(input_ref).get("caseId")
    except json.JSONDecodeError:
        return None


def _post_complete(assignment_id: uuid.UUID, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{CORE_URL}/v1/internal/assignments/{assignment_id}/complete"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise HTTPException(status_code=502, detail=f"core complete {exc.code}: {detail}") from exc


@app.get("/health")
def health() -> dict[str, Any]:
    files = []
    for path in _list_weight_files():
        files.append(
            {
                "path": path,
                "sha256": _file_sha256(path),
                "placeholder": _is_placeholder(path),
            }
        )
    default_exists = os.path.isfile(WEIGHTS_PATH)
    return {
        "ok": default_exists or bool(files),
        "weights_path": WEIGHTS_PATH,
        "weights_sha256": _file_sha256(WEIGHTS_PATH) if default_exists else None,
        "weights": files,
    }


def _fetch_my_assignments() -> list[dict[str, Any]]:
    """Core에서 내게 배정된 살아 있는 lease만 가져온다. 큐를 뒤지지 않는다."""
    if not NODE_ID:
        return []
    url = f"{CORE_URL}/v1/internal/nodes/{NODE_ID}/assignments"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode()).get("assignments", [])
    except Exception:
        return []


def _is_mine(assignment_id: uuid.UUID) -> bool:
    """Core가 이 Node에 배정한 lease인지 확인한다.

    이게 없으면 Node에 네트워크로 닿는 누구나 추론을 시킬 수 있다.
    Core의 도메인·티어 FK는 assignment 기록을 막지만 Node 직접 호출은 막지 못한다.
    """
    return any(str(a.get("id")) == str(assignment_id) for a in _fetch_my_assignments())


def _run(assignment_id: uuid.UUID, weights_sha256: str, input_ref: str | None) -> dict[str, Any]:
    path = _resolve_weights(weights_sha256)
    dummy = _is_placeholder(path)
    started = time.perf_counter()
    if dummy:
        with safe_open(path, framework="np") as fh:
            keys = list(fh.keys())
        label = _dummy_label(input_ref)
        confidence = 0.0
    else:
        from app.infer import case_path, predict_image

        cid = _case_id(input_ref)
        if not cid:
            raise HTTPException(status_code=400, detail="caseId required for scratch infer")
        image = case_path(CASES_DIR, cid)
        if not image.is_file():
            raise HTTPException(status_code=404, detail=f"case image missing: {image}")
        label, confidence = predict_image(path, str(image))
        keys = ["scratch"]

    duration_ms = int((time.perf_counter() - started) * 1000)
    reported = _post_complete(
        assignment_id,
        {
            "weights_sha256": weights_sha256,
            "label": label,
            "confidence": confidence,
            "dummy": dummy,
            "duration_ms": duration_ms,
        },
    )
    return {
        "assignment_id": str(assignment_id),
        "label": label,
        "dummy": dummy,
        "tensor_keys": keys,
        "weights_sha256": weights_sha256,
        "core": reported,
    }


@app.post("/v1/execute")
def execute(body: ExecuteBody) -> dict[str, Any]:
    """수동 실행 경로. Core가 이 Node에 배정한 lease만 허용한다."""
    if NODE_ID and not _is_mine(body.id):
        raise HTTPException(
            status_code=403,
            detail="assignment not leased to this node (Core가 배정하지 않았다)",
        )
    return _run(body.id, body.weights_sha256, body.input_ref)


def _poll_loop() -> None:
    while True:
        try:
            for a in _fetch_my_assignments():
                try:
                    out = _run(uuid.UUID(str(a["id"])), a["weights_sha256"], a.get("input_ref"))
                    print(f"node: ran assignment={a['id']} label={out.get('label')}", flush=True)
                except Exception as exc:  # 한 건 실패가 루프를 죽이지 않는다
                    print(f"node: assignment {a.get('id')} failed: {exc}", flush=True)
        except Exception as exc:
            print(f"node: poll error: {exc}", flush=True)
        time.sleep(POLL_INTERVAL_S)


@app.on_event("startup")
def _start_poll() -> None:
    if not (POLL_ENABLED and NODE_ID):
        print(f"node: poll disabled (NODE_ID={NODE_ID} POLL={POLL_ENABLED})", flush=True)
        return
    print(f"node: poll started node_id={NODE_ID} interval={POLL_INTERVAL_S}s", flush=True)
    threading.Thread(target=_poll_loop, name="node-poll", daemon=True).start()
