# CapNet 컨텍스트 핸드오프

> Cowork 세션(기획·리뷰) → Claude Code 세션(구현) 인계 문서.
> 대화 전문이 아니라 **결정·검증된 사실·함정**만 담는다.
> 새 세션이 이 파일 하나로 5분 안에 맥락을 잡는 것이 목적.
>
> 자동 로드되지 않는다. 필요할 때 `@docs/context-handoff.md`로 부른다.
> 최종 갱신: 2026-08-01

---

## 1. 확정된 결정과 근거

바꾸려면 근거를 먼저 반박해야 하는 것들이다.

| # | 결정 | 근거 |
|---|------|------|
| D1 | MVP 증명 대상 = **Capability 추상화 성립** (E2E 아님) | E2E는 기성 기술 조합이라 되는 게 당연. 미검증 명제는 "같은 계약의 Agent가 대체 가능한가" |
| D2 | Capability = 이름이 아니라 **계약** (스키마 + 골든셋 + 게이트) | 이름만으로는 대체 가능성이 보장 안 됨 |
| D3 | **전처리는 계약의 일부** (32×32 RGB). Gate·Product·Proof 동일 | 게이트만 열화하면 증명이 제품에 대해 아무 말도 못 함. 바꾸려면 `@2`로 버전 상승 |
| D4 | 게이트 실행은 **team gate-runner Node에서만** | 제출자 Node에서 골든셋을 돌리면 정답 하드코딩으로 게이팅 무력화 |
| D5 | 가중치 **safetensors만** | `.pt`/`.pth`는 pickle 역직렬화 → 로드만으로 임의 코드 실행 |
| D6 | **사전학습 가중치 금지. EuroSAT scratch 학습만** | 대회 2차 라이선스 검증. ImageNet 가중치는 조건 승계 논란 |
| D7 | MVP Node = **팀 자체 조달만** | 인센티브가 P6인데 공급은 P2부터 필요 → 닭-달걀. 외부는 Phase 3+ |
| D8 | 입력은 **allowlist된 datasetId만**. 자유 업로드 경로를 만들지 않음 | fileToken은 다운로드 이후를 통제 못 함. 정책이 문서에만 있으면 안 지켜짐 |
| D9 | **모델 기반 골든셋 샘플 선택 금지** | 참조 모델의 귀납 편향이 골든셋에 박히면, A/B 편차가 Agent 차이인지 편향인지 구분 불가 |
| D10 | 난이도 조준은 **입력 열화만** (혼동 가중 없음) | D9의 귀결 |
| D11 | **M25(위반 거절 데모)가 대회 Must** | 유일한 진짜 변별점. 구현 비용 ≈ 0 (SQL 스크립트) |
| D12 | Changelog는 `docs/CHANGELOG.md` 단독 | README는 대회 심사용 5분 기동 안내 전용 |
| D13 | 커밋 계정 = **gncorpseo-commits** | 전역 CLAUDE.md의 jangsejong 아님 |

---

## 2. PostgreSQL 16에서 실제로 검증된 것

`docs/schema.sql` v4.4를 적재해 **위반 시도가 DB에서 거부되는 것을 실측**했다. 문서상 주장이 아니라 실행 결과다.

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

UPDATE 경로도 함께 닫혀 있다 — 할당이 살아있는 동안 `task.trust_domain`·`capability.compute_tier`·`node.trust_domain`을 아무도 못 바꾼다.

---

## 3. 함정 — 여기서 시간을 잃는다

### 3.1 `INSERT ... SELECT` 강제

`assignment` 하나에 스냅샷 컬럼과 복합 FK 5개가 걸린다. **값을 손으로 채우면 반드시 틀린다.** ORM으로 `Assignment(task_id=…, node_id=…)` 식으로 짜면 FK가 쏟아지고, 우회하려다 제약을 끄면 §2가 통째로 무의미해진다.

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

### 3.2 게이트 사슬 순서

```text
gate_run(PASSED, team runner) → gate_run_passed → agent_capability(PASSED, gate_run_id)
  → agent_capability_passed → 그제서야 assignment 가능
```

순서를 건너뛰면 FK가 막는다. 막히면 우회하지 말고 순서를 맞춘다.

### 3.3 `compute_tier`는 텍스트 정렬이 반대다

알파벳순은 `L < M < S`. 의도는 `S < M < L`. **`WHERE node.compute_tier_max >= capability.compute_tier` 같은 코드를 쓰면 조용히 뒤집힌다.** v4.4는 `compute_tier_rank` + `tier_compatible` 행렬로 해결했으니, 앱에서 티어를 직접 비교하지 말고 **행렬 FK에 맡긴다.**

### 3.4 큐 claim

- Core 워커만 claim한다. **Node는 큐를 pull하지 않는다** (이중 디스패치 방지)
- `FOR UPDATE SKIP LOCKED` 필수
- 활성 lease 유니크 인덱스가 이중 할당을 DB에서 막는다

### 3.5 훅

전역 훅이 `git add -A` / `git add .`를 차단한다. **명시적 경로로 스테이징**한다. 정상 동작이니 훅을 끄지 않는다.

---

## 4. 골든셋 요점

상세는 `docs/golden/image-classify-v1.md`.

- 계약: `image.classify@1`, closed-set 10라벨, 32×32 RGB
- 데이터: EuroSAT **RGB 배포판**, Zenodo `7711810`, MIT
- **게이트 통과 조건은 AND**: `min_accuracy` ∧ `min_macro_f1` ∧ `max_invalid_rate`
- 채점 규칙: 부분 점수 없음 · 스키마 위반 = 오답 · **유사도 매칭 금지**
- `confidence`는 채점에 쓰지 않는다 (캘리브레이션 차이가 판정을 오염)
- 케이스 수: **대회 데모 N=30–50**, 본편 통계 판정 n=300 이상
  - n=50이면 SE ≈ 0.05로 편차 임계값과 같아 **판정 불가**. 보고서에 이 사실을 명시할 것
- Sanity floor 3종(상수·난수·스키마 위반)이 전부 FAILED여야 골든셋을 신뢰

---

## 5. 대회 범위 (Contest v0.3)

- 출품 ~**8/27**. 2차에 **라이선스 검증**이 정식 단계로 있음
- Must: M1–M13, M15–M21, **M25**
- Non-goal: UI · tenant/public · 자동 재할당 · **사전학습 가중치**
- W2 버퍼: 8/16–17
- 밀리면 버리는 순서: A/B → WS를 폴링으로 → heartbeat 스캐너 → sanity 3종→1종
  - **절대 안 버림: M25 · M4(단일 demo 스크립트) · M11(게이트 사슬)**
- 영상 3분: 105–135초에 위반 3종 상세, 135–150초에 나머지 3종 표

---

## 6. 미결 항목

| # | 내용 | 기한 |
|---|------|------|
| 1 | `contest@oss.kr` 문의 (배점·소스 제출 형식) | W0. 답신에 며칠 걸림 |
| 2 | EuroSAT 다운로드 후 **디렉터리명·픽셀 크기·archive_sha256 확정** | W0–W1 |
| 3 | `min_accuracy` 실측 확정 (통과율 20–80%) | 베이스라인 2개 실측 후 |
| 4 | 베이스라인 백본 2종 선정 (서로 다른 계열, 둘 다 scratch) | W2 |
| 5 | 전역 `~/.claude/CLAUDE.md`의 GitHub 계정 정정 | 급하지 않음 |

---

## 7. 이 문서 쓰는 법

- **자동 로드 금지.** `CLAUDE.md`는 짧게 유지하고, 이 파일은 필요할 때 `@docs/context-handoff.md`로 부른다
- 결정이 바뀌면 §1에 행을 고치고 근거를 갱신한다. 근거 없이 바꾸지 않는다
- 세션 상태는 `STATE.md`, 버전 이력은 `docs/CHANGELOG.md`. 역할을 섞지 않는다
