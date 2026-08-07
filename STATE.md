# STATE — 현재 작업 상태

> 세션 인계용 단기 상태판. 결정·미결은 `docs/context-handoff.md`, 이력은 `docs/history/CHANGELOG.md`, 지도는 `docs/INDEX.md`.
> **갱신: 2026-08-07**

---

## 대회 정보

팀명 **지엔** · 팀장 **서우석** · 접수번호 **915**
자유과제 / 세부과제 **인공지능** · 사회문제해결 항목 공란
출품작 제출 **8/27(목) 18:00**, 1차 평가 9/3, 멘토링 9/18–10/9, 2차 평가 10/12–10/28, 시상식 12/4

전체 일정은 `docs/ops/contest-submission-checklist.md`. 제출 가이드: https://osscontest.kr/notice/39

---

## 지금 어디인가

**E1: n=300 채점 + A/B 골격** (Must 승격 아님 · SD-001 미결). 출품 패키지(양식·영상·포털)가 여전히 최우선.

- `TinyEuroSATB` · `score_n300` · `compare_ab` (n&lt;300 → INCONCLUSIVE)
- 출품: [`docs/ops/contest-report-form-draft.md`](docs/ops/contest-report-form-draft.md) → 공식 docx/hwp · YouTube · PDF

실측 (과장 금지):

| 항목 | 결과 |
|------|------|
| scratch N=40 | acc=0.70 · f1≈0.688 · **PASSED** (`dummy=false`) |
| sanity 3종 | 전부 **FAILED** |
| 임계 | **0.68/0.65** (실측 보정 · SD-004) |
| 가중치 공개 | raw.githubusercontent.com …/eurosat_scratch.safetensors **200 OK** · 378784 B |
| n=300 / A/B | Agent A n300: acc≈0.817 · f1≈0.814 · PASSED · B·paired 미실행 |

## 체크리스트

1. [x] compose · claim · dummy E2E · CRUD · 게이트 배관
2. [x] EuroSAT 핀 · 골든 N=40 · M25 · Node 3대 limits
3. [x] scratch 실게이트 · Task · demo/sanity/README (#13)
4. [x] S3 sha256 거부 · S4 OpenAPI (#14)
5. [x] Capability 런타임 POST + golden n=300 파이프라인 (#15)
6. [ ] 시연 영상 YouTube · 공식 양식 이식 · PDF · 포털 제출
7. [x] `node_credential` 설계 초안 (DDL 없음)
8. [x] 보고서 md §3–9 · 영상 스토리보드 · cyclonedx SBOM
9. [x] 운영규정 준수 근거 · 양식 초안 문장 · 가중치 URL 실측
10. [x] E1 n=300 채점·A/B 골격 (Must 아님)

## 아직 아닌 것

- A/B **Must 승격** · `node_credential` DDL · WS/만료 스캐너
- 공식 양식 파일 기입·PDF·유튜브·포털 zip
- Agent B 학습·n=300 paired 실측·통계 확정

상세: [`docs/retrospective/register.md`](docs/retrospective/register.md) · [`docs/ops/regulation-compliance.md`](docs/ops/regulation-compliance.md)

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 1 | **A/B(S2) Must 여부 — 미결** (SD-001). 골격만 있음 | 8/11 |
| 2 | Agent B 학습·n300 실측을 Must 전에 돌릴지 | — |
| 3 | 정부지원 중복수혜 해당 여부 (팀 확인) | 제출 전 |

## 함정

`@docs/error/pitfalls.md` · assignment/gate_run은 `INSERT ... SELECT`만 · 게이트는 team runner만 · safetensors만
