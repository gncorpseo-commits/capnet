# Changelog

## 남의 Agent 를 받기 위한 첫 두 칸 — arch 결속 · 자원 한도 (I1·I2) — 2026-08-11

새 설계 문서 [`design/foreign-agent-isolation.md`](../design/foreign-agent-isolation.md) —
「남의 Agent」를 **F1(남의 가중치) · F2(남의 아키텍처 선언) · F3(남의 코드)** 세 단계로 쪼개고,
F3 앞에 있는 **코드로 못 푸는 전제**(법무 킥오프 · 고객 1곳)를 명시한다.
Phase 3 진입조건의 「격리 초안」이 이 문서다.

**드러난 구멍 2개 (F1·F2 를 막는 것)**

1. **아키텍처가 계약에 없었다.** `infer.py` 가 Node **로컬 파일**(`meta.json`)에서 arch 를 읽었다.
   Agent 신원은 `weights_sha256` 뿐이라 arch 는 그 해시에 포함되지 않는다 —
   게이트가 승인한 것과 실행한 것이 같다는 보장이 **코드에 없었다**
2. **추론에 자원 한도가 전무했다.** compose 의 `mem_limit` 은 컨테이너 **전체** 한도라,
   한 건의 악성 추론이 같은 Node 의 다른 lease 까지 죽인다

**I1 — arch 를 계약에 묶는다** (`migrations/0008`)

- `agent_arch` 룩업 테이블 — 허용 아키텍처가 **DB 행**이다 (`compute_tier_rank` 와 같은 idiom).
  없는 arch 로는 Agent 등록이 **FK 로** 막힌다 (HTTP 400)
- `agent.arch` → FK. 배정 페이로드가 **Core 의 arch** 를 싣고, Node 는 그것으로 로드한다
- legacy 는 `arch IS NULL` 로 두고 `agent_arch_unbound` 뷰로 드러낸다 —
  **실 DB 실측 45건 · 라우팅 가능 35건.** Core 는 가중치 파일을 보지 않으므로 추측으로 채우지 않았다

**I2 — 실행 자원 한도** (부분)

- 파라미터 수 상한 (`agent_arch.max_params` → 페이로드 → **매 호출** 검사) ·
  입력 픽셀 상한 · torch thread 제한
- 구현 중 「로드할 때만 검사」 버그를 만들었고 실측으로 잡았다 — 캐시된 뒤 상한을 낮춰도 계속 돌았다
- **wall-clock timeout 은 아직 없다.** 파이썬에서 CPU 바운드를 안전히 끊으려면 별도 프로세스가 필요하고,
  그건 F3 의 프로세스 격리와 같은 작업이라 거기서 함께 한다

**검증** — 통합 10종(allowlist 밖 arch 등록 FK 차단 · 페이로드 arch·max_params 전달 · legacy 가시화 · 격리) ·
Node 한도 실측(정상 / 상한 초과 거부 / allowlist 밖 arch 거부 / legacy 경로 유지) · 실 사슬 회귀 통과.

## 최소 UI — Node 등록 · 능력 호출 (P2-3) — 2026-08-11

로드맵 P2-3(「최소 UI · 호출면」)을 채운다. Core 가 직접 서빙한다.

- `/ui/nodes.html` — Node 등록 · 함대 상태(생존·증서) · **증서 발급/폐기**.
  발급 시 평문 시크릿을 **그 자리에서 한 번만** 보여 주고(C3), 파일 주입을 권장한다고 알린다
- `/ui/call.html` — **Agent 를 지정하지 않는** 능력 호출. 결과와 함께 **증적**(기기·Agent·가중치 해시)을
  같이 보여 준다. `dummy=true` 면 「실제 추론이 아니다」를 붉게 띄운다
- `GET /v1/datasets` — 입력 allowlist 조회면 (절대규칙 7)
- `GET /` → `/ui/nodes.html` 리다이렉트

**새 의존성 0** — `StaticFiles` 는 starlette 동봉이다. 외부 자산(CDN·폰트·아이콘)을 쓰지 않아
내부망·오프라인에서 그대로 뜬다. 빌드 단계도 없다.

UI 는 등급을 **Core 가 부여한다**는 것을 화면에 명시하고, 등급 조합 제약(`ck_trust_provision_align`)을
미리 알려 준다 — 실측으로 `team`+`public` 조합은 **400** 으로 거절된다.

**UI 가 하지 않는 것:** Agent 게이트·바인딩 (가중치가 기기에 있어야 하므로 터미널 작업).

## Node 운영화 — 등록부터 능력 호출까지 (v제품-1) — 2026-08-11

증서(P2-4)를 만들었지만 **Node 런타임이 그것을 보내지 않아** 강제를 켤 수 없었다.
그리고 「Capability 로 요청한다」는 제품 경로가 스크립트로도 문서로도 없었다. 둘 다 메운다.

- **Node 런타임이 증서를 실어 보낸다** — heartbeat · assignments · complete 세 경로 모두.
  `NODE_CREDENTIAL_FILE` 로 **파일 주입**을 권장한다 (환경변수 직접 주입은 `docker inspect` 에 노출).
  `/health` 는 `credential_present` 만 알리고 값도 prefix 도 내보내지 않는다
- **`scripts/node_onboard.sh`** — 등록 + 증서 발급 + 0600 파일 + 주입할 환경변수 출력.
  `provision_source` 를 도메인에서 유도한다 (`ck_trust_provision_align` 준수)
- **`scripts/node_bind.sh`** — 가중치 sha 실측 → Agent 등록 → **team gate-runner 에서** 실게이트
  (절대규칙 8) → 통과 시에만 바인딩. 미통과면 exit 2
- **`scripts/call.sh`** — **Agent 를 지정하지 않는** 능력 호출. 증적(node·agent·weights_sha256)을 같이 낸다.
  `dummy=true` 면 exit 2 — 실제 추론이 아닌 것을 성공으로 읽지 않게
- `docs/guide/operate-node.md` — 세 단계가 각각 무엇을 세우는지 · 등급 조합 제약 · 강제 켜는 법 ·
  자주 막히는 곳 · **아직 없는 것**
- `.gitignore` 에 `data/node-secrets/` · `*.credential`

**실측** — 강제 모드(`REQUIRE_NODE_CREDENTIAL=1`)에서 전체 사슬 확인:
증서 없는 heartbeat **401** · 증서 실은 Node 가 `is_fresh=true` · 능력 호출이 실가중치로 완료
(`forest` conf 0.9642 · dummy 아님). 검증 후 시험 증서는 폐기하고 스택을 복구했다.

## P2-4 node_credential — Node 신원 증서 (SD-002 · SD-010) — 2026-08-11

기획서 §16 이 동결한 v4.4 를 **처음으로** 건드리는 변경이다. 로드맵 §3.1 의 선행 조건 셋
(①마이그레이션 도구 ②볼륨 보존 경로 ③승인)이 모두 충족돼 열렸고, **추가만** 한다 (절대규칙 1).

**무엇을 막는가.** Node 경로는 `node_id` 를 **URL 에서 그대로** 받았다 —
`POST /v1/internal/nodes/{node_id}/heartbeat` 를 아무나 부를 수 있었고 방어는
「팀 내부망 전제」뿐이었다 (SD-010). 이제 증서가 오면 Core 가 시크릿을 검증해 node_id 를
**해석**하고 URL 이 주장하는 값과 대조한다.

- `migrations/0007` — `node_credential` + `node_credential_status` 뷰 ·
  활성 증서 1개(부분 UNIQUE) · 이유 없는 폐기 금지 · prefix 형식 CHECK
- `apps/core/app/credential.py` — 발급·검증·폐기. 평문 시크릿은 **응답에 한 번만**, DB 엔 sha256 만 (C3)
- API — `POST /v1/nodes/{id}/credentials` · `.../revoke` · `GET /v1/nodes-credentials`
- **절대규칙 4 를 구조로 강제** — 증서에 등급 컬럼이 **없다.** 발급 API 는 `extra="forbid"` 로
  등급 필드를 **422** 로 거절한다. 등급은 언제나 `node` 행에서 읽는다
- **강제는 플래그** (`REQUIRE_NODE_CREDENTIAL`, 기본 꺼짐 — 데모 경로 유지).
  다만 **토큰이 오면 항상 검증**한다. 잘못된 증서가 통과하는 구간을 만들지 않는다
- 검증: 통합 17종 · HTTP 7종(사칭 **403** · 위조 **401** · 폐기 후 **401** · 강제 모드 **401**) ·
  상태 조회에 시크릿·해시 미노출

초안의 열린 질문 4개를 확정했다 — opaque+해시 / 전 Node·플래그 강제 / `expires_at` 선택·폐기 후 재발급 /
`api_key` 와 통합하지 않음.

## P2-1 tenant 운용 · 시드 결함 2건 (SD-015 · SD-016) — 2026-08-11

- **`migrations/0006` — tenant 신뢰 경계 운용 (P2-1 · D19).** tenant 플릿 Node + `image.classify@2`(`trust_domain_min='tenant'`).
  로드맵은 「DDL 추가가 아니라 운용」이라고만 적었는데, 실제로는 한 칸이 더 있었다 —
  `domain_min_compatible` 상 tenant Task 는 `min='team'` 계약을 **원천적으로 못 쓴다**.
  기존 계약을 낮추지 않고 새 계약을 추가했다 (출품 트랙 불변)
- **`tests/integration/check_tenant_routing.py` 6종** — tenant→tenant 배정(양성 대조) · tenant→team 허용 ·
  **team→tenant 차단** · tenant 가 team 전용 계약 사용 불가 · public 이 tenant 계약 사용 불가 · 거짓 스냅샷 거절

### SD-015 — 시드가 「얻을 수 없는 증서」를 발급했다

`seed-agent` 는 `placeholder.safetensors` 라 **실게이트가 원리적으로 불가능**한데(로드조차 안 된다)
라우팅 가능 증서를 갖고 있었고, UUID 가 가장 낮아 **claim 1순위**였다.
`requestedAgentId` 없는 Task 가 `dummy:true` 라벨을 COMPLETED 로 받았다 — 실 DB 에 **5건**.

- `seed.sql` 이 라우팅 투영을 만들지 않는다 · 기존 볼륨은 `migrations/0005` 가 폐기
- 시드 증서에 기대던 `demo_violations.sql`·`check_pg_violations`·`check_revocation` 을 자립시켰다
- CI 가 「새 볼륨에 placeholder 라우팅 증서 0건」을 검사한다

### SD-016 — claim 이 호환 행렬을 후보 단계에서 보지 않았다

`CLAIM_SQL` 이 `domain_compatible`·`tier_compatible` 을 조인하지 않아, 호환 불가 조합을 **고른 뒤**
INSERT 에서 FK 가 거절했다. 라우팅 차단 보장은 지켜지지만 **가용성이 깨진다** —
team Node 가 바빠 tenant Node 가 먼저 정렬되면 호환 Node 가 있는데도 예외가 나고 Task 가 배정되지 않는다.
tenant Node 를 넣자마자 재현됐다. 두 행렬을 조인해 후보 단계에서 거른다. FK 는 최후 방어로 유지.

## PG 위반 19종 자동 회귀 (M25) — 2026-08-11

이 프로젝트의 중심 주장은 「판정은 앱 `if` 가 아니라 PostgreSQL 제약이 한다」이다.
그 증거가 **수동 실측 기록**(`docs/error/pg-violations.md` 14종)과
**CI 밖 스크립트**(`scripts/demo_violations.sql` 6종)뿐이었다.

- **`tests/integration/check_pg_violations.py` 신설 · 19개** — CI migrate job 에 편입
- **어느 제약이 거절했는지까지 대조한다.** 이게 핵심이다 —
  실제로 `assignment_agent_id_capability_id_fkey` 를 떨어뜨려 보니 그 케이스는 **여전히 거절됐다**
  (다른 FK 가 잡았다). 거절 여부만 보는 시험이었으면 그때 초록이 떴다
- **양성 대조** — 정상 할당은 반드시 통과해야 한다. 없으면 스키마가 통째로 망가져도
  「전부 거절됨」으로 초록이 뜬다
- 전부 SAVEPOINT + 최종 ROLLBACK. 롤백됐는지도 검사한다 (seed 오염 방지)
- 변이 검사 — 제약 2종을 실제로 DROP 해 각각 FAIL 재현
- 만들면서 시험 자체의 결함 3건을 고쳤다: psycopg 다중 문장 · `ck_gate_runner_team` 이 먼저
  걸려 겨냥한 FK 를 못 보던 것 · 스냅샷을 거짓으로 적어 다른 케이스와 같은 것을 시험하던 것
- `scripts/demo_violations.sql` 은 촬영용 6종 시연으로 남긴다 (NOTICE 가 화면에 보인다)

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
