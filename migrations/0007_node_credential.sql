-- 0007 · node_credential (P2-4 · SD-002)
--
-- 무엇
--   Node 프로세스가 「자기가 어떤 node.id 인지」를 **증명**하는 증서 테이블.
--   기획서 §16 이 동결한 v4.4 를 처음으로 건드리는 변경이다 — 그러나 **추가만** 한다 (절대규칙 1).
--
-- 왜 지금
--   로드맵 §3.1 이 이 작업의 선행 조건 셋을 적었다.
--     1. 마이그레이션 도구·순서 결정      → SD-007 (0001~)
--     2. 기존 볼륨 업그레이드 경로        → SD-007 (down -v 없이)
--     3. 승인                              → 이 브랜치의 PR
--   앞의 둘이 끝났으므로 이제 열린다.
--
-- 무엇을 막는가 (SD-010)
--   지금 Node 가 부르는 경로는 `node_id` 를 **URL 에서 그대로** 받는다.
--     POST /v1/internal/nodes/{node_id}/heartbeat
--     GET  /v1/internal/nodes/{node_id}/assignments
--   즉 아무나 임의 Node 를 사칭할 수 있다. 지금까지의 방어는 「팀 내부망 전제」뿐이었다 (SD-010).
--   증서를 붙이면 Core 가 시크릿을 검증해 node_id 를 **해석**한다 — URL 이 주장하는 값을 믿지 않는다.
--
-- 절대규칙 4 (Node 는 자기 등급을 주장할 수 없다)
--   이 테이블에 `trust_domain`·`compute_tier_max`·`is_gate_runner` 가 **없다.** 의도다.
--   증서는 「너는 이 node.id 다」만 말한다. 등급은 언제나 `node` 행에서 읽는다 (C1·C2).
--
-- 열린 질문(초안 §6) 확정
--   1. 시크릿 형식 → **opaque 토큰 + DB 해시**. JWT 는 등급 claim 이 실릴 여지가 있어 쓰지 않는다
--   2. 강제 범위   → 전 Node. 다만 **강제는 플래그**이며 기본 꺼짐 (초안 §4 — 데모는 증서 없이 돈다)
--   3. 만료·회전   → `expires_at` 은 선택. 회전은 **폐기 후 재발급** (활성 1개 제약 때문)
--   4. api_key 통합 → 하지 않는다. 주체(사용자 vs 기기)와 권한이 다르다
--
-- 시크릿은 저장하지 않는다
--   평문은 발급 응답에서 **한 번만** 나간다. DB 에는 sha256 해시만 남는다 (C3).
--   토큰 엔트로피가 충분하므로(256비트) 느린 KDF 대신 sha256 을 쓴다 — `api_key` 와 같은 방식이다.

CREATE TABLE IF NOT EXISTS node_credential (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id         UUID        NOT NULL REFERENCES node (id),
    issued_by       UUID        NOT NULL REFERENCES app_user (id),
    key_prefix      TEXT        NOT NULL,
    secret_hash     BYTEA       NOT NULL,
    label           TEXT,
    issued_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    revoked_reason  TEXT,
    last_used_at    TIMESTAMPTZ,

    -- 이유 없는 폐기를 남기지 않는다 (0004 와 같은 규율)
    CONSTRAINT ck_nc_revoked_needs_reason
        CHECK (revoked_at IS NULL OR revoked_reason IS NOT NULL),
    -- 발급보다 이른 만료는 의미가 없다
    CONSTRAINT ck_nc_expiry_after_issue
        CHECK (expires_at IS NULL OR expires_at > issued_at),
    -- prefix 는 조회·로그용이다. 형식을 고정해 두면 로그에서 시크릿과 혼동되지 않는다
    CONSTRAINT ck_nc_prefix_shape
        CHECK (key_prefix ~ '^cn_[0-9a-f]{8}$')
);

-- Node 당 활성 증서는 하나. 회전은 「폐기 → 재발급」이다.
-- (만료를 조건에 넣을 수 없다 — now() 는 immutable 이 아니라 부분 인덱스에 못 쓴다.)
CREATE UNIQUE INDEX IF NOT EXISTS node_credential_active_idx
    ON node_credential (node_id)
    WHERE revoked_at IS NULL;

-- 검증은 prefix 로 찾고 해시로 대조한다.
CREATE UNIQUE INDEX IF NOT EXISTS node_credential_prefix_idx
    ON node_credential (key_prefix);

COMMENT ON TABLE node_credential IS
    'Node 프로세스가 자기 node.id 를 증명하는 증서 (P2-4 · SD-002). '
    '등급 컬럼이 없는 것은 의도다 — 절대규칙 4. 등급은 node 행에서만 읽는다.';
COMMENT ON COLUMN node_credential.secret_hash IS
    '평문 시크릿의 sha256. 평문은 발급 응답에서 한 번만 나가고 저장하지 않는다 (C3).';
COMMENT ON COLUMN node_credential.last_used_at IS
    '마지막 검증 성공 시각. 죽은 증서를 찾는 데 쓴다. 검증 경로에서만 갱신한다.';

-- 운영자가 한 줄로 보는 면
CREATE OR REPLACE VIEW node_credential_status AS
SELECT
    n.id                AS node_id,
    n.name              AS node_name,
    n.trust_domain,
    n.provision_source,
    nc.id               AS credential_id,
    nc.key_prefix,
    nc.issued_at,
    nc.expires_at,
    nc.last_used_at,
    (nc.id IS NOT NULL
     AND nc.revoked_at IS NULL
     AND (nc.expires_at IS NULL OR nc.expires_at > now())) AS credential_valid
FROM node n
LEFT JOIN node_credential nc
       ON nc.node_id = n.id AND nc.revoked_at IS NULL;

COMMENT ON VIEW node_credential_status IS
    'Node 별 활성 증서 상태. credential_valid=false 면 강제 모드에서 그 Node 는 일하지 못한다.';
