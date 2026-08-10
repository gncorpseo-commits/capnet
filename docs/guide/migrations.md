# 마이그레이션 운용 (SD-007)

> 기존 볼륨을 `docker compose down -v` 없이 다음 세대로 올린다.
> 결정 근거: [`../context-handoff.md`](../context-handoff.md) §2-7 · [`../retrospective/register.md`](../retrospective/register.md) SD-007
> 유통 세대와의 관계: [`../design/product-distribution.md`](../design/product-distribution.md) §5 — **v제품-1 착수 관문**
>
> 갱신: 2026-08-10 (초판)

---

## 1. 왜 있는가

Phase 1 은 스키마 v4.4 동결 전제였으므로 DDL 적용 경로가 `docker-entrypoint-initdb.d` 일괄뿐이었다.
그 경로는 **빈 볼륨에서만** 돈다. 이미 데이터가 있는 볼륨은 `down -v`(전부 삭제) 말고는 올릴 수단이 없었다.

Phase 2 의 `node_credential` DDL(SD-002)은 v4.4 동결을 처음 건드리는 작업이고,
`product-distribution.md` §5 는 유통 세대를 올리는 조건으로 **「스키마 제약을 약화하지 않는다. DDL 추가와 마이그레이션(SD-007)만」** 을 못박았다.
그래서 마이그레이션 체계가 유통의 실질 첫 관문이다.

---

## 2. 쓰는 법

```bash
scripts/migrate.sh status         # 적용 상태 (기본값)
scripts/migrate.sh verify         # 체크섬·금지 패턴 검사 · 쓰기 없음
scripts/migrate.sh up --dry-run   # 적용될 목록만
scripts/migrate.sh up             # 실제 적용
```

`postgres` 만 떠 있으면 된다. `core` 이미지를 일회용으로 빌려 쓴다 (`score_n300.sh` 와 같은 패턴).

> **처음 한 번은 core 를 다시 빌드해야 한다.**
> 러너는 이미지 안의 `/app/migrations` 를 읽는데, 이 커밋 이전에 빌드된 `core` 이미지에는 그 디렉터리가 없다.
> `docker compose build core` 를 먼저 돌린다. 안 하면 `마이그레이션 디렉터리 없음` 으로 멈춘다 (아무것도 쓰지 않는다).
컨테이너 없이 직접 돌릴 수도 있다:

```bash
DATABASE_URL=postgresql://capnet:capnet@127.0.0.1:5432/capnet \
  python -m app.migrate status
```

종료 코드: `0` 정상 · `1` 드리프트/거부/실패.

---

## 3. 설계 (왜 이렇게 생겼나)

| 결정 | 이유 |
|------|------|
| **순방향 전용** — down/rollback 없음 | 절대규칙 1(제약 약화 금지)과 같은 방향. 되돌리기는 새 파일로 한다 |
| **0001 = no-op baseline** | 새 볼륨(initdb 가 schema.sql 적용)과 기존 볼륨이 **같은 길**을 타게 한다. baseline 을 실제 DDL 로 두면 두 경로가 갈라지고 그 순간 기존 볼륨 업그레이드가 깨진다 |
| **파일 1개 = 트랜잭션 1개** | 러너가 BEGIN/COMMIT 을 잡는다. 실패하면 그 파일만 롤백되고 앞 파일은 적용된 채 남는다 |
| **체크섬 고정** | 적용된 파일을 나중에 고치면 `verify`·`up` 이 거부한다. 적용된 마이그레이션은 수정하지 않고 새 파일을 추가한다 |
| **자문 잠금** | 러너가 동시에 여러 개 떠도 하나만 적용한다. 원장 생성도 잠금 안에서 한다 (`CREATE TABLE IF NOT EXISTS` 는 경합에 안전하지 않다) |
| **새 의존성 0** | alembic 을 넣지 않았다. `psycopg` 만 쓴다 (CLAUDE.md 「의존성 추가는 먼저 묻는다」) |

원장은 `schema_migration` 테이블 하나다 — `version · name · checksum · applied_at · applied_by`.

---

## 4. 절대규칙을 도구가 강제한다

문서에만 적힌 규칙은 언젠가 깨진다. 러너는 **적용 전에** 파일을 정적 검사하고, 하나라도 걸리면 **아무것도 적용하지 않는다.**

| 막는 것 | 근거 |
|---------|------|
| `DROP CONSTRAINT` · `DROP TABLE` · `DROP COLUMN` · `DROP NOT NULL` | 절대규칙 1 |
| `NOT VALID` · `DISABLE TRIGGER` · `SET CONSTRAINTS … DEFERRED` | 절대규칙 1 (우회) |
| `INSERT INTO assignment … VALUES` · `INSERT INTO gate_run … VALUES` | 절대규칙 2 — 스냅샷은 `INSERT … SELECT` 로만 |
| 파일 안의 `BEGIN` / `COMMIT` / `ROLLBACK` | 러너의 원자성 |
| 파일명 규칙 위반 · 버전 중복 · 버전 구멍 | 계보 무결성 |

제약을 정말 건드려야 하면 파일에 근거와 함께 `-- capnet:allow-constraint-change` 를 적는다.
그 표식은 리뷰에서 눈에 띄라고 있는 것이지 면허가 아니다 — `github-team-guide.md` 승인 절차를 그대로 탄다.

---

## 5. 새 마이그레이션 추가

1. `migrations/NNNN_snake_case.sql` 로 만든다. 번호는 마지막 +1, 구멍을 내지 않는다.
2. 맨 위 주석에 **무엇을·왜·무엇을 하지 않는가**를 적는다.
3. `scripts/migrate.sh verify` 로 정적 검사를 통과시킨다.
4. `scripts/migrate.sh up --dry-run` → `up`.
5. 적용한 뒤에는 그 파일을 **고치지 않는다.** 고칠 일이 생기면 새 번호로 추가한다.

DDL 은 **추가만** 한다 (절대규칙 1). 컬럼 추가는 `NOT NULL DEFAULT` 대신 3단계(널 허용 추가 → 백필 → 제약 추가)로 쪼갠다.

---

## 6. 지금 있는 마이그레이션

| # | 이름 | 내용 |
|---|------|------|
| 0001 | `baseline` | schema v4.4 를 계보 출발점으로 선언 (no-op · 검증만) |
| 0002 | `provenance_drift_view` | `provenance_drift` · `provenance_drift_summary` 뷰 추가 (읽기 전용) |

### 0002 를 왜 넣었나

v제품-0 의 유통 카피는 「증적이 남고 **조회된다**」이다.
그런데 골든셋이 교체되면 `capability.golden_set_sha256` 만 바뀌고, 이미 발급된 PASS 증서는
**다른 골든셋에서 얻은 것**인데도 라우팅 가능 상태로 남는다. 지금까지 이걸 조회할 수단이 없었다.

```sql
SELECT * FROM provenance_drift_summary;
```

`drifted_still_routable > 0` 이면 재게이트 대상이다. 뷰는 **보이게만** 한다 — sha 를 고치거나 증서를 지우지 않는다.
그것은 재게이트 결정을 동반하므로 사람이 정한다 (D15 · 절대규칙 8).

---

## 7. 한계

- **다운그레이드가 없다.** 의도한 것이다. 되돌리려면 되돌리는 마이그레이션을 새로 쓴다.
- **긴 잠금을 쪼개지 않는다.** 대형 테이블 `ALTER` 는 이 러너가 잠금 시간을 관리해 주지 않는다. Phase 3 규모에서 재검토한다.
- **정적 검사는 정규식이다.** 문자열 안에 숨긴 `DROP CONSTRAINT` 같은 건 잡지 못한다. 리뷰를 대체하지 않는다.
- **seed 는 마이그레이션이 아니다.** `apps/core/sql/seed.sql` 은 새 볼륨 부트스트랩용이고, 기존 볼륨에 재적용되지 않는다. 기존 볼륨에 들어가야 할 데이터 변경은 마이그레이션으로 쓴다.
