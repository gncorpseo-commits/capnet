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
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.config import settings

# 러너가 단독으로 도는 것을 보장하는 자문 잠금 키 (임의 상수).
ADVISORY_LOCK_KEY = 0x43_41_50_4E_45_54_07  # "CAPNET" + 07 (SD-007)


def _default_migrations_dir() -> Path:
    """컨테이너(`/app/migrations`)와 리포 체크아웃(`<root>/migrations`) 둘 다에서 찾는다."""
    override = os.environ.get("CAPNET_MIGRATIONS_DIR")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "migrations",  # 컨테이너: /app/app/migrate.py → /app/migrations
        here.parents[3] / "migrations" if len(here.parents) > 3 else None,  # 리포 루트
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_dir():
            return candidate
    return candidates[0]


MIGRATIONS_DIR = _default_migrations_dir()

FILENAME_RE = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")

# schema.sql v4.4 가 이미 적용되어 있는지 확인하는 최소 표본.
# 마이그레이션은 baseline 위에서만 의미가 있다.
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

# --- 절대규칙 정적 검사 -------------------------------------------------------
# CLAUDE.md 절대규칙 1·2 를 마이그레이션 경로에서도 깨지지 않게 한다.
# 우회가 정말 필요하면 파일에 허용 주석을 적고 근거를 남긴다 (ALLOW_MARKER).
ALLOW_MARKER = "-- capnet:allow-constraint-change"

FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"\bDROP\s+CONSTRAINT\b", "제약 삭제 — 절대규칙 1"),
    (r"\bDROP\s+TABLE\b", "테이블 삭제 — 절대규칙 1"),
    (r"\bDROP\s+COLUMN\b", "컬럼 삭제 — 절대규칙 1"),
    (r"\bNOT\s+VALID\b", "제약 우회(NOT VALID) — 절대규칙 1"),
    (r"\bDISABLE\s+TRIGGER\b", "트리거 비활성 — 절대규칙 1"),
    (r"\bALTER\s+TABLE\s+\S+\s+DISABLE\b", "테이블 검사 비활성 — 절대규칙 1"),
    (r"\bSET\s+CONSTRAINTS\b.*\bDEFERRED\b", "제약 지연 — 절대규칙 1"),
    (r"\bDROP\s+NOT\s+NULL\b", "NOT NULL 해제 — 절대규칙 1"),
]

# assignment · gate_run 은 INSERT … SELECT 만 (절대규칙 2).
SNAPSHOT_TABLES = ("assignment", "gate_run")

# 파일이 스스로 트랜잭션을 열면 러너의 원자성이 깨진다.
TXN_PATTERNS = [
    (r"^\s*BEGIN\s*;", "BEGIN — 트랜잭션은 러너가 잡는다"),
    (r"^\s*COMMIT\s*;", "COMMIT — 트랜잭션은 러너가 잡는다"),
    (r"^\s*ROLLBACK\s*;", "ROLLBACK — 트랜잭션은 러너가 잡는다"),
]


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    path: Path
    sql: str
    checksum: str


def _strip_sql_comments(sql: str) -> str:
    """정적 검사에서 주석 안의 금지어를 오탐하지 않도록 주석을 지운다."""
    without_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", without_block)


def lint(sql: str) -> list[str]:
    """적용 전에 잡아야 할 위반을 모두 모아 돌려준다."""
    problems: list[str] = []
    allowed = ALLOW_MARKER in sql
    body = _strip_sql_comments(sql)
    flat = re.sub(r"\s+", " ", body)

    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, flat, flags=re.I):
            if allowed:
                continue
            problems.append(f"{reason} — 정말 필요하면 근거와 함께 `{ALLOW_MARKER}` 를 적는다")

    for table in SNAPSHOT_TABLES:
        # INSERT INTO <table> ( ... ) VALUES  → 수기 스냅샷. SELECT 로만 채워야 한다.
        pattern = rf"\bINSERT\s+INTO\s+{table}\b[^;]*?\bVALUES\b"
        if re.search(pattern, flat, flags=re.I):
            problems.append(
                f"{table} 에 VALUES 로 INSERT — 절대규칙 2. INSERT … SELECT 만 쓴다"
            )

    for line in body.splitlines():
        for pattern, reason in TXN_PATTERNS:
            if re.match(pattern, line, flags=re.I):
                problems.append(reason)

    return problems


def load_migrations(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    if not directory.is_dir():
        raise SystemExit(f"마이그레이션 디렉터리 없음: {directory}")

    found: dict[int, Migration] = {}
    for path in sorted(directory.glob("*.sql")):
        match = FILENAME_RE.match(path.name)
        if not match:
            raise SystemExit(
                f"파일명 규칙 위반: {path.name} — NNNN_snake_case.sql 이어야 한다"
            )
        version = int(match.group(1))
        if version in found:
            raise SystemExit(f"버전 중복: {version:04d} — {found[version].path.name} vs {path.name}")
        sql = path.read_text(encoding="utf-8")
        found[version] = Migration(
            version=version,
            name=match.group(2),
            path=path,
            sql=sql,
            checksum=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        )

    migrations = [found[v] for v in sorted(found)]
    if migrations and migrations[0].version != 1:
        raise SystemExit("0001 baseline 이 없다")
    for expected, migration in enumerate(migrations, start=1):
        if migration.version != expected:
            raise SystemExit(
                f"버전 번호에 구멍: {expected:04d} 가 없고 {migration.version:04d} 가 있다"
            )
    return migrations


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


def _connect() -> psycopg.Connection:
    return psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False)


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
                    conn.execute(m.sql)
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
    return {"status": cmd_status, "verify": cmd_verify, "up": cmd_up}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
