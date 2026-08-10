-- 0002 · 증적 드리프트 조회면 (읽기 전용 뷰 · 추가만)
--
-- 왜 필요한가
--   v제품-0 이 유통 카피로 보장하는 것은 「누가·무엇으로·언제 실행했는지 증적이 남고
--   **조회된다**」이다 (docs/design/product-distribution.md §2).
--   그런데 골든셋이 교체되면 `capability.golden_set_sha256` 만 바뀌고,
--   이미 발급된 PASS 증서(`agent_capability_passed`)는 **다른 골든셋에서 얻은 것**인데도
--   그대로 라우팅 가능 상태로 남는다. 지금 조회할 수단이 없다.
--
--   2026-08-10 홀드아웃 재추출이 정확히 이 상태를 만들었다.
--   커밋된 매니페스트의 정본 sha 는 c21d9ef7… 인데
--   `apps/core/sql/seed.sql` 의 capability 행은 여전히 c8254bcb…(구 누출 골든셋)이다.
--
-- 무엇을 하지 않는가
--   sha 를 고치지 않는다. 증서를 지우지 않는다. 라우팅을 막지 않는다.
--   그것들은 **재게이트 결정**을 동반해야 하므로 사람이 정한다 (절대규칙 8 · D15).
--   이 마이그레이션은 「보이게」만 한다.

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
    -- 이 gate_run 에 기대어 지금도 라우팅 가능한 증서가 있는가
    EXISTS (
        SELECT 1
        FROM agent_capability ac
        JOIN agent_capability_passed acp
          ON acp.agent_id = ac.agent_id
         AND acp.capability_id = ac.capability_id
        WHERE ac.gate_run_id = gr.id
    )                           AS still_routable
FROM gate_run gr
JOIN capability c ON c.id = gr.capability_id
JOIN agent a      ON a.id = gr.agent_id
WHERE gr.golden_set_sha256 IS DISTINCT FROM c.golden_set_sha256;

COMMENT ON VIEW provenance_drift IS
    'gate_run 이 스냅샷한 골든셋 sha 와 capability 의 현재 sha 가 다른 행. '
    'still_routable=true 면 다른 골든셋에서 얻은 증서로 지금도 배정이 된다는 뜻이다. '
    'SD-007 · D15 Provenance by Design.';

-- 골든셋이 바뀌었는데 아무도 모르는 상태를 막는 요약. 운영자가 한 줄로 본다.
CREATE OR REPLACE VIEW provenance_drift_summary AS
SELECT
    capability_code,
    capability_version,
    capability_golden_sha256,
    count(*)                                        AS drifted_gate_runs,
    count(*) FILTER (WHERE still_routable)          AS drifted_still_routable,
    min(finished_at)                                AS oldest,
    max(finished_at)                                AS newest
FROM provenance_drift
GROUP BY 1, 2, 3;

COMMENT ON VIEW provenance_drift_summary IS
    'capability 별 증적 드리프트 요약. drifted_still_routable > 0 이면 재게이트 대상이다.';
