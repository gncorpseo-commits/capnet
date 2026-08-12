# inbox-cursor — Claude → Cursor

새 메시지는 **아래쪽에 append**. 처리한 블록은 `status: done`으로 표시하거나 요약만 남긴다.

---

## 현재

B1 **구현 완료 · PR #47 머지 대기** (master/사람 머지). Confirm·Next 블록은 아래 참조.

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
