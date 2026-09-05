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

**실측 (2026-09-05): 참조 449건 · 관계 26종 · 없는 컬럼 0건.**

## 사각이던 뷰를 열었다 (큐 #41)

첫 판은 뷰를 **이름으로만** 알고 컬럼은 통째로 건너뛰었다 — 「정적으로 못 뽑는다」고
적어 두었다. **틀렸다.** 이 저장소의 뷰 정의 **12개(중복 정의 포함) 전부**가 명시
`SELECT` 목록을 갖는다. 최상위 `SELECT *` 는 **하나도 없다.**

```sql
CREATE OR REPLACE VIEW node_liveness AS
SELECT n.id AS node_id, s.availability, …   -- ← 여기서 뽑힌다
FROM node n
LEFT JOIN LATERAL (SELECT * FROM node_session ns …) s ON TRUE;
```

깊이 0 의 `FROM` 에서 끊으므로 **LATERAL 안쪽의 `SELECT *` 는 섞이지 않는다.**
`END AS reason`(CASE)·`count(*) FILTER (…) AS drifted_still_routable` 도 꼬리의
`AS <이름>` 으로 잡힌다.

| 무엇 | 수 |
|---|---|
| 뷰 | **10** (`CREATE OR REPLACE` 재정의는 뒤가 이긴다) |
| 뽑힌 뷰 컬럼 | **86** |
| Core 의 **뷰 컬럼** 참조 | **27** (뷰 **6**종) — 전에는 전부 버려졌다 |
| 그중 없는 컬럼 | **0** |

**컬럼을 못 뽑는 뷰가 생기면 조용히 건너뛰지 않는다** — `_unresolved_views()` 가
세고, 오늘의 **0** 을 `test_no_view_is_silently_skipped` 가 못박는다. 건너뛴 채로
두면 그 뷰의 참조가 말없이 사라져 검사가 **지키는 척**만 한다.

## 두 번째 사각도 열었다 — f-string SQL (큐 #51)

첫 판은 `ast.Constant` 만 읽었다. 그런데 이 저장소에는 **조각을 조립한 SQL** 이 넷 있다:

```text
TOTALS_SQL = f-string:  WITH w AS ({_WINDOW})  SELECT {_AGG}, …  FROM w
```

`ast.Constant` 가 아니라 `ast.JoinedStr` 라서 **넷이 통째로 안 보였다** —
`work_units.py` 셋 · `safety.py` 하나. 조각(`_WINDOW`·`_AGG`)은 **모듈 자리의 문자열
상수**라 그대로 풀어 넣을 수 있다. 모르는 표현은 공백으로 둔다 — **반쪽이라도 보는 편이
통째로 못 보는 것보다 낫다.**

| 무엇 | 전 | 후 |
|---|---|---|
| Core 참조 | 362 | **449** (+87) |
| 없는 컬럼 | 0 | **0** |

## 무엇을 안 보나 — 정직하게 적는다

- **한정 없는 컬럼** (`WHERE status = …`). 어느 관계인지 정적으로 못 정한다
- f-string 의 **모르는 조각**(함수 호출·조건식). 공백으로 두므로 그 부분은 안 보인다.
  오늘 조각은 전부 모듈 상수라 **전부 풀린다**
- **CTE 별칭의 컬럼** (`WITH w AS (…) … SELECT w.capability_id`). `w` 는 테이블도 뷰도
  아니라 관계로 안 풀린다 — 뮤테이션으로 확인했다(`w.capability_idz` 로 바꿔도 안 운다).
  조각 **안쪽**(`FROM assignment a`)과 함께 조인되는 실제 테이블은 본다
- `%`·`.format()` 로 만든 SQL. 오늘 Core 에 **0건**이고, 아래 검사가 늘면 운다
- 뷰가 `SELECT *` 를 쓰면 컬럼을 못 뽑는다 — **오늘 0건**이고 위 검사가 운다
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


VIEW_HEAD = re.compile(r"CREATE(?:\s+OR\s+REPLACE)?\s+VIEW\s+([a-z_][a-z0-9_]*)\s+AS\s", re.I)
# 꼬리의 `AS <이름>` — `END AS reason` · `count(*) FILTER (…) AS x` 를 잡는다
AS_TAIL = re.compile(r"\bAS\s+([a-z_][a-z0-9_]*)\s*$", re.I)
IDENT_TAIL = re.compile(r"^(?:[a-z_][a-z0-9_]*\.)?([a-z_][a-z0-9_]*)$", re.I)


def _select_list(body: str) -> str | None:
    """최상위 `SELECT` 목록. **깊이 0 의 `FROM`** 에서 끊는다.

    괄호 안(LATERAL 서브쿼리 등)의 `SELECT *` 는 섞이지 않는다.
    """
    head = re.match(r"\s*SELECT\s+(?:DISTINCT\s+)?", body, re.I)
    if not head:
        return None
    depth, i = 0, head.end()
    while i < len(body):
        ch = body[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and re.match(r"\bFROM\b", body[i:], re.I):
            return body[head.end():i]
        i += 1
    return None


def _view_columns(body: str) -> set[str]:
    """뷰가 **내놓는** 컬럼 이름. 못 뽑으면 빈 집합 — 그건 아래에서 센다."""
    select_list = _select_list(body)
    if select_list is None:
        return set()
    out: set[str] = set()
    for piece in _split_top_level(select_list):
        piece = " ".join(piece.split())
        if not piece:
            continue
        tail = AS_TAIL.search(piece)
        if tail:
            out.add(tail.group(1).lower())
            continue
        ident = IDENT_TAIL.match(piece)
        if ident:
            out.add(ident.group(1).lower())
            continue
        return set()   # `*` 등 — 하나라도 못 읽으면 **이 뷰는 못 뽑은 것**이다
    return out


def _unresolved_views() -> list[str]:
    """컬럼을 못 뽑은 뷰. 조용히 건너뛰면 그 참조가 말없이 사라진다."""
    _, views = schema()
    return sorted(name for name, cols in views.items() if not cols)


def schema() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(테이블→컬럼, 뷰→컬럼). `schema.sql` 다음에 마이그레이션을 **순서대로** 얹는다."""
    cols: dict[str, set[str]] = {}
    views: dict[str, set[str]] = {}

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

        for m in VIEW_HEAD.finditer(sql):
            name = m.group(1).lower()
            end = sql.find(";", m.end())
            body = sql[m.end():end if end != -1 else len(sql)]
            # `CREATE OR REPLACE` 는 **뒤가 이긴다** — 0004 가 0002 의 provenance_drift 를 덮는다
            views[name] = _view_columns(body)

    return cols, views


def _module_strings(tree: ast.Module) -> dict[str, str]:
    """모듈 자리의 `NAME = "…"` 문자열 상수. f-string SQL 의 조각을 풀 때 쓴다."""
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            out[node.targets[0].id] = node.value.value
    return out


def _joined(node: ast.JoinedStr, frags: dict[str, str]) -> str:
    """f-string 을 **읽을 수 있는 만큼** 편다.

    조각이 모듈 상수면 그 값을 넣고, 모르는 표현이면 공백으로 둔다 — 반쪽이라도
    보는 편이 통째로 못 보는 것보다 낫다 (큐 #51).
    """
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        elif isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name):
            parts.append(frags.get(value.value.id, " "))
        else:
            parts.append(" ")
    return "".join(parts)


def _sql_literals(path: Path) -> list[tuple[int, str]]:
    """소스를 **데이터로** 읽는다 — import 하지 않는다 (의존성 0).

    f-string 도 본다. `work_units.py` 의 `WITH w AS ({_WINDOW})` 처럼 **조각을 조립한
    SQL** 이 이 저장소에 넷 있고, 첫 판은 `ast.Constant` 만 읽어 그 넷을 통째로 놓쳤다.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    frags = _module_strings(tree)
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        text = None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
        elif isinstance(node, ast.JoinedStr):
            text = _joined(node, frags)
        if text and len(text) > 30 and SQL_HINT.search(text):
            out.append((node.lineno, text))
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
                # 뷰도 본다 (큐 #41). 컬럼을 못 뽑은 뷰만 건너뛰고, 그 수는 따로 센다.
                if rel and (rel in tables or views.get(rel)):
                    out.append((path.name, lineno, rel, col))
    return out


class TestCoreSqlNamesRealColumns(unittest.TestCase):
    def test_every_qualified_column_exists(self) -> None:
        """없는 컬럼은 임포트도 테스트도 통과하고 **요청 한복판**에서 터진다."""
        tables, views = schema()
        known = {**views, **tables}
        bad = sorted(
            {
                f"{name}:{lineno} {rel}.{col}"
                for name, lineno, rel, col in _references()
                if col not in known[rel]
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
        # 오늘 실측 86. 이름만 알고 컬럼이 비면 뷰 참조가 통째로 사라진다 (큐 #41).
        self.assertGreaterEqual(
            sum(len(c) for c in views.values()), 80,
            f"뷰 컬럼을 {sum(len(c) for c in views.values())}개밖에 못 뽑았다",
        )

    def test_no_view_is_silently_skipped(self) -> None:
        """컬럼을 못 뽑은 뷰는 **참조가 말없이 사라진다** — 오늘은 0 이다."""
        self.assertEqual([], _unresolved_views(),
                         f"컬럼을 못 뽑은 뷰: {_unresolved_views()}")

    def test_view_columns_are_really_read(self) -> None:
        """추출기가 껍데기면 위 바닥만 채우고 **엉뚱한 이름**을 담을 수 있다."""
        _, views = schema()
        self.assertIn("is_fresh", views.get("node_liveness", set()))          # 괄호식 + AS
        self.assertIn("availability", views.get("node_liveness", set()))      # 별칭 없는 s.availability
        self.assertIn("reason", views.get("task_input_purge_due", set()))     # END AS (CASE)
        self.assertIn("drifted_still_routable",                                # FILTER (…) AS
                      views.get("provenance_drift_summary", set()))
        # LATERAL 안쪽 `SELECT * FROM node_session` 이 새어 들어오면 안 된다
        self.assertNotIn("closed_at", views.get("node_liveness", set()))

    def test_core_actually_reads_views(self) -> None:
        """뷰 참조가 0 이면 위 확장은 **아무것도 안 지킨다** (오늘 27건 · 뷰 6종)."""
        _, views = schema()
        view_refs = [r for r in _references() if r[2] in views]
        self.assertGreaterEqual(len(view_refs), 20, f"뷰 컬럼 참조 {len(view_refs)}건")
        # 6 종만 **한정된** 컬럼으로 부른다. 나머지 넷은 한정 없이 부르거나 안 쓴다.
        self.assertGreaterEqual(len({r[2] for r in view_refs}), 5,
                                sorted({r[2] for r in view_refs}))

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

    # 오늘 실측 449 (f-string SQL 87건이 큐 #51 로 들어왔다 · 그전 362 · 그전 335).
    # **별칭이 안 풀리면 참조가 조용히 빠지므로** 바닥을 가깝게 둔다.
    # 줄었다면 왜 줄었는지 확인하고 근거와 함께 이 수를 다시 적는다.
    REFERENCE_FLOOR = 440

    def test_enough_references_are_checked(self) -> None:
        """`FROM task t` 에서 별칭 하나만 빠져도 열여덟 건이 말없이 사라진다."""
        refs = _references()
        self.assertGreaterEqual(
            len(refs),
            self.REFERENCE_FLOOR,
            f"참조 {len(refs)}건밖에 못 봤다 (바닥 {self.REFERENCE_FLOOR}) — "
            "별칭이 안 풀렸을 수 있다. 줄어든 이유를 확인하고 바닥을 다시 적는다",
        )

    def test_fstring_sql_is_read(self) -> None:
        """조각을 조립한 SQL 넷 — `ast.Constant` 만 읽으면 통째로 안 보인다 (큐 #51)."""
        seen = {name for name, _, _, _ in _references()}
        joined = [(n, l) for n, l in
                  [(p.name, l) for p in sorted(CORE.glob("*.py")) for l, _ in _sql_literals(p)]]
        self.assertTrue(joined, "SQL 리터럴을 하나도 못 읽었다")
        work = [(n, l, s) for n, l, s in
                [(p.name, l, s) for p in sorted(CORE.glob("*.py")) for l, s in _sql_literals(p)]
                if n == "work_units.py" and "WITH w AS" in s]
        self.assertGreaterEqual(len(work), 3, f"work_units 의 조립 SQL {len(work)}건만 봤다")
        self.assertIn("work_units.py", seen)
        self.assertIn("safety.py", seen)

    def test_fragments_are_substituted(self) -> None:
        """조각을 안 풀면 `FROM w` 만 남아 **컬럼이 하나도 안 보인다**."""
        body = [s for l, s in _sql_literals(CORE / "work_units.py") if "WITH w AS" in s]
        self.assertTrue(body, "조립 SQL 을 못 찾았다")
        self.assertIn("FROM assignment", body[0], "_WINDOW 조각이 안 풀렸다")

    def test_no_percent_or_format_built_sql(self) -> None:
        """`%`·`.format()` 조립은 여기서 안 보인다 — 오늘 0건이고, 생기면 운다."""
        bad = []
        for path in sorted(CORE.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                    left = node.left
                    if isinstance(left, ast.Constant) and isinstance(left.value, str) \
                            and SQL_HINT.search(left.value) and len(left.value) > 30:
                        bad.append(f"{path.name}:{node.lineno}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                        and node.func.attr == "format" \
                        and isinstance(node.func.value, ast.Constant) \
                        and isinstance(node.func.value.value, str) \
                        and SQL_HINT.search(node.func.value.value):
                    bad.append(f"{path.name}:{node.lineno}")
        self.assertEqual([], bad, f"`%`·`.format()` 로 조립한 SQL: {bad}")

    def test_alias_resolution_works(self) -> None:
        """별칭을 못 풀면 참조가 통째로 빠지고 검사가 조용히 비어 버린다."""
        rels = {rel for _, _, rel, _ in _references()}
        self.assertGreaterEqual(len(rels), 8, f"관계 {len(rels)}종만 풀렸다: {sorted(rels)}")
        self.assertIn("node_liveness", rels)   # 뷰도 풀린다 (큐 #41)
        self.assertIn("assignment", rels)
        self.assertIn("task", rels)


if __name__ == "__main__":
    unittest.main()
