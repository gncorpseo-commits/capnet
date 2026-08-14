-- 0017 · 조직 경계 (D24 — 등급과 소속을 분리한다)
--
-- 무엇이 문제였나
--   `trust_domain='tenant'` 는 **민감도 등급**이지 **어느 조직**이 아니다.
--   tenant 가 둘이면 둘 다 `'tenant'` 라 `domain_compatible` 이 구별할 수가 없다.
--   실측: 조직 A 의 작업이 조직 B 의 tenant 기기에 **배정됐다.** 막는 것이 없었다.
--
--   이건 조회 문제가 아니라 **실행 문제**다. read-auth(#69)로 「누가 볼 수 있나」는 닫았지만
--   「어디서 도는가」는 열려 있었다. 제품 주장(「승인하지 않은 신뢰 도메인으로 라우팅되지
--   않는다」)은 참이지만, **같은 등급의 다른 조직**은 승인한 적이 없는데도 라우팅됐다.
--
--   그리고 소유자 컬럼은 이미 있는데 죽어 있었다 — `node.owner_id`·`agent.owner_id` 가
--   앱에서 전부 시드 admin 으로 하드코딩됐다. 진짜인 것은 `task.user_id` 하나뿐이었다(B0).
--
-- 설계 — 도메인·티어와 **같은 모양**
--   조직을 **별도 축**으로 둔다(등급과 섞지 않는다). 배정에 스냅샷을 싣고,
--   **판정은 CHECK 와 복합 FK 가** 한다. 앱은 후보를 고르기만 한다 (절대규칙 2).
--
--     ck_assignment_org — 같은 조직이거나, 공용 기기이거나. 그것뿐이다.
--
--   행렬 테이블이 필요 없다 — 도메인·티어와 달리 **순서가 아니라 동일성**이기 때문이다.
--
-- 지금 동작을 깨지 않는다 (D24-3)
--   기존 `app_user`·`task` 는 `default` org 로 백필하고, **기존 Node 는 NULL(공용)로 둔다.**
--   NULL = 팀이 운영하는 공용 기기이며 **모든 조직의 작업을 받는다.** 그래서 데모·심사 경로는
--   그대로 돈다. `NOT NULL` 승격은 하지 않는다 — 조직을 쓰지 않는 배포를 계속 지원한다.
--
-- 추가만 (절대규칙 1) — 테이블 1 · 컬럼 6 · CHECK 1 · UNIQUE 2 · FK 2. 삭제·완화 없음.

-- ── 1. 조직 ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS org (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE org IS
    '조직 (0017 · D24). trust_domain 과 다른 축이다 — 등급은 민감도, org 는 소속. '
    'node.org_id IS NULL 은 팀이 운영하는 공용 기기이며 모든 조직의 작업을 받는다.';

-- 기존 행이 갈 곳. 조직을 쓰지 않는 배포에서도 이 하나로 돈다.
INSERT INTO org (id, code, name)
VALUES ('00000000-0000-4000-8000-0000000000f0', 'default', '기본 조직')
ON CONFLICT (code) DO NOTHING;

-- ── 2. 소속 ───────────────────────────────────────────────────────────────

ALTER TABLE app_user ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES org(id);
ALTER TABLE node     ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES org(id);
ALTER TABLE task     ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES org(id);

COMMENT ON COLUMN node.org_id IS
    '이 기기를 내놓은 조직. NULL = 팀 운영 공용 기기 — 모든 조직의 작업을 받는다 (D24-1).';
COMMENT ON COLUMN task.org_id IS
    '요청자의 조직 스냅샷. 배정 판정(ck_assignment_org)의 한쪽 항이다.';

-- 초대가 조직을 정하는 자리다 (G2 와 같은 모양 — 신청자가 주장하지 못한다).
ALTER TABLE node_invite ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES org(id);
COMMENT ON COLUMN node_invite.org_id IS
    '초대로 들어온 기기가 속할 조직. 등급과 마찬가지로 발행 시점에 박힌다 (절대규칙 4).';

-- 백필 — 기존 사용자·작업은 default 로. **Node 는 건드리지 않는다** (NULL = 공용).
UPDATE app_user SET org_id = '00000000-0000-4000-8000-0000000000f0' WHERE org_id IS NULL;
UPDATE task     SET org_id = '00000000-0000-4000-8000-0000000000f0' WHERE org_id IS NULL;

-- ── 3. 배정 판정 (스냅샷 + 복합 FK + CHECK) ──────────────────────────────

ALTER TABLE node ADD CONSTRAINT node_id_org_key UNIQUE (id, org_id);
ALTER TABLE task ADD CONSTRAINT task_id_org_key UNIQUE (id, org_id);

ALTER TABLE assignment ADD COLUMN IF NOT EXISTS task_org_id UUID;
ALTER TABLE assignment ADD COLUMN IF NOT EXISTS node_org_id UUID;

-- 스냅샷이 진짜 행과 같아야 한다. 값이 NULL 이면 FK 는 검사하지 않는다(MATCH SIMPLE) —
-- 그래서 기존 배정 행과 공용 기기(org_id IS NULL)가 그대로 통과한다.
ALTER TABLE assignment
    ADD CONSTRAINT assignment_task_org_fkey
    FOREIGN KEY (task_id, task_org_id) REFERENCES task (id, org_id);
ALTER TABLE assignment
    ADD CONSTRAINT assignment_node_org_fkey
    FOREIGN KEY (node_id, node_org_id) REFERENCES node (id, org_id);

-- 요점 한 줄 — **같은 조직이거나, 공용 기기이거나.**
--
-- `IS NOT DISTINCT FROM` 을 쓰는 것은 NULL 안전을 위해서다. 그냥 `=` 로 쓰면
-- task_org_id 가 NULL 인 행(조직을 안 쓰는 배포)이 **어느 조직 기기로든** 통과한다 —
-- 비교 결과가 NULL 이고 CHECK 는 NULL 을 통과시키기 때문이다. 그건 바로 이 마이그레이션이
-- 닫으려는 구멍이므로, 「모르면 거절」로 못박는다.
ALTER TABLE assignment
    ADD CONSTRAINT ck_assignment_org
    CHECK (node_org_id IS NULL OR node_org_id IS NOT DISTINCT FROM task_org_id);

COMMENT ON CONSTRAINT ck_assignment_org ON assignment IS
    '조직 경계 (D24). 공용 기기(node_org_id IS NULL)가 아니면 작업과 같은 조직이어야 한다.';

-- ── 4. 조회 편의 ─────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS node_org_idx ON node (org_id);
CREATE INDEX IF NOT EXISTS task_org_idx ON task (org_id);
