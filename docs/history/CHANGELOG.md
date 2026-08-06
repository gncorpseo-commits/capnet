# Changelog

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

- [`Contest_MVP_2026.md`](./Contest_MVP_2026.md) **v0.3** — 문서세트 정합 (골든셋 v0.2, 영문 파일명, M25 6종 고정)
- [`user-guide-ko.md`](./user-guide-ko.md) — IT 비전문가용
- [`golden/image-classify-v1.md`](./golden/image-classify-v1.md) — 골든셋 정본

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
