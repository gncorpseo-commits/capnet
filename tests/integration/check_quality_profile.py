#!/usr/bin/env python3
"""품질 프로파일 — 게이트 없는 Capability 라우팅 (D20 · migrations/0010). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

D18 은 골든셋 게이트를 **선택적 품질 프로파일**로 내렸다. `0010` 이 그것을 스키마에 반영했는데,
푸는 방식이 「제약 약화」가 아니라 「센티널 + 추가 제약」이다. 그 규약이 **기계로 지켜지는지**를 본다.

1. 기존 능력·게이트런은 전부 `golden` — 오늘 동작이 바뀌지 않았다
2. `none` 능력은 **센티널을 갖춰야만** 만들어진다
3. 센티널 규약 위반 3종은 `capability` 가 거절한다
4. `kind` 와 프로파일이 어긋나면 `gate_run` 이 거절한다
5. 계약 게이트런도 **team gate-runner** 만 만들 수 있다 (절대규칙 8 — 새 경로에도 그대로 걸린다)
6. 계약 게이트런은 골든 통계를 **가질 수 없다** (없는 채점의 점수가 증적에 남지 않게)
7. 정상 contract 사슬은 `agent_capability_passed` 까지 서서 **assignment FK 를 만족**한다

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.config import settings  # noqa: E402

ZERO_SHA = "0" * 64
SENTINEL_REF = "(none)"

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


CAP_INSERT = """
INSERT INTO capability (code, version, name, input_schema, output_schema, output_kind,
                        compute_tier, trust_domain_min, golden_set_ref, golden_set_sha256,
                        golden_set_size, golden_metrics, quality_profile)
VALUES (%(code)s, 1, 'probe', '{}'::jsonb, '{}'::jsonb, 'structured',
        'M', 'team', %(ref)s, %(sha)s, %(size)s, %(metrics)s::jsonb, %(profile)s)
RETURNING id
"""

# assignment · gate_run 은 INSERT … SELECT 만 (절대규칙 2).
GATE_RUN_INSERT = """
INSERT INTO gate_run (agent_id, capability_id, runner_node_id, runner_is_gate_runner, status,
                      golden_set_sha256, golden_score, kind, capability_quality_profile,
                      sample_input_id)
SELECT %(agent)s, %(cap)s, %(runner)s, %(is_runner)s, 'PASSED',
       %(sha)s, %(score)s, %(kind)s, %(profile)s, %(sample)s
RETURNING id
"""

# 계약 게이트런에는 검증 샘플이 필요하다 (0013). 없으면 다른 제약을 시험하기도 전에
# ck_gate_run_contract_needs_sample 이 먼저 걸려서 **엉뚱한 이유로 통과**한다.
SAMPLE_INSERT = """
INSERT INTO task_input (capability_id, sha256, byte_size, media_type, uploaded_by,
                        capability_max_input_bytes)
SELECT c.id, %(sha)s, 1024, 'image/jpeg', %(uploader)s, c.max_input_bytes
  FROM capability c WHERE c.id = %(cap)s
RETURNING id
"""


def rejected(conn: psycopg.Connection, sql: str, params: dict) -> str | None:
    """SQL 이 거절되면 제약 이름을, 통과하면 None 을 준다. 항상 롤백한다."""
    conn.execute("SAVEPOINT probe")
    try:
        conn.execute(sql, params)
    except (psycopg.errors.CheckViolation, psycopg.errors.ForeignKeyViolation) as exc:
        conn.execute("ROLLBACK TO SAVEPOINT probe")
        name = getattr(exc.diag, "constraint_name", None)
        return name or exc.__class__.__name__
    conn.execute("ROLLBACK TO SAVEPOINT probe")
    return None


def main() -> int:
    print("품질 프로파일 — 게이트 없는 Capability 도 라우팅된다 (D20) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        col = conn.execute(
            "SELECT count(*) AS n FROM information_schema.columns "
            "WHERE table_name = 'capability' AND column_name = 'quality_profile'"
        ).fetchone()["n"]
        if col == 0:
            print("quality_profile 이 없다 — migrations/0010 미적용", file=sys.stderr)
            return 1

        # 1. 오늘 동작은 바뀌지 않았다
        rows = conn.execute(
            "SELECT quality_profile AS p, count(*) AS n FROM capability GROUP BY 1"
        ).fetchall()
        by = {r["p"]: r["n"] for r in rows}
        check(by.get("none", 0) == 0 and by.get("golden", 0) > 0,
              "기존 능력은 전부 golden", str(by))
        kinds = conn.execute(
            "SELECT kind, count(*) AS n FROM gate_run GROUP BY 1"
        ).fetchall()
        check(all(r["kind"] == "golden" for r in kinds) if kinds else True,
              "기존 게이트런은 전부 golden", str({r["kind"]: r["n"] for r in kinds}))

        agent = conn.execute("SELECT id FROM agent LIMIT 1").fetchone()
        runner = conn.execute(
            "SELECT id FROM node WHERE is_gate_runner LIMIT 1"
        ).fetchone()
        plain = conn.execute(
            "SELECT id FROM node WHERE NOT is_gate_runner LIMIT 1"
        ).fetchone()
        golden_cap = conn.execute(
            "SELECT id FROM capability WHERE quality_profile = 'golden' LIMIT 1"
        ).fetchone()
        if not (agent and runner and golden_cap):
            print("시드가 부족하다 (agent · gate-runner · golden capability)", file=sys.stderr)
            return 1

        conn.execute("SAVEPOINT root")

        # 2. none 능력은 센티널을 갖춰야만 만들어진다
        none_cap = conn.execute(CAP_INSERT, {
            "code": "probe.ungated", "ref": SENTINEL_REF, "sha": ZERO_SHA,
            "size": 1, "metrics": "{}", "profile": "none",
        }).fetchone()["id"]
        check(none_cap is not None, "센티널 갖춘 none 능력이 생성된다")

        # 3. 센티널 규약 위반은 capability 가 거절한다
        for label, params in [
            ("none 인데 진짜 골든셋 참조",
             {"code": "probe.bad.a", "ref": "docs/spec/golden/real.md", "sha": "a" * 64,
              "size": 40, "metrics": "{}", "profile": "none"}),
            ("none 인데 size 가 1 이 아님",
             {"code": "probe.bad.b", "ref": SENTINEL_REF, "sha": ZERO_SHA,
              "size": 40, "metrics": "{}", "profile": "none"}),
            ("golden 인데 센티널 sha",
             {"code": "probe.bad.c", "ref": SENTINEL_REF, "sha": ZERO_SHA,
              "size": 1, "metrics": "{}", "profile": "golden"}),
            ("모르는 프로파일 값",
             {"code": "probe.bad.d", "ref": SENTINEL_REF, "sha": ZERO_SHA,
              "size": 1, "metrics": "{}", "profile": "maybe"}),
        ]:
            name = rejected(conn, CAP_INSERT, params)
            check(name is not None, f"거절: {label}", name or "통과해버렸다")

        # 계약 게이트런용 샘플. 이게 없으면 아래 검사들이 전부
        # ck_gate_run_contract_needs_sample 로 떨어져 의도한 제약을 시험하지 못한다.
        sample_id = conn.execute(SAMPLE_INSERT, {
            "cap": none_cap, "sha": "b" * 64, "uploader": "00000000-0000-4000-8000-000000000001",
        }).fetchone()
        sample_id = sample_id["id"] if sample_id else None
        check(sample_id is not None, "계약 검증 샘플 준비")

        # 4~6. gate_run 쪽 규약
        base = {"agent": agent["id"], "runner": runner["id"], "is_runner": True,
                "score": None, "sha": ZERO_SHA, "sample": sample_id}
        for label, over in [
            ("golden 능력에 contract 게이트런",
             {"cap": golden_cap["id"], "kind": "contract", "profile": "none"}),
            ("none 능력에 golden 게이트런",
             {"cap": none_cap, "kind": "golden", "profile": "golden", "sha": "a" * 64}),
            ("contract 인데 골든 점수가 있음",
             {"cap": none_cap, "kind": "contract", "profile": "none", "score": 0.99}),
            ("contract 인데 골든 sha 가 진짜",
             {"cap": none_cap, "kind": "contract", "profile": "none", "sha": "a" * 64}),
            ("모르는 kind",
             {"cap": none_cap, "kind": "handshake", "profile": "none"}),
        ]:
            name = rejected(conn, GATE_RUN_INSERT, {**base, **over})
            check(name is not None, f"거절: {label}", name or "통과해버렸다")

        # 0013 — 샘플 없는 계약 게이트런은 시작될 수 없다
        name = rejected(conn, GATE_RUN_INSERT, {
            **base, "cap": none_cap, "kind": "contract", "profile": "none", "sample": None,
        })
        check(name == "ck_gate_run_contract_needs_sample",
              "거절: 샘플 없는 계약 게이트런 (B2)", name or "통과해버렸다")

        # 5. 절대규칙 8 — 게이트러너가 아니면 계약 게이트런도 못 만든다
        if plain:
            name = rejected(conn, GATE_RUN_INSERT, {
                **base, "cap": none_cap, "kind": "contract", "profile": "none",
                "runner": plain["id"], "is_runner": False,
            })
            check(name is not None,
                  "거절: 게이트러너가 아닌 Node 의 계약 게이트런 (절대규칙 8)",
                  name or "통과해버렸다")
        else:
            check(False, "게이트러너 아닌 Node 가 시드에 없다 — 검사 불가")

        # 7. 정상 contract 사슬 → acp 까지 선다 (= assignment FK 만족)
        gr = conn.execute(GATE_RUN_INSERT, {
            **base, "cap": none_cap, "kind": "contract", "profile": "none",
        }).fetchone()["id"]
        conn.execute(
            "INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status) "
            "VALUES (%s, %s, %s, 'PASSED')", (gr, agent["id"], none_cap),
        )
        conn.execute(
            "INSERT INTO agent_capability (agent_id, capability_id, gate_status, gate_run_id, gated_at) "
            "VALUES (%s, %s, 'PASSED', %s, now())", (agent["id"], none_cap, gr),
        )
        conn.execute(
            "INSERT INTO agent_capability_passed (agent_id, capability_id) VALUES (%s, %s)",
            (agent["id"], none_cap),
        )
        row = conn.execute("""
            SELECT c.quality_profile, g.kind
              FROM agent_capability_passed acp
              JOIN capability c ON c.id = acp.capability_id
              JOIN agent_capability ac
                ON ac.agent_id = acp.agent_id AND ac.capability_id = acp.capability_id
              JOIN gate_run g ON g.id = ac.gate_run_id
             WHERE acp.capability_id = %s
        """, (none_cap,)).fetchone()
        check(row is not None and row["quality_profile"] == "none" and row["kind"] == "contract",
              "게이트 없는 능력이 라우팅 증서까지 선다",
              f"profile={row['quality_profile']} kind={row['kind']}" if row else "증서 없음")

        # 프로파일을 나중에 바꿔 증적을 뒤엎을 수 없다.
        # 센티널까지 같이 바꿔 CHECK 를 통과시켜도 **복합 FK** 가 막아야 한다 —
        # 그래야 「이 증서가 무엇을 근거로 발급됐는가」가 사후에 조작되지 않는다.
        name = rejected(conn, """
            UPDATE capability
               SET quality_profile   = 'golden',
                   golden_set_ref    = 'docs/spec/golden/real.md',
                   golden_set_sha256 = repeat('a', 64),
                   golden_set_size   = 40
             WHERE id = %(id)s
        """, {"id": none_cap})
        check(name == "gate_run_capability_profile_fkey",
              "증적이 달린 능력의 프로파일은 복합 FK 가 막는다", name or "통과해버렸다")

        conn.rollback()
        left = conn.execute(
            "SELECT count(*) AS n FROM capability WHERE code LIKE 'probe.%'"
        ).fetchone()["n"]
        check(left == 0, "격리: 시험 능력이 롤백됐다")

    failed = [r for r in results if not r[0]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        return 1
    print("게이트는 선택이다 — 그러나 «없음» 도 DB 가 검사하는 규약이다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
