#!/usr/bin/env python3
"""안전 자세 조회면 (S2 · safety-chain G3). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

이 조회면의 유일한 실패 방식은 **거짓말**이다 — 실제 배정과 다른 그림을 보여주는 것.
그래서 「필드가 있다」가 아니라 **「claim 이 고르는 것과 같은가」** 를 본다.

1. 조회면이 **쓰지 않는다** — 호출 전후로 테이블 행 수가 같다
2. **시크릿이 나가지 않는다** — 증서 해시도 토큰도 응답에 없다 (prefix 만)
3. `routable_pairs` 가 **`claim` 의 후보와 일치한다** — 티어 비호환 기기는 0 이고,
   같은 조건으로 `claim` 도 그 기기를 고르지 않는다
4. 증서를 **발급·폐기하면** `credential_valid` 와 위험 표시가 따라간다
5. `accepts_task_domains` 가 **정책 행렬 그대로**다 — public 기기는 team 요청을 못 받는다
6. **강제가 꺼져 있으면 `ok=false`** — 데모 기본값에서 「안전하다」고 말하지 않는다
7. Agent 를 `DISABLED` 로 내리면 `routable_pairs` 가 **줄어든다** (claim 과 같은 조건)
8. 증서를 **폐기하면** `routable_pairs` 도 줄어든다 (SD-014 와 같은 조건)

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))
# claim 후보 대조가 목적이라 유휴 판정은 끈다 (세션 픽스처를 만들지 않는다).
os.environ.setdefault("REQUIRE_LIVE_NODE", "0")

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.claim import claim_next  # noqa: E402
from app.config import settings  # noqa: E402
from app.credential import issue_credential, revoke_credential  # noqa: E402
from app.safety import safety_posture  # noqa: E402

ADMIN = uuid.UUID("00000000-0000-4000-8000-000000000001")
CAP_TEAM = "00000000-0000-4000-8000-000000000010"  # image.classify@1 · M · min=team
AGENT = "00000000-0000-4000-8000-000000000020"
NODE_TEAM = uuid.UUID("00000000-0000-4000-8000-000000000030")  # team gate-runner · M

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def setup(conn: psycopg.Connection) -> None:
    """Agent 를 게이트 통과시키고 team Node 에 바인딩한다 — 라우팅 가능한 상태를 만든다.

    시드는 증서를 발급하지 않는다(그게 정상이다). 검사가 필요한 만큼만 세운다.
    """
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
        {"cap": CAP_TEAM, "runner": str(NODE_TEAM), "agent": AGENT},
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
        {"agent": AGENT, "cap": CAP_TEAM},
    )
    conn.execute(
        "INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen) "
        "SELECT a.id, %(node)s::uuid, 'BOUND', a.weights_sha256 FROM agent a WHERE a.id = %(agent)s "
        "ON CONFLICT (agent_id, node_id) DO NOTHING",
        {"node": str(NODE_TEAM), "agent": AGENT},
    )
    conn.execute(
        "INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256) "
        "SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen "
        "FROM agent_node an JOIN agent a ON a.id = an.agent_id "
        "AND a.weights_sha256 = an.weights_sha256_seen "
        "WHERE an.node_id = %(node)s::uuid AND an.agent_id = %(agent)s "
        "ON CONFLICT (agent_id, node_id) DO NOTHING",
        {"node": str(NODE_TEAM), "agent": AGENT},
    )


def posture(conn: psycopg.Connection, **kw: bool) -> dict:
    kw.setdefault("require_api_key", False)
    kw.setdefault("require_credential", False)
    return safety_posture(conn, **kw)  # type: ignore[arg-type]


def node_by_id(snap: dict, node_id) -> dict | None:
    return next((n for n in snap["nodes"] if str(n["node_id"]) == str(node_id)), None)


def main() -> int:
    print("안전 자세 조회면 (S2) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        if conn.execute("SELECT to_regclass('public.node_credential') AS t").fetchone()["t"] is None:
            print("node_credential 이 없다 — migrations/0007 미적용", file=sys.stderr)
            return 1
        conn.execute("SAVEPOINT s")
        setup(conn)

        # ── 1. 쓰지 않는다 ────────────────────────────────────────────────
        tables = ("node", "assignment", "task", "agent_capability_passed",
                  "node_credential", "node_session", "audit_log")

        def counts() -> dict[str, int]:
            return {
                t: conn.execute(f"SELECT count(*) AS c FROM {t}").fetchone()["c"]
                for t in tables
            }

        before = counts()
        snap = posture(conn)
        check(counts() == before, "조회면이 쓰지 않는다", f"{len(tables)}개 테이블 행 수 불변")
        check(len(snap["nodes"]) == before["node"],
              "등록된 기기가 전부 보인다", f"{len(snap['nodes'])}대")

        # ── 2. 시크릿이 나가지 않는다 ─────────────────────────────────────
        issued = issue_credential(conn, node_id=NODE_TEAM, issued_by=ADMIN, label="s2-check")
        snap = posture(conn)
        blob = json.dumps(snap, default=str)
        row = conn.execute(
            "SELECT key_prefix, secret_hash FROM node_credential WHERE id = %s", (issued["id"],)
        ).fetchone()
        check(bytes(row["secret_hash"]).hex() not in blob and "secret_hash" not in blob,
              "증서 해시가 응답에 없다")
        check(issued["secret"] not in blob, "발급 토큰이 응답에 없다")
        check(row["key_prefix"] in blob, "prefix 는 보인다 — 어느 증서인지는 답한다",
              row["key_prefix"])

        node = node_by_id(snap, NODE_TEAM)
        check(node["credential_valid"] and not any("증서 없음" in r for r in node["risks"]),
              "증서를 발급하면 그 위험 표시가 사라진다", f"risks={node['risks']}")
        # 시드 Agent 는 arch 가 NULL 이다 (0008 이전 세대). 조회면이 그걸 **드러내야** 한다 —
        # 게이트를 통과했으니 라우팅은 되는데 아키텍처는 선언돼 있지 않다 (G5).
        check(any("arch 미선언" in r for r in node["risks"]),
              "arch 미선언 Agent 가 라우팅 가능하면 그 기기에 표시된다",
              f"arch_unbound_routable={node['arch_unbound_routable']}")

        # ── 3. routable_pairs 가 claim 후보와 일치한다 ────────────────────
        check(node["routable_pairs"] == 1,
              "게이트 통과·바인딩된 기기는 routable_pairs = 1", str(node["routable_pairs"]))

        # 티어 비호환 기기 — M(rank 2) 능력은 S(rank 1) 기기에서 못 돈다.
        # 텍스트 정렬은 L < M < S 로 의도와 반대다 — 판정은 tier_compatible 이 한다 (절대규칙 3).
        weak_id = conn.execute(
            """
            INSERT INTO node (owner_id, name, device_type, provision_source,
                              trust_domain, compute_tier_max)
            VALUES (%s, 'safety-small', 'PHONE', 'team', 'team', 'S')
            RETURNING id
            """,
            (str(ADMIN),),
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen) "
            "SELECT a.id, %(node)s::uuid, 'BOUND', a.weights_sha256 FROM agent a WHERE a.id = %(agent)s",
            {"node": str(weak_id), "agent": AGENT},
        )
        conn.execute(
            "INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256) "
            "SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen "
            "FROM agent_node an JOIN agent a ON a.id = an.agent_id "
            "AND a.weights_sha256 = an.weights_sha256_seen "
            "WHERE an.node_id = %(node)s::uuid AND an.agent_id = %(agent)s",
            {"node": str(weak_id), "agent": AGENT},
        )
        weak = node_by_id(posture(conn), weak_id)
        check(weak["agents_ready"] == 1 and weak["routable_pairs"] == 0,
              "바인딩돼 있어도 티어가 안 맞으면 routable_pairs = 0",
              f"agents_ready={weak['agents_ready']} · M 능력 vs S 기기")

        def new_task() -> uuid.UUID:
            return conn.execute(
                """
                INSERT INTO task (user_id, capability_id, status, trust_domain,
                                  capability_trust_domain_min, input_ref)
                SELECT %s, c.id, 'QUEUED', 'team', c.trust_domain_min, '{"caseId":"case-001"}'
                  FROM capability c WHERE c.id = %s
                RETURNING id
                """,
                (str(ADMIN), CAP_TEAM),
            ).fetchone()["id"]

        # task 를 하나씩 따로 쓴다 — 첫 claim 이 성공하면 그 task 는 ASSIGNED 가 되어
        # 두 번째 claim 은 「기기가 아니라 task 때문에」 실패한다 (검사가 무의미해진다).
        check(claim_next(conn, task_id=new_task(), node_id=weak_id) is None,
              "claim 도 그 기기를 고르지 않는다", "조회면과 배정이 같은 답")
        check(claim_next(conn, task_id=new_task(), node_id=NODE_TEAM) is not None,
              "routable_pairs > 0 인 기기는 claim 이 고른다",
              "조회면이 「가능」이라 한 곳에서 실제로 배정된다")

        # ── 4. accepts_task_domains 가 정책 행렬 그대로다 ─────────────────
        pub_id = conn.execute(
            """
            INSERT INTO node (owner_id, name, device_type, provision_source,
                              trust_domain, compute_tier_max)
            VALUES (%s, 'safety-public', 'PC_GPU', 'public', 'public', 'S')
            RETURNING id
            """,
            (str(ADMIN),),
        ).fetchone()["id"]
        snap = posture(conn)
        pub = node_by_id(snap, pub_id)
        check(pub["accepts_task_domains"] == ["public"],
              "public 기기는 public 요청만 받는다", str(pub["accepts_task_domains"]))
        team = node_by_id(snap, NODE_TEAM)
        check(set(team["accepts_task_domains"]) == {"team", "tenant", "public"},
              "team 기기는 셋 다 받는다", str(team["accepts_task_domains"]))
        bd = snap["by_task_domain"]
        check(bd["team"]["nodes_eligible"] < bd["public"]["nodes_eligible"],
              "team 요청을 돌릴 수 있는 기기가 public 보다 적다",
              f"team {bd['team']['nodes_eligible']} < public {bd['public']['nodes_eligible']}")

        # ── 5. 강제 플래그가 응답에 반영된다 ──────────────────────────────
        off = posture(conn, require_api_key=False, require_credential=False)
        check(off["ok"] is False and any("SD-010" in w for w in off["warnings"]),
              "강제가 꺼져 있으면 ok=false", "데모 기본값에서 「안전하다」고 하지 않는다")
        on = posture(conn, require_api_key=True, require_credential=True)
        check(not any("SD-010" in w for w in on["warnings"]),
              "강제를 켜면 그 경고는 사라진다", f"경고 {len(on['warnings'])}건")

        # ── 6. Agent DISABLED 는 routable_pairs 에서 빠진다 ───────────────
        conn.execute("UPDATE agent SET status = 'DISABLED' WHERE id = %s", (AGENT,))
        after = node_by_id(posture(conn), NODE_TEAM)
        check(after["routable_pairs"] == 0 and after["agents_ready"] == 1,
              "DISABLED Agent 는 routable_pairs 에서 빠진다 (바인딩은 남는다)",
              f"ready={after['agents_ready']} · routable={after['routable_pairs']}")
        conn.execute("UPDATE agent SET status = 'ACTIVE' WHERE id = %s", (AGENT,))

        # ── 7. 증서 폐기가 반영된다 ───────────────────────────────────────
        back = node_by_id(posture(conn), NODE_TEAM)
        check(back["routable_pairs"] == 1, "복구하면 다시 라우팅 가능")
        revoke_credential(conn, node_id=NODE_TEAM, reason="s2-check")
        gone = node_by_id(posture(conn), NODE_TEAM)
        check(not gone["credential_valid"], "증서 폐기가 credential_valid 에 반영된다")
        check(any("증서 없음" in r for r in gone["risks"]),
              "증서 없는 기기에 위험 표시가 붙는다", "; ".join(gone["risks"])[:70])

        on_risk = node_by_id(
            posture(conn, require_credential=True), NODE_TEAM
        )["risks"]
        check(any("배정을 가져갈 수 없다" in r for r in on_risk),
              "강제가 켜져 있으면 같은 상태를 다르게 읽는다", "; ".join(on_risk)[:70])

        conn.execute("ROLLBACK TO SAVEPOINT s")
        conn.rollback()

    ok = sum(1 for r in results if r[0])
    print(f"\n{ok}/{len(results)} 통과")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
