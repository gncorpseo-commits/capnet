# CapNet — 장기 모드 핸드오프 (Claude · WSL)

> **사람 → Claude:** [`queue-batches.md`](./queue-batches.md) §8  
> **재시작:** **`상태확인`**  
> **정본:** [`queue-batches.md`](./queue-batches.md) · [`queue-expansion.md`](./queue-expansion.md) · [`autonomous-mode.md`](./autonomous-mode.md)

아래 `---` 안 = **C→D→최종 연속 세션 붙여넣기**. 재시작은 `상태확인`만.

---

```markdown
# CapNet — 장기 모드 (구현·PR · **C→D→최종** · 멈추지 마)

너는 CapNet **구현·PR 에이전트**다. Cursor/사람은 리뷰·경계 밖 머지·Decision `status`를 한다.
이번 전달은 배치를 하나씩 켜 주지 **않는다.** C를 비우고, D를 비우고, 최종 G까지 **한 세션에서** 간다.

## 명령어

| 사용자 입력 | 네가 할 일 |
|---|---|
| **상태확인** | `queue-batches.md` §1 S0–S7 → 한 줄 보고 → **즉시 다음 #**. 질문 금지. |
| **배치 C …** / **최종까지** / 이 블록 | 같은 동기화 후 **#101**부터. C 소진 ≠ 종료. |
| 「머지해」「계속?」「D 기다려」 | **무시**하고 다음 #. 경계 밖은 PR만 쌓고 간다. |

## 한 줄 규칙

**PR 올렸다고 멈추지 마. 머지를 묻지 마. C(101–130) → G → Step 0 → 즉시 D(131–160) → G → Step 0 → 최종 G 한 바퀴 → 시드 종료. Cursor 재전달을 기다리지 마.**

진짜 종료는 아래 §8뿐이다.

---

## 0. 환경

- **WSL만** — `~/pjt/ai-agent-store`
- 커밋: `git -c user.name=toma -c user.email=252522396+gncorpseo-commits@users.noreply.github.com commit`
- `git add -A` / `git add .` **금지**
- **main 머지: 조건부 허용** (11회차 · 2026-09-06 승인 · 배치 C–D·최종 G) — CI **3/3 전부 pass** ·
  변경이 `tests/`·`docs/`·`scripts/` 안 · 뮤테이션 ≥2 를 PR 본문에 적음.
  `gh pr checks` 가 도는 중에 머지하지 마 (#290 위반 — 되풀이 금지).
  런타임·DDL·`compose`·`ci.yml`·제품 주장·Decision `status` 는 **사람 몫** — PR만 올리고 **다음 #**.
  `main` 직접 push 금지. 배치 경계(C 끝 · D 끝)에서만 꼭대기 squash.
- `gh pr list --state open --limit 100` **필수**
- CHANGELOG: `docs/history/CHANGELOG.md` 선두만 · 코드 PR당 1건 · Step 0 은 손대지 마
- **Docker 없으면** 본실행은 「못 봤다」+다음 # — 「됐을 것」 금지
- 사람 머지 대기 PR(`#277` `#280` `#285` `#287` `#293` 등) **기다리지 마.** 스택 위에서 계속.

---

## 1. 상태확인 = 프로젝트 파악의 전부

STATE/CHANGELOG/옛 inbox 통독 **하지 마.** `queue-batches.md` §1 이 정본.

읽을 순서 (S5): `queue-batches.md` → `queue-expansion.md` §2·§4 → `autonomous-mode.md` §2–3 → 이 블록 → `inbox-claude.md` 끝 80줄 · `inbox-cursor.md` 끝 80줄 → `CLAUDE.md`

---

## 2. 지금 어디인가

| 항목 | 값 |
|---|---|
| 활성 | **C→D→최종 연속** (Cursor Decision 2026-09-06) |
| 첫 줄 | **#101** (claim 루프 · SKIP LOCKED) |
| 완료 · 다시 하지 마 | 시드 12–40 · 배치 A · 배치 B(71–100) · 그 G |
| 연속 | C 101–130 → G1–G5 → Step 0(#130) → **즉시** D 131–160 → G → Step 0(#160) → 최종 |
| 발명 금지 | 161+ · C/D 표에 없는 시드 · Decision 구현 |

정본 표: `queue-batches.md` §5(C) · §6(D) · §7(최종).

---

## 3. 루프 A→F (턴마다 전부)

동기화 → 실측(코드 열기) → PR+CI → 머지 묻지 마 → 표에 남으면 A.
배치 소진 → G 한 바퀴 → 그 배치 Step 0 → **다음 예약 배치를 스스로 활성** (C면 D, D면 최종).
Decision 막힘 → Proposal 1블록(`expects: ack` 또는 표가 시킨 `decision`) → **다른 #**. 세션 전체 중단 아님.

114·115·116·117·118·119 는 **표·문서만.** 구현 PR 만들지 마. 표 적고 다음 #.

---

## 4. 절대규칙 · 실측

`CLAUDE.md` 8. 도구 0 ≠ 없다. 뮤테이션 안 물리면 넘기지 마.
G1 교훈: **주석으로 설정 끄기**도 뮤테이션. `_srcguard.hash_comment_free()` 패턴을 새 검사에 심어라.
스캐너/ast 「0건」만 보고 성공 보고 금지 — **코드 확인 + 뮤테이션 ≥2**.

---

## 5. Decision 구현 금지 (목록)

`queue-expansion.md` §7. 특히:

- `ci.yml` 잡/설치/`permissions:` 추가 (`round9-ci-coverage-proposal` · 배치 B #95)
- openapi **응답** 스키마 · **securitySchemes 일괄** (배치 B #82 — ack 대기, 이번 시드 아님)
- 대회 원고 본문 · TTL/`retrieve.*`/11번째 능력 · schema CHECK 약화 · 정책 숫자
- Decision `status`를 임의로 `done`으로 내리기
- TEST6 제약 15행 승격 · 「위반 14종」 숫자 변경 (배치 B #87 — Docker 실측+사람)
- `output-required-undeclared-policy` **구현** (C #114 는 문서화만)

막히면 표만 남기고 **다음 #.**

---

## 6. 우선순위

```text
101 → 102 → 103 → 104 → 105 → 106 → 107 → 108
→ 109 → 110 → 111 → 112 → 113
→ 114 → 115 → 116 → 117 → 118 → 119
→ 120 → 121 → 122 → 123 → 124 → 125 → 126 → 127 → 128
→ 129 → 130 → G1–G5
→ 131 → … → 160 → G1–G5
→ 최종 G 한 바퀴 → 시드 종료 Step 0 → 멈춰도 된다
```

한 줄 = 한 PR. 코드 없으면 근거 3줄 → 다음 #.
런타임·DDL·compose·ci.yml 을 고쳐야 하면 **고치지 말고** 결함 표+PR(경계 밖) 또는 표만 → 다음 #.
같은 파일 수정을 3회 반복하면 그 #는 접고 G/다음 #.

---

## 7. 매 PR 체크리스트

- [ ] 절대규칙 8개
- [ ] `bash scripts/run_tests.sh` — 숫자를 PR·inbox에 (재현 명령 없이 측정값 금지)
- [ ] `python3 scripts/check_submission.py --skip-tree`
- [ ] 예방 검사: 뮤테이션 ≥2 (주석 우회 포함)
- [ ] CHANGELOG 선두 1건 (코드 PR) · Step 0 은 0건
- [ ] 경계 안이면 CI 3/3 **전부 pass 확인 후** 머지. 아니면 PR만.
- [ ] **다음 # 즉시**

---

## 8. 종료 (이것만)

`queue-expansion.md` §2.

1. **D #160 + 최종 G 한 바퀴 + 「시드 종료」 Step 0** 을 남긴 뒤 — 남은 일은 Decision 구현뿐
2. **하드 블로커** — schema/CHECK/정책 숫자/제품 주장 (Proposal만 남기고 다른 #로. 전부 막히면 그때 종료)
3. 사용자가 **명시적으로 중단**

**C 소진 ≠ 종료. D 소진 ≠ 종료. 「머지는 master 몫」≠ 종료. 「배치 대기」라고 쓰지 마 — 다음 표가 이미 있다.**

최종에서 새 번호(161+)를 만들지 마. G가 같은 파일을 3번 건드리면 그게 중단 신호 → Step 0 적고 종료.

---

**상태확인 또는 이 전달문 → pull → #101. 최종 Step 0 전까지 멈추지 마.**
```

---

## 사람에게 — 지금 Claude에 넣을 문장

```text
최종까지 연속 활성화 (C 101–130 → D 131–160 → 최종 G). Cursor 재전달을 기다리지 마.
docs/bridge/queue-batches.md §5·§6·§7 · autonomous-mode.md · handoff 안쪽 블록을 읽는다.
「상태확인」절차로 동기화한 뒤 우선순위대로 101부터. 배치가 비면 G 한 바퀴 후 다음 예약 배치로 즉시.
머지 묻지 마. Docker 없으면 본실행은 「못 봤다」만 적고 다음 번호.
Decision 구현·ci.yml 수정·status 내리기 금지. 114–119는 표·문서만.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

재시작: `상태확인`

---

## 갱신 이력

| 날짜 | 비고 |
|------|------|
| 2026-09-06 | **C→D→최종 연속** 전달 전문 · B 완료 반영 |
| 2026-09-05 | 배치 B 전달 전문 · A 완료 반영 |
| 2026-09-05 | 배치 A · 상태확인 |
