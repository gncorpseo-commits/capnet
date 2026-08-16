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
       -- arch 는 **Core 가** 말한다. Node 로컬 meta 로 정하면 게이트가 승인한 것과
       -- 실행한 것이 같다는 보장이 없다 (I1 · foreign-agent-isolation §2.1).
       ag.arch,
       aa.max_params,
       -- 전처리도 **Core 가 말한다** (0014 · I1 과 같은 이유). 이게 없으면 Node 는
       -- predict_image 기본값으로 떨어지고, 계약이 다른 값을 선언한 능력에서
       -- 「검증한 전처리」와 「실행한 전처리」가 갈라진다.
       c.input_schema -> 'preprocess' AS preprocess,
       t.input_ref, t.status AS task_status
  FROM assignment a
  JOIN agent ag ON ag.id = a.agent_id
  LEFT JOIN agent_arch aa ON aa.arch = ag.arch
  JOIN capability c ON c.id = a.capability_id
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
       -- 입력 바이트 보존기간(종결 후 7일)의 기준이다 (0011). updated_at 은 claim 회수에서도
       -- 갱신되므로 TTL 기준이 될 수 없다.
       finished_at = now(),
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


NODE_ASSIGNMENTS_SQL = """
SELECT a.id, a.task_id, a.agent_id, a.capability_id, a.node_id, a.status,
       a.lease_expires_at,
       ag.weights_uri, ag.weights_sha256, ag.weights_format,
       -- arch 는 **Core 가** 말한다. Node 로컬 meta 로 정하면 게이트가 승인한 것과
       -- 실행한 것이 같다는 보장이 없다 (I1 · foreign-agent-isolation §2.1).
       ag.arch,
       aa.max_params,
       -- 전처리도 **Core 가 말한다** (0014 · I1 과 같은 이유). 이게 없으면 Node 는
       -- predict_image 기본값으로 떨어지고, 계약이 다른 값을 선언한 능력에서
       -- 「검증한 전처리」와 「실행한 전처리」가 갈라진다.
       c.input_schema -> 'preprocess' AS preprocess,
       t.input_ref, t.status AS task_status
  FROM assignment a
  JOIN agent ag ON ag.id = a.agent_id
  LEFT JOIN agent_arch aa ON aa.arch = ag.arch
  JOIN capability c ON c.id = a.capability_id
  JOIN task t ON t.id = a.task_id
 WHERE a.node_id = %(node_id)s
   AND a.status = 'LEASED'
   AND a.lease_expires_at > now()
 ORDER BY a.lease_expires_at, a.id
"""


def node_assignments(conn: psycopg.Connection, node_id: uuid.UUID) -> list[dict[str, Any]]:
    """해당 Node에 **이미 배정된** 살아 있는 lease만 돌려준다.

    Node가 큐를 pull하는 것이 아니다 — 배치는 Core 워커가 결정하고,
    Node는 자기 몫만 가져간다. NAT 뒤 Node도 outbound로 동작할 수 있게 하는 경로다.
    """
    rows = conn.execute(NODE_ASSIGNMENTS_SQL, {"node_id": str(node_id)}).fetchall()
    return [dict(r) for r in rows]


def lease_detail(conn: psycopg.Connection, assignment_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        LEASE_DETAIL_SQL, {"assignment_id": str(assignment_id)}
    ).fetchone()
    return dict(row) if row else None


# 계약이 요구하는 출력 키. `required` 의 첫 항목을 쓴다 — 배열 하나를 내는 능력들이
# 실제로 그 모양이다(`vector` · `forecast`). 못 읽으면 `vector` 로 떨어진다.
OUTPUT_KEY_SQL = """
SELECT c.output_schema -> 'required' AS required
  FROM assignment a
  JOIN capability c ON c.id = a.capability_id
 WHERE a.id = %(assignment_id)s
"""


def _output_key(conn: psycopg.Connection, assignment_id: uuid.UUID) -> str:
    row = conn.execute(OUTPUT_KEY_SQL, {"assignment_id": str(assignment_id)}).fetchone()
    required = row["required"] if row else None
    if isinstance(required, list) and required and isinstance(required[0], str):
        return required[0]
    return "vector"


def complete_assignment(
    conn: psycopg.Connection,
    *,
    assignment_id: uuid.UUID,
    weights_sha256: str,
    label: str | None,
    vector: list[float] | None = None,
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

    # 낸 것만 적는다. 라벨이 없는 능력(임베딩)에 빈 라벨을 넣으면
    # 증적이 「라벨이 있었다」고 거짓말한다.
    result: dict[str, Any] = {"dummy": dummy, "weights_sha256": weights_sha256}
    if label is not None:
        result["label"] = label
    if confidence is not None:
        result["confidence"] = confidence
    if vector is not None:
        # **이름은 계약이 정한다.** Node 가 보낸 필드명을 그대로 쓰면, 게이트가
        # 검증한 출력(`forecast`)과 증적에 남는 출력(`vector`)이 갈라진다 —
        # 「승인한 것과 실행한 것이 같다」가 깨진다. Node 는 값만 보내고 이름은 여기서 붙인다.
        result[_output_key(conn, assignment_id)] = vector

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
