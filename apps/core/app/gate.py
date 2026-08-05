"""게이트 사슬 — INSERT … SELECT 만. 골든셋 추론은 여기서 하지 않는다."""

from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg
from psycopg import errors as pg_errors

START_SQL = """
INSERT INTO gate_run (
    agent_id, capability_id, runner_node_id, runner_is_gate_runner,
    status, golden_set_sha256
)
SELECT a.id, c.id, n.id, n.is_gate_runner,
       'RUNNING', c.golden_set_sha256
  FROM agent a
  JOIN capability c ON c.id = %(capability_id)s
  JOIN node n ON n.id = %(runner_node_id)s AND n.is_gate_runner = true
 WHERE a.id = %(agent_id)s
RETURNING id, agent_id, capability_id, runner_node_id, runner_is_gate_runner,
          status, golden_set_sha256, created_at
"""

FINISH_SQL = """
UPDATE gate_run
   SET status = %(status)s,
       golden_score = %(golden_score)s,
       cases_total = %(cases_total)s,
       cases_passed = %(cases_passed)s,
       result_summary = %(result_summary)s::jsonb,
       finished_at = now()
 WHERE id = %(gate_run_id)s
   AND status = 'RUNNING'
RETURNING id, agent_id, capability_id, runner_node_id, status,
          golden_score, cases_total, cases_passed, result_summary, finished_at
"""

MINT_PASSED_SQL = """
INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status)
SELECT gr.id, gr.agent_id, gr.capability_id, gr.status
  FROM gate_run gr
 WHERE gr.id = %(gate_run_id)s
   AND gr.status = 'PASSED'
ON CONFLICT (gate_run_id) DO NOTHING
"""

UPSERT_AC_PASSED_SQL = """
INSERT INTO agent_capability (
    agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at
)
SELECT grp.agent_id, grp.capability_id, 'PASSED', %(golden_score)s, grp.gate_run_id, now()
  FROM gate_run_passed grp
 WHERE grp.gate_run_id = %(gate_run_id)s
ON CONFLICT (agent_id, capability_id) DO UPDATE
   SET gate_status = 'PASSED',
       golden_score = EXCLUDED.golden_score,
       gate_run_id = EXCLUDED.gate_run_id,
       gated_at = EXCLUDED.gated_at
"""

MINT_ACP_SQL = """
INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status)
SELECT ac.agent_id, ac.capability_id, ac.gate_status
  FROM agent_capability ac
  JOIN gate_run_passed grp ON grp.agent_id = ac.agent_id
                          AND grp.capability_id = ac.capability_id
 WHERE grp.gate_run_id = %(gate_run_id)s
   AND ac.gate_status = 'PASSED'
ON CONFLICT (agent_id, capability_id) DO NOTHING
"""

UPSERT_AC_FAILED_SQL = """
INSERT INTO agent_capability (
    agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at
)
SELECT gr.agent_id, gr.capability_id, 'FAILED', %(golden_score)s, NULL, now()
  FROM gate_run gr
 WHERE gr.id = %(gate_run_id)s
   AND gr.status = 'FAILED'
ON CONFLICT (agent_id, capability_id) DO UPDATE
   SET gate_status = 'FAILED',
       golden_score = EXCLUDED.golden_score,
       gate_run_id = NULL,
       gated_at = EXCLUDED.gated_at
 WHERE agent_capability.gate_status <> 'PASSED'
"""


def start_gate_run(
    conn: psycopg.Connection,
    *,
    agent_id: uuid.UUID,
    capability_id: uuid.UUID,
    runner_node_id: uuid.UUID,
) -> dict[str, Any] | None:
    try:
        row = conn.execute(
            START_SQL,
            {
                "agent_id": str(agent_id),
                "capability_id": str(capability_id),
                "runner_node_id": str(runner_node_id),
            },
        ).fetchone()
    except pg_errors.ForeignKeyViolation:
        return None
    return dict(row) if row else None


def finish_gate_run(
    conn: psycopg.Connection,
    *,
    gate_run_id: uuid.UUID,
    status: str,
    golden_score: float | None,
    cases_total: int | None,
    cases_passed: int | None,
    dummy: bool,
    note: str | None,
) -> dict[str, Any] | None:
    if status not in ("PASSED", "FAILED", "ERROR"):
        raise ValueError("status must be PASSED, FAILED, or ERROR")

    summary = {"dummy": dummy, "scored_by": "api-record-only"}
    if note:
        summary["note"] = note

    row = conn.execute(
        FINISH_SQL,
        {
            "gate_run_id": str(gate_run_id),
            "status": status,
            "golden_score": golden_score,
            "cases_total": cases_total,
            "cases_passed": cases_passed,
            "result_summary": json.dumps(summary),
        },
    ).fetchone()
    if row is None:
        return None

    params = {"gate_run_id": str(gate_run_id), "golden_score": golden_score}
    if status == "PASSED":
        conn.execute(MINT_PASSED_SQL, params)
        conn.execute(UPSERT_AC_PASSED_SQL, params)
        conn.execute(MINT_ACP_SQL, params)
    elif status == "FAILED":
        conn.execute(UPSERT_AC_FAILED_SQL, params)

    out = dict(row)
    out["chain_minted"] = status == "PASSED"
    return out


def get_gate_run(conn: psycopg.Connection, gate_run_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, agent_id, capability_id, runner_node_id, runner_is_gate_runner, "
        "status, golden_set_sha256, golden_score, cases_total, cases_passed, "
        "result_summary, created_at, finished_at "
        "FROM gate_run WHERE id = %s",
        (str(gate_run_id),),
    ).fetchone()
    return dict(row) if row else None


def list_agent_capabilities(conn: psycopg.Connection, agent_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at "
        "FROM agent_capability WHERE agent_id = %s",
        (str(agent_id),),
    ).fetchall()
    return [dict(r) for r in rows]
