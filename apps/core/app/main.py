import json
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.allowlist import assert_dataset_id
from app.capability import create_capability, get_capability, list_capabilities
from app.claim import claim_next
from app.complete import complete_assignment, lease_detail, try_audit_succeeded
from app.const import SEED_ADMIN_ID
from app.db import get_conn
from app.gate import finish_gate_run, get_gate_run, list_agent_capabilities, start_gate_run
from app.registry import (
    bind_agent_node,
    create_agent,
    create_node,
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
    # S3: 실게이트는 필수. dummy plumbing은 생략 가능(넣으면 스냅샷과 일치해야 함).
    golden_set_sha256: str | None = None


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
    golden_set_ref: str
    golden_set_sha256: str
    golden_set_size: int
    golden_metrics: dict[str, Any]


class ClaimBody(BaseModel):
    task_id: uuid.UUID | None = None
    node_id: uuid.UUID | None = None


class CompleteBody(BaseModel):
    weights_sha256: str
    label: str
    confidence: float | None = None
    dummy: bool = True
    duration_ms: int | None = None


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
def capabilities_create(body: CapabilityCreate) -> dict[str, Any]:
    """런타임 Capability 등록. UNIQUE(code,version)·CHECK는 DB가 강제한다."""
    try:
        with get_conn() as conn:
            return create_capability(
                conn,
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
def agents_create(body: AgentCreate) -> dict[str, Any]:
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
            )
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
def agents_bind(agent_id: uuid.UUID, body: BindBody) -> dict[str, Any]:
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
def nodes_create(body: NodeCreate) -> dict[str, Any]:
    """관리자/Core 등록. Node 런타임이 trust_domain·tier를 주장하는 경로가 아니다."""
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


@app.post("/v1/internal/gate-runs")
def gate_start(body: GateStartBody) -> dict[str, Any]:
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
def gate_finish(gate_run_id: uuid.UUID, body: GateFinishBody) -> dict[str, Any]:
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
                golden_set_sha256=body.golden_set_sha256,
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


@app.post("/v1/tasks")
def create_task(body: TaskCreate) -> dict[str, Any]:
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
def claim(body: ClaimBody | None = None) -> dict[str, Any]:
    """Core 워커 전용. Node는 이 경로를 pull하지 않는다."""
    payload = body or ClaimBody()
    with get_conn() as conn:
        row = claim_next(conn, task_id=payload.task_id, node_id=payload.node_id)
        if row is None:
            raise HTTPException(status_code=409, detail="no claimable task or no compatible node")
        detail = lease_detail(conn, row["id"])
    if detail:
        row = {**row, **detail}
    return row


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
def complete(assignment_id: uuid.UUID, body: CompleteBody) -> dict[str, Any]:
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
