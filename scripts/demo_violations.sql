-- M25 고정 6종 — 각각 DB가 거절해야 한다. 제약 끄지 않음.
-- 사용: docker compose exec -T postgres psql -U capnet -d capnet -v ON_ERROR_STOP=1 -f - < scripts/demo_violations.sql
-- 각 테스트는 서브트랜잭션에서 잡고 ROLLBACK하여 seed를 더럽히지 않는다.

\echo === M25 demo_violations ===

BEGIN;

-- 공용: 테스트용 public/S 노드 (롤백됨)
INSERT INTO node (
    id, owner_id, name, device_type, provision_source,
    trust_domain, compute_tier_max, is_gate_runner
) VALUES (
    '00000000-0000-4000-8000-0000000000a1',
    '00000000-0000-4000-8000-000000000001',
    'm25-public-m', 'SERVER', 'public',
    'public', 'M', false
);

INSERT INTO node (
    id, owner_id, name, device_type, provision_source,
    trust_domain, compute_tier_max, is_gate_runner
) VALUES (
    '00000000-0000-4000-8000-0000000000a2',
    '00000000-0000-4000-8000-000000000001',
    'm25-team-s', 'PHONE', 'team',
    'team', 'S', false
);

INSERT INTO agent (
    id, owner_id, name, version, status,
    manifest_hash, weights_format, weights_uri, weights_sha256
) VALUES (
    '00000000-0000-4000-8000-0000000000b1',
    '00000000-0000-4000-8000-000000000001',
    'm25-ungated', '0.0.0', 'ACTIVE',
    'm25', 'safetensors', 'file:///tmp/x.safetensors',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
);

INSERT INTO capability (
    id, code, version, name, description,
    input_schema, output_schema, output_kind,
    compute_tier, trust_domain_min, mvp_eligible,
    golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics
) VALUES (
    '00000000-0000-4000-8000-0000000000c1',
    'image.classify', 99,
    'm25-L-cap', 'violation fixture only',
    '{"type":"object"}'::jsonb,
    '{"type":"object"}'::jsonb,
    'closed_set_labels',
    'L', 'team', false,
    'm25', repeat('b', 64), 1,
    '{"primary_metric":"accuracy","min_accuracy":0.99}'::jsonb
);

SAVEPOINT m25_setup;
\echo TEST1 gate-ungated assignment
DO $$
BEGIN
    INSERT INTO assignment (
        task_id, agent_id, capability_id, node_id,
        task_trust_domain, node_trust_domain, capability_tier, node_tier_max,
        lease_expires_at, status
    ) VALUES (
        '00000000-0000-4000-8000-000000000040',
        '00000000-0000-4000-8000-0000000000b1',
        '00000000-0000-4000-8000-000000000010',
        '00000000-0000-4000-8000-000000000030',
        'team', 'team', 'M', 'M',
        now() + interval '60 seconds', 'LEASED'
    );
    RAISE EXCEPTION 'TEST1 UNEXPECTED SUCCESS';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'TEST1 REJECTED: %', SQLERRM;
END $$;

\echo TEST2 team task -> public node snapshots
DO $$
BEGIN
    INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen)
    SELECT a.id, '00000000-0000-4000-8000-0000000000a1'::uuid, 'BOUND', a.weights_sha256
      FROM agent a WHERE a.id = '00000000-0000-4000-8000-000000000020';
    INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256)
    SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen
      FROM agent_node an
      JOIN agent a ON a.id = an.agent_id AND a.weights_sha256 = an.weights_sha256_seen
     WHERE an.node_id = '00000000-0000-4000-8000-0000000000a1';

    INSERT INTO assignment (
        task_id, agent_id, capability_id, node_id,
        task_trust_domain, node_trust_domain, capability_tier, node_tier_max,
        lease_expires_at, status
    ) VALUES (
        '00000000-0000-4000-8000-000000000040',
        '00000000-0000-4000-8000-000000000020',
        '00000000-0000-4000-8000-000000000010',
        '00000000-0000-4000-8000-0000000000a1',
        'team', 'public', 'M', 'M',
        now() + interval '60 seconds', 'LEASED'
    );
    RAISE EXCEPTION 'TEST2 UNEXPECTED SUCCESS';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'TEST2 REJECTED: %', SQLERRM;
END $$;

\echo TEST3 L capability -> S node snapshots
DO $$
BEGIN
    INSERT INTO gate_run (
        id, agent_id, capability_id, runner_node_id, runner_is_gate_runner,
        status, golden_set_sha256, golden_score, cases_total, cases_passed, finished_at
    )
    SELECT '00000000-0000-4000-8000-0000000000e1'::uuid,
           a.id, c.id, n.id, n.is_gate_runner,
           'PASSED', c.golden_set_sha256, 0.99, 1, 1, now()
      FROM agent a
      JOIN capability c ON c.id = '00000000-0000-4000-8000-0000000000c1'
      JOIN node n ON n.id = '00000000-0000-4000-8000-000000000030' AND n.is_gate_runner
     WHERE a.id = '00000000-0000-4000-8000-000000000020';

    INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status)
    SELECT gr.id, gr.agent_id, gr.capability_id, gr.status
      FROM gate_run gr WHERE gr.id = '00000000-0000-4000-8000-0000000000e1';

    INSERT INTO agent_capability (agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at)
    SELECT grp.agent_id, grp.capability_id, 'PASSED', 0.99, grp.gate_run_id, now()
      FROM gate_run_passed grp WHERE grp.gate_run_id = '00000000-0000-4000-8000-0000000000e1';

    INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status)
    SELECT ac.agent_id, ac.capability_id, ac.gate_status
      FROM agent_capability ac
     WHERE ac.capability_id = '00000000-0000-4000-8000-0000000000c1';

    INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen)
    SELECT a.id, '00000000-0000-4000-8000-0000000000a2'::uuid, 'BOUND', a.weights_sha256
      FROM agent a WHERE a.id = '00000000-0000-4000-8000-000000000020';
    INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256)
    SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen
      FROM agent_node an
      JOIN agent a ON a.id = an.agent_id AND a.weights_sha256 = an.weights_sha256_seen
     WHERE an.node_id = '00000000-0000-4000-8000-0000000000a2';

    INSERT INTO task (
        id, user_id, capability_id, status, trust_domain,
        capability_trust_domain_min, input_ref
    )
    SELECT '00000000-0000-4000-8000-0000000000d2'::uuid,
           u.id, c.id, 'QUEUED', 'team', c.trust_domain_min, '{"datasetId":"eurosat-rgb","caseId":"m25-L"}'
      FROM app_user u
      JOIN capability c ON c.id = '00000000-0000-4000-8000-0000000000c1'
     WHERE u.id = '00000000-0000-4000-8000-000000000001';

    INSERT INTO assignment (
        task_id, agent_id, capability_id, node_id,
        task_trust_domain, node_trust_domain, capability_tier, node_tier_max,
        lease_expires_at, status
    ) VALUES (
        '00000000-0000-4000-8000-0000000000d2',
        '00000000-0000-4000-8000-000000000020',
        '00000000-0000-4000-8000-0000000000c1',
        '00000000-0000-4000-8000-0000000000a2',
        'team', 'team', 'L', 'S',
        now() + interval '60 seconds', 'LEASED'
    );
    RAISE EXCEPTION 'TEST3 UNEXPECTED SUCCESS';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'TEST3 REJECTED: %', SQLERRM;
END $$;

\echo TEST4 live lease then demote node tier
DO $$
DECLARE
    aid uuid;
BEGIN
    INSERT INTO task (
        id, user_id, capability_id, status, trust_domain,
        capability_trust_domain_min, input_ref
    )
    SELECT
        '00000000-0000-4000-8000-0000000000d1'::uuid,
        u.id, c.id, 'QUEUED', 'team',
        c.trust_domain_min,
        '{"datasetId":"eurosat-rgb","caseId":"m25-lease"}'
    FROM app_user u
    JOIN capability c ON c.id = '00000000-0000-4000-8000-000000000010'
    WHERE u.id = '00000000-0000-4000-8000-000000000001';

    INSERT INTO assignment (
        task_id, agent_id, capability_id, node_id,
        task_trust_domain, node_trust_domain, capability_tier, node_tier_max,
        lease_expires_at, status)
    SELECT t.id, acp.agent_id, c.id, n.id,
           t.trust_domain, n.trust_domain, c.compute_tier, n.compute_tier_max,
           now() + interval '60 seconds', 'LEASED'
      FROM task t
      JOIN capability c ON c.id = t.capability_id
      JOIN agent_capability_passed acp ON acp.capability_id = c.id
      JOIN agent_node_ready anr ON anr.agent_id = acp.agent_id
      JOIN node n ON n.id = anr.node_id
     WHERE t.id = '00000000-0000-4000-8000-0000000000d1'
     LIMIT 1
    RETURNING id INTO aid;

    IF aid IS NULL THEN
        RAISE EXCEPTION 'TEST4 setup claim failed';
    END IF;

    BEGIN
        UPDATE node
           SET compute_tier_max = 'S'
         WHERE id = '00000000-0000-4000-8000-000000000030';
        RAISE EXCEPTION 'TEST4 UNEXPECTED SUCCESS';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'TEST4 REJECTED: %', SQLERRM;
    END;
END $$;

\echo TEST5 READY live weight swap
DO $$
BEGIN
    UPDATE agent
       SET weights_sha256 = repeat('c', 64)
     WHERE id = '00000000-0000-4000-8000-000000000020';
    RAISE EXCEPTION 'TEST5 UNEXPECTED SUCCESS';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'TEST5 REJECTED: %', SQLERRM;
END $$;

\echo TEST6 invalidate PASSED gate_run
DO $$
BEGIN
    UPDATE gate_run
       SET status = 'FAILED'
     WHERE id = '00000000-0000-4000-8000-000000000031';
    RAISE EXCEPTION 'TEST6 UNEXPECTED SUCCESS';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'TEST6 REJECTED: %', SQLERRM;
END $$;

ROLLBACK;
\echo === M25 all 6 attempted (see NOTICE REJECTED lines) ===
