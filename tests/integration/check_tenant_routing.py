#!/usr/bin/env python3
"""tenant 신뢰 경계 실동작 (P2-1 · D19). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

`product-distribution.md` §2 의 유통 카피는 이렇게 말한다.

> 승인하지 않은 `trust_domain` 으로 **라우팅되지 않는다** (FK)

이 파일이 그 문장을 실행으로 바꾼다. 여섯 가지를 본다.

1. tenant Task 가 tenant Node 로 **배정된다** (양성 대조 — 없으면 나머지가 무의미하다)
2. tenant Task 는 **team Node 로도** 갈 수 있다 (team 이 더 사적 — privacy_rank 3 >= 2)
3. **team Task 는 tenant Node 로 못 간다** (더 낮은 격리로 내려보내지 않는다)
4. **tenant Task 는 team 전용 계약을 못 쓴다** (`image.classify@1` · min=team)
5. **public Task 는 tenant 계약을 못 쓴다** (min=tenant)
6. 거짓 스냅샷은 DB 가 거절한다 (tenant Node 인데 team 이라 적기)

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다.

환경: DATABASE_URL · PYTHONPATH=apps/core · REQUIRE_LIVE_NODE=0
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))
os.environ.setdefault("REQUIRE_LIVE_NODE", "0")

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.config import settings  # noqa: E402

ADMIN = "00000000-0000-4000-8000-000000000001"
CAP_TEAM = "00000000-0000-4000-8000-000000000010"  # image.classify@1 · min=team
CAP_TENANT = "00000000-0000-4000-8000-000000000011"  # image.classify@2 · min=tenant
AGENT = "00000000-0000-4000-8000-000000000020"
NODE_TEAM = "00000000-0000-4000-8000-000000000030"  # team gate-runner · M
NODE_TENANT = "00000000-0000-4000-8000-000000000050"  # tenant fleet · M

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def setup(conn) -> None:
    """Agent 를 두 계약 모두에 게이트 통과시키고 두 Node 에 바인딩한다 (전부 롤백된다)."""
    for cap in (CAP_TEAM, CAP_TENANT):
        gr = conn.execute(
            """
            INSERT INTO gate_run (agent_id, capability_id, runner_node_id, runner_is_gate_runner,
                                  status, golden_set_sha256, golden_score, cases_total,
                                  cases_passed, finished_at)
            SELECT a.id, c.id, n.id, n.is_gate_runner, 'PASSED', c.golden_set_sha256,
                   0.90, 40, 36, now()
              FROM agent a JOIN capability c ON c.id = %(cap)s
              JOIN node n ON n.id = %(runner)s AND n.is_gate_runner
             WHERE a.id = %(agent)s
            RETURNING id
            """,
            {"cap": cap, "runner": NODE_TEAM, "agent": AGENT},
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status) "
            "SELECT id, agent_id, capability_id, status FROM gate_run WHERE id = %s",
            (str(gr),),
        )
        conn.execute(
            "INSERT INTO agent_capability (agent_id, capability_id, gate_status, golden_score, "
            "gate_run_id, gated_at) SELECT agent_id, capability_id, 'PASSED', 0.90, gate_run_id, "
            "now() FROM gate_run_passed WHERE gate_run_id = %s "
            "ON CONFLICT (agent_id, capability_id) DO UPDATE SET gate_status='PASSED', "
            "gate_run_id = EXCLUDED.gate_run_id",
            (str(gr),),
        )
        conn.execute(
            "INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status) "
            "SELECT ac.agent_id, ac.capability_id, ac.gate_status FROM agent_capability ac "
            "WHERE ac.agent_id = %(agent)s AND ac.capability_id = %(cap)s "
            "ON CONFLICT (agent_id, capability_id) DO UPDATE "
            "SET revoked_at = NULL, revoked_reason = NULL, revoked_gate_run_id = NULL",
            {"agent": AGENT, "cap": cap},
        )

    for node in (NODE_TEAM, NODE_TENANT):
        conn.execute(
            "INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen) "
            "SELECT a.id, %(node)s::uuid, 'BOUND', a.weights_sha256 FROM agent a WHERE a.id = %(agent)s "
            "ON CONFLICT (agent_id, node_id) DO NOTHING",
            {"node": node, "agent": AGENT},
        )
        conn.execute(
            "INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256) "
            "SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen "
            "FROM agent_node an JOIN agent a ON a.id = an.agent_id "
            "AND a.weights_sha256 = an.weights_sha256_seen "
            "WHERE an.node_id = %(node)s::uuid AND an.agent_id = %(agent)s "
            "ON CONFLICT (agent_id, node_id) DO NOTHING",
            {"node": node, "agent": AGENT},
        )


def make_task(conn, cap: str, domain: str):
    """계약·도메인 조합으로 Task 를 만든다. domain_min_compatible 위반이면 예외가 난다."""
    return conn.execute(
        """
        INSERT INTO task (user_id, capability_id, status, trust_domain,
                          capability_trust_domain_min, input_ref)
        SELECT u.id, c.id, 'QUEUED', %(domain)s, c.trust_domain_min,
               '{"datasetId":"eurosat-rgb","caseId":"ic1-0001"}'
          FROM app_user u JOIN capability c ON c.id = %(cap)s
         WHERE u.id = %(admin)s
        RETURNING id
        """,
        {"cap": cap, "domain": domain, "admin": ADMIN},
    ).fetchone()["id"]


def claim_to(conn, task_id, node: str | None):
    from app.claim import claim_next
    import uuid as _uuid
    return claim_next(conn, task_id=task_id, node_id=_uuid.UUID(node) if node else None)


def main() -> int:
    print("tenant 신뢰 경계 실동작 (P2-1 · D19) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        exists = conn.execute(
            "SELECT count(*) AS n FROM capability WHERE code='image.classify' AND version=2"
        ).fetchone()["n"]
        if not exists:
            print("image.classify@2 가 없다 — migrations/0006 이 적용되지 않았다", file=sys.stderr)
            return 1
        n = conn.execute(
            "SELECT count(*) AS n FROM node WHERE id=%s AND trust_domain='tenant'", (NODE_TENANT,)
        ).fetchone()["n"]
        if not n:
            print("tenant Node 가 없다 — migrations/0006 이 적용되지 않았다", file=sys.stderr)
            return 1

        setup(conn)

        # 1. 양성 대조 — tenant Task → tenant Node
        conn.execute("SAVEPOINT s")
        tid = make_task(conn, CAP_TENANT, "tenant")
        got = claim_to(conn, tid, NODE_TENANT)
        check(got is not None, "tenant Task 가 tenant Node 로 배정된다 (양성 대조)")
        conn.execute("ROLLBACK TO SAVEPOINT s")

        # 2. tenant Task → team Node (team 이 더 사적이므로 허용)
        conn.execute("SAVEPOINT s")
        tid = make_task(conn, CAP_TENANT, "tenant")
        got = claim_to(conn, tid, NODE_TEAM)
        check(got is not None, "tenant Task 는 team Node 로도 갈 수 있다 (더 사적 → 허용)")
        conn.execute("ROLLBACK TO SAVEPOINT s")

        # 3. team Task → tenant Node (거부돼야 한다)
        conn.execute("SAVEPOINT s")
        tid = make_task(conn, CAP_TEAM, "team")
        got = claim_to(conn, tid, NODE_TENANT)
        check(got is None, "team Task 는 tenant Node 로 가지 않는다 (격리를 낮추지 않는다)")
        conn.execute("ROLLBACK TO SAVEPOINT s")

        # 4. tenant Task 가 team 전용 계약을 쓰려 하면 DB 가 막는다
        conn.execute("SAVEPOINT s")
        try:
            make_task(conn, CAP_TEAM, "tenant")
            conn.execute("ROLLBACK TO SAVEPOINT s")
            check(False, "tenant Task 는 team 전용 계약을 못 쓴다", "Task 가 만들어졌다")
        except psycopg.errors.IntegrityError as exc:
            name = exc.diag.constraint_name or ""
            conn.execute("ROLLBACK TO SAVEPOINT s")
            check("capability_trust_domain_min" in name or "domain_min" in name,
                  "tenant Task 는 team 전용 계약을 못 쓴다", name)

        # 5. public Task 가 tenant 계약을 쓰려 하면 막힌다
        conn.execute("SAVEPOINT s")
        try:
            make_task(conn, CAP_TENANT, "public")
            conn.execute("ROLLBACK TO SAVEPOINT s")
            check(False, "public Task 는 tenant 계약을 못 쓴다", "Task 가 만들어졌다")
        except psycopg.errors.IntegrityError as exc:
            name = exc.diag.constraint_name or ""
            conn.execute("ROLLBACK TO SAVEPOINT s")
            check("capability_trust_domain_min" in name or "domain_min" in name,
                  "public Task 는 tenant 계약을 못 쓴다", name)

        # 6. 거짓 스냅샷 — tenant Node 인데 team 이라 적기
        conn.execute("SAVEPOINT s")
        tid = make_task(conn, CAP_TENANT, "tenant")
        try:
            conn.execute(
                """
                INSERT INTO assignment (task_id, agent_id, capability_id, node_id,
                                        task_trust_domain, node_trust_domain,
                                        capability_tier, node_tier_max, lease_expires_at, status)
                VALUES (%(task)s, %(agent)s, %(cap)s, %(node)s, 'tenant', 'team', 'M', 'M',
                        now() + interval '60 seconds', 'LEASED')
                """,
                {"task": tid, "agent": AGENT, "cap": CAP_TENANT, "node": NODE_TENANT},
            )
            conn.execute("ROLLBACK TO SAVEPOINT s")
            check(False, "tenant Node 를 team 이라 적으면 거절된다", "통과했다")
        except psycopg.errors.IntegrityError as exc:
            name = exc.diag.constraint_name or ""
            conn.execute("ROLLBACK TO SAVEPOINT s")
            check("node_trust_domain" in name, "tenant Node 를 team 이라 적으면 거절된다", name)

        conn.rollback()

    failed = [r for r in results if not r[0]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        return 1
    print("승인하지 않은 trust_domain 으로 라우팅되지 않는다 — 실측으로 확인.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
