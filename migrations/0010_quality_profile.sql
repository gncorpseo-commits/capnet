-- 0010 · 품질 프로파일 — 게이트 없는 Capability 도 라우팅된다 (D18 코드 정합)
--
-- 무엇이 문제였나
--   D18(2026-08-09)은 「Capability = 인터페이스 계약, 골든셋 게이트는 **선택적 품질 프로파일**」
--   로 정리했다. 그런데 코드와 스키마는 게이트를 **필수**로 붙들고 있었다.
--
--     capability(golden_set_ref/sha256/size/metrics 전부 NOT NULL)
--       gate_run(PASSED · golden_set_sha256 NOT NULL · CHECK runner_is_gate_runner)
--         → gate_run_passed → agent_capability(PASSED ⇒ gate_run_id NOT NULL)
--           → agent_capability_passed → assignment (FK)
--
--   여섯 층이다. 그래서 **새 능력을 하나 추가할 때마다 골든셋 40장 + 채점기**를 만들어야 했고,
--   제품이 `image.classify@1` 하나에 묶여 있었다. "능력만 요구한다" 는 주장이 실체가 없었다.
--
-- 어떻게 푸는가 — 계약 바인딩도 게이트런이다
--   사슬을 끊지 않는다. **골든셋 0장짜리 게이트런**을 하나 더 인정한다.
--   `kind='contract'` 게이트런은 채점 대신 계약(입출력 스키마·전처리·arch·max_params)을 검증하고,
--   통과하면 기존과 **똑같은 경로**로 증서가 올라간다. 그래서 `claim` 쿼리도 `assignment` FK 도
--   손대지 않는다 — 라우팅은 지금 그대로 돈다.
--
--   계약 검증도 **team gate-runner 가 한다** (절대규칙 8 유지). Core 가 스스로 판정을 만들면
--   「실행과 판정을 분리한다」는 것이 무너진다. runner_is_gate_runner CHECK 를 그대로 통과한다.
--
-- 센티널을 쓰는 이유
--   `golden_set_*` 4개의 NOT NULL 을 **해제하지 않는다** (절대규칙 1). 대신 「골든셋 없음」을
--   고정된 값으로 표현하고 그 규약을 CHECK 로 강제한다. size=1 같은 값을 숫자로 읽으면 거짓말이
--   되므로, **읽는 쪽은 항상 quality_profile 을 먼저 본다.**
--     golden → 실제 골든셋 통계가 유효하다
--     none   → 품질 프로파일이 없다. 골든 통계를 적용하지 않는다
--
-- 오늘 동작은 바뀌지 않는다
--   기존 capability 는 전부 quality_profile='golden' 으로 채워지고, 기존 gate_run 은 kind='golden'
--   이 된다. `image.classify@1` 의 게이트는 그대로다 (대회·데모 서사 보존).
--
-- 추가만 (절대규칙 1) — 컬럼 3 · CHECK 4 · UNIQUE 1 · FK 1. 삭제·완화 없음.

-- ── 1. capability: 품질 프로파일 ──────────────────────────────────────────

ALTER TABLE capability
    ADD COLUMN IF NOT EXISTS quality_profile TEXT NOT NULL DEFAULT 'golden';

COMMENT ON COLUMN capability.quality_profile IS
    'golden = 골든셋 게이트를 붙인 능력 (통계 유효). '
    'none = 계약만으로 라우팅하는 능력 — golden_set_* 는 센티널이며 읽지 않는다 (D18).';

ALTER TABLE capability
    ADD CONSTRAINT ck_capability_quality_profile
    CHECK (quality_profile IN ('golden', 'none'));

-- 센티널 규약. 「골든셋 없음」이 우연히 진짜 값처럼 보이는 일을 막는다.
ALTER TABLE capability
    ADD CONSTRAINT ck_capability_profile_sentinel CHECK (
        (quality_profile = 'golden'
             AND golden_set_ref    <> '(none)'
             AND golden_set_sha256 <> repeat('0', 64))
        OR
        (quality_profile = 'none'
             AND golden_set_ref    =  '(none)'
             AND golden_set_sha256 =  repeat('0', 64)
             AND golden_set_size   =  1
             AND golden_metrics    =  '{}'::jsonb)
    );

-- gate_run 이 복합 FK 로 참조할 대상. (id, compute_tier) · (id, trust_domain_min) 과 같은 관례다.
ALTER TABLE capability
    ADD CONSTRAINT capability_id_quality_profile_key UNIQUE (id, quality_profile);

-- ── 2. gate_run: 게이트런의 종류 ──────────────────────────────────────────

ALTER TABLE gate_run
    ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'golden',
    ADD COLUMN IF NOT EXISTS capability_quality_profile TEXT NOT NULL DEFAULT 'golden';

COMMENT ON COLUMN gate_run.kind IS
    'golden = 골든셋 채점. contract = 계약 검증(스키마·전처리·arch·max_params). '
    '둘 다 team gate-runner 가 실행한다 (절대규칙 8).';
COMMENT ON COLUMN gate_run.capability_quality_profile IS
    '실행 시점 capability.quality_profile 스냅샷. 복합 FK 로 실제 값과 묶인다 — '
    '나중에 능력의 프로파일이 바뀌어도 이 증적이 무엇을 근거로 발급됐는지가 남는다.';

ALTER TABLE gate_run
    ADD CONSTRAINT ck_gate_run_kind
    CHECK (kind IN ('golden', 'contract'));

-- 종류와 프로파일은 1:1 이다. 앱이 고르는 게 아니라 DB 가 맞춘다.
-- golden 능력에 계약 게이트런을 붙이거나 그 반대를 하는 경로를 없앤다.
ALTER TABLE gate_run
    ADD CONSTRAINT ck_gate_run_kind_matches_profile CHECK (
        (kind = 'golden'   AND capability_quality_profile = 'golden')
        OR
        (kind = 'contract' AND capability_quality_profile = 'none')
    );

-- 스냅샷이 실제 capability 와 어긋날 수 없다.
ALTER TABLE gate_run
    ADD CONSTRAINT gate_run_capability_profile_fkey
    FOREIGN KEY (capability_id, capability_quality_profile)
        REFERENCES capability (id, quality_profile);

-- 계약 게이트런은 골든 통계를 **가질 수 없다.** 없는 채점의 점수가 증적에 남는 것을 막는다.
ALTER TABLE gate_run
    ADD CONSTRAINT ck_gate_run_contract_no_golden_stats CHECK (
        kind <> 'contract'
        OR (golden_set_sha256 = repeat('0', 64)
            AND golden_score  IS NULL
            AND cases_total   IS NULL
            AND cases_passed  IS NULL)
    );
