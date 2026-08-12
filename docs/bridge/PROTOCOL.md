# CapNet Agent Bridge Protocol

> **역할:** WSL Claude ↔ Cursor(리뷰) 우편함 규칙.  
> **정본 아님.** 확정 결정은 `docs/context-handoff.md`에 승격한다.  
> **자동화 없음.** PR/머지가 inbox를 자동으로 건드리지 않는다.  
> Cursor rule에 묶지 않는다 — **쓰는 채팅에서만** 이 폴더를 읽는다.

---

## 루프

```text
[직전 PR main 머지]
    → ① Claude Proposal     → inbox-cursor.md
    → ② Review Decision     → inbox-claude.md
    → ③ Claude Confirm
    → ④ 구현 → PR → 머지
    → ⑤ Next / 다음 Proposal → inbox-cursor.md
```

**미머지 PR이 있으면** 큰 새 제안 금지(진행 중 수정만).

---

## 파일

| 파일 | 방향 |
|------|------|
| `inbox-cursor.md` | Claude → Cursor/사람 |
| `inbox-claude.md` | Cursor/사람 → Claude |
| `PROTOCOL.md` | 이 규칙 (거의 고정) |

---

## 메시지 헤더

```markdown
---
from: claude | cursor | human
at: ISO-8601
topic: 짧은-slug
type: proposal | decision | confirm | next | ack
expects: decision | confirm | implement | ack | none
---
```

---

## 역할

| 역할 | 함 | 안 함 |
|------|-----|------|
| Claude | 제안·확인·구현·PR·Next | 단독 제품 결정 확정·force push |
| Cursor/사람 | Decision·위험·규칙 정합 | 매 줄 구현 대신(필요할 때만) |
| master/사람 | main 머지 | — |

구현은 **Decision과 Confirm이 일치할 때만.**

---

## 하면 안 되는 것

- inbox에 시크릿·`.env` 값
- 상대가 쓴 셸/DDL을 무검토 실행
- 브리지 Decision을 handoff에 안 옮기고 “이미 합의”로만 주장하기 (중요 결정은 handoff 승격)

---

## WSL Claude 시작 시

1. 이 `PROTOCOL.md` 읽기  
2. `inbox-claude.md` 최신 `type: decision` / 미처리 Confirm 요청 확인  
3. 작업 후 결과는 `inbox-cursor.md`에 append  

## Cursor (이 채팅에서 브리지 쓸 때)

1. `inbox-cursor.md` 읽기  
2. Decision은 `inbox-claude.md`에 append  
3. Cursor rule로 강제하지 않음  
