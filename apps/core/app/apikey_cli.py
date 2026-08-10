"""관리 API 키 부트스트랩 CLI.

    python -m app.apikey_cli issue --role admin --label bootstrap
    python -m app.apikey_cli issue --user <uuid> --label ci
    python -m app.apikey_cli list
    python -m app.apikey_cli revoke --prefix ck_1a2b3c4d

## 왜 CLI 인가

키 발급을 API 로만 하면 **첫 키를 만들 수 없다** — 강제를 켠 순간 잠긴다.
DB 에 직접 붙는 경로가 하나 필요하고, 그건 이미 DB 자격증명을 가진 사람만 쓸 수 있다.

`scripts/migrate.sh` 와 같은 자리다: 운영자가 서버 옆에서 도는 도구.
"""

from __future__ import annotations

import argparse
import sys
import uuid

import psycopg
from psycopg.rows import dict_row

from app.apikey import ROLE_RANK, ensure_user, issue_key, list_key_status, revoke_key
from app.config import settings


def _conn() -> psycopg.Connection:
    return psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False)


def cmd_issue(args: argparse.Namespace) -> int:
    with _conn() as conn:
        if args.user:
            user_id = uuid.UUID(args.user)
            row = conn.execute(
                "SELECT id, name, role FROM app_user WHERE id = %s", (str(user_id),)
            ).fetchone()
            if row is None:
                print(f"app_user 없음: {user_id}", file=sys.stderr)
                return 1
            user = dict(row)
        else:
            name = args.name or f"{args.role}-{uuid.uuid4().hex[:6]}"
            user = ensure_user(conn, name=name, role=args.role)

        out = issue_key(conn, user_id=user["id"], label=args.label)

    print(f"사용자 : {user['name']} ({user['role']}) · {user['id']}")
    print(f"prefix : {out['key_prefix']}")
    print()
    print("키 (이번 한 번만 보인다 — 저장은 해시만 된다):")
    print(f"  {out['secret']}")
    print()
    print("사용:")
    print(f"  curl -H 'Authorization: CapNet-Key {out['secret']}' ...")
    print("  파일로 보관하고 0600 으로 둔다. 커밋하지 않는다.")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    with _conn() as conn:
        rows = list_key_status(conn)
    if not rows:
        print("발급된 키가 없다.")
        return 0
    print(f"{'prefix':<14}{'역할':<12}{'사용자':<20}{'활성':<6}{'마지막 사용'}")
    for r in rows:
        used = r["last_used_at"].strftime("%Y-%m-%d %H:%M") if r["last_used_at"] else "-"
        print(f"{r['key_prefix']:<14}{r['role']:<12}{r['user_name']:<20}"
              f"{'예' if r['active'] else '아니오':<6}{used}")
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    with _conn() as conn:
        row = revoke_key(conn, key_prefix=args.prefix)
    if row is None:
        print(f"활성 키 없음: {args.prefix}", file=sys.stderr)
        return 1
    print(f"폐기됨: {row['key_prefix']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="app.apikey_cli", description="관리 API 키 (SD-010)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("issue", help="키를 발급한다 (평문은 이때 한 번만)")
    i.add_argument("--role", default="admin", choices=sorted(ROLE_RANK))
    i.add_argument("--user", help="기존 app_user UUID (없으면 새로 만든다)")
    i.add_argument("--name", help="새 사용자 이름")
    i.add_argument("--label", help="키 용도 메모")

    sub.add_parser("list", help="발급 상태 (시크릿·해시 미노출)")

    r = sub.add_parser("revoke", help="키를 폐기한다")
    r.add_argument("--prefix", required=True)

    args = ap.parse_args()
    return {"issue": cmd_issue, "list": cmd_list, "revoke": cmd_revoke}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
