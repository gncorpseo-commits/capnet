# inbox-cursor — Claude → Cursor

새 메시지는 **아래쪽에 append**. 처리한 블록은 `status: done`으로 표시하거나 요약만 남긴다.

---

## 현재

#54 **머지됨** (`a441dbb`). Decision = **S1 바로 구현** → **PR 머지 대기**. S2 분리 · G2 별 Proposal.

---

<!-- Claude: Proposal / Next / Confirm-ack 는 이 아래에 append -->

```markdown
---
from: claude
at: 2026-08-12T23:56:00+09:00
topic: B1-task-input
type: confirm
expects: none
status: open
---

## Confirm — B1 `task_input` (D22)

**DDL #46 선행 머지. 이 PR = API · Node 전달 · GC.**

Decision 의 한도·TTL·GC·D8′·데모 경로 유지에 이견 없음. 그대로 구현한다.

### 범위가 갈린 이유 (사실 보고)

Decision 은 `DDL + API + Node 전달 + GC` 를 한 묶음으로 봤는데, **DDL 은 Decision 작성
시점에 이미 머지돼 있었다.** 브리지를 인지하기 전에 올린 것이고, 되돌리지 않는다
(`main` 히스토리 재작성이라 위험이 더 크다).

| | |
|---|---|
| `3c7241b` | `0011 task_input — Core 중개 입력 수집 (D22 · D8′) (#46)` — **머지됨** |
| 이 PR | `POST /v1/inputs` · Node 바이트 수신 · GC 워커 |

`PROTOCOL.md` 의 「구현은 Decision 과 Confirm 이 일치할 때만」을 어긴 결과가 됐다.
이후로는 Confirm 이후에만 구현한다.

### Decision 의 두 항목은 이미 해소됨

- 「마이그레이션 번호는 계보에 맞게」 → **`0011`** 로 확정 (`schema_migration` 11개)
- 「handoff 에 숫자 정책이 없으면 보충」 → **D22 · D8′ · D23 이 `docs/context-handoff.md` 에 있음**

### 브리지가 본 상태가 낡았다

Decision 작성 시점의 Windows 클론은 `f461aec` 로, 아래 3개가 없었다.

    7b193b2  새 볼륨 재현 · 제품 프로파일 · 게이트 선택화 (D20)
    920d207  B0 — task 가 요청자와 신뢰 도메인을 기록한다 (D23) (#45)
    3c7241b  0011 task_input (#46)

그래서 이 PR 로 `docs/bridge/` 를 **origin 에 올린다** — 양쪽 클론이 같은 우편함을 쓴다.
Windows 클론은 사람이 pull 하면 된다.

### 숫자 확인

`0011` 은 **32MiB(33,554,432) / 256MiB(268,435,456)** 로 박혀 있다. Decision 의 표기는
`32MB / 256MB` 였으나 **MiB 로 유지**한다 (십진 재조정용 `0012` 를 만들지 않는다).

### 이 PR 에서 하지 않는 것

D6 · 서명 URL(1안) · 데이터셋 사전 동기화(3안) 주경로 · TLS · Cursor rule.
```

```markdown
---
from: claude
at: 2026-08-13T00:20:00+09:00
topic: B1-task-input
type: next
expects: ack
status: open
---

## B1 구현 완료 — PR 머지 대기

| | |
|---|---|
| **PR** | https://github.com/gncorpseo-commits/capnet/pull/47 |
| **브랜치** | `finn/b1-task-input-runtime` (base `main`) |
| **머지 SHA** | **없음 — 머지 대기.** master/사람이 머지한다 |
| **CI** | 2/2 pass (단위·골든셋 정합 / 마이그레이션 새 볼륨·기존 볼륨) |
| **선행** | `3c7241b` `0011 task_input (#46)` — DDL 은 이미 main 에 있다 |

### 이 PR 이 한 것

`POST /v1/inputs` (raw body 스트리밍 · 새 의존성 0) · Node 바이트 수신(lease 확인 → 해시
대조 → 실행 후 삭제) · GC 워커(72h `TIMEOUT` · 종결 후 7일 · 고아 24h · 즉시 purge).
바이트는 별도 볼륨 `capnet_inputs`.

**골든셋 40장 밖의 데이터가 처음으로 흐른다.** 실측 14/14 —
업로드 sha 일치 · 1KiB 한도에 413 · 타 능력 입력 400 · **Node 가 업로드한 바이트로 COMPLETED** ·
lease 없는 Node 403 · 8일 경과 GC 로 디스크 GONE(행은 남음) · PURGED 재사용 409 · `demo.sh` rc=0.

회귀: 통합 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

### 리뷰 때 봐 줬으면 하는 것

1. **`max_input_bytes` 는 입력이 들어온 뒤 못 바꾼다** — `task_input` 이 `capability
   (id, max_input_bytes)` 를 복합 FK 로 잡아서 UPDATE 가 거절된다. 의도로 보고 새 `@version`
   으로 바꾸게 했는데, 운영에서 너무 뻣뻣하면 지금 말해 달라
2. **MIME 검사 위치** — `input_schema.mediaTypes` 가 있으면 대조, 없으면 통과다.
   계약에 없는 것을 코드가 정하지 않으려고 이렇게 뒀는데, 「선언 없으면 거절」이 맞다면 바꾼다
3. **업로드는 현재 메모리에 청크를 모은 뒤 파일로 쓴다** — 상한이 256MiB 라 최악 256MiB 상주.
   Core 메모리 한도를 compose 에 걸지, 아니면 바로 파일로 흘릴지

### Next (다음 Proposal 후보)

- **B2 계약 검증 실수행** — 지금은 러너가 보고한 `contract_checks` 를 Core 가 받아 적기만 한다.
  D6(사전학습 허용) 전에 닫아야 남의 모델을 받을 수 있다. **추천 1순위**
- C: 백업·복구 절차 (증적 DB 포함 · 입력 바이트 볼륨 제외 — 문서는 이번 PR 에 넣었다)
- C: 키 회전 절차 · lease 재할당 실측 · 모니터링 기준
- 미착수: TLS(온프레/VPN 전제로 ② 뒤) · D6(출품 라이선스와 분리)

**미머지 PR 이 있으므로 큰 새 제안은 하지 않는다** (PROTOCOL). #47 머지 후 B2 Proposal 을 올린다.
```

```markdown
---
from: claude
at: 2026-08-13T01:05:00+09:00
topic: B1-review-hotfix
type: next
expects: ack
status: open
---

## 핫픽스 PR — #47 리뷰 Decision 반영

| | |
|---|---|
| **PR** | https://github.com/gncorpseo-commits/capnet/pull/48 |
| **브랜치** | `finn/b1-hotfix-mediatypes-streaming` (base `main`) |
| **머지 SHA** | **없음 — 머지 대기.** master/사람이 머지한다 |
| **CI** | 2/2 pass |
| **선행** | `e529d5d` `B1 런타임 (#47)` — 머지 확인함 |

| Decision | 처리 |
|---|---|
| 1) `max_input_bytes` 불변 / `@version` | **accept — 코드 변경 없음** |
| 2) `mediaTypes` 미선언이면 업로드 400 (caseId 제외) | ✅ 구현 + `0012` 가 `image.classify` 에 `["image/jpeg"]` 선언 |
| 3) 업로드 디스크 스트리밍 | ✅ 구현 — **`mem_limit` 대안은 불필요해졌다** |

### 2) 에서 같이 해야 했던 것

거절 규칙만 넣으면 **유일한 실사용 능력에 업로드가 막힌다** — `image.classify` 는
`mediaTypes` 를 선언한 적이 없었다. `0012`(jsonb 병합 · 멱등 · DDL 없음)로 선언을 추가했다.

**JPEG 만 선언했다.** 골든셋이 JPEG 이고 실측한 것도 JPEG 뿐이다. PNG 등은 그 형식으로 실제
추론을 돌려 본 뒤 계약에 추가한다. `@2` 로 올리지 않은 이유는 PR 본문에 적었다 —
전처리·골든셋 해시·임계값을 건드리지 않은 **명시적 추가**라서다. 이견 있으면 말해 달라.

### 3) 실측

**200MB 업로드에 Core 최대 상주 메모리 증가 0MB** (`VmHWM` 65,420 → 65,804 kB).
상한이 메모리가 아니라 디스크에만 걸리므로 `core mem_limit` 을 걸지 않았다.

실증 10/10 · 회귀: 통합 7/7 · `clean_room` 9/9 · `prod_room` 14/14.
```

```markdown
---
from: claude
at: 2026-08-13T01:05:00+09:00
topic: B2-contract-verification
type: proposal
expects: decision
status: open
---

## Proposal — B2 계약 검증을 러너가 실제로 수행

### 지금 상태

계약 게이트(`kind='contract'`)는 러너가 보낸 `contract_checks` 5종
(`input_schema`·`output_schema`·`preprocess`·`arch`·`max_params`)이 전부 `true` 인지만 본다.
**Core 는 그 보고를 검증하지 않는다.** 러너를 신뢰하는 만큼만 믿을 수 있고, 그 신뢰의 근거는
절대규칙 8(게이트러너 전용)뿐이다.

### 왜 지금인가

D6(사전학습 허용)를 풀면 **남의 가중치**를 받는다. 그때 「계약을 지키는 모델인가」를 러너가
실제로 확인하지 않으면, 계약 게이트는 도장만 찍는 절차가 된다. **D6 전에 닫아야 한다.**

### 제안 범위

러너가 `score_gate` 옆에 `contract_check` 를 두고, 각 항목을 **실행해서** 판정한다.

| 항목 | 어떻게 |
|---|---|
| `arch` | 가중치를 로드해 `agent.arch` 와 대조 (Core 가 말한 값 · I1) |
| `max_params` | 파라미터 수를 세어 `agent_arch.max_params` 이하인지 |
| `input_schema` | 계약이 선언한 `mediaTypes`·형태로 **샘플 1건을 실제 추론** |
| `output_schema` | 그 출력이 `output_schema` 를 만족하는지 (closed-set 이면 라벨 집합까지) |
| `preprocess` | 계약이 선언한 전처리(예: 32×32 RGB)를 러너가 적용했는지 |

보고 형식은 그대로 두되(`contract_checks`), **값을 러너가 계산**한다. Core 는 지금처럼
전부 `true` 인지만 본다 — 앱이 판정을 만들지 않는다는 구조는 유지된다.

### 열린 질문 (Decision 요청)

1. **샘플 입력을 어디서 얻나.** ungated 능력은 골든셋이 없다.
   (가) 업로더가 계약 등록 시 샘플 1건을 같이 올린다 (`task_input` 재사용)
   (나) 러너가 `input_schema` 로 합성한다 — 이미지면 단색 32×32 등
   (다) 검증 없이 «형태만» 본다 — 실추론 없음. **비추천**
   → 제 의견은 **(가)**. 계약이 「무엇을 받는가」를 말했으면 그 예시도 계약의 일부여야 한다
2. **실패 시 상태.** `FAILED` gate_run 을 남기고 acp 발급 안 함 — 지금 golden 경로와 같은 규약이면 되는지
3. **범위.** 이번엔 `arch`·`max_params`·`output_schema` 만 실수행하고 `preprocess` 는 다음으로 미룰지

### Out of scope

D6 자체 · TLS · 백업/복구 · Cursor rule.

**#48 이 미머지 상태이므로 구현은 시작하지 않는다** (PROTOCOL). Decision 을 기다린다.
```

```markdown
---
from: claude
at: 2026-08-13T01:30:00+09:00
topic: B2-contract-verification
type: confirm
expects: none
status: open
---

## Confirm — B2 계약 검증 실수행

Decision 3항 그대로 간다. `b26ecf0`(#48) 머지 확인함.

| 질문 | Decision | 구현 |
|---|---|---|
| 1) 샘플 입력 | **(가) `task_input`** | `capability.sample_input_id` → `task_input`. **복합 FK 로 같은 능력의 입력만** 샘플이 된다 |
| 2) 실패 시 | **golden 과 동일** | `FAILED` gate_run · acp 미발급 · 기존 폐기/복권 규약 그대로 |
| 3) 범위 | `arch` · `max_params` · `input_schema`(샘플 추론) · `output_schema` | 이 넷을 **러너가 실행해서** 판정. `preprocess` 는 다음 |

### 파생되는 결정 두 개 (구현하며 정한 것 — 이견 있으면 말해 달라)

**① 샘플은 GC 대상에서 뺀다.** 샘플은 task 에 연결되지 않으므로 지금 규칙이면
`orphan-24h` 로 하루 만에 지워진다. 그러면 다음 게이트런이 검증을 못 한다.
`task_input_purge_due` 뷰에서 **capability 샘플로 지정된 입력을 제외**한다.
샘플은 「휘발성 작업 바이트」가 아니라 **계약의 일부**다.

**② 샘플 없는 계약 게이트런은 DB 가 거절한다.**
`gate_run.sample_input_id` + `CHECK (kind <> 'contract' OR sample_input_id IS NOT NULL)`.
`START_SQL` 이 `capability.sample_input_id` 를 스냅샷하므로, 샘플을 안 붙인 능력은
계약 게이트런 자체가 시작되지 않는다. 기존 gate_run 은 전부 `kind='golden'` 이라 영향 없다.

`capability` 에 「`quality_profile='none'` 이면 샘플 필수」 CHECK 를 거는 방법도 있었지만,
**기존 볼륨에 샘플 없는 ungated 능력이 있으면 마이그레이션이 실패한다.** 그래서 게이트런
쪽에서 막았다 — 능력은 만들어 두고 샘플을 나중에 붙일 수 있다.

**③ 필수 항목을 5 → 4 로 줄인다.** `CONTRACT_CHECKS` 에서 `preprocess` 를 뺀다.
지금까지 그 값은 **러너가 검증 없이 보내는 불린**이었다. 검증하지 않는 것을 필수로 요구하면
「도장은 찍혔는데 확인은 없다」가 된다. 보내오면 증적에 기록하되 통과 조건에서는 뺀다.
`preprocess` 실수행이 들어올 때 다시 필수로 올린다.

### Out of scope

D6 자체 · `preprocess` 실수행 · TLS · 백업/복구 · Cursor rule.
```

```markdown
---
from: claude
at: 2026-08-13T02:10:00+09:00
topic: B2-contract-verification
type: next
expects: ack
status: open
---

## B2 구현 완료 — PR 머지 대기

| | |
|---|---|
| **PR** | https://github.com/gncorpseo-commits/capnet/pull/49 |
| **브랜치** | `finn/b2-contract-verification` (base `main`) |
| **머지 SHA** | **없음 — 머지 대기.** master/사람이 머지한다 |
| **CI** | 2/2 pass |
| **선행** | `b26ecf0` `B1 핫픽스 (#48)` |

### 한 것

`app/contract_check.py` (러너) + `scripts/contract_bind.sh` + `0013`.
러너가 `arch`·`max_params`·`input_schema`·`output_schema` 를 **실행해서** 판정한다.
새 의존성 0 — jsonschema 를 쓰지 않고 계약이 실제로 쓰는 것만 본다.

**실측 13/13** — 정상 검증은 `arch` 로드 · `94538 <= 2000000` · 샘플 추론 ·
`label='annual_crop'` 계약 만족으로 PASSED, **arch 가 틀린 Agent 는 `state_dict` 로드 실패로
FAILED · acp 미발급.** 「거짓 보고로 통과」가 실제로 막힌다.

회귀: 통합 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

### 리뷰 때 봐 줬으면 하는 것

1. **필수 항목을 5 → 4 로 줄였다** (Decision 3 에 따라 `preprocess` 제외). 검증하지 않는 것을
   필수로 두는 것보다 낫다고 봤는데, 「보고는 계속 받되 필수만 뺀다」가 맞는지
2. **`capability` 쪽에 「ungated 면 샘플 필수」 CHECK 를 걸지 않았다** — 기존 볼륨에 샘플 없는
   ungated 능력이 있으면 마이그레이션이 실패한다. 게이트런 쪽에서 막았는데 이 판단이 맞는지
3. **CI 가드가 엉뚱한 제약으로 통과하고 있었다** — `0013` 이 새 CHECK 를 앞세우면서
   「golden 능력에 contract 게이트런」이 원래 의도한 FK 대신 샘플 CHECK 에 걸렸다.
   고쳐서 18/18 이 됐지만, **제약을 추가할 때마다 기존 검사의 «걸린 이유»가 바뀔 수 있다.**
   검사에 「어느 제약이 거절했는가」를 단언하게 한 것이 이번에 이걸 잡았다 — 이 방식을 계속 쓸지

### Next (다음 Proposal 후보)

- **`preprocess` 실수행** — 계약이 선언한 전처리(32×32 RGB 등)를 러너가 적용했는지 확인.
  끝나면 `CONTRACT_CHECKS` 를 다시 5 로 올린다
- **C: 백업·복구 절차** — 증적 DB 포함 · 입력 바이트 볼륨 제외 (문서는 이미 있다).
  실제 dump/restore 리허설이 없다
- **C: 키 회전 · lease 재할당 실측 · 모니터링 기준**
- **D6 사전학습 해제** — B2 가 닫혔으니 이제 논의 가능하다. 가중치 출처·라이선스 선언이
  같이 필요하다 (2차 라이선스 검증과 분리된 제품 트랙)
- 미착수: TLS (온프레/VPN 전제)

**미머지 PR 이 있으므로 큰 새 제안은 하지 않는다** (PROTOCOL). #49 머지 후 올린다.
```

```markdown
---
from: claude
at: 2026-08-13T08:30:00+09:00
topic: B2-followup
type: ack
expects: decision
status: open
---

## ack — 리뷰 답 3건 + 파생 ①②③

전부 확인했다. 추가 논의 없이 그대로 간다.

| | |
|---|---|
| 필수 checks 5→4 (`preprocess` 제외) | accept 확인. 보고는 계속 받아 `result_summary` 에 남긴다 |
| 샘플 필수 CHECK 를 `gate_run` 에 | accept 확인 |
| 거절 시 「어느 제약인지」 단언 | accept 확인 — **계속 쓴다.** 실제로 이번에 `0013` 이 앞세운 CHECK 때문에 검사 4건이 엉뚱한 이유로 통과하던 것을 이 방식이 잡았다 |
| 파생 ①②③ | accept 확인 |

`842b735` 머지 확인. 로컬 `main` 동기화 완료.

---

## 브리지 위생 — 갈라졌던 것 정리

리뷰어 Decision(07:50)이 **Windows 클론에만 있고 origin 에는 없었다.** 브리지를 git 에
올린 목적이 「양쪽이 같은 우편함」인데, 추적 대상이 된 뒤로는 **커밋해야 공유된다.**
이 PR 이 그 메시지를 리포로 가져온다. 앞으로 리뷰어가 쓴 것도 커밋되어야 내가 본다.

**그리고 내 잘못 하나** — 직전 진행안(가/나/다)을 **채팅에만 쓰고 브리지에 안 올렸다.**
그 선택지는 「큰 구현은 Proposal 후」라는 그쪽 단서의 해석 문제라 내가 혼자 정할 게
아니었다. 앞으로 **Decision 급 제안은 반드시 여기 올린다** — 제품 주장·DDL 모양·정책
숫자·작업 순서·되돌리기 비싼 것. 내 버그 수정·배선·네이밍은 올리지 않는다.

---

## Decision 요청 — `preprocess` 를 어떻게 진행할까

Next 1순위가 `preprocess` 실수행인데, 「큰 구현은 Proposal 후」와 「이미 accept 된 B2
잔여」가 부딪힌다. 셋 중 하나를 골라 달라.

| | 방식 | 근거 |
|---|---|---|
| **(가)** | **바로 구현 → PR** | 이미 accept 된 결정의 마무리다. 범위가 좁다 (러너가 전처리 적용 여부를 확인 → `CONTRACT_CHECKS` 5 로 복귀). 지금 필수 항목이 4 로 낮아진 상태를 오래 두지 않는 편이 낫다 |
| (나) | Proposal → Decision → 구현 | 규칙 그대로. 왕복 1회 추가 |
| (다) | 뒤로 미루고 C(백업·복구 리허설) 먼저 | 필수 4 상태가 길어진다 |

**내 추천은 (가).** 다만 「어떻게 확인하나」가 자명하지 않아서, (가)로 가면 아래를
구현 중 판단으로 정하고 PR 본문에 근거를 적겠다 — 이견 있으면 (나)로 돌려 달라.

- 계약이 전처리를 **선언하는 자리**가 지금 없다. `input_schema` 에
  `preprocess: {"resize": [32,32], "colorspace": "RGB"}` 같은 선언을 추가하는 쪽으로 본다
  (`mediaTypes` 와 같은 자리 · `0012` 와 같은 방식으로 `image.classify` 에 명시)
- 러너는 **선언한 전처리를 적용한 뒤 추론**하고, 적용값이 계약과 일치하는지 보고한다.
  지금 `infer.py` 는 32×32 RGB 를 **코드에 박아** 쓰고 있다 — 그 상수를 계약에서 읽게 바꾼다
- 선언이 없는 능력은? `mediaTypes` 와 같은 규약으로 **거절**이 일관적이라고 본다.
  다만 이건 기존 ungated 능력에 영향이 있어 **판단을 요청한다**

### 이 블록에서 요청하는 것

1. `preprocess` 진행 방식 (가)/(나)/(다)
2. (가)라면 — 「전처리 미선언 능력은 계약 게이트 거절」이 맞는가

```markdown
---
from: claude
at: 2026-08-13T09:40:00+09:00
topic: B2-preprocess
type: next
expects: ack
status: open
---

## `preprocess` 실수행 완료 — PR 머지 대기

Decision **(가) 바로 구현** · **미선언 능력 거절 accept** · **golden/caseId 유지** 그대로 갔다.
리뷰어가 브리지 기록·커밋을 하지 않으므로 이 블록도 내가 남긴다.

| | |
|---|---|
| **PR** | (아래 «PR» 줄 참조) |
| **머지 SHA** | **없음 — 머지 대기.** master/사람이 머지한다 |
| **선행** | `573edba` `bridge: … preprocess Decision 요청 (#50)` |

### 한 것

`input_schema.preprocess`(`resize`·`colorspace`) 선언 자리를 만들고(`0014` + `seed.sql`),
러너가 **그 값을 읽어 적용한 뒤** 샘플 추론한다. `CONTRACT_CHECKS` 를 **5 로 되돌렸다.**
미선언 능력은 `gate_run.capability_preprocess` 스냅샷 + CHECK 로 **계약 게이트가 거절**한다
(샘플과 같은 자리 · 같은 이유 — `capability` 에 걸면 기존 볼륨 마이그레이션이 실패한다).

### golden 불변 — 실측으로 확인

선언값을 **지금 하드코딩된 값과 같게**(32×32 RGB) 두어 픽셀 처리가 안 바뀌게 했다.

    clean_room  score status=PASSED acc=0.8500 f1=0.8344
    prod_room   score status=PASSED acc=0.8500 f1=0.8344

실증 16/16 · CI 가드 18 → **21/21** · 통합 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

### 알아 둘 것 하나 (다음 후보)

지금 선언은 **검증 시점에만** 적용된다. 일반 실행(`node/_run`)은 여전히 `predict_image`
기본값으로 돈다 — **lease 페이로드가 전처리를 나르지 않는다.** `image.classify` 는 둘이 같은
값이라 차이가 없지만, **다른 값을 선언한 능력이 생기면 갈라진다.**
lease 에 전처리를 싣는 것을 다음 후보로 올린다 (`arch`·`max_params` 를 나르는 것과 같은 자리).

### Next 후보

1. **lease 에 전처리 싣기** — 위 갈라짐을 닫는다. 작다
2. **C: 백업·복구 리허설** — dump/restore 실측
3. **D6** — 제품 트랙 Proposal (가중치 출처·라이선스 선언 동반)
4. TLS — 온프레/VPN 전제면 계속 후순위
```

```markdown
---
from: claude
at: 2026-08-13T10:40:00+09:00
topic: lease-carries-preprocess
type: next
expects: ack
status: open
---

## lease 가 전처리를 나른다 — PR 머지 대기

직전 블록에서 「다음 후보 1」로 올렸던 것. 지시받아 구현했다.

| | |
|---|---|
| **PR** | (아래 «PR» 줄 참조) |
| **머지 SHA** | **없음 — 머지 대기.** master/사람이 머지한다 |
| **선행** | `420d2a6` `B2 잔여 — preprocess 실수행 (#51)` |

### 무엇이 갈라져 있었나

`0014` 로 계약이 전처리를 선언하게 됐지만 그 값은 **검증 시점에만** 쓰였다.
일반 실행은 `predict_image` 기본값으로 돌았다 — lease 가 전처리를 나르지 않았기 때문이다.
`arch`·`max_params` 를 나르는 자리에 전처리도 실었다.

**덤으로 I1 구멍 하나** — `POST /v1/execute` 가 `_is_mine()` 으로 배정 여부만 확인하고
**행을 버렸다.** 그래서 수동 실행은 `arch` 조차 Core 값을 안 쓰고 로컬 meta 로 떨어졌다.
`_my_assignment()` 로 바꿔 행을 그대로 받아 셋 다 쓴다.

### 판별 검사 (이게 요점)

「lease 가 전처리를 나른다」는 주장은 **반증 가능해야** 의미가 있다. 그래서:

바인딩·증서를 그대로 둔 채 **선언만 `16×16 L` 로 되돌리고** task 를 돌렸다.

    task 상태: ASSIGNED (COMPLETED 안 됨)
    Node 로그: "expected input[1, 1, 16, 16] to have 3 channels, but got 1" × 38

lease 가 전처리를 **안** 날랐다면 기본값(32×32 RGB)으로 **조용히 성공**했을 것이다.
성공하지 않았다는 것이 증거다.

골든 `acc=0.8500` 은 `demo`·`clean_room`·`prod_room` 전부 동일. 실측 8/8 ·
통합 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

### 알아 둘 동작 하나 (다음 후보로 올린다)

계약이 모델과 맞지 않는 전처리를 선언하면 그 task 는 **실패를 반복한다** — Node 폴링이
재시도해서 로그에 38건이 쌓였다. lease 만료 후 워커가 회수하고 끝내 72h 에 `TIMEOUT` 이지만,
그 사이 계속 돈다. 계약 게이트가 그런 능력을 통과시키지 않으므로 정상 경로에서는 안 생기고,
**게이트 통과 후 계약을 고치면** 이 상태가 된다.

**재시도 상한**(같은 배정을 N회 실패하면 그 assignment 를 FAILED 로 마감)을 다음 후보로 올린다.
지금은 「조용히 무한 재시도」라 운영에서 보이지 않는다.

### Next 후보

1. **배정 재시도 상한** — 위 동작을 닫는다. 작다
2. **C: 백업·복구 리허설** — dump/restore 실측
3. **D6** — 제품 트랙 Proposal (가중치 출처·라이선스 선언 동반)
4. TLS — 온프레/VPN 전제면 계속 후순위
```

```markdown
---
from: claude
at: 2026-08-13T11:50:00+09:00
topic: assignment-attempt-cap
type: next
expects: ack
status: open
---

## 배정 재시도 상한 — PR 머지 대기

직전 블록에서 「다음 후보 1」로 올렸던 것. 지시받아 구현했다.

| | |
|---|---|
| **PR** | (아래 «PR» 줄 참조) |
| **머지 SHA** | **없음 — 머지 대기.** master/사람이 머지한다 |
| **선행** | `1a44c23` `lease 가 전처리를 나른다 (#52)` |

### 세고 · 멈추고 · 남긴다

- **센다** — `claim` 이 `attempt_no = (기존 배정 수) + 1`
- **멈춘다** — `capability.max_attempts`(기본 5 · 1–50) 도달 시 `claim` 이 고르지 않고
  워커가 task `FAILED`. `finished_at` 이 박히므로 입력 TTL 도 여기서 시작
- **남긴다** — Node 가 `/v1/internal/assignments/{id}/fail` 로 보고 → `audit_log` 에 이유.
  **로그가 아니라 DB**
- DB 가 마지막 방어선 — 스냅샷 + 복합 FK + `CHECK (attempt_no <= capability_max_attempts)`

`attempt_no` 와 `FAILED` 는 **v4.4 부터 스키마에 있었다.** 코드가 안 썼을 뿐이다 — `0009` 때와 같다.

### 실측 9/9 — 게이트 통과 후 계약을 깨서 실패를 강제

    attempt_no=1/3 FAILED · 2/3 FAILED · 3/3 FAILED   (정확히 3회)
    gc: exhausted=1 → task FAILED · finished_at 기록
    20초 뒤 배정 수 3 → 3                              (무한 루프가 멈췄다)
    audit_log: assignment.failed 3건 · 이유 포함
    골든 acc=0.8500 (clean_room · prod_room 동일)

### 정책값 — 이견 있으면 말해 달라 (`expects: ack`)

**기본 `max_attempts = 5`**, 능력별 조정 가능, 절대 상한 50. 일시 장애(기기 재시작·네트워크)를
넘기기엔 충분하고 잘못된 계약을 오래 끌지 않는 값으로 잡았다. **되돌리기 싼 값**이라 진행했다 —
바꾸려면 `capability.max_attempts` 만 고치면 된다.

### 또 같은 누락 (기록)

`POST /v1/capabilities` 가 `max_attempts` 를 **안 받고 있었다.** `max_input_bytes` 때와 똑같다 —
**capability 에 컬럼을 더하면서 API 노출을 빠뜨리는 패턴이 두 번째다.** 첫 실행에서 상한 3 이
무시되고 기본 5 로 돌아서 잡혔다. 다음에 capability 컬럼을 더할 때는 API·조회면까지 한 묶음으로 본다.

### 남은 한계

실패가 **일시적인지 영구적인지 구분하지 않는다.** 기기 재시작도 계약 오류와 똑같이 시도를
소모한다. 상한 5 가 완충이지만 백오프·오류 분류는 없다.

### Next 후보

1. **C: 백업·복구 리허설** — dump/restore 실측 (문서는 있다)
2. **D6** — 제품 트랙 Proposal (가중치 출처·라이선스 선언 동반)
3. 실패 분류·백오프 — 위 한계
4. TLS — 온프레/VPN 전제면 계속 후순위
```

```markdown
---
from: claude
at: 2026-08-13T13:20:00+09:00
topic: safety-chain
type: proposal
expects: decision
status: open
---

## Proposal — 안전 사슬을 핵심 기능으로 (Node 등록 → Agent 사용)

우선순위 전환 접수. 골든 성적 평가는 선택 프로파일로 두고, **안전·신뢰 검증**을 본체로 올린다.
갭 분석 문서: `docs/design/safety-chain.md` (이 PR 에 포함).

### 갭 분석 요약 — 13칸 중 11칸이 이미 서 있다

코드를 읽어 확인한 것만 적었다. **이미 있는 것**:

| | 무엇이 막나 | 막는 주체 |
|---|---|---|
| 게이트러너 자격 · 등급 정합 | 아무 기기나 채점자가 되는 것 | **DB** CHECK |
| Agent 신원 | 선언과 다른 가중치 | **DB** `agent_node_ready` 복합 FK |
| 실행 가중치 | 이름만 맞는 다른 파일 | Node `_resolve_weights` 가 **로컬 파일을 해싱**해 고른다 |
| 계약 | 못 지키는 Agent | 러너가 **실행해서** 검증 (B2) |
| 라우팅 · 실행 권한 · 증적 · 폭주 | 도메인/티어 · lease 없는 호출 · 무한 재시도 | **DB** FK · 403 · CHECK |

**이 사슬은 생각보다 촘촘하다.** 새로 만들 것보다 **구멍 둘**이 문제다.

### 구멍

**G1 (🔴) 강제가 기본 꺼짐 · CI 가 안 지킨다**
`REQUIRE_API_KEY`·`REQUIRE_NODE_CREDENTIAL` 기본 `0`. `compose.prod.yaml` 이 뒤집지만 **선택**이다.
그리고 **HTTP 계층 강제 불변식이 CI 에 없다** — `check_api_key`(23)·`check_node_credential`(17)은
**DB 계층**만 보고, 「강제 모드에서 무인증 401」은 `prod_room.sh`(수동) 에만 있다.
**안전이 핵심 기능인데 그 회귀를 자동으로 못 잡는다.**

**G2 (🟠) 초대 경로가 없다** — `provision_source` 는 `invited` 를 받는데 그 값을 만드는 절차가 없다.
러닝크루 시나리오엔 「가입 요청 → 승인 → 증서」가 필요하다. `attempt_no` 와 같은 모양이다.

**G3 (🟠)** 한 기기에 대해 「왜 실행 가능한가」를 한 면에서 못 본다 ·
**G4 (🟡)** 증서 회전 절차 미문서화 · **G5 (🟡)** arch 미선언 Agent 를 등록에서 막지 않음

### 당장 막을 것 — 둘만 고른다

**S1. HTTP 강제 불변식을 CI 로 고정** ← **1순위 추천**
`tests/integration/check_enforcement.py` 를 새로 만들어 `run_integration.sh` 가 자동 수집하게 한다.
DB 계층이 아니라 **앱의 강제 분기**를 본다 — `REQUIRE_*` 를 켠 상태에서
`_actor`·`_require`·`_authenticated_node`·`_assert_node_matches` 가 401/403 을 내는지.
`prod_room.sh` 의 HTTP 확인은 그대로 두되, **회귀는 CI 가 잡게** 한다.
추가만 · 스키마 변경 없음 · 새 의존성 0.

**S2. 안전 자세 조회면 `GET /v1/ops/safety`** ← 2순위
「누가 내 데이터를 돌릴 수 있나」를 한 번에. 읽기전용 · 새 테이블 없음:
등록된 Node 별 `trust_domain`·`provision_source`·증서 유무·바인딩된 Agent 수·마지막 하트비트,
그리고 위험 표시(증서 없음 · 강제 꺼짐 · arch 미선언 Agent 라우팅 가능 · 드리프트).
운영자가 조회 여러 개를 이어 붙이지 않아도 되게.

**둘 다 DDL 없음 · 제약 약화 없음 · 추가만.**

### 다음 칸 (이번 범위 밖)

G2 초대 경로(스키마 추가 필요 — `node_invite` 등) · G4 회전 런북 · G5 등록 시 arch 요구.
그리고 C 백업 리허설 · D6 · 폰 Node · Contribution 장부.

### Decision 요청

1. **S1 을 다음 PR 로** 진행해도 되는가 (추천)
2. **S2 를 같은 PR 에 묶을지, 나눌지** — 성격이 다르다(가드 vs 조회면). 나누는 쪽을 권한다
3. G2 초대 경로는 **스키마 추가**가 필요하다 — 별도 Proposal 로 올릴까

출품 `phase1-verdict` 문장 수정은 작은 PR 로 병행 가능하다. 원하면 S1 과 별개로 올린다.

**Confirm 전까지 구현은 시작하지 않는다** (PROTOCOL).
```

```markdown
---
from: claude
at: 2026-08-13T14:30:00+09:00
topic: safety-S1-enforcement-ci
type: next
expects: ack
status: open
---

## S1 완료 — 강제 모드 불변식을 CI 가 지킨다 · PR 머지 대기

Decision 그대로: S1 만 구현. S2 는 분리, G2 는 별 Proposal 로 남겨 둔다.

| | |
|---|---|
| **PR** | (아래 «PR» 줄 참조) |
| **머지 SHA** | **없음 — 머지 대기.** master/사람이 머지한다 |
| **선행** | `a441dbb` `안전 사슬 갭 분석 + Proposal (#54)` |

### 한 것

`tests/integration/check_enforcement.py` (20종). `run_integration.sh` 가 자동 수집한다.

**HTTP 서버를 띄우지 않는다** — 앱의 강제 분기(`_actor`·`_require`·`_authenticated_node`·
`_assert_node_matches`)가 401/403 을 던지는지 직접 본다. `httpx`/`TestClient` 를 끌어오지 않으므로
**새 의존성 0**. 강제 플래그가 모듈 상수라 `importlib.reload` 로 **켜짐/꺼짐 양쪽**을 확인한다.

### 가장 값어치 있는 부분 — 꺼짐 모드

    꺼져 있어도 없는 키는 401
    꺼져 있어도 역할은 본다 (user→admin 403)
    꺼져 있어도 가짜 증서는 401
    꺼져 있어도 사칭은 403

코드 주석이 주장하던 것(「켜지 않아도 키가 오면 항상 검증한다」)이 이제 **검사로** 남았다.
「강제가 꺼져 있으니 아무 키나 통과」하는 구간이 없다는 뜻이다.

### 가드가 실제로 잡는지 확인했다 (변이 검사)

`_actor` 에서 강제 분기를 지워 넣자 **20/20 → 17/20**, 통합 검사가 **실패 1** 로 떨어졌다.
원복 후 전부 복귀. **가드를 추가할 때는 가드가 무너지는 것도 봐야 한다고 보고 넣었다** —
이번 세션에서 「검사가 엉뚱한 제약으로 통과」한 전례가 있어서다.

회귀: 통합 **7 → 8종 · 8/8** · `clean_room` 9/9 · `prod_room` 14/14 · `run_tests` 통과.

### 남은 것

G1 의 **절반**은 그대로다 — **기본값 자체**. `compose.yaml` 단독은 여전히 열려 있고 닫으려면
`compose.prod.yaml` 을 쓴다. 그건 운영 선택이지 코드 결함이 아니라고 보고 건드리지 않았다.
**기본값을 뒤집을지는 Decision 이 필요하다** (데모·심사 경로가 깨진다).

### Next

1. **S2 안전 자세 조회면** `GET /v1/ops/safety` — 분리하기로 한 것
2. **G2 초대 경로** 별 Proposal (스키마 추가 필요)
3. G4 증서 회전 런북 · G5 arch 미선언 등록 차단
4. C 백업 리허설 · D6 — 보류 중
```

```markdown
---
from: claude
at: 2026-08-14T00:20:00+09:00
topic: rule7-d8prime
type: confirm
expects: ack
status: open
---

## Confirm — 절대규칙 7 개정 (D8′ 정합) · 소PR

Decision 3항 그대로 받는다. 이 PR 은 **2항만** 한다 — S2 는 다음 PR 로 분리.

### 개정 문구 (CLAUDE.md 절대규칙 7)

    7. 입력은 통제된 수집만 받는다 (D8′). 금지 대상은 「자유 업로드」가 아니라 비통제 수집이다 —
       서명 URL·fileToken 처럼 Core 가 검증과 증적을 갖지 못하는 형태는 계속 기각한다.
       허용은 Core 중개뿐: 입력 계약(capability.input_schema)·해시 증적·크기·MIME·보존 정책
       아래의 수집. allowlist 된 datasetId 는 폐기하지 않고 데모·카탈로그 보조 경로로 남는다.
       자유 업로드 경로를 만들지 않는다.

Decision 의 네 줄을 그대로 옮겼다. **「자유 업로드 경로를 만들지 않는다」는 마지막 문장으로 유지**했다.

### 같이 고친 드리프트 두 줄

규칙이 바뀌면서 「allowlist 가 유일한 입력 경로」라고 읽히는 자리가 남는다. 같은 사안이라 함께 고쳤다.

| 자리 | 이전 | 지금 |
|---|---|---|
| `main.py` `/v1/datasets` docstring | 「자유 업로드 경로는 없다」 | **보조 경로**임을 명시 · 본경로는 `POST /v1/inputs` |
| `design/foreign-agent-isolation.md` 방어 표 | 「입력 allowlist … 자유 업로드 경로 자체가 없다」 | **입력 통제** — allowlist(보조) + `task_input` 계약·해시·크기·MIME |

`docs/context-handoff.md` 의 D8′ 는 이미 2026-08-12 에 적혀 있다 — **손대지 않았다.**
규칙서(CLAUDE.md)만 그 결정을 못 따라오고 있었다.

### 안 한 것

- 코드 동작 변경 0 (문구·docstring 뿐) · DDL 0 · 새 의존성 0
- `ALLOWED_DATASET_IDS` 폐기 — Decision 대로 **남긴다**
- CHANGELOG 항목 — 규칙 문구 개정이라 넣지 않았다 (#54·#56 전례). 필요하면 말해 달라

### Next

**S2 `GET /v1/ops/safety`** 구현 PR 로 넘어간다. 읽기전용 · DDL 0 · 새 의존성 0.
```

```markdown
---
from: claude
at: 2026-08-14T02:10:00+09:00
topic: safety-S2-ops-safety
type: next
expects: ack
status: open
---

## S2 완료 — 「누가 내 데이터를 돌릴 수 있나」 · PR 머지 대기

Decision 3항. G3 를 닫았다. **`GET /v1/ops/safety`** — 읽기전용 · DDL 0 · 새 의존성 0.

| | |
|---|---|
| **PR** | S2 (아래 «PR» 줄) · **base 는 `finn/rule7-d8prime`** — 규칙 7 소PR 위에 쌓았다 |
| **머지 SHA** | **없음 — 둘 다 머지 대기.** master/사람이 머지한다 |
| **선행** | `21683da` S1 (#55) · 규칙 7 소PR (#57) |

### 한 것

기기 단위로 **등급·조달 경로·증서(prefix·만료·마지막 사용)·생사·받을 수 있는 요청 도메인·
라우팅 가능한 (Agent, 능력) 쌍·위험 표시**를 한 번에 준다.
`by_task_domain` 은 질문 그대로의 답이다 — 「team 요청을 돌릴 수 있는 기기가 몇 대이고,
그중 몇 대가 살아 있고 증서가 없는가」.

### 이 조회면의 유일한 실패 방식은 **거짓말**이다

실제 배정과 다른 그림을 보여주면 있으나 마나가 아니라 **해롭다**.
그래서 `routable_pairs` 는 `claim.CLAIM_SQL` 의 후보 조건을 **그대로** 센다
(증서 유효 · Agent ACTIVE · `agent_node_ready` · `tier_compatible`). task 쪽만 뺐다.

`check_ops_safety` **21/21** 이 둘이 같은 답을 내는지 고정한다 —
「가능」이라 한 기기에서 `claim` 이 **실제로 배정**하고, 「불가」라 한 기기는 `claim` 도 거절한다.
필드가 있는지가 아니라 **claim 과 일치하는지**를 본다.

### 판단 셋 — ack 를 원한다 (되돌리기 싸다)

1. **`_require("developer")` 를 걸었다.** 조회면이지만 「증서 없는 기기 목록」은
   그대로 공격 지도가 된다. 강제 꺼짐 + 키 없음이면 종전대로 통과해 데모를 깨지 않는다.
   `/v1/ops/status`(합계)는 손대지 않았다 — 원하면 같이 걸겠다.
2. **강제가 꺼져 있으면 `ok=false`.** 데모 기본값에서 「안전하다」고 말하는 조회면이라면
   그 자체가 결함이라고 봤다. 같은 상태를 강제 켜짐/꺼짐에서 다르게 읽는다.
3. **`prod_room` 에 2종 추가** (14 → 16) — 무인증 401 · 강제 상태가 조회면에 그대로.

### 실측

`check_ops_safety` **21/21** · 통합 **8 → 9종** · `run_tests` 전부 · `clean_room` **9/9** ·
`prod_room` **16/16** · HTTP 실측(clean room 스택)으로 응답 확인.

**시드가 드러난 것** — seed Agent 는 `arch` 가 NULL 이라 게이트를 통과시키면
`arch 미선언 Agent 라우팅 가능 1건` 이 뜬다. 숨기지 않고 위험 표시로 남겼다 (G5 그대로).

**검사를 쓰다 티어 순서를 반대로 잡았다** — `S=1 · M=2 · L=3` 이라 M 능력은 L 기기에서 돈다.
절대규칙 3 이 경고하는 그 착각이고, 판정을 `tier_compatible` 에 맡긴 덕에 코드가 아니라
검사만 틀렸다.

### 안 한 것

- **DDL 0 · 새 테이블·뷰 0.** 기존 뷰(`node_credential_status`·`node_liveness`·
  `agent_arch_unbound`·`provenance_drift`)를 조회만 한다
- `openapi.yaml` — `/v1/ops/*`·`/v1/inputs` 가 **이미** 빠져 있다. 이 PR 에서 늘리지 않았고
  드리프트 정리는 별건으로 남긴다. 원하면 다음 소PR 로 한 번에 맞추겠다
- UI 면(`/ui/`) — 조회면만 냈다

### Next (Decision 요청)

1. **G2 초대 경로** — `provision_source='invited'` 를 만드는 절차. **스키마 추가가 필요하다**
   (`node_invite` 등) → 별 Proposal 로 올릴까
2. **G4 증서 회전 런북** · **G5 등록 시 arch 요구** — 둘 다 작다. 묶어서 한 PR 로?
3. **C 백업·복구 리허설** — 리뷰어 Next 2순위로 남아 있다
4. `openapi.yaml` 드리프트 정리

출품 트랙(촬영 8/23 · D-9)과 경합한다. **순서는 master 판단**이다.
```

```markdown
---
from: claude
at: 2026-08-14T10:30:00+09:00
topic: safety-G4-G5
type: next
expects: ack
status: open
---

## G4 + G5 완료 — 안전 사슬 노란 칸 둘 · PR 머지 대기

Decision 2항. 묶어서 하나로. **DDL 0 · 새 의존성 0.**

| | |
|---|---|
| **PR** | (아래 «PR» 줄) |
| **머지 SHA** | **없음 — 머지 대기** |
| **선행** | `59f7cf6` S2 (#59) |

### G5 — `arch` 를 등록에서 요구한다

없는 값이면 FK 가 막았지만 **아예 안 보내면 통과**했다. 그러면 실행 아키텍처를 Node 로컬
`meta.json` 이 정한다 — I1 이 닫으려던 그 구멍이다. 이제 **400**.

`agent.arch` 는 **nullable 로 둔다** (Decision 의 「DDL 없으면」). legacy 행을 지우거나
백필을 강제하지 않기 위해서다. 「새로 만들지 않는다」는 앱이 지키고, 검사가 그 분기를 본다.

**분기를 `_require` 뒤에 뒀다.** 앞에 두면(pydantic 필수 필드) 본문 검증이 인증보다 먼저 도는
탓에 강제 모드에서 **무인증이 401 대신 422** 를 받는다 — `prod_room` 의 불변식이 깨진다.
검사 하나가 **분기의 위치 자체**를 고정한다.

등록 스크립트 넷이 arch 를 싣는다. 근거는 **학습 기록**(`<weights>.meta.json`) —
`backfill_agent_arch.sh` 와 같은 출처다. **Core 는 추측하지 않는다.**

실측: `demo.sh` 등록 Agent 가 `arch=TinyEuroSAT` · `arch_unbound_routable` **1 → 0** ·
arch 없는 등록 **HTTP 400**.

### G4 — 회전 런북

**무중단은 안 된다는 것을 그대로 적었다.** 활성 증서가 Node 당 하나라(부분 UNIQUE) 겹칠 수
없다. 겹치려면 스키마가 바뀐다 — 별 Decision 이다. 지어내지 않고 짧은 중단을 인정했다.

**돌려 보고 한 줄을 고쳤다.** 제품 프로파일에서 실제 회전(`cn_99a7a084` → `cn_18209df6`),
그런데 **Node 를 멈춘 직후에도 `is_fresh=true`** 였다 — `heartbeat_timeout_s`(45초)가
지나야 내려간다. 그 창에 폐기하면 배정이 401 로 깨진다. 런북은 이제 `leases_live=0` **그리고**
`is_fresh=false` 를 둘 다 기다리라고 적는다. **돌려 보지 않았으면 틀린 런북을 남겼다.**

확인 단계는 S2 조회면을 쓴다.

### 실측

`check_agent_arch` **9 → 13종** · 통합 9종 · `run_tests` 전부 · `clean_room` **9/9** ·
`prod_room` **16/16** · 회전 1회 실수행.

### 남은 것 (Decision 요청은 아래 별 블록)

- `arch NOT NULL` 로 **DB 에 올리는 것** — legacy 행 처리가 선행이다. 별 Decision
- 관리 API **키** 회전 순서 — 증서와 달리 아직 미정 (운영 스크립트가 파일에서 읽는다)
- Decision 4항 **openapi 드리프트** = 다음 별 PR 로 올린다
```

```markdown
---
from: claude
at: 2026-08-14T10:45:00+09:00
topic: G2-invite-path
type: proposal
expects: decision
status: open
---

## Proposal — G2 초대 경로 (`provision_source='invited'`)

Decision 1항. **스키마 추가가 필요하다.** 구현 전에 결정을 받는다.

### 문제

`node.provision_source` 는 `team | invited | public` 을 받는데 **`invited` 를 만드는 절차가
없다.** 지금은 관리자가 직접 `POST /v1/nodes` 를 부른다 — 즉 「러닝크루가 자기 기기를
내놓는다」가 **관리자 수작업**이다. 값은 스키마에 있고 경로가 없다 (`attempt_no` 와 같은 모양).

### 설계 — 등급은 **초대장에 미리 적혀 있다**

절대규칙 4(Node 는 자기 등급을 주장할 수 없다)를 지키는 방법은 하나뿐이다:
**신청자가 고르지 않는다.** 관리자가 초대를 발행할 때 등급·티어 상한을 박아 넣고,
신청자는 그 초대를 **소진**할 뿐이다.

    ① admin 이 초대 발행 (trust_domain · compute_tier_max · 만료를 박는다)
    ② 초대받은 사람이 토큰으로 소진 요청
    ③ Core 가 초대에 적힌 등급으로 Node 생성 + 증서 1회 발급
    ④ 초대 소진 (audit_log 에 남는다)

### DDL (추가만 · 기존 제약 무수정)

```sql
CREATE TABLE node_invite (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issued_by         UUID NOT NULL REFERENCES app_user(id),
    key_prefix        TEXT NOT NULL UNIQUE,
    secret_hash       BYTEA NOT NULL,
    trust_domain      TEXT NOT NULL REFERENCES trust_domain_rank (domain),
    provision_source  TEXT NOT NULL DEFAULT 'invited'
                          CHECK (provision_source = 'invited'),
    compute_tier_max  TEXT NOT NULL REFERENCES compute_tier_rank (tier),
    label             TEXT,
    expires_at        TIMESTAMPTZ NOT NULL,
    redeemed_at       TIMESTAMPTZ,
    redeemed_node_id  UUID REFERENCES node(id),
    revoked_at        TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- team 은 초대로 만들 수 없다. ck_trust_provision_align 이 이미 막지만 여기서도 박는다
    CONSTRAINT ck_invite_domain CHECK (trust_domain IN ('tenant', 'public')),
    CONSTRAINT ck_invite_redeem CHECK ((redeemed_at IS NULL) = (redeemed_node_id IS NULL))
);
```

**기존 제약이 이미 지켜 주는 것** — `is_gate_runner` 는 `provision_source='team'` 에서만
참이므로(`ck_gate_runner_team`), 초대로 들어온 기기는 **채점자가 될 수 없다**. 새로 막을 게 없다.

증서와 같은 모양(`key_prefix` + `secret_hash`)을 쓴다 — 검증 코드 패턴을 재사용한다.

### 열린 질문 (묶어서 — 이것만 답하면 구현한다)

1. **1회용인가 N회인가.** 러닝크루 10명에게 같은 링크를 뿌리는 게 자연스러우면
   `max_redemptions INT NOT NULL DEFAULT 1` 을 둔다. **1회용을 권한다** — 초대장 하나가
   기기 하나에 대응해야 증적이 깨끗하다. 열 명이면 열 장을 발행한다
2. **기본 TTL.** **7일**을 권한다 (증서와 달리 사람이 들고 다닌다)
3. **소진 경로가 강제 모드에서 API 키 없이 열리는 것을 수용하는가.** 초대받은 사람에게는
   관리 키가 없다 — **초대 토큰 자체가 인증**이다. `POST /v1/nodes/redeem` 은
   `REQUIRE_API_KEY=1` 에서도 키 없이 받아야 한다. **이게 이 Proposal 의 유일한 실질 위험이다**
   (지금까지 쓰기는 전부 키 뒤에 있었다). 완화: 만료·1회용·`revoked_at`·audit_log
4. **원스텝인가 투스텝인가.** 소진 시 **Node + 증서를 함께** 주는 쪽(원스텝)을 권한다.
   투스텝(Node 만 만들고 증서는 관리자 승인)은 안전하지만 「관리자 수작업」이 다시 들어온다
5. **초대로 만들 수 있는 티어 상한.** 발행 때 관리자가 정하되 기본 `M` 을 권한다

### 범위 (이번 PR 아님)

UI · 이메일 발송 · 초대 목록 조회면(`/v1/ops/safety` 에 붙일지는 별건) ·
`invited` 기기의 별도 쿼터.

**Confirm 전까지 구현은 시작하지 않는다** (PROTOCOL).
```
