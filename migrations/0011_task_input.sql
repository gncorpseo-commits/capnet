-- 0011 · task_input — Core 중개 입력 수집 (D22 · D8′)
--
-- 무엇이 문제였나
--   Core→Node 로 **바이트가 전송되지 않는다.** Node 는 `input_ref` 의 `caseId` 로
--   미리 마운트된 골든셋 40장 중 하나를 고를 뿐이다. 제품 문구가
--   「내 데이터를 남의 기계에 보내면서 어디로 갔는지 답할 수 있는가」인데,
--   지금은 **내 데이터를 보낼 수가 없다.**
--
-- 결정 (D22 · D8′)
--   금지 대상은 「자유 업로드」가 아니라 **「비통제 수집」**이다. Core 가 계약 검증·해시 증적·
--   보존 정책을 갖는 수집만 허용한다. 서명 URL(1안)은 D8 근거(다운로드 이후 통제 불가)로 계속 기각.
--
-- 원칙 한 줄
--   **증적 = 해시·누가·어디로 · 바이트 = 휘발성 작업 저장소.**
--   바이트는 지워도 `task_input` 행은 남는다 — 그래야 나중에도 「어디로 갔는지」에 답한다.
--
-- 왜 바이트를 DB 에 넣지 않나
--   백업 대상에서 **입력 바이트는 빼고 증적 DB 는 넣는다**는 정책과 충돌한다.
--   바이트는 별도 볼륨에, DB 에는 메타(해시·크기·MIME·소유자·상태)만 둔다.
--
-- 확정된 숫자
--   크기   기본 32MB · capability 별 상향/하향 · 절대 상한 256MB
--   보존   완료(최종 상태) 후 7일 · 고아 입력 24시간 · 미완료 task 최대 수명 72시간
--   GC     Core 워커 주기 삭제가 본경로 (+ 선택적 즉시 purge)
--
-- 데모 경로는 그대로다 — `caseId` 만 있는 요청은 `input_id` 가 NULL 이고 바이트도 TTL 도 없다.
--
-- 추가만 (절대규칙 1) — 테이블 1 · 뷰 1 · 컬럼 4 · CHECK 6 · UNIQUE 3 · FK 3. 삭제·완화 없음.

-- ── 1. capability: 입력 크기 계약 ─────────────────────────────────────────

ALTER TABLE capability
    ADD COLUMN IF NOT EXISTS max_input_bytes BIGINT NOT NULL DEFAULT 33554432;  -- 32MiB

COMMENT ON COLUMN capability.max_input_bytes IS
    '이 능력이 받는 입력의 최대 크기. 기본 32MiB. 절대 상한 256MiB — '
    'Core 가 중개하므로 기본을 키우면 그대로 디스크·DoS 면이 된다.';

ALTER TABLE capability
    ADD CONSTRAINT ck_capability_max_input_bytes
    CHECK (max_input_bytes > 0 AND max_input_bytes <= 268435456);               -- 256MiB

-- task_input 이 복합 FK 로 잡을 대상 (스냅샷 패턴 · (id, compute_tier) 와 같은 관례).
ALTER TABLE capability
    ADD CONSTRAINT capability_id_max_input_bytes_key UNIQUE (id, max_input_bytes);

-- ── 2. task: 종결 시각 ────────────────────────────────────────────────────
--
-- 「완료 후 7일」의 기준이 없었다. `updated_at` 은 claim 회수(status→QUEUED)에서도 갱신되므로
-- TTL 기준으로 쓰면 만료가 뒤로 밀린다. 종결 시각을 따로 둔다.

ALTER TABLE task
    ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;

COMMENT ON COLUMN task.finished_at IS
    '최종 상태로 넘어간 시각. 입력 바이트 보존기간(완료 후 7일)의 기준이다. '
    'updated_at 은 회수·재배정에서도 갱신되므로 기준이 될 수 없다.';

-- 진행 중인데 종결 시각이 박히는 일을 막는다. legacy 행(NULL)은 그대로 통과한다.
ALTER TABLE task
    ADD CONSTRAINT ck_task_finished_only_terminal CHECK (
        finished_at IS NULL
        OR status IN ('COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELED')
    );

-- ── 3. task_input ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS task_input (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 입력은 **수집 시점에 능력에 묶인다** (D8′ 「계약된 ingest」).
    -- 다른 능력으로 재사용하려면 다시 올린다 — 계약이 다르면 검증도 다르다.
    capability_id UUID NOT NULL REFERENCES capability (id),

    -- 사용자끼리 중복 제거하지 않는다. 같은 바이트라도 소유자·신뢰도메인이 다르면 다른 입력이다.
    sha256        TEXT   NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    byte_size     BIGINT NOT NULL CHECK (byte_size > 0),
    media_type    TEXT   NOT NULL CHECK (media_type <> ''),
    uploaded_by   UUID   NOT NULL REFERENCES app_user (id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- 크기 계약 스냅샷. 앱이 재는 게 아니라 **DB 가 거절한다.**
    capability_max_input_bytes BIGINT NOT NULL,

    -- 바이트의 생사. 행은 지우지 않는다 — task 가 FK 로 참조하고, 증적이 그 위에 있다.
    storage_state   TEXT NOT NULL DEFAULT 'STORED'
                        CHECK (storage_state IN ('STORED', 'PURGED')),
    bytes_purged_at TIMESTAMPTZ,

    CONSTRAINT ck_task_input_within_contract
        CHECK (byte_size <= capability_max_input_bytes),

    -- 「지웠다」와 「언제 지웠다」가 어긋날 수 없다.
    CONSTRAINT ck_task_input_purge_pairs CHECK (
        (storage_state = 'STORED' AND bytes_purged_at IS NULL)
        OR (storage_state = 'PURGED' AND bytes_purged_at IS NOT NULL)
    ),

    -- 스냅샷이 실제 계약과 어긋날 수 없다.
    CONSTRAINT task_input_capability_limit_fkey
        FOREIGN KEY (capability_id, capability_max_input_bytes)
            REFERENCES capability (id, max_input_bytes),

    -- task 가 복합 FK 로 잡을 대상.
    UNIQUE (id, capability_id)
);

COMMENT ON TABLE task_input IS
    'Core 가 중개해 받은 입력의 **메타**. 바이트는 별도 볼륨에 있고 여기엔 없다 (D22). '
    '증적 = 해시·누가·어디로 · 바이트 = 휘발성. PURGED 후에도 행은 남는다.';

CREATE INDEX IF NOT EXISTS task_input_stored_idx
    ON task_input (created_at) WHERE storage_state = 'STORED';

-- ── 4. task ↔ 입력 결속 ───────────────────────────────────────────────────

ALTER TABLE task
    ADD COLUMN IF NOT EXISTS input_id UUID;

COMMENT ON COLUMN task.input_id IS
    'Core 가 받은 입력. NULL 이면 데모 경로(caseId → Node 로컬 골든셋)다. '
    '복합 FK 로 capability 까지 묶이므로, 다른 능력의 입력을 끌어다 쓸 수 없다.';

-- **다른 능력의 입력을 쓸 수 없다.** 계약이 다르면 검증도 달랐기 때문이다.
ALTER TABLE task
    ADD CONSTRAINT task_input_capability_fkey
    FOREIGN KEY (input_id, capability_id)
        REFERENCES task_input (id, capability_id);

-- ── 5. GC 가 볼 것을 조회 가능하게 ────────────────────────────────────────
--
-- 정책이 워커 코드 안에만 있으면 「지금 무엇이 지워질 예정인가」를 사람이 못 본다.
-- 뷰로 드러낸다 — 「모른다」를 숨기지 않는다 (0008 agent_arch_unbound 와 같은 태도).

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
 WHERE ti.storage_state = 'STORED';

COMMENT ON VIEW task_input_purge_due IS
    '입력 바이트의 삭제 예정 시각 (D22). due_at <= now() 인 행이 워커 GC 대상이다. '
    'orphan-24h = task 에 연결되지 않은 업로드 · finished-7d = 종결 후 7일 · '
    'stale-72h = 미완료 task 최대 수명. 바이트만 지우고 행은 남긴다.';
