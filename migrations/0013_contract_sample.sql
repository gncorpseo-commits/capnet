-- 0013 · 계약 검증 샘플 (B2 · Decision 1·2)
--
-- 무엇이 문제였나
--   계약 게이트(`kind='contract'`)는 러너가 보낸 `contract_checks` 가 전부 true 인지만 봤다.
--   **Core 도 DB 도 그 보고를 검증하지 않는다.** 러너를 신뢰하는 만큼만 믿을 수 있었고,
--   그 신뢰의 근거는 절대규칙 8(게이트러너 전용)뿐이었다.
--
--   D6(사전학습 허용)를 풀면 **남의 가중치**를 받는다. 그때 「계약을 지키는 모델인가」를
--   러너가 실제로 확인하지 않으면 계약 게이트는 도장만 찍는 절차가 된다.
--
-- 검증하려면 샘플이 있어야 한다
--   ungated 능력은 골든셋이 없다. 리뷰 Decision 1 = **(가) `task_input` 을 샘플로 쓴다.**
--   계약이 「무엇을 받는가」를 말했으면 그 예시도 계약의 일부다.
--
-- 추가만 (절대규칙 1) — 컬럼 2 · CHECK 1 · FK 2 · 뷰 1 갱신. 삭제·완화 없음.

-- ── 1. capability: 계약 샘플 ──────────────────────────────────────────────

ALTER TABLE capability
    ADD COLUMN IF NOT EXISTS sample_input_id UUID;

COMMENT ON COLUMN capability.sample_input_id IS
    '계약 검증용 샘플 입력 (B2). 러너가 이 바이트로 실제 추론해 input_schema·output_schema 를 '
    '확인한다. 「무엇을 받는가」를 선언했으면 그 예시도 계약의 일부다.';

-- **같은 능력으로 수집된 입력만** 샘플이 될 수 있다. 남의 능력 입력을 예시로 걸 수 없다.
-- task 가 입력을 붙일 때 쓰는 것과 같은 복합 FK 패턴이다 (0011).
ALTER TABLE capability
    ADD CONSTRAINT capability_sample_input_fkey
    FOREIGN KEY (sample_input_id, id)
        REFERENCES task_input (id, capability_id);

-- ── 2. gate_run: 무엇으로 검증했는가 ──────────────────────────────────────

ALTER TABLE gate_run
    ADD COLUMN IF NOT EXISTS sample_input_id UUID REFERENCES task_input (id);

COMMENT ON COLUMN gate_run.sample_input_id IS
    '계약 게이트런이 실제로 돌려 본 샘플 (B2). 「무엇을 근거로 통과시켰는가」가 증적에 남는다. '
    'golden 게이트런은 NULL — 골든셋 40장이 그 자리를 대신한다.';

-- **샘플 없는 계약 게이트런은 시작될 수 없다.** START_SQL 이 capability.sample_input_id 를
-- 스냅샷하므로, 샘플을 안 붙인 능력은 계약 게이트런 자체가 거절된다.
-- 기존 gate_run 은 전부 kind='golden' 이라 이 CHECK 를 그대로 통과한다.
--
-- capability 쪽에 「quality_profile='none' 이면 샘플 필수」 CHECK 를 걸지 않은 것은,
-- 기존 볼륨에 샘플 없는 ungated 능력이 있으면 이 마이그레이션이 실패하기 때문이다.
-- 능력은 만들어 두고 샘플을 나중에 붙일 수 있어야 한다.
ALTER TABLE gate_run
    ADD CONSTRAINT ck_gate_run_contract_needs_sample CHECK (
        kind <> 'contract' OR sample_input_id IS NOT NULL
    );

-- ── 3. 샘플은 GC 대상이 아니다 ────────────────────────────────────────────
--
-- 샘플은 task 에 연결되지 않으므로 지금 규칙이면 `orphan-24h` 로 하루 만에 지워진다.
-- 그러면 다음 게이트런이 검증을 못 한다. 샘플은 「휘발성 작업 바이트」가 아니라 **계약의 일부**다.
-- 0011 과 같은 컬럼·순서를 유지한다 (CREATE OR REPLACE 제약).

CREATE OR REPLACE VIEW task_input_purge_due AS
SELECT
    ti.id                AS task_input_id,
    ti.sha256,
    ti.byte_size,
    ti.uploaded_by,
    t.id                 AS task_id,
    t.status             AS task_status,
    CASE
        WHEN t.id IS NULL                    THEN 'orphan-24h'
        WHEN t.finished_at IS NOT NULL       THEN 'finished-7d'
        ELSE                                      'stale-72h'
    END                  AS reason,
    CASE
        WHEN t.id IS NULL                    THEN ti.created_at + INTERVAL '24 hours'
        WHEN t.finished_at IS NOT NULL       THEN t.finished_at + INTERVAL '7 days'
        ELSE                                      t.created_at  + INTERVAL '72 hours'
    END                  AS due_at
  FROM task_input ti
  LEFT JOIN task t ON t.input_id = ti.id
 WHERE ti.storage_state = 'STORED'
   -- 계약 샘플은 지우지 않는다 (B2).
   AND NOT EXISTS (
       SELECT 1 FROM capability c WHERE c.sample_input_id = ti.id
   );

COMMENT ON VIEW task_input_purge_due IS
    '입력 바이트의 삭제 예정 시각 (D22). due_at <= now() 인 행이 워커 GC 대상이다. '
    'orphan-24h = task 에 연결되지 않은 업로드 · finished-7d = 종결 후 7일 · '
    'stale-72h = 미완료 task 최대 수명. 계약 샘플(capability.sample_input_id)은 제외한다 (B2). '
    '바이트만 지우고 행은 남긴다.';
