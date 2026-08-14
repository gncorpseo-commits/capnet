"""Core 워커 claim — INSERT … SELECT + FOR UPDATE SKIP LOCKED.

앱은 task(·node)만 고른다. 스냅샷·티어·도메인 판정은 DB FK가 한다.
"""

from __future__ import annotations

import json
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
    task_org_id, node_org_id,
    lease_expires_at, status, attempt_no, capability_max_attempts)
SELECT t.id, acp.agent_id, c.id, n.id,
       t.trust_domain, n.trust_domain, c.compute_tier, n.compute_tier_max,
       -- 조직 스냅샷 (0017 · D24). 판정은 ck_assignment_org 와 복합 FK 가 한다.
       t.org_id, n.org_id,
       now() + INTERVAL '60 seconds', 'LEASED',
       -- 몇 번째 시도인가 (0015). 세지 않으면 「조용한 무한 재시도」가 된다.
       (SELECT count(*) + 1 FROM assignment a2 WHERE a2.task_id = t.id),
       c.max_attempts
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
   -- 조직 경계를 **후보 단계에서** 본다 (0017 · D24). 이 조건이 없으면 claim 이
   -- 다른 조직 기기를 고르고 INSERT 에서 CHECK 가 거절한다 — 보장은 지켜지지만
   -- 가용성이 깨진다(호환 기기가 있는데도 배정되지 않는다). P2-1 에서 겪은 것과 같은 모양이다.
   -- NULL 인 기기는 팀 운영 공용이므로 모든 조직을 받는다.
   AND (n.org_id IS NULL OR n.org_id IS NOT DISTINCT FROM t.org_id)
   AND (nl.availability IS DISTINCT FROM 'DRAINING')
   AND (nl.availability IS DISTINCT FROM 'OFFLINE')
   -- 시도 상한을 다 쓴 task 는 고르지 않는다 (0015). 워커가 FAILED 로 종결한다.
   -- DB 의 ck_assignment_attempt_within_cap 이 마지막 방어선이지만, 여기서 걸러야
   -- 「상한 초과 INSERT 가 거절돼 claim 이 조용히 실패」하는 상태가 안 된다.
   AND (SELECT count(*) FROM assignment a3 WHERE a3.task_id = t.id) < c.max_attempts
 -- 덜 바쁜 기기 먼저. 동률이면 UUID 순으로 고정해 재현성을 지킨다.
 ORDER BY (SELECT count(*) FROM assignment a2
            WHERE a2.node_id = n.id AND a2.status = 'LEASED'
              AND a2.lease_expires_at > now()),
          acp.agent_id, n.id
 LIMIT 1
RETURNING id, task_id, agent_id, capability_id, node_id,
          task_trust_domain, node_trust_domain, capability_tier, node_tier_max,
          task_org_id, node_org_id, lease_expires_at, status
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


# ── 실패 보고 · 상한 소진 종결 (0015) ─────────────────────────────────────

FAIL_ASSIGNMENT_SQL = """
UPDATE assignment
   SET status = 'FAILED', finished_at = now()
 WHERE id = %(assignment_id)s
   AND node_id = %(node_id)s
   AND status IN ('LEASED', 'RUNNING')
RETURNING id, task_id, attempt_no, capability_max_attempts
"""

# 실패한 배정의 task 는 다시 QUEUED 로 — **다른 기기가 시도할 수 있어야 한다.**
# 상한을 다 썼는지는 여기서 보지 않는다. claim 이 고르지 않고, 워커가 종결한다.
REQUEUE_SQL = """
UPDATE task
   SET status = 'QUEUED', current_assignment_id = NULL, updated_at = now()
 WHERE id = %(task_id)s
   AND status = 'ASSIGNED'
   AND current_assignment_id = %(assignment_id)s
RETURNING id, status
"""

FAIL_AUDIT_SQL = """
INSERT INTO audit_log (task_id, actor_type, event, payload)
VALUES (%(task_id)s, 'node', 'assignment.failed', %(payload)s::jsonb)
"""

# 상한을 다 쓴 미완료 task 를 종결한다. 정책은 뷰가 갖는다 (0015).
EXHAUSTED_SQL = """
UPDATE task t
   SET status = 'FAILED', finished_at = now(), updated_at = now()
  FROM task_attempts_exhausted x
 WHERE t.id = x.task_id
RETURNING t.id, x.capability_code, x.attempts, x.max_attempts
"""


def fail_assignment(
    conn: psycopg.Connection,
    *,
    assignment_id: uuid.UUID,
    node_id: uuid.UUID,
    reason: str,
) -> dict[str, Any] | None:
    """Node 가 실행에 실패했다고 보고한다.

    이게 없으면 실패가 **lease 만료(60초)로만** 드러난다 — 그 동안 Node 는 같은 배정을
    계속 재시도하고, 로그에만 쌓인다. 보고하면 즉시 FAILED 로 남고 시도 횟수에 반영된다.
    """
    row = conn.execute(
        FAIL_ASSIGNMENT_SQL,
        {"assignment_id": str(assignment_id), "node_id": str(node_id)},
    ).fetchone()
    if row is None:
        return None
    out = dict(row)
    conn.execute(
        FAIL_AUDIT_SQL,
        {
            "task_id": str(out["task_id"]),
            "payload": json.dumps(
                {
                    "assignment_id": str(out["id"]),
                    "node_id": str(node_id),
                    "attempt_no": out["attempt_no"],
                    "max_attempts": out["capability_max_attempts"],
                    # 이유는 Node 가 준 것이다. 길면 자른다 — 증적이지 로그가 아니다.
                    "reason": (reason or "")[:500],
                }
            ),
        },
    )
    conn.execute(
        REQUEUE_SQL,
        {"task_id": str(out["task_id"]), "assignment_id": str(out["id"])},
    )
    return out


def fail_exhausted_tasks(conn: psycopg.Connection) -> list[dict[str, Any]]:
    """시도 상한을 다 쓴 task 를 FAILED 로 종결한다.

    `finished_at` 을 박으므로 입력 바이트 TTL(종결 후 7일)도 여기서 시작된다 (0011).
    """
    return [dict(r) for r in conn.execute(EXHAUSTED_SQL).fetchall()]
