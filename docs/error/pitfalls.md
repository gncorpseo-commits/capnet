# 함정 — 여기서 시간을 잃는다

**카테고리:** error  
**관련:** [`../context-handoff.md`](../context-handoff.md) · [`../spec/schema.sql`](../spec/schema.sql)

## 1. `INSERT ... SELECT` 강제

`assignment` 하나에 스냅샷 컬럼과 복합 FK 5개가 걸린다. **값을 손으로 채우면 반드시 틀린다.** ORM으로 `Assignment(task_id=…, node_id=…)` 식으로 짜면 FK가 쏟아지고, 우회하려다 제약을 끄면 [pg-violations](./pg-violations.md)가 통째로 무의미해진다.

```sql
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
  JOIN agent_node_ready anr        ON anr.agent_id = acp.agent_id
  JOIN node n                      ON n.id = anr.node_id
 WHERE t.id = $1 AND n.id = $2;
```

앱은 **고르기만** 하고 판정은 DB가 한다.

## 2. 게이트 사슬 순서

```text
gate_run(PASSED, team runner) → gate_run_passed → agent_capability(PASSED, gate_run_id)
  → agent_capability_passed → 그제서야 assignment 가능
```

순서를 건너뛰면 FK가 막는다. 막히면 우회하지 말고 순서를 맞춘다.

## 3. `compute_tier`는 텍스트 정렬이 반대다

알파벳순은 `L < M < S`. 의도는 `S < M < L`. **`WHERE node.compute_tier_max >= capability.compute_tier` 같은 코드를 쓰면 조용히 뒤집힌다.** v4.4는 `compute_tier_rank` + `tier_compatible` 행렬로 해결했으니, 앱에서 티어를 직접 비교하지 말고 **행렬 FK에 맡긴다.**

## 4. 큐 claim

- Core 워커만 claim한다. **Node는 큐를 pull하지 않는다** (이중 디스패치 방지)
- `FOR UPDATE SKIP LOCKED` 필수
- 활성 lease 유니크 인덱스가 이중 할당을 DB에서 막는다

## 5. 훅

전역 훅이 `git add -A` / `git add .`를 차단한다. **명시적 경로로 스테이징**한다. 정상 동작이니 훅을 끄지 않는다.

## 6. Wiki 링크 하이픈

제목·링크의 하이픈은 **키보드 `-`만** 쓴다. 워드 복붙 하이픈(`%E2%80%90`)은 다른 페이지로 보이거나 “Create new page”가 뜬다. 상세는 [팀 GitHub 가이드](../guide/github-team-guide.md).
