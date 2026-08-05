import json
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.allowlist import assert_dataset_id
from app.claim import claim_next
from app.db import get_conn

app = FastAPI(title="CapNet Core", version="0.1.0-w1")


class TaskCreate(BaseModel):
    dataset_id: str = Field(alias="datasetId")
    case_id: str = Field(alias="caseId")
    capability_code: str = "image.classify"
    capability_version: int = 1

    model_config = {"populate_by_name": True}


class ClaimBody(BaseModel):
    task_id: uuid.UUID | None = None
    node_id: uuid.UUID | None = None


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


@app.get("/v1/capabilities")
def list_capabilities() -> dict[str, Any]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, code, version, name, compute_tier, trust_domain_min, mvp_eligible "
            "FROM capability ORDER BY code, version"
        ).fetchall()
    return {"items": [dict(r) for r in rows]}


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
            ("00000000-0000-4000-8000-000000000001",),
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=500, detail="seed admin missing")
        # trust_domain_min 스냅샷은 capability 행에서 SELECT
        created = conn.execute(
            """
            INSERT INTO task (
                user_id, capability_id, status, trust_domain,
                capability_trust_domain_min, input_ref
            )
            SELECT %(user_id)s, c.id, 'QUEUED', 'team',
                   c.trust_domain_min, %(input_ref)s
              FROM capability c
             WHERE c.id = %(capability_id)s
            RETURNING id, status, input_ref, capability_id, trust_domain
            """,
            {
                "user_id": str(user["id"]),
                "capability_id": str(cap["id"]),
                "input_ref": input_ref,
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
    return row
