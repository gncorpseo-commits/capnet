# CapNet 자율 모드 — 큐 확장 전문

> **대상:** WSL Claude Code (구현·PR) · Cursor/사람 (리뷰·main 머지)  
> **이 파일이 정본인 것:** 종료 조건 · 시드 12–40 완료 기록 · 상시 생성기 G1–G5  
> **활성 시드 41+ (30개 배치):** [`queue-batches.md`](./queue-batches.md)  
> **루프·스택·실측:** [`autonomous-mode.md`](./autonomous-mode.md)  
> **붙여넣기·상태확인:** [`handoff-long-mode-claude.md`](./handoff-long-mode-claude.md)

---

## 한 줄 규칙

**번호 큐가 비면 멈추지 마. 활성 배치 → G. 머지를 묻지 마. 「상태확인」이면 동기화 후 즉시 다음 #.**

---

## 1. 왜 큐를 늘리는가

8회차(2026-09-03)는 큐 **세 줄**(#10 · #5 · #11)을 한 세션에서 비우고 멈췄다.
멈춘 이유는 **다음에 잴 줄이 없어서**다. 이후 시드 12–40 · **배치 A 41–70**으로 줄을 고정한다.
큐를 늘리는 것은 Decision이 아니다. **실측 대상 목록**이다.

---

## 2. 종료 조건 (이것만)

세션을 끝내도 되는 때:

1. **활성 배치와 G 루프가 비었고** 다음 배치가 미기입이며 남은 일이 Decision 구현뿐이다
2. **하드 블로커** — schema/CHECK/정책 숫자/제품 주장
3. 사용자가 **명시적으로 중단**

**번호·배치 소진 ≠ 종료.** Step 0에 「다음 큐」≥3 또는 「다음 배치 대기」 후 루프 가능.
「머지는 master 몫이라 멈춘다」는 종료 이유가 **아니다.**

---

## 3. 큐를 스스로 늘리는 규칙

매 코드 PR 또는 Step 0마다 inbox에 **다음 줄 ≥3**을 남긴다.
**활성 배치 표를 벗어나 71+를 발명하지 않는다** — 그건 Cursor가 `queue-batches.md`에 채운다.
배치가 비면 **G1–G5만** (아래 §6).

고르는 우선순위: `queue-batches.md` 배치 안 우선순위표 → 옆자리 → G.

**금지:** Decision 구현 · `retrieve.*` · 정책 숫자 · schema 약화 ·
대회 원고 본문 수정(Proposal만) · ack 없는 블록을 done으로 쓰기.

---

## 4. 완료분 — 다시 하지 마

| 큐 | PR | 상태 |
|---|---|---|
| 3·4·6·7·8·9 | #186–#196 | 7회차 |
| **10** · **5**(버전) · **11** | #200–#202 | 8회차 |
| **12–40** | #205–#223 등 | 9–10회차 · 시드 소진 |
| **41–70** | — | **배치 A 진행 중** → [`queue-batches.md`](./queue-batches.md) §3 |

상세 완료 표·활성 시드는 **queue-batches.md** 가 정본이다.

---

## 5. 시드 큐 12–40 (아카이브 · 완료)

9회차 정본. **다시 하지 마.**

완료: 12(#205·#223) · 13–33(#206–#218) · 34–36·39(#219–#222) · 38·30·40 코드없음/환경.
열린 Decision만 남긴 것: `contest-report-device-address-claim` · `openapi-response-schemas`.

---

## 5b. 시드 41+ — 배치 정본

**[`queue-batches.md`](./queue-batches.md)** — 배치 A(41–70) · 상태확인 · 전달 문구.

---

## 6. 상시 생성기 (활성 배치가 비면)

한 번에 **5줄**을 inbox에 추가하고 계속한다.

```text
G1. 방금 PR의 뮤테이션이 안 덮는 우회 한 가지를 더 심고 검사 보강
G2. 같은 디렉터리의 형제 파일 전수 (예: scripts/*.sh 다음 파일)
G3. 「오늘은 0」인 전수의 재현 명령을 tests/에 남겼는가 — 없으면 핀
G4. CHANGELOG 선두 주장이 테스트 이름과 같은 말을 하는가
G5. CI 3잡이 로컬 run_tests와 다른 파일을 보는가
```

G 루프는 Decision이 아니다. 새 능력이 아니다.
실측 0이면 「0 + 재현」만 남기고 다음 G.

**그래도 멈추는 신호** → Proposal 1블록 → **G/배치로 복귀.** 전체 중단 아님.

---

## 7. Decision — 구현하지 마 (목록만)

- `silent-truncation` · `gate-run-stuck-running` · `failure-reason-not-surfaced`
- `retention-ttl-policy` · `11th-capability-timeseries-anomaly`
- `changelog-changeset-rule` · `golden-leakage-claim-unreproducible`
- `output-required-undeclared-policy` (#186 · B 거절 권장)
- **`contest-report-device-address-claim`** · **`openapi-response-schemas`**
- **`round9-ci-coverage-proposal`** (ci.yml 수정)
- Next · D27 `retrieve.*`

---

## 8. 세션 시작 / 상태확인

**재시작:** 채팅에 `상태확인` → `queue-batches.md` §1.

**첫 배치 A:**

```text
배치 A (41–70). docs/bridge/queue-batches.md · autonomous-mode.md · handoff 안쪽 블록을 읽는다.
「상태확인」절차로 동기화한 뒤 우선순위대로 41부터. 배치가 빌 때까지 멈추지 마. 머지 묻지 마.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

읽을 순서: `queue-batches.md` → `queue-expansion.md` §2·§4 → `autonomous-mode.md` → handoff → inbox 끝 → `CLAUDE.md`.

**첫 작업:** 큐 **#41**.

---

## 9. 갱신 이력

| 날짜 | 비고 |
|---|---|
| 2026-09-05 | 배치 A 41–70 · queue-batches · 상태확인 · 12–40 아카이브 |
| 2026-09-05 | 10회차 머지 · 다음 41–45 (#224) |
| 2026-09-03 | 최초 — 시드 12–40 · G1–G5 (#203) |
