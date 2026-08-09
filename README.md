# CapNet — Capability Network

> README에는 **잘 안 바뀌는 것**만 둔다 (정의·실행·링크).  
> 상태·결정·일정·진척 → [`STATE.md`](STATE.md) · [`docs/context-handoff.md`](docs/context-handoff.md) · [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md)

**사용자는 능력만 요구한다. 승인한 신뢰 도메인 안의 기기로만 작업이 가고, 누가 무엇으로 실행했는지 증적이 남는다. 잘못된 조합은 앱이 아니라 DB가 거절한다.**

오픈소스 실행 계층. 사용자는 기기 주소를 모르고, 기기는 Core가 배정하지 않은 실행을 거부한다.

2026 오픈소스 개발자대회 출품작 (팀 지엔 · 접수 915).

---

## 심사 · 빠른 시작

사전: Docker Desktop. 시드/스키마를 바꾼 뒤에는 `docker compose down -v`가 필요할 수 있다.

```bash
docker compose up --build -d
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
powershell -ExecutionPolicy Bypass -File scripts/demo_violations.ps1
```

| 보고 싶은 것 | 위치 |
|--------------|------|
| 결과보고서 초안(양식 이식용) | [`docs/ops/contest-report-form-draft.md`](docs/ops/contest-report-form-draft.md) |
| 위반 거절(M25) | `scripts/demo_violations.ps1` / `.sh` |
| 지금 어디까지인지 | [`STATE.md`](STATE.md) |
| 제출·일정 정본 | [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md) |

Linux/macOS: `scripts/demo.sh`, `scripts/demo_violations.sh` (health 확인 후).  
더 많은 스크립트: 아래 [실행 스크립트](#실행-스크립트).

---

## 무엇이 다른가

AI 에이전트 스토어는 이미 많다. CapNet이 다루는 건 그 앞의 질문이다.

> **"같은 능력을 표방하는 두 에이전트를, 사용자가 모르는 채로 서로 바꿔 끼울 수 있는가?"**

Capability는 **이름이 아니라 계약**(스키마·골든셋·통과 기준)이다. 판정은 앱 `if`가 아니라 **PostgreSQL 제약**이 한다.

- 게이트 미통과 Agent에는 Task를 **할당할 수 없다**
- `team` Task는 `public` Node로 **내려갈 수 없다**
- `L` 계약은 `S` Node에서 **실행될 수 없다**
- 할당 중 Node 신뢰 등급을 **강등할 수 없다**
- 가중치 해시 불일치면 Node는 **READY가 될 수 없다**

스키마: [`docs/spec/schema.sql`](docs/spec/schema.sql). 위반 14종 실측: [`docs/error/pg-violations.md`](docs/error/pg-violations.md).

---

## 실행 스크립트

| 스크립트 | 하는 일 |
|----------|---------|
| `smoke_w1.ps1` | dummy 게이트 배관 + placeholder 추론 |
| `demo.ps1` / `.sh` | scratch 실게이트 → Task 완주 |
| `sanity.ps1` / `.sh` | 상수·난수·스키마위반 floor |
| `demo_violations` | M25 DB REJECTED |
| `score_n300` / `compare_ab` | n=300 채점 · paired 비교 (숫자는 STATE) |
| `train_scratch` | EuroSAT scratch → safetensors |

가중치가 없으면 `scripts/train_scratch.ps1`(또는 `.sh`). EuroSAT zip은 `scripts/download_eurosat.*`로 받고 저장소에 동봉하지 않는다. claim은 Core만 · `INSERT … SELECT`.

---

## 문서 (두 갈래)

| 누구 | 경로 |
|------|------|
| **심사·재현** | 이 README → 빠른 시작 → 결과보고서 초안 → (선택) 위반 데모 |
| **개발·에이전트** | [`CLAUDE.md`](CLAUDE.md) → [`STATE.md`](STATE.md) → 필요 시 [`docs/context-handoff.md`](docs/context-handoff.md) → [`docs/INDEX.md`](docs/INDEX.md) |

| 링크 | 역할 (정본) |
|------|-------------|
| [`STATE.md`](STATE.md) | 현재 단계·실측·체크리스트 |
| [`docs/context-handoff.md`](docs/context-handoff.md) | 확정 결정·미결 |
| [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md) | **대회 일정·제출 정본** |
| [`docs/ops/Contest_MVP_2026.md`](docs/ops/Contest_MVP_2026.md) | Contest 시나리오·UC (일정은 checklist) |
| [`docs/spec/schema.sql`](docs/spec/schema.sql) | DDL 정본 v4.4 |
| [`docs/INDEX.md`](docs/INDEX.md) | 문서 지도 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 협업 |
| [Wiki](https://github.com/gncorpseo-commits/capnet/wiki) | 온보딩 허브 |

---

## 라이선스

[Apache License 2.0](LICENSE). 고지: [`NOTICE`](NOTICE).

사전학습 가중치 미사용·미동봉. EuroSAT RGB(Zenodo `7711810`, MIT) scratch만. 원본 zip 미동봉 · `scripts/download_eurosat.*` · 핀 [`docs/spec/golden/eurosat-rgb.json`](docs/spec/golden/eurosat-rgb.json).
