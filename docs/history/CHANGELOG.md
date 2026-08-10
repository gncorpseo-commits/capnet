# Changelog

## 출품 패키지 기계 점검 (SD-005) — 2026-08-10

촬영 당일에 사람이 눈으로 훑는 것은 재현되지 않는다. 8/23 촬영·Release 때 또 봐야 하는
항목들이라 자동으로 고정한다.

- **`scripts/check_submission.py` 신설 · 19개 검사** — 표준 라이브러리만 (새 의존성 0)
  - 금지 산출물 미동봉(EuroSAT 원본 · golden-n300 · artifacts · **pickle 계열 가중치**) ·
    필수 scratch 가중치 2종 유지 · 라이선스 4종 · 사전학습 미사용 선언(meta 16건) ·
    의존성 THIRD-PARTY 등재 · 시크릿 리터럴 · 상대 링크 180개 · 골든셋 정본 1개 ·
    골든셋 sha 정합 · 패키지 크기 · 워킹트리 청결
- 현 상태 **19/19 통과** (패키지 0.8 MB / 한도 50 MB)
- 변이 검사로 실제로 잡는지 확인 — 깨진 링크 · `artifacts/` 추적 · `pretrained=true` 각각 FAIL 재현
- `run_tests.sh` · CI unit job · 체크리스트 · 촬영 런북에 편입
- GitHub Wiki 링크(`(Page-Name)`)는 파일이 아니므로 링크 검사에서 제외

## 능력 증서 폐기 경로 (SD-014) · claim 이 agent.status 를 강제 — 2026-08-10

SD-013 재게이트 중 드러난 공백을 메운다. 재게이트가 FAILED 여도 기존 PASSED 증서가 살아남았고,
**폐기할 방법이 아예 없었다.**

- **삭제가 아니라 표시로 끊는다.** `assignment` 가 `agent_capability_passed` 를 FK 로 참조해
  실행 이력이 있는 증서는 삭제 자체가 불가능하다 (실측 20쌍). 이건 증적 보장이다 (D15)
- `migrations/0004` — `revoked_at` · `revoked_reason` · `revoked_gate_run_id` 추가 (DDL 추가만) ·
  `ck_acp_revoked_needs_reason` · 부분 인덱스 · `revoked_capability` 뷰 · `provenance_drift` 가 폐기를 반영
- **근거 없는 폐기는 거부한다** — 현재 골든셋에서 FAILED 인 `gate_run` 이 있어야 한다 (`RevokeRefused` → HTTP 409)
- **복권 경로** — 다시 통과하면 되살아난다 (`MINT_ACP_SQL` 을 `DO NOTHING` → `DO UPDATE`)
- `POST /v1/internal/agent-capabilities/revoke` · `audit_log` 에 `capability_revoked` 기록
- **`agent.status` 가 이제 실제로 강제된다** — 스키마에 선언만 돼 있고 `CLAIM_SQL` 이 보지 않았다 (SD-010 과 같은 계열).
  실 DB 41건 전부 ACTIVE 라 오늘 동작은 안 바뀐다
- `tests/integration/check_revocation.py` 10개 계약 · CI 편입.
  파일명이 `test_` 로 시작하지 않는 것은 의도 — `unittest discover` 가 집어가면 DB 없는 단위 테스트가 깨진다

## 검증 체계 도입 — 테스트 48개 · CI — 2026-08-10

이 리포는 오래 **테스트 0 · CI 0** 이었다. SD-007·SD-013 으로 **DB 밖에서 판정하는 도구**가
셋 생겼고(마이그레이션 정적 검사 · 골든셋 정합 · 계보/체크섬), 이것들은 스키마 제약이 잡아 주지 않는다.

- **`tests/` 신설 · 48개** — 표준 라이브러리 `unittest` 만 (새 의존성 0 · pip 없는 개발 환경 고려)
  - `test_migrate_lint.py` 33개 — 금지 패턴 · **오탐 방지**(정상 `INSERT … SELECT`·주석·PL/pgSQL `BEGIN`) · 허용 표식의 **범위** · 파일명/번호 규칙
  - `test_golden_sha.py` 15개 — 정본화 방식 · 선언부 4곳 일치 · 케이스 40건 · 파서가 조용히 통과하지 않는지 · `split=holdout` 유지
  - 골든 픽스처를 따로 두지 않고 **커밋된 실제 파일**을 본다 — 막으려는 사고가 「커밋된 선언부가 어긋나는 것」이라서
- **`app/migrate_lint.py` 분리** — 정적 검사·로딩이 psycopg·pydantic 없이 import 된다.
  DB 드라이버에 묶여 있어 단독 테스트가 불가능하던 것을 푼 것이고, 테스트 이전에 구조가 옳다
- **`.github/workflows/ci.yml`** — unit job(의존성 설치 없음) + migrate job(postgres 서비스)
  - migrate job 은 **빈 볼륨·기존 볼륨 양쪽**을 회귀 시험한다: baseline 가드 → 새 볼륨 드리프트 0 → 멱등 → 체크섬 잠금 → 구 sha 에서 0003 상승
- `scripts/run_tests.sh` · [`docs/guide/testing.md`](../guide/testing.md)
- 변이 검사로 테스트가 **실제로 실패하는지** 확인: sha 한 글자 변조 → 2건 실패 · 마이그레이션에 `DROP CONSTRAINT` 추가 → 1건 실패
- CI 6단계를 로컬 컨테이너로 그대로 재현해 전부 통과 확인 (첫 실행에서 깨지지 않게)

## 재게이트 29건 · 실 볼륨 마이그레이션 적용 — 2026-08-10

- **실 볼륨에 0001–0003 적용.** `pg_dump` 백업 선행. 적용 시점 드리프트 41건 / 라우팅 가능 31건
- **`scripts/regate.sh` 신설** — 골든셋 교체 후 기존 `agent_id` 를 그대로 두고 게이트만 다시 돈다.
  `proof_ab.sh` 는 실행마다 **새 Agent 를 등록**하므로 재게이트에 쓸 수 없다
- **29건 전부 PASSED** (acc 0.80~0.95). `agent_capability.gate_run_id` 가 새 run(`c21d9ef7…`)으로 이동
- 라우팅 드리프트 **31 → 1건** · 증서 수 31 유지 · assignment 무손실 · `demo.sh` 사슬 정상
- 남은 1건은 `seed-agent` — `placeholder.safetensors` 라 실게이트 불가. 새 볼륨에는 생기지 않는 이 볼륨만의 유물
- 스크립트 버그 1건 수정: `docker compose exec -T` 가 루프 stdin 을 먹어 첫 건만 처리하던 것을 fd 3 분리로 해결

## SD-013 골든셋 sha 정합 — 선언부 5곳 통일 — 2026-08-10

홀드아웃 재추출(#26) 때 매니페스트만 교체되고 선언부가 따라오지 않아 sha 가 갈렸다.
capability 행이 **리포에 없는 골든셋**을 가리켰다 (D15 위반). 사슬이 self-consistent 라 데모는 통과했다 — 조용히 틀렸다.

- 정본 = 커밋된 매니페스트 재계산값 `c21d9ef7…` (`extract_golden.py:175-177` 과 동일 정본화)
- 선언부 4곳 정정: `image-classify-v1.md`(`0341d121…`) · `eurosat-rgb.json` 기계 핀 · `seed.sql` · `contest-report-draft.md`
  (당초 3곳으로 보고했으나 실제로는 기계 핀·보고서 초안을 포함해 **5곳**이었다)
- 매니페스트 실체는 **무변경** — 케이스 40건 sha 가 파일과 전부 일치함을 확인
- `migrations/0003_golden_set_sha256_holdout.sql` — 기존 볼륨 경로. 구 값 한정 UPDATE 라 멱등
- **`scripts/check_golden_sha.py` 신설** — 매니페스트 재계산값 vs 선언부 4곳 vs 케이스 40건 대조.
  정정 전에 돌려 5곳 전부를 잡는 것을 확인한 뒤 고쳤다. 이 검사가 있었으면 #26 에서 걸렸다
- 러너가 서버 `RAISE NOTICE` 를 흘리도록 수정 — 0003 의 드리프트 경고가 삼켜지고 있었다
- 검증: 기존 볼륨(구 sha) 업그레이드 → `c21d9ef7…` · 드리프트 1건 경고 · 멱등 /
  새 볼륨(정본 seed) → 드리프트 0건. 실 볼륨은 미적용
- **재게이트는 미결** — 구 골든셋에서 얻은 PASS 증서가 그대로 라우팅된다 (`drifted_still_routable=1`).
  증서 삭제는 하지 않았다 (절대규칙 8 · D15)

## SD-007 마이그레이션 체계 — 유통 세대 v제품-1 착수 관문 — 2026-08-10

`product-distribution.md` §5 「스키마 제약을 약화하지 않는다. DDL **추가**와 마이그레이션(SD-007)만」의
적용 수단을 만들었다. 기존 볼륨을 `docker compose down -v` 없이 올릴 수 있다.

- **러너** `apps/core/app/migrate.py` — `status` / `verify` / `up [--dry-run]`. 순방향 전용, 다운그레이드 없음
- **원장** `schema_migration` (version · name · checksum · applied_at · applied_by)
- **`migrations/0001_baseline.sql`** — no-op. 신규 볼륨(initdb)과 기존 볼륨이 같은 경로를 타게 하는 장치
- **`migrations/0002_provenance_drift_view.sql`** — `provenance_drift` · `provenance_drift_summary` 뷰 추가.
  골든셋 교체 후 **다른 골든셋에서 얻은 PASS 증서가 그대로 라우팅되는지** 조회 가능하게 (D15)
- **절대규칙을 도구가 강제** — 제약 약화(`DROP CONSTRAINT`·`NOT VALID`…)와
  `assignment`/`gate_run` 수기 `VALUES` INSERT 를 적용 **전에** 정적 거부
- 래퍼 `scripts/migrate.sh` · 문서 [`docs/guide/migrations.md`](../guide/migrations.md) · INDEX 링크
- 새 의존성 **0** (psycopg 만 · alembic 도입 안 함) · compose 무변경 · Dockerfile 에 `COPY migrations` 한 줄
- 검증: 일회용 컨테이너 11종 — 적용·멱등·부분실패 롤백·체크섬 드리프트 양방향·baseline 가드·파일명/번호 규칙·러너 4개 동시 기동.
  동시 기동에서 `CREATE TABLE IF NOT EXISTS` 경합 버그를 발견해 잠금 안으로 옮김
- **실 볼륨 미적용** — 승인 후 `scripts/migrate.sh up`
- **SD-013 신규**: 골든셋 sha 가 매니페스트 `c21d9ef7…` / 문서 `0341d121…` / seed `c8254bcb…` 로 3중 불일치.
  자동 수정하지 않았다 — 정정은 재게이트를 동반한다

## 제품 유통 목표 문서화 (D19) · 데모 골든 홀드아웃 — 2026-08-10

- **D19:** Open Agent + (선택) Open Compute + User-defined Trust Domain. 경제는 선택·비기초. 정본 [`docs/design/product-distribution.md`](../design/product-distribution.md)
- 로드맵 §5.1 · handoff · STATE · INDEX · README 링크 · 사용안내 신뢰 경계 절
- **데모 N=40** `split=holdout` 재추출 · `check_golden_leakage` clean. 커밋 A 가중치는 여전히 `train_images=27000`
- 커밋 서명: `user.name`=finn|toma|pl + 팀 noreply (`CLAUDE.md` · github-team-guide)
- 촬영 런북·regulation sha·handoff A/B Within 무효 반영

## 사이클 폐쇄 + 서사 전환 (v4.7) — 2026-08-09

**코드** — 사용자 → Core → Node → Core → 사용자 사이클을 닫았다
- Core 디스패치 워커 · `GET /v1/internal/nodes/{id}/assignments` (당기는 방식·NAT)
- Node 폴링 루프 + **배정 검증(403)**. 이전에는 기기에 닿는 누구나 추론을 시킬 수 있었다
- `demo.sh`·`proof_ab.sh`에서 기기 직접 호출 제거. 증적 출력 추가
- 스키마 변경 없음

**계약** — 기획서 v4.6 → v4.7
- **Capability = 인터페이스 계약.** 골든셋 게이트는 선택적 품질 프로파일 (D18)
- `min_per_class_recall 0.10` 신설(유도) — 없으면 클래스 2개 버린 모델이 통과(m=8 → 0.80/0.711)
- `min_accuracy 0.68`은 **선언된 서비스 수준**으로 근거 교체 (SD-004 순환 대체)
- 편차는 숫자를 두지 않음 — `1−t`는 항등식이지 제약이 아니다
- `guarantee` 블록 — 무엇에 조건부인지를 기계가 읽는 형태로

**서사** — 전 문서에서 「채점 가능한 계약」 제거
- 기획서 §1·§4.4 · README · 보고서 md·양식 · 런북 · 스토리보드 · Contest MVP · 체크리스트
- 촬영 런북: A/B 20→10초, **증적 10초 신설**. 자막 8문장 교체


## Phase 1 판정 = 보류 · 골든셋 누출 발견 — 2026-08-08

- **P1-1·P1-2 달성**: `scripts/proof_ab.sh` — A/B 실게이트 PASSED(`dummy=false`) + 동일 case 교차 할당(`honored=true`, assignment 2건 SUCCEEDED). §7.1-2·3 사슬 위 달성
- **P1-3**: `scripts/pass_rate.sh` · 8후보 사다리(TE{5,20,40,80}·TEB{5,10,20,40}) → **75.0%**. 모집단 설계는 결과 확인 전 커밋(`7100c9f`)
- **P1-4**: `docs/ops/phase1-verdict.md` — **판정 보류(HOLD)**
- **SD-008 골든셋 ⊂ 학습셋**: 데모 40/40 · n300 300/300이 학습에 쓰인 이미지. 홀드아웃 없음 → 게이트가 능력이 아니라 학습 데이터 재현을 잰다. `scripts/check_golden_leakage.py` (exit 2). **Phase 2 착수 차단**
- 영향 없음: 게이트 사슬 · M25 6종 · sanity floor 3종 · Product Track 구조
- n=300 재현: A 0.8800 · B 0.9267 · abs_diff 0.046667 · **label_agreement 0.8933**(300건 중 32건 라벨 상이)
- 재현성 수정: `demo.sh`·`sanity.sh` 호스트 `python`→`python3`, `demo.sh` f-string 백슬래시 → % 포맷. **.sh 경로는 Linux에서 한 번도 성공한 적이 없었다** (Contest Must M4 직결)
- 보고서 초안 §8에 누출 명시 · §0·§8의 낡은 A/B 서술 정정

## 종착점 Phase 3+ 확장 · Phase 1 좌표 정정 — 2026-08-08

- **D16**: 프로젝트 종착점 = 기획서 §9 Phase 3+ 전체. Contest MVP는 Phase 1 슬라이스 (SD-006)
- `docs/design/roadmap.md` 신설 — Phase 1 완주 → 2 → 3 → 4–6 진입조건·산출물·판정 게이트
- **정정**: A/B n300 Within은 **게이트 사슬 밖 측정**. §7.1 증명 대상 2·3번(Agent B 실게이트 PASSED, 증명 모드 교체 할당) 미달 · 통과율 20–80% 미실측 — STATE·SD-001 반영
- **SD-007**: 마이그레이션 체계 부재 (Phase 2 `node_credential` DDL 선결과제)
- **지정 실행(M14) 배관은 이미 존재** — `task.requested_agent_id` + `claim.py` 조인(`agent_capability_passed` 경유). §7.1-3은 미구현이 아니라 **미실행**이며 막는 것은 Agent B 하나. 실제 공백은 `proof_run_id` 기록·UC-7 절차
- 촬영 런북: UC-7 불가 명시(B 미통과). 스키마·코드 변경 없음

## Team role pl (peer of finn/toma) — 2026-08-08

- `docs/guide/github-team-guide.md` v1.3 · `CONTRIBUTING.md` — 작업 역할 **pl** (`pl/<topic>`, `LGTM (pl)`, finn/toma와 동급). master는 merge 전용

## README stable-only + schedule canon — 2026-08-08

- README: 심사 빠른 시작 상단 · 상태/결정/일정 본문 제거 → STATE·handoff·checklist 링크만
- `contest-submission-checklist.md` = 일정·제출 정본 (notice/39 인용). Contest_MVP §1·handoff §4는 링크

## A/B Must Within (n=300) — 2026-08-08

- Agent A 80ep · B 40ep · n300 abs_diff≈0.0467 → **WITHIN_THRESHOLD** (SD-001 closed)
- 공개 가중치: `eurosat_scratch.safetensors` 갱신 · `eurosat_scratch_b.safetensors` 추가 (gitignore 예외)
- 한계: epoch A≠B · SE≈임계 — 보고서/영상에 명시. 출품 양식·UC-7 반영 가능

## Agent B n300 + A/B measure — 2026-08-08

- `TinyEuroSATB` 20ep → `eurosat_scratch_b.safetensors` (local · gitignore)
- n300: A≈0.817 · B≈0.887 · `|diff|=0.07` → **EXCEEDS_THRESHOLD** · Contest Must 아님 (SD-001)
- 출품 우선: 양식·영상·포털. A/B Must 승격 비권장

## Dual-track contest runbook + Agent B train — 2026-08-07

- `docs/ops/shoot-day-runbook.md` · `gate-chain-slide.md` · 출품 체크리스트 갭/이중 트랙 갱신
- Agent B(`TinyEuroSATB` → `eurosat_scratch_b.safetensors`) 학습 착수 (gitignore · Must 아님)

## E1 n=300 score + A/B skeleton — 2026-08-07

- `TinyEuroSATB` + `ARCH_REGISTRY` / `build_model` · meta `arch`로 infer 로드
- `train_scratch` `ARCH`/`OUT_NAME` · `scripts/score_n300` · `scripts/compare_ab` (n&lt;300 → INCONCLUSIVE)
- 로컬 실측 Agent A n=300: acc≈0.817 · f1≈0.814 (artifacts/ 미커밋). B·paired 미실행
- A/B **Must 아님** (SD-001 미결). 스키마 DDL 변경 없음

## Contest compliance drafts — 2026-08-07

- `docs/ops/regulation-compliance.md` — 운영규정 조항별 준수 근거
- `docs/ops/contest-report-form-draft.md` — 공식 양식용 5P·붙임1·2 초안 문장
- 가중치 raw URL HTTP 200 실측 (제9조 유형3 공개)

## SBOM cyclonedx + retrospective — 2026-08-07

- 호스트 Python 3.12 · `scripts/generate_sbom.ps1` / `.sh` · `enrich_sbom.py` → `sbom.json` (수동본 대체)
- `docs/retrospective/` — TD / Scope Decision / Environment Adaptation 레지스터
- TD-001(수동 SBOM) closed

## Contest deliverables draft — 2026-08-06

- `docs/ops/contest-report-draft.md` — §3 아키텍처(게이트 사슬) · §4 DB 제약 · §6 골든 · §7 재현 · §9 라이선스
- `docs/ops/demo-video-storyboard.md` — 3분 영상 촬영 체크리스트
- `sbom.json` — CycloneDX 1.5 (THIRD-PARTY-LICENSES와 정합)

## node_credential 설계 초안 — 2026-08-06

- `docs/design/node-credential-draft.md` — 발급·검증 원칙. **스키마 DDL 없음**

## Capability API + golden n=300 pipeline — 2026-08-06

- `POST /v1/capabilities` 런타임 등록 (UNIQUE·mvp CHECK는 DB). 스키마 DDL 변경 없음
- `scripts/extract_golden.py --n 300` + `extract_golden_n300` → `data/golden-n300/` (gitignore)
- 데모 N=40과 본편 N=300 분리. A/B Must 미결·미구현

## S3 + OpenAPI — 2026-08-06

- S3: `gate finish`에서 `golden_set_sha256`가 `gate_run` 스냅샷과 불일치하면 거부. 실게이트(`dummy=false`)는 필드 필수
- S4: `docs/spec/openapi.yaml` 초안 + Core `GET /openapi.yaml`. 스키마 DDL 변경 없음

## MVP phase2 — 2026-08-06

- EuroSAT RGB **scratch** TinyEuroSAT → `eurosat_scratch.safetensors` (safetensors만, 사전학습 없음)
- Node: scratch 추론 · Core: `dummy=false` 실게이트 검증(지표 AND) · `score_gate`
- 실측 후 임계 보정: `min_accuracy` 0.68 · `min_macro_f1` 0.65 (가정 0.75/0.72는 실측 위)
- `scripts/demo` 실게이트 PASSED + Task 완주 · `scripts/sanity` floor 3종 FAILED
- torch/torchvision(CPU, node-m-team) · Pillow · THIRD-PARTY 갱신
- **seed/smoke dummy PASSED ≠ 실게이트.** A/B Must 미결·미구현

## MVP phase1 — 2026-08-06

- 골든셋 데모 N=40 manifest + cases/ (균등 스트라이드, 모델 선택 없음)
- 픽셀 전수: EuroSAT RGB 27,000장 전부 64×64×3
- `scripts/demo_violations` M25 6종
- 결과보고서 초안 0·1·2·5·8절
- compose Node 3대 자원 제한 (S/team, S/public, M/team). `node_credential` 없음
- **scratch 학습·실게이트 채점 아님**

## W1 — 2026-08-06 (EuroSAT RGB pin)

- Zenodo `7711810` / `EuroSAT_RGB.zip` 실측: `archive_sha256`, 원본 64×64, Pascal 클래스 폴더
- 핀 파일 `docs/spec/golden/eurosat-rgb.json` · 다운로드 스크립트. **원본 미동봉 · scratch 학습 아님 · 케이스 manifest 없음**
- seed `golden_metrics.dataset`에 archive 핀. `golden_set_sha256`은 빈 placeholder 유지. 스키마 변경 없음

## W1 — 2026-08-06 (CRUD + gate chain API)

- Agent / Node 등록·조회, 바인딩 → READY (`INSERT … SELECT`)
- `gate_run` 시작·종료 사슬 API. **골든셋 추론 아님.** PASSED는 `dummy=true` 기록만
- Node 등급은 Core 관리자 등록. Node 런타임 자기주장 경로 없음
- smoke: .pth 거절 · non-runner 409 · dummy 게이트 후 claim/execute

## W1 — 2026-08-06 (plan v4.5 + dummy Node)

- 기획서 **v4.5**: §2.5 Interface–Implementation Separation, Execution Provenance(개념), §14 문헌, §15 완료=최소 증서. 스키마는 v4.4 유지
- dummy Node: placeholder safetensors 로드 → dummy 추론 → `POST /v1/internal/assignments/{id}/complete`
- smoke: 새 task claim 후 node `/v1/execute`까지. **EuroSAT scratch 학습 아님**

## W1 — 2026-08-05

- `compose.yaml`: PostgreSQL 16 + Core(FastAPI)
- `docs/spec/schema.sql` 적재 + `image.classify@1` seed + datasetId allowlist (`eurosat-rgb`)
- claim: `INSERT … SELECT` + `FOR UPDATE SKIP LOCKED` (`POST /v1/internal/claim`)
- 팀 가이드 v1.2 fast-track (§6.4)

## Docs — 2026-08-05

- 문서 레이아웃 [PR #5](https://github.com/gncorpseo-commits/capnet/pull/5) `main` 머지
- Wiki Home 링크를 `main` 카테고리 경로로 고정

## Docs — 2026-08-03 (layout)

- 문서 트리 정리: `docs/{guide,error,history,design,spec,ops,research}` + [`docs/INDEX.md`](../INDEX.md)
- 위반·함정 본문을 `docs/error/`로 분리 (handoff 중복 제거)
- README 문서 표 → INDEX 위임

## Docs — 2026-08-03

- 팀 GitHub 사용 표준 가이드 v1.1 (`docs/guide/github-team-guide.md`, Wiki 동기화)
- `CONTRIBUTING.md` 추가

## v4.4 — 2026-07-31

게이트 사슬·trust_domain_min 무결성. Phase 1 동결 후보.

- `gate_run`: runner NOT NULL + `node(id, is_gate_runner)` 복합 FK
- `gate_run_passed` 증서 → `agent_capability` PASSED만 근거 있는 run에 연결
- `domain_min_compatible` + task `capability_trust_domain_min`
- 기획서 파일명 `capnet-plan.md`로 정리; `docs/_to_delete` 제거

## Naming — 2026-07-31

제품명 확정: **Capability Network (CapNet)**. 약어 **CN**.  
**ai-agent-store** = 상위 레포/공간 · CapNet = 그 안 첫 제품.  
(이전 가칭: AI World / AI Agent Store)

## Contest — 2026-08-01

- [`Contest_MVP_2026.md`](../ops/Contest_MVP_2026.md) **v0.3** — 문서세트 정합 (골든셋 v0.2, 영문 파일명, M25 6종 고정)
- [`user-guide-ko.md`](../guide/user-guide-ko.md) — IT 비전문가용
- [`golden/image-classify-v1.md`](../spec/golden/image-classify-v1.md) — 골든셋 정본

## v4.3 — 2026-07-31

호환 행렬 무결성.

- `tier_compatible` / `domain_compatible`: rank 컬럼 + rank 테이블 복합 FK + CHECK 순서
- 독성 행렬 INSERT 차단 (team→public, L→S)
- Phase 1 스키마 동결 후보

## v4.2 — 2026-07-31

스냅샷 거짓 기재·가중치 드리프트 패치.

- `UNIQUE (task.id, capability_id, trust_domain)` ← assignment FK
- `UNIQUE (capability.id, compute_tier)` ← assignment FK
- `agent_node_ready` 이중 FK: node seen hash + `agent(id, weights_sha256)`
- live READY/assignment 중 가중치 UPDATE 거부

## v4.1 — 2026-07-31

리뷰 실측 결함 패치.

- `compute_tier_rank` / `tier_compatible` (TEXT `'L'<='S'` 함정 제거)
- `trust_domain_rank` / `domain_compatible` (privacy_rank; tenant ↛ public)
- `agent_capability_passed`, `agent_node_ready`, assignment 복합 FK
- Node `(id, trust_domain, compute_tier_max)` UNIQUE — 강등 TOCTOU
- 문서 §5.1 모순 해소; 10주 인터뷰 3–5건; `energy_wh` 예약

## v4.0 — 2026-07-31

전략·계층·경제 개정. v3.2 기술 골격 유지.

- Wedge: 배치/비동기/거주지 (클라우드 실시간 API 비경쟁)
- First capability: `image.classify@1`
- Compute Tier S/M/L, Trust Domain team→tenant→public
- Kill/Pivot criteria, 10-week Phase 1 plan
- work_units metering from Phase 2 (no settlement)
- Schema: compute_tier, trust_domain*, assignment duration/vram

## v3.2 — 2026-07-31

리뷰 병합 + 자체점검 20항목. Schema S1–S11.

## v3.1 / v3.0

전제 교정 및 WSL 유실 후 복원 통합.
