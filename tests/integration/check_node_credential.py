#!/usr/bin/env python3
"""Node 증서 발급·검증·폐기 (P2-4 · SD-002). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

1. 발급하면 **평문 시크릿이 한 번** 나오고, DB 에는 해시만 남는다 (C3)
2. 그 시크릿으로 검증하면 **node_id 가 해석된다** — URL 이 주장하는 값을 믿지 않는다 (SD-010)
3. 틀린 시크릿 · 없는 prefix · **폐기된 증서** · **만료된 증서** 는 거부된다
4. **Node 당 활성 증서는 하나** — 회전은 폐기 후 재발급
5. 증서에 **등급 컬럼이 없다** (절대규칙 4 · C1)
6. `last_used_at` 이 검증 시 갱신된다

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
from app.credential import (  # noqa: E402
    CredentialError,
    issue_credential,
    revoke_credential,
    split_token,
    verify_credential,
)

ADMIN = uuid.UUID("00000000-0000-4000-8000-000000000001")
NODE_TEAM = uuid.UUID("00000000-0000-4000-8000-000000000030")
NODE_TENANT = uuid.UUID("00000000-0000-4000-8000-000000000050")

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def refused(conn, fn, *a, **kw) -> bool:
    """거부를 기대하는 호출. SAVEPOINT 로 감싼다.

    DB 오류(UniqueViolation 등)로 거부되면 트랜잭션이 abort 되므로,
    감싸지 않으면 이후 문장이 전부 죽는다. 실제 API 는 호출마다 별도 트랜잭션이라 무관하다.
    """
    conn.execute("SAVEPOINT r")
    try:
        fn(*a, **kw)
    except CredentialError:
        conn.execute("ROLLBACK TO SAVEPOINT r")
        return True
    conn.execute("RELEASE SAVEPOINT r")
    return False


def main() -> int:
    print("Node 증서 (P2-4 · SD-002) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        if conn.execute(
            "SELECT to_regclass('public.node_credential') AS t"
        ).fetchone()["t"] is None:
            print("node_credential 이 없다 — migrations/0007 미적용", file=sys.stderr)
            return 1

        # 5. 등급 컬럼이 없어야 한다 (절대규칙 4)
        cols = {
            r["column_name"]
            for r in conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'node_credential'"
            ).fetchall()
        }
        forbidden = cols & {"trust_domain", "compute_tier_max", "is_gate_runner"}
        check(not forbidden, "증서에 등급 컬럼이 없다 (절대규칙 4)", ", ".join(forbidden))

        conn.execute("SAVEPOINT c")

        # 1. 발급 — 평문은 한 번, DB 에는 해시만
        issued = issue_credential(conn, node_id=NODE_TEAM, issued_by=ADMIN, label="시험")
        token = issued["secret"]
        prefix, secret = split_token(token)
        check(token.startswith("cn_") and "." in token, "토큰 형식 cn_xxxxxxxx.secret", prefix)

        stored = conn.execute(
            "SELECT secret_hash, key_prefix FROM node_credential WHERE id = %s",
            (str(issued["id"]),),
        ).fetchone()
        raw = bytes(stored["secret_hash"])
        check(secret.encode() not in raw and len(raw) == 32,
              "DB 에는 sha256 해시만 남는다 (C3)")

        # 2. 검증 → node_id 해석
        got = verify_credential(conn, token)
        check(got == NODE_TEAM, "검증하면 node_id 가 해석된다", str(got)[-12:])

        # 스킴 접두사도 받는다
        got2 = verify_credential(conn, f"CapNet-Node {token}")
        check(got2 == NODE_TEAM, "Authorization 스킴 접두사를 허용한다")

        # 6. last_used_at 갱신
        used = conn.execute(
            "SELECT last_used_at FROM node_credential WHERE id = %s", (str(issued["id"]),)
        ).fetchone()["last_used_at"]
        check(used is not None, "검증 시 last_used_at 이 갱신된다")

        # 3. 틀린 시크릿 / 없는 prefix / 형식 오류
        check(refused(conn, verify_credential, conn, f"{prefix}.{'x' * 43}"), "틀린 시크릿은 거부된다")
        check(refused(conn, verify_credential, conn, f"cn_deadbeef.{secret}"), "없는 prefix 는 거부된다")
        check(refused(conn, verify_credential, conn, "not-a-token"), "형식이 아니면 거부된다")

        # 4. 활성 증서는 하나
        check(refused(conn, issue_credential, conn, node_id=NODE_TEAM, issued_by=ADMIN),
              "Node 당 활성 증서는 하나다")

        # 폐기 → 거부 → 재발급 가능 (회전)
        rev = revoke_credential(conn, node_id=NODE_TEAM, reason="회전 시험")
        check(rev is not None and rev["revoked_at"] is not None, "폐기된다")
        check(refused(conn, verify_credential, conn, token), "폐기된 증서는 거부된다")

        again = issue_credential(conn, node_id=NODE_TEAM, issued_by=ADMIN, label="회전 후")
        check(verify_credential(conn, again["secret"]) == NODE_TEAM,
              "폐기 후 재발급하면 다시 쓸 수 있다 (회전)")

        # 만료 — 발급 시각도 함께 과거로 민다.
        # `ck_nc_expiry_after_issue` 가 「발급보다 이른 만료」를 막기 때문이다 (제약이 옳다).
        conn.execute(
            "UPDATE node_credential SET issued_at = now() - interval '2 hours', "
            "expires_at = now() - interval '1 hour' WHERE id = %s",
            (str(again["id"]),),
        )
        check(refused(conn, verify_credential, conn, again["secret"]), "만료된 증서는 거부된다")

        # 다른 Node 의 증서로 이 Node 를 주장할 수 없다 (해석값이 다르다)
        conn.execute("UPDATE node_credential SET revoked_at = now(), revoked_reason='정리' "
                     "WHERE node_id = %s AND revoked_at IS NULL", (str(NODE_TEAM),))
        t2 = issue_credential(conn, node_id=NODE_TENANT, issued_by=ADMIN)
        check(verify_credential(conn, t2["secret"]) == NODE_TENANT,
              "다른 Node 의 증서는 그 Node 로 해석된다 (사칭 불가)")

        # 이유 없는 폐기는 막힌다
        try:
            revoke_credential(conn, node_id=NODE_TENANT, reason="  ")
            check(False, "이유 없는 폐기는 거부된다", "통과했다")
        except ValueError:
            check(True, "이유 없는 폐기는 거부된다")

        conn.execute("ROLLBACK TO SAVEPOINT c")
        conn.rollback()

        left = conn.execute("SELECT count(*) AS n FROM node_credential").fetchone()["n"]
        check(left == 0, "격리: 증서가 롤백됐다", "" if left == 0 else f"{left}건 남음")

    failed = [r for r in results if not r[0]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        return 1
    print("Node 는 자기 등급을 주장할 수 없다 — 증서는 신원만 말한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
