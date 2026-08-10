-- 0003 · capability.golden_set_sha256 을 홀드아웃 매니페스트 정본으로 맞춘다 (SD-013)
--
-- 무엇
--   image.classify@1 의 golden_set_sha256 을
--     c8254bcb…(재추출 전 · 누출 골든셋)  →  c21d9ef7…(커밋된 홀드아웃 매니페스트 재계산값)
--   으로 올린다. `apps/core/sql/seed.sql` 은 새 볼륨에만 적용되므로 기존 볼륨은 이 경로로만 올라간다.
--
-- 왜
--   2026-08-10 홀드아웃 재추출(#26)에서 매니페스트만 교체되고 선언부가 따라오지 않았다.
--   그 결과 capability 행이 **리포에 없는 골든셋**을 가리켰다 (D15 Provenance by Design 위반).
--   사슬은 self-consistent 라서 데모는 통과한다 — 조용히 틀린다.
--   정본 재계산: `python3 scripts/check_golden_sha.py --print`
--
-- 무엇을 하지 않는가
--   **증서를 지우지 않는다.** 이 UPDATE 이후, 구 골든셋에서 PASS 를 받은 Agent 는
--   `agent_capability_passed` 에 그대로 남아 라우팅 가능하다. 그것은 재게이트로 푸는 문제이고,
--   삭제는 절대규칙 8·D15 상 사람이 정한다. 대신 0002 의 `provenance_drift` 로 보이게 하고,
--   아래 RAISE NOTICE 가 적용 즉시 건수를 알린다.
--
-- 안전
--   capability 에는 UNIQUE (id, golden_set_sha256) 이 없다 — 이 컬럼을 겨냥한 복합 FK 가 없으므로
--   UPDATE 가 기존 gate_run·task 스냅샷의 FK 를 깨지 않는다.
--   (UNIQUE (id, compute_tier) · UNIQUE (id, trust_domain_min) 만 복합 FK 대상이다.)
--   구 값에 한정해 갱신하므로 재실행해도 0건이 되고, 이미 정본이면 아무것도 하지 않는다.

UPDATE capability
   SET golden_set_sha256 = 'c21d9ef796e2165e27926358981489fe397a639d7c0ceb0d01b74846da6b0eef'
 WHERE code = 'image.classify'
   AND version = 1
   AND golden_set_sha256 = 'c8254bcb454d6ca362f61c0426e4a7c9c7de42cc81fa6ab3ed097b64c2862066';

-- 남은 드리프트를 적용 순간에 알린다. 조용히 넘어가지 않게 한다.
DO $$
DECLARE
    drifted   INT;
    routable  INT;
BEGIN
    SELECT count(*), count(*) FILTER (WHERE still_routable)
      INTO drifted, routable
      FROM provenance_drift;

    IF drifted > 0 THEN
        RAISE NOTICE '증적 드리프트 % 건 (라우팅 가능 % 건). 구 골든셋에서 얻은 PASS 증서다.', drifted, routable;
        RAISE NOTICE '조회: SELECT * FROM provenance_drift_summary;';
        RAISE NOTICE '재게이트 전까지 그 증서는 다른 골든셋 기준이다 — SD-013.';
    ELSE
        RAISE NOTICE '증적 드리프트 없음.';
    END IF;
END $$;
