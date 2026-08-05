"""lease 완료 — 최소 증서만 필수로 닫는다.

완료 = assignment 종료 + agent.weights_sha256 일치 + (게이트 사슬은 assignment FK).
audit_log 삽입 실패는 관측 공백으로 남기고 Task를 FAILED로 뒤집지 않는다.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg

LEASE_DETAIL_SQL = """
SELECT a.id, a.task_id, a.agent_id, a.capability_id, a.node_id, a.status,
       a.lease_expires_at,
       ag.weights_uri, ag.weights_sha256, ag.weights_format,
       t.input_ref, t.status AS task_status
  FROM assignment a
  JOIN agent ag ON ag.id = a.agent_id
  JOIN task t ON t.id = a.task_id
 WHERE a.id = %(assignment_id)s
"""

COMPLETE_SQL = """
UPDATE assignment a
   SET status = 'SUCCEEDED',
       finished_at = now(),
       duration_ms = %(duration_ms)s
  FROM agent ag
 WHERE a.id = %(assignment_id)s
   AND a.status IN ('LEASED', 'RUNNING')
   AND ag.id = a.agent_id
   AND ag.weights_sha256 = %(weights_sha256)s
   AND ag.weights_format = 'safetensors'
RETURNING a.id, a.task_id, a.agent_id, a.node_id, a.status, ag.weights_sha256
"""

MARK_TASK_SQL = """
UPDATE task
   SET status = 'COMPLETED',
       result_ref = %(result_ref)s,
       updated_at = now()
 WHERE id = %(task_id)s
   AND status IN ('ASSIGNED', 'RUNNING')
   AND current_assignment_id = %(assignment_id)s
RETURNING id, status, result_ref, current_assignment_id
"""

AUDIT_SQL = """
INSERT INTO audit_log (task_id, actor_type, event, payload)
VALUES (%(task_id)s, 'core', 'assignment.succeeded', %(payload)s::jsonb)
"""


def try_audit_succeeded(
    conn: psycopg.Connection,
    *,
    task_id: uuid.UUID,
    assignment_id: uuid.UUID,
    weights_sha256: str,
    dummy: bool,
) -> None:
    """관측만. 실패해도 호출측에서 삼킨다."""
    conn.execute(
        AUDIT_SQL,
        {
            "task_id": str(task_id),
            "payload": json.dumps(
                {
                    "assignment_id": str(assignment_id),
                    "weights_sha256": weights_sha256,
                    "dummy": dummy,
                }
            ),
        },
    )


def lease_detail(conn: psycopg.Connection, assignment_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        LEASE_DETAIL_SQL, {"assignment_id": str(assignment_id)}
    ).fetchone()
    return dict(row) if row else None


def complete_assignment(
    conn: psycopg.Connection,
    *,
    assignment_id: uuid.UUID,
    weights_sha256: str,
    label: str,
    confidence: float | None,
    dummy: bool,
    duration_ms: int | None,
) -> dict[str, Any] | None:
    row = conn.execute(
        COMPLETE_SQL,
        {
            "assignment_id": str(assignment_id),
            "weights_sha256": weights_sha256,
            "duration_ms": duration_ms,
        },
    ).fetchone()
    if row is None:
        return None

    result = {
        "label": label,
        "dummy": dummy,
        "weights_sha256": weights_sha256,
    }
    if confidence is not None:
        result["confidence"] = confidence

    task = conn.execute(
        MARK_TASK_SQL,
        {
            "task_id": str(row["task_id"]),
            "assignment_id": str(assignment_id),
            "result_ref": json.dumps(result, separators=(",", ":")),
        },
    ).fetchone()
    if task is None:
        raise RuntimeError("assignment closed but task mark missed")

    out = dict(row)
    out["task_status"] = task["status"]
    out["result_ref"] = task["result_ref"]
    return out
