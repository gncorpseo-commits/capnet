-- 0016 · 초대 경로 (G2 — `provision_source='invited'` 를 만드는 절차)
--
-- 무엇이 문제였나
--   `node.provision_source` 는 `team | invited | public` 을 받는데 **`invited` 를 만드는
--   절차가 없었다.** 값은 스키마에 있고 경로가 없다 — `attempt_no` 와 같은 모양이다.
--   그래서 「러닝크루가 자기 기기를 내놓는다」가 실제로는 **관리자 수작업**이었다.
--
-- 절대규칙 4 를 지키는 방법
--   Node 는 자기 등급을 주장할 수 없다. 초대에서 그것을 지키는 길은 하나뿐이다 —
--   **신청자가 고르지 않는다.** 관리자가 초대를 발행할 때 `trust_domain` 과
--   `compute_tier_max` 를 박아 넣고, 신청자는 그 초대를 **소진**할 뿐이다.
--   등급은 언제나 초대장에 적힌 값이고, 소진 요청 본문은 그것을 바꾸지 못한다.
--
-- 기존 제약이 이미 지켜 주는 것 (새로 막을 게 없다)
--   `ck_gate_runner_team` — `is_gate_runner` 는 `provision_source='team'` 에서만 참이다.
--     그래서 초대로 들어온 기기는 **채점자가 될 수 없다** (절대규칙 8 이 그대로 선다).
--   `ck_trust_provision_align` — `(team, invited)` 조합은 애초에 거절된다.
--     아래 `ck_invite_domain` 은 그것을 **초대 발행 시점으로 당겨** 온다.
--
-- 추가만 (절대규칙 1) — 테이블 1 · 인덱스 2. 기존 제약 삭제·완화 없음.

CREATE TABLE IF NOT EXISTS node_invite (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issued_by         UUID NOT NULL REFERENCES app_user(id),

    -- 증서와 같은 모양이다 (`cn_` 대신 `ci_`). 평문은 발행 응답에서 한 번만 나간다.
    key_prefix        TEXT NOT NULL UNIQUE,
    secret_hash       BYTEA NOT NULL,

    -- 등급은 **여기에 박힌다.** 소진 요청이 아니라 초대장이 정한다 (절대규칙 4).
    trust_domain      TEXT NOT NULL REFERENCES trust_domain_rank (domain),
    provision_source  TEXT NOT NULL DEFAULT 'invited'
                          CHECK (provision_source = 'invited'),
    compute_tier_max  TEXT NOT NULL DEFAULT 'M' REFERENCES compute_tier_rank (tier),

    label             TEXT,
    expires_at        TIMESTAMPTZ NOT NULL,
    max_redemptions   INT NOT NULL DEFAULT 1 CHECK (max_redemptions >= 1),
    redeemed_count    INT NOT NULL DEFAULT 0 CHECK (redeemed_count >= 0),
    revoked_at        TIMESTAMPTZ,
    revoked_reason    TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- team 은 초대로 만들 수 없다. `ck_trust_provision_align` 이 node INSERT 에서 막지만,
    -- 여기서 막으면 「발행은 됐는데 소진이 안 되는 초대장」이 아예 생기지 않는다.
    CONSTRAINT ck_invite_domain CHECK (trust_domain IN ('tenant', 'public')),
    -- 상한을 넘겨 소진할 수 없다. 앱이 세고 **DB 가 막는다** (0015 와 같은 규율).
    CONSTRAINT ck_invite_redeem_within_cap CHECK (redeemed_count <= max_redemptions)
);

COMMENT ON TABLE node_invite IS
    '초대장 (G2 · 0016). 등급(trust_domain·compute_tier_max)은 발행 시점에 박히고 '
    '소진 요청이 바꾸지 못한다 — 절대규칙 4. team 등급은 초대로 만들 수 없다.';

COMMENT ON COLUMN node_invite.max_redemptions IS
    '초대장 하나가 만들 수 있는 Node 수. 기본 1 — 초대장 하나가 기기 하나에 대응해야 '
    '증적이 깨끗하다. 열 명이면 열 장을 발행한다.';

-- 소진된 Node 를 초대장에 되짚는다. 「이 기기는 어느 초대로 들어왔나」에 답한다.
CREATE TABLE IF NOT EXISTS node_invite_redemption (
    invite_id   UUID NOT NULL REFERENCES node_invite(id),
    node_id     UUID NOT NULL REFERENCES node(id) ON DELETE CASCADE,
    redeemed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (invite_id, node_id),
    -- 한 Node 는 초대장 하나로만 들어온다
    UNIQUE (node_id)
);

COMMENT ON TABLE node_invite_redemption IS
    '초대 소진 이력 (0016). 「이 기기가 어느 초대로 들어왔나」 — 증적이다.';

-- 살아 있는 초대장을 prefix 로 찾는다 (검증 경로).
CREATE INDEX IF NOT EXISTS node_invite_live_idx
    ON node_invite (key_prefix)
 WHERE revoked_at IS NULL;

-- 조회면 — 초대장이 지금 쓸 수 있는 상태인가. 판정을 앱마다 다시 쓰지 않게 한다.
CREATE OR REPLACE VIEW node_invite_status AS
SELECT
    i.id,
    i.key_prefix,
    i.label,
    i.trust_domain,
    i.compute_tier_max,
    i.issued_by,
    i.created_at,
    i.expires_at,
    i.max_redemptions,
    i.redeemed_count,
    i.revoked_at,
    (i.revoked_at IS NULL
     AND i.expires_at > now()
     AND i.redeemed_count < i.max_redemptions) AS usable,
    CASE
        WHEN i.revoked_at IS NOT NULL                      THEN 'REVOKED'
        WHEN i.expires_at <= now()                         THEN 'EXPIRED'
        WHEN i.redeemed_count >= i.max_redemptions         THEN 'REDEEMED'
        ELSE 'USABLE'
    END AS state
FROM node_invite i;
