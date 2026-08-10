"""SD-007 마이그레이션 러너 — 순방향 전용.

기존 볼륨을 `docker compose down -v` 없이 다음 세대로 올린다.
새 의존성을 쓰지 않는다 (psycopg 만 · CLAUDE.md 「의존성 추가는 먼저 묻는다」).

설계 원칙
- **순방향만.** down/rollback 이 없다. 절대규칙 1(제약 약화 금지)과 같은 방향이다.
- **파일 1개 = 트랜잭션 1개.** BEGIN/COMMIT 은 러너가 잡는다. 파일 안에 쓰면 거부한다.
- **체크섬 고정.** 적용된 파일이 나중에 바뀌면 `verify` 가 실패한다.
- **절대규칙을 기계가 강제한다.** 금지 패턴(제약 약화 · assignment/gate_run 수기 INSERT)을
  적용 **전에** 정적으로 막는다. 문서에만 적힌 규칙은 언젠가 깨진다.

사용:
    python -m app.migrate status
    python -m app.migrate up [--dry-run]
    python -m app.migrate verify
"""

from __future__ import annotations

import argparse
import sys

import psycopg
from psycopg.rows import dict_row

from app.config import settings

# 정적 검사·로딩은 DB 를 모르는 모듈에 있다 (표준 라이브러리만 · 단독 테스트 가능).
from app.migrate_lint import (
    ALLOW_MARKER,
    MigrationError,
    default_migrations_dir,
    lint,
    load_migrations,
)

__all__ = ["ALLOW_MARKER", "lint", "load_migrations", "main"]

# 러너가 단독으로 도는 것을 보장하는 자문 잠금 키 (임의 상수).
ADVISORY_LOCK_KEY = 0x43_41_50_4E_45_54_07  # "CAPNET" + 07 (SD-007)


# baseline 스키마가 있는지 확인하는 최소 표본. 마이그레이션은 baseline 위에서만 의미가 있다.
BASELINE_TABLES = ("capability", "agent", "node", "task", "assignment", "gate_run")

SCHEMA_MIGRATION_DDL = """
CREATE TABLE IF NOT EXISTS schema_migration (
    version     INT         PRIMARY KEY,
    name        TEXT        NOT NULL,
    checksum    TEXT        NOT NULL CHECK (checksum ~ '^[0-9a-f]{64}$'),
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_by  TEXT        NOT NULL DEFAULT current_user
)
"""


def _assert_baseline(conn: psycopg.Connection) -> None:
    """schema.sql 이 먼저 적용돼 있어야 한다. 빈 DB 에 마이그레이션만 돌리지 않는다."""
    rows = conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = ANY(%s)",
        (list(BASELINE_TABLES),),
    ).fetchall()
    present = {r["tablename"] for r in rows}
    missing = [t for t in BASELINE_TABLES if t not in present]
    if missing:
        raise SystemExit(
            "baseline 스키마가 없다 (없는 테이블: "
            + ", ".join(missing)
            + ").\n"
            "docs/spec/schema.sql 이 먼저 적용돼야 한다 — 새 볼륨이면 compose 의 "
            "docker-entrypoint-initdb.d 가 처리한다."
        )


def _ensure_ledger(conn: psycopg.Connection) -> None:
    """원장 테이블을 만든다.

    `CREATE TABLE IF NOT EXISTS` 는 경합에 안전하지 않다 — 두 세션이 동시에 들어오면
    한쪽이 pg_type 유니크 위반으로 죽는다. 그 경우는 상대가 만들었다는 뜻이므로 삼킨다.
    """
    try:
        conn.execute(SCHEMA_MIGRATION_DDL)
        conn.commit()
    except (psycopg.errors.UniqueViolation, psycopg.errors.DuplicateTable):
        conn.rollback()
        # 정말 생겼는지 확인한다. 아니면 진짜 오류다.
        exists = conn.execute("SELECT to_regclass('public.schema_migration') AS t").fetchone()
        if not exists or exists["t"] is None:
            raise


def _applied(conn: psycopg.Connection) -> dict[int, dict]:
    rows = conn.execute(
        "SELECT version, name, checksum, applied_at FROM schema_migration ORDER BY version"
    ).fetchall()
    return {r["version"]: r for r in rows}


# 마이그레이션 **본문**이 낸 notice 만 흘린다. 러너 자신의 부트스트랩 DDL 이 내는
# 「already exists, skipping」 같은 잡음은 막는다.
_relay_notices = False


def _notice(diag: object) -> None:
    if _relay_notices:
        message = getattr(diag, "message_primary", None) or ""
        print(f"  [db] {message.strip()}")


def _connect() -> psycopg.Connection:
    conn = psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False)
    # 마이그레이션이 RAISE NOTICE 로 남기는 경고를 삼키지 않는다.
    # 0003 처럼 「적용은 됐지만 사람이 알아야 하는 것」을 알리는 유일한 통로다.
    conn.add_notice_handler(_notice)
    return conn


def cmd_status(_args: argparse.Namespace) -> int:
    migrations = load_migrations()
    with _connect() as conn:
        _assert_baseline(conn)
        _ensure_ledger(conn)
        applied = _applied(conn)

    print(f"migrations/ = {len(migrations)}개 · 적용됨 = {len(applied)}개")
    drift = 0
    for m in migrations:
        row = applied.get(m.version)
        if row is None:
            mark = "PENDING"
        elif row["checksum"] != m.checksum:
            mark = "CHECKSUM 불일치"
            drift += 1
        else:
            mark = "applied " + row["applied_at"].strftime("%Y-%m-%d %H:%M")
        print(f"  {m.version:04d} {m.name:<40s} {mark}")

    unknown = sorted(set(applied) - {m.version for m in migrations})
    for version in unknown:
        print(f"  {version:04d} {applied[version]['name']:<40s} DB 에만 있음 (파일 없음)")
        drift += 1
    return 1 if drift else 0


def cmd_verify(_args: argparse.Namespace) -> int:
    """적용된 마이그레이션의 체크섬이 파일과 같은지만 본다. 아무것도 쓰지 않는다."""
    migrations = load_migrations()
    problems: list[str] = []

    for m in migrations:
        for problem in lint(m.sql):
            problems.append(f"{m.path.name}: {problem}")

    with _connect() as conn:
        _assert_baseline(conn)
        _ensure_ledger(conn)
        applied = _applied(conn)

    by_version = {m.version: m for m in migrations}
    for version, row in applied.items():
        m = by_version.get(version)
        if m is None:
            problems.append(f"{version:04d} {row['name']}: DB 에 적용됐는데 파일이 없다")
        elif m.checksum != row["checksum"]:
            problems.append(
                f"{m.path.name}: 적용 후 파일이 바뀌었다 "
                f"(DB={row['checksum'][:12]} 파일={m.checksum[:12]})"
            )

    if problems:
        print("verify 실패:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"verify OK — {len(migrations)}개 파일 · {len(applied)}개 적용 · 체크섬 일치")
    return 0


def cmd_up(args: argparse.Namespace) -> int:
    migrations = load_migrations()

    # 적용 전에 전부 lint 한다. 하나라도 위반이면 아무것도 적용하지 않는다.
    blocked = False
    for m in migrations:
        for problem in lint(m.sql):
            print(f"거부 {m.path.name}: {problem}", file=sys.stderr)
            blocked = True
    if blocked:
        return 1

    with _connect() as conn:
        _assert_baseline(conn)

        # 다른 러너가 동시에 돌지 못하게 먼저 잠근다. 트랜잭션 밖 세션 잠금.
        # 원장 생성도 잠금 안에서 한다 — CREATE TABLE IF NOT EXISTS 는 경합에 안전하지 않다.
        conn.execute("SELECT pg_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
        conn.commit()
        try:
            _ensure_ledger(conn)
            applied = _applied(conn)
            for version, row in applied.items():
                m = next((x for x in migrations if x.version == version), None)
                if m is not None and m.checksum != row["checksum"]:
                    print(
                        f"중단: {m.path.name} 은 이미 적용됐는데 내용이 바뀌었다. "
                        "적용된 마이그레이션은 수정하지 않고 새 파일을 추가한다.",
                        file=sys.stderr,
                    )
                    return 1

            pending = [m for m in migrations if m.version not in applied]
            if not pending:
                print(f"적용할 것 없음 (최신 = {max(applied) if applied else 0:04d})")
                return 0

            for m in pending:
                if args.dry_run:
                    print(f"[dry-run] {m.version:04d} {m.name}")
                    continue
                try:
                    global _relay_notices
                    _relay_notices = True
                    try:
                        conn.execute(m.sql)
                    finally:
                        _relay_notices = False
                    conn.execute(
                        "INSERT INTO schema_migration (version, name, checksum) "
                        "VALUES (%s, %s, %s)",
                        (m.version, m.name, m.checksum),
                    )
                    conn.commit()
                except Exception as exc:  # 파일 하나가 실패하면 그 파일만 롤백하고 멈춘다
                    conn.rollback()
                    print(f"실패 {m.path.name}: {exc}", file=sys.stderr)
                    print("이 파일은 롤백됐다. 앞 파일들은 적용된 채로 남는다.", file=sys.stderr)
                    return 1
                print(f"적용 {m.version:04d} {m.name}")

            if args.dry_run:
                print(f"[dry-run] {len(pending)}개가 적용될 예정 — 아무것도 쓰지 않았다")
            else:
                print(f"완료 — {len(pending)}개 적용")
            return 0
        finally:
            conn.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK_KEY,))
            conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="app.migrate", description="CapNet 순방향 마이그레이션 러너 (SD-007)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="적용 상태를 표로 보여준다")
    sub.add_parser("verify", help="체크섬·금지 패턴만 검사한다 (쓰기 없음)")
    up = sub.add_parser("up", help="미적용 마이그레이션을 순서대로 적용한다")
    up.add_argument("--dry-run", action="store_true", help="적용하지 않고 목록만 보여준다")

    args = parser.parse_args()
    try:
        return {"status": cmd_status, "verify": cmd_verify, "up": cmd_up}[args.cmd](args)
    except MigrationError as exc:
        # 디렉터리 구조 위반 — 파일명·번호·중복. DB 는 건드리지 않았다.
        print(str(exc), file=sys.stderr)
        print(f"(migrations 디렉터리: {default_migrations_dir()})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
