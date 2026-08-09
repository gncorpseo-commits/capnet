"""게이트 사슬 — INSERT … SELECT 만. 추론은 Node/score_gate, 여기선 기록·검증만."""

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


def _load_cap_metrics(conn: psycopg.Connection, gate_run_id: uuid.UUID) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT c.golden_metrics, c.golden_set_size, c.golden_set_sha256 AS capability_sha256,
               gr.golden_set_sha256 AS gate_run_sha256
          FROM gate_run gr
          JOIN capability c ON c.id = gr.capability_id
         WHERE gr.id = %s
        """,
        (str(gate_run_id),),
    ).fetchone()
    if row is None:
        raise ValueError("gate-run not found")
    return dict(row)


def assert_golden_set_sha256(
    *,
    dummy: bool,
    provided: str | None,
    expected: str,
) -> None:
    """S3: 채점에 쓴 골든셋 해시가 gate_run 스냅샷과 다르면 거부."""
    if provided is None:
        if not dummy:
            raise ValueError(
                "real gate requires golden_set_sha256 matching the gate_run snapshot"
            )
        return
    if provided != expected:
        raise ValueError(
            f"golden_set_sha256 mismatch: provided={provided} expected={expected}"
        )


def assert_real_finish(
    *,
    status: str,
    dummy: bool,
    golden_score: float | None,
    cases_total: int | None,
    cases_passed: int | None,
    macro_f1: float | None,
    invalid_rate: float | None,
    min_per_class_recall: float | None,
    cap: dict[str, Any],
) -> None:
    """dummy=false PASSED는 골든 지표를 충족해야 한다. dummy plumbing과 섞지 않는다."""
    if dummy:
        return
    if cases_total is None or cases_passed is None or golden_score is None:
        raise ValueError("real gate requires golden_score, cases_total, cases_passed")
    if cases_total != cap["golden_set_size"]:
        raise ValueError(
            f"cases_total {cases_total} != golden_set_size {cap['golden_set_size']}"
        )
    expected_acc = cases_passed / cases_total if cases_total else 0.0
    if abs(expected_acc - float(golden_score)) > 1e-6:
        raise ValueError("golden_score must equal cases_passed / cases_total")
    if status != "PASSED":
        return
    if macro_f1 is None or invalid_rate is None:
        raise ValueError("real PASSED requires macro_f1 and invalid_rate")
    metrics = cap["golden_metrics"]
    if isinstance(metrics, str):
        metrics = json.loads(metrics)
    min_acc = float(metrics["min_accuracy"])
    min_f1 = float(metrics["min_macro_f1"])
    max_inv = float(metrics["max_invalid_rate"])
    if golden_score < min_acc or macro_f1 < min_f1 or invalid_rate > max_inv:
        raise ValueError(
            "real PASSED rejected: "
            f"acc={golden_score:.4f} f1={macro_f1:.4f} inv={invalid_rate:.4f} "
            f"need acc>={min_acc} f1>={min_f1} inv<={max_inv}"
        )
    # 계약이 선언했으면 증명 없이 PASSED 를 받지 않는다.
    # 이게 없으면 클래스를 통째로 버린 모델도 통과한다 (m=8 -> acc 0.80 / f1 0.711).
    min_recall_req = metrics.get("min_per_class_recall")
    if min_recall_req is not None:
        if min_per_class_recall is None:
            raise ValueError(
                "real PASSED requires min_per_class_recall "
                f"(capability declares >= {min_recall_req})"
            )
        if float(min_per_class_recall) < float(min_recall_req):
            raise ValueError(
                "real PASSED rejected: "
                f"min_per_class_recall={float(min_per_class_recall):.4f} "
                f"< {float(min_recall_req)}"
            )


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
    macro_f1: float | None = None,
    invalid_rate: float | None = None,
    min_per_class_recall: float | None = None,
    golden_set_sha256: str | None = None,
) -> dict[str, Any] | None:
    if status not in ("PASSED", "FAILED", "ERROR"):
        raise ValueError("status must be PASSED, FAILED, or ERROR")

    cap = _load_cap_metrics(conn, gate_run_id)
    expected_sha = str(cap["gate_run_sha256"])
    assert_golden_set_sha256(dummy=dummy, provided=golden_set_sha256, expected=expected_sha)
    assert_real_finish(
        status=status,
        dummy=dummy,
        golden_score=golden_score,
        cases_total=cases_total,
        cases_passed=cases_passed,
        macro_f1=macro_f1,
        invalid_rate=invalid_rate,
        min_per_class_recall=min_per_class_recall,
        cap=cap,
    )

    summary: dict[str, Any] = {
        "dummy": dummy,
        "scored_by": "plumbing-only" if dummy else "golden-set-v1",
        "golden_set_sha256": expected_sha,
    }
    if golden_set_sha256 is not None:
        summary["golden_set_sha256_provided"] = golden_set_sha256
    if macro_f1 is not None:
        summary["macro_f1"] = macro_f1
    if invalid_rate is not None:
        summary["invalid_rate"] = invalid_rate
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
