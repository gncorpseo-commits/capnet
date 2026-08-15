"""Node 실행 — Core가 준 lease만 처리. 큐 pull 금지."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import threading
import tempfile
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
# 받은 입력을 잠깐 두는 곳. 실행이 끝나면 지운다 — Node 에 남기지 않는다.
INPUT_TMP_DIR = os.environ.get("NODE_INPUT_TMP_DIR") or None

# 이 Node의 신원. Core가 배정한 lease만 가져오고 실행한다.
NODE_ID = os.environ.get("NODE_ID") or None

# Core 가 발급한 증서 (P2-4). 있으면 모든 Core 호출에 실어 보낸다.
# 없어도 돈다 — Core 의 REQUIRE_NODE_CREDENTIAL 이 꺼져 있으면 통과한다 (데모 경로).
# 파일 경로로 주는 편이 낫다: 프로세스 목록·docker inspect 에 시크릿이 노출되지 않는다.
NODE_CREDENTIAL_FILE = os.environ.get("NODE_CREDENTIAL_FILE") or None


def _load_credential() -> str | None:
    if NODE_CREDENTIAL_FILE and os.path.isfile(NODE_CREDENTIAL_FILE):
        return open(NODE_CREDENTIAL_FILE, encoding="utf-8").read().strip() or None
    return os.environ.get("NODE_CREDENTIAL") or None


NODE_CREDENTIAL = _load_credential()


def _core_headers() -> dict[str, str]:
    """Core 로 보내는 공통 헤더. 증서가 있으면 신원을 함께 보낸다."""
    headers = {"content-type": "application/json"}
    if NODE_CREDENTIAL:
        headers["Authorization"] = f"CapNet-Node {NODE_CREDENTIAL}"
    return headers
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


def _input_meta(input_ref: str | None) -> tuple[str, str] | None:
    """Core 가 받아 둔 입력이면 (inputId, inputSha). 없으면 None → 데모 경로.

    이 갈림길이 D22 의 「해시가 있으면 pull, 없으면 기존 경로」다.
    """
    if not input_ref:
        return None
    try:
        payload = json.loads(input_ref)
    except json.JSONDecodeError:
        return None
    iid, sha = payload.get("inputId"), payload.get("inputSha")
    return (str(iid), str(sha)) if iid and sha else None


def _fetch_input(input_id: str, expected_sha: str) -> str:
    """Core 에서 입력 바이트를 받아 임시 파일로 떨군다. 해시가 다르면 거부.

    Core 가 준 것과 내가 받은 것이 같다는 것을 **Node 가 직접 확인한다.** 전송 중
    바뀐 바이트로 추론하면 증적의 sha 와 실행한 바이트가 달라진다.
    """
    if not NODE_ID:
        raise HTTPException(status_code=500, detail="NODE_ID 가 없다 — 입력을 받을 수 없다")
    url = f"{CORE_URL}/v1/internal/inputs/{input_id}/bytes?node_id={NODE_ID}"
    req = urllib.request.Request(url, headers=_core_headers(), method="GET")
    digest = hashlib.sha256()
    fd, tmp = tempfile.mkstemp(prefix="capnet-input-", dir=INPUT_TMP_DIR)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, os.fdopen(fd, "wb") as fh:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                fh.write(chunk)
        got = digest.hexdigest()
        if got != expected_sha:
            raise HTTPException(
                status_code=422,
                detail=f"input sha256 mismatch: got={got[:16]}… want={expected_sha[:16]}…",
            )
        return tmp
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _report_failure(assignment_id: uuid.UUID, reason: str) -> None:
    """실행 실패를 Core 에 보고한다 (0015).

    보고하지 않으면 실패가 **lease 만료(60초)로만** 드러나고, 그 동안 같은 배정을 계속
    재시도한다 — 로그에만 쌓이고 증적에는 없다. 실측으로 채널 불일치 38건이 그렇게 쌓였다.

    보고 자체가 실패해도 삼킨다 — 그때는 종전처럼 lease 만료로 회수된다.
    """
    if not NODE_ID:
        return
    url = f"{CORE_URL}/v1/internal/assignments/{assignment_id}/fail"
    body = json.dumps({"nodeId": NODE_ID, "reason": reason[:500]}).encode()
    req = urllib.request.Request(url, data=body, headers=_core_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as exc:
        print(f"node: failure report failed: {exc}", flush=True)


def _post_complete(assignment_id: uuid.UUID, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{CORE_URL}/v1/internal/assignments/{assignment_id}/complete"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers=_core_headers(),
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
        entry = {
            "path": path,
            "sha256": _file_sha256(path),
            "placeholder": _is_placeholder(path),
        }
        # 학습 시 기록된 아키텍처. **Node 의 증언**이지 Core 의 판정이 아니다 —
        # legacy Agent 의 arch 백필에 쓴다 (scripts/backfill_agent_arch.sh).
        try:
            from app.infer import _arch_for_weights

            entry["arch"] = _arch_for_weights(path)
        except Exception:
            entry["arch"] = None
        files.append(entry)
    default_exists = os.path.isfile(WEIGHTS_PATH)
    return {
        "ok": default_exists or bool(files),
        "node_id": NODE_ID,
        # 증서 **보유 여부만** 알린다. 값도 prefix 도 내보내지 않는다.
        "credential_present": bool(NODE_CREDENTIAL),
        "weights_path": WEIGHTS_PATH,
        "weights_sha256": _file_sha256(WEIGHTS_PATH) if default_exists else None,
        "weights": files,
    }


def _send_heartbeat(availability: str, metrics: dict[str, Any] | None = None) -> None:
    """살아 있음을 Core에 알린다. 실패해도 조용히 넘어간다 — 다음 주기에 다시 보낸다."""
    if not NODE_ID:
        return
    url = f"{CORE_URL}/v1/internal/nodes/{NODE_ID}/heartbeat"
    req = urllib.request.Request(
        url,
        data=json.dumps({"availability": availability, "metrics": metrics or {}}).encode(),
        headers=_core_headers(),
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5).close()
    except Exception:
        pass


def _fetch_my_assignments() -> list[dict[str, Any]]:
    """Core에서 내게 배정된 살아 있는 lease만 가져온다. 큐를 뒤지지 않는다."""
    if not NODE_ID:
        return []
    url = f"{CORE_URL}/v1/internal/nodes/{NODE_ID}/assignments"
    req = urllib.request.Request(url, headers=_core_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode()).get("assignments", [])
    except Exception:
        return []


def _my_assignment(assignment_id: uuid.UUID) -> dict[str, Any] | None:
    """Core가 이 Node에 배정한 lease면 **그 행을 그대로** 돌려준다.

    이게 없으면 Node에 네트워크로 닿는 누구나 추론을 시킬 수 있다.
    Core의 도메인·티어 FK는 assignment 기록을 막지만 Node 직접 호출은 막지 못한다.

    불린이 아니라 행을 돌려주는 이유: 이 경로도 `arch`·`max_params`·`preprocess` 를
    **Core 가 말한 값**으로 써야 한다 (I1). 전에는 확인만 하고 버려서, 수동 실행이
    로컬 meta·기본값으로 떨어지고 있었다.
    """
    for a in _fetch_my_assignments():
        if str(a.get("id")) == str(assignment_id):
            return a
    return None


def _modality_of(arch: str | None) -> str:
    """arch → 모달리티. 정본은 `ARCH_MODALITY` 다 (단계 5).

    모르면 `image` — 종전 동작이고, legacy Agent(arch NULL)도 그쪽으로 간다.
    """
    if not arch:
        return "image"
    from app.tiny_cnn import ARCH_MODALITY

    return ARCH_MODALITY.get(arch, "image")


def _run(
    assignment_id: uuid.UUID,
    weights_sha256: str,
    input_ref: str | None,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """배정 1건 실행.

    `arch` 는 **Core 가 말한 값**이다 (I1). 로컬 meta 로 정하면 게이트가 승인한 것과
    실행한 것이 같다는 보장이 없다. Core 가 모르면(legacy Agent) None 이고, 그때만 로컬로 떨어진다.

    `preprocess` 도 같다 (0014). 계약이 선언한 전처리로 돌아야 **계약 검증 때 통과한 그것**과
    실행이 같아진다. 없으면 종전 기본값(32×32 RGB)으로 떨어진다.
    """
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

        # 어느 실행기로 갈지는 **arch** 가 정한다 (단계 5). Core 가 말한 값이고
        # 게이트가 그 값으로 승인했으므로, 「승인한 것과 실행한 것이 같다」를 지킨다 (I1).
        modality = _modality_of(arch)

        # D22: Core 가 받아 둔 입력이 있으면 그 바이트로 돈다. 없으면 종전 데모 경로
        # (caseId → Node 로컬 골든셋)로 그대로 떨어진다.
        meta = _input_meta(input_ref)
        fetched: str | None = None
        if meta is not None:
            fetched = _fetch_input(*meta)
            image_path = fetched
        elif modality == "text":
            # 텍스트에는 로컬 골든셋 폴백이 없다 — 입력은 Core 중개로만 온다 (D8′).
            raise HTTPException(
                status_code=400,
                detail="text 실행에는 Core 가 중개한 입력이 필요하다 (inputSha)",
            )
        else:
            cid = _case_id(input_ref)
            if not cid:
                raise HTTPException(status_code=400, detail="caseId required for scratch infer")
            image = case_path(CASES_DIR, cid)
            if not image.is_file():
                raise HTTPException(status_code=404, detail=f"case image missing: {image}")
            image_path = str(image)
        from app.infer import ResourceLimitExceeded

        try:
            if modality == "text":
                from app.infer_text import TextResourceLimitExceeded, predict_text

                try:
                    label, confidence = predict_text(
                        path, image_path, arch=arch, max_params=max_params,
                        preprocess=preprocess,
                    )
                except TextResourceLimitExceeded as exc:
                    raise ResourceLimitExceeded(str(exc)) from exc
            else:
                label, confidence = predict_image(
                    path, image_path, arch=arch, max_params=max_params,
                    preprocess=preprocess,
                )
        except ResourceLimitExceeded as exc:
            # 조용히 도는 것보다 터뜨리는 편이 낫다 — Core 가 FAILED 로 기록한다.
            raise HTTPException(status_code=422, detail=f"resource limit: {exc}") from exc
        except ValueError as exc:
            # allowlist 밖 arch. build_model 이 던진다.
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        finally:
            # 받은 입력은 Node 에 남기지 않는다 (D22 · 바이트는 휘발성).
            if fetched:
                with contextlib.suppress(OSError):
                    os.unlink(fetched)
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
    """수동 실행 경로. Core가 이 Node에 배정한 lease만 허용한다.

    **닫힌 실패.** NODE_ID 가 없으면 배정 여부를 확인할 수단이 없으므로 실행하지 않는다.
    이전에는 `if NODE_ID and ...` 여서 NODE_ID 미설정 노드가 무방비였다.
    """
    if not NODE_ID:
        raise HTTPException(
            status_code=503,
            detail="NODE_ID 미설정 — 배정 확인 불가. 실행을 거부한다 (fail closed)",
        )
    mine = _my_assignment(body.id)
    if mine is None:
        raise HTTPException(
            status_code=403,
            detail="assignment not leased to this node (Core가 배정하지 않았다)",
        )
    # 폴링 경로와 같은 값을 쓴다 — 배정마다 다른 계약을 탈 수 있다.
    return _run(
        body.id, body.weights_sha256, body.input_ref,
        arch=mine.get("arch"),
        max_params=mine.get("max_params"),
        preprocess=mine.get("preprocess"),
    )


def _poll_loop() -> None:
    while True:
        try:
            mine = _fetch_my_assignments()
            # 일이 있으면 BUSY, 없으면 AVAILABLE. Core 는 이걸 보고 배정한다.
            _send_heartbeat("BUSY" if mine else "AVAILABLE", {"active": len(mine)})
            for a in mine:
                try:
                    out = _run(
                        uuid.UUID(str(a["id"])),
                        a["weights_sha256"],
                        a.get("input_ref"),
                        arch=a.get("arch"),
                        max_params=a.get("max_params"),
                        preprocess=a.get("preprocess"),
                    )
                    print(f"node: ran assignment={a['id']} label={out.get('label')}", flush=True)
                except Exception as exc:  # 한 건 실패가 루프를 죽이지 않는다
                    print(f"node: assignment {a.get('id')} failed: {exc}", flush=True)
                    # **Core 에 알린다.** 안 알리면 lease 만료까지 같은 배정을 계속 잡는다.
                    with contextlib.suppress(Exception):
                        _report_failure(uuid.UUID(str(a["id"])), f"{type(exc).__name__}: {exc}")
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
