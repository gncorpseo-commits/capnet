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
| 10 | 해시 불일치로 READY 등재 | `agent_node_ready_..._weights_sha2_fkey` |
| 11 | 증서 존재 중 게이트 강등 | `agent_capability_passed_..._gate_status_fkey` |
| 12 | 비-게이트러너 Node로 gate_run 기록 | `gate_run_runner_node_id_runner_is_gate_runner_fkey` |
| 13 | 근거 없이 `gate_status='PASSED'` | `ck_ac_run_only_when_passed` |
| 14 | 행렬 독성 INSERT (`team,public` / `L,S`) | `domain_compatible_check` / `tier_compatible_check` |
| — | 정상 할당 | 통과 |

**M25 스크립트는 이 표를 그대로 재현하면 된다.** 6종만 골라도 되지만 전부 이미 검증돼 있다.

업데이트 경로도 함께 닫혀 있다 — 할당이 살아있는 동안 `task.trust_domain`·`capability.compute_tier`·`node.trust_domain`을 아무도 못 바꾼다.
