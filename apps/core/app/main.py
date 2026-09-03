import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import psycopg
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.allowlist import ALLOWED_DATASET_IDS, assert_dataset_id
from app.apikey import (
    ApiKeyError,
    Forbidden,
    list_key_status,
    looks_like_api_key,
    verify_key,
)
from app.arch import create_arch, list_arches
from app.capability import (
    create_capability,
    get_capability,
    list_capabilities,
    update_capability_description,
)
from app.claim import claim_next, fail_assignment, fail_exhausted_tasks, reclaim_expired
from app.complete import (
    complete_assignment,
    lease_detail,
    node_assignments,
    try_audit_succeeded,
)
from app.const import SEED_ADMIN_ID
from app.credential import (
    CredentialError,
    issue_credential,
    list_credential_status,
    revoke_credential,
    verify_credential,
)
from app.db import get_conn, pool_stats
from app.inputs import (
    InputRejected,
    get_sample,
    is_gate_runner,
    set_sample,
    InputTooLarge,
    assert_media_type,
    blob_path,
    load_capability,
    mark_purged,
    node_may_read,
    purge_blob,
    purge_due,
    record,
    store_stream,
    timeout_stale_tasks,
)
from app.inputs import get as get_input
from app.gate import (
    RevokeRefused,
    finish_gate_run,
    get_gate_run,
    list_agent_capabilities,
    revoke_capability,
    start_gate_run,
)
from app.invite import (
    InviteError,
    issue_invite,
    list_invites,
    looks_like_invite,
    redeem_invite,
    revoke_invite,
    verify_invite,
)
from app.safety import safety_posture
from app.work_units import DEFAULT_WINDOW_DAYS, work_units
from app.registry import (
    bind_agent_node,
    create_agent,
    create_node,
    heartbeat,
    liveness,
    get_agent,
    get_node,
    list_agents,
    list_nodes,
)

# **핸들러를 붙이지 않으면 `logger.*` 는 조용히 버려진다 (2026-09-02 실측).**
# uvicorn 은 자기 로거만 설정하고 앱 로거는 건드리지 않는다. 그래서 이 파일의
# `logger.info`·`logger.exception` 15곳이 **한 줄도 안 나왔다** — 컨테이너 로그에
# `core gc started` 도 `gc: purged=…` 도 없었다.
#
# 무엇이 안 보였나가 중요하다:
#   - GC 가 **입력 바이트를 언제 몇 개 지웠는지** (D22 보존 정책이 도는 증거)
#   - 시도 상한을 다 쓴 task 를 **종결했는지** (0015 가 「운영에서 보이게」 하려던 것)
#   - `gc: pass failed` · `worker: claim failed` — **예외 경로**.
#     둘 다 「죽지 않는다」고 삼키고 로그로만 알리는데, 그 로그가 없었다.
#     매 패스마다 터져도 아무도 몰랐을 것이다.
#
# `force=` 를 쓰지 않는다 — uvicorn 이 이미 붙인 것을 걷어내지 않는다.
logging.basicConfig(
    level=os.environ.get("CORE_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CapNet Core",
    # openapi.yaml 의 info.version 과 **같아야 한다** (test_openapi_drift 가 못박는다).
    # 갈리면 `GET /openapi.yaml` 과 `GET /openapi.json` 이 같은 Core 를 다른 버전으로 부른다.
    version="0.3.0",
    description="Capability 게이트·claim Core. 정적 YAML 초안은 GET /openapi.yaml (S4).",
)

_OPENAPI_YAML = Path(__file__).resolve().parents[1] / "openapi.yaml"

# 최소 UI (P2-3 호출면). StaticFiles 는 starlette 동봉이라 새 의존성이 아니다.
# 외부 자산(CDN·폰트·아이콘)을 쓰지 않는다 — 내부망·오프라인에서 그대로 뜬다.
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_STATIC_DIR), html=True), name="ui")


class TaskCreate(BaseModel):
    dataset_id: str = Field(alias="datasetId")
    case_id: str = Field(alias="caseId")
    capability_code: str = "image.classify"
    capability_version: int = 1
    requested_agent_id: uuid.UUID | None = Field(default=None, alias="requestedAgentId")
    # 요청자가 자기 작업의 신뢰 도메인을 정한다 (B0). 기본은 종전 동작인 team.
    # 아무 값이나 되는 게 아니다 — capability.trust_domain_min 과의 호환은
    # task 의 복합 FK(domain_min_compatible)가 거절한다. 앱이 다시 검사하지 않는다.
    trust_domain: str = Field(default="team", alias="trustDomain")
    # Core 가 받아 둔 입력 (D22). 주면 그 바이트로 실행하고, 없으면 caseId 데모 경로다.
    input_id: uuid.UUID | None = Field(default=None, alias="inputId")

    model_config = {"populate_by_name": True}


class ArchCreate(BaseModel):
    """허용 아키텍처 등록 (D-arch). **추가만** — 갱신·삭제 없음."""

    arch: str
    max_params: int
    note: str | None = None


class AgentCreate(BaseModel):
    name: str
    version: str
    manifest_hash: str
    weights_uri: str
    weights_sha256: str
    weights_format: str = "safetensors"
    # 허용 아키텍처는 DB 행이다 (agent_arch). 없는 값이면 FK 가 등록을 막는다 (I1).
    # 선택 타입이지만 **필수다** — 핸들러가 인증 뒤에서 본다 (G5 · agents_create 주석 참조).
    arch: str | None = None


class InviteCreate(BaseModel):
    """초대 발행. **등급은 여기서 정해진다** — 소진하는 쪽이 아니라 (절대규칙 4)."""

    trust_domain: str = "tenant"          # team 은 DB 가 거절한다
    compute_tier_max: str = "M"
    # 초대로 들어온 기기가 속할 조직 (D24). 생략하면 발행자의 조직.
    # 등급과 같은 모양이다 — 신청자가 주장하지 못한다.
    org_id: uuid.UUID | None = None
    label: str | None = None
    ttl_days: int = Field(default=7, ge=1, le=90)
    max_redemptions: int = Field(default=1, ge=1, le=100)


class InviteRevokeBody(BaseModel):
    reason: str = "revoked"


class NodeRedeem(BaseModel):
    """초대 소진. 등급 필드가 **없다** — 초대장이 정한다 (절대규칙 4)."""

    name: str
    device_type: str = "PC_GPU"
    gpu: str | None = None


class CredentialIssueBody(BaseModel):
    """등급 필드가 없다 — 절대규칙 4 (C1). 있으면 400 으로 떨어진다 (extra 금지)."""

    label: str | None = None
    expires_at: Any | None = Field(default=None, alias="expiresAt")

    model_config = {"populate_by_name": True, "extra": "forbid"}


class CredentialRevokeBody(BaseModel):
    reason: str


class RevokeBody(BaseModel):
    agent_id: uuid.UUID = Field(alias="agentId")
    capability_id: uuid.UUID = Field(alias="capabilityId")
    reason: str

    model_config = {"populate_by_name": True}


class NodeCreate(BaseModel):
    name: str
    device_type: str
    trust_domain: str
    compute_tier_max: str
    is_gate_runner: bool = False
    gpu: str | None = None
    provision_source: str | None = None
    # 조직 (D24). 생략하면 **팀 운영 공용 기기** — 모든 조직의 작업을 받는다.
    # admin 이 정한다. Node 가 자기 소속을 주장하는 자리가 아니다.
    org_id: uuid.UUID | None = None


class BindBody(BaseModel):
    node_id: uuid.UUID
    weights_sha256_seen: str


class GateStartBody(BaseModel):
    agent_id: uuid.UUID
    capability_id: uuid.UUID
    runner_node_id: uuid.UUID


class GateFinishBody(BaseModel):
    status: str
    golden_score: float | None = None
    cases_total: int | None = None
    cases_passed: int | None = None
    dummy: bool = False
    note: str | None = None
    macro_f1: float | None = None
    invalid_rate: float | None = None
    # 라벨 공간 붕괴 차단. 계약이 min_per_class_recall 을 선언하면 실게이트 PASSED 에 필수.
    min_per_class_recall: float | None = None
    # S3: 실게이트는 필수. dummy plumbing은 생략 가능(넣으면 스냅샷과 일치해야 함).
    golden_set_sha256: str | None = None
    # 계약 게이트(quality_profile='none')에서 러너가 확인한 항목. golden 게이트에는 보내지 않는다.
    contract_checks: dict[str, Any] | None = None


class CapabilityCreate(BaseModel):
    code: str
    version: int = 1
    name: str
    description: str | None = None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    output_kind: str = "closed_set_labels"
    compute_tier: str = "M"
    trust_domain_min: str = "team"
    mvp_eligible: bool = False
    # golden = 골든셋 게이트를 붙인다 (아래 4개 필수).
    # none   = 계약만으로 라우팅한다 (아래 4개를 **보내지 않는다** — Core 가 센티널을 채운다).
    quality_profile: str = "golden"
    # 입력 크기 계약 (0011). 생략하면 32MiB. 절대 상한 256MiB 는 DB 가 거절한다.
    max_input_bytes: int | None = None
    # 배정 시도 상한 (0015). 생략하면 5. 절대 상한 50 은 DB 가 거절한다.
    max_attempts: int | None = None
    golden_set_ref: str | None = None
    golden_set_sha256: str | None = None
    golden_set_size: int | None = None
    golden_metrics: dict[str, Any] | None = None


class CapabilityDescriptionPatch(BaseModel):
    """`description` **하나만**. 다른 칸이 오면 400 이다 (`extra: forbid`).

    화이트리스트를 손으로 세지 않는다 — 계약 칸이 늘 때 빠뜨리면 그때 구멍이 생긴다.
    허용하는 것을 적고 **나머지는 모델이 막게** 한다.
    """

    description: str | None = None

    model_config = {"populate_by_name": True, "extra": "forbid"}


class ClaimBody(BaseModel):
    task_id: uuid.UUID | None = None
    node_id: uuid.UUID | None = None


class CompleteBody(BaseModel):
    """결과 보고.

    `label` 이 선택인 것은 **모든 능력이 라벨을 내지 않기 때문**이다 (단계 6 ①).
    임베딩은 벡터를 내고, 라벨 칸은 비어 있는 것이 사실이다 —
    빈 문자열로 채우면 증적이 「라벨이 있었다」고 거짓말한다.

    Node 는 둘 중 하나만 채운다. **둘 다 비면** Core 가 거절한다 —
    아무것도 안 낸 실행이 COMPLETED 로 기록되면 안 된다.
    """

    weights_sha256: str
    label: str | None = None
    confidence: float | None = None
    vector: list[float] | None = None
    # 여러 칸을 내는 능력(예: 표 추출)용. **키 이름은 Core 가 계약과 대조한다** —
    # 그러지 않으면 게이트가 검증한 모양과 증적에 남는 모양이 갈린다.
    output: dict[str, Any] | None = None
    dummy: bool = True
    duration_ms: int | None = None


# 관리 API 인증 강제. 기본 꺼짐 — 데모·로컬 compose 를 깨지 않는다.
# 켜지 않아도 **키가 오면 항상 검증한다.** 잘못된 키가 통과하는 구간을 만들지 않는다.
#
# 이 플래그가 꺼져 있는 동안 관리 API 는 열려 있다 — 그게 SD-010 의 상태다.
# 신뢰 네트워크 밖에 Core 를 두려면 반드시 켠다.
REQUIRE_API_KEY = os.environ.get("REQUIRE_API_KEY", "0") == "1"


def _actor(authorization: str | None) -> dict[str, Any] | None:
    """Authorization 에서 사용자를 해석한다. 키가 없으면 None (강제 모드면 401)."""
    if not looks_like_api_key(authorization):
        if REQUIRE_API_KEY:
            raise HTTPException(status_code=401, detail="api key required")
        return None
    try:
        with get_conn() as conn:
            return verify_key(conn, authorization)
    except ApiKeyError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _require(minimum: str, authorization: str | None) -> dict[str, Any] | None:
    """최소 역할을 요구한다.

    키가 오면 **항상** 역할까지 본다 — 강제가 꺼져 있어도 마찬가지다.
    「강제가 꺼져 있으니 권한 없는 키도 통과」하는 구간을 만들지 않는다.
    """
    from app.apikey import assert_role

    actor = _actor(authorization)
    if actor is None:
        return None  # 강제 꺼짐 + 키 없음 → 통과 (레거시 경로)
    try:
        assert_role(actor, minimum)
    except Forbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return actor


# 증서 강제. 기본 꺼짐 — 데모·로컬 compose 는 증서 없이 돈다 (초안 §4).
# 켜지 않아도 **토큰이 오면 항상 검증한다**. 잘못된 증서가 통과하는 구간을 만들지 않는다.
REQUIRE_NODE_CREDENTIAL = os.environ.get("REQUIRE_NODE_CREDENTIAL", "0") == "1"


def _authenticated_node(authorization: str | None) -> uuid.UUID | None:
    """Authorization 헤더에서 node_id 를 해석한다.

    URL 이 주장하는 node_id 를 믿지 않는다 — 호출자가 이 반환값과 대조한다 (SD-010).
    """
    if not authorization:
        if REQUIRE_NODE_CREDENTIAL:
            raise HTTPException(status_code=401, detail="node credential required")
        return None
    try:
        with get_conn() as conn:
            return verify_credential(conn, authorization)
    except CredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _assert_node_matches(claimed: uuid.UUID, authorization: str | None) -> None:
    actual = _authenticated_node(authorization)
    if actual is not None and actual != claimed:
        raise HTTPException(
            status_code=403,
            detail="credential belongs to a different node",
        )


def _actor_org(actor: dict[str, Any] | None) -> uuid.UUID | None:
    """행위자의 조직. 없으면 None — 팀 운영자이거나 강제 꺼진 데모 경로다 (D24).

    `app_user.org_id` 에서 읽는다. 요청 본문은 조직을 **주장하지 못한다** —
    등급과 같은 규율이다 (절대규칙 4 의 확장).
    """
    if actor is None:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT org_id FROM app_user WHERE id = %s", (str(actor["user_id"]),)
        ).fetchone()
    return row["org_id"] if row and row["org_id"] else None


def _actor_user(actor: dict[str, Any] | None) -> uuid.UUID | str:
    """행위자의 user_id. 키가 없으면 시드 admin (레거시 경로)."""
    return uuid.UUID(str(actor["user_id"])) if actor else SEED_ADMIN_ID


@app.get("/health")
def health() -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 AS ok").fetchone()
        cap = conn.execute(
            "SELECT id, code, version FROM capability WHERE code = %s AND version = %s",
            ("image.classify", 1),
        ).fetchone()
    return {
        "ok": bool(row),
        "postgres": "up",
        "capability": dict(cap) if cap else None,
    }


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/nodes.html")


@app.get("/v1/datasets")
def datasets_list() -> dict[str, Any]:
    """입력 allowlist — **보조 경로**다 (기획서 §5.2 · 절대규칙 7 = D8′).

    본경로는 Core 중개 수집(`POST /v1/inputs` · 계약·해시·크기·MIME·보존)이다.
    금지되는 것은 「자유 업로드」가 아니라 **비통제 수집**(서명 URL·fileToken)이다.
    """
    return {"items": sorted(ALLOWED_DATASET_IDS)}


@app.get("/v1/ops/status")
def ops_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """운영 한 눈 — 함대·큐·증적·신원이 지금 어떤 상태인가.

    조회면이 여러 개로 흩어져 있어서 「지금 괜찮은가」를 보려면 여러 번 물어야 했다.
    여기서 한 번에 준다. **쓰기 없음 · 시크릿 없음.**

    모니터링이 없다는 게 제품화의 공백 중 하나였다 (SD-017). 이건 그 첫 칸이고,
    알림·시계열은 아직 없다 — 이 응답을 긁어가는 쪽이 한다.
    """
    _require("developer", authorization)
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
              (SELECT count(*) FROM task WHERE status = 'QUEUED')            AS queue_depth,
              (SELECT count(*) FROM assignment
                WHERE status = 'LEASED' AND lease_expires_at > now())        AS leases_live,
              (SELECT count(*) FROM assignment
                WHERE status = 'LEASED' AND lease_expires_at <= now())       AS leases_expired,
              (SELECT count(*) FROM node)                                    AS nodes_total,
              (SELECT count(*) FROM node_liveness
                WHERE is_fresh AND availability IN ('AVAILABLE','BUSY'))     AS nodes_ready,
              (SELECT count(*) FROM agent_capability_passed
                WHERE revoked_at IS NULL)                                    AS certs_live,
              (SELECT count(*) FROM revoked_capability)                      AS certs_revoked,
              (SELECT count(*) FROM provenance_drift WHERE still_routable)   AS drift_routable,
              (SELECT count(*) FROM agent_arch_unbound WHERE routable)       AS arch_unbound_routable,
              (SELECT count(*) FROM node_credential_status
                WHERE NOT credential_valid)                                  AS nodes_without_credential,
              (SELECT count(*) FROM api_key WHERE revoked_at IS NULL)        AS api_keys_active,
              (SELECT max(version) FROM schema_migration)                    AS schema_version
            """
        ).fetchone()
    s = dict(row)

    # 「괜찮은가」를 판정해 준다 — 숫자만 주면 보는 사람마다 기준이 달라진다.
    warnings: list[str] = []
    if s["nodes_ready"] == 0:
        warnings.append("일할 수 있는 기기가 없다 (heartbeat 확인)")
    if s["leases_expired"] > 0:
        warnings.append(f"만료 lease {s['leases_expired']}건 — 워커가 회수 중이어야 한다")
    if s["drift_routable"] > 0:
        warnings.append(f"구 골든셋 증서로 라우팅 가능 {s['drift_routable']}건 (재게이트 대상)")
    if s["arch_unbound_routable"] > 0:
        warnings.append(f"arch 미결속 Agent 가 라우팅 가능 {s['arch_unbound_routable']}건")
    if s["api_keys_active"] == 0:
        warnings.append("관리 API 키가 없다 — 강제를 켜면 잠긴다")

    s["db_pool"] = pool_stats()
    if not s["db_pool"].get("enabled"):
        warnings.append("DB 커넥션 풀이 꺼져 있다 — 요청마다 새로 연결한다 (SD-017)")

    s["enforcement"] = {
        "node_credential": REQUIRE_NODE_CREDENTIAL,
        "api_key": REQUIRE_API_KEY,
    }
    s["warnings"] = warnings
    s["ok"] = not warnings
    return s


@app.get("/v1/ops/safety")
def ops_safety(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """안전 자세 — 「누가 내 데이터를 돌릴 수 있나」 (S2 · safety-chain G3).

    `/v1/ops/status` 는 함대 **합계**를 준다. 여기는 **기기 단위**로, 한 기기에 대해
    「왜 실행 가능한가」를 한 면에 모은다 — 등급·조달 경로·증서·생사·받을 수 있는
    요청 도메인·라우팅 가능한 (Agent, 능력) 쌍, 그리고 위험 표시.

    **읽기 전용 · DDL 0 · 시크릿 없음** (증서는 prefix·만료·마지막 사용만).

    운영 조회면이라 `developer` 이상을 요구한다. 강제가 꺼져 있고 키가 없으면
    종전대로 통과한다 — 데모 경로를 깨지 않는다. 키가 오면 역할은 항상 본다.
    """
    _require("developer", authorization)
    with get_conn() as conn:
        return safety_posture(
            conn,
            require_api_key=REQUIRE_API_KEY,
            require_credential=REQUIRE_NODE_CREDENTIAL,
        )


@app.get("/v1/ops/work-units")
def ops_work_units(
    days: int = DEFAULT_WINDOW_DAYS,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """작업량 — 얼마나 돌았고 얼마나 걸렸나 (P2-2 · PR-C · D1–D3).

    **정본은 Core 관측 시간**(`finished_at − created_at`)이다. Node 가 보고한
    `assignment.duration_ms` 는 추론 구간만 잰 값이라 **힌트**로 함께 낸다 (D1).
    절대규칙 4 의 정신이다 — Node 는 자기 등급을 주장할 수 없고, 자기 일의 양도
    같은 질문을 받는다.

    `vram_mb_peak` · `energy_wh` 는 **미계측**이다 (D2). RSS 로 대신 채우지 않는다.

    **읽기 전용 · DDL 0 · 시크릿 없음.** 관측 시간은 저장하지 않는 파생값이다.
    기본 창은 최근 7일이고 `?days=` 로 1..90 까지 넓힐 수 있다 (D3).
    """
    _require("developer", authorization)
    try:
        with get_conn() as conn:
            return work_units(conn, days=days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/openapi.yaml", include_in_schema=False)
def openapi_yaml() -> FileResponse:
    if not _OPENAPI_YAML.is_file():
        raise HTTPException(status_code=404, detail="openapi.yaml missing")
    return FileResponse(_OPENAPI_YAML, media_type="application/yaml", filename="openapi.yaml")


@app.get("/v1/arches")
def arches_list(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """허용 아키텍처 목록 (D-arch).

    공개하지 않는다 — 「이 플랫폼이 어떤 모델 구조를 받는가」는 운영 정보다.
    등록하려는 사람이 **먼저 확인**할 수 있어야 해서 `developer` 로 열었다.
    """
    _require("developer", authorization)
    with get_conn() as conn:
        return {"items": list_arches(conn)}


@app.post("/v1/arches")
def arches_create(body: ArchCreate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """허용 아키텍처를 **추가**한다 (D-arch · admin 전용).

    `agent.arch` 는 이 표를 FK 로 참조한다(`0008` · I1). 즉 여기 없는 arch 로는
    Agent 등록이 막힌다 — 그 동작은 **그대로 둔다.** 없던 것은 행을 넣는 경로였다.

    **갱신·삭제가 없는 것이 설계다.** `max_params` 는 계약 게이트의 상한이라
    사후에 바꾸면 **이미 통과한 증서의 근거가 바뀐다**(D15). 상한을 바꿔야 하면
    새 arch 이름으로 등록한다.
    """
    _require("admin", authorization)
    try:
        with get_conn() as conn:
            return create_arch(
                conn, arch=body.arch, max_params=body.max_params, note=body.note,
            )
    except ValueError as exc:
        detail = str(exc)
        code = 409 if "already exists" in detail else 400
        raise HTTPException(status_code=code, detail=detail) from exc


@app.get("/v1/capabilities")
def capabilities_list() -> dict[str, Any]:
    with get_conn() as conn:
        return {"items": list_capabilities(conn)}


@app.post("/v1/capabilities")
def capabilities_create(body: CapabilityCreate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """런타임 Capability 등록. UNIQUE(code,version)·CHECK는 DB가 강제한다.

    `quality_profile='none'` 이면 골든셋 없이 계약만으로 라우팅한다 (D20).
    센티널은 **Core 가 채운다** — 호출자가 넣으면 거절한다. 규약이 새면 언젠가
    진짜 골든셋 자리에 센티널이 들어간다.
    """
    _require("admin", authorization)
    try:
        with get_conn() as conn:
            return create_capability(
                conn,
                quality_profile=body.quality_profile,
                max_input_bytes=body.max_input_bytes,
                max_attempts=body.max_attempts,
                code=body.code,
                version=body.version,
                name=body.name,
                description=body.description,
                input_schema=body.input_schema,
                output_schema=body.output_schema,
                output_kind=body.output_kind,
                compute_tier=body.compute_tier,
                trust_domain_min=body.trust_domain_min,
                mvp_eligible=body.mvp_eligible,
                golden_set_ref=body.golden_set_ref,
                golden_set_sha256=body.golden_set_sha256,
                golden_set_size=body.golden_set_size,
                golden_metrics=body.golden_metrics,
            )
    except ValueError as exc:
        detail = str(exc)
        code = 409 if "already exists" in detail else 400
        raise HTTPException(status_code=code, detail=detail) from exc


@app.get("/v1/capabilities/{capability_id}")
def capabilities_get(capability_id: uuid.UUID) -> dict[str, Any]:
    with get_conn() as conn:
        row = get_capability(conn, capability_id)
    if row is None:
        raise HTTPException(status_code=404, detail="capability not found")
    return row


@app.patch("/v1/capabilities/{capability_id}")
def capabilities_patch_description(
    capability_id: uuid.UUID,
    body: CapabilityDescriptionPatch,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """라우터가 읽는 **설명만** 고친다. 계약은 못 고친다.

    등록(`POST`)은 `(code, version)` UNIQUE 로 한 번뿐이라, 저장소에서 설명을 고쳐도
    이미 등록된 스택에는 들어가지 않았다. 그 하나를 여기서 연다 — **DDL 0**.

    계약 칸(`input_schema`·`compute_tier`·`golden_*` …)은 `body` 모델이 400 으로 막는다.
    그것들은 `task_input`·`gate_run`·`assignment` **스냅샷의 원본**이고, 원본이 움직이면
    이미 찍힌 스냅샷이 거짓말이 된다.
    """
    _require("admin", authorization)
    with get_conn() as conn:
        row = update_capability_description(conn, capability_id, description=body.description)
    if row is None:
        raise HTTPException(status_code=404, detail="capability not found")
    return row


@app.get("/v1/agents")
def agents_list(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
    with get_conn() as conn:
        return {"items": list_agents(conn)}


@app.post("/v1/agents")
def agents_create(body: AgentCreate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    actor = _require("developer", authorization)
    # arch 를 **등록에서** 요구한다 (G5). 없으면 실행 아키텍처를 Node 로컬 meta 가 정하게
    # 되고, 그게 I1 이 닫으려던 구멍이다. legacy 행(arch IS NULL)은 그대로 두고
    # `agent_arch_unbound` 로 계속 드러낸다 — 새로 만들지만 않는다.
    #
    # 검사를 pydantic 필수 필드로 두지 않은 것은 의도다. 본문 검증이 인증보다 먼저 돌아서
    # (operate-production §5) 무인증 요청이 401 대신 422 를 받게 된다 — 강제 모드의
    # 「무인증 쓰기는 401」 불변식이 깨진다. 그래서 `_require` **뒤에서** 본다.
    if not body.arch:
        raise HTTPException(
            status_code=400,
            detail="arch 를 선언해야 한다 — 허용 목록은 agent_arch 행이다 (I1 · G5)",
        )
    try:
        with get_conn() as conn:
            return create_agent(
                conn,
                name=body.name,
                version=body.version,
                manifest_hash=body.manifest_hash,
                weights_uri=body.weights_uri,
                weights_sha256=body.weights_sha256,
                weights_format=body.weights_format,
                arch=body.arch,
                owner_id=_actor_user(actor),
            )
    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=400,
            detail=f"unknown arch {body.arch!r} — agent_arch 에 없는 아키텍처다",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/agents/{agent_id}")
def agents_get(agent_id: uuid.UUID, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
    with get_conn() as conn:
        row = get_agent(conn, agent_id)
        if row is None:
            raise HTTPException(status_code=404, detail="agent not found")
        row["capabilities"] = list_agent_capabilities(conn, agent_id)
    return row


@app.post("/v1/agents/{agent_id}/bindings")
def agents_bind(agent_id: uuid.UUID, body: BindBody, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
    try:
        with get_conn() as conn:
            return bind_agent_node(
                conn,
                agent_id=agent_id,
                node_id=body.node_id,
                weights_sha256_seen=body.weights_sha256_seen,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/nodes")
def nodes_list(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    actor = _require("developer", authorization)
    with get_conn() as conn:
        return {"items": list_nodes(conn, org_id=_actor_org(actor))}


@app.post("/v1/nodes")
def nodes_create(body: NodeCreate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """관리자/Core 등록. Node 런타임이 trust_domain·tier를 주장하는 경로가 아니다."""
    actor = _require("admin", authorization)
    try:
        with get_conn() as conn:
            return create_node(
                conn,
                name=body.name,
                device_type=body.device_type,
                trust_domain=body.trust_domain,
                compute_tier_max=body.compute_tier_max,
                is_gate_runner=body.is_gate_runner,
                gpu=body.gpu,
                provision_source=body.provision_source,
                org_id=body.org_id,
                owner_id=_actor_user(actor),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/nodes/invites")
def invite_issue(body: InviteCreate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """초대장을 발행한다 — 평문은 이때 한 번만 나온다 (G2 · 0016).

    **등급은 여기서 정해져 초대장에 박힌다.** 소진하는 쪽은 바꾸지 못한다 (절대규칙 4).
    `team` 은 초대로 만들 수 없다 — DB 가 거절한다.
    """
    actor = _require("admin", authorization)
    issued_by = uuid.UUID(str(actor["user_id"])) if actor else SEED_ADMIN_ID
    try:
        with get_conn() as conn:
            return issue_invite(
                conn,
                issued_by=issued_by,
                org_id=body.org_id or _actor_org(actor),
                trust_domain=body.trust_domain,
                compute_tier_max=body.compute_tier_max,
                label=body.label,
                ttl_days=body.ttl_days,
                max_redemptions=body.max_redemptions,
            )
    except InviteError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/nodes/invites")
def invites_list(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """초대장 상태 목록. 시크릿도 해시도 나가지 않는다 — prefix·상태만.

    폐기하려면 `id` 가 필요한데 발행 응답을 잃으면 다시 볼 길이 없다. 그래서 있다.
    """
    _require("admin", authorization)
    with get_conn() as conn:
        return {"items": list_invites(conn)}


@app.post("/v1/nodes/invites/{invite_id}/revoke")
def invite_revoke(
    invite_id: uuid.UUID,
    body: InviteRevokeBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require("admin", authorization)
    with get_conn() as conn:
        row = revoke_invite(conn, invite_id=invite_id, reason=body.reason)
    if row is None:
        raise HTTPException(status_code=404, detail="살아 있는 초대가 없다")
    return row


@app.post("/v1/nodes/redeem")
def node_redeem(body: NodeRedeem, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """초대를 소진해 Node 를 만들고 증서까지 받는다 (G2 · 원스텝).

    **이 경로만 관리 키 없이 열린다.** 초대받은 사람에게는 키가 없기 때문이다 —
    초대 토큰 자체가 인증이다. 그래서 완화를 겹쳐 둔다: 만료 · 1회용(기본) ·
    폐기 · `audit_log` · 소진 판정을 DB 의 조건부 UPDATE 가 한다.

    **등급은 초대장에서 읽는다.** 본문은 이름·기기 종류만 준다 (절대규칙 4).
    `is_gate_runner` 는 언제나 거짓이다 — `ck_gate_runner_team` 이 어차피 막는다.
    """
    if not looks_like_invite(authorization):
        raise HTTPException(status_code=401, detail="초대 토큰이 필요하다 (CapNet-Invite ci_…)")
    try:
        with get_conn() as conn:
            invite = verify_invite(conn, authorization or "")
            node = create_node(
                conn,
                name=body.name,
                device_type=body.device_type,
                # 등급은 초대장 값이다. 본문에 무엇이 오든 쓰지 않는다.
                trust_domain=invite["trust_domain"],
                compute_tier_max=invite["compute_tier_max"],
                is_gate_runner=False,
                gpu=body.gpu,
                provision_source="invited",
                # 조직도 초대장이 정한다 (D24). 소진 요청은 여전히 아무것도 주장하지 않는다.
                org_id=invite["org_id"],
                owner_id=invite["issued_by"],
            )
            redeem_invite(
                conn, invite=invite, node_id=node["id"], node_name=body.name
            )
            cred = issue_credential(
                conn, node_id=node["id"], issued_by=invite["issued_by"], label="invite"
            )
    except InviteError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except CredentialError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"node": node, "credential": cred}


@app.get("/v1/nodes/{node_id}")
def nodes_get(node_id: uuid.UUID, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
    with get_conn() as conn:
        row = get_node(conn, node_id)
    if row is None:
        raise HTTPException(status_code=404, detail="node not found")
    return row


@app.post("/v1/nodes/{node_id}/credentials")
def credential_issue(node_id: uuid.UUID, body: CredentialIssueBody | None = None, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """증서 발급 (admin). `secret` 은 **이 응답에만** 있다 — 저장하지 않는다 (C3).

    등급 필드를 받지 않는다 (C1 · 절대규칙 4). 보내면 422 로 떨어진다.
    회전은 폐기 후 재발급이다 — Node 당 활성 증서는 하나다.
    """
    _require("admin", authorization)
    body = body or CredentialIssueBody()
    try:
        with get_conn() as conn:
            return issue_credential(
                conn,
                node_id=node_id,
                issued_by=uuid.UUID(SEED_ADMIN_ID),
                label=body.label,
                expires_at=body.expires_at,
            )
    except CredentialError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/nodes/{node_id}/credentials/revoke")
def credential_revoke(node_id: uuid.UUID, body: CredentialRevokeBody, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("admin", authorization)
    try:
        with get_conn() as conn:
            row = revoke_credential(conn, node_id=node_id, reason=body.reason)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="active credential not found")
    return row


@app.get("/v1/api-keys")
def api_keys_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """발급된 관리 키 상태. 시크릿도 해시도 나가지 않는다 — prefix·역할만.

    발급은 API 로 하지 않는다. 첫 키를 만들 수 없어 잠기기 때문이다 —
    `python -m app.apikey_cli issue` 가 DB 에 직접 붙는다.
    """
    _require("admin", authorization)
    with get_conn() as conn:
        return {"items": list_key_status(conn)}


@app.get("/v1/nodes-credentials")
def credentials_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Node 별 증서 상태. 시크릿도 해시도 나가지 않는다 — prefix 만."""
    _require("admin", authorization)
    with get_conn() as conn:
        return {"items": list_credential_status(conn)}


@app.post("/v1/internal/gate-runs")
def gate_start(body: GateStartBody, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
    try:
        with get_conn() as conn:
            row = start_gate_run(
            conn,
                agent_id=body.agent_id,
                capability_id=body.capability_id,
                runner_node_id=body.runner_node_id,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(
            status_code=409,
            detail="gate-run start rejected (missing row or runner is not gate-runner)",
        )
    return row


@app.post("/v1/internal/gate-runs/{gate_run_id}/finish")
def gate_finish(gate_run_id: uuid.UUID, body: GateFinishBody, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
    try:
        with get_conn() as conn:
            row = finish_gate_run(
                conn,
                gate_run_id=gate_run_id,
                status=body.status,
                golden_score=body.golden_score,
                cases_total=body.cases_total,
                cases_passed=body.cases_passed,
                dummy=body.dummy,
                note=body.note,
                macro_f1=body.macro_f1,
                invalid_rate=body.invalid_rate,
                min_per_class_recall=body.min_per_class_recall,
                golden_set_sha256=body.golden_set_sha256,
                contract_checks=body.contract_checks,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=409, detail="gate-run not RUNNING or not found")
    return row


@app.get("/v1/internal/gate-runs/{gate_run_id}")
def gate_get(gate_run_id: uuid.UUID, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
    with get_conn() as conn:
        row = get_gate_run(conn, gate_run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="gate-run not found")
    return row


@app.post("/v1/internal/agent-capabilities/revoke")
def capability_revoke(body: RevokeBody, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """능력 증서 폐기 — 행은 남기고 라우팅만 끊는다 (SD-014).

    근거 없이는 거부한다: 현재 골든셋에서 FAILED 인 gate_run 이 있어야 한다.
    되돌리려면 다시 게이트를 통과시킨다.
    """
    _require("admin", authorization)
    try:
        with get_conn() as conn:
            row = revoke_capability(
                conn,
                agent_id=body.agent_id,
                capability_id=body.capability_id,
                reason=body.reason,
            )
    except RevokeRefused as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="routable certificate not found (already revoked, or never passed)",
        )
    return row


@app.post("/v1/tasks")
def create_task(body: TaskCreate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    actor = _require("user", authorization)
    # D8′ · Decision A — **Core 가 중개한 입력이면 allowlist 를 건너뛴다.**
    #
    # allowlist 는 「비통제 수집」을 막으려고 있다. `inputId` 가 있으면 바이트는 이미
    # Core 를 거쳐 왔고, **수집 시점에 능력에 묶였으며**(`task_input.capability_id` 복합 FK)
    # 해시·크기·MIME 이 계약과 대조됐다. 그 경로에서 datasetId 를 다시 묻는 것은
    # 통제를 더하지 않는다 — 오히려 **거짓말을 시킨다.**
    #
    # 실제로 그랬다: 텍스트 작업에는 맞는 datasetId 가 없어서, 통과시키려면
    # `eurosat-rgb` 를 적어야 했다. 그러면 증적에 **없던 데이터셋**이 남는다 —
    # 「내 데이터가 어디로 갔는지 답한다」를 스스로 깨는 것이다.
    #
    # 지금은 요청자가 `text-demo` 처럼 **참인 이름**을 적고 그대로 증적에 남는다.
    # 「비통제 수집 금지」는 그대로다 — 바이트를 받는 문(`POST /v1/inputs`)은 안 건드렸다.
    if body.input_id is None:
        try:
            assert_dataset_id(body.dataset_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    ref: dict[str, Any] = {"datasetId": body.dataset_id, "caseId": body.case_id}
    with get_conn() as conn:
        # Core 가 받아 둔 입력을 쓰는 경로 (D22). 해시를 input_ref 에 실어 Node 가 대조한다.
        # 이 값이 없으면 종전 데모 경로(caseId → Node 로컬 골든셋)로 그대로 돈다.
        if body.input_id is not None:
            ti = get_input(conn, body.input_id)
            if ti is None:
                raise HTTPException(status_code=404, detail="input not found")
            if ti["storage_state"] != "STORED":
                raise HTTPException(
                    status_code=409,
                    detail=f"input bytes are {ti['storage_state']} — 다시 올린다",
                )
            ref["inputId"] = str(body.input_id)
            ref["inputSha"] = ti["sha256"]
            ref["mediaType"] = ti["media_type"]
        input_ref = json.dumps(ref)
        cap = conn.execute(
            "SELECT id, trust_domain_min FROM capability WHERE code = %s AND version = %s",
            (body.capability_code, body.capability_version),
        ).fetchone()
        if cap is None:
            raise HTTPException(status_code=404, detail="capability not found")

        # 요청자는 **키가 말한다** (B0). `_actor()` 가 이미 해석해 둔 것을 버리지 않는다.
        # 키가 없는 경로(강제 꺼진 데모)에서만 seed admin 으로 떨어진다 — 그때는
        # 「누가 요청했는지 모른다」가 사실이고, 그 사실이 seed admin 으로 기록된다.
        user_id = str(actor["user_id"]) if actor else SEED_ADMIN_ID
        owner = conn.execute(
            "SELECT id FROM app_user WHERE id = %s", (user_id,)
        ).fetchone()
        if owner is None:
            raise HTTPException(status_code=500, detail=f"app_user missing: {user_id}")

        # trust_domain_min 스냅샷은 capability 행에서 SELECT.
        # trust_domain 은 요청자가 준 값이며, capability 와 맞지 않으면
        # task 의 복합 FK(domain_min_compatible)가 INSERT 를 거절한다 — 앱이 판정하지 않는다.
        try:
            created = conn.execute(
                """
                INSERT INTO task (
                    user_id, capability_id, status, trust_domain,
                    capability_trust_domain_min, input_ref, requested_agent_id, input_id,
                    org_id
                )
                -- 조직은 **요청자의 것**을 읽어 박는다 (D24). 본문이 정하지 않는다.
                SELECT %(user_id)s, c.id, 'QUEUED', %(trust_domain)s,
                       c.trust_domain_min, %(input_ref)s, %(requested_agent_id)s::uuid,
                       %(input_id)s::uuid,
                       (SELECT u.org_id FROM app_user u WHERE u.id = %(user_id)s)
                  FROM capability c
                 WHERE c.id = %(capability_id)s
                RETURNING id, user_id, status, input_ref, capability_id,
                          trust_domain, capability_trust_domain_min, requested_agent_id,
                          input_id, org_id
                """,
                {
                    "user_id": user_id,
                    "capability_id": str(cap["id"]),
                    "trust_domain": body.trust_domain,
                    "input_ref": input_ref,
                    "requested_agent_id": str(body.requested_agent_id) if body.requested_agent_id else None,
                    "input_id": str(body.input_id) if body.input_id else None,
                },
            ).fetchone()
        except psycopg.errors.ForeignKeyViolation as exc:
            name = getattr(exc.diag, "constraint_name", "") or ""
            if "task_input_capability_fkey" in name:
                # 입력은 수집 시점에 능력에 묶인다 (D8′). 다른 능력의 입력은 못 쓴다.
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "이 입력은 다른 capability 로 수집됐다 — 해당 능력으로 다시 올린다 "
                        f"({name})"
                    ),
                ) from exc
            # capability 가 요구하는 최소 도메인보다 낮은 도메인으로 요청한 경우.
            raise HTTPException(
                status_code=400,
                detail=(
                    f"trust_domain={body.trust_domain!r} 은 이 capability 에 쓸 수 없다 "
                    f"(최소 {cap['trust_domain_min']!r}) — {name}"
                ),
            ) from exc
    return dict(created)


@app.post("/v1/inputs")
async def input_upload(
    request: Request,
    capability: str = "image.classify",
    version: int = 1,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """입력 바이트를 Core 가 받는다 (D22 · D8′ 「계약된 ingest」).

        curl -X POST 'localhost:8000/v1/inputs?capability=image.classify&version=1' \
             -H 'content-type: image/jpeg' -H "Authorization: CapNet-Key $KEY" \
             --data-binary @my.jpg

    **자유 업로드가 아니다.** 입력은 수집 시점에 능력에 묶이고(`task_input.capability_id`),
    크기는 계약이 정하며(DB 가 판정), MIME 은 계약이 선언한 목록과 대조한다.

    multipart 를 쓰지 않는다 — `python-multipart` 의존성이 새로 필요해진다.
    raw body 를 스트리밍으로 받고 `content-type` 을 media_type 으로 쓴다.
    """
    actor = _require("user", authorization)
    media_type = (request.headers.get("content-type") or "").split(";")[0].strip()
    if not media_type:
        raise HTTPException(status_code=400, detail="content-type 헤더가 필요하다")

    with get_conn() as conn:
        cap = load_capability(conn, code=capability, version=version)
        if cap is None:
            raise HTTPException(status_code=404, detail="capability not found")
        try:
            assert_media_type(media_type, cap["input_schema"])
        except InputRejected as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        max_bytes = int(cap["max_input_bytes"])

    input_id = uuid.uuid4()

    # 받는 즉시 디스크로 흘린다 — 메모리에 모으면 상한(최대 256MiB)만큼 상주한다.
    try:
        sha256, byte_size = await store_stream(
            request.stream(), input_id=input_id, max_bytes=max_bytes
        )
    except InputTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except InputRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    uploader = str(actor["user_id"]) if actor else SEED_ADMIN_ID
    try:
        with get_conn() as conn:
            row = record(
                conn,
                input_id=input_id,
                capability_id=cap["id"],
                sha256=sha256,
                byte_size=byte_size,
                media_type=media_type,
                uploaded_by=uploader,
            )
    except InputTooLarge as exc:
        purge_blob(input_id)
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except InputRejected as exc:
        purge_blob(input_id)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return row


@app.get("/v1/inputs/{input_id}")
def input_get(input_id: uuid.UUID, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """입력 **메타**. 바이트는 여기서 안 준다 (Node 전용 경로가 따로 있다)."""
    _require("user", authorization)
    with get_conn() as conn:
        row = get_input(conn, input_id)
    if row is None:
        raise HTTPException(status_code=404, detail="input not found")
    return row


@app.post("/v1/inputs/{input_id}/purge")
def input_purge(input_id: uuid.UUID, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """바이트만 즉시 삭제한다. **행·해시는 남는다** (증적).

    본경로는 워커 GC 다 (Decision). 이건 사고·고객 요청용 선택 경로다.
    """
    _require("admin", authorization)
    with get_conn() as conn:
        row = get_input(conn, input_id)
        if row is None:
            raise HTTPException(status_code=404, detail="input not found")
        if row["storage_state"] == "PURGED":
            return {**row, "purged_now": False}
        marked = mark_purged(conn, input_id)
        if marked is None:
            # **UPDATE 가 0행이다 — 내가 지운 것이 아니다.**
            #
            # 위에서 읽은 뒤 여기 오기까지 사이에 다른 쪽이 이미 지웠다는 뜻이다.
            # 가상의 경우가 아니다 — GC 가 **같은 프로세스의 배경 스레드**로 돌고
            # (`_gc_loop`), `task_input_purge_due` 에 걸린 입력을 언제든 집는다.
            #
            # 예전에는 여기서도 `purged_now: True` 를 돌려줬다. 그것도 문제지만
            # 더 나쁜 것은 `marked or row` 로 **읽어 둔 옛 행**을 함께 실어 보낸 것이다 —
            # 응답이 `storage_state: STORED` 와 `purged_now: true` 를 **동시에** 말했다.
            # 「못 했다」를 「됐다」로 뭉뚱그리는 자리라 사실을 다시 읽어 돌려준다.
            raced = get_input(conn, input_id) or row
            logger.info("input purge raced id=%s — 다른 쪽이 이미 지웠다", input_id)
            return {**raced, "purged_now": False}
    removed = purge_blob(input_id)
    logger.info("input purged id=%s file_removed=%s", input_id, removed)
    return {**marked, "purged_now": True, "file_removed": removed}


class SampleBody(BaseModel):
    input_id: uuid.UUID = Field(alias="inputId")

    model_config = {"populate_by_name": True}


@app.post("/v1/capabilities/{capability_id}/sample")
def capability_set_sample(
    capability_id: uuid.UUID,
    body: SampleBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """계약 검증 샘플을 지정한다 (B2 · Decision 1 = task_input).

    ungated 능력은 골든셋이 없다. 러너가 **이 바이트로 실제 추론해서** input_schema ·
    output_schema 를 확인한다. 「무엇을 받는가」를 선언했으면 그 예시도 계약의 일부다.

    같은 능력으로 수집된 입력만 샘플이 될 수 있다 — 복합 FK 가 판정한다 (0013).
    """
    _require("admin", authorization)
    with get_conn() as conn:
        try:
            row = set_sample(conn, capability_id=capability_id, input_id=body.input_id)
        except InputRejected as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="capability not found")
    return row


@app.get("/v1/internal/capabilities/{capability_id}/sample")
def capability_get_sample(
    capability_id: uuid.UUID,
    node_id: uuid.UUID,
    authorization: str | None = Header(default=None),
) -> Any:
    """게이트러너가 계약 샘플 바이트를 가져간다 (B2).

    lease 가 아니라 **게이트러너 자격**으로 준다 — 계약 검증은 배정 이전에 일어난다.
    절대규칙 8: 게이트는 team gate-runner 에서만 돈다.
    """
    _assert_node_matches(node_id, authorization)
    with get_conn() as conn:
        if not is_gate_runner(conn, node_id):
            raise HTTPException(status_code=403, detail="게이트러너만 계약 샘플을 받는다")
        row = get_sample(conn, capability_id)
    if row is None:
        raise HTTPException(status_code=404, detail="이 능력에 계약 샘플이 없다")
    if row["storage_state"] != "STORED":
        raise HTTPException(status_code=410, detail="sample bytes purged")
    path = blob_path(row["id"])
    if not path.is_file():
        raise HTTPException(status_code=410, detail="sample bytes missing on disk")
    return FileResponse(
        str(path),
        media_type=row["media_type"],
        headers={"x-capnet-input-sha256": row["sha256"]},
    )


@app.get("/v1/internal/inputs/{input_id}/bytes")
def input_bytes(
    input_id: uuid.UUID,
    node_id: uuid.UUID,
    authorization: str | None = Header(default=None),
) -> Any:
    """Node 가 자기 배정의 입력 바이트를 가져간다.

    **살아 있는 lease 가 있어야 한다.** 증서만으로 아무 입력이나 내려주면 등록된 기기
    전부가 남의 데이터를 읽는다 — 「승인 도메인 안으로만 간다」가 무너진다.
    """
    _assert_node_matches(node_id, authorization)
    with get_conn() as conn:
        row = get_input(conn, input_id)
        if row is None:
            raise HTTPException(status_code=404, detail="input not found")
        if row["storage_state"] != "STORED":
            raise HTTPException(status_code=410, detail="input bytes purged")
        if not node_may_read(conn, node_id=node_id, input_id=input_id):
            raise HTTPException(
                status_code=403,
                detail="이 Node 에 이 입력을 쓰는 살아 있는 lease 가 없다",
            )
    path = blob_path(input_id)
    if not path.is_file():
        raise HTTPException(status_code=410, detail="input bytes missing on disk")
    return FileResponse(
        str(path),
        media_type=row["media_type"],
        headers={"x-capnet-input-sha256": row["sha256"]},
    )


@app.post("/v1/internal/claim")
def claim(body: ClaimBody | None = None, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Core 워커 전용. Node는 이 경로를 pull하지 않는다."""
    _require("admin", authorization)
    payload = body or ClaimBody()
    with get_conn() as conn:
        row = claim_next(conn, task_id=payload.task_id, node_id=payload.node_id)
        if row is None:
            raise HTTPException(status_code=409, detail="no claimable task or no compatible node")
        detail = lease_detail(conn, row["id"])
    if detail:
        row = {**row, **detail}
    return row


class HeartbeatBody(BaseModel):
    availability: str = "AVAILABLE"
    metrics: dict[str, Any] | None = None


@app.post("/v1/internal/nodes/{node_id}/heartbeat")
def node_heartbeat(
    node_id: uuid.UUID,
    body: HeartbeatBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Node 생존·가용 신고. 이게 없으면 죽은 기기에도 배정이 간다.

    증서가 오면 URL 의 node_id 와 대조한다 — 사칭 차단 (SD-010 · P2-4).
    """
    _assert_node_matches(node_id, authorization)
    try:
        with get_conn() as conn:
            return heartbeat(
                conn, node_id=node_id, availability=body.availability, metrics=body.metrics
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/nodes-liveness")
def nodes_liveness(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """어느 기기가 살아 있고 얼마나 바쁜지. 배정 근거를 사람이 볼 수 있게 한다."""
    actor = _require("developer", authorization)
    with get_conn() as conn:
        return {"nodes": liveness(conn, org_id=_actor_org(actor))}


@app.get("/v1/internal/nodes/{node_id}/assignments")
def node_open_assignments(
    node_id: uuid.UUID, authorization: str | None = Header(default=None)
) -> dict[str, Any]:
    """Node가 자기에게 배정된 살아 있는 lease를 가져간다.

    큐 pull이 아니다. 배치는 Core 워커가 이미 끝냈고, 여기서는 결과만 전달한다.
    이 경로 덕분에 Core가 Node로 들어갈 필요가 없다 (NAT).

    증서가 오면 URL 의 node_id 와 대조한다 — 사칭 차단 (SD-010 · P2-4).
    """
    _assert_node_matches(node_id, authorization)
    with get_conn() as conn:
        rows = node_assignments(conn, node_id)
    return {"node_id": str(node_id), "count": len(rows), "assignments": rows}


class FailBody(BaseModel):
    node_id: uuid.UUID = Field(alias="nodeId")
    reason: str = ""

    model_config = {"populate_by_name": True}


@app.post("/v1/internal/assignments/{assignment_id}/fail")
def assignment_fail(
    assignment_id: uuid.UUID,
    body: FailBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Node 가 실행 실패를 보고한다 (0015).

    이게 없으면 실패가 **lease 만료(60초)로만** 드러나고, 그 동안 Node 는 같은 배정을
    계속 재시도한다 — 로그에만 쌓이고 증적에는 없다.

    보고하면 배정은 즉시 FAILED 로 남고, task 는 QUEUED 로 돌아가 **다른 기기가 시도**할 수
    있다. 시도 상한을 다 쓰면 워커가 task 를 FAILED 로 종결한다.
    """
    _assert_node_matches(body.node_id, authorization)
    with get_conn() as conn:
        row = fail_assignment(
            conn, assignment_id=assignment_id, node_id=body.node_id, reason=body.reason
        )
    if row is None:
        raise HTTPException(
            status_code=409,
            detail="살아 있는 lease 가 아니거나 이 Node 의 배정이 아니다",
        )
    logger.info(
        "assignment failed id=%s task=%s attempt=%s/%s",
        row["id"], row["task_id"], row["attempt_no"], row["capability_max_attempts"],
    )
    return row


@app.get("/v1/tasks/{task_id}")
def get_task(task_id: uuid.UUID, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """작업 상태와 실행 증적. **자기 작업만** 본다.

    이 응답에는 결과(`result_ref`)와 증적(어느 기기·어느 에이전트)이 들어 있다.
    인증 없이 열려 있으면 「증적이 남고 조회된다」가 「누구나 조회된다」가 된다.

    소유자가 아니면 **404** 다 (403 아님) — 403 은 「그 id 는 존재한다」를 흘린다.
    `developer` 이상은 **자기 조직 안에서** 남의 작업도 본다 (D24).
    조직 없는 `admin` 은 팀 운영자로 보고 전체를 본다.

    키가 없으면(강제 꺼짐) 종전대로 통과한다 — 데모·심사 재현 경로를 깨지 않는다.
    """
    actor = _require("user", authorization)
    with get_conn() as conn:
        task = conn.execute(
            "SELECT id, user_id, org_id, status, input_ref, result_ref, "
            "current_assignment_id, capability_id, trust_domain FROM task WHERE id = %s",
            (str(task_id),),
        ).fetchone()
        if task is None:
            raise HTTPException(status_code=404, detail="task not found")
        if actor is not None:
            from app.apikey import ROLE_RANK

            is_owner = str(task["user_id"]) == str(actor["user_id"])
            rank = ROLE_RANK.get(str(actor["role"]), 0)
            my_org = _actor_org(actor)
            # 운영자는 **자기 조직 안에서만** 남의 작업을 본다 (D24).
            # 조직 없는 admin 은 팀 운영자다 — 플랫폼 전체를 본다.
            same_org = my_org is not None and str(task["org_id"]) == str(my_org)
            is_operator = (
                (rank >= ROLE_RANK["developer"] and same_org)
                or (rank >= ROLE_RANK["admin"] and my_org is None)
            )
            if not (is_owner or is_operator):
                # 없는 것과 같은 답을 준다. 존재 여부를 캐지 못하게.
                raise HTTPException(status_code=404, detail="task not found")
        assignment = None
        if task["current_assignment_id"]:
            # 배정 시점의 **스냅샷**도 같이 준다 — 「승인 도메인 안으로만 갔다」를
            # 증적으로 보이려면 어느 도메인·어느 티어로 판정됐는지가 응답에 있어야 한다.
            # 이 네 열은 DB 가 복합 FK 로 검증한 값이지 앱이 계산한 값이 아니다.
            assignment = conn.execute(
                "SELECT id, status, agent_id, node_id, finished_at, "
                "task_trust_domain, node_trust_domain, capability_tier, node_tier_max "
                "FROM assignment WHERE id = %s",
                (str(task["current_assignment_id"]),),
            ).fetchone()
    return {**dict(task), "assignment": dict(assignment) if assignment else None}


@app.post("/v1/internal/assignments/{assignment_id}/complete")
def complete(
    assignment_id: uuid.UUID,
    body: CompleteBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """결과 보고. 증서가 오면 **그 배정의 주인인지**까지 본다.

    heartbeat·assignments 와 달리 URL 에 node_id 가 없다 — assignment 를 통해 소유권을 확인한다.
    """
    # 아무것도 안 낸 실행이 COMPLETED 로 기록되면 안 된다. dummy 는 예외 —
    # 그쪽은 「placeholder 라 답을 못 낸다」가 이미 증적에 남는다.
    if not body.dummy and body.label is None and body.vector is None and body.output is None:
        raise HTTPException(
            status_code=422, detail="label · vector · output 중 하나는 있어야 한다",
        )

    node = _authenticated_node(authorization)
    if node is not None:
        with get_conn() as conn:
            owner = conn.execute(
                "SELECT node_id FROM assignment WHERE id = %s", (str(assignment_id),)
            ).fetchone()
        if owner is None:
            raise HTTPException(status_code=404, detail="assignment not found")
        if owner["node_id"] != node:
            raise HTTPException(
                status_code=403, detail="credential does not own this assignment"
            )

    from app.complete import OutputKeysMismatch

    try:
        with get_conn() as conn:
            row = complete_assignment(
                conn,
                assignment_id=assignment_id,
                weights_sha256=body.weights_sha256,
                label=body.label,
                confidence=body.confidence,
                vector=body.vector,
                output=body.output,
                dummy=body.dummy,
                duration_ms=body.duration_ms,
            )
    except OutputKeysMismatch as exc:
        # 계약과 다른 칸을 받아 적지 않는다. Node 는 값만 내고 모양은 계약이 정한다.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(
            status_code=409,
            detail="complete rejected (not live lease or weights_sha256 mismatch)",
        )
    try:
        with get_conn() as conn:
            try_audit_succeeded(
                conn,
                task_id=row["task_id"],
                assignment_id=row["id"],
                weights_sha256=row["weights_sha256"],
                dummy=body.dummy,
            )
    except Exception:
        logger.warning("audit_log insert failed; min certificate already committed", exc_info=True)
    return row


# ---------------------------------------------------------------------------
# Core 디스패치 워커
#
# 사용자 → Core → (Node가 자기 몫을 가져감) → Core → 사용자 의 사이클을 닫는다.
# 이전에는 클라이언트가 claim 을 직접 호출하고 Node 에도 직접 접속했다.
# 큐 claim 은 여전히 Core 만 한다 (CLAUDE.md 규칙 유지).
# ---------------------------------------------------------------------------

WORKER_ENABLED = os.environ.get("CORE_WORKER", "1") != "0"
WORKER_INTERVAL_S = float(os.environ.get("CORE_WORKER_INTERVAL_S", "1.0"))


def _worker_once() -> dict[str, Any] | None:
    with get_conn() as conn:
        # 만료 lease 를 먼저 회수한다. 안 그러면 기기가 죽은 작업이 영구히 갇힌다.
        for r in reclaim_expired(conn):
            logger.info("worker: reclaimed expired lease task=%s", r["task_id"])
        return claim_next(conn)


# 입력 바이트 GC 주기. 배정 루프(1s)보다 훨씬 느려도 된다 — TTL 은 시간 단위다.
GC_INTERVAL_S = float(os.environ.get("CORE_GC_INTERVAL_S", "300"))
GC_BATCH = int(os.environ.get("CORE_GC_BATCH", "50"))


def _gc_once() -> dict[str, int]:
    """72h 미완료 task 종결 + 만료된 입력 바이트 삭제.

    정책은 코드가 아니라 `task_input_purge_due` 뷰가 갖는다 (0011) — 무엇이 왜 언제
    지워지는지를 사람이 SQL 로 볼 수 있어야 한다. **바이트만 지우고 행은 남긴다.**
    """
    purged = 0
    freed = 0
    with get_conn() as conn:
        timed_out = timeout_stale_tasks(conn)
        # 시도 상한을 다 쓴 task 를 종결한다 (0015). finished_at 이 박히므로
        # 입력 바이트 TTL(종결 후 7일)도 여기서 시작된다.
        exhausted = fail_exhausted_tasks(conn)
        for item in exhausted:
            logger.info(
                "gc: task exhausted id=%s capability=%s attempts=%s/%s",
                item["id"], item["capability_code"], item["attempts"], item["max_attempts"],
            )
        due = purge_due(conn, limit=GC_BATCH)
        for item in due:
            input_id = item["task_input_id"]
            purge_blob(input_id)  # 파일이 이미 없어도 상태는 맞춰 둔다
            if mark_purged(conn, input_id):
                purged += 1
                freed += int(item["byte_size"] or 0)
                logger.info(
                    "gc: input purged id=%s reason=%s bytes=%s",
                    input_id, item["reason"], item["byte_size"],
                )
    return {
        "timed_out": timed_out,
        "exhausted": len(exhausted),
        "purged": purged,
        "freed_bytes": freed,
    }


def _gc_loop() -> None:
    logger.info("core gc started (interval=%.0fs batch=%d)", GC_INTERVAL_S, GC_BATCH)
    while True:
        try:
            out = _gc_once()
            if out["timed_out"] or out["purged"] or out["exhausted"]:
                logger.info(
                    "gc: timed_out=%d exhausted=%d purged=%d freed=%d bytes",
                    out["timed_out"], out["exhausted"], out["purged"], out["freed_bytes"],
                )
        except Exception:  # GC 는 죽지 않는다
            logger.exception("gc: pass failed")
        time.sleep(GC_INTERVAL_S)


def _worker_loop() -> None:
    logger.info("core worker started (interval=%.1fs)", WORKER_INTERVAL_S)
    while True:
        try:
            row = _worker_once()
        except Exception:  # 워커는 죽지 않는다. 실패는 남기고 계속 돈다
            logger.exception("worker: claim failed")
            row = None
        if row is None:
            time.sleep(WORKER_INTERVAL_S)
            continue
        logger.info(
            "worker: dispatched task=%s assignment=%s node=%s agent=%s",
            row.get("task_id"), row.get("id"), row.get("node_id"), row.get("agent_id"),
        )


@app.on_event("startup")
def _start_worker() -> None:
    if not WORKER_ENABLED:
        logger.info("core worker disabled (CORE_WORKER=0)")
        return
    threading.Thread(target=_worker_loop, name="core-worker", daemon=True).start()
    threading.Thread(target=_gc_loop, name="core-gc", daemon=True).start()
