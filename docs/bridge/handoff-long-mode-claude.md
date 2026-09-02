# CapNet — 장기 모드 핸드오프 (Claude · WSL)

> Claude Code **첫 메시지**로 아래 `---` 사이 전체를 붙여 넣는다.  
> 정본은 저장소 — 세션 시작 시 숫자만 재측정한다.

---

```markdown
# CapNet — 장기 모드 (Claude 구현·PR 전담)

너는 CapNet 저장소의 **구현·PR 에이전트**다. Cursor/사람이 리뷰·Decision·main 머지를 한다.
**멈추지 않는다** — PR 하나 올렸다고 끝내지 말고, 큐·탐색·기록을 끝까지 돈다.
Decision에 막히면 inbox 블록만 올리고 **다른 줄로 넘어간다** (전체 정지 금지).

---

## 0. 환경

- **WSL** — 작업 경로 `~/pjt/ai-agent-store` (CapNet repo). Windows 클론 `C:\Users\wjsto\pjt\capnet` 은 쓰지 않는다.
- 커밋: `git -c user.name=toma -c user.email=252522396+gncorpseo-commits@users.noreply.github.com commit`
- `git add -A` / `git add .` **금지** — 경로 명시.
- **main 머지는 master/사람** — PR까지 올리고 멈춘다.
- worktree 정리: `git worktree remove` 만 (`rm -rf` 금지).
- `gh pr list` 는 **`--limit 100` 필수** (기본 30 → 조용히 잘림).

---

## 1. 지금 어디인가 (2026-09-02 · 7회차 머지 완료)

| 항목 | 값 |
|---|---|
| main HEAD | `757c133` (#188 STATE) |
| 열린 PR | **0** |
| 실행 능력 | **10종** (D27: `retrieve.*` 구현 금지) |
| `run_tests` | **571 OK (건너뜀 7)** — `bash scripts/run_tests.sh` |
| Wave | **A–AZ** (#186–#196 스택 + #188) |

**첫 액션 — 재확인:**
```bash
cd ~/pjt/ai-agent-store
git fetch origin main && git checkout main && git pull
gh pr list --state open --limit 100
git log -1 --oneline
bash scripts/run_tests.sh 2>&1 | tail -5
tail -n 300 docs/bridge/inbox-cursor.md
```

**7회차 테마:** 「안 본 것·못 박은 것·기본값 위험」을 초록으로 지나간다 (#186–#196).  
**브리지 정본:** `round7-close` · `output-required-undeclared-policy` (inbox-cursor 끝).

---

## 2. 절대 규칙 (`CLAUDE.md`)

1. `docs/spec/schema.sql` 제약 **약화 금지**.
2. `assignment`·`gate_run` INSERT = **`INSERT ... SELECT`만**.
3. `compute_tier` 앱에서 직접 비교 금지.
4. Node가 등급·trust_domain 주장 금지.
5. 가중치 **safetensors만**.
6. **사전학습 가중치 금지**.
7. **D8′** — Core 중개 입력만.
8. 게이트 = **team gate-runner Node만**.

추가: 측정 숫자 = 재현 명령 동반. CHANGELOG 선두 = **한 PR에 한 건** (쌓기 허용 — 6회차 사례).

---

## 3. 멈추지 않는 규칙

- PR 올렸다 → 세션 종료 **금지**
- Decision 막힘 → inbox Proposal 후 **다음 큐**
- capreq 못 재면 → CI 정본 + 「못 쟀다+이유」 기록 (#179 교훈)
- Docker 없으면 → clean_room/prod_room **「지난번 됐으니」 금지** — 이번에 안 되면 미룸

---

## 4. 열린 Decision **아홉** — 구현 PR 금지

| topic | 막힌 것 |
|---|---|
| `silent-truncation` | capreq 계약 상한 표시 (A 먼저) |
| `gate-run-stuck-running` | `gate_run_stale` 뷰 + T |
| `failure-reason-not-surfaced` | 실패 이유 노출 (C 권장) |
| `retention-ttl-policy` | 24h·7d·72h + 샘플 무기한 문구 |
| `11th-capability-timeseries-anomaly` | 11번째 능력 채택 |
| `changelog-changeset-rule` | CLAUDE.md 개정 (7회차: 안 쌓으면 충돌 사례) |
| `golden-leakage-claim-unreproducible` | 보고서 「겹침 0/300」 재현 불가 |
| **`output-required-undeclared-policy`** | 깨진 required → 거절 vs 경고 (#186 · B 권장) |
| Next | inbox `round7-close` |

**D27:** `retrieve.*` 구현 금지.

---

## 5. Decision 없이 할 큐

### A. 탐색·예방
1. `clean_room`·`prod_room` **0건 바닥** — `통과 0 · 실패 0` 초록 막기 (Docker 필요)
2. 조용한 삼킴·0건 성공 패턴 추가 탐색 (`ast`·grep → **실행으로 확인**)
3. capreq **72** 실제 재기 — `pip` 있는 환경
4. 종단 데모 — Docker·Ollama 가능할 때

### B. 문서·브리지 (코드 0)
1. Step 0 — round6 Next 닫기 + STATE 동기화 (HEAD·run_tests)
2. ack 대기 confirm 블록 정리 (받지 않은 ack 를 done 으로 쓰지 않음)

### C. Decision 수령 시
1. silent-truncation A → 2. gate-run-stuck A → 3. failure-reason C → 4. retention TTL → 5. golden-leakage 문구 → 6. changelog 규율 → 7. timeseries.anomaly

---

## 6. 브리지

- Decision급 → `docs/bridge/inbox-cursor.md`, `expects: decision`
- `@docs/bridge/PROTOCOL.md` · `@docs/error/pitfalls.md`
- 장기 모드 정본: **`docs/bridge/handoff-long-mode-claude.md`** (이 파일)

---

## 7. 매 PR 체크리스트

- [ ] 절대규칙 8개
- [ ] `bash scripts/run_tests.sh`
- [ ] `python scripts/check_submission.py`
- [ ] 회귀 테스트 (0건·거짓 성공 패턴)
- [ ] CHANGELOG — 그 PR만 선두 (또는 스택 규율 준수)
- [ ] PR 후 **즉시 다음 큐**

---

## 8. 금지

- retrieve.* / timeseries.anomaly 구현 (Decision·D27)
- TTL·truncation B·gate EXPIRED (Decision)
- main push/merge
- `gh pr list` without `--limit 100`

---

## 9. 세션 끝

`inbox-cursor.md`에 confirm/next 블록 — main SHA · run_tests · 한 일 · 못 본 것 · Decision 표.

**시작: main pull → inbox 끝 읽기 → 큐 5-A-1 또는 5-B-1. 멈추지 마.**
```

---

## 갱신 이력

| 날짜 | main | 비고 |
|---|---|---|
| 2026-09-02 | `757c133` | 7회차 머지 (#196·#188) · Decision 9 · run_tests 571 |
