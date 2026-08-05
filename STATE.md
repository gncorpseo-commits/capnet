# STATE — 현재 작업 상태

> 세션 인계용 단기 상태판. 결정·미결은 `docs/context-handoff.md`, 이력은 `docs/history/CHANGELOG.md`, 지도는 `docs/INDEX.md`.
> **갱신: 2026-08-06**

---

## 대회 정보

팀명 **지엔** · 팀장 **서우석** · 접수번호 **915**
자유과제 / 세부과제 **인공지능** · 사회문제해결 항목 공란
출품작 제출 **8/27**, 1차 평가 9/3, 멘토링 9/18–10/9, 2차 평가 10/12–10/28, 시상식 12/4

전체 일정은 `docs/ops/contest-submission-checklist.md`.

---

## 지금 어디인가

**W1 (8/4–8/10) 진행 중.** EuroSAT RGB 아카이브 핀 확정. 문의 회신 무관으로 진행.

- 기획서 **문서 v4.5** (스키마는 **v4.4** 유지). §2.5 IIS · Provenance by Design · §14 문헌
- dummy Node: placeholder safetensors · dummy 라벨 · complete API. **scratch 학습 아님**
- 로컬: Docker Desktop 있음. **2026-08-06 smoke 통과** (CRUD + dummy 게이트 사슬 + claim/execute). 시드 해시가 바뀌면 `docker compose down -v` 후 스모크. **골든셋 채점은 아직 아님**

## 이번 주 목표

1. [x] **docker compose** — PostgreSQL 16 + Core(FastAPI)
2. [x] **`docs/spec/schema.sql` 적재** + `image.classify@1` seed + allowlist `datasetId`
3. [x] **claim `INSERT ... SELECT` + `FOR UPDATE SKIP LOCKED`**
4. [x] **기획서 v4.5** (문서만)
5. [x] **dummy Node E2E** — lease → placeholder 로드 → dummy 추론 → 결과 보고 (품질·게이트 실측 아님)

6. [x] **Agent / Node 등록·조회 + bind READY** (M9·M10). Capability POST는 없음(시드 `image.classify@1`만)
7. [x] **게이트 사슬 API** (M11 배관). `dummy=true` PASSED만. **골든셋 채점·M18 아님**
8. [x] **EuroSAT RGB 핀** — `archive_sha256` · 64×64 · 디렉터리명. 케이스 추출·scratch 아님

아직 아닌 것 (과장 금지):

- EuroSAT scratch Agent · 실제 분류 품질 · 골든셋 게이트 추론
- 컨테이너 Node 3대 제한 · `node_credential`
- Capability 런타임 등록 API

## 다음 (W2, 8/11–8/17)

- **컨테이너 Node 3대** (S/team, S/public, M/team). CPU·메모리 실제 제한 — M26
- **Node 자격증명** — Core가 발급, Node는 자기 등급을 주장할 수 없다. `node_credential` 증서 테이블은 **스키마 마이그레이션 이슈** (문서 v4.5와 별개)
- Agent 1개 EuroSAT scratch 학습 → 게이트 PASSED → Task 1건 완주
- 8/16–17 버퍼. 절반은 결과보고서 초안에 쓴다
- **A/B Must vs D1** 판단 기한 8/11

## W0에서 넘어온 잔여

| # | 내용 | 상태 |
|---|------|------|
| 1 | `contest@oss.kr` 문의 발송 (보고서 서식·소스 제출 형식·라이선스 산출물·사회문제해결 가점 여부) | 회신 무관 진행 |
| 2 | EuroSAT RGB 내려받아 **디렉터리명 · 픽셀 크기 · `archive_sha256` 확정** | 완료 (핀). 케이스 manifest 없음 |
| 3 | 문서 개정 — D15 신설(v4.5). M26·M27은 미착수 | 진행 |

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 1 | **A/B 비교(S2)를 Must로 올릴지, 아니면 D1을 하향 조정할지.** 지금 문서는 대체가능성을 핵심 명제로 두면서 그것을 가장 먼저 버리는 항목으로 두고 있다 | **8/11 (W2 시작 전)** |
| 2 | `min_accuracy` 실측 확정 (통과율 20–80% 구간) | 베이스라인 2개 실측 후 |
| 3 | 베이스라인 백본 2종 선정 (서로 다른 계열, 둘 다 scratch) | W2 |
| 4 | `NOTICE` 저작권자 표기를 개인명으로 바꿀지 | 언제든 |

## 함정 요약

전문은 `@docs/error/pitfalls.md`.

- `assignment`는 스냅샷 컬럼과 복합 FK 5개가 걸린다. **손으로 값을 채우면 반드시 틀린다.** `INSERT ... SELECT`만 쓴다
- `compute_tier`는 텍스트 정렬이 의도와 반대다(`L < M < S`). 앱에서 직접 비교하지 말고 `tier_compatible` 행렬에 맡긴다
- 게이트 사슬 순서를 건너뛰면 FK가 막는다. 우회하지 말고 순서를 맞춘다
- `git add -A` / `git add .` 는 전역 훅이 차단한다. 명시적 경로로 스테이징한다
- live READY가 있는 볼륨에서 `agent.weights_sha256`를 바꾸면 FK가 막는다. 시드 해시 변경 시 `down -v`
