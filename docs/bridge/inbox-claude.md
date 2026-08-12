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
