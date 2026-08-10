-- 0001 · baseline = schema v4.4 (docs/spec/schema.sql)
--
-- 이 파일은 DDL 을 만들지 않는다. `docs/spec/schema.sql` 이 이미 적용된 DB 를
-- 마이그레이션 계보의 출발점으로 **선언**할 뿐이다.
--
-- 왜 no-op 인가
--   새 볼륨은 compose 의 docker-entrypoint-initdb.d 가 schema.sql 을 적용한다.
--   기존 볼륨은 이미 적용돼 있다. 둘 다 0001 을 no-op 으로 기록하고 0002 부터 같은 길을 탄다.
--   baseline 을 실제 DDL 로 두면 두 경로가 갈라지고, 그 순간 「기존 볼륨 업그레이드」가 깨진다.
--
-- 기획서 §16: v4.4 를 Phase 1 DDL 기준으로 둔다. 이후 변경은 마이그레이션 이슈로만.

DO $$
BEGIN
    -- baseline 이 정말 있는지 확인한다. 없으면 계보를 시작하지 않는다.
    IF to_regclass('public.capability') IS NULL
       OR to_regclass('public.assignment') IS NULL
       OR to_regclass('public.gate_run') IS NULL THEN
        RAISE EXCEPTION 'baseline 스키마 없음 — docs/spec/schema.sql 이 먼저 적용돼야 한다';
    END IF;
END $$;
