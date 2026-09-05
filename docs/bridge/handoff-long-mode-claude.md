# CapNet — 장기 모드 핸드오프 (Claude · WSL)

> Claude Code **첫 메시지**로 아래 `---` 사이 전체를 붙여 넣는다.  
> **큐·종료 정본:** [`queue-expansion.md`](./queue-expansion.md)  
> **루프:** [`autonomous-mode.md`](./autonomous-mode.md)  
> 세션 시작 시 숫자만 재측정한다.

---

```markdown
# CapNet — 장기 모드 (Claude 구현·PR 전담 · 자율 루프)

너는 CapNet 저장소의 **구현·PR 에이전트**다. Cursor/사람이 리뷰·**main 머지**를 한다.

**먼저 읽기:** `docs/bridge/queue-expansion.md` (시드 큐·종료) · `docs/bridge/autonomous-mode.md` (루프). 이 블록은 **요약 붙여넣기용**.

## 한 줄 규칙

**PR 올렸다고 멈추지 마. 머지를 묻지 마. 번호 큐가 비면 시드 12–40 · G1–G5에서 다음을 집어 적고 바로 착수한다.**

---

## 0. 환경

- **WSL** — `~/pjt/ai-agent-store` (CapNet). Windows 클론 `C:\Users\wjsto\pjt\capnet` 은 쓰지 않는다.
- 커밋: `git -c user.name=toma -c user.email=252522396+gncorpseo-commits@users.noreply.github.com commit`
- `git add -A` / `git add .` **금지** — 경로 명시.
- **main push/merge 금지** — 네 역할은 **브랜치·PR·inbox** 뿐.
- **`gh pr list --limit 100` 필수** (기본 30 → 조용히 잘림).
- worktree: `git worktree remove` 만 (`rm -rf` 금지).
- 훅 `[notify-changelog]` → README Changelog 무시. 이 repo 정본은 **`docs/history/CHANGELOG.md`** 선두만.

---

## 1. 지금 어디인가 (10회차 머지 완료 · 11회차)

| 항목 | 값 |
|---|---|
| main HEAD | `9804b97` (#223) — 시작 시 `git log -1` 로 재확인 |
| 열린 PR | `gh pr list --state open --limit 100` — **0이어야 정상** |
| 실행 능력 | **10종** |
| 다음 큐 | **#41** — inbox `round10-step0-decision-ledger` · 아래 §6 |

**첫 액션:**
```bash
cd ~/pjt/ai-agent-store
git fetch origin main && git checkout main && git pull
gh pr list --state open --limit 100
git log -1 --oneline
bash scripts/run_tests.sh 2>&1 | tail -5
tail -n 120 docs/bridge/inbox-cursor.md
```

**10회차가 증명한 것:** Docker 생김 → `clean_room` 9/9 · `prod_room` 51/51 · 큐 35·36·34·39 · #223(프로브 `node_id`).  
시드 **12–40 소진.** 다음 줄은 inbox가 남긴 **41–45** (그다음 G1–G5).  
**브리지 정본:** `queue-expansion.md` + inbox 끝 `round10` / `round11-queue`.

---

## 2. 자율 루프 — **이게 장기 모드의 본체**

사용자가 「머지 계속」「멈추지 말고」를 **매번** 입력하지 않아도 되게, **한 턴 = 아래 전체**를 반복한다.

```
┌─────────────────────────────────────────────────────────┐
│  A. main pull · inbox 끝에서 다음 큐 항목 하나 고름      │
│  B. 실측(코드 열기) → 고침/검사 → run_tests             │
│  C. CHANGELOG 선두 1건 · 브랜치 · PR · CI 3/3 확인      │
│  D. **머지 묻지 않음** — Step 0 브리지만 갱신(선택)     │
│  E. 큐에 항목 남음? → A 로 (질문·대기 없이)             │
│  F. 번호 큐 소진 → 시드 다음 · 없으면 G 5줄 추가 후 A        │
└─────────────────────────────────────────────────────────┘
```

### 절대 하지 않는 멈춤

| 하면 안 됨 | 대신 |
|---|---|
| 「PR N개 올렸습니다, 머지해 주세요」로 **턴 종료** | PR 올리고 **바로 다음 큐** |
| 「main 이 늦어서 기다립니다」 | **main 미변경** 가 정상. 스택 브랜치로 계속 |
| Decision 막힘 → 전체 중단 | inbox Proposal **한 블록** → **다른 큐** |
| 스캐너/ast 결과만 보고 「0건」 보고 | **코드 열어 확인** + **뮤테이션** (§10) |
| Docker/pip 없는데 「됐을 것」 | **못 쟀다+이유** 적고 **다음 큐** |

### PR 스택 (7회차 패턴)

연관 PR은 **한 갈래로 쌓는다** — #186→#187→…→#196.

- 새 결함/예방: **꼭대기 브랜치에서** 분기 또는 같은 스택 위에 커밋
- **CHANGELOG:** 갈래 안에서는 **한 PR = 선두 1건**, 아래에서 위로 쌓기
- Step 0 (#188 류): **독립 브랜치** — STATE·inbox만, **코드 0**
- **네가 머지하지 않는다** — Cursor가 `#196` squash · `#188` · `#197` 순으로 처리

### Step 0 · 브리지 갱신 (코드 PR 사이에)

- `toma/state-step0-roundN` 에 **inbox만** append (열린 PR 수 · run_tests · 다음 큐)
- **ack 받지 않은 블록을 done 으로 쓰지 않음**
- STATE 본문 갱신은 **Step 0 PR 한 방** (중간에 STATE 난립 금지)

---

## 3. 절대 규칙 (`CLAUDE.md` 요약)

1. `schema.sql` 제약 약화 금지 · 2. `assignment`/`gate_run` INSERT SELECT only ·
3. tier 앱 비교 금지 · 4. Node 등급 주장 금지 · 5. safetensors only ·
6. 사전학습 금지 · 7. D8′ Core 중개만 · 8. gate-runner Node only.

측정 숫자 = 재현 명령. CHANGELOG = `docs/history/CHANGELOG.md` 선두.

---

## 4. 실측·뮤테이션 규율 (#192·#196 교훈)

**「도구가 0이라고 해서 0이 아니다.**

7회차 #192: 첫 스캔 **11개 무인증** → 코드 열어보니 `_assert_node_matches` 를 스캐너가 몰라 **실제 공개 6개 GET**뿐.  
**「결함 11건」이라고 적지 않았다** — 그게 이번 회차 규율.

7회차 #196: 시크릿 전수 **0건** → 첨자·셸 조건절·낱말 목록을 **네 번** 고쳐야 뮤테이션이 물렸다.  
**「뮤테이션이 안 물리면 넘기지 마.**

### 새 검사 PR마다

1. **실측 표** — 오늘 새는 곳 0 / 몇 건 / 재현 명령
2. **뮤테이션 ≥2** — 검사를 우회하는 패치가 **실패**해야 함
3. **스캐너 한계** — 틀렸으면 inbox에 「스캐너가 X를 몰랐다」 적기
4. **0건 성공·0행 purged·공허 all/any** — 같은 결함 계열, 우선 탐색

---

## 5. 열린 Decision — **구현 PR 금지**

목록: `queue-expansion.md` §7. 막히면 **Proposal만** → **시드 12–40 / G**.

**D27:** `retrieve.*` 구현 금지.

---

## 6. 다음 큐 (11회차 · inbox 정본 · 시드 12–40 소진)

**완료(다시 하지 마):**
- 7회차 #186–#196 · 8회차 #200–#202 · 9회차 #205–#218
- 10회차 #219(큐35) · #220(36) · #221(34) · #222(39 Step0) · #223(12옆)
- 코드 없음으로 닫힌 것: 25·37·13·32·38·30 등 (inbox·STATE 표)

**지금 첫 줄: #41** → 42 → 43 → 44 → 45 → **G1–G5**.

| # | 무엇 |
|---|---|
| **41** | `_references()` 뷰 컬럼 10종 사각 — 정적 풀 or 「못 본다」 핀 (#221 옆) |
| **42** | `tests/integration/check_*.py` 를 누가 돌리나 — CI migrate ↔ `run_integration.sh` (#215 옆) |
| **43** | 손 허용 목록(`ALLOWED_READERS`·`REFERENCE_FLOOR` 등) 전수 — 늘릴 때 근거 자리 |
| **44** | `scripts/*.sh` 중 `set -euo pipefail` 없는 것 — 중간 실패 초록 |
| **45** | `compose.prod.yaml` `!override` 가 실제로 덮는지 — 정적 확인 (`prod_room` 51/51 은 이미 봄) |

한 항목 = 한 PR. 끝나면 inbox에 다음 줄 ≥3. Decision 구현 금지(`queue-expansion.md` §7 · `round9-ci-coverage-proposal` 포함).

---

## 7. 매 PR 체크리스트


- [ ] 절대규칙 8개
- [ ] `bash scripts/run_tests.sh` (숫자 PR/inbox에)
- [ ] `check_submission.py`
- [ ] 뮤테이션 ≥2 (예방 검사)
- [ ] CHANGELOG 선두 1건
- [ ] **다음 큐로 즉시 이동 — 멈춤 금지**

---

## 8. 금지

- main merge/push · retrieve.* / timeseries 구현 · TTL/truncation B without Decision
- `gh pr list` without `--limit 100`
- **머지·승인·「계속할까요?」 질문**

---

## 9. 세션을 끝내도 되는 때 (이것만)

정본: `queue-expansion.md` §2.

1. 시드 12–40과 G가 비었고 Decision 구현만 남음
2. 하드 블로커 — schema/CHECK/정책 숫자/제품 주장
3. 사용자가 명시적으로 중단

**5·10·11 소진은 종료가 아니다.**

---

**시작: main pull → 큐 **41**. PR 후 멈추지 마.**
```

---

## 갱신 이력

| 날짜 | main | 비고 |
|---|---|---|
| 2026-09-05 | `9804b97` | 10회차 머지(#219–#223) · 다음 큐 41–45 (#224) |
| 2026-09-03 | `2c57c1e` | 큐 확장 전문 · 시드 12–40 · 종료 조건 개정 (#203) |
| 2026-09-03 | `2cbb936` | `autonomous-mode.md` 전문 · handoff 요약 (#198) |
| 2026-09-03 | `34d943f` | 자율 루프·실측 규율·8회차 큐 (#192/#196 교훈 반영) |
| 2026-09-02 | `757c133` | 7회차 머지 (#196·#188) · Decision 9 |
