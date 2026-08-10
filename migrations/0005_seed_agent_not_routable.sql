-- 0005 · seed-agent 의 라우팅 증서를 끊는다 (SD-015)
--
-- 무엇이 문제였나
--   `seed-agent` 의 가중치는 `placeholder.safetensors` 다. Node 가 그것을 감지해 dummy 모드로 답한다.
--   즉 이 Agent 는 **실게이트를 통과할 수 없다** — 로드조차 되지 않는다 (safetensors 키가 다르다).
--   그런데 seed 가 라우팅 가능 증서를 발급해 뒀고, UUID 가 가장 낮아
--   claim 정렬(`ORDER BY acp.agent_id, n.id`)에서 **1순위**였다.
--
--   그래서 `requestedAgentId` 없이 들어온 Task 는 이 Agent 로 가서 `dummy:true` 라벨을 받고
--   **COMPLETED 로 기록**됐다. 실측: 이 볼륨에 그런 assignment 이 5건 SUCCEEDED 로 남아 있다.
--   증적에 dummy 플래그는 남으므로 「증적이 남는다」는 보장은 지켜졌지만,
--   `label` 만 읽는 사용자에게는 지어낸 답이다. 그리고 제품 경로는
--   「모델 이름이 아니라 Capability 로 요청한다」(product-distribution §4)이므로 정면으로 닿는다.
--
-- 왜 삭제가 아닌가
--   0004 와 같은 이유다 — `assignment` 이 FK 로 참조한다 (이 볼륨에 6건). 삭제는 불가능하고,
--   가능하더라도 실행을 인가한 증서를 지우면 그 실행의 증적이 끊긴다 (D15).
--
-- 왜 revoked_gate_run_id 가 NULL 인가
--   **근거가 될 FAILED gate_run 을 만들 수 없기 때문이다.** placeholder 는 채점기가 로드하지 못해
--   FAILED 점수가 아니라 오류가 난다. 이건 「기준에 못 미쳤다」가 아니라
--   「애초에 게이트에 올릴 수 없는 것에 증서가 발급돼 있었다」는 시드 결함이다.
--
--   운영 폐기 경로(`POST /v1/internal/agent-capabilities/revoke`)의 근거 규칙은 그대로다 —
--   그쪽은 여전히 현재 골든셋의 FAILED gate_run 을 요구한다. 이 마이그레이션은
--   시드가 만든 잘못된 상태를 되돌리는 **일회성 정정**이고, 그 사실을 reason 에 적는다.
--
-- 새 볼륨
--   `apps/core/sql/seed.sql` 이 이제 이 증서를 만들지 않는다. 그래서 새 볼륨에서는 이 UPDATE 가 0건이다.

UPDATE agent_capability_passed
   SET revoked_at = now(),
       revoked_reason =
           'SD-015 시드 결함 정정: placeholder 가중치라 실게이트가 원리적으로 불가능한 Agent 에 '
           '라우팅 증서가 발급돼 있었다. claim 1순위였고 requestedAgentId 없는 Task 가 '
           'dummy 라벨을 COMPLETED 로 받았다. 근거 gate_run 은 만들 수 없다(로드 불가).'
 WHERE agent_id = '00000000-0000-4000-8000-000000000020'
   AND revoked_at IS NULL;

DO $$
DECLARE
    live INT;
BEGIN
    SELECT count(*) INTO live
      FROM agent_capability_passed acp
      JOIN agent a ON a.id = acp.agent_id
     WHERE acp.revoked_at IS NULL
       AND a.weights_sha256 = '5cd21e43471e2d0a495ce5cee3aae102cbdbd98c7f0db770a74476268b3a3887';

    IF live > 0 THEN
        RAISE EXCEPTION 'placeholder 가중치 Agent 에 라우팅 증서가 아직 % 건 남아 있다', live;
    END IF;

    RAISE NOTICE 'placeholder 가중치 Agent 는 더 이상 라우팅되지 않는다 (SD-015).';
END $$;
