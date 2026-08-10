-- 0008 · 아키텍처를 계약에 묶는다 (I1 · foreign-agent-isolation)
--
-- 무엇이 문제였나
--   `apps/node/app/infer.py` 의 `_arch_for_weights()` 는 **Node 로컬 파일**
--   (`<weights>.meta.json`)에서 아키텍처를 읽었다.
--
--   Agent 신원은 `weights_sha256` 뿐이고 **arch 는 그 해시에 포함되지 않는다.**
--   그래서 Core 가 「이 Agent 는 이 arch 다」라고 말할 방법이 없고, 실행 Node 가 로컬 파일로 정했다.
--   지금은 어긋나면 load_state_dict 가 터지지만, 그건 **우연한 실패**이지 보장이 아니다.
--
--   남의 Agent 를 받는 순간 이건 즉시 문제가 된다 — 제출자가 arch 를 선언하고
--   Core 가 그것을 증적에 묶어야 한다.
--
-- 왜 룩업 테이블인가
--   허용 아키텍처를 **DB 행**으로 둔다. 이 리포의 idiom 그대로다 —
--   `compute_tier_rank` · `domain_compatible` 처럼 「행렬이 정책」이다.
--   코드 상수(`ARCH_REGISTRY`)는 여전히 있지만, **등록을 막는 것은 FK** 다.
--   없는 arch 로는 Agent 등록 자체가 되지 않는다.
--
-- 왜 nullable 인가
--   기존 Agent 41건은 arch 선언 없이 만들어졌다. NOT NULL 로 만들면 그것들을 추측해 채워야 하는데,
--   Core 는 가중치 파일을 보지 않으므로 **추측이 된다.** 증적에 추측을 적지 않는다.
--   대신 `agent_arch_unbound` 뷰로 남은 구멍을 드러낸다. 새 Agent 는 선언해야 한다.
--
-- max_params
--   게이트는 **품질**만 본다 (정확도). 40장 채점을 통과하는 10GB 모델을 막을 것이 없었다.
--   아키텍처별 파라미터 상한을 DB 에 둔다 — Node 가 로드 후 이 값으로 검사한다.

CREATE TABLE IF NOT EXISTS agent_arch (
    arch        TEXT PRIMARY KEY,
    max_params  BIGINT NOT NULL CHECK (max_params > 0),
    note        TEXT,
    added_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE agent_arch IS
    '허용 아키텍처 = DB 행 (I1). 없는 arch 로는 Agent 등록이 FK 로 막힌다. '
    'Node 의 ARCH_REGISTRY 와 이름이 일치해야 한다.';
COMMENT ON COLUMN agent_arch.max_params IS
    '파라미터 수 상한. 게이트는 품질만 보므로, 거대 모델은 이 값으로 막는다.';

-- TinyEuroSAT ~93k · TinyEuroSATB ~24k (실측). 상한은 여유를 두되 자릿수를 넘지 않게.
INSERT INTO agent_arch (arch, max_params, note) VALUES
    ('TinyEuroSAT',  2000000, 'scratch CNN · 32x32 RGB · 10 labels'),
    ('TinyEuroSATB', 2000000, 'scratch CNN (경량 변형) · 32x32 RGB · 10 labels')
ON CONFLICT (arch) DO NOTHING;

ALTER TABLE agent
    ADD COLUMN IF NOT EXISTS arch TEXT REFERENCES agent_arch (arch);

COMMENT ON COLUMN agent.arch IS
    'Core 가 아는 아키텍처. NULL 은 legacy (0008 이전 등록) — Node 가 로컬 meta 로 떨어진다. '
    '새 Agent 는 선언해야 한다. agent_arch_unbound 뷰로 남은 구멍을 본다.';

-- 남은 구멍을 조회 가능하게. 「모른다」를 숨기지 않는다.
CREATE OR REPLACE VIEW agent_arch_unbound AS
SELECT
    a.id            AS agent_id,
    a.name,
    a.version,
    a.status,
    a.weights_sha256,
    EXISTS (
        SELECT 1 FROM agent_capability_passed acp
        WHERE acp.agent_id = a.id AND acp.revoked_at IS NULL
    )               AS routable
FROM agent a
WHERE a.arch IS NULL;

COMMENT ON VIEW agent_arch_unbound IS
    'arch 가 계약에 묶이지 않은 Agent (legacy). routable=true 면 지금도 배정되는데 '
    '실행 arch 를 Node 로컬 파일이 정한다 — I1 의 남은 구멍이다.';

DO $$
DECLARE
    n_unbound INT;
    n_routable INT;
BEGIN
    -- 변수명이 뷰 컬럼(routable)과 겹치면 PL/pgSQL 이 모호하다고 거부한다. 접두사로 피한다.
    SELECT count(*), count(*) FILTER (WHERE v.routable)
      INTO n_unbound, n_routable
      FROM agent_arch_unbound v;
    IF n_unbound > 0 THEN
        RAISE NOTICE 'arch 미선언 Agent % 건 (라우팅 가능 % 건) — legacy. 새 Agent 는 선언이 필요하다.',
            n_unbound, n_routable;
        RAISE NOTICE '조회: SELECT * FROM agent_arch_unbound;';
    END IF;
END $$;
