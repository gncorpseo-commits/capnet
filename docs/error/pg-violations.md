# PostgreSQL 위반 거절 (실측)

**카테고리:** error  
**관련:** [`../spec/schema.sql`](../spec/schema.sql) v4.4 · [`../context-handoff.md`](../context-handoff.md) · Contest M25

[`../spec/schema.sql`](../spec/schema.sql) v4.4를 PostgreSQL 16에 적재해 **위반 시도가 DB에서 거부되는 것을 실측**했다. 문서상 주장이 아니라 실행 결과다.

| # | 위반 시도 | 거부한 제약 |
|---|-----------|-------------|
| 1 | 게이트 미통과 Agent로 할당 | `assignment_agent_id_capability_id_fkey` |
| 2 | team Task → public Node | `..._capability_tier_node_tier_max_fkey` / `domain_compatible` |
| 3 | L 계약 → S Node | `tier_compatible` 부재 |
| 4 | Task 도메인 거짓 기재 | `..._task_id_capability_id_task_trust_domain_fkey` |
| 5 | tier 거짓 기재 | `..._capability_id_capability_tier_fkey` |
| 6 | 다른 계약의 capability_id 차용 | 위와 동일 |
| 7 | 미바인딩 Node로 할당 | `assignment_agent_id_node_id_fkey` |
| 8 | 라이브 lease 중 Node public 강등 | `..._node_id_node_trust_domain_node_tier_max_fkey` |
| 9 | READY 존재 중 가중치 교체 | `agent_node_ready_agent_id_weights_sha256_fkey` |
| 10 | 해시 불일치로 READY 등재 | `agent_node_ready_..._weights_sha256_fk` (63자 절단) |
| 11 | 증서 존재 중 게이트 강등 | `agent_capability_passed_..._gate_status_fkey` |
| 12 | 비-게이트러너 Node로 gate_run 기록 | `gate_run_runner_node_id_runner_is_gate_runner_fkey` |
| 13 | 근거 없이 `gate_status='PASSED'` | `ck_ac_run_only_when_passed` |
| 14 | 행렬 독성 INSERT (`team,public` / `L,S`) | `domain_compatible_check` / `tier_compatible_check` |
| — | 정상 할당 | 통과 |

**이 표는 이제 자동으로 지켜진다** — `tests/integration/check_pg_violations.py` (CI · migrate job).

```bash
python3 tests/integration/check_pg_violations.py   # DATABASE_URL 필요 · 전부 롤백된다
```

수동 기록과 다른 점 셋:

1. **19개 케이스** — 위 14종 + lease 중 task/capability 변경 2종 + 행렬 독성 2종 분리 + **양성 대조**
2. **어느 제약이 거절했는지**까지 대조한다. 「거절됐다」만 보면 부족하다 —
   실제로 `assignment_agent_id_capability_id_fkey` 를 떨어뜨려 봤더니 그 케이스는
   **여전히 거절됐다**. 다른 FK 가 잡았기 때문이다. 거절 여부만 보는 시험은 그때 초록이 뜬다
3. **양성 대조** — 정상 할당은 반드시 통과해야 한다. 없으면 스키마가 통째로 망가져
   모든 INSERT 가 실패해도 「전부 거절됨」으로 초록이 뜬다

`scripts/demo_violations.sql` 은 촬영용 6종 시연으로 남긴다 (NOTICE 출력이 화면에 보인다).

시연 여섯이 **표의 어느 행**을 치는가 — 스키마에서 FK 이름을 도출해 각 시연의 실패 문장이
건드리는 표로 정적 대조했다 (`tests/test_violation_demo_names_its_constraint.py`, 2026-09-06).
시연의 `WHEN foreign_key_violation` 은 **어떤 FK 든** 받아 주므로, 실행만으로는 위 2 의 함정을
못 가른다. Docker 로 실측하면 `CONSTRAINT_NAME` 단언을 SQL 에 넣는다 (브리지).

| 시연 | 행 | 정적 대조 |
|---|---|---|
| TEST1 gate-ungated assignment | 1 | `assignment_agent_id_capability_id_fkey` — 후보 안 |
| TEST2 team task → public node | 2 | `assignment_capability_tier_node_tier_max_fkey` — 후보 안 |
| TEST3 L capability → S node | 3 | `tier_compatible` 을 참조하는 FK — 후보 안 |
| TEST4 live lease then demote node | 8 | `assignment_node_id_node_trust_domain_node_tier_max_fkey` — 후보 안 |
| TEST5 READY live weight swap | 9 | `agent_node_ready_agent_id_weights_sha256_fkey` — 후보 안 |
| TEST6 invalidate PASSED gate_run | — | `UPDATE gate_run.status` 가 칠 수 있는 것은 `gate_run_passed_…_status_fkey` 뿐 — **표 밖**. 11행은 `agent_capability.gate_status` 강등이라 다른 문장이다. 실측 뒤 15행 후보 |

업데이트 경로도 함께 닫혀 있다 — 할당이 살아있는 동안 `task.trust_domain`·`capability.compute_tier`·`node.trust_domain`을 아무도 못 바꾼다.
