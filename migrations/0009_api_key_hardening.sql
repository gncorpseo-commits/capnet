-- 0009 · api_key 보강 (관리 API 인증 · SD-010 나머지 절반)
--
-- 무엇이 문제였나
--   관리 API 에 **인증이 없었다.** 실측:
--     익명 Node 등록 (team · L등급 · **게이트러너**) → HTTP 200
--     익명 증서 발급                                → HTTP 200
--
--   게이트러너가 되면 자기 Agent 를 자기가 채점해 통과시킬 수 있다.
--   FK 사슬·증적·Node 증서는 전부 그 위에 쌓은 심층 방어인데, **정문이 열려 있었다.**
--   SD-010 이 「Core API 에 인증이 없다」고 적었고, P2-4 는 그중 **Node 사칭**만 닫았다.
--
-- 스키마는 이미 예견해 뒀다
--   `app_user(role IN ('user','developer','admin'))` 과 `api_key(key_prefix, key_hash, revoked_at)` 가
--   v4.4 부터 있었다. **코드가 쓰지 않았을 뿐이다.** 그래서 새 테이블이 필요 없다.
--
-- 이 마이그레이션이 더하는 것 (추가만 · 절대규칙 1)
--   1. `key_prefix` UNIQUE — prefix 로 조회해 해시로 대조하므로 중복이 있으면 검증이 모호해진다
--   2. `last_used_at` — 죽은 키를 찾는 데 쓴다 (node_credential 과 같은 규약)
--   3. 조회면 — 시크릿도 해시도 내보내지 않고 prefix·역할·유효성만

ALTER TABLE api_key
    ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ;

COMMENT ON COLUMN api_key.last_used_at IS
    '마지막 검증 성공 시각. 죽은 키를 찾는 데 쓴다. 검증 경로에서만 갱신한다.';
COMMENT ON COLUMN api_key.key_hash IS
    '평문 키의 sha256. 평문은 발급 시 한 번만 나가고 저장하지 않는다.';

-- prefix 는 조회 키다. 중복되면 「어느 키인지」가 모호해진다.
CREATE UNIQUE INDEX IF NOT EXISTS api_key_prefix_unique ON api_key (key_prefix);

-- 운영자가 한 줄로 본다. 시크릿·해시는 나가지 않는다.
CREATE OR REPLACE VIEW api_key_status AS
SELECT
    k.id            AS api_key_id,
    u.id            AS user_id,
    u.name          AS user_name,
    u.role,
    k.key_prefix,
    k.label,
    k.created_at,
    k.last_used_at,
    (k.revoked_at IS NULL) AS active
FROM api_key k
JOIN app_user u ON u.id = k.user_id;

COMMENT ON VIEW api_key_status IS
    '발급된 관리 API 키 상태. 시크릿도 해시도 나가지 않는다 — prefix 와 역할만.';

DO $$
DECLARE
    n_keys INT;
    n_admin INT;
BEGIN
    SELECT count(*) INTO n_keys FROM api_key WHERE revoked_at IS NULL;
    SELECT count(*) INTO n_admin FROM app_user WHERE role = 'admin';
    RAISE NOTICE '활성 API 키 % 개 · admin 사용자 % 명', n_keys, n_admin;
    IF n_keys = 0 THEN
        RAISE NOTICE '키가 없다. 강제를 켜기 전에 발급한다: python -m app.apikey_cli issue --role admin --label bootstrap';
    END IF;
END $$;
