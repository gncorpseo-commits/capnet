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

**MVP 핵심 경로 실측 완료 (문의 회신 무관).** 스키마 변경·`node_credential` 없음.

- 1단계 **main** (PR #12)
- 2–3단계 **main** ([PR #13](https://github.com/gncorpseo-commits/capnet/pull/13) squash): scratch 실게이트 + Task + demo/sanity/README

실측 (과장 금지):

| 항목 | 결과 |
|------|------|
| scratch N=40 | acc=0.70 · f1≈0.688 · invalid=0 · **PASSED** (`dummy=false`) |
| sanity 3종 | 전부 **FAILED** |
| smoke_w1 | dummy 배관 OK (실게이트 아님) |
| 임계 | 가정 0.75/0.72 → 실측 보정 **0.68/0.65** |

## 체크리스트

1. [x] compose PG16 + Core + Node 3대 limits
2. [x] schema + seed + allowlist
3. [x] claim `INSERT ... SELECT`
4. [x] dummy E2E · CRUD · dummy 게이트 배관
5. [x] EuroSAT 핀 · 골든 N=40 · 픽셀 전수 · M25
6. [x] scratch Agent · 실게이트 · Task 완주
7. [x] `scripts/demo` · `sanity` · README 5분 안내
8. [x] phase2(+3) PR squash merge (#13)
9. [ ] 시연 영상 · 보고서 나머지 절

## 아직 아닌 것

- A/B Must · `node_credential` · Capability 런타임 등록
- seed Agent의 시드 `gate_run` PASSED는 **배관**
- 사전학습 가중치 / `.pt` 경로 없음

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 1 | **A/B(S2) Must 여부 — 미결, 구현 안 함** | 8/11 |
| 2 | 베이스라인 백본 2종 (A/B를 Must로 올릴 때만) | — |
| 3 | `NOTICE` 저작권자 표기 | 언제든 |

## 함정

`@docs/error/pitfalls.md` · assignment/gate_run은 `INSERT ... SELECT`만 · 게이트는 team runner만 · safetensors만
