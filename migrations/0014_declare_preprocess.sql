-- 0014 · 전처리 선언 (B2 잔여 · Decision)
--
-- 무엇이 문제였나
--   `infer.py` 가 **32×32 RGB 를 코드에 박아** 쓴다. D3 는 「전처리는 계약의 일부」라고 하는데,
--   계약에는 그 값을 **적을 자리가 없었다.** 그래서 계약 검증의 `preprocess` 항목은 러너가
--   검증 없이 보내는 불린이었고, 그래서 필수 항목에서 뺐다 (0013 · B2).
--
-- 결정
--   `input_schema.preprocess` 에 선언한다 (`mediaTypes` 와 같은 자리 · 0012 와 같은 방식).
--   러너는 **선언한 값을 읽어 적용**하고, 그 값으로 추론이 도는지 확인한다.
--   전처리를 선언하지 않은 능력은 **계약 게이트를 거절**한다 (아래 §2).
--
--   `image.classify` 의 선언값은 **지금 하드코딩된 값과 같다** (32×32 RGB).
--   골든 경로의 픽셀 처리는 바뀌지 않는다 — 달라지는 것은 「그 값이 어디서 오는가」뿐이다.
--
-- 추가만 (절대규칙 1) — 데이터 1 · 컬럼 1 · CHECK 1. 삭제·완화 없음.

-- ── 1. image.classify 에 선언을 붙인다 ────────────────────────────────────
--
-- jsonb 병합이라 멱등하다. 이미 있으면 건드리지 않는다.

UPDATE capability
   SET input_schema = input_schema
       || '{"preprocess":{"resize":[32,32],"colorspace":"RGB"}}'::jsonb
 WHERE code = 'image.classify'
   AND input_schema -> 'preprocess' IS NULL;

COMMENT ON COLUMN capability.input_schema IS
    '입력 계약. `mediaTypes` 배열이 있으면 업로드 MIME 을 그 목록과 대조한다 — '
    '선언이 없으면 업로드를 거절한다 (0012 · D8′). '
    '`preprocess` 객체(`resize`·`colorspace`)가 있으면 러너가 그 값을 적용해 계약을 검증한다 — '
    '선언이 없으면 계약 게이트를 거절한다 (0014 · B2). caseId 데모 경로는 해당 없음.';

-- ── 2. 전처리 미선언 능력은 계약 게이트를 시작할 수 없다 ──────────────────
--
-- 샘플(0013)과 같은 자리에 같은 방식으로 건다. `capability` 에 CHECK 를 걸면
-- **기존 볼륨에 선언 없는 ungated 능력이 있을 때 이 마이그레이션이 실패한다.**
-- 게이트런 쪽에 두면 능력은 만들어 두고 선언을 나중에 붙일 수 있다.

ALTER TABLE gate_run
    ADD COLUMN IF NOT EXISTS capability_preprocess JSONB;

COMMENT ON COLUMN gate_run.capability_preprocess IS
    '계약 게이트런이 검증한 전처리 선언의 스냅샷 (B2). 「무엇을 적용해 통과시켰는가」가 '
    '증적에 남는다 — 나중에 계약이 바뀌어도 이 증서의 근거는 고정된다. golden 게이트런은 NULL.';

-- 기존 gate_run 은 전부 kind='golden' 이라 이 CHECK 를 그대로 통과한다.
-- jsonb 'null' 이 들어와 「선언했다」로 통하는 것도 막는다.
ALTER TABLE gate_run
    ADD CONSTRAINT ck_gate_run_contract_needs_preprocess CHECK (
        kind <> 'contract'
        OR (capability_preprocess IS NOT NULL
            AND jsonb_typeof(capability_preprocess) = 'object')
    );
