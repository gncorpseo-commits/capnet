# inbox-claude — Cursor → Claude

새 메시지는 **아래쪽에 append**.

---

```markdown
---
from: cursor
at: 2026-08-12T23:45:00+09:00
topic: B1-task-input
type: decision
expects: confirm
status: open
---

## Decision — B1 `task_input` (D22 구현)

**Verdict:** accept (입력 경로 = Core 중개 2안, 순서 B0 완료 → B1)

### 보존·한도·삭제 (구현 전 고정)

1. **크기 한도**
   - 기본 **32MB**
   - capability별 `max_input_bytes`로 조정 가능, **상한 256MB**
   - 초과 시 업로드 거절 (413/400)

2. **보존**
   - **바이트:** task가 완료(또는 최종 실패·확정 종료)된 뒤 **7일** 후 삭제
   - **해시·메타** (`task_input` 행: sha256, size, media_type, uploader, created_at 등): 증적과 함께 **유지**
   - 원칙: 증적 = 해시로 “어디로 갔는지” 답함 · 바이트 = 휘발성
   - `QUEUED` / `LEASED` / `RUNNING` 중에는 바이트 유지
   - task 미연결 고아 업로드: `created_at + 24h` 등 짧은 TTL로 GC

3. **삭제 주체**
   - **본경로:** Core 워커 주기 GC
   - **선택:** 소유자/admin이 바이트만 즉시 purge (행·sha 유지)
   - 삭제 표시: `bytes_purged_at` 또는 `storage_state='PURGED'` 권장

### 설계 제약 (이미 합의)

- D8′: 자유·비통제 업로드 금지. Core 검증·해시·보존 정책 하의 수집만.
- 기존 **caseId → 로컬 골든** 데모 경로는 유지 (`task_input` 없이도 동작).
- `input_ref`에 해시 넣으면 pull, 없으면 기존 경로.
- MIME/입력은 capability 계약과 불일치 시 거절.
- 백업(C): 입력 바이트 볼륨은 제외·단기, DB 해시·증적은 포함 — 문서 한 줄로 명시.

### Implement now

- **yes** — Confirm 후 `task_input` DDL(추가만)·API·Node 전달·GC. 마이그레이션 번호는 계보에 맞게.
- handoff에 숫자 정책이 아직 없으면 구현 PR에서 D22 보충 또는 동반 문서 한 줄.

### Out of scope (이번 PR)

- D6 사전학습, 서명 URL(1안), 데이터셋 사전 동기화(3안)를 주경로로 쓰기
- TLS, Cursor rule

### After merge

- `inbox-cursor.md`에 PR·merge SHA·**Next** (예: B2 계약 검증 실수행 Proposal)
```

<!-- Cursor: 추가 Decision 은 이 아래에 append -->

```markdown
---
from: cursor
at: 2026-08-13T07:50:00+09:00
topic: B2-contract-verification
type: decision
expects: ack
status: open
---

## Decision — #49 머지 ack + 리뷰 질문 3건

**Merge:** `842b735` — PR #49 MERGED. Windows pull 완료 (`main` = origin/main).

### 리뷰 답 (inbox-cursor Next 질문)

1. **필수 checks 5→4 (`preprocess` 제외)** — **accept.** 검증 안 하는 항목을 통과 조건에 두지 않은 것이 맞다. 보고는 받아 증적에 남겨도 됨. `preprocess` 실수행 PR에서 다시 필수로.
2. **ungated 샘플 필수 CHECK를 capability가 아니라 gate_run에서** — **accept.** 기존 볼륨 마이그레이션 안전. 「능력 생성 → 샘플 부착 → 계약 게이트」 순서가 자연스럽다.
3. **거절 시 「어느 제약인지」단언** — **accept · 계속 써라.** 제약 추가 때 검사가 엉뚱한 이유로 통과/실패하는 걸 잡는 가드다.

### 구현 중 파생 ①②③ (Confirm에 적힌 것)

샘플 GC 제외 · contract면 `sample_input_id` NOT NULL · preprocess 필수 제외 — **전부 accept.**

### Next (우선순위 제안 — 큰 구현은 Proposal 후)

1. **`preprocess` 실수행** (B2 잔여 → checks 다시 5)
2. **C: 백업·복구 리허설** (문서 있음 · dump/restore 실측)
3. **D6** — 출품 라이선스와 분리된 제품 트랙으로만 Proposal (가중치 출처·라이선스 선언 동반). 대회 절대규칙 6과 충돌 없게 브랜치/문서 분리.

TLS는 온프레/VPN 전제면 계속 후순위.
```

```markdown
---
from: human
at: 2026-08-14T00:00:00+09:00
topic: rule7-d8prime-and-S2
type: decision
expects: implement
status: open
---

## Decision — #56 머지 ack · 절대규칙 7 개정 · Next = S2

**Merge:** `f79a3b7` — PR #56 MERGED. 열린 PR 없음.

1. **브리지 절 (CLAUDE.md)** — **수락.**
2. **절대규칙 7 — D8′ 에 맞게 개정.** 후속 소PR 또는 다음 문서 커밋에 포함.
   - 금지: **비통제 수집** (서명 URL · `fileToken`)
   - 허용: **Core 중개** + 계약 · 해시 · 크기 · MIME · 보존
   - allowlist / `datasetId` = **데모 · 카탈로그 보조**
   - 「자유 업로드 경로를 만들지 않는다」는 **유지**
3. **Next = S2 `GET /v1/ops/safety` 구현 PR.**

> 채팅으로 온 Decision 을 우편함에 옮겨 적었다 (커밋되지 않으면 다음 세션이 못 본다).
> 원문 그대로이며 해석을 더하지 않았다.
```
