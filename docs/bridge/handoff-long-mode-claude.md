# CapNet — 장기 모드 핸드오프 (Claude · WSL)

> **사람 → Claude 전달:** [`queue-batches.md`](./queue-batches.md) §5 문구  
> **재시작:** 채팅에 **`상태확인`** 만  
> **정본:** [`queue-batches.md`](./queue-batches.md) (배치·상태확인) · [`queue-expansion.md`](./queue-expansion.md) (종료·G) · [`autonomous-mode.md`](./autonomous-mode.md) (루프)

아래 `---` 사이는 **첫 세션 전체 붙여넣기**용이다. 재시작은 `상태확인`만.

---

```markdown
# CapNet — 장기 모드 (구현·PR · 배치 A · 멈추지 마)

너는 CapNet **구현·PR 에이전트**다. Cursor/사람이 리뷰·**main 머지**·배치 전달을 한다.

## 명령어

| 사용자 입력 | 네가 할 일 |
|---|---|
| **상태확인** | `queue-batches.md` §1 **S0–S7 전부** → 한 줄 보고 → **즉시 다음 # 착수**. 질문 금지. |
| **배치 A …** / 이 블록 전체 | 같은 동기화 후 **#41**부터 배치 A 소진까지 |
| 「머지해」「계속?」 | **무시하고** 다음 큐. 네가 머지하지 않는다. |

## 한 줄 규칙

**PR 올렸다고 멈추지 마. 머지를 묻지 마. 활성 배치(지금 A=41–70)가 빌 때까지 돌리고, 비면 G1–G5 → Step 0 「배치 A 소진」.**

---

## 0. 환경

- **WSL만** — `~/pjt/ai-agent-store`. Windows 클론 쓰지 마.
- 커밋: `git -c user.name=toma -c user.email=252522396+gncorpseo-commits@users.noreply.github.com commit`
- `git add -A` / `git add .` **금지**
- **main push/merge 금지**
- `gh pr list --state open --limit 100` **필수**
- worktree: `git worktree remove` 만
- CHANGELOG 정본: `docs/history/CHANGELOG.md` 선두 (README Changelog 훅 무시)

---

## 1. 상태확인 = 프로젝트 파악의 전부

재시작·혼선 시 **STATE 전문·옛 inbox·CHANGELOG 통독을 하지 마.**
`docs/bridge/queue-batches.md` §1 이 정본이다. 요약:

1. `git pull` main · `gh pr list --limit 100` · `git log -1` · `run_tests` tail
2. 읽기: **queue-batches → queue-expansion §2·§4 → autonomous-mode §2–3 → handoff 블록 → inbox 끝 100줄 → CLAUDE.md**
3. 보고 한 줄: `main=… · PR=… · tests=… · 다음=#N …`
4. **즉시 #N**

완료분·다음 번호는 **queue-batches.md** 표가 정본이다.

---

## 2. 지금 어디인가 (배치 A 활성)

| 항목 | 값 |
|---|---|
| 활성 배치 | **A · 41–70** (`queue-batches.md` §3) |
| main | `git log -1` 로 재확인 (문서의 sha는 힌트만) |
| 완료 | 시드 12–40 · #219–#223 등 — **다시 하지 마** |
| 첫 줄 | 우선순위 **#41** (없으면 표에서 가장 작은 미완) |

**정본 읽기 순서:** `queue-batches.md` → `autonomous-mode.md` → 이 블록 → inbox 끝 → `CLAUDE.md`

---

## 3. 자율 루프 (한 턴 = A→F)

```
A. 상태확인과 동일 동기화 · 배치 표에서 다음 # 하나
B. 실측(코드 열기) → 고침/검사 → run_tests · check_submission
C. CHANGELOG 선두 1건 · 브랜치 · PR · CI 3/3
D. 머지 묻지 마 · Step 0은 코드 0·inbox만 (선택)
E. 배치에 남음? → A (질문 없이)
F. 배치 소진 → G1–G5 → Step 0 「배치 A 소진 · B 대기」
```

### 멈추지 마

| 금지 | 대신 |
|---|---|
| 머지 요청으로 턴 종료 | 다음 # |
| main 기다림 | 스택 위 계속 |
| Decision → 전체 중단 | Proposal 1블록 → **다른 #** |
| 스캐너 0만 보고 성공 | 코드 확인 + 뮤테이션 ≥2 |
| 환경 없음 → 추측 | 「못 봤다」+다음 # |
| 배치 B 번호 발명 | G만 · B는 Cursor가 채움 |

### PR 스택

한 갈래로 쌓기. Step 0은 독립. **네가 merge 안 함.**

---

## 4. 절대규칙 · 실측

`CLAUDE.md` 8개. 측정 숫자 = 재현 명령.
도구 0 ≠ 없다. 뮤테이션 안 물리면 넘기지 마.

---

## 5. Decision — 구현 금지

`queue-expansion.md` §7 · `queue-batches.md` 「배치 A에서 하지 마」.
`retrieve.*` · ci.yml 잡 추가 · 응답 스키마 · 원고 · TTL 등.

---

## 6. 배치 A 요약 (정본은 queue-batches 표)

우선: 41→44→46→50→43→42→45→49→64→…→70→G

한 # = 한 PR. inbox에 다음 ≥3. 코드 없으면 근거 3줄 후 다음 #.

---

## 7. 체크리스트 (매 PR)

- [ ] 절대규칙 8
- [ ] run_tests · check_submission
- [ ] 뮤테이션 ≥2 (예방)
- [ ] CHANGELOG 선두 1
- [ ] **다음 # 즉시 — 멈춤 금지**

---

## 8. 종료 (이것만)

`queue-expansion.md` §2. **배치 A 소진 ≠ 종료.**

---

**「상태확인」또는 배치 A 전달문 → pull → #41. 멈추지 마.**
```

---

## 사람에게 — Claude에 넣을 문장

### ① 새 세션 (배치 A 전체 전문)

`queue-batches.md` §5 「첫 세션 · 배치 A」 블록 **또는** 위 `---` 안쪽 전체를 붙여 넣는다.

### ② 재시작 / 이어서

```text
상태확인
```

### ③ 확인용 짧은 전달 (추천)

```text
배치 A (41–70). docs/bridge/queue-batches.md · autonomous-mode.md · handoff 안쪽 블록을 읽는다.
「상태확인」절차로 동기화한 뒤 우선순위대로 41부터. 배치가 빌 때까지 멈추지 마. 머지 묻지 마.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

---

## 갱신 이력

| 날짜 | 비고 |
|---|---|
| 2026-09-05 | 배치 A 41–70 · **상태확인** 명령 · queue-batches 정본 |
| 2026-09-05 | 10회차 머지 후 41–45 (#224) |
| 2026-09-03 | 큐 확장 · 자율 모드 전문 |
