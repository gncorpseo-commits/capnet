"""Core 워커 claim — INSERT … SELECT + FOR UPDATE SKIP LOCKED.

앱은 task(·node)만 고른다. 스냅샷·티어·도메인 판정은 DB FK가 한다.
"""

from __future__ import annotations

import os
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
                                  -- 폐기된 증서로는 배정하지 않는다 (SD-014 · 0004)
                                  AND acp.revoked_at IS NULL
  -- agent.status 는 스키마에 선언돼 있었지만 claim 이 보지 않았다 (SD-014).
  -- 선언만 있고 강제가 없으면 DISABLED 가 아무 의미도 없다.
  JOIN agent ag                    ON ag.id = acp.agent_id AND ag.status = 'ACTIVE'
  JOIN agent_node_ready anr        ON anr.agent_id = acp.agent_id
  JOIN node n                      ON n.id = anr.node_id
                                  AND (%(node_id)s::uuid IS NULL OR n.id = %(node_id)s::uuid)
  -- 호환 행렬을 **후보 단계에서** 본다 (P2-1 에서 발견).
  -- 이 조인이 없으면 claim 이 호환 불가 조합을 고르고 INSERT 에서 FK 가 거절한다.
  -- 보장은 지켜지지만(라우팅은 안 된다) 가용성이 깨진다 — 호환 Node 가 있는데도
  -- 예외가 나서 Task 가 배정되지 않는다. tenant Node 가 함대에 들어오는 순간 실제로 재현된다.
  -- FK 는 그대로 최후 방어로 남는다 (판정은 제약이 한다).
  JOIN domain_compatible dc        ON dc.task_domain = t.trust_domain
                                  AND dc.node_domain = n.trust_domain
  JOIN tier_compatible tc          ON tc.capability_tier = c.compute_tier
                                  AND tc.node_tier_max = n.compute_tier_max
  -- 유휴 판정: 살아 있고(heartbeat 신선) 일을 받을 수 있는 기기만 후보다.
  -- 세션 기록이 아직 없는 기기는 %(require_live)s = false 일 때만 허용한다(초기 기동·데모).
  LEFT JOIN node_liveness nl       ON nl.node_id = n.id
 WHERE t.id = %(task_id)s
   AND (
        NOT %(require_live)s
        OR (nl.is_fresh AND nl.availability IN ('AVAILABLE', 'BUSY'))
       )
   AND (nl.availability IS DISTINCT FROM 'DRAINING')
   AND (nl.availability IS DISTINCT FROM 'OFFLINE')
 -- 덜 바쁜 기기 먼저. 동률이면 UUID 순으로 고정해 재현성을 지킨다.
 ORDER BY (SELECT count(*) FROM assignment a2
            WHERE a2.node_id = n.id AND a2.status = 'LEASED'
              AND a2.lease_expires_at > now()),
          acp.agent_id, n.id
 LIMIT 1
RETURNING id, task_id, agent_id, capability_id, node_id,
          task_trust_domain, node_trust_domain, capability_tier, node_tier_max,
          lease_expires_at, status
"""

RECLAIM_SQL = """
-- 만료된 lease 회수. 이게 없으면 배정 후 기기가 죽은 작업이 영구히 갇힌다
-- (Node 는 만료 배정을 가져가지 않고, 워커는 QUEUED 만 본다).
WITH dead AS (
    UPDATE assignment a
       SET status = 'EXPIRED', finished_at = now()
      FROM task t
     WHERE a.task_id = t.id
       AND a.status = 'LEASED'
       AND a.lease_expires_at <= now()
    RETURNING a.id, a.task_id
)
UPDATE task t
   SET status = 'QUEUED', current_assignment_id = NULL, updated_at = now()
  FROM dead
 WHERE t.id = dead.task_id AND t.status = 'ASSIGNED'
RETURNING t.id AS task_id, dead.id AS assignment_id
"""

MARK_SQL = """
UPDATE task
   SET status = 'ASSIGNED',
       current_assignment_id = %(assignment_id)s,
       updated_at = now()
 WHERE id = %(task_id)s
   AND status = 'QUEUED'
"""


def reclaim_expired(conn: psycopg.Connection) -> list[dict[str, Any]]:
    """만료된 lease 를 회수해 task 를 다시 QUEUED 로 되돌린다."""
    rows = conn.execute(RECLAIM_SQL).fetchall()
    return [dict(r) for r in rows]


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
    require_live = os.environ.get("REQUIRE_LIVE_NODE", "1") != "0"
    locked = conn.execute(LOCK_SQL, params).fetchone()
    if locked is None:
        return None

    locked_id = locked["id"]
    row = conn.execute(
        CLAIM_SQL,
        {
            "task_id": str(locked_id),
            "node_id": params["node_id"],
            "require_live": require_live,
        },
    ).fetchone()
    if row is None:
        return None

    conn.execute(
        MARK_SQL,
        {"assignment_id": str(row["id"]), "task_id": str(locked_id)},
    )
    return dict(row)
