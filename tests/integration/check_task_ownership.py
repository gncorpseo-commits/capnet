#!/usr/bin/env python3
"""작업 조회 소유권 (read-auth). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

`GET /v1/tasks/{id}` 응답에는 **결과(`result_ref`)와 증적**(어느 기기·어느 에이전트)이 들어 있다.
제품 문구가 「증적이 남고 조회된다」인데, 소유권 판정이 없으면 **「누구나 조회된다」**가 된다.

1. 소유자는 자기 작업을 본다
2. **다른 사용자는 404** — 403 이 아니다. 403 은 「그 id 는 존재한다」를 흘린다
3. **없는 작업도 404** — 둘이 구별되지 않아야 존재를 캐지 못한다
4. `developer` 이상은 남의 작업도 본다 (운영)
5. 키가 없으면(강제 꺼짐) 종전대로 통과한다 — 데모 경로를 깨지 않는다
6. 응답에 **요청자(`user_id`)가 실린다** — B0 가 기록한 것이 조회로 이어진다

## 왜 SAVEPOINT 로 안 굴리나

핸들러(`get_task`)는 **자기 커넥션을 연다.** 그래서 시험 데이터가 보이려면 **커밋해야** 한다 —
`check_revocation` 과 같은 사정이다. 대신 만든 행을 끝에서 **명시적으로 지운다**.
러너(`run_integration.sh`)가 검사마다 DB 를 복제해 주므로 남아도 다른 검사를 오염시키지 않는다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import importlib
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.apikey import ensure_user, issue_key  # noqa: E402
from app.config import settings  # noqa: E402

CAP = "00000000-0000-4000-8000-000000000010"

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def status_of(fn, *args) -> int | str:
    from fastapi import HTTPException

    try:
        fn(*args)
    except HTTPException as exc:
        return exc.status_code
    return "pass"


def load_main(*, api_key: bool):
    """강제 플래그는 모듈 상수라 임포트 시점에 굳는다 — reload 로 양쪽을 본다."""
    os.environ["REQUIRE_API_KEY"] = "1" if api_key else "0"
    import app.main as m  # noqa: PLC0415

    return importlib.reload(m)


def main() -> int:
    print("작업 조회 소유권 (read-auth) — 커밋하고 끝에서 지운다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        # 두 사용자 — 소유자(user)와 남(user), 그리고 운영자(developer)
        owner = ensure_user(conn, name="owner-probe", role="user")
        other = ensure_user(conn, name="other-probe", role="user")
        oper = ensure_user(conn, name="oper-probe", role="developer")
        owner_key = issue_key(conn, user_id=owner["id"], label="owner")["secret"]
        other_key = issue_key(conn, user_id=other["id"], label="other")["secret"]
        oper_key = issue_key(conn, user_id=oper["id"], label="oper")["secret"]

        task_id = conn.execute(
            """
            INSERT INTO task (user_id, capability_id, status, trust_domain,
                              capability_trust_domain_min, input_ref, result_ref)
            SELECT %s, c.id, 'COMPLETED', 'team', c.trust_domain_min,
                   '{"caseId":"ic1-0001"}', '{"label":"annual_crop"}'
              FROM capability c WHERE c.id = %s
            RETURNING id
            """,
            (str(owner["id"]), CAP),
        ).fetchone()["id"]
        conn.commit()  # 핸들러는 자기 커넥션을 연다 — 보이려면 커밋해야 한다

        try:
            m = load_main(api_key=True)
            print("  [REQUIRE_API_KEY=1]")

            check(status_of(m.get_task, task_id, None) == 401, "무인증 조회 → 401")

            got = m.get_task(task_id, f"CapNet-Key {owner_key}")
            check(str(got["id"]) == str(task_id), "소유자는 자기 작업을 본다")
            check(str(got.get("user_id")) == str(owner["id"]),
                  "응답에 요청자가 실린다 (B0 가 기록한 것)", str(got.get("user_id"))[:8])
            check(got.get("result_ref") is not None, "결과가 실린다 — 그래서 잠가야 한다")

            check(status_of(m.get_task, task_id, f"CapNet-Key {other_key}") == 404,
                  "남의 작업은 404 (403 이면 존재를 흘린다)")

            missing = uuid.uuid4()
            check(status_of(m.get_task, missing, f"CapNet-Key {other_key}") == 404,
                  "없는 작업도 404 — 둘이 구별되지 않는다")

            got = m.get_task(task_id, f"CapNet-Key {oper_key}")
            check(str(got["id"]) == str(task_id), "developer 는 남의 작업도 본다 (운영)")

            # ── 강제 꺼짐: 데모 경로가 안 깨진다 ─────────────────────────
            m = load_main(api_key=False)
            print("\n  [REQUIRE_API_KEY=0 — 데모 경로]")
            got = m.get_task(task_id, None)
            check(str(got["id"]) == str(task_id), "키 없으면 종전대로 통과한다")
            check(status_of(m.get_task, task_id, f"CapNet-Key {other_key}") == 404,
                  "꺼져 있어도 키가 오면 소유권은 본다")
        finally:
            os.environ.pop("REQUIRE_API_KEY", None)
            # 커밋했으므로 손으로 지운다 (위 「왜 SAVEPOINT 로 안 굴리나」 참조)
            conn.execute("DELETE FROM task WHERE id = %s", (str(task_id),))
            conn.execute(
                "DELETE FROM api_key WHERE user_id = ANY(%s)",
                ([str(owner["id"]), str(other["id"]), str(oper["id"])],),
            )
            conn.execute(
                "DELETE FROM app_user WHERE id = ANY(%s)",
                ([str(owner["id"]), str(other["id"]), str(oper["id"])],),
            )
            conn.commit()
            left = conn.execute(
                "SELECT count(*) AS n FROM app_user WHERE name LIKE '%-probe'"
            ).fetchone()["n"]
            check(left == 0, "격리: 시험 사용자·작업이 지워졌다", f"{left}건 남음")

    ok = sum(1 for r in results if r[0])
    print(f"\n{ok}/{len(results)} 통과")
    if ok != len(results):
        return 1
    print("증적은 남고 조회된다 — 다만 자기 것만.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
