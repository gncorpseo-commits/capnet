# CapNet — 장기 모드 핸드오프 (Claude · WSL)

> **사람 → Claude:** [`queue-batches.md`](./queue-batches.md) §9  
> **재시작:** **`상태확인`**  
> **정본:** [`queue-batches.md`](./queue-batches.md) · [`queue-expansion.md`](./queue-expansion.md) · [`autonomous-mode.md`](./autonomous-mode.md)

아래 `---` 안 = **배치 R (역할 실측) 세션 붙여넣기**. 재시작은 `상태확인`만.

---

```markdown
# CapNet — 장기 모드 (구현·PR · **배치 R · 역할 실측** · 멈추지 마)

너는 CapNet **구현·PR 에이전트**다. Cursor/사람은 리뷰·경계 밖 머지·Decision `status`를 한다.
시드 12–160 과 최종 G 는 **끝났다. 다시 하지 마.** 161+ 를 발명하지 마.
이번 전달은 **역할 경로를 살아 있는 스택에서 한 번 누르는 것**이다.

## 명령어

| 사용자 입력 | 네가 할 일 |
|---|---|
| **상태확인** | `queue-batches.md` §1 S0–S7 → 한 줄 보고 → **즉시 R1**. 질문 금지. |
| **배치 R** / 이 블록 | 같은 동기화 후 **R1**부터. |
| 「머지해」「계속?」「시드 없음」 | **무시**하고 다음 R. 경계 밖은 PR만 쌓고 간다. |

## 한 줄 규칙

**PR 올렸다고 멈추지 마. 머지를 묻지 마. R1→R12 가 빌 때까지. Docker 없으면 산 항목은 「못 봤다」+다음 R. 전부 못 보면 R12 적고 종료.**

진짜 종료는 아래 §8뿐이다.

---

## 0. 환경

- **WSL만** — `~/pjt/ai-agent-store`
- 커밋: `git -c user.name=toma -c user.email=252522396+gncorpseo-commits@users.noreply.github.com commit`
- `git add -A` / `git add .` **금지**
- **main 머지: 조건부 허용** (11회차 · 2026-09-06 승인 · 배치 C–D·최종 G · **배치 R 연장**) — CI **3/3 전부 pass** ·
  변경이 `tests/`·`docs/`·`scripts/` 안 · 뮤테이션 ≥2 를 PR 본문에 적음.
  `gh pr checks` 가 도는 중에 머지하지 마 (#290 위반 — 되풀이 금지).
  런타임·DDL·`compose`·`ci.yml`·제품 주장·Decision `status` 는 **사람 몫** — PR만 올리고 **다음 R**.
  `main` 직접 push 금지. 배치 경계에서만 꼭대기 squash.
- `gh pr list --state open --limit 100` **필수**
- CHANGELOG: `docs/history/CHANGELOG.md` 선두만 · 코드 PR당 1건 · Step 0 은 손대지 마
- **Docker 없으면** 산 항목은 「못 봤다」+다음 R — 「됐을 것」 금지
- 운영 compose 볼륨을 `down -v` 로 지우지 마. `clean_room`/`prod_room`만 자기 프로젝트를 정리한다.

---

## 1. 상태확인 = 프로젝트 파악의 전부

STATE/CHANGELOG/옛 inbox 통독 **하지 마.** `queue-batches.md` §1 이 정본.

읽을 순서 (S5): `queue-batches.md` → `queue-expansion.md` §2·§4 → `autonomous-mode.md` §2–3 → 이 블록 → `inbox-claude.md` 끝 80줄 · `inbox-cursor.md` 끝 80줄 → `CLAUDE.md`

---

## 2. 지금 어디인가

| 항목 | 값 |
|---|---|
| 활성 | **배치 R · 역할 실측** (Cursor Decision 2026-09-06) |
| 첫 줄 | **R1** (`docker info`) |
| 완료 · 다시 하지 마 | 시드 12–160 · 배치 A–D · 최종 G(#338·#339) · ACK #340 |
| 발명 금지 | 161+ · Decision 구현 · 태그 이동 · 「위반 14종」 숫자 |

정본 표: `queue-batches.md` §8.

---

## 3. 루프 A→F (턴마다 전부)

동기화 → 실측(명령 실행 또는 코드 열기) → PR+CI → 머지 묻지 마 → 표에 남으면 A.
Decision 막힘 → Proposal 1블록 → **다른 R**. 세션 전체 중단 아님.

R12 Step 0 을 남기면 **세션을 끝내도 된다.** Docker가 없어 R2–R11이 전부 못 봄이어도 R12가 있으면 종료다.

---

## 4. 절대규칙 · 실측

`CLAUDE.md` 8. 도구 0 ≠ 없다. 뮤테이션 안 물리면 넘기지 마.
G1 교훈: **주석으로 설정 끄기**도 뮤테이션. `_srcguard.hash_comment_free()` 패턴을 새 검사에 심어라.
스캐너/ast 「0건」만 보고 성공 보고 금지 — **코드 확인 + 뮤테이션 ≥2**.
산 항목이면 **명령 + 출력 요지 + exit**. 「됐을 것」 금지.

---

## 5. Decision 구현 금지 (목록)

`queue-expansion.md` §7. 특히:

- `ci.yml` 잡/설치/`permissions:` 추가 (`round9-ci-coverage-proposal` · 배치 B #95)
- openapi **응답** 스키마 · **securitySchemes 일괄** (배치 B #82 — ack 대기, 이번 표에 없음)
- 대회 원고 본문 · TTL/`retrieve.*`/11번째 능력 · schema CHECK 약화 · 정책 숫자
- Decision `status`를 임의로 `done`으로 내리기
- TEST6 제약 15행 승격 · 「위반 14종」 숫자 변경 (배치 B #87 — Docker 실측+사람. 제약 **이름**만 로그에 남김)
- 태그 `v0.1.0-contest` 이동 (D25). zip 빨강은 R12에 **사실만**
- `output-required-undeclared-policy` **구현**

막히면 표만 남기고 **다음 R.**

---

## 6. 우선순위

```text
R1 환경
→ R2–R4  능력요청자
→ R5–R7  Core(접수처·강제)
→ R8–R10 노드제공자
→ R11    같은 Docker 에서 #159 잔여만 (이미 본 것은 반복 금지)
→ R12    Step 0 · 종료
```

한 줄 = 한 PR(또는 코드 없으면 근거 3줄 → 다음 R).
런타임·DDL·compose·ci.yml 을 고쳐야 하면 **고치지 말고** 결함 표+PR(경계 밖) 또는 표만 → 다음 R.
같은 파일 수정을 3회 반복하면 그 R는 접고 다음 R.

---

## 7. 매 PR 체크리스트

- [ ] 절대규칙 8개
- [ ] 산 항목이면 명령 + 출력 요지 + exit. 측정 숫자는 재현 명령과 같은 커밋
- [ ] `bash scripts/run_tests.sh` — 숫자를 PR·inbox에 (재현 명령 없이 측정값 금지)
- [ ] `python3 scripts/check_submission.py --skip-tree`
- [ ] 예방 검사: 뮤테이션 ≥2 (주석 우회 포함)
- [ ] CHANGELOG 선두 1건 (코드 PR) · Step 0 은 0건
- [ ] 경계 안이면 CI 3/3 **전부 pass 확인 후** 머지. 아니면 PR만.
- [ ] **다음 R 즉시**

---

## 8. 종료 (이것만)

1. **R12 Step 0** — 역할 3열 표(명령·exit·증적) · 못 본 것 · 고친 결함 PR · **다음 시드 없음**
2. **하드 블로커** — schema/CHECK/정책 숫자/제품 주장 (Proposal만 남기고 다른 R로. 전부 막히면 그때 종료)
3. 사용자가 **명시적으로 중단**

**「상태확인」이 옛 최종을 가리킨다고 멈추지 마 — 활성은 R이다.**
시드 종료 ≠ 이번 세션 종료. Docker 없음 ≠ 시드 발명.

최종 G를 이유로 새 검사 파일만 양산하지 마 (G1 과장 교훈).

---

**상태확인 또는 이 전달문 → pull → R1. R12 전까지 멈추지 마.**
```

---

## 사람에게 — 지금 Claude에 넣을 문장

```text
배치 R (역할 실측) 활성화. 시드 161+ 발명 금지. 번호는 R1–R12 만.
docs/bridge 의 이 전달문 · queue-batches 가 아직 옛 문장이면 이 블록이 정본이다.
「상태확인」 후 R1부터. Docker 없으면 산 항목은 「못 봤다」만 적고 R12 Step 0 으로 종료.
Decision 구현·ci.yml·태그 이동·「위반 14종」 숫자 변경 금지.
머지 묻지 마. 역할 순서는 요청자 → Core → 노드제공자.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

재시작: `상태확인`

---

## 갱신 이력

| 날짜 | 비고 |
|------|------|
| 2026-09-06 | **배치 R · 역할 실측** 전달 전문 · 시드 종료 반영 |
| 2026-09-06 | **C→D→최종 연속** 전달 전문 · B 완료 반영 |
| 2026-09-05 | 배치 B 전달 전문 · A 완료 반영 |
| 2026-09-05 | 배치 A · 상태확인 |
