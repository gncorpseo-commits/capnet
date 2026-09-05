# CapNet 자율 모드 — 큐 확장 전문

> **대상:** WSL Claude Code (구현·PR) · Cursor/사람 (리뷰·main 머지)  
> **이 파일이 정본인 것:** 종료 조건 · 시드 큐 12–40 · 상시 생성기 G1–G5  
> **루프·스택·실측 규율:** [`autonomous-mode.md`](./autonomous-mode.md)  
> **붙여넣기:** [`handoff-long-mode-claude.md`](./handoff-long-mode-claude.md)

---

## 한 줄 규칙

**번호 큐가 비면 멈추지 마. 상시 목록에서 다음을 집어 적고 바로 착수한다. 머지를 묻지 마.**

---

## 1. 왜 큐를 늘리는가

8회차(2026-09-03)는 큐 **세 줄**(#10 · #5 · #11)을 한 세션에서 비우고 멈췄다.

| PR | 큐 | 무엇 |
|---|---|---|
| #200 | 10 | README가 틀린 파일을 지목 — `demo.sh` vs `product_demo.sh` |
| #201 | 5 | openapi `info.version` 0.3.0 ↔ 앱 0.2.0 |
| #202 | 11 + Step 0 | Docker/pip 불가 기록 · Decision 둘 Proposal |

멈춘 이유는 도구가 아니라 **다음에 잴 줄이 없어서**다.
`autonomous-mode.md` §11이 「5·10·11 소진 = 종료」라서, Claude가 규약대로 끝냈다.

큐를 늘리는 것은 Decision이 아니다. **실측 대상 목록**이다.
제품 주장·스키마·TTL을 바꾸지 않는 한, 같은 결함 계열을 더 전수해도 된다.

---

## 2. 종료 조건 (이것만)

세션을 끝내도 되는 때:

1. **시드 12–40과 상시 G 루프가 비었고** 남은 일이 Decision 구현뿐이다
2. **하드 블로커** — schema/CHECK/정책 숫자/제품 주장
3. 사용자가 **명시적으로 중단**

**번호 큐 소진 ≠ 종료.** Step 0에 「다음 큐」를 **≥3줄** 채운 뒤 즉시 루프 A.

미머지 PR이 있어도 **같은 갈래 예방·핀·결함 PR**은 계속 쌓는다.
금지되는 것은 **큰 새 제품 Wave**(새 능력 · DDL · 유통) 뿐이다.

「머지는 master 몫이라 멈춘다」는 종료 이유가 **아니다.**

---

## 3. 큐를 스스로 늘리는 규칙

매 코드 PR 또는 Step 0마다 inbox에 **다음 줄 ≥3**을 남긴다.

```text
### 다음 큐 (Decision 없이)
N. <한 줄 실측 대상> — <재현 힌트> — <핀 | 결함 | 못 봤다>
```

고르는 우선순위:

1. 방금 고친 것과 **같은 결함 계열**의 옆자리
2. 「고치고 못박지 않은」 주석 · CHANGELOG · `이전에는`
3. 두 사본 · 두 버전 · 문서 vs 코드
4. 0건 초록 · 공허 `all`/`any` · 기본값 `else` · 조용한 `except`
5. 환경 없으면 「못 봤다」만 적고 **다음 줄**

**금지:** Decision 구현 · `retrieve.*` · 정책 숫자 · schema 약화 ·
대회 원고 본문 수정(Proposal만) · ack 없는 블록을 done으로 쓰기.

---

## 4. 완료분 — 다시 하지 마

| 큐 | PR | 상태 |
|---|---|---|
| 3·4·6·7·8·9 | #186–#196 | 7회차 완료 |
| **10** | #200 | README 「할 수 있다」 핀. **원고 세 줄은 Decision** (`contest-report-device-address-claim`) |
| **5** (버전) | #201 | `info.version` 드리프트 핀. **응답 스키마 45/45 부재는 Decision** (`openapi-response-schemas`) |
| **11** | #202 기록 · **#219 트리에서 `clean_room` 본실행** | 10회차 Docker 생김 → **통과 9 · 실패 0** |
| **12** | #205 · **#223** | 라우트 전수 + 필수 쿼리(`node_id`) — `prod_room` **51/51** |
| **13–33** | #206–#218 등 | 9회차 · 코드 없음(25·37·13·32) 포함 |
| **34–36 · 39** | #221 · #220 · #219 · #222 | 10회차 |
| **38 · 30 · 40** | — | 코드 없음 / Docker 재측정 완료 |

**시드 12–40 소진.** 다음 줄 = inbox **41–45** → G1–G5.

---

## 5. 시드 큐 12–40 (9회차 정본)

한 줄 = **한 PR**(또는 스택 한 층). 뮤테이션 ≥2. CHANGELOG 선두 1건(코드 PR).

**우선순위:** 12 → 22 → 33 → 14–19 → 20·21 → 나머지.

| # | 무엇 | 왜 Decision 없는가 | 완료 모양 |
|---|---|---|---|
| **12** | `prod_room.sh`가 손으로 고른 여섯 개만 누르는가 vs 공개 GET 전수 | 운영 스크립트 핀 | 누락이면 검사 또는 스크립트 보강 |
| **13** | Compose/Dockerfile의 `0.0.0.0`·포트 vs capreq 루프백 전제 | #195 옆자리 | 상수·주석 불일치면 핀 |
| **14** | pickle / `.pt` / `.pth` 로드 경로 전수 (거부) | 절대규칙 5 | 새 로드가 생기면 실패하는 검사 |
| **15** | `assignment`·`gate_run` INSERT가 `INSERT … SELECT`만인가 | 절대규칙 2 | ORM insert 뮤테이션이 실패 |
| **16** | Node가 `trust_domain`/`compute_tier_max`를 그대로 기록하는 경로 0건 | 절대규칙 4 | 핀 |
| **17** | 게이트가 제출자 Node에서 돌 수 있게 열린 경로 0건 | 절대규칙 8 | 핀 |
| **18** | 자유 업로드 · 서명 URL · `fileToken` 경로 0건 (D8′) | 절대규칙 7 | 핀 |
| **19** | `compute_tier` 앱 문자열 비교 (`<` / `sort`) 0건 | 절대규칙 3 | 핀 |
| **20** | `except Exception` / bare except가 삼키고 성공으로 끝나는 자리 | 7회차 재확인 | 결함 or 핀 |
| **21** | 테스트가 빈 컬렉션만 돌고 초록 (루프 안 단언, 바닥 없음) | #187 계열 | 결함 or 「바닥 있음」 표 |
| **22** | 문서·스크립트가 기기 주소/Node URL을 잘못 지목 (**원고 제외**) | #200 옆자리 | user-guide·HTML·다른 sh 전수 |
| **23** | 버전 문자열 드리프트 (`0.2.0` / `0.3.0` / package / CI) | #201 옆자리 | 한곳으로 못박거나 표로 핀 |
| **24** | OpenAPI **요청** 스키마 vs 핸들러 파라미터 | 응답 스키마는 Decision 대기 | 경로·메서드 다음 층 |
| **25** | `openapi.yaml` 두 사본 — 머리말·서버 URL까지 | 경로 동일 검사 있는지 실측 | 핀 |
| **26** | CI 잡 vs `run_tests.sh` 스킵 구멍 | 「CI만 본다」를 목록화 | 못 봤다 금지 |
| **27** | seed/카탈로그 「구현됨」 ↔ 실행기 등록 (없는 이름) | 개수 세기는 OK | 핀 |
| **28** | HTML 데이터셋 폴백·데모 이미지 기본값 | #184·#189 옆, 템플릿 | 결함 or 핀 |
| **29** | `scripts/`가 Core 우회해 Node를 누르는 명령 (`demo.sh` 외) | #200이 연 자리 | 표 + 핀 |
| **30** | 측정 숫자 재현 명령 없는 **신규** 카탈로그/STATE 줄 | measured-claims §7 | 위반 있으면 좁은 검사 |
| **31** | GitHub Actions 로그에 시크릿이 그대로 찍히는가 | #196 옆, YAML | 핀 |
| **32** | compose 헬스체크가 항상 성공하는 명령 | 0건 초록 계열 | 결함 or 핀 |
| **33** | `TODO`/`FIXME`/`이전에는` 주석 중 못박힌 검사 없는 과거 버그 | #194 패턴 | 핀 |
| **34** | Core 코드 vs `schema.sql` **컬럼명** ast (DDL 변경 없음) | 드리프트만 | 불일치 표 |
| **35** | capreq 어댑터가 키를 쿼리/URL에 싣는가 | #195 옆 | 핀 |
| **36** | 스크립트가 `gh pr list`를 `--limit 100` 없이 쓰는가 | 운영 실수 핀 | 강제 |
| **37** | 공개 GET 6개가 STATE·D24·#192 PUBLIC과 세 곳 일치 | 문서 삼각 | 핀 |
| **38** | `test_*` 머리말 「fastapi 없이 돈다」 vs 실제 import | 거짓 머리말 | 결함 or 정정 |
| **39** | 열린 `expects: decision` 목록만 최신화 | 문서 · 코드 0 | Step 0 표 |
| **40** | WSL에 pip/Docker가 생겼는지 재측정. 생겼으면 #11 본실행 | 환경 | 본실행 or 「여전히 못 봄」 |

스택: 가능하면 **#201 위**에 12번을 쌓는다. Step 0(#202 류)은 **독립 브랜치**.

---

## 6. 상시 생성기 (40번까지 비면)

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

**그래도 멈추는 신호**

- G가 **같은 파일만** 세 번 반복
- 열린 Decision을 구현으로 풀고 싶어짐
- schema.sql / 정책 숫자를 건드리고 싶어짐

→ Proposal 1블록 → **다음 시드/G로 복귀.** 전체 중단 아님.

---

## 7. Decision — 구현하지 마 (목록만)

기존 아홉 + 8회차가 올린 둘:

- `silent-truncation` · `gate-run-stuck-running` · `failure-reason-not-surfaced`
- `retention-ttl-policy` · `11th-capability-timeseries-anomaly`
- `changelog-changeset-rule` · `golden-leakage-claim-unreproducible`
- `output-required-undeclared-policy` (#186 · B 거절 권장)
- **`contest-report-device-address-claim`** (#202 · 원고 세 줄)
- **`openapi-response-schemas`** (#202 · 2xx 스키마 0/45)
- Next · D27 `retrieve.*`

---

## 8. 세션 시작 (복붙)

```text
docs/bridge/queue-expansion.md 와 autonomous-mode.md 와 handoff-long-mode-claude.md 안쪽 블록을 읽는다.
시드 12–40은 끝났다. 번호가 비면 inbox 41–45 · 없으면 G1–G5.
PR 후 다음 줄을 inbox에 ≥3 남기고 즉시 다음 항목.
머지 묻지 마. Decision 구현하지 마.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
gh pr list --state open --limit 100
```

읽을 순서:

1. 이 파일 (`queue-expansion.md`)
2. `autonomous-mode.md`
3. `handoff-long-mode-claude.md` 안쪽 블록
4. `inbox-cursor.md` 끝
5. `CLAUDE.md`

**첫 작업:** 큐 **#41** (`_references()` 뷰 컬럼 사각). 시드 12–40은 다시 하지 마.

---

## 9. 갱신 이력

| 날짜 | 비고 |
|---|---|
| 2026-09-05 | `9804b97` | 10회차 머지 · 시드 12–40 소진 · 다음 41–45 |
| 2026-09-03 | `2c57c1e` | 최초 작성 — 8회차 종료 조건 개정 · 시드 12–40 · G1–G5 (#203) |
