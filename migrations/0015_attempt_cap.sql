-- 0015 · 배정 재시도 상한 (조용한 무한 재시도를 닫는다)
--
-- 무엇이 문제였나
--   계약이 모델과 맞지 않으면 Node 실행이 매번 깨진다. 그런데
--     1. Node 는 그 실패를 **Core 에 보고하지 않았다** — 로그에만 쌓였다
--     2. `attempt_no` 는 스키마에 있었지만 **아무도 세지 않았다** (항상 1)
--   그래서 lease 가 만료되면 회수 → QUEUED → 다시 배정 → 또 실패가 **72h TIMEOUT 까지** 돈다.
--   실측: 선언을 잘못 고친 능력 하나로 Node 로그에 채널 불일치 38건이 쌓였다.
--
--   「조용히 무한 재시도」는 운영에서 보이지 않는다. 실패는 **횟수로 세어지고 멈춰야** 한다.
--
-- 상한을 어디에 두나
--   능력별로 둔다 (`capability.max_attempts`). 무거운 능력은 몇 번 더 시도할 값어치가 있고,
--   가벼운 능력은 빨리 포기하는 편이 낫다. 기본 5 — 일시적 장애(기기 재시작·네트워크)를
--   넘기기에 충분하고, 계약이 잘못된 경우를 오래 끌지 않는다.
--
-- 앱이 세고 DB 가 막는다
--   claim 이 시도 횟수를 세어 `attempt_no` 에 적고, 상한에 닿은 task 는 애초에 고르지 않는다.
--   그래도 **DB 가 마지막 방어선**이다 — 스냅샷 + 복합 FK + CHECK 로 상한 초과 배정을 거절한다.
--
-- 추가만 (절대규칙 1) — 컬럼 2 · CHECK 2 · UNIQUE 1 · FK 1. 삭제·완화 없음.

-- ── 1. capability: 시도 상한 ──────────────────────────────────────────────

ALTER TABLE capability
    ADD COLUMN IF NOT EXISTS max_attempts INT NOT NULL DEFAULT 5;

COMMENT ON COLUMN capability.max_attempts IS
    '한 task 에 허용하는 배정 시도 횟수. 넘으면 task 를 FAILED 로 종결한다 (0015). '
    '기본 5 — 일시적 장애는 넘기고 잘못된 계약은 오래 끌지 않는 값.';

ALTER TABLE capability
    ADD CONSTRAINT ck_capability_max_attempts
    CHECK (max_attempts >= 1 AND max_attempts <= 50);

-- assignment 가 복합 FK 로 참조할 대상 (max_input_bytes 와 같은 관례).
ALTER TABLE capability
    ADD CONSTRAINT capability_id_max_attempts_key UNIQUE (id, max_attempts);

-- ── 2. assignment: 몇 번째 시도인가 ───────────────────────────────────────
--
-- `attempt_no` 는 이미 있다 (기본 1). 상한 스냅샷을 붙여 **DB 가 초과를 거절**하게 한다.
-- 기존 행은 attempt_no=1 · 스냅샷 기본 5 라 CHECK·FK 를 그대로 통과한다.

ALTER TABLE assignment
    ADD COLUMN IF NOT EXISTS capability_max_attempts INT NOT NULL DEFAULT 5;

COMMENT ON COLUMN assignment.capability_max_attempts IS
    '배정 시점 capability.max_attempts 스냅샷 (0015). 복합 FK 로 실제 값과 묶인다 — '
    '나중에 상한이 바뀌어도 이 배정이 어떤 상한 아래 만들어졌는지가 남는다.';

ALTER TABLE assignment
    ADD CONSTRAINT ck_assignment_attempt_within_cap
    CHECK (attempt_no >= 1 AND attempt_no <= capability_max_attempts);

ALTER TABLE assignment
    ADD CONSTRAINT assignment_capability_max_attempts_fkey
    FOREIGN KEY (capability_id, capability_max_attempts)
        REFERENCES capability (id, max_attempts);

-- ── 3. 상한에 닿은 task 를 조회 가능하게 ──────────────────────────────────
--
-- 워커가 이 뷰를 보고 종결한다. 정책이 코드 안에만 있으면 「왜 멈췄나」를 사람이 못 본다
-- (task_input_purge_due 와 같은 태도).

CREATE OR REPLACE VIEW task_attempts_exhausted AS
SELECT
    t.id            AS task_id,
    t.capability_id,
    c.code          AS capability_code,
    c.max_attempts,
    count(a.id)     AS attempts,
    max(a.finished_at) AS last_attempt_at
  FROM task t
  JOIN capability c ON c.id = t.capability_id
  LEFT JOIN assignment a ON a.task_id = t.id
 WHERE t.status IN ('CREATED', 'QUEUED', 'ASSIGNED')
 GROUP BY t.id, t.capability_id, c.code, c.max_attempts
HAVING count(a.id) >= c.max_attempts;

COMMENT ON VIEW task_attempts_exhausted IS
    '시도 상한을 다 쓴 미완료 task (0015). 워커가 이걸 보고 FAILED 로 종결한다. '
    '「왜 멈췄나」를 SQL 로 볼 수 있어야 한다.';
