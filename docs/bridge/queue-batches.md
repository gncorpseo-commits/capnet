# CapNet — 큐 배치 (30개 단위)

> **이 파일이 정본인 것:** 활성 배치 · 배치별 시드 표 · 「상태확인」이 읽는 다음 줄  
> **루프:** [`autonomous-mode.md`](./autonomous-mode.md)  
> **종료·G:** [`queue-expansion.md`](./queue-expansion.md)  
> **붙여넣기:** [`handoff-long-mode-claude.md`](./handoff-long-mode-claude.md)

---

## 한 줄

**활성 배치가 빌 때까지 멈추지 마. 배치가 비면 G1–G5 · 그다음 Step 0에 「다음 배치 대기」만 적고, 머지를 묻지 마.**

---

## 0. 배치 규약

| 이름 | 번호 | 상태 |
|---|---|---|
| **배치 A** | **41–70** | **활성** ← 지금 전달분 |
| 배치 B | 71–100 | 예약 (A 소진 후 Cursor가 채움) |
| 배치 C | 101–130 | 예약 |

규칙:

1. Cursor/사람이 **한 번에 배치 하나**만 Claude에 전달한다.
2. Claude는 **활성 배치 표**만 소진한다. 다음 배치 표를 제멋대로 발명하지 않는다 (G1–G5는 예외).
3. 배치 안 우선순위 표를 따른다. 막히면 **다음 번호**로 — 전체 중단 금지.
4. 배치 소진 + G 5줄까지 돌린 뒤 → Step 0에 `expects: ack` 「배치 X 소진」.
5. **「배치가 비었다」≠ 세션 종료.** 종료는 `queue-expansion.md` §2만.

---

## 1. 「상태확인」 프로토콜 (재시작·동기화)

사용자가 **「상태확인」** 만 입력하면 (다른 말 없이) **아래를 한 턴에 끝낸 뒤 즉시 다음 큐 착수**한다.
질문·요약 장문·머지 요청 **금지**.

```text
S0. cd ~/pjt/ai-agent-store
S1. git fetch origin main && git checkout main && git pull
S2. gh pr list --state open --limit 100
S3. git log -1 --oneline
S4. bash scripts/run_tests.sh 2>&1 | tail -8
S5. 읽기 (이 순서, 짧게):
      docs/bridge/queue-batches.md        ← 활성 배치 · 다음 번호
      docs/bridge/queue-expansion.md §2·§4  ← 종료·완료분
      docs/bridge/autonomous-mode.md §2–3 ← 루프
      docs/bridge/handoff-long-mode-claude.md 안쪽 블록
      tail -n 100 docs/bridge/inbox-cursor.md
      CLAUDE.md (절대규칙 8)
S6. 한 줄 보고만 (채팅에 짧게):
      main=<sha> · PR열림=<n> · run_tests=<요약> · 다음=#N <한줄제목>
S7. **즉시 #N 착수** (A→F). 「계속할까요?」 금지.
```

**효율:** STATE.md 전문·CHANGELOG 전체·옛 inbox 수천 줄은 **읽지 않는다.**
완료분은 `queue-batches.md` §2 표 + `queue-expansion.md` §4만 본다.

---

## 2. 완료분 — 다시 하지 마 (배치 A 시작 시점)

| 구간 | PR/기록 |
|---|---|
| 7회차 3–9 | #186–#196 |
| 8회차 5·10·11 | #200–#202 |
| 9회차 12–33 | #205–#218 (코드없음 25·37·13·32) |
| 10회차 34–36·39·40·12옆 | #219–#223 · clean_room 9/9 · prod_room 51/51 |
| 코드없음 | 38·30 등 |

---

## 3. 배치 A — 시드 **41–70** (활성 · 30줄)

한 줄 = 한 PR(또는 스택 한 층). 뮤테이션 ≥2. CHANGELOG 선두 1건(코드 PR).
코드 없으면 inbox에 **근거 3줄**만 남기고 **다음 번호**.

### 우선순위 (세션 안)

```text
41 → 44 → 46 → 50 → 43 → 42 → 45
→ 49 → 64 → 47 → 48
→ 55 → 53 → 54
→ 59 → 61 → 58
→ 66 → 68 → 65 → 67
→ 51 → 52 → 56 → 57
→ 60 → 62 → 63
→ 69 → 70 → (배치 안 남은 번호) → G1–G5
```

### 표

| # | 무엇 | 왜 Decision 없는가 | 완료 모양 |
|---|---|---|---|
| **41** | `_references()` 뷰 컬럼 10종 사각 — 정적 풀 or 「못 본다」 핀 | #221 옆 | 핀 or 못 봤다 |
| **42** | `tests/integration/check_*.py` 를 누가 돌리나 — CI migrate ↔ `run_integration.sh` | #215 옆 | 핀 or 결함 |
| **43** | 손 허용 목록(`ALLOWED_READERS`·`REFERENCE_FLOOR`·`DECLARED_*`·`ALLOWED_*`) 전수 — 늘릴 때 근거 | #219/#221 | 표 + 핀 |
| **44** | `scripts/*.sh` 중 `set -euo pipefail` 없는 것 — **힌트:** `prod_room.sh`는 `set -uo` | 중간 실패 초록 | 결함 or 핀 |
| **45** | `compose.prod.yaml` `!override` 가 실제로 덮는지 — 정적 | 운영 | 핀 or 못 봤다 |
| **46** | `clean_room.sh` 프로브가 필수 쿼리/경로를 빼먹는가 | #223 형제 | 보강+검사 or 0 |
| **47** | `scripts/lib/{authprobe,tally,http}.sh` — 판정 함수에 단위 검사 0인가 | #44·#205 | 핀 |
| **48** | `prod_room`/`clean_room` 통과 N vs 런북·STATE 숫자 드리프트 | 측정 규율 | 검사 |
| **49** | 쓰기 라우트(POST/PUT/PATCH/DELETE) 무인증 401을 `prod_room`이 안 재는가 | #205 옆 | 표+핀 (파괴 없음) |
| **50** | `REFERENCE_FLOOR` 등 **바닥을 내리면 초록**인가 | #210 계열 | 뮤테이션 실패 |
| **51** | Core SQL 추출기 두 번째 사각(동적 SQL·문자열 포맷) | #41 다음 | 목록 고정 |
| **52** | `migrations/*.sql` vs `schema.sql` 최종 컬럼 — DDL 변경 없이 드리프트만 | #34 옆 | 표+검사 |
| **53** | `*.sh` ↔ 동명 `*.ps1` 주소·플래그 재전수 (#206 이후) | #206 | 표+핀 |
| **54** | `demo.sh`/`product_demo.sh`/`capreq_demo.sh` 같은 주장·다른 경로 | #200 옆 | 맞춤 or 핀 |
| **55** | `scripts/*.sh`가 curl 실패를 `|| true` / `000`으로 삼키는 자리 | #205 교훈 | 결함 or 허용+근거 |
| **56** | `node_onboard.sh`·`node_bind.sh` 시크릿 파일만 — 재전수+뮤테이션 | #196 옆 | 핀 |
| **57** | `migrate.sh`가 실패해도 다음 세대로 넘어가는 분기 | 운영 | 결함 or 핀 |
| **58** | `run_tests.sh` 건너뜀 수 vs `test_skip_reasons.ALLOWED` 개수 | #186/#215 | 일치 검사 |
| **59** | CI 「본다」문구 전수 — **ci.yml 수정 금지**(목록·문서만) | #215 · Decision 옆 | 목록 핀 |
| **60** | capreq 72 — fastapi 있으면 본실행 · 없으면 CI 로그만 못박기 | #11 잔여 | 숫자+재현 |
| **61** | compose 헬스체크가 항상 성공하는 명령 | 옛 #32 | 결함 or 0 |
| **62** | `INSTALL_TORCH`·빌드 ARG가 사전학습 가중치 경로를 여는가 | 절대규칙 6 | 0건 핀 |
| **63** | `regate.sh`/`proof_ab.sh` 본실행 or 「못 봄」명시 | Docker 열림 | 표 |
| **64** | 경로 `{id}` 인증 GET — 프로브가 401 전에 404/422로 끝나는가 | #223 일반화 | 규칙+검사 |
| **65** | `_require_*`/역할 가드 우회 신 패턴 (데코·DI) | #192/#193 | 스캔 or 0 |
| **66** | `ALLOWED_DATASET_IDS` ↔ HTML/시드/카탈로그 세 곳 | D8′ | 드리프트 검사 |
| **67** | Node execute 실패 — Core 다운 시 로컬만 성공으로 끝나는 경로 | #194/#207 | 결함 or 핀 |
| **68** | claim SQL에 `FOR UPDATE SKIP LOCKED` 없는 분기 | pitfalls §4 | 0건 핀 |
| **69** | CHANGELOG 선두 주장 ↔ 테스트 이름 같은 말 (G4 고정) | 메타 | 좁은 검사 |
| **70** | 열린 Decision 중 **코드 이미 나간 것** 표만 — **status 내리지 마** | #222 후속 · 코드 0 | Step 0 표 |

### 배치 A에서 하지 마

- `ci.yml`에 잡/설치 추가 (`round9-ci-coverage-proposal` Decision)
- openapi **응답** 스키마 · 대회 원고 기기주소
- TTL / truncation / `retrieve.*` / 11번째 능력
- schema CHECK 약화 · 정책 숫자 변경

---

## 4. 배치 B — 71–100 (예약 · **비어 있음**)

Cursor가 A 소진 후 채운다. Claude는 **이 절이 「미기입」이면 번호를 만들지 말고 G만** 한다.

| # | 무엇 | 상태 |
|---|---|---|
| 71–100 | _(미기입)_ | 대기 |

---

## 5. 배치 전달 문구 (사람이 Claude에 줌)

### 첫 세션 · 배치 A

```text
배치 A (41–70). docs/bridge/queue-batches.md · autonomous-mode.md · handoff 안쪽 블록을 읽는다.
「상태확인」절차로 동기화한 뒤 우선순위대로 41부터. 배치가 빌 때까지 멈추지 마. 머지 묻지 마.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

### 재시작 · 이어하기

```text
상태확인
```

(위 한 단어면 충분. `queue-batches.md` §1이 정의한다.)

### 배치 A 끝난 뒤 (사람)

새 배치 B 표를 `queue-batches.md`에 채운 뒤:

```text
배치 B (71–100) 활성화. queue-batches.md를 읽고 상태확인 후 71부터. 멈추지 마.
```

---

## 6. 갱신 이력

| 날짜 | 비고 |
|---|---|
| 2026-09-05 | 최초 — 배치 A 41–70 · 상태확인 프로토콜 · 배치 B 예약 |
