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

**MVP + S3/S4 + Capability/n300 main (#15).** `node_credential` 설계 초안만 추가 (DDL 없음).

- Capability: `POST /v1/capabilities`
- n=300: `data/golden-n300/` gitignore 추출 파이프라인
- 다음 출품: 시연 영상 · 보고서 / 다음 본편: credential DDL은 **승인 후**


실측 (과장 금지):

| 항목 | 결과 |
|------|------|
| scratch N=40 | acc=0.70 · f1≈0.688 · **PASSED** (`dummy=false`) |
| sanity 3종 | 전부 **FAILED** |
| 임계 | **0.68/0.65** (실측 보정) |

## 체크리스트

1. [x] compose · claim · dummy E2E · CRUD · 게이트 배관
2. [x] EuroSAT 핀 · 골든 N=40 · M25 · Node 3대 limits
3. [x] scratch 실게이트 · Task · demo/sanity/README (#13)
4. [x] S3 sha256 거부 · S4 OpenAPI (#14)
5. [x] Capability 런타임 POST + golden n=300 파이프라인 (#15)
6. [ ] 시연 영상 · 보고서 나머지 절
7. [x] `node_credential` 설계 초안 (DDL 없음 · `docs/design/node-credential-draft.md`)

## 아직 아닌 것

- A/B Must · `node_credential` DDL · WS/만료 스캐너
- seed `gate_run` PASSED는 **배관**
- n=300 통계 판정·A/B 확정 (추출·gitignore만; 케이스 미커밋)


## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 1 | **A/B(S2) Must 여부 — 미결, 구현 안 함** | 8/11 |
| 2 | 베이스라인 백본 2종 (A/B를 Must로 올릴 때만) | — |
| 3 | `NOTICE` 저작권자 표기 | 언제든 |

## 함정

`@docs/error/pitfalls.md` · assignment/gate_run은 `INSERT ... SELECT`만 · 게이트는 team runner만 · safetensors만
