-- 0006 · tenant 신뢰 경계 운용 (P2-1 · D19)
--
-- 무엇
--   `tenant` 도메인을 **실제로 쓸 수 있게** 만든다. 스키마는 v4.4 부터 이미 tenant 를 알고 있었다
--   (`trust_domain_rank` · `domain_compatible`). 없던 것은 **운용 데이터**다.
--   DDL 을 추가하지 않는다 — 행만 넣는다. 로드맵 §3 P2-1 이 말한 그대로다.
--
-- 왜 새 capability 가 필요한가 (로드맵이 놓친 것)
--   로드맵 P2-1 은 「스키마에 이미 있음 · DDL 추가가 아니라 운용」이라고만 적었다.
--   실제로 해 보면 한 칸이 더 있다.
--
--   `domain_min_compatible` 은 **task 의 privacy_rank 가 capability.trust_domain_min 이상**일 것을 요구한다.
--   순위는 public=1 < tenant=2 < team=3 이고, `image.classify@1` 의 min 은 `team`(3) 이다.
--   즉 tenant Task(2) 는 그 capability 를 **원천적으로 쓸 수 없다**. 노드를 아무리 넣어도 안 된다.
--
--   그래서 tenant 유통에는 `trust_domain_min <= tenant` 인 capability 가 **선행**한다.
--   기존 계약을 낮추지 않는다 — 출품 데모의 계약을 건드리면 안 된다. 새 계약을 추가한다.
--
-- 무엇을 하지 않는가
--   - `image.classify@1` 의 `trust_domain_min` 을 낮추지 않는다 (출품 트랙 불변)
--   - Agent 를 게이트하지 않는다. 게이트는 team gate-runner 에서 실행으로만 한다 (절대규칙 8).
--     이 마이그레이션은 **경계와 계약**만 놓는다
--   - 경제·정산과 무관하다 (D19 — 경제는 선택·비기초)
--
-- 유통 세대
--   product-distribution §3: tenant = 「조직 허용 데이터 · 초대·조직 플릿」.
--   이 마이그레이션은 v제품-1 의 전제 한 칸이다. 신원(node_credential · SD-002)은 아직이다.

-- 1) tenant 플릿 노드 — 초대된 조직 기기 (provision_source='invited')
--    ck_trust_provision_align: tenant 는 team|invited 만 허용한다.
INSERT INTO node (id, owner_id, name, device_type, provision_source,
                  trust_domain, compute_tier_max, is_gate_runner)
SELECT '00000000-0000-4000-8000-000000000050', u.id,
       'tenant-fleet-1', 'PC_GPU', 'invited', 'tenant', 'M', false
  FROM app_user u WHERE u.id = '00000000-0000-4000-8000-000000000001'
ON CONFLICT (id) DO NOTHING;

-- 2) tenant 가 쓸 수 있는 계약.
--    골든셋은 image.classify@1 과 **같은 것**을 쓴다 — 같은 계약 내용, 다른 신뢰 정책이다.
--    (같은 매니페스트를 가리키므로 check_golden_sha.py 의 정합 규칙도 그대로 유지된다.)
INSERT INTO capability (
    id, code, version, name, description,
    input_schema, output_schema, output_kind,
    compute_tier, trust_domain_min, mvp_eligible,
    golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics
)
SELECT '00000000-0000-4000-8000-000000000011',
       'image.classify', 2,
       'EuroSAT land-cover classify (tenant)',
       'image.classify@1 과 같은 계약. trust_domain_min 만 tenant — 조직 허용 데이터용 (P2-1 · D19)',
       c.input_schema, c.output_schema, c.output_kind,
       c.compute_tier, 'tenant', false,
       c.golden_set_ref, c.golden_set_sha256, c.golden_set_size, c.golden_metrics
  FROM capability c
 WHERE c.code = 'image.classify' AND c.version = 1
ON CONFLICT (code, version) DO NOTHING;

-- 골든셋이 교체되면 이 계약도 따라가야 한다. 안 그러면 SD-013 이 두 배로 재발한다.
UPDATE capability t
   SET golden_set_sha256 = s.golden_set_sha256,
       golden_set_size   = s.golden_set_size,
       golden_metrics    = s.golden_metrics
  FROM capability s
 WHERE t.code = 'image.classify' AND t.version = 2
   AND s.code = 'image.classify' AND s.version = 1
   AND t.golden_set_sha256 IS DISTINCT FROM s.golden_set_sha256;

-- 3) 경계가 실제로 서 있는지 적용 시점에 확인한다. 문서가 아니라 행렬로 답하게 한다.
DO $$
DECLARE
    tenant_can_use   BOOL;
    tenant_on_team   BOOL;
    team_on_tenant   BOOL;
BEGIN
    -- tenant Task 가 새 계약을 쓸 수 있는가 (min=tenant 이므로 가능해야 한다)
    SELECT EXISTS (SELECT 1 FROM domain_min_compatible
                    WHERE min_domain = 'tenant' AND task_domain = 'tenant')
      INTO tenant_can_use;

    -- tenant Task 가 image.classify@1(min=team)을 쓸 수 있는가 (불가능해야 한다)
    SELECT EXISTS (SELECT 1 FROM domain_min_compatible
                    WHERE min_domain = 'team' AND task_domain = 'tenant')
      INTO tenant_on_team;

    -- team Task 가 tenant Node 로 갈 수 있는가 (불가능해야 한다 — 더 낮은 격리로 내려보내지 않는다)
    SELECT EXISTS (SELECT 1 FROM domain_compatible
                    WHERE task_domain = 'team' AND node_domain = 'tenant')
      INTO team_on_tenant;

    IF NOT tenant_can_use THEN
        RAISE EXCEPTION 'tenant Task 가 tenant 계약을 쓸 수 없다 — 행렬이 깨졌다';
    END IF;
    IF tenant_on_team THEN
        RAISE EXCEPTION 'tenant Task 가 team 전용 계약을 쓸 수 있다 — 경계가 없다';
    END IF;
    IF team_on_tenant THEN
        RAISE EXCEPTION 'team Task 가 tenant Node 로 갈 수 있다 — 격리가 내려앉았다';
    END IF;

    RAISE NOTICE 'tenant 경계 확인: tenant 계약 사용 가능 · team 전용 계약 차단 · team→tenant 라우팅 차단.';
END $$;

COMMENT ON TABLE node IS
    'Node 등급·도메인은 Core 가 부여한다 (절대규칙 4). tenant 는 provision_source team|invited 만.';
