#!/usr/bin/env python3
"""관리 API 인증 (SD-010 나머지 절반). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 왜 이 검사가 있나

이 기능 이전에는 관리 API 에 **인증이 없었다.** 실측으로 익명 요청이
`team` · `L등급` · **게이트러너** Node 를 등록하고 증서까지 받았다.
게이트러너가 되면 자기 Agent 를 자기가 채점해 통과시킬 수 있다 —
FK 사슬·증적·Node 증서가 전부 그 위에 쌓은 심층 방어인데 정문이 열려 있었다.

## 무엇을 고정하나

1. 발급하면 평문이 **한 번만** 나오고 DB 에는 해시만 남는다
2. 검증하면 `{user_id, role, name}` 이 해석된다
3. 틀린 키 · 없는 prefix · **폐기된 키** 는 거부된다
4. **역할 순위가 표로 판정된다** — 문자열 정렬이 아니다 (`user < developer < admin`)
5. 새 테이블을 만들지 않았다 — `app_user`·`api_key` 는 v4.4 부터 있었다
6. `key_prefix` 가 UNIQUE 다 (0009) — 중복되면 검증이 모호해진다

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.apikey import (  # noqa: E402
    ROLE_RANK,
    ApiKeyError,
    Forbidden,
    assert_role,
    ensure_user,
    issue_key,
    looks_like_api_key,
    revoke_key,
    split_token,
    verify_key,
)
from app.config import settings  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def refused(conn, fn, *a, **kw) -> bool:
    conn.execute("SAVEPOINT r")
    try:
        fn(*a, **kw)
    except ApiKeyError:
        conn.execute("ROLLBACK TO SAVEPOINT r")
        return True
    conn.execute("RELEASE SAVEPOINT r")
    return False


def main() -> int:
    print("관리 API 인증 (SD-010) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        # 5. 새 테이블을 만들지 않았다
        for tbl in ("app_user", "api_key"):
            got = conn.execute(
                "SELECT to_regclass(%s) AS t", (f"public.{tbl}",)
            ).fetchone()["t"]
            check(got is not None, f"{tbl} 는 v4.4 부터 있던 테이블이다")

        # 6. prefix UNIQUE (0009)
        uniq = conn.execute(
            "SELECT count(*) AS n FROM pg_indexes "
            "WHERE tablename='api_key' AND indexname='api_key_prefix_unique'"
        ).fetchone()["n"]
        check(uniq == 1, "key_prefix 가 UNIQUE 다 (0009)")

        conn.execute("SAVEPOINT a")

        # 1. 발급 — 평문은 한 번, DB 엔 해시만
        admin = ensure_user(conn, name="probe-admin", role="admin")
        issued = issue_key(conn, user_id=admin["id"], label="시험")
        token = issued["secret"]
        prefix, secret = split_token(token)
        check(token.startswith("ck_") and "." in token, "토큰 형식 ck_xxxxxxxx.secret", prefix)

        raw = bytes(conn.execute(
            "SELECT key_hash FROM api_key WHERE id = %s", (str(issued["id"]),)
        ).fetchone()["key_hash"])
        check(secret.encode() not in raw and len(raw) == 32, "DB 에는 sha256 해시만 남는다")

        # 2. 검증 → 사용자·역할 해석
        actor = verify_key(conn, token)
        check(actor["role"] == "admin" and actor["user_id"] == admin["id"],
              "검증하면 사용자·역할이 해석된다", actor["role"])
        check(verify_key(conn, f"CapNet-Key {token}")["role"] == "admin",
              "Authorization 스킴 접두사를 허용한다")

        used = conn.execute(
            "SELECT last_used_at FROM api_key WHERE id = %s", (str(issued["id"]),)
        ).fetchone()["last_used_at"]
        check(used is not None, "검증 시 last_used_at 이 갱신된다")

        # 3. 거부 경로
        check(refused(conn, verify_key, conn, f"{prefix}.{'x' * 43}"), "틀린 시크릿은 거부된다")
        check(refused(conn, verify_key, conn, f"ck_deadbeef.{secret}"), "없는 prefix 는 거부된다")
        check(refused(conn, verify_key, conn, "not-a-token"), "형식이 아니면 거부된다")

        revoke_key(conn, key_prefix=prefix)
        check(refused(conn, verify_key, conn, token), "폐기된 키는 거부된다")

        # 4. 역할 순위 — 문자열 정렬이 아니다
        check(ROLE_RANK["user"] < ROLE_RANK["developer"] < ROLE_RANK["admin"],
              "역할 순위가 표로 정의된다 (user<developer<admin)")

        def forbidden(role: str, need: str) -> bool:
            try:
                assert_role({"role": role}, need)
                return False
            except Forbidden:
                return True

        check(forbidden("user", "admin"), "user 는 admin 을 못 한다")
        check(forbidden("user", "developer"), "user 는 developer 를 못 한다")
        check(forbidden("developer", "admin"), "developer 는 admin 을 못 한다")
        check(not forbidden("admin", "user"), "admin 은 user 를 할 수 있다")
        check(not forbidden("developer", "user"), "developer 는 user 를 할 수 있다")
        check(forbidden("nosuchrole", "user"), "모르는 역할은 아무것도 못 한다")

        # 스킴 구분 — Node 증서와 섞이지 않는다
        check(looks_like_api_key("CapNet-Key ck_1.2"), "API 키 스킴을 알아본다")
        check(not looks_like_api_key("CapNet-Node cn_1.2"), "Node 증서를 API 키로 보지 않는다")
        check(not looks_like_api_key(None), "헤더 없음은 키가 아니다")

        conn.execute("ROLLBACK TO SAVEPOINT a")
        conn.rollback()

        left = conn.execute(
            "SELECT count(*) AS n FROM app_user WHERE name = 'probe-admin'"
        ).fetchone()["n"]
        check(left == 0, "격리: 시험 사용자가 롤백됐다")

    failed = [r for r in results if not r[0]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        return 1
    print("관리 API 는 이제 누구인지 묻는다 — 정문이 닫혔다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
