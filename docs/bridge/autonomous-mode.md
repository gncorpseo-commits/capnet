# CapNet 자율 모드 — 운영 전문

> **대상:** WSL Claude Code (구현·PR 전담) · Cursor/사람 (리뷰·main 머지)  
> **정본:** 이 파일(루프·스택·실측) + [`queue-batches.md`](./queue-batches.md)(활성 배치·**상태확인**) + [`queue-expansion.md`](./queue-expansion.md)(종료·G)  
> **붙여넣기:** `handoff-long-mode-claude.md`  
> **브리지:** `@docs/bridge/PROTOCOL.md` — Decision·Confirm은 여기와 별개로 유지

---

## 1. 왜 자율 모드인가

7회차(2026-09-02)에서 Claude가 **한 세션 안**에서 결함 5건 + 예방 5건 + Step 0을 연속으로 처리했다.
그러나 턴 끝마다 「머지 = #196 · #188」 요약으로 **사람 머지를 암시**했고,
사용자가 「멈추지 말고」「5시까지」를 **매번** 재입력해야 이어졌다.

**자율 모드**는 이 간극을 메운다:

| 역할 | 함 | 안 함 |
|---|---|---|
| **Claude** | 시드·G가 빌 때까지 PR·검사·브리지 Step 0 · **자기 스택 머지 (조건부 · 아래)** | Decision 단독 확정 · 조건 밖 머지 |

> **머지 예외 (11회차 · 2026-09-06 사용자 승인 · 배치 B–D).** Claude 가 자기 스택을
> 머지한다 — CI **3/3 green** · 변경이 `tests/`·`docs/`·`scripts/` 안 · 뮤테이션 ≥2 를
> 돌려 PR 에 적었을 때만. 런타임 코드·DDL·`compose`·`ci.yml`·제품 주장·Decision `status`
> 는 **그대로 사람 몫**이다. 배치 경계에서 꼭대기만 squash.
| **Cursor/사람** | PR 리뷰 · main squash merge · Decision | 매 PR마다 「계속해」 재촉 |
| **master** | main 머지 최종 | — |

**핵심:** Claude는 PR을 올린 뒤 **머지를 기다리지 않고** 다음 큐로 간다.
main이 늦어도 **스택 브랜치**로 작업을 이어간다.

---

## 2. 한 줄 규칙

**PR 올렸다고 멈추지 마. 머지를 묻지 마. 활성 배치가 빌 때까지 돌린다. 「상태확인」= 동기화 후 즉시 다음 #.**

사용자가 **「상태확인」** 만 보내면 [`queue-batches.md`](./queue-batches.md) §1 (S0–S7)을 **한 턴에 끝낸 뒤** 다음 큐에 착수한다. 장문 브리핑·머지 요청·「계속?」 **금지**.

---

## 3. 자율 루프 (한 턴 = A→F 전체)

```
┌──────────────────────────────────────────────────────────────┐
│  A. 동기화                                                    │
│     git fetch/pull main · gh pr list --limit 100              │
│     queue-batches.md 활성 배치에서 다음 # 1개                 │
│     (「상태확인」이면 §1 S0–S7 전부 후 즉시 착수)             │
├──────────────────────────────────────────────────────────────┤
│  B. 실측                                                      │
│     ast/스캐너 결과만 믿지 않음 — **코드 열어 확인**          │
│     고침 또는 tests/ 검사 추가 · run_tests · check_submission │
├──────────────────────────────────────────────────────────────┤
│  C. PR                                                        │
│     CHANGELOG 선두 1건 · 브랜치 · push · gh pr create         │
│     CI 3/3 확인 (실패 시 고치고 같은 브랜치)                  │
├──────────────────────────────────────────────────────────────┤
│  D. 브리지 (선택·코드 PR 사이)                                │
│     toma/state-step0-roundN — inbox append만 (코드 0)         │
│     **머지 요청 문장 금지**                                   │
├──────────────────────────────────────────────────────────────┤
│  E. 분기                                                      │
│     배치 남음 → A (질문·대기 없이)                            │
│     Decision 막힘 → Proposal 1블록 → **다른 #**               │
├──────────────────────────────────────────────────────────────┤
│  F. 배치 소진 → G1–G5 · Step 0 「다음 배치 대기」            │
│     종료는 queue-expansion.md §2만                            │
└──────────────────────────────────────────────────────────────┘
```

### 절대 하지 않는 멈춤

| 하면 안 됨 | 대신 |
|---|---|
| 「PR N개 올렸습니다, 머지해 주세요」로 턴 종료 | PR 올리고 **바로 다음 큐** |
| 「main 이 늦어서 기다립니다」 | main 미변경 = 정상. **스택 위에서 계속** |
| 스캐너/ast 「0건」만 보고 성공 보고 | **코드 확인 + 뮤테이션 ≥2** |
| Docker/pip 없이 「됐을 것」 | **못 쟀다 + 이유** 적고 다음 큐 |
| Decision 때문에 전체 중단 | **Proposal만** — 배치 다른 # / G로 |

---

## 4. 환경·도구

| 항목 | 값 |
|---|---|
| 작업 경로 | WSL `~/pjt/ai-agent-store` |
| Windows 클론 | `C:\Users\wjsto\pjt\capnet` — Claude **사용 안 함** |
| 커밋 서명 | `git -c user.name=toma -c user.email=252522396+gncorpseo-commits@users.noreply.github.com commit` |
| 스테이징 | 경로 명시만 — `git add -A` / `git add .` **금지** |
| PR 목록 | `gh pr list --state open --limit 100` **필수** (기본 30 잘림) |
| worktree | `git worktree remove` 만 |
| CHANGELOG | `docs/history/CHANGELOG.md` 선두 — README Changelog 훅 무시 |
| 테스트 | `bash scripts/run_tests.sh` · `python scripts/check_submission.py` |

---

## 5. PR 스택 (7회차 패턴)

연관 PR은 **한 갈래**로 쌓는다: `#186 → #187 → … → #196`.

```
main ──●──●──●  (Cursor가 squash merge)
              \
               ●── #186
                    └── #187
                         └── …
                              └── #196  ← 꼭대기만 squash
```

**규칙**

1. 새 결함/예방: **스택 꼭대기**에서 분기하거나 같은 갈래에 커밋
2. **CHANGELOG:** 갈래 안에서 PR마다 선두 1건 — 아래에서 위로 쌓기
3. **Step 0** (#188 류): **독립 브랜치** — STATE·inbox만, 코드 0
4. **Claude는 merge 하지 않음** — Cursor가 `#196` squash · `#188` · `#197` 순
5. 독립 브랜치끼리 CHANGELOG 충돌 (#189 vs #187 교훈) — **한 갈래로 모으거나** Step 0에서만 STATE

**Cursor 머지 순서 (참고 — Claude가 실행하지 않음)**

1. 스택 **꼭대기** squash merge (#196)
2. superseded PR close (#186–#195)
3. Step 0 / bridge PR (#188)
4. STATE sync PR (#197)

---

## 6. 실측·뮤테이션 규율

> **도구가 0이라고 해서 0이 아니다.**  
> **뮤테이션이 안 물리면 넘기지 마.**

### #192 — 라우트 인증

- 첫 ast 스캔: **11개 무인증**
- 코드 확인: 스캐너가 `_assert_node_matches` 를 몰라 **오탐**
- **실제 공개: 6개 GET** — STATE·D24 와 일치
- **「결함 11건」이라고 적지 않았다** — 이것이 자율 모드 보고 규율

### #196 — 시크릿 출력

- 첫 전수: **0건** → 첨자 `out["secret"]` · 셸 조건절 · `$cred` 낱말 · `if …; then echo` 를 **네 번** 고침
- **「뮤테이션이 안 물린다」= 검사가 헛도는 것** — 스캐너 자체를 뮤테이션으로 검증

### 새 검사 PR마다

1. **실측 표** — 오늘 새는 곳 / 건수 / 재현 명령
2. **뮤테이션 ≥2** — 우회 패치가 **실패**해야 함
3. **스캐너 한계** — inbox에 「스캐너가 X를 몰랐다」 기록
4. **같은 결함 계열 우선 탐색** — 0건 초록 · 공허 all/any · 기본값 위험 · 조용한 except

---

## 7. 절대 규칙 (`CLAUDE.md` 요약)

1. `docs/spec/schema.sql` 제약 약화 금지  
2. `assignment` · `gate_run` INSERT는 **INSERT … SELECT** 만  
3. `compute_tier` 앱에서 직접 비교 금지  
4. Node는 등급 주장 금지 — Core가 부여  
5. safetensors만 · 사전학습 금지  
6. D8′ — Core 중개 입력만 · 자유 업로드 금지  
7. 게이트는 team gate-runner Node만  
8. 측정 숫자 = 같은 커밋에 재현 명령

**D27:** `retrieve.*` 구현 금지.

---

## 8. Decision — **구현 PR 금지**

정본 목록: [`queue-expansion.md`](./queue-expansion.md) §7 (기존 아홉 + 8회차 둘).

막히면 `inbox-cursor.md`에 **Proposal 1블록** (`expects: decision`) → **다른 #(배치 / G)**.

---

## 9. 다음 큐

**정본:** [`queue-batches.md`](./queue-batches.md) (활성 배치) · [`queue-expansion.md`](./queue-expansion.md) §4–§6 (완료·G).

**완료(다시 하지 마):** #186–#196 · 큐 10(#200) · 큐 5 버전(#201) · 큐 11 기록(#202).

**지금 첫 줄:** **#12** (`prod_room.sh` vs 공개 GET). 그다음 13–40 · G1–G5.

응답 스키마(45/45 부재) · 원고 기기 주소 문장은 **Decision** — 구현하지 마.

---

## 10. 매 PR 체크리스트

- [ ] 절대규칙 8개
- [ ] `bash scripts/run_tests.sh` — 숫자를 PR·inbox에
- [ ] `python scripts/check_submission.py`
- [ ] 예방 검사: 뮤테이션 ≥2
- [ ] `docs/history/CHANGELOG.md` 선두 1건
- [ ] **다음 큐로 즉시 이동 — 멈춤 금지**

---

## 11. 세션 종료 조건 (이것만)

정본은 [`queue-expansion.md`](./queue-expansion.md) §2.

1. **활성 배치와 G가 비었고** 다음 배치가 미기입이며 남은 일은 Decision 구현뿐
2. **하드 블로커** — schema/CHECK/정책 숫자/제품 주장
3. 사용자가 **명시적으로 중단**

**5·10·11 소진은 종료가 아니다.** 12번으로 간다.

---

## 12. 세션 시작 (복붙용)

```bash
cd ~/pjt/ai-agent-store
git fetch origin main && git checkout main && git pull
gh pr list --state open --limit 100
git log -1 --oneline
bash scripts/run_tests.sh 2>&1 | tail -5
tail -n 120 docs/bridge/inbox-cursor.md
```

**읽을 파일 (순서):**

1. `docs/bridge/queue-batches.md` — **상태확인** · 활성 배치 A
2. `docs/bridge/queue-expansion.md` — 종료 · G
3. `docs/bridge/autonomous-mode.md` (이 파일)
4. `docs/bridge/handoff-long-mode-claude.md` 안쪽 markdown 블록
5. `docs/bridge/inbox-cursor.md` 끝
6. `CLAUDE.md` — 절대 규칙

**첫 작업:** 배치 B **#71**. 재시작은 채팅에 **`상태확인`**.

---

## 13. 금지 목록

- main merge / push / force push
- `retrieve.*` · timeseries 구현 (D27)
- TTL/truncation B without Decision
- `gh pr list` without `--limit 100`
- **머지·승인·「계속할까요?」 질문**
- ack 없는 inbox 블록을 done 으로 표기
- 스캐너 0건만으로 「안전」 주장

---

## 14. 7회차 성과 (기준선)

| 구분 | PR | 내용 |
|---|---|---|
| 결함 | #186–#191 | 깨진 계약 · 0건 방검사 · 폴백 · conflict · executor→image |
| 예방 | #192–#196 | Core 인증·역할 · Node · capreq 루프백 · 시크릿 출력 |
| Step 0 | #188 · #197 | 브리지 · STATE sync |

**합친 트리:** `run_tests` **571 OK (건너뜀 7)** · 충돌 0.

---

## 15. 갱신 이력

| 날짜 | main | 비고 |
|---|---|---|
| 2026-09-05 | — | 배치 A · queue-batches · 「상태확인」 |
| 2026-09-03 | `2c57c1e` | 큐 확장 — §9·§11을 `queue-expansion.md`에 맡김 (#203) |
| 2026-09-03 | `2cbb936` | 자율 모드 전문 최초 작성 (#198) |
| 2026-09-02 | `34d943f` | 7회차 머지 완료 (#196·#188·#197) |
