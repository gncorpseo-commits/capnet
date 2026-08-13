# STATE — 현재 작업 상태

> **갱신: 2026-08-12** · 종착점 = **Phase 3+ 전체** (D16) · 제품 유통 = **D19** · README는 상태 비보유(링크만)

---

## 대회 정보

팀명 **지엔** · 접수번호 **915**  
일정·제출 정본: [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md)

---

## 지금 어디인가

**서사 전환 완료 (기획서 v4.7) · 사이클 폐쇄 완료.** 촬영 8/23.

> **제품 주장이 바뀌었다.** 「채점 가능한 계약」 → **「능력만 요구 · 승인 도메인 안 라우팅 · 실행 증적」** (D18)
> 근거는 실패가 아니라 기획서 §1 원래 취지다. 골든셋 게이트는 **선택적 품질 프로파일**로 내려갔고,
> 그래서 골든셋의 세 구멍(표본·분포·게이밍)이 계약 핵심에서 부속 기능의 한계가 됐다.

**오늘 코드로 닫은 것 — 사이클**

| | 이전 | 지금 |
|---|---|---|
| 스케줄링 | 클라이언트가 `claim` 호출 | **Core 워커가 배정** |
| 실행 | 클라이언트가 기기 직접 호출 | **기기가 자기 배정을 가져감** (outbound·NAT) |
| 무단 호출 | 누구나 가능했음 | **HTTP 403** (실측) |
| 사용자 | 기기 주소를 알아야 했음 | **Core만 안다** |

**보장 / 불보장**

| 보장 | 승인 도메인 밖 라우팅 안 됨 (FK) · 실행 증적이 남고 조회됨 |
|---|---|
| **불보장** | 기기가 데이터를 안 남김 (TEE 없이 원리적 불가) · 두 에이전트가 같은 답 |

| 트랙 | 상태 |
|------|------|
| **출품 (1순위)** | 양식 이식 ✅ · **촬영 2026-08-23 확정** · 편집·업로드 8/24 · Release/포털 미완 |
| **Phase 1** | ✅ 완주 · 판정 **Go** (v4.6) |
| **Phase 2** | 사이클 폐쇄 완료. 유휴 판정은 스키마 필요 → SD-007 **해소** |
| **제품 유통 (D19)** | 문서 정본 [`product-distribution.md`](docs/design/product-distribution.md). 1호 = 초대 team/tenant · 경제 비기초. **코드 유통 세대 = v제품-0 직전** |
| **마이그레이션 (SD-007)** | ✅ 러너·`migrations/`·원장. **실 볼륨 0001–0003 적용 완료 (2026-08-10)** → [`guide/migrations.md`](docs/guide/migrations.md) |
| **최소 UI (P2-3)** | ✅ `/ui/nodes.html` 등록·증서 · `/ui/call.html` 능력 호출·증적 · 새 의존성 0 |
| **운영화 (v제품-1)** | ✅ `node_onboard` → `node_bind` → `call` 3단계 · Node 런타임이 증서 전송 · 강제 모드 실측 → [`guide/operate-node.md`](docs/guide/operate-node.md) |
| **성능 (SD-017)** | ✅ 커넥션 풀 — API 15ms→**3.8ms** · 100건 부하 5.4/s→**12.4/s** · 포화 해소 |
| **관리 API 인증** | ✅ `api_key`+역할(user<developer<admin) · 쓰기 11개 보호 · **SD-010 해소** · 강제는 플래그 |
| **Node 신원 (P2-4)** | ✅ `0007` `node_credential` — v4.4 동결 이후 첫 스키마 변경(추가만) · 사칭 403 실측 · 강제는 플래그(기본 꺼짐) |
| **tenant 운용 (P2-1)** | ✅ `0006` — tenant 플릿 Node + `image.classify@2`(min=tenant) · 경계 6종 실측 · **claim 버그 SD-016 발견·수정** |
| **증적 정합 (SD-013)** | ✅ 골든셋 sha `c21d9ef7…` 통일 · **재게이트 29건 완료** · 라우팅 드리프트 31 → **1건**(`seed-agent` placeholder) |
| **B0 증적 절반 복구 (2026-08-12)** | ✅ task 가 **요청자**(`_actor()` — seed admin 하드코딩 제거)와 **요청 신뢰 도메인**(하드코딩 `'team'` 제거)을 기록. 호환은 복합 FK `domain_min_compatible` 가 판정. 실증 11/11 → D23. **tenant 유통이 구조적으로 가능해짐** |
| **촬영 리허설 (2026-08-14)** | ✅ **D-9 에 런북 타임라인 1회 완주.** `demo.sh` `acc=0.8500` · sanity 3종 FAILED · 위반 **6종 REJECTED** · `proof_ab` A/B 완결 · 증적 출력 · `migrate status` 세대 16 · `check_submission` **20/20**. **촬영일 사고 하나를 미리 잡음** — `demo.ps1`·`smoke_w1.ps1` 이 `arch` 없이 등록해 HTTP 400 (G5 회귀). 촬영은 PowerShell 인데 검증 3종은 `.sh` 만 만져 안 걸리던 구멍. `test_agent_arch_wiring` 으로 고정 |
| **G2 초대 경로 (2026-08-14)** | ✅ **관리 키 없이 함대에 들어온다.** `0016` `node_invite`(추가만) — **등급은 초대장에 박힌다**(소진 본문에 등급 필드 없음 · 절대규칙 4). `team` 초대는 발행 단계에서 거절 · 초대 기기는 채점자 불가(`ck_gate_runner_team`). 만료 7일 · 1회용 · 폐기 · audit, **소진 판정은 DB 조건부 UPDATE**. `check_node_invite` **20/20** · `check_enforcement` 20→**23** · `prod_room` 16→**20**. **수용 게이트가 옛 이미지로 마이그레이션하던 구멍**도 닫음(§3 앞 `dc build`) |
| **G4·G5 (2026-08-14)** | ✅ **안전 사슬 노란 칸 둘 닫힘.** G5 — `POST /v1/agents` 가 `arch` 를 요구(400). 분기는 `_require` **뒤**(앞이면 무인증이 401 대신 422). 등록 스크립트 4개가 학습 기록에서 arch 를 싣는다. **실측: `arch_unbound_routable` 1 → 0**. G4 — 증서 회전 런북(`operate-node.md` §2) · **무중단 불가를 그대로 적음**(활성 증서 1개 제약). **돌려 보고 한 줄 고침** — 멈춘 직후에도 `is_fresh=true`(heartbeat 45초). `check_agent_arch` 9→**13종** |
| **S2 안전 자세 조회면 (2026-08-14)** | ✅ **「누가 내 데이터를 돌릴 수 있나」를 한 면에서 답한다** (G3 닫힘). `GET /v1/ops/safety` — 기기 단위 등급·조달·증서·생사·`accepts_task_domains`·`routable_pairs`·위험 표시 · `by_task_domain` 요약. **읽기전용 · DDL 0 · 새 의존성 0 · 시크릿 없음**(prefix 만). `routable_pairs` 는 `CLAIM_SQL` 후보 조건 그대로 — `check_ops_safety` **21/21** 이 「조회면이 가능이라 한 곳에서 claim 이 실제 배정 · 불가라 한 곳은 claim 도 거절」을 고정. 강제 꺼짐이면 `ok=false`. 통합 8→**9종** · `prod_room` 14→**16종** |
| **절대규칙 7 개정 (2026-08-14)** | ✅ D8′ 정합 — 금지는 「자유 업로드」가 아니라 **비통제 수집**(서명 URL·fileToken). Core 중개 + 계약·해시·크기·MIME·보존은 허용, allowlist 는 **보조**. 규칙서만 결정을 못 따라오고 있었다 (PR #57) |
| **S1 강제 불변식 CI (2026-08-13)** | ✅ **안전 회귀를 CI 가 잡는다.** `check_enforcement` 20종 — 앱 강제 분기 직접 검사(HTTP 서버·새 의존성 0 · `importlib.reload` 로 켜짐/꺼짐 양쪽). **꺼져 있어도 잘못된 키·사칭은 401/403** 을 고정. **변이 검사로 가드 확인** (강제 우회 주입 시 20/20→17/20). 통합 7→8종 |
| **배정 재시도 상한 (2026-08-13)** | ✅ **조용한 무한 재시도 종결.** `claim` 이 `attempt_no` 계수 · `capability.max_attempts`(기본 5) 도달 시 워커가 task `FAILED` · Node 가 `/fail` 로 보고해 `audit_log` 에 이유 기록 · DB 가 상한 초과 배정 거절. **실측: 3회에서 정지, 20초 뒤에도 추가 배정 0** · 골든 `acc=0.8500` 불변 |
| **lease 가 전처리를 나른다 (2026-08-13)** | ✅ **검증과 실행이 같아짐.** `arch`·`max_params` 자리에 전처리도 적재 · 수동 실행 경로(`/v1/execute`)가 배정 행을 버리던 I1 구멍도 닫음. **판별 실측** — 선언만 16×16 L 로 되돌리자 task 가 `ASSIGNED` 에 머물고 채널 불일치 38건 (기본값이면 조용히 성공했을 것). 골든 `acc=0.8500` 불변 |
| **B2 잔여 — preprocess (2026-08-13)** | ✅ `input_schema.preprocess` 선언 자리 신설(`0014`) · 러너가 **선언을 적용해** 검증 · **`CONTRACT_CHECKS` 5 복귀** · 미선언 능력은 계약 게이트 거절. **골든 정확도 `acc=0.8500` 불변** 실측. 실증 16/16 · CI 가드 21/21. 남은 것: 일반 실행은 아직 기본값(lease 가 전처리를 안 나름) |
| **B2 계약 검증 실수행 (2026-08-13)** | ✅ 러너가 `arch`(가중치 로드)·`max_params`(파라미터 수)·`input_schema`(샘플 실추론)·`output_schema`(출력 검증)를 **실행해서** 판정. 샘플=`task_input`(복합 FK) · 샘플 없는 계약 게이트런은 DB 가 거절 · 샘플은 GC 제외 · `preprocess` 는 다음. **arch 틀린 Agent 가 FAILED 로 걸림** 실증 13/13 · CI 가드 18/18 |
| **B1 핫픽스 (2026-08-13)** | ✅ #47 리뷰 반영 — MIME **미선언이면 업로드 400**(`0012` 가 `image.classify` 에 `["image/jpeg"]` 선언) · 업로드 **디스크 스트리밍**(200MB 업로드에 core 상주 메모리 증가 **0MB** 실측 → `mem_limit` 불필요). `max_input_bytes` 불변은 accept(코드 변경 없음). 실증 10/10 |
| **B1 런타임 (2026-08-13)** | ✅ **Core→Node 바이트 전송 완성.** `POST /v1/inputs`(raw body 스트리밍·새 의존성 0) · Node 가 lease 확인 후 받아 **해시 대조** 후 추론·실행 후 삭제 · GC 워커(72h TIMEOUT·종결 후 7일·고아 24h). 별도 볼륨 `capnet_inputs`. 실증 14/14 — **골든셋 40장 밖의 데이터가 처음 흐름** |
| **B1 DDL (2026-08-12)** | ✅ `0011` `task_input` — 크기 계약(32MiB 기본·256MiB 상한) · 보존(종결 후 7일·고아 24h·미완료 72h) · `task.finished_at` · `task_input_purge_due` 뷰. **입력이 수집 시점에 능력에 묶인다**(복합 FK) · 크기는 DB 가 거절. 실증 15/15. **런타임 미착수** — 업로드 API·바이트 저장소·lease 전달·GC 워커 |
| **입력 경로 결정 (2026-08-12)** | ✅ **D22 = Core 중개(2안)** · 서명 URL(1안) 기각 · 데이터셋 등록제(3안) 보조 · **D8′** = 「자유 업로드 금지」→「비통제 수집 금지」. **B1 미착수** — Core→Node 바이트 전송은 아직 없다 (Node 가 `caseId` 로 로컬 골든을 고른다) |
| **② 게이트 선택화 (2026-08-12)** | ✅ **완료 (DDL + 런타임)** — `0010` 품질 프로파일(센티널 CHECK · `gate_run.kind` · 복합 FK) · `POST /v1/capabilities` 가 센티널을 Core 가 채움 · 계약 게이트런(`kind` 는 **능력이 결정**, `contract_checks` 5종 요구). **제약 약화 0 · `claim.py` 무수정.** 실증 DDL 10/10 · API 7/7 · 계약 10/10 · CI 가드 `check_quality_profile` 16/16 → D20. 남은 것: 계약 검증을 **러너가 실제로 수행**(지금은 보고를 받아 적는다) |
| **P1 정문 (2026-08-12)** | ✅ **목표가 제품으로 전환됨.** `compose.prod.yaml` — 인증·증서 강제, postgres 비공개, migrate 수동, `.env` 필수, seed Node `profiles: demo`. 운영 스크립트 7개에 `ccurl` 키 주입. 제품 수용 게이트 `scripts/prod_room.sh` **14/14** · 데모 `clean_room.sh` 9/9 유지 → [`operate-production.md`](docs/guide/operate-production.md) |
| **라이선스 산출물 (2026-08-12)** | ✅ `sbom.json` 에 `psycopg-pool`(LGPL-3.0) 누락 · torch 무버전 → 해소. Dockerfile `ARG` 가 버전 정본 · SBOM 11개 · 붙임1 11행. **`sbom.json` 드리프트 기계 검사는 아직 없음** |
| **새 볼륨 재현 (2026-08-12)** | ✅ README 경로가 `demo.sh` 에서 깨져 있었다 — initdb 는 `schema.sql`(08-03)까지만 넣는데 `0007`–`0009`(08-11)를 적용하는 단계가 없었다. compose 일회성 `migrate` 서비스로 해소 · `CAPNET_AUTO_MIGRATE=0` 으로 끈다 |
| **문서 위생** | README stable-only · 일정 정본 = checklist |
| **역할** | finn · toma · **pl**(동급) · master(merge) — [`github-team-guide`](docs/guide/github-team-guide.md) v1.3 |

### Phase 1 §7.1 좌표 (2026-08-08 실측)

| # | 증명 대상 | 상태 |
|---|-----------|------|
| 1 | `image.classify@1` + 골든셋 | ✅ |
| 2 | Agent **A, B** PASSED | ✅ 사슬 위 실측 (`dummy=false`) |
| 3 | 증명 모드 A/B 교체 할당 | ✅ `honored=true` · assignment 2건 SUCCEEDED |
| 4 | (v4.6) 하한 예측 | ✅ 반증 안 됨 — 통과자 6/6 유지, 최소 0.5 SE |
| 5 | Product Track Agent 선택 없음 | ✅ |

실측 — **홀드아웃 n=300** (2026-08-09, 유효):

| 후보 | 5ep | 10ep | 20ep | 40ep | 80ep |
|------|-----|------|------|------|------|
| TinyEuroSAT | 0.660 ✗ | — | 0.737 | 0.860 | **0.910** |
| TinyEuroSATB | 0.710 | **0.813** | 0.707 | **0.447** ✗ | — |

| 항목 | 결과 |
|------|------|
| 통과율 | **6/8 = 75.0%** — 밴드 안 |
| A/B 편차 (최선 ho80 vs hob10) | **0.0967** · 일치율 0.833 → EXCEEDS |
| A/B 편차 (원래 쌍 ho80 vs hob40) | 0.4633 · 일치율 0.450 → EXCEEDS |
| sanity floor 3종 | 전부 FAILED |
| M25 위반 6종 | 전부 REJECTED |
| 골든셋 누출 | 홀드아웃 n300 **0/300** · 데모 N=40도 holdout 재추출(2026-08-10). **커밋 A는 전수 학습** — 일반화 주장은 재학습 후 |

### 촬영 전 준비 (2026-08-09 완료)

| # | 항목 | 상태 |
|---|------|------|
| ① | **깨끗한 환경 재현** — `scripts/clean_room.sh` · 빈 볼륨 **9/9 통과** (2026-08-11 · 세대 8 기준 재검증) | ✅ |
| ② | `user-guide-ko.md` 새 서사(접수처·장부) | ✅ |
| ③ | README Linux 명령·403 재현·liveness | ✅ |
| ④ | 보고서 PDF·docx | ❌ 촬영 후 |
| ⑤ | 터미널 캡처 | ❌ 촬영 중 |
| ⑥ | Release 태그·zip | ❌ 8/25–26 |

## 체크리스트

6. [ ] 양식·영상·포털 ← **지금 여기**
13. [x] A/B n300 Within · 사슬 위 교체 할당
14. [x] Phase 1 판정 리포트 → **보류(HOLD)**
15. [x] P1-5 완료 — H1~H4. 판정 = **Go 아님**
16. [x] SD-009 계약 재정의 — **C안 채택** (v4.6, 등가성 → 관측값)
17. [x] SD-007 마이그레이션 체계 — 러너·원장·정적 검사. #27 머지 · **실 볼륨 0001–0003 적용 완료**
18. [x] SD-013 골든셋 sha — 선언부 **5곳** 통일 + `check_golden_sha.py`. **재게이트 29건 완료** · `seed-agent` 1건만 남음

## 연구·형제 제품 (대회 Must 밖)

| 항목 | 상태 |
|------|------|
| TeachMe Agent 기획서 | v0.1 · [`docs/research/teachme-plan.md`](docs/research/teachme-plan.md) |

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 0 | **촬영 8/23** — 영상이 보고서를 막는다 (YouTube URL이 양식 필수 칸) | **확정** |
| 1 | 중복수혜 팀 확인 | 제출 전 |
| 2 | **H1–H4를 8/27 전에 할지** (CPU 3–4h · 출품 트랙과 경합) | master |
| 3 | A/B를 보고서 Must로 승격할지 (SD-001) | master |
| 4 | ~~마이그레이션 체계 (SD-007)~~ | ✅ #27 머지 · **실 볼륨 0001–0003 적용 완료** |
| 5 | ~~실험 가중치 `.meta.json` gitignore~~ | ✅ `*.meta.json` ignore · A/B 메타만 예외 |
| 6 | 커밋 A 가중치 `HOLDOUT=1` 재학습 (meta `train_images=27000`) | 출품 전 권장 |
| 7 | 제품 유통 v제품-1 — SD-007 ✅ → **P2-1(tenant 운용) 다음** → credential (D19) | 출품 후 |
| 8 | ~~SD-013 재게이트~~ | ✅ 29건 완료. `seed-agent` 1건도 **SD-015 로 해소** — 시드가 얻을 수 없는 증서를 발급한 결함이었다 |
| 9 | ~~P2-1 tenant 운용~~ · ~~P2-4 node_credential~~ | ✅ 둘 다 완료. 유통 v제품-1 남은 것은 **lease/재할당 운영화 · 기본 모니터링** |
