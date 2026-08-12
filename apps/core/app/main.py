import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import psycopg
from fastapi import FastAPI, Header, HTTPException
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
from app.capability import create_capability, get_capability, list_capabilities
from app.claim import claim_next, reclaim_expired
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
from app.gate import (
    RevokeRefused,
    finish_gate_run,
    get_gate_run,
    list_agent_capabilities,
    revoke_capability,
    start_gate_run,
)
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

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CapNet Core",
    version="0.2.0",
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

    model_config = {"populate_by_name": True}


class AgentCreate(BaseModel):
    name: str
    version: str
    manifest_hash: str
    weights_uri: str
    weights_sha256: str
    weights_format: str = "safetensors"
    # 허용 아키텍처는 DB 행이다 (agent_arch). 없는 값이면 FK 가 등록을 막는다 (I1).
    arch: str | None = None


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
    golden_set_ref: str | None = None
    golden_set_sha256: str | None = None
    golden_set_size: int | None = None
    golden_metrics: dict[str, Any] | None = None


class ClaimBody(BaseModel):
    task_id: uuid.UUID | None = None
    node_id: uuid.UUID | None = None


class CompleteBody(BaseModel):
    weights_sha256: str
    label: str
    confidence: float | None = None
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
    """입력 allowlist. 자유 업로드 경로는 없다 (기획서 §5.2 · 절대규칙 7)."""
    return {"items": sorted(ALLOWED_DATASET_IDS)}


@app.get("/v1/ops/status")
def ops_status() -> dict[str, Any]:
    """운영 한 눈 — 함대·큐·증적·신원이 지금 어떤 상태인가.

    조회면이 여러 개로 흩어져 있어서 「지금 괜찮은가」를 보려면 여러 번 물어야 했다.
    여기서 한 번에 준다. **쓰기 없음 · 시크릿 없음.**

    모니터링이 없다는 게 제품화의 공백 중 하나였다 (SD-017). 이건 그 첫 칸이고,
    알림·시계열은 아직 없다 — 이 응답을 긁어가는 쪽이 한다.
    """
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


@app.get("/openapi.yaml", include_in_schema=False)
def openapi_yaml() -> FileResponse:
    if not _OPENAPI_YAML.is_file():
        raise HTTPException(status_code=404, detail="openapi.yaml missing")
    return FileResponse(_OPENAPI_YAML, media_type="application/yaml", filename="openapi.yaml")


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


@app.get("/v1/agents")
def agents_list() -> dict[str, Any]:
    with get_conn() as conn:
        return {"items": list_agents(conn)}


@app.post("/v1/agents")
def agents_create(body: AgentCreate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
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
            )
    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=400,
            detail=f"unknown arch {body.arch!r} — agent_arch 에 없는 아키텍처다",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/agents/{agent_id}")
def agents_get(agent_id: uuid.UUID) -> dict[str, Any]:
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
def nodes_list() -> dict[str, Any]:
    with get_conn() as conn:
        return {"items": list_nodes(conn)}


@app.post("/v1/nodes")
def nodes_create(body: NodeCreate, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """관리자/Core 등록. Node 런타임이 trust_domain·tier를 주장하는 경로가 아니다."""
    _require("admin", authorization)
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
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/nodes/{node_id}")
def nodes_get(node_id: uuid.UUID) -> dict[str, Any]:
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
def credentials_status() -> dict[str, Any]:
    """Node 별 증서 상태. 시크릿도 해시도 나가지 않는다 — prefix 만."""
    with get_conn() as conn:
        return {"items": list_credential_status(conn)}


@app.post("/v1/internal/gate-runs")
def gate_start(body: GateStartBody, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _require("developer", authorization)
    with get_conn() as conn:
        row = start_gate_run(
            conn,
            agent_id=body.agent_id,
            capability_id=body.capability_id,
            runner_node_id=body.runner_node_id,
        )
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
def gate_get(gate_run_id: uuid.UUID) -> dict[str, Any]:
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
    _require("user", authorization)
    try:
        assert_dataset_id(body.dataset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    input_ref = json.dumps({"datasetId": body.dataset_id, "caseId": body.case_id})
    with get_conn() as conn:
        cap = conn.execute(
            "SELECT id, trust_domain_min FROM capability WHERE code = %s AND version = %s",
            (body.capability_code, body.capability_version),
        ).fetchone()
        if cap is None:
            raise HTTPException(status_code=404, detail="capability not found")
        user = conn.execute(
            "SELECT id FROM app_user WHERE id = %s",
            (SEED_ADMIN_ID,),
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=500, detail="seed admin missing")
        # trust_domain_min 스냅샷은 capability 행에서 SELECT
        created = conn.execute(
            """
            INSERT INTO task (
                user_id, capability_id, status, trust_domain,
                capability_trust_domain_min, input_ref, requested_agent_id
            )
            SELECT %(user_id)s, c.id, 'QUEUED', 'team',
                   c.trust_domain_min, %(input_ref)s, %(requested_agent_id)s::uuid
              FROM capability c
             WHERE c.id = %(capability_id)s
            RETURNING id, status, input_ref, capability_id, trust_domain, requested_agent_id
            """,
            {
                "user_id": str(user["id"]),
                "capability_id": str(cap["id"]),
                "input_ref": input_ref,
                "requested_agent_id": str(body.requested_agent_id) if body.requested_agent_id else None,
            },
        ).fetchone()
    return dict(created)


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
def nodes_liveness() -> dict[str, Any]:
    """어느 기기가 살아 있고 얼마나 바쁜지. 배정 근거를 사람이 볼 수 있게 한다."""
    with get_conn() as conn:
        return {"nodes": liveness(conn)}


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


@app.get("/v1/tasks/{task_id}")
def get_task(task_id: uuid.UUID) -> dict[str, Any]:
    with get_conn() as conn:
        task = conn.execute(
            "SELECT id, status, input_ref, result_ref, current_assignment_id, capability_id, trust_domain "
            "FROM task WHERE id = %s",
            (str(task_id),),
        ).fetchone()
        if task is None:
            raise HTTPException(status_code=404, detail="task not found")
        assignment = None
        if task["current_assignment_id"]:
            assignment = conn.execute(
                "SELECT id, status, agent_id, node_id, finished_at FROM assignment WHERE id = %s",
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

    with get_conn() as conn:
        row = complete_assignment(
            conn,
            assignment_id=assignment_id,
            weights_sha256=body.weights_sha256,
            label=body.label,
            confidence=body.confidence,
            dummy=body.dummy,
            duration_ms=body.duration_ms,
        )
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
