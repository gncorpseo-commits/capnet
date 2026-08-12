-- W1 seed — 고정 UUID · 재실행 가능(ON CONFLICT).
-- gate_run / assignment 는 INSERT … SELECT 만 (스냅샷 수기 금지).

BEGIN;

INSERT INTO app_user (id, name, role) VALUES
    ('00000000-0000-4000-8000-000000000001', 'seed-admin', 'admin')
ON CONFLICT (id) DO NOTHING;

INSERT INTO capability (
    id, code, version, name, description,
    input_schema, output_schema, output_kind,
    compute_tier, trust_domain_min, mvp_eligible,
    golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics
) VALUES (
    '00000000-0000-4000-8000-000000000010',
    'image.classify', 1,
    'EuroSAT land-cover classify',
    'closed-set 10 labels · native 64x64 RGB · contract resize 32x32 · contest demo N=40',
    '{"type":"object","required":["datasetId","caseId"],"properties":{"datasetId":{"type":"string"},"caseId":{"type":"string"}},"mediaTypes":["image/jpeg"]}'::jsonb,
    '{"type":"object","required":["label"],"properties":{"label":{"type":"string","enum":["annual_crop","forest","herbaceous_vegetation","highway","industrial","pasture","permanent_crop","residential","river","sea_lake"]},"confidence":{"type":"number","minimum":0,"maximum":1}},"additionalProperties":false}'::jsonb,
    'closed_set_labels',
    'M', 'team', true,
    'docs/spec/golden/manifest-image-classify-v1.json',
    'c21d9ef796e2165e27926358981489fe397a639d7c0ceb0d01b74846da6b0eef',
    40,
    '{"primary_metric":"accuracy","min_accuracy":0.68,"min_macro_f1":0.65,"max_invalid_rate":0.02,"combine":"AND","min_per_class_recall":0.10,"guarantee":{"type":"floor_on_declared_sample","holds_on":{"dataset":"eurosat-rgb","sampling":"per_class_even_stride","preprocessing":"32x32 RGB","class_balance":"uniform"},"does_not_hold_under":["distribution shift","inputs outside declared allowlist","deliberate overfitting to the static public golden set"],"strengthened_by":"rotating hidden probes (Phase 2 spot-check)"},"deviation":{"enforceable_bound":"1 - min_accuracy","note":"tautological under a floor gate; NOT a constraint. bounding pairwise deviation requires a banded pass criterion","observed":{"n":300,"passer_range":[0.6933,0.8700]}},"scoring_version":1,"threshold_basis":{"kind":"declared_service_level","note":"NOT derived from measurement. admissible band (0.447,0.910] measured: collapsed model 0.447, feasible best 0.910 under no-pretrain 32x32. value is declared and re-declared when a real user requirement exists (supersedes SD-004)"},"dataset":{"id":"eurosat-rgb","zenodo_record":"7711810","archive":"EuroSAT_RGB.zip","archive_sha256":"b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90","zip_root":"EuroSAT_RGB","native_hw":[64,64],"contract_resize_hw":[32,32]}}'::jsonb
)
ON CONFLICT (code, version) DO NOTHING;

-- 기존 볼륨에서도 임계 실측 보정이 반영되게 한다 (스키마 변경 없음).
UPDATE capability
   SET golden_metrics = '{"primary_metric":"accuracy","min_accuracy":0.68,"min_macro_f1":0.65,"max_invalid_rate":0.02,"combine":"AND","min_per_class_recall":0.10,"guarantee":{"type":"floor_on_declared_sample","holds_on":{"dataset":"eurosat-rgb","sampling":"per_class_even_stride","preprocessing":"32x32 RGB","class_balance":"uniform"},"does_not_hold_under":["distribution shift","inputs outside declared allowlist","deliberate overfitting to the static public golden set"],"strengthened_by":"rotating hidden probes (Phase 2 spot-check)"},"deviation":{"enforceable_bound":"1 - min_accuracy","note":"tautological under a floor gate; NOT a constraint. bounding pairwise deviation requires a banded pass criterion","observed":{"n":300,"passer_range":[0.6933,0.8700]}},"scoring_version":1,"threshold_basis":{"kind":"declared_service_level","note":"NOT derived from measurement. admissible band (0.447,0.910] measured: collapsed model 0.447, feasible best 0.910 under no-pretrain 32x32. value is declared and re-declared when a real user requirement exists (supersedes SD-004)"},"dataset":{"id":"eurosat-rgb","zenodo_record":"7711810","archive":"EuroSAT_RGB.zip","archive_sha256":"b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90","zip_root":"EuroSAT_RGB","native_hw":[64,64],"contract_resize_hw":[32,32]}}'::jsonb
 WHERE code = 'image.classify' AND version = 1;

INSERT INTO agent (
    id, owner_id, name, version, status,
    manifest_hash, weights_format, weights_uri, weights_sha256
) VALUES (
    '00000000-0000-4000-8000-000000000020',
    '00000000-0000-4000-8000-000000000001',
    'seed-agent', '0.0.1-seed', 'ACTIVE',
    'seed-manifest',
    'safetensors',
    'file:///weights/placeholder.safetensors',
    '5cd21e43471e2d0a495ce5cee3aae102cbdbd98c7f0db770a74476268b3a3887'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO node (
    id, owner_id, name, device_type, provision_source,
    trust_domain, compute_tier_max, is_gate_runner
) VALUES (
    '00000000-0000-4000-8000-000000000030',
    '00000000-0000-4000-8000-000000000001',
    'seed-gate-runner', 'PC_GPU', 'team',
    'team', 'M', true
)
ON CONFLICT (id) DO NOTHING;

-- gate_run: runner·agent·capability를 SELECT로만 채움
INSERT INTO gate_run (
    id, agent_id, capability_id, runner_node_id, runner_is_gate_runner,
    status, golden_set_sha256, golden_score, cases_total, cases_passed,
    finished_at
)
SELECT
    '00000000-0000-4000-8000-000000000031'::uuid,
    a.id, c.id, n.id, n.is_gate_runner,
    'PASSED', c.golden_set_sha256, 0.80, 40, 32,
    now()
FROM agent a
JOIN capability c ON c.code = 'image.classify' AND c.version = 1
JOIN node n ON n.id = '00000000-0000-4000-8000-000000000030'::uuid
WHERE a.id = '00000000-0000-4000-8000-000000000020'::uuid
  AND n.is_gate_runner = true
ON CONFLICT (id) DO NOTHING;

INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status)
SELECT gr.id, gr.agent_id, gr.capability_id, gr.status
FROM gate_run gr
WHERE gr.id = '00000000-0000-4000-8000-000000000031'::uuid
  AND gr.status = 'PASSED'
ON CONFLICT (gate_run_id) DO NOTHING;

INSERT INTO agent_capability (
    agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at
)
SELECT grp.agent_id, grp.capability_id, 'PASSED', 0.80, grp.gate_run_id, now()
FROM gate_run_passed grp
WHERE grp.gate_run_id = '00000000-0000-4000-8000-000000000031'::uuid
ON CONFLICT (agent_id, capability_id) DO NOTHING;

-- seed-agent 에는 **라우팅 가능 증서를 발급하지 않는다** (SD-015).
--
-- 왜: seed-agent 의 가중치는 `placeholder.safetensors` 다. Node 는 그것을 감지해
-- dummy 모드로 답한다 — 즉 이 Agent 는 **실게이트를 통과할 수 없다** (로드조차 안 된다).
-- 얻을 수 없는 증서를 시드가 발급하면 안 된다.
--
-- 그런데도 발급돼 있었고, UUID 가 가장 낮아 claim 정렬(`ORDER BY acp.agent_id`)에서
-- **1순위**였다. requestedAgentId 없이 들어온 Task 는 이 Agent 로 가서
-- `dummy:true` 라벨을 받고 COMPLETED 로 기록됐다. 증적에 dummy 플래그는 남지만,
-- `label` 만 읽는 사용자에게는 지어낸 답이다.
-- 제품 경로가 「Capability 로 요청한다」(product-distribution §4)이므로 정면으로 닿는다.
--
-- 사슬(gate_run → gate_run_passed → agent_capability)은 그대로 둔다 — 시연 가치가 있다.
-- 라우팅 투영(agent_capability_passed)만 만들지 않는다.
-- 기존 볼륨은 `migrations/0005` 가 폐기 표시로 끊는다.

INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen)
SELECT a.id, n.id, 'BOUND', a.weights_sha256
FROM agent a
JOIN node n ON n.id = '00000000-0000-4000-8000-000000000030'::uuid
WHERE a.id = '00000000-0000-4000-8000-000000000020'::uuid
ON CONFLICT (agent_id, node_id) DO NOTHING;

INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256)
SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen
FROM agent_node an
JOIN agent a ON a.id = an.agent_id AND a.weights_sha256 = an.weights_sha256_seen
WHERE an.agent_id = '00000000-0000-4000-8000-000000000020'::uuid
  AND an.bind_status = 'BOUND'
ON CONFLICT (agent_id, node_id) DO NOTHING;

INSERT INTO task (
    id, user_id, capability_id, status, trust_domain,
    capability_trust_domain_min, input_ref
)
SELECT
    '00000000-0000-4000-8000-000000000040'::uuid,
    u.id, c.id, 'QUEUED', 'team',
    c.trust_domain_min,
    '{"datasetId":"eurosat-rgb","caseId":"ic1-0001"}'
FROM app_user u
JOIN capability c ON c.code = 'image.classify' AND c.version = 1
WHERE u.id = '00000000-0000-4000-8000-000000000001'::uuid
ON CONFLICT (id) DO NOTHING;

COMMIT;
