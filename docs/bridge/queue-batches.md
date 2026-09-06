# CapNet — 큐 배치 (30개 단위)

> **이 파일이 정본인 것:** 활성 배치 · 배치별 시드 표 · 「상태확인」 · **배치 R (역할 실측)**  
> **루프:** [`autonomous-mode.md`](./autonomous-mode.md)  
> **종료·G:** [`queue-expansion.md`](./queue-expansion.md)  
> **붙여넣기:** [`handoff-long-mode-claude.md`](./handoff-long-mode-claude.md)

---

## 한 줄

**R이 빌 때까지 멈추지 마. Docker 없으면 산 항목은 「못 봤다」만 적고 R12. 시드 161+ 발명 금지. 머지 묻지 마.**

---

## 0. 배치 규약

| 이름 | 번호 | 상태 |
|---|---|---|
| 배치 A | 41–70 | **완료** (#226–#262 · G1–G5) |
| 배치 B | 71–100 | **완료** (#266–#294 · G · Step 0) |
| 배치 C | 101–130 | **완료** (#297–#314 · Step 0) |
| 배치 D | 131–160 | **완료** (#316–#337 · Step 0) |
| 최종 | — | **완료** · G 한 바퀴(#338·#339) · 시드 종료 · Decision 표는 사람 (§7) |
| **배치 R** | R1–R12 | **활성 — 지금 여기** · **역할 실측 완료** (R1 Docker 없음 → R2–R11 못 봄 · R12) · Decision만 (§8) |

규칙:

1. **이번 전달 = 배치 R.** 시드 12–160 과 최종 G 는 끝났다. 다시 하지 마.
2. Claude는 **현재 표**만 소진한다. 161+ 와 표 밖 시드를 발명하지 않는다.
3. 배치 안 우선순위를 따른다. 막히면 **다음 번호**.
4. **시드 종료 ≠ 이번 세션 종료.** 「최종」에서 멈추지 마 — 활성은 R 이다.
5. 종료는 `queue-expansion.md` §2 · 이 파일 §8 끝 (R12).
6. **Docker 데몬 없으면** 산 항목은 「못 봤다+이유」만 적고 **다음 R** — 「됐을 것」 금지. 산 항목이 전부 못 보면 **R12로 가서 종료**.
7. 런타임·DDL·`compose`·`ci.yml` 수정이 필요하면 **PR만** (또는 표만) 남기고 다음 R. 묻지 마.

---

## 1. 「상태확인」 프로토콜

사용자가 **「상태확인」** 만 입력하면 아래를 **한 턴에** 끝낸 뒤 즉시 다음 #.

```text
S0. cd ~/pjt/ai-agent-store
S1. git fetch origin main && git checkout main && git pull
S2. gh pr list --state open --limit 100
S3. git log -1 --oneline
S4. bash scripts/run_tests.sh 2>&1 | tail -8
S5. 읽기: queue-batches.md → queue-expansion §2·§4 → autonomous-mode §2–3
         → handoff 안쪽 → inbox-claude 끝 80줄 · inbox-cursor 끝 80줄 → CLAUDE.md
S6. 한 줄: main=<sha> · PR=<n> · tests=<요약> · 다음=R1 <제목>
S7. 즉시 다음 줄 착수. 「계속?」 금지.
```

STATE·CHANGELOG·옛 inbox 통독 **금지**.

다음 줄 고르기: 미완료인 **가장 앞 R**. R이 비었으면 R12가 이미 있어야 하고, 없으면 R12를 적고 종료. 161+ 발명 금지.

---

## 2. 완료분 — 다시 하지 마

| 구간 | 기록 |
|---|---|
| 7–10회차 · 시드 12–40 | #186–#223 |
| **배치 A 41–70** | #226–#257 · Step0 |
| **G1–G5 (A 뒤)** | #258–#261 · Step0 #262 |
| **배치 B 71–100** | #266–#294 · G · Step0 |
| **배치 C 101–130** | #297–#314 · Step0 |
| **배치 D 131–160** | #316–#337 · Step0 |
| **최종 G** | #338·#339 · ACK #340 |
| main (배치 R 시작 전) | `git log -1` 로 재확인 — 숫자 기억 금지 |

---

## 3. 배치 A — 41–70 (**완료 · 아카이브**)

표는 git 이력. **다시 하지 마.**

---

## 4. 배치 B — 시드 **71–100** (**완료 · 아카이브**)

표는 git 이력. **다시 하지 마.** B가 남긴 Docker 못 봄은 **D #158** 이 한 번 기록한다. 71–75를 되풀이하지 마.

B에서 연 ack(구현 금지, 사람 손): `#82` securitySchemes · `#87` TEST6 15행 · `#95` `ci.yml permissions`.

---

## 5. 배치 C — 시드 **101–130** (**완료 · 아카이브**)

한 줄 = 한 PR. 뮤테이션 ≥2. CHANGELOG 선두 1건(코드 PR).
코드 없으면 근거 3줄 → 다음 #.

**출처:** 절대규칙 8개 재전수 + 배치 B가 연 옆자리(역할·공개 GET·OpenAPI 사본·Decision 실측 표).

### 우선순위

```text
101 → 102 → 103 → 104 → 105 → 106 → 107 → 108
→ 109 → 110 → 111 → 112 → 113
→ 114 → 115 → 116 → 117 → 118 → 119
→ 120 → 121 → 122 → 123 → 124 → 125 → 126 → 127 → 128
→ 129 → 130 → G1–G5 → 즉시 §6
```

### 표

| # | 무엇 | 왜 Decision 없는가 | 완료 모양 |
|---|---|---|---|
| **101** | Core 워커 claim 루프 — 이중 claim · `FOR UPDATE SKIP LOCKED` 재전수 | 절대규칙·pitfalls 핀 | 결함 or 0건+뮤테이션 ≥2 |
| **102** | `trust_domain` / `compute_tier_max` 스냅샷이 앱에서 덮어쓰이는 경로 0 | 절대규칙 4 | 0 or 표+핀 |
| **103** | gate-runner가 아닌 Node에서 gate 돌릴 API/스크립트 0 | 절대규칙 8 | 0 or 결함 |
| **104** | pickle / `.pt` / `.pth` 로드 **새 진입점** 재전수 | 절대규칙 5 | 0 or 결함 |
| **105** | 사전학습 URL · `torch.hub` · `from_pretrained` 문자열 전수 | 절대규칙 6 | 0 or 결함 |
| **106** | 자유 업로드 · 서명 URL · `fileToken` 문자열 재전수 (D8′) | 절대규칙 7 | 0 or 결함 |
| **107** | `tier_compatible` 우회 · `compute_tier` 문자열 비교 재전수 | 절대규칙 3 | 0 or 결함 |
| **108** | `assignment`/`gate_run` INSERT SELECT만 — ORM insert 뮤테이션 | 절대규칙 2 | 뮤테이션 ≥2 |
| **109** | 공개 GET 6 · PUBLIC · D24 · 코드 **네 곳** 일치 (STATE 숫자는 연대기 — 맞추려 고치지 마) | #192 핀 | 일치 or 드리프트 표 |
| **110** | 역할 매트릭스 admin/developer **양방향** 재전수 (#193) | 권한 핀 | 핀 |
| **111** | Node `/health` 증서·내부 필드 유출 재전수 | 시크릿 | 0건 핀 |
| **112** | capreq `--host` 기본 루프백 재전수 + compose 노출 **표** (compose 수정=사람) | #195 | 핀 or 표 |
| **113** | 입력 MIME/크기 거절이 **검사에서 실제로 도는가** | D22 옆 | 도는 검사 or 신설 |
| **114** | 출력 `required` 미선언 시 동작 — **문서화만** | 구현=`output-required-undeclared-policy` | inbox 표 1건 · **코드 0** |
| **115** | `silent-truncation` **실측 표만** — 정책 변경 금지 | Decision | inbox 표 |
| **116** | `gate_run` RUNNING 장기 방치 — **실측 기록만** | Decision | inbox 표 |
| **117** | failure reason이 API/UI에 안 가는 경로 표 | Decision | inbox 표 |
| **118** | 골든 겹침 주장 재현 명령 vs 보고서 — **표만** (원고 본문 금지) | 측정 규율 | 표 |
| **119** | changelog-changeset 규칙 — **문서 핀만** (`CLAUDE.md` 개정 금지) | Decision | 핀 |
| **120** | `docs/spec/openapi.yaml` ↔ `apps/core/openapi.yaml` 전필드 | 응답 스키마·securitySchemes = Decision 금지 | 요청/경로 드리프트 표 · yaml 고치면 **머지 대기** |
| **121** | seed SQL · 카탈로그 · 실행기 **세 장** 이름 일치 | 카탈로그 정합 | 핀 |
| **122** | `pass_rate`/`score_n300` 산출물 gitignore · 제출 zip 규칙 | 산출물 누출 | 핀 |
| **123** | `check_release.sh`가 막는 것 vs 문서 「제출물」 목록 | #238 형제 | 맞춤 or 핀 |
| **124** | 컨테이너 **non-root**·읽기전용 **주장 vs compose** (compose 수정=사람) | 운영 표 | 표 · 고치면 PR만 |
| **125** | 로그 INFO에서 PII/토큰 패턴 전수 | #196 형제 | 0 or 허용+근거 |
| **126** | 시계열/텍스트 데모 스크립트 **실패 시 초록** | 0건 초록 | 결함 or 핀 |
| **127** | `unittest` 순서에 깨지는 공유 상태 | 플레이키 | 결함 or 0 |
| **128** | 신규 `tests/test_*.py` 머리말·스킵 사유 규약 | #215 | 핀 |
| **129** | Step 0 — 열린 Decision **사실 갱신**(코드 유무) · status **내리지 마** | 코드 0 | inbox |
| **130** | Step 0 — 배치 C 소진 · **즉시 D 착수** (「C 대기」라고 쓰지 마) | 코드 0 | inbox 한 블록 → **#131** |

### 배치 C에서 하지 마

- `ci.yml` 잡/설치/`permissions:` (`round9-ci-coverage-proposal` · B #95)
- openapi **응답** 스키마 · **securitySchemes 일괄** (B #82)
- 대회 원고 본문 · TTL / `retrieve.*` / 11번째 능력
- Decision `status`를 임의로 `done`으로 내리기
- schema CHECK 약화 · 정책 숫자 변경
- 114–119를 **구현 PR**로 바꾸기
- 배치 B 71–100 되풀이 · 161+ 발명

---

## 6. 배치 D — 131–160 (**완료 · 아카이브**)

제품 Wave 없이 **유지·정직·사각 제거**만. C Step 0을 남긴 뒤 Cursor를 기다리지 말고 131부터.

### 우선순위

```text
131 → 132 → 133 → 134 → 135 → 136 → 137 → 138
→ 139 → 140 → 141 → 142 → 143
→ 144 → 145 → 146 → 147 → 148 → 149 → 150
→ 151 → 152 → 153 → 154 → 155 → 156
→ 157 → 158 → 159 → 160 → G1–G5 → 즉시 §7
```

### 표

| # | 무엇 | 왜 Decision 없는가 | 완료 모양 |
|---|---|---|---|
| **131** | 전체 `scripts/*.sh` shebang · `pipefail` · `errexit` 재전수 | 운영 핀 | 결함 or 0 |
| **132** | 전체 `*.ps1` `$ErrorActionPreference` | #206 형제 | 핀 · pwsh 없으면 정적 |
| **133** | CI 3잡 ↔ 로컬 discover **파일 집합 diff** (`ci.yml` 수정=사람) | G5 확장 | 표 · 잡 추가는 Proposal만 |
| **134** | `floors.json` 항목 수 vs 실제 검사 함수 수 | #77 형제 | 핀 |
| **135** | 뮤테이션 하네스 없는 「핀」PR 목록 → 보강 | 실측 규율 | 보강 or 0 |
| **136** | `_srcguard` 적용 파일 확대 (주석 우회) | G1 | 확대 or 0 |
| **137** | DB 세대 번호 vs `migrate` 문서 | 고정 숫자 | 일치 or 정정 |
| **138** | 통합 검사 이름 ↔ `run_integration.sh` 호출 목록 | #215 형제 | 핀 |
| **139** | README 링크·명령 **404/실패** 전수 (원고 제외) | 문서 정직 | 표 or 정정 |
| **140** | user-guide 주장 vs 실라우트 | 문서 정직 | 표 or 정정 |
| **141** | `capability-catalog` 「구현됨」↔ dispatch **재** | #27/#214 형제 | 핀 |
| **142** | Node onboard 문서 vs 스크립트 플래그 | 운영 | 표 or 정정 |
| **143** | 강제 모드 compose 키가 예시/커밋에 있는지 | 시크릿 | 0건 핀 |
| **144** | 테스트가 네트워크·실 Docker를 **몰래** 호출 | 격리 | 결함 or 0 |
| **145** | 시간대·`now()` 의존 플레이키 테스트 | 플레이키 | 결함 or 0 |
| **146** | JSON 계약 오류 메시지에 내부 경로 | 유출 | 0 or 허용+근거 |
| **147** | 대용량 입력 거절 경계값 검사 존재 | D22 옆 | 핀 or 신설 |
| **148** | 동시 lease 2개 시도 시 DB 유니크 | 스키마 약화 금지 | 있는 제약 핀 · 없으면 표만 |
| **149** | 게이트 골든 sha 고정 vs 가중치 경로 | SD-013 | 핀 |
| **150** | EuroSAT/데이터 라이선스 문구 vs 실파일 | 절대규칙 6 | 일치 or 정정 |
| **151** | SBOM 도구 버전 핀 | #239 형제 | 핀 |
| **152** | `NOTICE`/`LICENSE` 트리 누락 | 라이선스 | 표 or 한 줄 |
| **153** | 브리지 PROTOCOL 위반(Decision 없이 DDL) 정적 탐지 | 규율 | 핀 · DDL 만들지 마 |
| **154** | inbox `expects:decision` **열린 수** 기계 집계 핀 | #39/#222 | 핀 · status 내리지 마 |
| **155** | queue-batches 활성 표와 STATE 「다음」 일치 | 드리프트 | 맞춤 |
| **156** | handoff 「상태확인」S0–S7이 문서와 같은지 | 드리프트 | 맞춤 |
| **157** | 최종 제출 zip `check_release` 초록 | 출품 재현 | 명령+결과 (태그 이동 금지) |
| **158** | `clean_room`+`prod_room` Docker 세션 **한 번** 본실행 기록 | B 못 봄 청산 | 표 · 없으면 「못 봤다」 |
| **159** | Step 0 — 최종 정리 체크리스트 (사람용) | 코드 0 | inbox |
| **160** | Step 0 — **시드 종료** · 이후는 Decision·G만 · **즉시 §7** | 코드 0 | inbox → 최종 G |

### 배치 D에서 하지 마

C의 「하지 마」 전부 + 새 능력 · 새 Wave · 161+ 발명.

---

## 7. 최종 (D #160 뒤 · 시드 끝 · **완료 · 아카이브**)

시드 종료 Step 0 · ACK #340. **다시 하지 마.** 열린 Decision 구현은 사람 Confirm 후 별 세션.
배치 R 은 시드를 발명하지 않는다. G를 이유로 새 검사 파일만 양산하지 마.

---

## 8. 배치 R — 역할 실측 (R1–R12) (**활성**)

시드가 아니다. 요청자 · Core · 노드제공자 경로를 **살아 있는 스택에서** 한 번 누른다.
한 줄 = 한 PR(또는 코드 없으면 근거 3줄 → 다음 R).

### 우선순위

```text
R1 → R2 → R3 → R4
→ R5 → R6 → R7
→ R8 → R9 → R10
→ R11 → R12
```

### Docker 분기 (R1 에서 한 번만)

```bash
docker info >/dev/null 2>&1
```

- **실패:** R2–R11 마다 inbox에 「못 봤다 · docker info 실패」. 스크립트를 「됐을 것」으로 적지 마. **R12로 가서 세션 종료.**
- **성공:** 아래 표. 격리 방(`clean_room` · `prod_room`)은 운영 compose 프로젝트를 건드리지 않는다.

역할 순서: **요청자 → Core → 노드제공자.** 방을 먼저 비우고, 노드제공자(R8–R10)는 데모 Core(`:8000`)가 이미 떠 있으면 그것을 쓴다 — `down -v` 금지.

### 표

| # | 역할 | 명령 (글자 그대로) | 완료 모양 | 주장하지 마 |
|---|---|---|---|---|
| **R1** | 환경 | `docker info` · `docker compose version` | 됨/안 됨 + 이유. 안 되면 R2–R11 전부 「못 봄」표시 후 R12 | 「로컬에 있을 것」 |
| **R2** | 요청자 | `bash scripts/clean_room.sh --keep` (프로젝트 `capnet-cleanroom` · 포트 18800/18801 · 운영 스택 금지) | 통과/실패 표. 재현 명령을 PR에. `--keep` 은 R3·R4 가 같은 Core 를 쓰게 | 품질 `acc=` |
| **R3** | 요청자 | `CORE_URL=http://127.0.0.1:18800 bash scripts/product_demo.sh` — Core 공개 API만 · 기기 주소 없음 | exit 0 · 출력에 배정 증적(node·domain·tier) · `GET /v1/ops/work-units` 줄 | `text.ner` 정확도 |
| **R4** | 요청자 입구 | `CORE_URL=http://127.0.0.1:18800 bash scripts/capreq_demo.sh` | exit 0=경로 이어짐 · **2=라우팅 빗나감(배선 실패 아님)** · Ollama/capreq 없으면 「못 봄」+다음 | 라우팅 N/M 을 성적으로 |
| **R5** | Core | R2 방 정리 후 `bash scripts/prod_room.sh` (프로젝트 `capnet-prod` · 18830/18831). 스크립트는 `set -uo pipefail` (`-e` 없음 · #44). **파일의 `-e` 를 먼저 켜지 마.** 단계가 실패인데 초록이면 그게 결함 — scripts PR | 통과 N / 실패 0 을 **출력에서** 적는다 | 옛 `27/27` |
| **R6** | Core 문 | R5 로그에서 확인: 공개 GET **6** (키 없음) · 쓰기 최소몸통 **401**. 안 보이면 스크립트/프로브 결함으로 PR | 「인증은 있을 것」 | |
| **R7** | Core 거절 | 요청자가 기기 URL로 Node를 직접 치면 거절되는지 — `prod_room`/`clean_room` 이 이미 누르면 그 줄 인용. 없으면 최소 1호출 + 검사 | 직접 호출 성공을 제품으로 | |
| **R8** | 노드제공자 | 데모 Core(`CORE_URL=http://127.0.0.1:8000`)가 살아 있으면 그것을 쓴다. 없으면 `docker compose up -d` (이미 떠 있는 운영 프로젝트에 `down -v` 하지 마). `bash scripts/node_onboard.sh --name role-r8 --domain team --tier M --source team` | 증서 파일 `data/node-secrets/role-r8.credential` · 모드 0600 · 로그에 시크릿 없음 | 등급을 Node가 골랐다 |
| **R9** | 노드제공자 초대 | admin으로 `POST /v1/nodes/invites` (`trust_domain=tenant`, **team 초대는 DB 거절이 정상**) → 키 **없이** `POST /v1/nodes/redeem` + `Authorization: CapNet-Invite …` · body는 `name`·`device_type`만 (`trust_domain`/`org_id`/`tier` 칸을 넣어도 **적용되면 결함**) | 소진 1회 · 재소진 거절 · 초대한 Node는 gate-runner 불가 | 초대 본문에 등급 필드 추가 |
| **R10** | 노드제공자 사슬 | `bash scripts/node_bind.sh --node <R8 uuid> --weights apps/node/weights/eurosat_scratch.safetensors` 후 `bash scripts/call.sh ic1-0001` | Task COMPLETED · 증적에 요청자 기기 주소 없음 · 게이트는 runner Node | 제출자 Node에서 게이트 |
| **R11** | 잔여 실측 | **아직 못 본 것만.** 이미 R2/R5에 있으면 건너뜀. 후보: `bash scripts/demo_violations.sh`(제약 **이름**을 로그에 남김 · 「14종」을 15로 올리지 마) · `bash scripts/regate.sh` · `bash scripts/proof_ab.sh` · `python3 scripts/mutation_harness.py` · `python3 scripts/check_test_order.py --isolated` · 능력 `*_demo.sh` 종단은 clean_room이 안 덮는 것만 · 골든 누출은 `data/golden-*` 있을 때만 | 표: 돌림/못 봄/결함. #87 SQL 고침은 **CONSTRAINT_NAME 실측 후** 소PR. 숫자 「위반 14종」은 Proposal만 | 「전부 돌았을 것」 |
| **R12** | Step 0 | inbox-cursor 한 블록: 역할 3열 표(명령·exit·증적 한 줄) · 못 본 것 · 고친 결함 PR · **다음 시드 없음** | 코드 0 · STATE 「다음」을 역할 실측 완료로. 활성 행을 「역할 실측 완료 · Decision만」으로 | 배치 S 발명 |

R2 `--keep` 뒤 R4까지 끝나면 방이 안내한 `down -v` 로 **그 프로젝트만** 정리한 다음 R5.

### 역할별로 반드시 볼 것

**요청자**
- POST `/v1/tasks` 본문에 기기 주소·Node URL이 **없다**
- 입력은 Core 중개(`inputId`) — 빈 첨부 → 데모 데이터셋으로 몰래 성공하면 **결함**(#154 회귀)
- 조회 `GET /v1/tasks/{id}` 는 자기 것만 (남은 것은 404)

**Core**
- 워커만 claim · `FOR UPDATE SKIP LOCKED`
- 강제 모드에서 쓰기 무인증 401 (422로 인증을 건너뛴 줄은 프로브 결함)
- 공개 GET은 여섯뿐
- 키는 `ccurl` 파일 헤더. argv 금지 (#237)

**노드제공자**
- 소진/등록 본문에 `trust_domain`·`compute_tier_max`를 넣어도 **적용되지 않거나 거절**
- 큐 pull 없음
- pickle/`.pt` 로드 없음 (이미 핀 — 재발명 금지)

### 배치 R에서 하지 마

- 161+ · G를 이유로 새 검사 파일만 양산
- Decision 23개 status 일괄 `done`
- `ci.yml` 잡 추가 · `#95 permissions` · `#82` securitySchemes
- 태그 `v0.1.0-contest` 이동
- `retrieve.*` · TTL · 11번째 능력 · schema CHECK 약화
- 운영 compose 볼륨을 `down -v` 로 지우는 일
- `prod_room.sh` 의 `set -e` 를 실측 없이 켜는 일

---

## 9. 배치 전달 문구 (사람이 Claude에 줌)

### 지금 전달 — 배치 R

```text
배치 R (역할 실측) 활성화. 시드 161+ 발명 금지. 번호는 R1–R12 만.
docs/bridge/queue-batches.md §8 · autonomous-mode.md · handoff 안쪽 블록을 읽는다.
「상태확인」절차로 동기화한 뒤 우선순위대로 R1부터.
머지 묻지 마. Docker 없으면 산 항목은 「못 봤다」만 적고 R12.
Decision 구현·ci.yml 수정·status 내리기·태그 이동 금지.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

### 재시작

```text
상태확인
```

(아카이브 · 쓰지 마) C→D→최종 연속 / 배치 C만 / 배치 D만 따로 켜던 문구는 이번 전달로 대체됐다.

---

## 10. 갱신 이력

| 날짜 | 비고 |
|---|---|
| 2026-09-06 | **배치 R 활성 · 역할 실측** · 최종 아카이브 · 시드 종료 유지 |
| 2026-09-06 | **C 활성 · C→D→최종 연속** · B 아카이브 · 표 4칸 |
| 2026-09-05 | **배치 B 71–100** · C/D/최종 로드맵 · A 완료 |
| 2026-09-05 | 최초 — 배치 A · 상태확인 |
