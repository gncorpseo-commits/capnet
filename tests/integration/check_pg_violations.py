#!/usr/bin/env python3
"""PG 위반 14종 자동 회귀 (M25 · `docs/error/pg-violations.md`). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 왜 있나

이 프로젝트의 중심 주장은 **「판정은 앱 `if` 가 아니라 PostgreSQL 제약이 한다」**이다.
그 증거가 지금까지 두 가지였다.

- `docs/error/pg-violations.md` — 14종 **수동 실측 기록**. 자동 검증이 아니다
- `scripts/demo_violations.sql` — 6종. `ON_ERROR_STOP=1` 과 함께 실패는 하지만 CI 에 없다

여기서 셋을 메운다.

1. **14종 전부**를 시도한다 (6종 → 14종)
2. **어느 제약이 거절했는지**까지 본다. 엉뚱한 제약이 거절해도 「거절됐다」로 통과하면
   그 시험은 제약을 지키는 게 아니라 우연을 지키는 것이다
3. **양성 대조** — 정상 할당은 반드시 **통과**해야 한다. 이게 없으면 스키마가 통째로
   망가져 모든 INSERT 가 실패해도 14/14 「거절됨」으로 초록이 뜬다

## 격리

전부 하나의 트랜잭션 안에서 SAVEPOINT 로 돌리고 마지막에 ROLLBACK 한다. seed 를 더럽히지 않는다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.config import settings  # noqa: E402

# seed 고정 UUID
ADMIN = "00000000-0000-4000-8000-000000000001"
CAP_M = "00000000-0000-4000-8000-000000000010"  # image.classify · M · team
AGENT = "00000000-0000-4000-8000-000000000020"  # seed-agent (사슬은 있으나 SD-015 로 라우팅 증서 없음)
RUNNER = "00000000-0000-4000-8000-000000000030"  # team gate-runner · M
GATE_RUN = "00000000-0000-4000-8000-000000000031"
TASK = "00000000-0000-4000-8000-000000000040"

# 이 시험에서만 쓰는 픽스처 (전부 롤백된다)
NODE_PUBLIC_M = "00000000-0000-4000-8000-0000000000a1"
NODE_TEAM_S = "00000000-0000-4000-8000-0000000000a2"
AGENT_UNGATED = "00000000-0000-4000-8000-0000000000b1"
CAP_L = "00000000-0000-4000-8000-0000000000c1"
TASK_L = "00000000-0000-4000-8000-0000000000d2"
GATE_L = "00000000-0000-4000-8000-0000000000e1"

SETUP = f"""
INSERT INTO node (id, owner_id, name, device_type, provision_source,
                  trust_domain, compute_tier_max, is_gate_runner)
VALUES ('{NODE_PUBLIC_M}', '{ADMIN}', 'v-public-m', 'SERVER', 'public', 'public', 'M', false),
       ('{NODE_TEAM_S}',   '{ADMIN}', 'v-team-s',   'PHONE',  'team',   'team',   'S', false);

INSERT INTO agent (id, owner_id, name, version, status, manifest_hash,
                   weights_format, weights_uri, weights_sha256)
VALUES ('{AGENT_UNGATED}', '{ADMIN}', 'v-ungated', '0.0.0', 'ACTIVE', 'v',
        'safetensors', 'file:///tmp/x.safetensors', '{"a" * 64}');

INSERT INTO capability (id, code, version, name, input_schema, output_schema, output_kind,
                        compute_tier, trust_domain_min, mvp_eligible,
                        golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics)
VALUES ('{CAP_L}', 'v.heavy', 1, 'L tier probe', '{{}}'::jsonb, '{{}}'::jsonb,
        'closed_set_labels', 'L', 'team', false, 'x', '{"b" * 64}', 1,
        '{{"primary_metric":"accuracy","min_accuracy":0.99}}'::jsonb);

-- 3번(L→S)을 **정직한** 스냅샷으로 시험하려면 L 계약의 사슬이 온전해야 한다.
-- 스냅샷을 거짓으로 적으면 capability FK 가 먼저 걸려 5번과 같은 것을 시험하게 된다.
INSERT INTO gate_run (id, agent_id, capability_id, runner_node_id, runner_is_gate_runner,
                      status, golden_set_sha256, golden_score, cases_total, cases_passed, finished_at)
SELECT '{GATE_L}', a.id, c.id, n.id, n.is_gate_runner, 'PASSED', c.golden_set_sha256,
       0.99, 1, 1, now()
  FROM agent a JOIN capability c ON c.id = '{CAP_L}'
  JOIN node n ON n.id = '{RUNNER}' AND n.is_gate_runner
 WHERE a.id = '{AGENT}';

INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status)
SELECT gr.id, gr.agent_id, gr.capability_id, gr.status FROM gate_run gr WHERE gr.id = '{GATE_L}';

INSERT INTO agent_capability (agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at)
SELECT grp.agent_id, grp.capability_id, 'PASSED', 0.99, grp.gate_run_id, now()
  FROM gate_run_passed grp WHERE grp.gate_run_id = '{GATE_L}';

INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status)
SELECT ac.agent_id, ac.capability_id, ac.gate_status
  FROM agent_capability ac WHERE ac.capability_id = '{CAP_L}';

INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen)
SELECT a.id, '{NODE_TEAM_S}'::uuid, 'BOUND', a.weights_sha256 FROM agent a WHERE a.id = '{AGENT}';
INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256)
SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen
  FROM agent_node an JOIN agent a ON a.id = an.agent_id AND a.weights_sha256 = an.weights_sha256_seen
 WHERE an.node_id = '{NODE_TEAM_S}';

INSERT INTO task (id, user_id, capability_id, status, trust_domain,
                  capability_trust_domain_min, input_ref)
SELECT '{TASK_L}', u.id, c.id, 'QUEUED', 'team', c.trust_domain_min,
       '{{"datasetId":"eurosat-rgb","caseId":"v-L"}}'
  FROM app_user u JOIN capability c ON c.id = '{CAP_L}' WHERE u.id = '{ADMIN}';

-- seed 는 더 이상 라우팅 증서를 발급하지 않는다 (SD-015). 시험이 쓸 증서를 스스로 만든다.
-- 양성 대조가 성립하려면 CAP_M 에 라우팅 가능한 Agent 가 하나는 있어야 한다.
-- 앞선 시험(check_revocation)이 같은 DB 에 증서를 남겼을 수 있으므로 멱등하게 쓴다.
-- 폐기 상태로 남아 있으면 되살린다 — 전부 마지막에 ROLLBACK 된다.
INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status)
SELECT ac.agent_id, ac.capability_id, ac.gate_status
  FROM agent_capability ac
 WHERE ac.agent_id = '{AGENT}' AND ac.capability_id = '{CAP_M}' AND ac.gate_status = 'PASSED'
ON CONFLICT (agent_id, capability_id) DO UPDATE
   SET revoked_at = NULL, revoked_reason = NULL, revoked_gate_run_id = NULL;
"""

# 할당 한 건을 만드는 공용 조각 — 스냅샷 값을 인자로 바꿔가며 위반을 만든다.
ASSIGN = """
INSERT INTO assignment (task_id, agent_id, capability_id, node_id,
                        task_trust_domain, node_trust_domain,
                        capability_tier, node_tier_max, lease_expires_at, status)
VALUES (%(task)s, %(agent)s, %(cap)s, %(node)s, %(td)s, %(nd)s, %(ct)s, %(nt)s,
        now() + interval '60 seconds', 'LEASED')
"""

# psycopg 는 파라미터가 있는 다중 문장을 한 번에 못 받는다. 두 단계로 나눈다.
BIND_1 = """
INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen)
SELECT a.id, %(node)s::uuid, 'BOUND', a.weights_sha256 FROM agent a WHERE a.id = %(agent)s
"""

BIND_2 = """
INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256)
SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen
  FROM agent_node an JOIN agent a ON a.id = an.agent_id
                                 AND a.weights_sha256 = an.weights_sha256_seen
 WHERE an.node_id = %(node)s::uuid AND an.agent_id = %(agent)s
"""


def a(**over):
    """정상 할당 파라미터에 위반을 얹는다."""
    base = {
        "task": TASK, "agent": AGENT, "cap": CAP_M, "node": RUNNER,
        "td": "team", "nd": "team", "ct": "M", "nt": "M",
    }
    base.update(over)
    return base


# (번호, 설명, [(sql, params), ...], 기대 제약 이름 조각)
# 기대 조각은 **어느 제약이** 거절해야 하는지다. 다른 제약이 거절하면 실패로 본다.
CASES: list[tuple[int, str, list[tuple[str, dict]], str]] = [
    (1, "게이트 미통과 Agent 로 할당",
     [(ASSIGN, a(agent=AGENT_UNGATED))],
     "agent_id_capability_id_fkey"),

    (2, "team Task → public Node",
     [(BIND_1, {"node": NODE_PUBLIC_M, "agent": AGENT}),
      (BIND_2, {"node": NODE_PUBLIC_M, "agent": AGENT}),
      (ASSIGN, a(node=NODE_PUBLIC_M, nd="public"))],
     "task_trust_domain_node_trust_domain_fkey"),

    # 스냅샷이 전부 **정직하다** — 계약도 진짜 L, 노드도 진짜 S.
    # 그래서 걸릴 수 있는 것은 tier_compatible 복합 FK 하나뿐이다.
    (3, "L 계약 → S Node (tier 역전 · 정직한 스냅샷)",
     [(ASSIGN, a(task=TASK_L, cap=CAP_L, node=NODE_TEAM_S, ct="L", nt="S"))],
     "capability_tier_node_tier_max_fkey"),

    (4, "Task 도메인 거짓 기재 (team 인데 public 이라 적음)",
     [(ASSIGN, a(td="public", nd="public"))],
     "task_id_capability_id_task_trust_domain_fkey"),

    (5, "tier 거짓 기재 (M 인데 L 이라 적음)",
     [(ASSIGN, a(ct="L", nt="L"))],
     "capability_id_capability_tier_fkey"),

    (6, "다른 계약의 capability_id 차용",
     [(ASSIGN, a(cap=CAP_L))],
     "task_id_capability_id_task_trust_domain_fkey"),

    (7, "미바인딩 Node 로 할당",
     [(ASSIGN, a(node=NODE_PUBLIC_M, nd="public"))],
     "agent_id_node_id_fkey"),

    # 도메인이 아니라 tier 를 강등한다. provision_source 를 함께 바꾸면
    # ck_gate_runner_team 이 **먼저** 걸려서 겨냥한 복합 FK 를 시험하지 못한다.
    (8, "라이브 lease 중 Node 등급 강등 (M → S)",
     [(ASSIGN, a()),
      ("UPDATE node SET compute_tier_max = 'S' WHERE id = %(node)s", {"node": RUNNER})],
     "node_id_node_trust_domain_node_tier_max_fkey"),

    (9, "READY 존재 중 Agent 가중치 교체",
     [("UPDATE agent SET weights_sha256 = repeat('c', 64) WHERE id = %(agent)s",
       {"agent": AGENT})],
     "agent_node_ready_agent_id_weights_sha256_fkey"),

    (10, "해시 불일치로 READY 등재",
     [("INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen) "
       "VALUES (%(agent)s, %(node)s, 'BOUND', repeat('d', 64))",
       {"agent": AGENT, "node": NODE_PUBLIC_M}),
      ("INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256) "
       "VALUES (%(agent)s, %(node)s, 'BOUND', repeat('d', 64))",
       {"agent": AGENT, "node": NODE_PUBLIC_M})],
     "agent_node_ready_agent_id_weights_sha256_fkey"),

    (11, "증서 존재 중 게이트 강등",
     [("UPDATE agent_capability SET gate_status = 'FAILED', gate_run_id = NULL "
       "WHERE agent_id = %(agent)s AND capability_id = %(cap)s",
       {"agent": AGENT, "cap": CAP_M})],
     "agent_capability_passed_agent_id_capability_id_gate_status_fkey"),

    (12, "비-게이트러너 Node 로 gate_run 기록",
     [("INSERT INTO gate_run (agent_id, capability_id, runner_node_id, "
       "runner_is_gate_runner, status, golden_set_sha256) "
       "VALUES (%(agent)s, %(cap)s, %(node)s, true, 'RUNNING', repeat('e', 64))",
       {"agent": AGENT, "cap": CAP_M, "node": NODE_PUBLIC_M})],
     "gate_run_runner_node_id_runner_is_gate_runner_fkey"),

    (13, "근거 없이 gate_status='PASSED'",
     [("INSERT INTO agent_capability (agent_id, capability_id, gate_status, gate_run_id) "
       "VALUES (%(agent)s, %(cap)s, 'PASSED', NULL)",
       {"agent": AGENT_UNGATED, "cap": CAP_M})],
     "ck_ac_run_only_when_passed"),

    (14, "행렬 독성 INSERT (team,public)",
     [("INSERT INTO domain_compatible (task_domain, node_domain, "
       "task_privacy_rank, node_privacy_rank) VALUES ('team','public',3,1)", {})],
     "domain_compatible_check"),

    (15, "행렬 독성 INSERT (L,S)",
     [("INSERT INTO tier_compatible (capability_tier, node_tier_max, "
       "capability_rank, node_rank) VALUES ('L','S',3,1)", {})],
     "tier_compatible_check"),

    (16, "lease 중 task 도메인 변경",
     [(ASSIGN, a()),
      ("UPDATE task SET trust_domain = 'public' WHERE id = %(task)s", {"task": TASK})],
     "task_id_capability_id_task_trust_domain_fkey"),

    (17, "lease 중 capability tier 변경",
     [(ASSIGN, a()),
      ("UPDATE capability SET compute_tier = 'L' WHERE id = %(cap)s", {"cap": CAP_M})],
     "capability_id_capability_tier_fkey"),
]

results: list[tuple[bool, str, str]] = []


def record(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def run_case(conn, num: int, desc: str, steps, expect: str) -> None:
    conn.execute("SAVEPOINT v")
    label = f"{num:2d}. {desc}"
    try:
        for sql, params in steps:
            conn.execute(sql, params)
    except psycopg.errors.IntegrityError as exc:
        got = exc.diag.constraint_name or ""
        conn.execute("ROLLBACK TO SAVEPOINT v")
        if expect in got:
            record(True, label, got)
        else:
            record(False, label, f"거절은 됐으나 제약이 다르다 — 기대 *{expect}* / 실제 {got or '(이름 없음)'}")
        return
    except psycopg.Error as exc:
        conn.execute("ROLLBACK TO SAVEPOINT v")
        record(False, label, f"예상 못 한 오류: {type(exc).__name__} {exc}")
        return
    conn.execute("ROLLBACK TO SAVEPOINT v")
    record(False, label, "거절되지 않았다 — 제약이 사라졌거나 약해졌다")


def run_control(conn) -> None:
    """양성 대조 — 정상 할당은 통과해야 한다.

    이게 없으면 스키마가 통째로 망가져 모든 INSERT 가 실패해도 전부 「거절됨」으로 초록이 뜬다.
    """
    conn.execute("SAVEPOINT c")
    try:
        conn.execute(ASSIGN, a())
    except psycopg.Error as exc:
        conn.execute("ROLLBACK TO SAVEPOINT c")
        record(False, " 0. 양성 대조: 정상 할당은 통과한다", f"{type(exc).__name__} {exc}")
        return
    conn.execute("ROLLBACK TO SAVEPOINT c")
    record(True, " 0. 양성 대조: 정상 할당은 통과한다")


def main() -> int:
    print("PG 위반 자동 회귀 (M25) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        conn.execute(SETUP)
        run_control(conn)
        for num, desc, steps, expect in CASES:
            run_case(conn, num, desc, steps, expect)
        conn.rollback()

        # 롤백이 실제로 됐는지 — 시험이 seed 를 더럽히면 안 된다
        left = conn.execute(
            "SELECT count(*) AS n FROM node WHERE id IN (%s, %s)",
            (NODE_PUBLIC_M, NODE_TEAM_S),
        ).fetchone()["n"]
        record(left == 0, "격리: 픽스처가 롤백됐다", "" if left == 0 else f"{left}건 남음")

    failed = [r for r in results if not r[0]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        print("\n제약이 약해졌을 수 있다. docs/error/pg-violations.md 와 대조한다.")
        return 1
    print("판정은 앱이 아니라 제약이 한다 — 실측으로 확인.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
