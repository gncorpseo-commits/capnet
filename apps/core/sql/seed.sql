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
    '{"type":"object","required":["datasetId","caseId"],"properties":{"datasetId":{"type":"string"},"caseId":{"type":"string"}}}'::jsonb,
    '{"type":"object","required":["label"],"properties":{"label":{"type":"string","enum":["annual_crop","forest","herbaceous_vegetation","highway","industrial","pasture","permanent_crop","residential","river","sea_lake"]},"confidence":{"type":"number","minimum":0,"maximum":1}},"additionalProperties":false}'::jsonb,
    'closed_set_labels',
    'M', 'team', true,
    'docs/spec/golden/manifest-image-classify-v1.json',
    'c8254bcb454d6ca362f61c0426e4a7c9c7de42cc81fa6ab3ed097b64c2862066',
    40,
    '{"primary_metric":"accuracy","min_accuracy":0.68,"min_macro_f1":0.65,"max_invalid_rate":0.02,"combine":"AND","guarantee":"floor_only","equivalence_observed":{"metric":"accuracy","comparison":"paired_same_cases","note":"observation only; not a pass condition (SD-009, plan v4.6)"},"scoring_version":1,"threshold_basis":{"agent":"TinyEuroSAT","n":40,"measured_accuracy_range":[0.70,0.725],"note":"assumed 0.75/0.72 was above scratch baseline; calibrated for 20-80% pass band"},"dataset":{"id":"eurosat-rgb","zenodo_record":"7711810","archive":"EuroSAT_RGB.zip","archive_sha256":"b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90","zip_root":"EuroSAT_RGB","native_hw":[64,64],"contract_resize_hw":[32,32]}}'::jsonb
)
ON CONFLICT (code, version) DO NOTHING;

-- 기존 볼륨에서도 임계 실측 보정이 반영되게 한다 (스키마 변경 없음).
UPDATE capability
   SET golden_metrics = '{"primary_metric":"accuracy","min_accuracy":0.68,"min_macro_f1":0.65,"max_invalid_rate":0.02,"combine":"AND","guarantee":"floor_only","equivalence_observed":{"metric":"accuracy","comparison":"paired_same_cases","note":"observation only; not a pass condition (SD-009, plan v4.6)"},"scoring_version":1,"threshold_basis":{"agent":"TinyEuroSAT","n":40,"measured_accuracy_range":[0.70,0.725],"note":"assumed 0.75/0.72 was above scratch baseline; calibrated for 20-80% pass band"},"dataset":{"id":"eurosat-rgb","zenodo_record":"7711810","archive":"EuroSAT_RGB.zip","archive_sha256":"b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90","zip_root":"EuroSAT_RGB","native_hw":[64,64],"contract_resize_hw":[32,32]}}'::jsonb
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

INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status)
SELECT ac.agent_id, ac.capability_id, ac.gate_status
FROM agent_capability ac
WHERE ac.agent_id = '00000000-0000-4000-8000-000000000020'::uuid
  AND ac.gate_status = 'PASSED'
ON CONFLICT (agent_id, capability_id) DO NOTHING;

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
