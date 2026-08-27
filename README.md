# CapNet — Capability Network

> README에는 **잘 안 바뀌는 것**만 둔다 (정의·실행·링크).  
> 상태·결정·일정·진척 → [`STATE.md`](STATE.md) · [`docs/context-handoff.md`](docs/context-handoff.md) · [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md)

**사용자는 능력만 요구한다. 승인한 신뢰 도메인 안의 기기로만 작업이 가고, 누가 무엇으로 실행했는지 증적이 남는다. 잘못된 조합은 앱이 아니라 DB가 거절한다.**

오픈소스 실행 계층. 사용자는 기기 주소를 모르고, 기기는 Core가 배정하지 않은 실행을 거부한다.

2026 오픈소스 개발자대회 출품작 (팀 지엔 · 접수 915).  
출품 재현본(고정): [`v0.1.0-contest`](https://github.com/gncorpseo-commits/capnet/releases/tag/v0.1.0-contest) — 이후 개발은 이 저장소 `main`에서 계속한다 (D25).

---

## 심사 · 빠른 시작

사전: Docker Desktop (Compose v2). 추가로 내려받을 것은 없다 — 가중치와 골든셋 40장이 저장소에 들어 있다.

```bash
git clone https://github.com/gncorpseo-commits/capnet.git
cd capnet
docker compose up --build -d          # 1~3분
```

기동 순서는 `postgres` → `migrate`(일회성) → `core` → Node다. 새 볼륨은 `docs/spec/schema.sql`까지만 들어가고
그 뒤 세대는 `migrations/`에 있으므로, `migrate`가 끝나야 `core`가 뜬다. 적용 결과를 보려면:

```bash
docker compose logs migrate           # "완료 — 18개 적용" (재실행 시 "적용할 것 없음")
```

> **이 저장소를 이미 한 번 띄운 적이 있다면 `docker compose down -v` 로 볼륨까지 지우고 시작한다.**
> `-v` 없는 `down` 은 postgres 볼륨을 남기고, 그러면 초기화 스크립트가 **아예 돌지 않아**
> `migrate` 가 `0005` 에서 멈춘다 (`placeholder 가중치 Agent 에 라우팅 증서가 아직 … 남아 있다`).
> 처음 clone 한 경우에는 해당 없다.

**Linux / macOS**

```bash
bash scripts/demo.sh              # 능력 요구 → 자동 배정 → 실행 → 결과·증적
bash scripts/sanity.sh            # 정직하지 않은 에이전트 3종이 떨어지는지
bash scripts/demo_violations.sh   # 규칙 위반 6종을 DB가 거절하는지
```

**Windows** — 동명 `.ps1`

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
powershell -ExecutionPolicy Bypass -File scripts/sanity.ps1
powershell -ExecutionPolicy Bypass -File scripts/demo_violations.ps1
```

기대 출력

| 스크립트 | 성공 신호 |
|----------|-----------|
| `demo` | `score status=PASSED acc=0.8500` · `demo OK` · **증적 두 줄** (assignment·node·agent·status + 신뢰 도메인·티어) |
| `sanity` | 3종 전부 `FAILED` |
| `demo_violations` | `NOTICE ... REJECTED` **6건** (각 줄에 거절한 제약 이름) |

**보면 좋은 것 두 가지**

```bash
curl -s localhost:8000/v1/nodes-liveness      # 어느 기기가 살아 있고 얼마나 바쁜지
```

`scripts/demo.sh` **어디에도 기기 주소가 없다.** 사용자는 Core에 능력만 요구하고 결과를 받는다.
기기를 직접 부르면 거절된다.

```bash
curl -X POST localhost:8001/v1/execute -H 'content-type: application/json' \
  -d '{"id":"11111111-2222-4333-8444-555555555555","weights_sha256":"x","input_ref":"{}"}'
# -> HTTP 403  "assignment not leased to this node"
```

> 빈 볼륨에서 clone → compose up → 위 세 스크립트가 통과하는 것을 **2026-08-16**에 확인했다 (스키마 세대 18 · 마이그레이션 `0001`–`0018`).
>
> **이 기동은 데모·심사용이며, 열려 있는 것이 의도다.** 강제 플래그가 **기본 0**이라 관리 API 인증
> (`REQUIRE_API_KEY`)과 Node 증서 검증(`REQUIRE_NODE_CREDENTIAL`)이 꺼져 있고, postgres가 호스트로
> 공개되고, 마이그레이션이 자동으로 돈다(`CAPNET_AUTO_MIGRATE=1`). 심사위원이 키 발급 없이 한 번에
> 재현할 수 있게 한 선택이지, 강제 경로가 없어서가 아니다 — 제품은 오버레이로 그 넷을 뒤집는다:
>
> ```bash
> docker compose -f compose.yaml -f compose.prod.yaml up -d
> ```
>
> 부트스트랩 순서(첫 admin 키는 CLI로만 만들 수 있다)와 실측은 [`docs/guide/operate-production.md`](docs/guide/operate-production.md).

| 보고 싶은 것 | 위치 |
|--------------|------|
| 결과보고서 (양식 이식용 본문) | [`docs/ops/contest-report-form-draft.md`](docs/ops/contest-report-form-draft.md) |
| 상세·기술 보조 문서 | [`docs/ops/contest-report-draft.md`](docs/ops/contest-report-draft.md) |
| 위반 거절 (M25) | `scripts/demo_violations.sh` / `.ps1` |
| 쉬운 설명 | [`docs/guide/user-guide-ko.md`](docs/guide/user-guide-ko.md) |
| 지금 어디까지인지 | [`STATE.md`](STATE.md) |
| 제출·일정 정본 | [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md) |

---

## 무엇이 다른가

AI 에이전트 스토어는 이미 많다. CapNet이 다루는 건 그 앞의 질문이다.

> **"내 데이터를 남의 기계에 보내면서, 어디로 갔는지 나중에 답할 수 있는가?"**

대부분은 답하지 못한다. 로그에 모델 이름만 남고, 그 이름 뒤의 구현은 언제든 바뀔 수 있다.
정책을 문서에 적어 두는 것으로는 부족하다 — 문서는 우회되고 코드의 `if`는 빠뜨려진다.
**제약은 거절한다.**

**보장한다**

- 승인하지 않은 신뢰 도메인으로 **라우팅되지 않는다** (외래키 강제)
- 사용자는 **기기 주소를 모른다.** 기기는 Core가 배정하지 않은 실행을 거부한다 (HTTP 403)
- 누가·무엇으로·언제 실행했는지 **증적이 남고 조회된다**
- 살아 있고 덜 바쁜 기기로만 간다. 기기가 빠지면 대기했다가 복구 시 이어진다

**보장하지 않는다**

- 기기가 데이터를 남기지 않는다 — 추론은 평문을 요구한다. TEE 없이는 원리적으로 불가
- 두 에이전트가 **같은 답**을 낸다 — 등가는 선택 프로파일의 **관측값**이다

제품으로 **무엇을 유통할지**(초대 플릿 · 경제는 선택 · Private ≠ 안전): [`docs/design/product-distribution.md`](docs/design/product-distribution.md).

판정은 앱 `if`가 아니라 **PostgreSQL 제약**이 한다.

- **게이트를 붙인** Capability(`quality_profile='golden'`)에서는 미통과 Agent에 **할당할 수 없다**
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
