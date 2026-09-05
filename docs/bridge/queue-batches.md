# CapNet — 큐 배치 (30개 단위)

> **이 파일이 정본인 것:** 활성 배치 · 배치별 시드 표 · 「상태확인」 · **이후→최종 로드맵**  
> **루프:** [`autonomous-mode.md`](./autonomous-mode.md)  
> **종료·G:** [`queue-expansion.md`](./queue-expansion.md)  
> **붙여넣기:** [`handoff-long-mode-claude.md`](./handoff-long-mode-claude.md)

---

## 한 줄

**활성 배치가 빌 때까지 멈추지 마. 배치가 비면 G1–G5 · Step 0 「다음 배치 대기」. 머지 묻지 마.**

---

## 0. 배치 규약

| 이름 | 번호 | 상태 |
|---|---|---|
| 배치 A | 41–70 | **완료** (#226–#262 · G1–G5) |
| **배치 B** | **71–100** | **활성** ← 지금 전달분 |
| 배치 C | 101–130 | 예약 (§5 초안 · Cursor가 활성 전환) |
| 배치 D | 131–160 | 예약 · 최종 직화 전 마지막 시드 |
| 최종 | — | Decision만 · 새 시드 번호 중단 |

규칙:

1. Cursor/사람이 **한 번에 배치 하나**만 전달한다.
2. Claude는 **활성 배치 표**만 소진한다. 다음 배치를 발명하지 않는다 (G1–G5 예외).
3. 배치 안 우선순위를 따른다. 막히면 **다음 번호**.
4. 배치 소진 + G 한 바퀴 → Step 0 `expects: ack` 「배치 X 소진」.
5. **배치 소진 ≠ 세션 종료.** 종료는 `queue-expansion.md` §2만.
6. **Docker 데몬 없으면** 본실행 항목은 「못 봤다+이유」만 적고 **다음 #** — 「됐을 것」 금지.

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
         → handoff 안쪽 → inbox 끝 100줄 → CLAUDE.md
S6. 한 줄: main=<sha> · PR=<n> · tests=<요약> · 다음=#N <제목>
S7. 즉시 #N 착수. 「계속?」 금지.
```

STATE·CHANGELOG·옛 inbox 통독 **금지**.

---

## 2. 완료분 — 다시 하지 마

| 구간 | 기록 |
|---|---|
| 7–10회차 · 시드 12–40 | #186–#223 |
| **배치 A 41–70** | #226–#257 · Step0 |
| **G1–G5 (A 뒤)** | #258–#261 · Step0 #262 |
| main (배치 B 시작) | `cfa405c` (#262) — `git log -1` 로 재확인 |

---

## 3. 배치 A — 41–70 (**완료 · 아카이브**)

표는 git 이력. **다시 하지 마.**

---

## 4. 배치 B — 시드 **71–100** (**활성** · 30줄)

한 줄 = 한 PR. 뮤테이션 ≥2. CHANGELOG 선두 1건(코드 PR).
코드 없으면 근거 3줄 → 다음 #.

**출처:** 배치 A·G가 남긴 사실(#44·#46·#63 미본실행 · `prod_room`이 `ccurl` 우회 · 쓰기 라우트 잔여) + 옆자리.

### 우선순위

```text
71 → 72 → 73 → 74 → 75
→ 76 → 77 → 78
→ 79 → 80 → 81 → 82
→ 83 → 84 → 85 → 86
→ 87 → 88 → 89 → 90
→ 91 → 92 → 93 → 94
→ 95 → 96 → 97 → 98
→ 99 → 100 → G1–G5
```

### 표

| # | 무엇 | 왜 Decision 없는가 | 완료 모양 |
|---|---|---|---|
| **71** | `prod_room.sh`에 **`-e`/`set -euo`** — #44 잔여. Docker 있으면 51/51 재측 · 없으면 정적+「못 봄」 | 운영 핀 | 결함 or 핀+재측 |
| **72** | `prod_room`이 `ccurl` 안 쓰고 **키를 아홉 번 직접** 넘기는가 (#237 형제) | 시크릿 | 결함 or `-H @파일` |
| **73** | 쓰기 라우트 **잔여 무인증 401** (#49) — 최소 몸통·파괴 없음. Docker 없으면 표만+정적 | #49 옆 | 표+핀 or 못 봄 |
| **74** | `clean_room`에 **능력 종단 데모** 아홉 (#46) — Docker 없으면 못 봄 | #46 잔여 | 보강 or 못 봄 |
| **75** | `regate.sh`·`proof_ab.sh` **본실행** (#63) 또는 못 봄 명시 | #63 잔여 | 표 |
| **76** | `hash_comment_free` **전수** — 설정을 `#`로 꺼도 통과하는 검사 잔여 (G1 옆) | G1 | 결함 or 0 |
| **77** | `floors.json` / `REFERENCE_FLOOR` **신규 바닥**이 뮤테이션 없이 들어왔는가 | #50/#230 | 핀 |
| **78** | `scripts/floor_registry.py`·`room_check_count.py` — **공허 통과** 사각 | 메타 | 뮤테이션 |
| **79** | Node/Core **Dockerfile·compose**의 `ENV`/`ARG`에 시크릿·토큰 기본값 | #196/#237 | 0건 핀 |
| **80** | HTML/`call.html`이 **fetch에 키를 쿼리로** 싣는가 | #219 옆 | 핀 |
| **81** | `Authorization` 로그·트레이스 문자열 전수 (앱·스크립트) | 시크릿 | 0 or 허용+근거 |
| **82** | `GET`이 아닌 메서드의 **OpenAPI↔핸들러** 드리프트 잔여 | #24/#213 옆 | 표 |
| **83** | `check_submission.py` 주장 숫자 vs **실측 스크립트** (27/27 류 재발) | #238 | 검사 |
| **84** | `contest-submission-checklist`·촬영 런북 **낡은 N/M** 전수 | 측정 규율 | 맞춤 or 핀 |
| **85** | `THIRD-PARTY-LICENSES` ↔ `requirements`/`pyproject` **누락 한 줄** | 라이선스 | 표 |
| **86** | SBOM 생성 — **의존성 없이 성공**하는 다른 진입점 (#239 옆) | #239 | 결함 or 0 |
| **87** | `demo_violations`·위반 시연이 **문서 주장과 같은 실패**를 내는가 | 데모 | 핀 or 못 봄 |
| **88** | `agent_capability`/`gate_run` **상태 전이**를 앱이 손으로 쓰는 UPDATE | 절대규칙 2 옆 | 0 or 표 |
| **89** | Node가 **lease 만료 뒤에도** 바이트를 읽는 경로 | SD-010 옆 | 0건 핀 |
| **90** | `input` purge가 **「지웠다」고 말만** 하는가 (#187 계열) | 0건 초록 | 결함 or 핀 |
| **91** | `quality_profile`/계약 필드 **기본값이 느슨한 쪽**인 템플릿 | #189 계열 | 표 |
| **92** | capreq 라우터가 **카탈로그에 없는 code**를 조용히 폴백하는가 | #216 옆 | 결함 or 핀 |
| **93** | `tests/integration/*` **스킵 메시지**가 `ALLOWED`와 같은 말인가 | #215/#261 | 핀 |
| **94** | `run_tests.sh`가 **새 test_*.py를 빠뜨리는** discover 구멍 | G5 옆 | 결함 or 0 |
| **95** | GitHub Actions **permissions/secrets** 가 로그에 에코되는 workflow | #217 옆 | 0건 |
| **96** | `compose*.yaml` **포트·프로젝트명**이 clean/prod 런북과 충돌하는가 | 운영 | 표 |
| **97** | Windows `.ps1`만 있는 경로가 **WSL 문서에 「돌린다」**고 적혀 있는가 | #206/#240 | 정정 or 핀 |
| **98** | `measured-claims` §7 — **신규 STATE/카탈로그 줄** 재전수 (오탐→철회 OK) | #30 | 0 or 좁힘 |
| **99** | Step 0 — 열린 Decision **status 제안 표만** (내리지 마) · #70 갱신 | 코드 0 | 표 |
| **100** | Step 0 — **배치 B 소진 보고** · 배치 C 대기 · 못 본 Docker 줄 재목록 | 코드 0 | inbox |

### 배치 B에서 하지 마

- `ci.yml` 잡/설치 추가 (`round9-ci-coverage-proposal`)
- openapi **응답** 스키마 · 대회 원고 본문 · TTL/`retrieve.*`/11번째 능력
- Decision `status`를 임의로 `done`으로 내리기
- schema CHECK 약화 · 정책 숫자 변경

---

## 5. 배치 C — 101–130 (**예약** · 초안 30줄)

배치 B Step 0 뒤 Cursor가 **활성**으로 올린다. Claude는 활성 전 발명 금지.

| # | 무엇 (한 줄) |
|---|---|
| **101** | Core 워커 claim 루프 — 이중 claim·SKIP LOCKED 재전수 |
| **102** | `trust_domain` 스냅샷이 앱에서 덮어쓰이는 경로 0 |
| **103** | gate-runner가 아닌 Node에서 gate 돌릴 API/스크립트 0 |
| **104** | pickle/`.pt` 로드 **새 진입점** 재전수 (절대규칙 5) |
| **105** | 사전학습 URL·`torch.hub`·`from_pretrained` 문자열 전수 |
| **106** | 자유 업로드·서명 URL·`fileToken` 문자열 재전수 (D8′) |
| **107** | `tier_compatible` 우회 문자열 비교 재전수 |
| **108** | `assignment` INSERT SELECT만 — ORM insert 뮤테이션 |
| **109** | 공개 GET 6 · PUBLIC · D24 · STATE **네 곳** 일치 |
| **110** | 역할 매트릭스 admin/developer **양방향** 재전수 (#193) |
| **111** | Node `/health` 증서·내부 필드 유출 재전수 |
| **112** | capreq `--host` 기본 루프백 재전수 + compose 노출 표 |
| **113** | 입력 MIME/크기 거절이 **검사에서 실제로 도는가** |
| **114** | 출력 `required` 미선언 시 동작 — **문서화만**(구현=Decision) |
| **115** | `silent-truncation` 실측 표만 — 정책 변경 금지 |
| **116** | `gate_run` RUNNING 장기 방치 — **실측 기록만**(구현=Decision) |
| **117** | failure reason이 API/UI에 안 가는 경로 표 (구현=Decision) |
| **118** | 골든 겹침 주장 재현 명령 vs 보고서 — 표만 |
| **119** | changelog-changeset 규칙 — **문서 핀만** |
| **120** | `docs/spec/openapi.yaml` ↔ `apps/core/openapi.yaml` 전필드 |
| **121** | seed SQL·카탈로그·실행기 **세 장** 이름 일치 |
| **122** | `pass_rate`/`score_n300` 산출물 gitignore·제출 zip 규칙 |
| **123** | `check_release.sh`가 막는 것 vs 문서 「제출물」 목록 |
| **124** | 컨테이너 **non-root**·읽기전용 주장 vs compose |
| **125** | 로그 INFO에서 PII/토큰 패턴 전수 |
| **126** | 시계열/텍스트 데모 스크립트 **실패 시 초록** |
| **127** | `unittest` 순서에 깨지는 공유 상태 |
| **128** | 신규 `tests/test_*.py` 머리말·스킵 사유 규약 |
| **129** | Step 0 — Decision 열넷 **사실 갱신**(코드 유무) |
| **130** | Step 0 — 배치 C 소진 · 배치 D 대기 |

---

## 6. 배치 D — 131–160 (**예약** · 최종 시드)

제품 Wave 없이 **유지·정직·사각 제거**만. 끝나면 G 후 **최종**.

| # | 무엇 (한 줄) |
|---|---|
| **131** | 전체 `scripts/*.sh` shebang·`pipefail`·`errexit` 재전수 |
| **132** | 전체 `*.ps1` `$ErrorActionPreference` |
| **133** | CI 3잡 ↔ 로컬 discover **파일 집합 diff** |
| **134** | `floors.json` 항목 수 vs 실제 검사 함수 수 |
| **135** | 뮤테이션 하네스 없는 「핀」PR 목록 → 보강 |
| **136** | `_srcguard` 적용 파일 확대 (주석 우회) |
| **137** | DB 세대 번호 vs `migrate` 문서 |
| **138** | 통합 검사 이름 ↔ `run_integration.sh` 호출 목록 |
| **139** | README 링크·명령 **404/실패** 전수 (원고 제외) |
| **140** | user-guide 주장 vs 실라우트 |
| **141** | `capability-catalog` 「구현됨」↔ dispatch **재** |
| **142** | Node onboard 문서 vs 스크립트 플래그 |
| **143** | 강제 모드 compose 키가 예시/커밋에 있는지 |
| **144** | 테스트가 네트워크·실 Docker를 **몰래** 호출 |
| **145** | 시간대·`now()` 의존 플레이키 테스트 |
| **146** | JSON 계약 오류 메시지에 내부 경로 |
| **147** | 대용량 입력 거절 경계값 검사 존재 |
| **148** | 동시 lease 2개 시도 시 DB 유니크 |
| **149** | 게이트 골든 sha 고정 vs 가중치 경로 |
| **150** | EuroSAT/데이터 라이선스 문구 vs 실파일 |
| **151** | SBOM 도구 버전 핀 |
| **152** | `NOTICE`/`LICENSE` 트리 누락 |
| **153** | 브리지 PROTOCOL 위반(Decision 없이 DDL) 정적 탐지 |
| **154** | inbox `expects:decision` **열린 수** 기계 집계 핀 |
| **155** | queue-batches 활성 표와 STATE 「다음」 일치 |
| **156** | handoff 「상태확인」S0–S7이 문서와 같은지 |
| **157** | 최종 제출 zip `check_release` 초록 |
| **158** | `clean_room`+`prod_room` Docker 세션 **한 번** 본실행 기록 |
| **159** | Step 0 — 최종 정리 체크리스트 (사람용) |
| **160** | Step 0 — **시드 종료** · 이후는 Decision·G만 |

---

## 7. 최종 (시드 끝 이후)

1. **새 번호 시드 발명 중단.** G1–G5만 (같은 파일 3회 반복 시 중단 신호).
2. **Decision만** Cursor/master — 구현은 Confirm 후 별 PR.
3. 사람 Decision 우선: `round9-ci-coverage-proposal` · `silent-truncation` · `gate-run-stuck-running` · `failure-reason-not-surfaced` · `retention-ttl-policy` · `output-required-undeclared-policy` · `openapi-response-schemas` · `contest-report-device-address-claim` · `11th-capability` · 나머지.
4. 코드 이미 나간 여섯(`#70` 표) — status는 **사람 손**.

---

## 8. 배치 전달 문구 (사람이 Claude에 줌)

### 배치 B · 지금 전달

```text
배치 B (71–100) 활성화. docs/bridge/queue-batches.md §4 · autonomous-mode.md · handoff 안쪽 블록을 읽는다.
「상태확인」절차로 동기화한 뒤 우선순위대로 71부터. 배치가 빌 때까지 멈추지 마. 머지 묻지 마.
Docker 없으면 본실행은 「못 봤다」만 적고 다음 번호. Decision 구현·ci.yml 수정 금지.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

### 재시작

```text
상태확인
```

### 배치 C 활성화 (B 소진 뒤)

```text
배치 C (101–130) 활성화. queue-batches.md §5를 읽고 상태확인 후 101부터. 멈추지 마. 머지 묻지 마.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

### 배치 D 활성화

```text
배치 D (131–160) 활성화. queue-batches.md §6을 읽고 상태확인 후 131부터. 멈추지 마.
최종 직전 시드다. Decision 구현 금지.
cd ~/pjt/ai-agent-store && git fetch origin main && git checkout main && git pull
```

---

## 9. 갱신 이력

| 날짜 | 비고 |
|---|---|
| 2026-09-05 | **배치 B 71–100** · C/D/최종 로드맵 · A 완료 |
| 2026-09-05 | 최초 — 배치 A · 상태확인 |
