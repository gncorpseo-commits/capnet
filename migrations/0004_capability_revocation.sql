-- 0004 · 능력 증서 폐기 경로 (SD-014)
--
-- 무엇이 없었나
--   재게이트가 FAILED 여도 기존 PASSED 증서가 살아남았다.
--   `gate.py` UPSERT_AC_FAILED_SQL 의 `WHERE agent_capability.gate_status <> 'PASSED'` 때문이다.
--   그 가드 자체는 **의도된 방어**다 — 잘못된 게이트 한 번이 운영 라우팅을 죽이면 안 된다.
--   진짜 공백은 「폐기할 방법이 아예 없다」는 것이었다.
--
-- 왜 삭제가 아닌가
--   `assignment` 가 `agent_capability_passed (agent_id, capability_id)` 를 FK 로 참조한다.
--   한 번이라도 실행된 Agent 의 증서는 **삭제 자체가 불가능**하다. 이건 버그가 아니라
--   증적 보장이다 — 실행을 인가한 증서를 지울 수 없다 (D15).
--   그래서 폐기는 **행 삭제가 아니라 표시**로 한다. 사슬은 그대로 두고 라우팅만 끊는다.
--
-- 같이 메우는 구멍
--   `agent.status` 는 스키마에 ACTIVE/DISABLED/DELETED 로 선언돼 있는데
--   `CLAIM_SQL` 이 전혀 보지 않았다. 선언만 있고 강제가 없는 상태 — SD-010 과 같은 계열이다.
--   claim 이 이 마이그레이션과 함께 `status='ACTIVE'` 를 요구하도록 바뀐다.
--
-- 오늘 동작은 바뀌지 않는다
--   기존 행은 전부 revoked_at IS NULL 이고, 실 DB 의 agent 는 41건 전부 ACTIVE 다.
--   폐기를 실제로 부르기 전까지 라우팅 결과는 동일하다.

ALTER TABLE agent_capability_passed
    ADD COLUMN IF NOT EXISTS revoked_at          TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS revoked_reason      TEXT,
    ADD COLUMN IF NOT EXISTS revoked_gate_run_id UUID REFERENCES gate_run (id);

-- 이유 없는 폐기를 남기지 않는다. 왜 끊었는지가 증적의 일부다.
ALTER TABLE agent_capability_passed
    ADD CONSTRAINT ck_acp_revoked_needs_reason
    CHECK (revoked_at IS NULL OR revoked_reason IS NOT NULL);

-- 라우팅 후보는 살아 있는 증서뿐이다. claim 이 이 조건으로 고른다.
CREATE INDEX IF NOT EXISTS agent_capability_passed_live_idx
    ON agent_capability_passed (capability_id, agent_id)
    WHERE revoked_at IS NULL;

COMMENT ON COLUMN agent_capability_passed.revoked_at IS
    '폐기 시각. NULL 이면 라우팅 가능. 행은 지우지 않는다 — assignment 가 FK 로 참조한다 (D15).';
COMMENT ON COLUMN agent_capability_passed.revoked_gate_run_id IS
    '폐기 근거가 된 FAILED gate_run. 근거 없는 폐기를 막기 위해 Core 가 채운다.';

-- 드리프트 뷰도 폐기를 반영한다. 폐기된 증서는 「지금도 라우팅된다」가 아니다.
-- 0002 와 같은 컬럼·순서를 유지한다 (CREATE OR REPLACE 제약).
CREATE OR REPLACE VIEW provenance_drift AS
SELECT
    gr.id                       AS gate_run_id,
    gr.agent_id,
    a.name                      AS agent_name,
    gr.capability_id,
    c.code                      AS capability_code,
    c.version                   AS capability_version,
    gr.status                   AS gate_status,
    gr.golden_set_sha256        AS gate_run_golden_sha256,
    c.golden_set_sha256         AS capability_golden_sha256,
    gr.golden_score,
    gr.finished_at,
    EXISTS (
        SELECT 1
        FROM agent_capability ac
        JOIN agent_capability_passed acp
          ON acp.agent_id = ac.agent_id
         AND acp.capability_id = ac.capability_id
        WHERE ac.gate_run_id = gr.id
          AND acp.revoked_at IS NULL          -- 0004: 폐기된 증서는 라우팅되지 않는다
    )                           AS still_routable
FROM gate_run gr
JOIN capability c ON c.id = gr.capability_id
JOIN agent a      ON a.id = gr.agent_id
WHERE gr.golden_set_sha256 IS DISTINCT FROM c.golden_set_sha256;

-- 폐기 이력 조회면. 무엇을 왜 언제 끊었는지가 한 줄로 보여야 한다.
CREATE OR REPLACE VIEW revoked_capability AS
SELECT
    acp.agent_id,
    a.name              AS agent_name,
    acp.capability_id,
    c.code              AS capability_code,
    c.version           AS capability_version,
    acp.revoked_at,
    acp.revoked_reason,
    acp.revoked_gate_run_id,
    gr.golden_score     AS evidence_score,
    gr.golden_set_sha256 AS evidence_golden_sha256
FROM agent_capability_passed acp
JOIN agent a       ON a.id = acp.agent_id
JOIN capability c  ON c.id = acp.capability_id
LEFT JOIN gate_run gr ON gr.id = acp.revoked_gate_run_id
WHERE acp.revoked_at IS NOT NULL;

COMMENT ON VIEW revoked_capability IS
    '폐기된 능력 증서와 그 근거. 행은 남아 있고 라우팅만 끊긴 상태다 (SD-014).';
