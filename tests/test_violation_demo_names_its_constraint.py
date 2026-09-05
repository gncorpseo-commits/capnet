r"""위반 시연 여섯이 **문서가 말한 그 제약**을 칠 수 있는가 (배치 B #87).

## 왜 있는가

`pg-violations.md` 스스로 적어 뒀다 — 「`assignment_agent_id_capability_id_fkey` 를 떨어뜨려 봤더니
그 케이스는 여전히 거절됐다. **다른 FK 가 잡았기 때문이다.**」 `demo_violations.sql` 의 여섯 블록은
전부 `WHEN foreign_key_violation` 으로 받는다 — **어떤 FK 든** 통과다. 그러니 시연이 초록이어도
문서의 행과 같은 이유로 거절된 것인지는 아무도 모른다.

Docker 가 없어 실행은 못 본다. 대신 **정적으로** 좁힌다: 스키마에서 FK 40개의 이름·표·참조표를
도출하고, 각 시연의 실패 문장이 `INSERT`·`UPDATE` 하는 표에서 **칠 수 있는 FK 집합**을 구해
문서 행의 제약이 그 안에 있는지 본다.

## 실측 (2026-09-06)

| 시연 | 문서 행 | 판정 |
|---|---|---|
| TEST1 · 2 · 3 · 4 · 5 | 1 · 2 · 3 · 8 · 9 | 행의 제약이 후보 안 ✅ |
| TEST6 (`UPDATE gate_run … 'FAILED'`) | 11 이라 읽히지만 | 11행의 `agent_capability_passed_…_gate_status_fkey` 는 **칠 수 없다** — 칠 수 있는 것은 `gate_run_passed_…_status_fkey` 뿐이고 그건 **표 밖**이다 |
| 문서 14행의 제약 이름 | — | 전부 스키마에서 해석된다 (`…` 축약은 접두·접미 유일 일치). 10행은 PG 63자 절단 실명(`…_weights_sha256_fk`)으로 고쳤다 |

## 재현

```bash
python3 -m unittest tests.test_violation_demo_names_its_constraint
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "spec" / "schema.sql"
DOC = ROOT / "docs" / "error" / "pg-violations.md"
SQL = ROOT / "scripts" / "demo_violations.sql"

# 시연 → 문서 행. TEST6 는 표 밖이라 여기 없다 (아래 별도 검사).
MAPPING = {"TEST1": 1, "TEST2": 2, "TEST3": 3, "TEST4": 8, "TEST5": 9}


def _fks() -> list[tuple[str, str, str]]:
    """스키마의 FK — (PG 기본 이름 63자 절단, 표, 참조표)."""
    s = SCHEMA.read_text(encoding="utf-8")
    out: list[tuple[str, str, str]] = []
    for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)\s*\((.*?)\n\);", s, re.S):
        t, body = m.group(1), m.group(2)
        for fk in re.finditer(r"(?:CONSTRAINT (\w+)\s+)?FOREIGN KEY \(([^)]+)\)\s*REFERENCES (\w+)", body):
            cols = [c.strip() for c in fk.group(2).split(",")]
            out.append(((fk.group(1) or f"{t}_{'_'.join(cols)}_fkey")[:63], t, fk.group(3)))
        for ln in body.splitlines():
            cm = re.match(r"\s*(\w+)\s+\w[^,]*?\bREFERENCES (\w+)", ln)
            if cm and "FOREIGN KEY" not in ln:
                out.append((f"{t}_{cm.group(1)}_fkey", t, cm.group(2)))
    for m in re.finditer(r"ALTER TABLE (?:ONLY )?(\w+)\s+ADD (?:CONSTRAINT (\w+)\s+)?FOREIGN KEY \(([^)]+)\)\s*REFERENCES (\w+)", s):
        cols = [c.strip() for c in m.group(3).split(",")]
        out.append(((m.group(2) or f"{m.group(1)}_{'_'.join(cols)}_fkey")[:63], m.group(1), m.group(4)))
    return out


def _tables() -> set[str]:
    return set(re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", SCHEMA.read_text(encoding="utf-8")))


def _named_checks() -> set[str]:
    return set(re.findall(r"CONSTRAINT (ck_\w+)", SCHEMA.read_text(encoding="utf-8")))


def _doc_rows() -> dict[int, list[str]]:
    rows: dict[int, list[str]] = {}
    for n, cell in re.findall(r"^\| (\d+) \| [^|]+ \| ([^|]+) \|", DOC.read_text(encoding="utf-8"), re.M):
        rows[int(n)] = re.findall(r"`([^`]+)`", cell)
    return rows


def _resolve(cell: str) -> set[str]:
    """문서 셀 하나 → 스키마의 제약/표 이름 집합. 못 풀면 빈 집합."""
    names = {n for n, _, _ in _fks()}
    if "..." in cell:
        prefix, suffix = cell.split("...", 1)
        return {n for n in names if n.startswith(prefix) and n.endswith(suffix)}
    if cell in names or cell in _named_checks():
        return {cell}
    if cell in _tables():
        return {cell}                                     # `tier_compatible` = 그 표를 참조하는 FK
    if cell.endswith("_check") and cell[:-6] in _tables():
        return {cell}                                     # 행렬 표의 CHECK
    return set()


def _blocks() -> dict[str, set[str]]:
    """시연 → 실패 문장이 쓰는 표 (마지막 `BEGIN … EXCEPTION` 안)."""
    parts = re.split(r"^\\echo (TEST\d) ", SQL.read_text(encoding="utf-8"), flags=re.M)
    out: dict[str, set[str]] = {}
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        inner = body[body.rfind("BEGIN"):body.rfind("EXCEPTION")]
        out[parts[i]] = set(re.findall(r"(?:INSERT INTO|UPDATE)\s+(\w+)", inner))
    return out


def _candidates(writes: set[str]) -> set[str]:
    """그 표들을 쓰면 칠 수 있는 FK — 자기 표거나 참조표가 쓰이는 것."""
    return {n for n, t, r in _fks() if t in writes or r in writes}


def _hits(row: int, cands: set[str]) -> bool:
    fks = _fks()
    for cell in _doc_rows()[row]:
        for name in _resolve(cell):
            if name in cands:
                return True
            if any(r == name and n in cands for n, _, r in fks):   # 표 이름이면 그 표를 참조하는 FK
                return True
    return False


class TestEveryDocConstraintExists(unittest.TestCase):
    def test_all_fourteen_rows_resolve(self) -> None:
        rows = _doc_rows()
        self.assertEqual(14, len(rows), sorted(rows))
        unresolved = [(n, c) for n, cells in rows.items() for c in cells if not _resolve(c)]
        self.assertEqual([], unresolved, f"스키마에 없는 제약을 문서가 말한다: {unresolved}")
        ambiguous = [(n, c) for n, cells in rows.items() for c in cells if "..." in c and len(_resolve(c)) != 1]
        self.assertEqual([], ambiguous, f"`…` 축약이 하나로 안 풀린다: {ambiguous}")


class TestEachDemoCanHitItsRow(unittest.TestCase):
    def test_mapped_demos(self) -> None:
        blocks = _blocks()
        self.assertTrue(MAPPING)
        for demo, row in MAPPING.items():
            with self.subTest(demo=demo, row=row):
                cands = _candidates(blocks[demo])
                self.assertTrue(cands, f"{demo} 의 실패 문장이 쓰는 표를 못 찾았다: {blocks[demo]}")
                self.assertTrue(_hits(row, cands), f"{demo} 가 문서 {row}행의 제약을 칠 수 없다 — 후보 {sorted(cands)}")

    def test_test6_is_outside_the_table_and_the_doc_says_so(self) -> None:
        cands = _candidates(_blocks()["TEST6"])
        self.assertIn("gate_run_passed_gate_run_id_agent_id_capability_id_status_fkey", cands)
        self.assertFalse(_hits(11, cands), "TEST6 가 11행을 칠 수 있게 됐다 — 문서의 매핑 표를 고쳐라")
        self.assertIn("| TEST6 invalidate PASSED gate_run | — |", DOC.read_text(encoding="utf-8"))


class TestTheHandlersAcceptAnyFk(unittest.TestCase):
    def test_six_catch_alls_and_no_constraint_name_assertion(self) -> None:
        """이 검사가 정적인 이유 — 바뀌면(단언이 들어오면) 이 숫자도 같이 바꾼다."""
        sql = SQL.read_text(encoding="utf-8")
        self.assertEqual(6, len(re.findall(r"WHEN foreign_key_violation THEN", sql)))
        self.assertEqual(0, sql.count("CONSTRAINT_NAME"))


class TestProbeActuallyDerives(unittest.TestCase):
    def test_enough_fks_and_blocks(self) -> None:
        self.assertGreaterEqual(len(_fks()), 35, len(_fks()))
        self.assertEqual(6, len(_blocks()), sorted(_blocks()))


if __name__ == "__main__":
    unittest.main()
