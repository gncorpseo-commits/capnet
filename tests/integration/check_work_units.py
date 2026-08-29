#!/usr/bin/env python3
"""작업량 조회면 (P2-2 · PR-C · D1–D3). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

이 조회면의 실패 방식은 **두 시간을 뒤바꾸는 것**이다. Node 자기신고를 정본으로
읽으면 원가가 전송·대기·큐만큼 싸게 잡힌다. 그래서 관계 자체를 검사로 남긴다.

1. **관측 ≥ 자기신고** — Core 관측은 자기신고를 **포함하는** 구간이다.
   `hint_exceeds_observed` 가 0 이 아니면 실패다 (Proposal §3-5).
   **뒤집어서도 본다** — 자기신고를 관측보다 크게 만들면 감지기가 잡아야 한다
2. 조회면이 **쓰지 않는다** — 호출 전후로 테이블 행 수가 같다
3. `vram_mb_peak` · `energy_wh` 는 **미계측** — 실행을 완주해도 0 건이다 (D2)
4. 능력·Node 분해가 합계와 맞는다
5. 창 밖 배정은 빠진다 — `days` 가 실제로 자른다 (D3 · 기본 7일)
6. `days` 가 1..90 밖이면 거절한다

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))
# 유휴 판정은 끈다 — 세션 픽스처를 만들지 않는다 (check_ops_safety 와 같은 이유).
os.environ.setdefault("REQUIRE_LIVE_NODE", "0")

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.claim import claim_next  # noqa: E402
from app.complete import complete_assignment  # noqa: E402
from app.config import settings  # noqa: E402
from app.work_units import MAX_WINDOW_DAYS, work_units  # noqa: E402

ADMIN = uuid.UUID("00000000-0000-4000-8000-000000000001")
CAP_TEAM = "00000000-0000-4000-8000-000000000010"  # image.classify@1 · M · min=team
AGENT = "00000000-0000-4000-8000-000000000020"
NODE_TEAM = uuid.UUID("00000000-0000-4000-8000-000000000030")  # team gate-runner · M

# Node 가 보고할 자기신고(ms) 와, 배정이 살아 있던 시간(ms).
# 제품에서는 관측이 자기신고보다 크다 — 전송·대기·큐가 그 사이에 있다.
NODE_HINT_MS = 3
ELAPSED_MS = 1500

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def setup(conn: psycopg.Connection) -> None:
    """Agent 를 게이트 통과시키고 team Node 에 바인딩한다 — 배정 가능한 상태."""
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


def new_task(conn: psycopg.Connection) -> uuid.UUID:
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


def run_one(conn: psycopg.Connection) -> uuid.UUID:
    """실제 경로로 배정 하나를 완주시킨다 — claim(Core) → complete(Node 보고).

    **`now()` 는 트랜잭션 시각이다.** 검사가 한 트랜잭션 안에서 도는 탓에
    `assignment.created_at` 과 `finished_at` 이 **같은 값**이 되고 관측 시간이 0 ms 가 된다.
    제품 경로에서는 claim 과 complete 가 다른 트랜잭션이라 늘 벌어진다. 그 간격을
    여기서 만들어 준다 — 재는 방식이 아니라 **경과 시간만** 흉내낸다.
    """
    got = claim_next(conn, task_id=new_task(conn), node_id=NODE_TEAM)
    assert got is not None, "claim 이 배정하지 못했다 — 시드·바인딩 확인"
    assignment_id = got["assignment_id"] if "assignment_id" in got else got["id"]
    conn.execute(
        "UPDATE assignment SET created_at = created_at - make_interval(secs => %s) "
        "WHERE id = %s",
        (ELAPSED_MS / 1000.0, str(assignment_id)),
    )
    sha = conn.execute(
        "SELECT weights_sha256 FROM agent WHERE id = %s", (AGENT,)
    ).fetchone()["weights_sha256"]
    complete_assignment(
        conn,
        assignment_id=uuid.UUID(str(assignment_id)),
        weights_sha256=sha,
        label="forest",
        confidence=0.9,
        dummy=False,
        duration_ms=NODE_HINT_MS,
    )
    return uuid.UUID(str(assignment_id))


def main() -> int:
    print("작업량 조회면 (P2-2 · D1–D3) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        conn.execute("SAVEPOINT s")
        setup(conn)

        # ── 대조군: 아직 종결된 배정이 없다 ────────────────────────────────
        before = work_units(conn, days=7)
        base = before["totals"]["assignments"]

        assignment_id = run_one(conn)
        snap = work_units(conn, days=7)
        t = snap["totals"]

        check(t["assignments"] == base + 1, "완주한 배정이 창에 잡힌다",
              f"{base} → {t['assignments']}")
        check(t["succeeded"] >= 1, "SUCCEEDED 로 센다")

        # ── 1. 관측 ≥ 자기신고 (이 검사의 이유) ───────────────────────────
        check(t["hint_exceeds_observed"] == 0,
              "Node 자기신고가 Core 관측을 넘지 않는다",
              "관측은 자기신고를 포함하는 구간이다 (D1)")
        row = conn.execute(
            """
            SELECT duration_ms,
                   round(EXTRACT(EPOCH FROM (finished_at - created_at)) * 1000)::bigint AS observed
              FROM assignment WHERE id = %s
            """,
            (str(assignment_id),),
        ).fetchone()
        check(row["duration_ms"] == NODE_HINT_MS,
              "자기신고는 Node 가 보낸 값 그대로다", f"{row['duration_ms']} ms")
        check(row["observed"] >= row["duration_ms"],
              "같은 배정에서도 관측 ≥ 자기신고",
              f"관측 {row['observed']} ms ≥ 자기신고 {row['duration_ms']} ms")
        check(snap["measure"]["canonical"] == "core_observed_ms",
              "정본이 응답에 적혀 있다 (D1)")

        # 뒤집어 본다 — 감지기가 실제로 도는가. 값을 되돌린다.
        conn.execute(
            "UPDATE assignment SET duration_ms = %s WHERE id = %s",
            (ELAPSED_MS * 10, str(assignment_id)),
        )
        flipped = work_units(conn, days=7)
        check(flipped["totals"]["hint_exceeds_observed"] == 1,
              "자기신고가 관측을 넘으면 잡아낸다",
              "감지기가 놀고 있지 않다")
        check(any("시계나 보고가 어긋났다" in w for w in flipped["warnings"]),
              "그 사실을 warnings 로 말한다")
        check(flipped["ok"] is False, "그때 ok 는 false 다")
        conn.execute(
            "UPDATE assignment SET duration_ms = %s WHERE id = %s",
            (NODE_HINT_MS, str(assignment_id)),
        )

        # ── 2. 쓰지 않는다 ────────────────────────────────────────────────
        tables = ("assignment", "task", "audit_log", "node", "capability")

        def counts() -> dict[str, int]:
            return {
                tb: conn.execute(f"SELECT count(*) AS n FROM {tb}").fetchone()["n"]
                for tb in tables
            }

        c0 = counts()
        work_units(conn, days=7)
        work_units(conn, days=MAX_WINDOW_DAYS)
        check(counts() == c0, "조회가 아무것도 쓰지 않는다", str(c0))

        # ── 3. vram·energy 는 미계측이다 (D2) ─────────────────────────────
        check(t["vram_measured"] == 0 and t["energy_measured"] == 0,
              "vram_mb_peak · energy_wh 는 계측된 건이 없다",
              "RSS·추정으로 채우지 않는다")
        check("미계측" in snap["measure"]["vram_mb_peak"],
              "미계측이라고 응답에 적혀 있다")

        # ── 4. 분해가 합계와 맞는다 ───────────────────────────────────────
        by_cap = {f"{r['code']}@{r['version']}": r for r in snap["by_capability"]}
        check("image.classify@1" in by_cap, "능력별 분해에 실행한 능력이 있다",
              ", ".join(sorted(by_cap)))
        check(sum(r["assignments"] for r in snap["by_capability"]) == t["assignments"],
              "능력별 건수 합 = 전체 건수")
        node_ids = {str(r["node_id"]) for r in snap["by_node"]}
        check(str(NODE_TEAM) in node_ids, "Node 별 분해에 실행한 기기가 있다")
        check(sum(r["assignments"] for r in snap["by_node"]) == t["assignments"],
              "Node 별 건수 합 = 전체 건수")

        # ── 5. 창이 실제로 자른다 ─────────────────────────────────────────
        # created_at·finished_at 을 **함께** 8일 전으로 민다. 하나만 밀면 관측이 음수가 된다.
        conn.execute(
            "UPDATE assignment SET created_at = created_at - interval '8 days', "
            "finished_at = finished_at - interval '8 days' WHERE id = %s",
            (str(assignment_id),),
        )
        check(work_units(conn, days=7)["totals"]["assignments"] == base,
              "8일 전 배정은 기본 창(7일) 밖이다")
        check(work_units(conn, days=30)["totals"]["assignments"] == base + 1,
              "창을 넓히면 다시 잡힌다")

        # ── 6. days 범위 ──────────────────────────────────────────────────
        for bad in (0, -1, MAX_WINDOW_DAYS + 1):
            try:
                work_units(conn, days=bad)
            except ValueError:
                check(True, f"days={bad} 를 거절한다")
            else:
                check(False, f"days={bad} 를 통과시켰다")

        conn.execute("ROLLBACK TO SAVEPOINT s")
        conn.rollback()

    ok = sum(1 for r in results if r[0])
    print(f"\n{ok}/{len(results)} 통과")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
