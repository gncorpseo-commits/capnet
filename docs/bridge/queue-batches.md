# CapNet — 큐 배치 (30개 단위)

> **이 파일이 정본인 것:** 활성 배치 · 배치별 시드 표 · 「상태확인」 · **C→D→최종 연속 로드맵**  
> **루프:** [`autonomous-mode.md`](./autonomous-mode.md)  
> **종료·G:** [`queue-expansion.md`](./queue-expansion.md)  
> **붙여넣기:** [`handoff-long-mode-claude.md`](./handoff-long-mode-claude.md)

---

## 한 줄

**C가 빌 때까지 멈추지 마. 비면 G → Step 0 → 즉시 D. D가 비면 G → Step 0 → 최종 G 한 바퀴 → 시드 종료. 머지 묻지 마. Cursor 재전달을 기다리지 마.**

---

## 0. 배치 규약

| 이름 | 번호 | 상태 |
|---|---|---|
| 배치 A | 41–70 | **완료** (#226–#262 · G1–G5) |
| 배치 B | 71–100 | **완료** (#266–#294 · G · Step 0) |
| 배치 C | 101–130 | **완료** (#297–#314 · Step 0) |
| **배치 D** | **131–160** | **활성 — 지금 여기** (§6) |
| 최종 | — | **D Step 0 뒤 진입** · 새 시드 번호 중단 · G 한 바퀴 후 종료 (§7) |

규칙:

1. **이번 전달 = C→D→최종 연속.** 배치를 하나씩 켜 주기를 기다리지 않는다.
2. Claude는 **현재 표**만 소진한다. 161+ 와 표 밖 시드를 발명하지 않는다 (G1–G5 예외).
3. 배치 안 우선순위를 따른다. 막히면 **다음 번호**.
4. 배치 소진 + G 한 바퀴 → 그 배치 Step 0 → **다음 행을 즉시 활성** (C→D, D→최종).
5. **배치 소진 ≠ 세션 종료.** 종료는 `queue-expansion.md` §2 · 이 파일 §7 끝.
6. **Docker 데몬 없으면** 본실행 항목은 「못 봤다+이유」만 적고 **다음 #** — 「됐을 것」 금지.
7. 런타임·DDL·`compose`·`ci.yml` 수정이 필요하면 **PR만** (또는 표만) 남기고 다음 #. 묻지 마.

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
S6. 한 줄: main=<sha> · PR=<n> · tests=<요약> · 다음=#N <제목>
S7. 즉시 #N 착수. 「계속?」 금지.
```

STATE·CHANGELOG·옛 inbox 통독 **금지**.

다음 # 고르기: 미완료인 **가장 앞 번호**. C가 비었으면 D 131. D가 비었으면 최종 G.

---

## 2. 완료분 — 다시 하지 마

| 구간 | 기록 |
|---|---|
| 7–10회차 · 시드 12–40 | #186–#223 |
| **배치 A 41–70** | #226–#257 · Step0 |
| **G1–G5 (A 뒤)** | #258–#261 · Step0 #262 |
| **배치 B 71–100** | #266–#294 · G · Step0 |
| **배치 C 101–130** | #297–#314 · Step0 |
| main (배치 C 시작 전) | `git log -1` 로 재확인 — 숫자 기억 금지 |

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

## 6. 배치 D — 131–160 (**활성**)

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

## 7. 최종 (D #160 뒤 · 시드 끝)

Cursor를 기다리지 말고 들어간다.

1. **새 번호 시드 발명 중단.** G1–G5 **한 바퀴만** (같은 파일 3회 반복 시 그 G는 접고 다음 G. 다섯이 다 접히면 중단 신호).
2. **Decision 구현 금지.** 열린 것은 표로만 모아 Step 0에 붙인다. 구현은 Confirm 후 별 세션.
3. 사람 Decision 우선(구현하지 마, 목록만): `round9-ci-coverage-proposal` · `silent-truncation` · `gate-run-stuck-running` · `failure-reason-not-surfaced` · `retention-ttl-policy` · `output-required-undeclared-policy` · `openapi-response-schemas` · `contest-report-device-address-claim` · `11th-capability` · B #82/#87/#95 ack · 나머지.
4. 코드 이미 나간 여섯(`#70` 표) — status는 **사람 손**.
5. G 한 바퀴 + 「시드 종료 · Decision만 남음」 Step 0 을 `inbox-cursor.md`에 남기면 **세션을 끝내도 된다.**

이게 `queue-expansion.md` §2 조건 1이 충족되는 순간이다.

---

## 8. 배치 전달 문구 (사람이 Claude에 줌)

### 지금 전달 — C→D→최종 연속

```text
최종까지 연속 활성화 (C 101–130 → D 131–160 → 최종 G). Cursor 재전달을 기다리지 마.
docs/bridge/queue-batches.md §5·§6·§7 · autonomous-mode.md · handoff 안쪽 블록을 읽는다.
「상태확인」절차로 동기화한 뒤 우선순위대로 101부터. 배치가 비면 G 한 바퀴 후 다음 예약 배치로 즉시.
머지 묻지 마. Docker 없으면 본실행은 「못 봤다」만 적고 다음 번호.
Decision 구현·ci.yml 수정·status 내리기 금지. 114–119는 표·문서만.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

### 재시작

```text
상태확인
```

(아카이브 · 쓰지 마) 배치 C만 / 배치 D만 따로 켜던 문구는 이번 전달로 대체됐다.

---

## 9. 갱신 이력

| 날짜 | 비고 |
|---|---|
| 2026-09-06 | **C 활성 · C→D→최종 연속** · B 아카이브 · 표 4칸 |
| 2026-09-05 | **배치 B 71–100** · C/D/최종 로드맵 · A 완료 |
| 2026-09-05 | 최초 — 배치 A · 상태확인 |
