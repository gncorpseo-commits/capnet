# CapNet retrospective

출품·구현 과정에서 **왜 이렇게 했는지**와 **언제 갚을지**를 남긴다.  
숨긴 것과 의도적 범위 제한을 같은 단어로 부르지 않는다.

**갱신:** 2026-08-07

---

## 기존 문서와 역할 분리

| 문서 | 역할 | 여기와 |
|------|------|--------|
| [`../../STATE.md`](../../STATE.md) | 이번 주 어디인지 | open 개수·링크만 |
| [`../context-handoff.md`](../context-handoff.md) §1 | 바꾸려면 반박할 **규범 결정** (D1–) | 규범 ≠ 과정 기록 |
| [`../history/CHANGELOG.md`](../history/CHANGELOG.md) | 무엇이 언제 들어왔는지 | 왜/대안/기한은 여기 |
| [`../error/`](../error/) | 재발 방지 함정 | debt와 다름 |
| [`human-intervention.md`](./human-intervention.md) | 사람 개입 vs AI 보조 (붙임2 근거) | 기여 % 측정 아님 |

확정 규범이 바뀌면 **handoff §1만**.  
“왜 / 대안 / 언제 갚지”는 **이 폴더**.
“내가 뭘 결정했지?”는 **human-intervention**.

---

## 분류 (우회라는 말을 쓰지 않는다)

| 태그 | 의미 | 우선순위 |
|------|------|----------|
| **Technical Debt** | 정석 절차를 **임시로** 생략 | 출품 전·직후 갚기 |
| **Scope Decision** | MVP를 위한 **의도적 제외** | Must 승격·승인 시에만 |
| **Environment Adaptation** | 환경 제약에 대한 **정상 대체** | 보통 빚 아님 · 기록만 |

---

## 항목 템플릿

```markdown
### TD-00N · 짧은 제목
- **분류:** Technical Debt | Scope Decision | Environment Adaptation
- **무엇:** …
- **왜:** …
- **대안:** …
- **예정:** …
- **상태:** open | closed
```

---

## 파일

| 파일 | 내용 |
|------|------|
| [`register.md`](./register.md) | 항목 레지스터 (시드 포함) |
| [`lessons-learned.md`](./lessons-learned.md) | 패턴·원칙 (나열 금지) |
