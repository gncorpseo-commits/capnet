r"""Core 의 SQL 이 **없는 컬럼을 부르지 않는가** (큐 #34).

## 왜 있는가

컬럼 이름을 잘못 적으면 **임포트도 되고 테스트도 통과한다.** 그 SQL 이 실제로
돌 때 `psycopg.errors.UndefinedColumn` 이 나고, 그건 **사용자 요청 한복판**이다.

이 저장소는 스키마 세대가 **18** 이다. `ALTER TABLE … ADD COLUMN` 이 열여덟 번
지나갔고 컬럼이 붙고 이름이 바뀌었다. 코드가 그걸 따라갔는지 **아무도 안 세고 있었다.**

DDL 은 건드리지 않는다 — **드리프트만** 본다 (절대규칙 1).

## 정본을 어디서 읽나

`docs/spec/schema.sql` + `migrations/*.sql` 을 **정적으로** 읽는다. DB 가 없어도
돌아야 하기 때문이다(단위 잡은 아무것도 설치하지 않는다).

**그 추출기가 맞는지 먼저 증명했다.** 살아 있는 DB(세대 18)의
`information_schema.columns` 와 대조했다:

| 무엇 | 결과 |
|---|---|
| 정적 추출 테이블 | **27** · 컬럼 **217** |
| 컬럼이 어긋난 테이블 | **0** |
| DB 에만 있던 관계 | **3** — `schema_migration` · `audit_log_2026_08` · `audit_log_2026_09` |

남은 셋은 **런타임 산물**이다. 마이그레이션 러너가 만드는 대장과,
`ensure_audit_partition()` 이 매달 만드는 파티션 — DDL 파일에 없는 것이 맞다.

### 추출기가 처음엔 셋을 놓쳤다 (적어 둔다)

DB 와 대조하지 않았으면 **없는 컬럼 셋을 「드리프트」라고 적을 뻔했다.**

| 놓친 컬럼 | 왜 |
|---|---|
| `agent_capability_passed.revoked_reason` · `.revoked_gate_run_id` | 한 `ALTER TABLE` 에 `ADD COLUMN` 이 **여럿** (0004) |
| `gate_run.capability_quality_profile` | 같은 모양 (0010) |
| `audit_log.*` | `CREATE TABLE … ) PARTITION BY RANGE (at);` — 닫는 괄호 뒤가 `;` 가 아니다 |

**정본과 대조하지 않은 추출기는 그 자체가 결함 생성기다.**

## 무엇을 보나

`apps/core/app/*.py` 의 SQL 문자열에서 `<별칭>.<컬럼>` 을 뽑고, `FROM`·`JOIN`·
`UPDATE`·`INSERT INTO` 로 별칭→관계를 풀어 스키마에 있는지 본다.

**실측 (2026-09-04): 참조 335건 · 관계 20종 · 없는 컬럼 0건.**

## 무엇을 안 보나 — 정직하게 적는다

- **뷰의 컬럼** (10개). `CREATE VIEW … AS SELECT` 는 정적으로 컬럼을 못 뽑는다.
  뷰를 **이름으로만** 알고 컬럼은 건너뛴다. 여기는 **여전히 사각지대**다
- **한정 없는 컬럼** (`WHERE status = …`). 어느 관계인지 정적으로 못 정한다
- **문자열 조립으로 만든 SQL.** 이 저장소는 그렇게 쓰지 않지만, 쓰면 안 보인다
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "apps" / "core" / "app"
SCHEMA = ROOT / "docs" / "spec" / "schema.sql"
MIGRATIONS = ROOT / "migrations"

# 컬럼 정의가 아닌 테이블 제약 절의 머리말
NON_COLUMN = {
    "PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT", "EXCLUDE", "LIKE", "PARTITION",
}
# 별칭 자리에 올 수 있는 SQL 예약어 — 별칭으로 착각하면 엉뚱한 관계에 묶인다
KEYWORDS = {
    "select", "where", "set", "values", "on", "and", "or", "as", "returning", "using",
    "left", "right", "inner", "outer", "full", "cross", "natural", "join", "order",
    "group", "by", "limit", "offset", "having", "when", "then", "else", "end", "not",
    "null", "is", "conflict", "do", "update", "nothing", "into", "from", "with",
    "case", "distinct", "all",
}

SQL_HINT = re.compile(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|JOIN|FROM)\b", re.I)
RELATION = re.compile(
    r"\b(?:FROM|JOIN|UPDATE|INSERT\s+INTO)\s+([a-z_][a-z0-9_]*)"
    r"(?:\s+(?:AS\s+)?([a-z_][a-z0-9_]*))?",
    re.I,
)
QUALIFIED = re.compile(r"\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b")
COMMENT = re.compile(r"--[^\n]*")


def _split_top_level(body: str) -> list[str]:
    """괄호 깊이 0 의 쉼표로만 자른다 — `NUMERIC(10,2)` 가 둘로 쪼개지지 않게."""
    out: list[str] = []
    depth, cur = 0, ""
    for ch in body + ",":
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return out


def _matching_paren(sql: str, open_at: int) -> int:
    depth = 0
    for j in range(open_at, len(sql)):
        if sql[j] == "(":
            depth += 1
        elif sql[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return len(sql)


def schema() -> tuple[dict[str, set[str]], set[str]]:
    """(테이블→컬럼, 뷰 이름). `schema.sql` 다음에 마이그레이션을 **순서대로** 얹는다."""
    cols: dict[str, set[str]] = {}
    views: set[str] = set()

    def add(table: str, col: str) -> None:
        cols.setdefault(table, set()).add(col)

    for path in [SCHEMA] + sorted(MIGRATIONS.glob("*.sql")):
        if not path.is_file():
            continue
        sql = COMMENT.sub("", path.read_text(encoding="utf-8"))

        for m in re.finditer(
            r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([a-z_][a-z0-9_]*)\s*\(", sql, re.I
        ):
            end = _matching_paren(sql, m.end() - 1)
            for piece in _split_top_level(sql[m.end():end]):
                tok = piece.split()
                if not tok or tok[0].upper() in NON_COLUMN:
                    continue
                if re.fullmatch(r"[a-z_][a-z0-9_]*", tok[0]):
                    add(m.group(1), tok[0])

        # 파티션은 부모의 컬럼을 그대로 받는다
        for m in re.finditer(
            r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([a-z_][a-z0-9_]*)\s+PARTITION OF\s+([a-z_][a-z0-9_]*)",
            sql, re.I,
        ):
            cols.setdefault(m.group(1), set()).update(cols.get(m.group(2), set()))

        # 한 `ALTER TABLE` 에 절이 **여럿** 올 수 있다 (0004 · 0010 이 그렇다)
        for m in re.finditer(
            r"ALTER TABLE\s+(?:IF EXISTS\s+)?([a-z_][a-z0-9_]*)(.*?);", sql, re.S | re.I
        ):
            table, rest = m.group(1), m.group(2)
            for c in re.findall(r"ADD COLUMN(?:\s+IF NOT EXISTS)?\s+([a-z_][a-z0-9_]*)", rest, re.I):
                add(table, c)
            for c in re.findall(r"DROP COLUMN(?:\s+IF EXISTS)?\s+([a-z_][a-z0-9_]*)", rest, re.I):
                cols.get(table, set()).discard(c)
            for old, new in re.findall(
                r"RENAME COLUMN\s+([a-z_][a-z0-9_]*)\s+TO\s+([a-z_][a-z0-9_]*)", rest, re.I
            ):
                cols.get(table, set()).discard(old)
                add(table, new)

        for m in re.finditer(r"CREATE(?:\s+OR REPLACE)?\s+VIEW\s+([a-z_][a-z0-9_]*)", sql, re.I):
            views.add(m.group(1))

    return cols, views


def _sql_literals(path: Path) -> list[tuple[int, str]]:
    """소스를 **데이터로** 읽는다 — import 하지 않는다 (의존성 0)."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if len(node.value) > 30 and SQL_HINT.search(node.value):
                out.append((node.lineno, node.value))
    return out


def _references() -> list[tuple[str, int, str, str]]:
    """(파일, 줄, 관계, 컬럼) — 별칭을 푼 뒤의 `<관계>.<컬럼>` 참조 전부."""
    tables, views = schema()
    out: list[tuple[str, int, str, str]] = []
    for path in sorted(CORE.glob("*.py")):
        for lineno, raw in _sql_literals(path):
            sql = COMMENT.sub("", raw)
            alias: dict[str, str] = {}
            for m in RELATION.finditer(sql):
                rel = m.group(1).lower()
                if rel not in tables and rel not in views:
                    continue
                alias[rel] = rel
                nick = (m.group(2) or "").lower()
                if nick and nick not in KEYWORDS:
                    alias[nick] = rel
            for m in QUALIFIED.finditer(sql):
                nick, col = m.group(1).lower(), m.group(2).lower()
                rel = alias.get(nick)
                # 뷰는 컬럼을 정적으로 못 뽑는다 — 머리말에 사각지대로 적었다
                if rel and rel in tables:
                    out.append((path.name, lineno, rel, col))
    return out


class TestCoreSqlNamesRealColumns(unittest.TestCase):
    def test_every_qualified_column_exists(self) -> None:
        """없는 컬럼은 임포트도 테스트도 통과하고 **요청 한복판**에서 터진다."""
        tables, _ = schema()
        bad = sorted(
            {
                f"{name}:{lineno} {rel}.{col}"
                for name, lineno, rel, col in _references()
                if col not in tables[rel]
            }
        )
        self.assertEqual([], bad, "스키마에 없는 컬럼을 부른다: " + "; ".join(bad))


class TestProbeActuallyScans(unittest.TestCase):
    """범위가 비면 위 검사가 **공허하게** 통과한다."""

    def test_schema_is_read(self) -> None:
        tables, views = schema()
        self.assertGreaterEqual(len(tables), 25, f"테이블 {len(tables)}개밖에 못 읽었다")
        self.assertGreaterEqual(
            sum(len(c) for c in tables.values()), 200, "컬럼을 너무 적게 읽었다"
        )
        self.assertGreaterEqual(len(views), 8, f"뷰 {len(views)}개밖에 못 읽었다")

    def test_migrations_are_applied_on_top(self) -> None:
        """마이그레이션을 안 얹으면 **멀쩡한 컬럼이 「없다」로 뒤집힌다** — 오탐 공장이다."""
        tables, _ = schema()
        for table, col in (
            ("agent_capability_passed", "revoked_reason"),      # 0004 · 다중 ADD COLUMN
            ("agent_capability_passed", "revoked_gate_run_id"),  # 0004 · 같은 문장
            ("gate_run", "capability_quality_profile"),          # 0010 · 같은 모양
            ("audit_log", "payload"),                            # ) PARTITION BY 뒤
        ):
            with self.subTest(column=f"{table}.{col}"):
                self.assertIn(col, tables.get(table, set()))

    # 오늘 실측 335. **별칭이 안 풀리면 참조가 조용히 빠지므로** 바닥을 가깝게 둔다.
    # 줄었다면 왜 줄었는지 확인하고 근거와 함께 이 수를 다시 적는다.
    REFERENCE_FLOOR = 330

    def test_enough_references_are_checked(self) -> None:
        """`FROM task t` 에서 별칭 하나만 빠져도 열여덟 건이 말없이 사라진다."""
        refs = _references()
        self.assertGreaterEqual(
            len(refs),
            self.REFERENCE_FLOOR,
            f"참조 {len(refs)}건밖에 못 봤다 (바닥 {self.REFERENCE_FLOOR}) — "
            "별칭이 안 풀렸을 수 있다. 줄어든 이유를 확인하고 바닥을 다시 적는다",
        )

    def test_alias_resolution_works(self) -> None:
        """별칭을 못 풀면 참조가 통째로 빠지고 검사가 조용히 비어 버린다."""
        rels = {rel for _, _, rel, _ in _references()}
        self.assertGreaterEqual(len(rels), 8, f"관계 {len(rels)}종만 풀렸다: {sorted(rels)}")
        self.assertIn("assignment", rels)
        self.assertIn("task", rels)


if __name__ == "__main__":
    unittest.main()
