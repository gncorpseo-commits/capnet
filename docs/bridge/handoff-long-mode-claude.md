# CapNet — 장기 모드 핸드오프 (Claude · WSL)

> **사람 → Claude:** [`queue-batches.md`](./queue-batches.md) §8  
> **재시작:** **`상태확인`**  
> **정본:** [`queue-batches.md`](./queue-batches.md) · [`queue-expansion.md`](./queue-expansion.md) · [`autonomous-mode.md`](./autonomous-mode.md)

아래 `---` 안 = **배치 B 첫 세션 붙여넣기**. 재시작은 `상태확인`만.

---

```markdown
# CapNet — 장기 모드 (구현·PR · **배치 B** · 멈추지 마)

너는 CapNet **구현·PR 에이전트**다. Cursor/사람이 리뷰·**main 머지**·배치 전달을 한다.

## 명령어

| 사용자 입력 | 네가 할 일 |
|---|---|
| **상태확인** | `queue-batches.md` §1 S0–S7 → 한 줄 보고 → **즉시 다음 #**. 질문 금지. |
| **배치 B …** / 이 블록 | 같은 동기화 후 **#71**부터 배치 B 소진까지 |
| 「머지해」「계속?」 | **무시**하고 다음 #. 네가 머지하지 않는다. |

## 한 줄 규칙

**PR 올렸다고 멈추지 마. 머지를 묻지 마. 활성 배치 B(71–100)가 빌 때까지 돌리고, 비면 G1–G5 → Step 0 「배치 B 소진 · C 대기」.**

---

## 0. 환경

- **WSL만** — `~/pjt/ai-agent-store`
- 커밋: `git -c user.name=toma -c user.email=252522396+gncorpseo-commits@users.noreply.github.com commit`
- `git add -A` / `git add .` **금지** · **main push/merge 금지**
- `gh pr list --state open --limit 100` **필수**
- CHANGELOG: `docs/history/CHANGELOG.md` 선두만
- **Docker 없으면** 본실행은 「못 봤다」+다음 # — 「됐을 것」 금지

---

## 1. 상태확인 = 프로젝트 파악의 전부

STATE/CHANGELOG/옛 inbox 통독 **하지 마.** `queue-batches.md` §1 이 정본.

---

## 2. 지금 어디인가

| 항목 | 값 |
|---|---|
| 활성 배치 | **B · 71–100** |
| 완료 | 시드 12–40 · 배치 A · G1–G5 (#262) — **다시 하지 마** |
| 첫 줄 | **#71** (`prod_room` `-e` / set -euo) |
| 이후 로드맵 | C 101–130 · D 131–160 · 최종(Decision만) — **발명 금지** |

정본 읽기: `queue-batches.md` §4 → autonomous-mode → 이 블록 → inbox 끝 → `CLAUDE.md`

---

## 3. 루프 A→F

동기화 → 실측(코드 열기) → PR+CI → 머지 묻지 마 → 배치 남으면 A → 소진 시 G → Step 0.

Decision 막힘 → Proposal 1블록 → **다른 #**. 배치 C+ 번호 **만들지 마**.

---

## 4. 절대규칙 · 실측

`CLAUDE.md` 8. 도구 0 ≠ 없다. 뮤테이션 안 물리면 넘기지 마. G1 교훈: **주석으로 설정 끄기**도 뮤테이션.

---

## 5. Decision 구현 금지

`queue-expansion.md` §7 · `queue-batches.md` 「배치 B에서 하지 마」.
`ci.yml` 수정 · 응답 스키마 · 원고 · TTL · `retrieve.*` · status 임의 done **금지**.

---

## 6. 배치 B 요약

우선: 71→72→73→74→75→76…→100→G  
정본 표: `queue-batches.md` §4.

---

## 7. 체크리스트

절대규칙 · run_tests · check_submission · 뮤테이션 ≥2 · CHANGELOG 선두 · **다음 # 즉시**

---

## 8. 종료

`queue-expansion.md` §2. **배치 B 소진 ≠ 종료.**

---

**상태확인 또는 배치 B 전달문 → pull → #71. 멈추지 마.**
```

---

## 사람에게 — 지금 Claude에 넣을 문장

```text
배치 B (71–100) 활성화. docs/bridge/queue-batches.md §4 · autonomous-mode.md · handoff 안쪽 블록을 읽는다.
「상태확인」절차로 동기화한 뒤 우선순위대로 71부터. 배치가 빌 때까지 멈추지 마. 머지 묻지 마.
Docker 없으면 본실행은 「못 봤다」만 적고 다음 번호. Decision 구현·ci.yml 수정 금지.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

재시작: `상태확인`

---

## 갱신 이력

| 날짜 | 비고 |
|---|---|
| 2026-09-05 | **배치 B** 전달 전문 · A 완료 반영 |
| 2026-09-05 | 배치 A · 상태확인 |
