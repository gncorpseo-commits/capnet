# CapNet — 장기 모드 핸드오프 (Claude · WSL)

> Claude Code **첫 메시지**로 아래 `---` 사이 전체를 붙여 넣는다.  
> **전문:** [`autonomous-mode.md`](./autonomous-mode.md) — 루프·스택·실측 규율·큐 정본.  
> 정본은 저장소 — 세션 시작 시 숫자만 재측정한다.

---

```markdown
# CapNet — 장기 모드 (Claude 구현·PR 전담 · 자율 루프)

너는 CapNet 저장소의 **구현·PR 에이전트**다. Cursor/사람이 리뷰·**main 머지**를 한다.

**먼저 읽기:** `docs/bridge/autonomous-mode.md` (전문) — 이 블록은 **요약 붙여넣기용**.

## 한 줄 규칙

**PR 올렸다고 멈추지 마. 머지를 묻지 마. 큐가 빌 때까지 돈다.**

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

## 1. 지금 어디인가 (7회차 머지 완료 · 2026-09-02)

| 항목 | 값 |
|---|---|
| main HEAD | `2cbb936` (#198) — `git log -1` 로 재확인 |
| 열린 PR | **0** (새 작업 시작 시) |
| 실행 능력 | **10종** |
| `run_tests` | **571 OK (건너뜀 7)** — `bash scripts/run_tests.sh` |
| Wave | **A–AZ** (#186–#196 + #188·#197) |

**첫 액션:**
```bash
cd ~/pjt/ai-agent-store
git fetch origin main && git checkout main && git pull
gh pr list --state open --limit 100
git log -1 --oneline
bash scripts/run_tests.sh 2>&1 | tail -5
tail -n 120 docs/bridge/inbox-cursor.md   # round7-close · 다음 큐
```

**7회차가 증명한 것:** Core·Node·capreq **세 창구**를 전수·핀(#192–#196).  
**브리지 정본:** `round7-close` (inbox-cursor 끝).

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
│  F. 큐 소진 → inbox confirm/next · STATE Step 0 PR      │
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

## 5. 열린 Decision 아홉 — **구현 PR 금지**

`silent-truncation` · `gate-run-stuck-running` · `failure-reason-not-surfaced` ·
`retention-ttl-policy` · `11th-capability-timeseries-anomaly` ·
`changelog-changeset-rule` · `golden-leakage-claim-unreproducible` ·
**`output-required-undeclared-policy`** (#186 · B 거절 권장) · Next.

막히면 **Proposal만** — 구현 Wave 는 Decision 후.

**D27:** `retrieve.*` 구현 금지.

---

## 6. 다음 큐 (8회차 · Decision 없이 · `round7-close` 정본)

**완료(다시 하지 마):** #186–#191 결함 · #192–#196 전수·핀 · inbox 3·4·6·7·8·9.

| inbox # | 무엇 | 조건 |
|---|---|---|
| **5** | **`openapi.yaml` 응답 스키마** 드리프트 | 경로·메서드는 `#142`. **응답 모양**은 fastapi 있는 세션에서 스키마 추출 대조 |
| **10** | **`docs/` 「할 수 있다」 주장** | README·user-guide 서술 vs 코드·테스트. `test_report_claims` 는 카탈로그만 |
| **11** | **Docker·`pip` 세션** | `clean_room`·`prod_room`·종단 데모 · capreq **72** — **없으면 미루고 inbox에 적기** |

**우선순위:** 10 → 5 → 11 (Docker/pip 없으면 11은 「못 봤다」만).

한 항목 = **한 PR(또는 스택 한 층)**. 끝나면 inbox `round7-close` 다음 큐 갱신.

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

1. **큐 5·10·11 소진** (11은 환경 없으면 「못 봤다」 기록) + Step 0 PR + inbox confirm
2. **하드 블로cker** — schema/CHECK/정책 숫자/제품 주장 (Decision 필요)
3. 사용자가 명시적으로 중단

그 외에는 **5시까지·큐까지** — 사용자 재촉 없이 루프.

---

**시작: main pull → inbox `round7-close` → 큐 **10** (docs 주장). PR 후 멈추지 마.**
```

---

## 갱신 이력

| 날짜 | main | 비고 |
|---|---|---|
| 2026-09-03 | `2cbb936` | `autonomous-mode.md` 전문 · handoff 요약 (#198) |
| 2026-09-03 | `34d943f` | 자율 루프·실측 규율·8회차 큐 (#192/#196 교훈 반영) |
| 2026-09-02 | `757c133` | 7회차 머지 (#196·#188) · Decision 9 |
