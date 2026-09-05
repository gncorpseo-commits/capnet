r"""`schema.sql` + `migrations/*.sql` 가 **한 방향으로만 자라는가** (큐 #52 · `#221` 옆).

## 왜 있는가

이 저장소에는 **DB 를 세우는 길이 둘**이다.

| 길 | 무엇이 도는가 |
|---|---|
| 새 볼륨 | initdb 가 `docs/spec/schema.sql` 을 넣고 → `migrate up` 이 `0001`–`0018` |
| 기존 볼륨 | 그 세대 다음 것들만 |

**둘이 같은 곳에 도착해야 한다.** 안 그러면 「새로 clone 하면 되는데 우리 서버에서는
안 된다」가 되고, 그건 재현이 안 되는 결함이라 가장 비싸다.

`#221`(큐 #34)·`#227`(큐 #41)·`#249`(큐 #51)의 컬럼 검사는 **이 합성본을 정본으로 삼는다.**
합성이 어긋나면 그 검사들이 통째로 엉뚱한 것을 본다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| `schema.sql` 단독 | 테이블 **20** · 컬럼 **143** |
| `+ migrations/*.sql` (18개) | 테이블 **26** · 컬럼 **211** |
| 마이그레이션이 **더한** 컬럼 | **68** |
| **지우거나 이름을 바꾼** 컬럼 | **0** |
| 순서 문제 | **0** |

「순서 문제」는 셋이다 — 없는 테이블을 `ALTER`(가드 없이) · 이미 있는 테이블을 다시
`CREATE`(가드 없이) · 이미 있는 컬럼을 다시 `ADD`(가드 없이). 전부 **적용 순서를 잘못
가정했다**는 신호다.

## DDL 은 건드리지 않는다 (절대규칙 1)

제약을 약화하지도, 순서를 바꾸지도 않는다. **드리프트만** 본다.

## 무엇을 안 보나

- **실제 적용.** 두 경로를 진짜로 돌리는 것은 CI 의 `migrate` 잡이 한다 (§4 의 1–7단계).
  여기는 **파일이 서로 모순되지 않는가**만 정적으로 본다
- 제약·인덱스·타입. 컬럼 **존재**만 본다 — 그게 위 세 검사가 기대는 것이다
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_core_sql_columns_exist import (  # noqa: E402
    COMMENT, MIGRATIONS, NON_COLUMN, SCHEMA, _matching_paren, _split_top_level,
)

CREATE = re.compile(r"CREATE TABLE(\s+IF NOT EXISTS)?\s+([a-z_][a-z0-9_]*)\s*\(", re.I)
ALTER = re.compile(r"ALTER TABLE\s+(IF EXISTS\s+)?([a-z_][a-z0-9_]*)(.*?);", re.S | re.I)
ADD = re.compile(r"ADD COLUMN(\s+IF NOT EXISTS)?\s+([a-z_][a-z0-9_]*)", re.I)
DROP = re.compile(r"DROP COLUMN(?:\s+IF EXISTS)?\s+([a-z_][a-z0-9_]*)", re.I)
RENAME = re.compile(r"RENAME COLUMN\s+([a-z_][a-z0-9_]*)\s+TO\s+([a-z_][a-z0-9_]*)", re.I)


def _files() -> list[Path]:
    return [SCHEMA] + sorted(MIGRATIONS.glob("*.sql"))


def _apply(files: list[Path]) -> tuple[dict[str, set[str]], list[str], list[str]]:
    """순서대로 적용한 `(테이블→컬럼, 순서 문제, 사라진 컬럼)`."""
    cols: dict[str, set[str]] = {}
    issues: list[str] = []
    removed: list[str] = []
    for path in files:
        sql = COMMENT.sub("", path.read_text(encoding="utf-8"))
        for m in CREATE.finditer(sql):
            guard, table = m.group(1), m.group(2)
            if table in cols and not guard:
                issues.append(f"{path.name}: {table} 를 다시 CREATE (가드 없음)")
            end = _matching_paren(sql, m.end() - 1)
            for piece in _split_top_level(sql[m.end():end]):
                tok = piece.split()
                if tok and tok[0].upper() not in NON_COLUMN \
                        and re.fullmatch(r"[a-z_][a-z0-9_]*", tok[0]):
                    cols.setdefault(table, set()).add(tok[0])
        for m in ALTER.finditer(sql):
            guard, table, rest = m.group(1), m.group(2), m.group(3)
            if table not in cols and not guard:
                issues.append(f"{path.name}: 없는 테이블 {table} 를 ALTER (가드 없음)")
            for add_guard, name in ADD.findall(rest):
                if name in cols.get(table, set()) and not add_guard:
                    issues.append(f"{path.name}: {table}.{name} 이 이미 있는데 ADD (가드 없음)")
                cols.setdefault(table, set()).add(name)
            for name in DROP.findall(rest):
                if name in cols.get(table, set()):
                    removed.append(f"{path.name}: {table}.{name} DROP")
                cols.get(table, set()).discard(name)
            for old, new in RENAME.findall(rest):
                if old in cols.get(table, set()):
                    removed.append(f"{path.name}: {table}.{old} → {new} RENAME")
                cols.get(table, set()).discard(old)
                cols.setdefault(table, set()).add(new)
    return cols, issues, removed


class TestTheTwoBootPathsConverge(unittest.TestCase):
    def test_no_ordering_assumption_is_broken(self) -> None:
        """**여기가 핵심이다.** 순서를 잘못 가정하면 한쪽 볼륨에서만 깨진다."""
        _, issues, _ = _apply(_files())
        self.assertEqual([], issues, "적용 순서 문제: " + "; ".join(issues))

    def test_migrations_only_add(self) -> None:
        """지우거나 이름을 바꾸면 **옛 볼륨과 새 볼륨이 갈린다** — 오늘 0건이다."""
        _, _, removed = _apply(_files())
        self.assertEqual([], removed,
                         "마이그레이션이 컬럼을 지우거나 이름을 바꾼다 (오늘까지 0건이었다): "
                         + "; ".join(removed))

    def test_the_composite_is_bigger_than_the_baseline(self) -> None:
        """합성이 baseline 과 같으면 마이그레이션이 **아무것도 안 하는** 것이다."""
        base, _, _ = _apply([SCHEMA])
        full, _, _ = _apply(_files())
        self.assertGreater(sum(len(v) for v in full.values()),
                           sum(len(v) for v in base.values()))
        self.assertTrue(set(base) <= set(full), "baseline 의 테이블이 합성에서 사라졌다")


class TestTodaysNumbers(unittest.TestCase):
    """자라는 값이라 **바닥**으로 둔다 — 줄면 무언가 사라진 것이다."""

    def test_baseline_size(self) -> None:
        base, _, _ = _apply([SCHEMA])
        self.assertGreaterEqual(len(base), 20, f"baseline 테이블 {len(base)}")
        self.assertGreaterEqual(sum(len(v) for v in base.values()), 140, "baseline 컬럼")

    def test_composite_size(self) -> None:
        full, _, _ = _apply(_files())
        self.assertGreaterEqual(len(full), 26, f"합성 테이블 {len(full)}")
        self.assertGreaterEqual(sum(len(v) for v in full.values()), 205, "합성 컬럼")

    def test_migration_files_are_seen(self) -> None:
        self.assertGreaterEqual(len(_files()) - 1, 18, f"마이그레이션 {len(_files()) - 1}개")


class TestProbeActuallyScans(unittest.TestCase):
    def test_the_detector_would_catch_a_bad_order(self) -> None:
        """탐지기가 순서 문제를 못 잡으면 위 검사가 **공허하게** 통과한다."""
        fake = ROOT / "tests" / "__order_probe.sql"
        fake.write_text("ALTER TABLE nowhere ADD COLUMN x text;\n", encoding="utf-8")
        try:
            _, issues, _ = _apply([fake])
            self.assertTrue(issues, "없는 테이블 ALTER 를 못 잡았다")
        finally:
            fake.unlink()

    def test_the_detector_would_catch_a_drop(self) -> None:
        fake = ROOT / "tests" / "__drop_probe.sql"
        fake.write_text("CREATE TABLE t (a text, b text);\n"
                        "ALTER TABLE t DROP COLUMN b;\n", encoding="utf-8")
        try:
            _, _, removed = _apply([fake])
            self.assertTrue(removed, "DROP COLUMN 을 못 잡았다")
        finally:
            fake.unlink()


if __name__ == "__main__":
    unittest.main()
