# CapNet — Capability Network

**채점 가능한 Capability 계약을 게이트로 묶고, 신뢰 도메인 안의 Node에서 Task를 완결하는 오픈소스 실행 계층.**

2026년 오픈소스 개발자대회 출품작. `ai-agent-store`의 첫 번째 프로덕트.

---

## 무엇이 다른가

AI 에이전트를 모아놓은 스토어는 이미 많다. CapNet이 다루는 건 그 앞의 질문이다.

> **"같은 능력을 표방하는 두 에이전트를, 사용자가 모르는 채로 서로 바꿔 끼울 수 있는가?"**

이름표만으로는 보장되지 않는다. CapNet에서 Capability는 **이름이 아니라 계약**이다. 입출력 스키마, 골든셋, 통과 기준이 함께 묶여야 하나의 Capability가 되고, 그 계약을 통과하지 못한 Agent는 애초에 할당 대상이 되지 못한다.

그리고 이 판정을 애플리케이션 코드가 하지 않는다. **데이터베이스가 한다.**

## 핵심 설계 — 불가능한 상태를 표현할 수 없게 만든다

라우팅 불변식을 앱의 `if` 문으로 지키면, 그 `if` 문을 빠뜨린 경로 하나가 전체를 무너뜨린다. CapNet은 이 규칙들을 PostgreSQL의 제약으로 옮겼다.

- 게이트를 통과하지 못한 Agent에게는 Task를 **할당할 수 없다**
- `team` 등급 Task는 `public` Node로 **내려갈 수 없다**
- `L` 등급 계약은 `S` 등급 Node에서 **실행될 수 없다**
- 할당이 살아 있는 동안 Node의 신뢰 등급을 **강등할 수 없다**
- 가중치 해시가 일치하지 않으면 Node는 **READY가 될 수 없다**

"하지 않는다"가 아니라 "할 수 없다"이다. [`docs/spec/schema.sql`](docs/spec/schema.sql)의 복합 외래키·CHECK 제약·호환 행렬이 이를 강제하며, **위반 14종이 PostgreSQL 16에서 실제로 거부되는 것을 실측 확인했다.** 목록은 [`docs/error/pg-violations.md`](docs/error/pg-violations.md).

---

## 빠른 시작

```bash
docker compose up --build
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8001/health
curl -X POST http://127.0.0.1:8000/v1/internal/claim -H "content-type: application/json" -d "{}"
```

Windows: `powershell -ExecutionPolicy Bypass -File scripts/smoke_w1.ps1`

시드에 `image.classify@1`·게이트 사슬·QUEUED task가 들어 있다. claim은 Core만 하며 `INSERT … SELECT`다.  
smoke는 placeholder safetensors dummy 추론까지 간다. **학습된 EuroSAT 모델이 아니다.**  
시드 해시를 바꾼 뒤에는 `docker compose down -v`가 필요하다. 전체 데모(scratch 완주·M25)는 이후 주에 README를 채운다.

---

## 문서

지도·읽는 순서: **[`docs/INDEX.md`](docs/INDEX.md)**

| 진입 | 내용 |
|------|------|
| [`STATE.md`](STATE.md) | 이번 주 상태 (자주 갱신) |
| [`docs/context-handoff.md`](docs/context-handoff.md) | 확정 결정·미결 |
| [`docs/spec/schema.sql`](docs/spec/schema.sql) | DDL 정본 v4.4 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 협업 초단 |
| [`docs/guide/github-team-guide.md`](docs/guide/github-team-guide.md) | 팀 GitHub 가이드 (Wiki 동기) |
| [Wiki](https://github.com/gncorpseo-commits/capnet/wiki) | 온보딩 허브 |

카테고리: `guide` · `error` · `history` · `design` · `spec` · `ops` · `research` — 전부 INDEX에 링크.

## 현재 상태

설계와 스키마는 동결되었고 실행 코드를 구현하는 단계다. 대회 MVP 목표일은 **2026년 8월 27일**.

## 라이선스

[Apache License 2.0](LICENSE). 고지 사항은 [`NOTICE`](NOTICE)를 참조한다.

사전학습 가중치를 사용하거나 동봉하지 않는다. 모델은 EuroSAT 데이터로 처음부터 학습한 것만 쓴다. 데이터셋은 EuroSAT RGB 배포판(Zenodo `7711810`, MIT)이며 원본은 저장소에 포함하지 않고 내려받는다.
