# STATE — 현재 작업 상태

> 세션 인계용 단기 상태판. 결정과 근거는 `docs/context-handoff.md`, 버전 이력은 `docs/CHANGELOG.md`.
> **갱신: 2026-08-02**

---

## 대회 정보

팀명 **지엔** · 팀장 **서우석** · 접수번호 **915**
자유과제 / 세부과제 **인공지능** · 사회문제해결 항목 공란
출품작 제출 **8/27**, 1차 평가 9/3, 멘토링 9/18–10/9, 2차 평가 10/12–10/28, 시상식 12/4

전체 일정은 `docs/contest-submission-checklist.md`.

---

## 지금 어디인가

**W1 (8/4–8/10) 착수 직전.** 설계와 스키마는 끝났고 실행 코드는 아직 없다.

`docs/schema.sql` v4.4는 PostgreSQL 16에서 위반 14종이 거부되는 것까지 실측 확인했다. 제약을 약화하지 않는 한 그대로 쓴다.

## 이번 세션(W1) 목표

순서를 지킨다. 3번이 가장 중요하다.

1. **docker compose** — PostgreSQL 16 + Core(FastAPI) 골격
2. **`docs/schema.sql` 적재** + `image.classify@1` seed + allowlist `datasetId`
3. **claim 쿼리를 `INSERT ... SELECT` 패턴으로 고정** ← 이 패턴이 잡히기 전에 다른 엔드포인트를 늘리지 않는다

이어서 W1 안에 들어갈 것:

- Core CRUD — Capability / Agent / Node 등록·조회
- 게이트 사슬: `gate_run` → `gate_run_passed` → `agent_capability` → `agent_capability_passed`
- 의존성을 추가할 때마다 `THIRD-PARTY-LICENSES.md`에 한 줄 누적

## 다음 (W2, 8/11–8/17)

- Node 런타임 1종 — lease → safetensors 로드 → 추론 → 결과
- **컨테이너 Node 3대** (S/team, S/public, M/team). CPU·메모리 실제 제한을 건다 — M26
- **Node 자격증명** — Core가 발급, Node는 자기 등급을 주장할 수 없다. `node_credential` 증서 테이블 추가(v4.5) — M27
- Agent 1개 EuroSAT scratch 학습 → 게이트 PASSED → Task 1건 완주
- 8/16–17 버퍼. 절반은 결과보고서 초안에 쓴다

## W0에서 넘어온 잔여

| # | 내용 | 상태 |
|---|------|------|
| 1 | `contest@oss.kr` 문의 발송 (보고서 서식·소스 제출 형식·라이선스 산출물·사회문제해결 가점 여부) | 진행 |
| 2 | EuroSAT RGB 내려받아 **디렉터리명 · 픽셀 크기 · `archive_sha256` 확정** | 미착수 |
| 3 | 문서 개정 — 정의문 수정, D7 개정, D14·D15 신설, M26·M27 추가 | 진행 |

2번은 골든셋 작업의 선행 조건이다. compose와 Core CRUD는 이것 없이도 진행된다.

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 1 | **A/B 비교(S2)를 Must로 올릴지, 아니면 D1을 하향 조정할지.** 지금 문서는 대체가능성을 핵심 명제로 두면서 그것을 가장 먼저 버리는 항목으로 두고 있다 | **8/11 (W2 시작 전)** |
| 2 | `min_accuracy` 실측 확정 (통과율 20–80% 구간) | 베이스라인 2개 실측 후 |
| 3 | 베이스라인 백본 2종 선정 (서로 다른 계열, 둘 다 scratch) | W2 |
| 4 | `NOTICE` 저작권자 표기를 개인명으로 바꿀지 | 언제든 |

1번은 W1을 막지 않는다. W1은 그대로 진행한다.

## 함정 요약

전문은 `@docs/context-handoff.md` §3. 자주 걸리는 것만 다시 적는다.

- `assignment`는 스냅샷 컬럼과 복합 FK 5개가 걸린다. **손으로 값을 채우면 반드시 틀린다.** `INSERT ... SELECT`만 쓴다
- `compute_tier`는 텍스트 정렬이 의도와 반대다(`L < M < S`). 앱에서 직접 비교하지 말고 `tier_compatible` 행렬에 맡긴다
- 게이트 사슬 순서를 건너뛰면 FK가 막는다. 우회하지 말고 순서를 맞춘다
- `git add -A` / `git add .` 는 전역 훅이 차단한다. 명시적 경로로 스테이징한다
