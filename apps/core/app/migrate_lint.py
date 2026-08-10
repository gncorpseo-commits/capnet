"""마이그레이션 파일의 **정적** 검사·로딩 (SD-007).

DB 를 열지 않는다. 표준 라이브러리만 쓴다 — psycopg·pydantic 없이 import 된다.
그래서 이 규칙들은 DB 없이도 테스트되고, CI 에서 서비스 컨테이너 없이 돈다.

`migrate.py` 가 이 모듈을 가져다 쓴다. 여기 있는 것은 전부 순수 함수다.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

FILENAME_RE = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")

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


class MigrationError(Exception):
    """마이그레이션 디렉터리 구조가 규칙을 어겼다."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    path: Path
    sql: str
    checksum: str


def default_migrations_dir() -> Path:
    """컨테이너(`/app/migrations`)와 리포 체크아웃(`<root>/migrations`) 둘 다에서 찾는다."""
    override = os.environ.get("CAPNET_MIGRATIONS_DIR")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "migrations",  # 컨테이너: /app/app/…py → /app/migrations
        here.parents[3] / "migrations" if len(here.parents) > 3 else None,  # 리포 루트
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_dir():
            return candidate
    return candidates[0]


def strip_sql_comments(sql: str) -> str:
    """정적 검사에서 주석 안의 금지어를 오탐하지 않도록 주석을 지운다."""
    without_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", without_block)


def lint(sql: str) -> list[str]:
    """적용 전에 잡아야 할 위반을 모두 모아 돌려준다."""
    problems: list[str] = []
    allowed = ALLOW_MARKER in sql
    body = strip_sql_comments(sql)
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


def load_migrations(directory: Path | None = None) -> list[Migration]:
    """번호 순으로 읽는다. 파일명·번호 규칙 위반은 MigrationError."""
    directory = directory or default_migrations_dir()
    if not directory.is_dir():
        raise MigrationError(f"마이그레이션 디렉터리 없음: {directory}")

    found: dict[int, Migration] = {}
    for path in sorted(directory.glob("*.sql")):
        match = FILENAME_RE.match(path.name)
        if not match:
            raise MigrationError(
                f"파일명 규칙 위반: {path.name} — NNNN_snake_case.sql 이어야 한다"
            )
        version = int(match.group(1))
        if version in found:
            raise MigrationError(
                f"버전 중복: {version:04d} — {found[version].path.name} vs {path.name}"
            )
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
        raise MigrationError("0001 baseline 이 없다")
    for expected, migration in enumerate(migrations, start=1):
        if migration.version != expected:
            raise MigrationError(
                f"버전 번호에 구멍: {expected:04d} 가 없고 {migration.version:04d} 가 있다"
            )
    return migrations
