"""Core 워커 claim — INSERT … SELECT + FOR UPDATE SKIP LOCKED.

앱은 task(·node)만 고른다. 스냅샷·티어·도메인 판정은 DB FK가 한다.
"""

from __future__ import annotations

import uuid
from typing import Any

import psycopg

LOCK_SQL = """
SELECT id
  FROM task
 WHERE status = 'QUEUED'
   AND (%(task_id)s::uuid IS NULL OR id = %(task_id)s::uuid)
 ORDER BY created_at
   FOR UPDATE SKIP LOCKED
 LIMIT 1
"""

# 스냅샷 컬럼은 전부 조인 결과. 앱이 값을 계산해 넣지 않는다.
CLAIM_SQL = """
INSERT INTO assignment (
    task_id, agent_id, capability_id, node_id,
    task_trust_domain, node_trust_domain, capability_tier, node_tier_max,
    lease_expires_at, status)
SELECT t.id, acp.agent_id, c.id, n.id,
       t.trust_domain, n.trust_domain, c.compute_tier, n.compute_tier_max,
       now() + INTERVAL '60 seconds', 'LEASED'
  FROM task t
  JOIN capability c                ON c.id = t.capability_id
  JOIN agent_capability_passed acp ON acp.capability_id = c.id
                                  AND (t.requested_agent_id IS NULL
                                       OR acp.agent_id = t.requested_agent_id)
  JOIN agent_node_ready anr        ON anr.agent_id = acp.agent_id
  JOIN node n                      ON n.id = anr.node_id
                                  AND (%(node_id)s::uuid IS NULL OR n.id = %(node_id)s::uuid)
 WHERE t.id = %(task_id)s
 LIMIT 1
RETURNING id, task_id, agent_id, capability_id, node_id,
          task_trust_domain, node_trust_domain, capability_tier, node_tier_max,
          lease_expires_at, status
"""

MARK_SQL = """
UPDATE task
   SET status = 'ASSIGNED',
       current_assignment_id = %(assignment_id)s,
       updated_at = now()
 WHERE id = %(task_id)s
   AND status = 'QUEUED'
"""


def claim_next(
    conn: psycopg.Connection,
    *,
    task_id: uuid.UUID | None = None,
    node_id: uuid.UUID | None = None,
) -> dict[str, Any] | None:
    params = {
        "task_id": str(task_id) if task_id else None,
        "node_id": str(node_id) if node_id else None,
    }
    locked = conn.execute(LOCK_SQL, params).fetchone()
    if locked is None:
        return None

    locked_id = locked["id"]
    row = conn.execute(
        CLAIM_SQL,
        {"task_id": str(locked_id), "node_id": params["node_id"]},
    ).fetchone()
    if row is None:
        return None

    conn.execute(
        MARK_SQL,
        {"assignment_id": str(row["id"]), "task_id": str(locked_id)},
    )
    return dict(row)
