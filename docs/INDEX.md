# CapNet 문서 인덱스

클론·포크·AI 세션용 **진입 지도**. 파일 전역 순번 없음 — 역할 폴더 + 이 순서로 읽는다.

**갱신:** 폴더·진입 경로가 바뀔 때만. 주간 상태는 [`../STATE.md`](../STATE.md).

---

## AI / 신규 — 이 순서만

1. [`../README.md`](../README.md) — 제품 한 줄·심사용
2. [`../STATE.md`](../STATE.md) — 지금 어디인지
3. [`context-handoff.md`](./context-handoff.md) — 확정 결정·미결 (상세 error는 링크로)
4. [`spec/schema.sql`](./spec/schema.sql) — DDL 정본
5. 필요할 때만 [`design/capnet-plan.md`](./design/capnet-plan.md)

협업만: [`guide/github-team-guide.md`](./guide/github-team-guide.md) · [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

---

## 폴더 역할

| 폴더 | 역할 | 예 |
|------|------|-----|
| **guide/** | 사람·프로세스 “어떻게” | GitHub 가이드, 사용자 안내 |
| **error/** | 실패·함정·거절 | PG 위반 14종, claim 함정 |
| **history/** | 시간축 | CHANGELOG |
| **design/** | 시스템 “무엇/왜” | 기획서 |
| **spec/** | 기계가 읽을 계약 | schema.sql, golden/ |
| **ops/** | 기동·배포·제출 | Contest MVP, 제출 체크리스트 |
| **retrospective/** | 과정 결정·빚·범위·적응 | register · lessons |
| **research/** | MVP 밖 아이디어 | (비어 있어도 OK) |

루트 진입: `README` · `STATE` · `CONTRIBUTING` · `CLAUDE.md` · 이 `INDEX`.

---

## 카테고리별 링크

### guide
- [팀 GitHub 사용 표준](./guide/github-team-guide.md) (Wiki와 동기)
- [사용 안내 (쉬운 버전)](./guide/user-guide-ko.md)

### error
- [PG 위반 14종 실측](./error/pg-violations.md)
- [구현 함정](./error/pitfalls.md)

### history
- [CHANGELOG](./history/CHANGELOG.md)

### design
- [기획서 v4.5](./design/capnet-plan.md) (스키마는 v4.4)
- [node_credential 설계 초안](./design/node-credential-draft.md) (**DDL 미적용**)

### spec
- [schema.sql v4.4](./spec/schema.sql)
- [OpenAPI YAML 초안 (S4)](./spec/openapi.yaml) — 런타임 `GET /openapi.yaml` · `/openapi.json`
- [골든셋 image.classify@1](./spec/golden/image-classify-v1.md) (v0.4)
- [데모 manifest N=40](./spec/golden/manifest-image-classify-v1.json)
- [골든 산출물 안내 · n=300](./spec/golden/README.md)
- [EuroSAT RGB archive 핀](./spec/golden/eurosat-rgb.json)

### ops
- [Contest MVP 2026](./ops/Contest_MVP_2026.md)
- [출품 체크리스트](./ops/contest-submission-checklist.md)
- [운영규정 준수 근거](./ops/regulation-compliance.md)
- [결과보고서·붙임 초안 문장](./ops/contest-report-form-draft.md) — 공식 양식 이식용
- [결과보고서 md 초안](./ops/contest-report-draft.md) — §0–9
- [시연 영상 스토리보드](./ops/demo-video-storyboard.md)
- [촬영일 런북](./ops/shoot-day-runbook.md) — 명령·자막 복붙
- [게이트 사슬 1장](./ops/gate-chain-slide.md) — 영상 150–170초용

### retrospective
- [README · 분류 정의](./retrospective/README.md)
- [register](./retrospective/register.md) — TD / SD / EA
- [lessons-learned](./retrospective/lessons-learned.md)

### research
- [README](./research/README.md)

---

## 갱신 규칙

| 문서 | 언제 고치나 |
|------|-------------|
| `STATE.md` | 매 세션 / 매주 |
| `docs/INDEX.md` | 문서·폴더 구조가 바뀔 때 |
| `README.md` | 기동법·한 줄 소개가 바뀔 때 |
| `context-handoff.md` | 결정·미결이 바뀔 때 (일기장 금지) |

코드/일정을 바꾸면 **STATE부터**, 문서를 옮기면 **INDEX를** 고친다.
