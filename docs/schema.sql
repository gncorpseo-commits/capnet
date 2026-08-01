-- Capability Network (CapNet) — MVP schema (v4.4)
-- PostgreSQL 14+ / 16
-- v4.3 + gate chain integrity + capability.trust_domain_min on task
-- (no triggers)

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ===========================================================================
-- LOOKUPS — ordered ranks (TEXT sort is wrong: 'L' < 'M' < 'S' alphabetically)
-- ===========================================================================

CREATE TABLE compute_tier_rank (
    tier        TEXT PRIMARY KEY CHECK (tier IN ('S', 'M', 'L')),
    rank        INT  NOT NULL UNIQUE CHECK (rank BETWEEN 1 AND 3),
    UNIQUE (tier, rank)
);

INSERT INTO compute_tier_rank (tier, rank) VALUES
    ('S', 1),
    ('M', 2),
    ('L', 3);

-- Higher privacy_rank = more private. Assign iff node.privacy >= task.privacy
CREATE TABLE trust_domain_rank (
    domain          TEXT PRIMARY KEY CHECK (domain IN ('team', 'tenant', 'public')),
    privacy_rank    INT  NOT NULL UNIQUE CHECK (privacy_rank BETWEEN 1 AND 3),
    UNIQUE (domain, privacy_rank)
);

INSERT INTO trust_domain_rank (domain, privacy_rank) VALUES
    ('public', 1),
    ('tenant', 2),
    ('team',   3);

-- Compatible pairs only (matrix = policy). Rows MUST match rank order (v4.3).
CREATE TABLE tier_compatible (
    capability_tier     TEXT NOT NULL,
    node_tier_max       TEXT NOT NULL,
    capability_rank     INT  NOT NULL,
    node_rank           INT  NOT NULL,
    PRIMARY KEY (capability_tier, node_tier_max),
    FOREIGN KEY (capability_tier, capability_rank)
        REFERENCES compute_tier_rank (tier, rank),
    FOREIGN KEY (node_tier_max, node_rank)
        REFERENCES compute_tier_rank (tier, rank),
    CHECK (capability_rank <= node_rank)
);

INSERT INTO tier_compatible (capability_tier, node_tier_max, capability_rank, node_rank)
SELECT c.tier, n.tier, c.rank, n.rank
FROM compute_tier_rank c
JOIN compute_tier_rank n ON c.rank <= n.rank;

CREATE TABLE domain_compatible (
    task_domain         TEXT NOT NULL,
    node_domain         TEXT NOT NULL,
    task_privacy_rank   INT  NOT NULL,
    node_privacy_rank   INT  NOT NULL,
    PRIMARY KEY (task_domain, node_domain),
    FOREIGN KEY (task_domain, task_privacy_rank)
        REFERENCES trust_domain_rank (domain, privacy_rank),
    FOREIGN KEY (node_domain, node_privacy_rank)
        REFERENCES trust_domain_rank (domain, privacy_rank),
    CHECK (node_privacy_rank >= task_privacy_rank)
);

INSERT INTO domain_compatible (task_domain, node_domain, task_privacy_rank, node_privacy_rank)
SELECT t.domain, n.domain, t.privacy_rank, n.privacy_rank
FROM trust_domain_rank t
JOIN trust_domain_rank n ON n.privacy_rank >= t.privacy_rank;

-- Task may use a capability only if task.privacy_rank >= capability.trust_domain_min
CREATE TABLE domain_min_compatible (
    min_domain          TEXT NOT NULL,
    task_domain         TEXT NOT NULL,
    min_privacy_rank    INT  NOT NULL,
    task_privacy_rank   INT  NOT NULL,
    PRIMARY KEY (min_domain, task_domain),
    FOREIGN KEY (min_domain, min_privacy_rank)
        REFERENCES trust_domain_rank (domain, privacy_rank),
    FOREIGN KEY (task_domain, task_privacy_rank)
        REFERENCES trust_domain_rank (domain, privacy_rank),
    CHECK (task_privacy_rank >= min_privacy_rank)
);

INSERT INTO domain_min_compatible (min_domain, task_domain, min_privacy_rank, task_privacy_rank)
SELECT m.domain, t.domain, m.privacy_rank, t.privacy_rank
FROM trust_domain_rank m
JOIN trust_domain_rank t ON t.privacy_rank >= m.privacy_rank;

-- ===========================================================================
-- USER + API keys
-- ===========================================================================

CREATE TABLE app_user (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('user', 'developer', 'admin')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE api_key (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES app_user(id),
    key_prefix      TEXT NOT NULL,
    key_hash        BYTEA NOT NULL,
    label           TEXT,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX api_key_prefix_idx ON api_key (key_prefix) WHERE revoked_at IS NULL;

-- ===========================================================================
-- CAPABILITY
-- ===========================================================================

CREATE TABLE capability (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code                TEXT NOT NULL,
    version             INT  NOT NULL,
    name                TEXT NOT NULL,
    description         TEXT,
    input_schema        JSONB NOT NULL,
    output_schema       JSONB NOT NULL,
    output_kind         TEXT NOT NULL CHECK (output_kind IN (
                            'closed_set_labels', 'structured', 'freeform'
                        )),
    compute_tier        TEXT NOT NULL REFERENCES compute_tier_rank (tier),
    trust_domain_min    TEXT NOT NULL REFERENCES trust_domain_rank (domain)
                            DEFAULT 'team',
    mvp_eligible        BOOLEAN NOT NULL DEFAULT false,
    golden_set_ref      TEXT NOT NULL,
    golden_set_sha256   TEXT NOT NULL,
    golden_set_size     INT  NOT NULL CHECK (golden_set_size > 0),
    golden_metrics      JSONB NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (code, version),
    UNIQUE (id, compute_tier),
    UNIQUE (id, trust_domain_min),
    CONSTRAINT ck_capability_mvp_scoreable
        CHECK (NOT mvp_eligible OR output_kind = 'closed_set_labels')
);

-- ===========================================================================
-- AGENT
-- ===========================================================================

CREATE TABLE agent (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id            UUID NOT NULL REFERENCES app_user(id),
    name                TEXT NOT NULL,
    version             TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN (
                            'ACTIVE', 'DISABLED', 'DELETED'
                        )) DEFAULT 'ACTIVE',
    manifest_hash       TEXT NOT NULL,
    weights_format      TEXT NOT NULL CHECK (weights_format = 'safetensors'),
    weights_uri         TEXT NOT NULL,
    weights_sha256      TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, weights_sha256)
);

-- ===========================================================================
-- NODE (before gate_run — runner must be a team gate-runner)
-- ===========================================================================

CREATE TABLE node (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id                UUID NOT NULL REFERENCES app_user(id),
    name                    TEXT NOT NULL,
    device_type             TEXT NOT NULL CHECK (device_type IN (
                                'PC_GPU', 'PHONE', 'SERVER'
                            )),
    gpu                     TEXT,
    provision_source        TEXT NOT NULL CHECK (provision_source IN (
                                'team', 'invited', 'public'
                            )),
    trust_domain            TEXT NOT NULL REFERENCES trust_domain_rank (domain)
                                DEFAULT 'team',
    compute_tier_max        TEXT NOT NULL REFERENCES compute_tier_rank (tier)
                                DEFAULT 'M',
    is_gate_runner          BOOLEAN NOT NULL DEFAULT false,
    heartbeat_timeout_s     INT NOT NULL DEFAULT 45 CHECK (heartbeat_timeout_s > 0),
    availability_policy     JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_gate_runner_team
        CHECK (NOT is_gate_runner OR provision_source = 'team'),
    CONSTRAINT ck_trust_provision_align
        CHECK (
            (trust_domain = 'team'   AND provision_source = 'team')
         OR (trust_domain = 'tenant' AND provision_source IN ('team', 'invited'))
         OR (trust_domain = 'public')
        ),
    UNIQUE (id, trust_domain, compute_tier_max),
    -- composite FK target: gate_run may only cite a gate-runner node
    UNIQUE (id, is_gate_runner)
);

-- ===========================================================================
-- GATE_RUN + AGENT_CAPABILITY + PASSED projections (composite FK targets)
-- ===========================================================================

CREATE TABLE gate_run (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id                UUID NOT NULL REFERENCES agent(id),
    capability_id           UUID NOT NULL REFERENCES capability(id),
    runner_node_id          UUID NOT NULL,
    runner_is_gate_runner   BOOLEAN NOT NULL DEFAULT true
                                CHECK (runner_is_gate_runner),
    status                  TEXT NOT NULL CHECK (status IN (
                                'RUNNING', 'PASSED', 'FAILED', 'ERROR'
                            )),
    golden_set_sha256       TEXT NOT NULL,
    golden_score            NUMERIC,
    cases_total             INT,
    cases_passed            INT,
    result_summary          JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at             TIMESTAMPTZ,
    -- composite FK target for gate_run_passed
    UNIQUE (id, agent_id, capability_id, status),
    FOREIGN KEY (runner_node_id, runner_is_gate_runner)
        REFERENCES node (id, is_gate_runner)
);

-- Certificate: only PASSED runs that already satisfied runner FK may mint capability PASS.
CREATE TABLE gate_run_passed (
    gate_run_id         UUID PRIMARY KEY,
    agent_id            UUID NOT NULL,
    capability_id       UUID NOT NULL,
    status              TEXT NOT NULL DEFAULT 'PASSED'
                            CHECK (status = 'PASSED'),
    UNIQUE (gate_run_id, agent_id, capability_id, status),
    FOREIGN KEY (gate_run_id, agent_id, capability_id, status)
        REFERENCES gate_run (id, agent_id, capability_id, status)
);

CREATE TABLE agent_capability (
    agent_id            UUID NOT NULL REFERENCES agent(id) ON DELETE CASCADE,
    capability_id       UUID NOT NULL REFERENCES capability(id),
    gate_status         TEXT NOT NULL CHECK (gate_status IN (
                            'PENDING', 'PASSED', 'FAILED'
                        )) DEFAULT 'PENDING',
    golden_score        NUMERIC,
    -- non-null only when PASSED; FK to gate_run_passed pins agent+capability+PASSED
    gate_run_id         UUID,
    gated_at            TIMESTAMPTZ,
    PRIMARY KEY (agent_id, capability_id),
    UNIQUE (agent_id, capability_id, gate_status),
    CONSTRAINT ck_ac_run_only_when_passed CHECK (
        (gate_status = 'PASSED' AND gate_run_id IS NOT NULL)
        OR (gate_status <> 'PASSED' AND gate_run_id IS NULL)
    ),
    FOREIGN KEY (gate_run_id, agent_id, capability_id, gate_status)
        REFERENCES gate_run_passed (gate_run_id, agent_id, capability_id, status)
);

-- Routable only when this row exists. Insert requires parent gate_status='PASSED'.
CREATE TABLE agent_capability_passed (
    agent_id            UUID NOT NULL,
    capability_id       UUID NOT NULL,
    gate_status         TEXT NOT NULL DEFAULT 'PASSED'
                            CHECK (gate_status = 'PASSED'),
    PRIMARY KEY (agent_id, capability_id),
    FOREIGN KEY (agent_id, capability_id, gate_status)
        REFERENCES agent_capability (agent_id, capability_id, gate_status)
);

CREATE INDEX agent_capability_routable_idx
    ON agent_capability (capability_id)
    WHERE gate_status = 'PASSED';

CREATE TABLE agent_node (
    agent_id                UUID NOT NULL REFERENCES agent(id) ON DELETE CASCADE,
    node_id                 UUID NOT NULL REFERENCES node(id) ON DELETE CASCADE,
    bind_status             TEXT NOT NULL DEFAULT 'BOUND' CHECK (bind_status IN (
                                'BOUND', 'FAILED', 'UNBOUND'
                            )),
    weights_sha256_seen     TEXT NOT NULL,
    PRIMARY KEY (agent_id, node_id),
    UNIQUE (agent_id, node_id, bind_status),
    UNIQUE (agent_id, node_id, bind_status, weights_sha256_seen)
);

-- READY = BOUND + digest equals agent.weights_sha256 (both FKs).
CREATE TABLE agent_node_ready (
    agent_id                UUID NOT NULL,
    node_id                 UUID NOT NULL,
    bind_status             TEXT NOT NULL DEFAULT 'BOUND'
                                CHECK (bind_status = 'BOUND'),
    weights_sha256          TEXT NOT NULL,
    PRIMARY KEY (agent_id, node_id),
    FOREIGN KEY (agent_id, node_id, bind_status, weights_sha256)
        REFERENCES agent_node (agent_id, node_id, bind_status, weights_sha256_seen),
    FOREIGN KEY (agent_id, weights_sha256)
        REFERENCES agent (id, weights_sha256)
);

CREATE TABLE node_session (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id         UUID NOT NULL REFERENCES node(id) ON DELETE CASCADE,
    ws_connected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_heartbeat  TIMESTAMPTZ NOT NULL DEFAULT now(),
    availability    TEXT NOT NULL CHECK (availability IN (
                        'AVAILABLE', 'BUSY', 'DRAINING', 'OFFLINE'
                    )),
    metrics         JSONB,
    closed_at       TIMESTAMPTZ
);

CREATE INDEX node_session_alive_idx
    ON node_session (node_id, last_heartbeat DESC)
    WHERE closed_at IS NULL;

CREATE OR REPLACE VIEW node_liveness AS
SELECT
    n.id AS node_id,
    s.availability,
    s.last_heartbeat,
    n.heartbeat_timeout_s,
    (s.closed_at IS NULL
        AND s.last_heartbeat > now() - make_interval(secs => n.heartbeat_timeout_s)
    ) AS is_fresh
FROM node n
LEFT JOIN LATERAL (
    SELECT * FROM node_session ns
    WHERE ns.node_id = n.id AND ns.closed_at IS NULL
    ORDER BY ns.last_heartbeat DESC
    LIMIT 1
) s ON TRUE;

-- ===========================================================================
-- TASK + ASSIGNMENT (routing invariants enforced by composite FKs)
-- ===========================================================================

CREATE TABLE task (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                     UUID NOT NULL REFERENCES app_user(id),
    capability_id               UUID NOT NULL,
    status                      TEXT NOT NULL CHECK (status IN (
                                    'CREATED', 'QUEUED', 'ASSIGNED', 'RUNNING',
                                    'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELED'
                                )),
    trust_domain                TEXT NOT NULL REFERENCES trust_domain_rank (domain)
                                    DEFAULT 'team',
    -- snapshot of capability.trust_domain_min; must satisfy domain_min_compatible
    capability_trust_domain_min TEXT NOT NULL,
    input_ref                   TEXT,
    result_ref                  TEXT,
    current_assignment_id       UUID,
    requested_agent_id          UUID REFERENCES agent(id),
    proof_run_id                UUID,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, trust_domain),
    UNIQUE (id, capability_id),
    UNIQUE (id, capability_id, trust_domain),
    FOREIGN KEY (capability_id, capability_trust_domain_min)
        REFERENCES capability (id, trust_domain_min),
    FOREIGN KEY (capability_trust_domain_min, trust_domain)
        REFERENCES domain_min_compatible (min_domain, task_domain)
);

CREATE INDEX task_queued_by_capability_idx
    ON task (capability_id, created_at)
    WHERE status = 'QUEUED';

CREATE TABLE assignment (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id                 UUID NOT NULL,
    agent_id                UUID NOT NULL,
    capability_id           UUID NOT NULL,
    node_id                 UUID NOT NULL,
    task_trust_domain       TEXT NOT NULL,
    node_trust_domain       TEXT NOT NULL,
    capability_tier         TEXT NOT NULL,
    node_tier_max           TEXT NOT NULL,
    session_id              UUID REFERENCES node_session(id),
    lease_expires_at        TIMESTAMPTZ NOT NULL,
    status                  TEXT NOT NULL CHECK (status IN (
                                'LEASED', 'RUNNING', 'SUCCEEDED', 'FAILED',
                                'EXPIRED', 'SUPERSEDED'
                            )),
    attempt_no              INT NOT NULL DEFAULT 1,
    duration_ms             INT,
    vram_mb_peak            INT,
    energy_wh               NUMERIC,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at             TIMESTAMPTZ,

    FOREIGN KEY (task_id, capability_id, task_trust_domain)
        REFERENCES task (id, capability_id, trust_domain),

    FOREIGN KEY (capability_id, capability_tier)
        REFERENCES capability (id, compute_tier),

    FOREIGN KEY (agent_id, capability_id)
        REFERENCES agent_capability_passed (agent_id, capability_id),

    FOREIGN KEY (agent_id, node_id)
        REFERENCES agent_node_ready (agent_id, node_id),

    FOREIGN KEY (node_id, node_trust_domain, node_tier_max)
        REFERENCES node (id, trust_domain, compute_tier_max),

    FOREIGN KEY (capability_tier, node_tier_max)
        REFERENCES tier_compatible (capability_tier, node_tier_max),

    FOREIGN KEY (task_trust_domain, node_trust_domain)
        REFERENCES domain_compatible (task_domain, node_domain)
);

CREATE INDEX assignment_task_idx ON assignment (task_id, attempt_no);

CREATE UNIQUE INDEX assignment_one_live_per_task
    ON assignment (task_id)
    WHERE status IN ('LEASED', 'RUNNING');

ALTER TABLE task
    ADD CONSTRAINT task_current_assignment_fk
    FOREIGN KEY (current_assignment_id) REFERENCES assignment(id);

-- Claim: Core worker only. Snapshots must equal source rows or FK fails.
-- Gate chain: PASSED capability requires gate_run_passed ← team gate-runner.

-- ===========================================================================
-- AUDIT_LOG
-- ===========================================================================

CREATE TABLE audit_log (
    id          BIGSERIAL,
    at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    task_id     UUID,
    actor_type  TEXT,
    event       TEXT NOT NULL,
    payload     JSONB,
    PRIMARY KEY (id, at)
) PARTITION BY RANGE (at);

CREATE TABLE audit_log_default PARTITION OF audit_log DEFAULT;

CREATE INDEX audit_log_task_idx ON audit_log (task_id, at);

CREATE OR REPLACE FUNCTION ensure_audit_partition(p_month DATE DEFAULT date_trunc('month', now())::date)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    start_ts TIMESTAMPTZ := p_month;
    end_ts   TIMESTAMPTZ := (p_month + INTERVAL '1 month');
    part_name TEXT := format('audit_log_%s', to_char(p_month, 'YYYY_MM'));
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_log
         FOR VALUES FROM (%L) TO (%L)',
        part_name, start_ts, end_ts
    );
END;
$$;

SELECT ensure_audit_partition(date_trunc('month', now())::date);
SELECT ensure_audit_partition((date_trunc('month', now()) + INTERVAL '1 month')::date);

COMMIT;

-- ---------------------------------------------------------------------------
-- Expected FK rejections:
-- A) Honest wrong combos (v4.1 — 6 classes)
-- 1) PENDING agent  2) tenant/public domain  3) L→S tier
-- 4) TEXT 'L'<='S' trap  5) node demotion under lease  6) unbound node
-- B) Lying / stale snapshots (v4.2)
-- 7) task is team but snapshot task_trust_domain=public
-- 8) capability is L but snapshot capability_tier=S
-- 9) weights_sha256_seen ≠ agent.weights_sha256 → cannot enter agent_node_ready
-- C) Matrix poison (v4.3)
-- 11) domain_compatible ('team','public')  12) tier_compatible ('L','S')
-- D) Gate chain / trust_domain_min (v4.4)
-- 13) gate_run PASSED without team gate-runner (null runner / non-runner node)
-- 14) agent_capability PASSED without gate_run_passed (null / forged gate_run_id)
-- 15) task.trust_domain below capability.trust_domain_min (e.g. public task, min=team)
-- ---------------------------------------------------------------------------
