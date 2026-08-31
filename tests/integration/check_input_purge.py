#!/usr/bin/env python3
"""입력 바이트 보존·삭제 (D22 · 0011 · 0013 B2). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 왜 있는가

**D22 는 Core 중개 수집을 허용하면서 「보존·삭제 정책이 선행 조건」이라고 못박았다.**
그 정책은 구현돼 있다 — `task_input_purge_due` 뷰 · `mark_purged` · Core 워커의 GC.
**그런데 검사가 하나도 없었다.**

없으면 무엇이 조용히 무너지나:

- 뷰의 `NOT EXISTS (… capability.sample_input_id …)` 가 빠지면 **계약 샘플 바이트가
  24시간 뒤 지워지고**, 그 뒤 계약 게이트가 통째로 못 돈다 (0013 B2)
- `mark_purged` 가 행을 지우게 바뀌면 **「어디로 갔는지 답할 수 있다」가 거짓**이 된다 —
  제품 주장이 사라지는데 아무도 모른다
- `WHERE storage_state = 'STORED'` 가 빠지면 이미 지운 것을 계속 다시 집는다

## 무엇을 고정하나

1. **정책이 SQL 에 있다** — 뷰가 `reason` 세 종(`orphan-24h`·`finished-7d`·`stale-72h`)을 낸다
2. **바이트만 지우고 행은 남는다** — `PURGED` 뒤에도 `sha256`·`byte_size`·`uploaded_by` 가 그대로다
3. **계약 샘플은 대상이 아니다** (0013 B2)
4. 아직 살아 있는 task 의 입력은 **due 가 아니다**
5. `mark_purged` 는 **STORED 인 것만** 바꾼다 (두 번 돌려도 안전)
6. 이미 `PURGED` 인 것은 **다시 목록에 안 뜬다**

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.config import settings  # noqa: E402
from app.inputs import get as get_input  # noqa: E402
from app.inputs import mark_purged, purge_due  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


CAP_SQL = """
INSERT INTO capability (code, version, name, input_schema, output_schema, output_kind,
                        compute_tier, trust_domain_min, golden_set_ref, golden_set_sha256,
                        golden_set_size, golden_metrics, quality_profile, max_input_bytes)
VALUES (%(code)s, 1, 'purge probe', '{}'::jsonb, '{}'::jsonb, 'structured',
        'M', 'team', '(none)', %(zero)s, 1, '{}'::jsonb, 'none', 4096)
RETURNING id
"""

# 스냅샷 컬럼을 앱이 계산해 넣지 않는다 (절대규칙 2) — capability 에서 복사해 온다.
INPUT_SQL = """
INSERT INTO task_input (id, capability_id, sha256, byte_size, media_type, uploaded_by,
                        capability_max_input_bytes, created_at)
SELECT %(id)s, c.id, %(sha)s, %(size)s, 'text/plain', %(uploader)s,
       c.max_input_bytes, now() - (%(age_hours)s || ' hours')::interval
  FROM capability c
 WHERE c.id = %(cap)s
RETURNING id
"""

# `uploaded_by` 는 `app_user` 를 가리키는 FK 다 — 아무 값이나 못 넣는다.
# 시드에 있는 사용자를 쓴다 (증적의 「누가 올렸나」가 실제 사람을 가리켜야 뜻이 있다).
ANY_USER_SQL = "SELECT id FROM app_user ORDER BY created_at LIMIT 1"

# `capability_trust_domain_min` 은 **스냅샷**이고 복합 FK 가 걸려 있다 —
# 앱이 계산해 넣지 않고 `capability` 에서 복사해 온다 (절대규칙 2 와 같은 태도).
TASK_SQL = """
INSERT INTO task (user_id, capability_id, status, trust_domain,
                  capability_trust_domain_min, input_id, created_at, finished_at)
SELECT %(user)s, c.id, %(status)s, 'team',
       c.trust_domain_min, %(input)s,
       now() - (%(age_hours)s || ' hours')::interval,
       CASE WHEN %(finished_hours)s::int IS NULL THEN NULL
            ELSE now() - (%(finished_hours)s || ' hours')::interval END
  FROM capability c
 WHERE c.id = %(cap)s
RETURNING id
"""


def due_rows(conn: psycopg.Connection, input_id) -> list[dict]:
    return [r for r in purge_due(conn, limit=500) if str(r["task_input_id"]) == str(input_id)]


def view_row(conn: psycopg.Connection, input_id) -> dict | None:
    row = conn.execute(
        "SELECT reason, due_at, task_status FROM task_input_purge_due WHERE task_input_id = %s",
        (str(input_id),),
    ).fetchone()
    return dict(row) if row else None


def new_input(conn, cap_id, uploader, *, age_hours: int) -> uuid.UUID:
    input_id = uuid.uuid4()
    conn.execute(INPUT_SQL, {
        "id": str(input_id), "cap": cap_id, "sha": "a" * 64, "size": 1234,
        "uploader": uploader, "age_hours": age_hours,
    })
    return input_id


def run(conn: psycopg.Connection) -> None:
    conn.execute("SAVEPOINT probe")
    cap_id = conn.execute(
        CAP_SQL, {"code": f"probe.purge.{uuid.uuid4().hex[:8]}", "zero": "0" * 64}
    ).fetchone()["id"]
    uploader = conn.execute(ANY_USER_SQL).fetchone()["id"]

    # --- 1. 고아 업로드: task 가 없고 24h 지났다 -------------------------------
    orphan = new_input(conn, cap_id, uploader, age_hours=25)
    row = view_row(conn, orphan)
    check(row is not None and row["reason"] == "orphan-24h",
          "task 없는 업로드는 24h 뒤 orphan-24h", str(row and row["reason"]))
    check(bool(due_rows(conn, orphan)), "그리고 실제로 목록에 뜬다")

    fresh = new_input(conn, cap_id, uploader, age_hours=1)
    check(not due_rows(conn, fresh), "1시간짜리 고아는 아직 아니다")

    # --- 2. 종결된 task: 7일 -------------------------------------------------
    done = new_input(conn, cap_id, uploader, age_hours=200)
    conn.execute(TASK_SQL, {"user": uploader, "cap": cap_id, "input": str(done), "status": "COMPLETED",
                            "age_hours": 200, "finished_hours": 200})
    row = view_row(conn, done)
    check(row is not None and row["reason"] == "finished-7d",
          "종결된 task 의 입력은 finished-7d", str(row and row["reason"]))
    check(bool(due_rows(conn, done)), "종결 후 7일이 지나면 목록에 뜬다")

    recent = new_input(conn, cap_id, uploader, age_hours=2)
    conn.execute(TASK_SQL, {"user": uploader, "cap": cap_id, "input": str(recent), "status": "COMPLETED",
                            "age_hours": 2, "finished_hours": 1})
    check(not due_rows(conn, recent), "**방금 끝난 task 의 입력은 아직 안 지운다**")

    # --- 3. 미완료 task: 72h -------------------------------------------------
    stale = new_input(conn, cap_id, uploader, age_hours=100)
    conn.execute(TASK_SQL, {"user": uploader, "cap": cap_id, "input": str(stale), "status": "QUEUED",
                            "age_hours": 100, "finished_hours": None})
    row = view_row(conn, stale)
    check(row is not None and row["reason"] == "stale-72h",
          "미완료 task 는 72h 가 최대 수명", str(row and row["reason"]))

    running = new_input(conn, cap_id, uploader, age_hours=1)
    conn.execute(TASK_SQL, {"user": uploader, "cap": cap_id, "input": str(running), "status": "RUNNING",
                            "age_hours": 1, "finished_hours": None})
    check(not due_rows(conn, running), "**도는 중인 task 의 입력은 안 지운다**")

    # --- 4. 계약 샘플은 대상이 아니다 (0013 B2) ------------------------------
    sample = new_input(conn, cap_id, uploader, age_hours=999)
    check(bool(due_rows(conn, sample)), "샘플로 붙기 전에는 고아라 대상이다")
    conn.execute("UPDATE capability SET sample_input_id = %s WHERE id = %s",
                 (str(sample), cap_id))
    check(not due_rows(conn, sample),
          "**계약 샘플로 붙으면 대상에서 빠진다** — 안 그러면 게이트가 못 돈다 (B2)")
    check(view_row(conn, sample) is None, "뷰에서 아예 사라진다")

    # --- 5. 바이트만 지우고 행은 남는다 --------------------------------------
    before = get_input(conn, orphan)
    marked = mark_purged(conn, orphan)
    after = get_input(conn, orphan)
    check(marked is not None and after is not None, "PURGED 로 표시해도 행이 남는다")
    check(after["storage_state"] == "PURGED", "상태가 PURGED", str(after["storage_state"]))
    check(after["bytes_purged_at"] is not None, "언제 지웠는지 남는다")
    kept = all(after[c] == before[c] for c in ("sha256", "byte_size", "media_type", "uploaded_by"))
    check(kept, "**증적(sha256·크기·MIME·올린 주체)이 그대로다** — 「어디로 갔는지」에 답한다")

    # --- 6. 두 번 돌려도 안전하고, 다시 안 뜬다 ------------------------------
    check(mark_purged(conn, orphan) is None, "이미 PURGED 면 다시 바꾸지 않는다 (STORED 만)")
    check(not due_rows(conn, orphan), "PURGED 는 목록에서 빠진다 — 무한 재시도가 없다")

    conn.execute("ROLLBACK TO SAVEPOINT probe")


def main() -> int:
    print("== 입력 바이트 보존·삭제 (D22 선행 조건) ==")
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        run(conn)

    failed = [n for ok, n, _ in results if not ok]
    print(f"\n===== 결과: 통과 {len(results) - len(failed)} · 실패 {len(failed)} =====")
    if failed:
        for name in failed:
            print(f"  FAIL {name}")
        return 1
    print("바이트는 지워지고 증적은 남는다 — 정책은 뷰가 갖는다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
