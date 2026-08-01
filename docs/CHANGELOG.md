# Changelog

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
