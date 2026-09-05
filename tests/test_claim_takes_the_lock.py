r"""claim 이 **잠금을 잡고 고르는가** (큐 #68 · `pitfalls` §4).

## 왜 있는가

`pitfalls` §4 는 두 줄로 못박는다:

> - `FOR UPDATE SKIP LOCKED` **필수**
> - 활성 lease 유니크 인덱스가 이중 할당을 DB 에서 막는다

두 줄은 **다른 것을 지킨다.** 유니크 인덱스는 이중 배정을 **거절**하고, `SKIP LOCKED` 는
애초에 **두 워커가 같은 작업을 집지 않게** 한다. 잠금이 빠지면 유니크 인덱스가 계속
잡아 주긴 하지만, 그건 **정상 경로가 계속 실패하는** 모양이다 — 조용히 느려지고
재시도 수가 는다.

`SKIP LOCKED` 없는 맨 `FOR UPDATE` 는 더 나쁘다. 거절이 아니라 **대기**라서, 워커가
서로를 막고 큐가 멈춘다. 「안 되는」게 아니라 「안 끝나는」 것이라 알아채기 어렵다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| `task` 를 고르는 SQL | **4** |
| 그중 **배정을 쓰는** 것 | **1** — `CLAIM_SQL`(`INSERT … SELECT`) |
| 그 앞에서 잠그는 것 | **1** — `LOCK_SQL`(`FOR UPDATE SKIP LOCKED`) ✅ |
| `SKIP LOCKED` 없는 맨 `FOR UPDATE` | **0** ✅ |
| 나머지 둘 | 조회 전용 (`/v1/ops/status` 집계 · `GET /v1/tasks/{id}`) |

**오늘 0건이다.** 나기 전에 막는다.

## 무엇을 안 보나

- **동시성 실측.** 두 워커를 실제로 붙여 보는 것은 DB 가 필요하다 —
  `tests/integration/check_*.py` 쪽 일이다. 여기는 **SQL 의 모양**만 본다
- 유니크 인덱스. 그건 스키마가 지키고 `test_absolute_rules_are_enforced` 가 본다
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "apps" / "core" / "app"
CLAIM = CORE / "claim.py"
PITFALLS = ROOT / "docs" / "error" / "pitfalls.md"

SELECT = re.compile(r"\bSELECT\b", re.I)
FROM_TASK = re.compile(r"\bFROM\s+task\b", re.I)
SKIP_LOCKED = re.compile(r"FOR\s+UPDATE\s+SKIP\s+LOCKED", re.I)
FOR_UPDATE = re.compile(r"FOR\s+UPDATE\b", re.I)
INSERT_ASSIGNMENT = re.compile(r"INSERT\s+INTO\s+assignment", re.I)


def _sql_literals() -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    for path in sorted(CORE.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and len(node.value) > 40 and SELECT.search(node.value):
                out.append((path.name, node.lineno, node.value))
    return out


def _task_pickers() -> list[tuple[str, int, str]]:
    return [(f, l, s) for f, l, s in _sql_literals() if FROM_TASK.search(s)]


class TestPlainForUpdateNeverAppears(unittest.TestCase):
    """맨 `FOR UPDATE` 는 거절이 아니라 **대기**다 — 워커가 서로를 막는다."""

    def test_every_for_update_skips_locked(self) -> None:
        bad = [f"{f}:{l}" for f, l, s in _sql_literals()
               if FOR_UPDATE.search(s) and not SKIP_LOCKED.search(s)]
        self.assertEqual([], bad, f"`SKIP LOCKED` 없는 `FOR UPDATE`: {bad}")


class TestClaimLocksBeforeItWrites(unittest.TestCase):
    def test_the_lock_sql_exists_and_skips(self) -> None:
        body = CLAIM.read_text(encoding="utf-8")
        self.assertIn("LOCK_SQL", body, "claim.py 에 LOCK_SQL 이 없다")
        self.assertTrue(SKIP_LOCKED.search(body), "claim 에 FOR UPDATE SKIP LOCKED 가 없다")

    def test_claim_next_runs_the_lock_before_the_insert(self) -> None:
        """순서가 뒤집히면 **두 워커가 같은 작업을 집는다**."""
        body = CLAIM.read_text(encoding="utf-8")
        fn = body.index("def claim_next")
        rest = body[fn:]
        lock_at, claim_at = rest.find("LOCK_SQL"), rest.find("CLAIM_SQL")
        self.assertNotEqual(-1, lock_at, "claim_next 가 LOCK_SQL 을 안 쓴다")
        self.assertNotEqual(-1, claim_at, "claim_next 가 CLAIM_SQL 을 안 쓴다")
        self.assertLess(lock_at, claim_at, "잠그기 전에 배정을 쓴다")

    def test_the_assignment_writer_is_an_insert_select(self) -> None:
        """절대규칙 2 — 스냅샷을 앱이 계산해 넣지 않는다."""
        writers = [(f, l, s) for f, l, s in _task_pickers() if INSERT_ASSIGNMENT.search(s)]
        self.assertEqual(1, len(writers), f"배정을 쓰는 SQL 이 {len(writers)}개다")
        self.assertRegex(writers[0][2], r"INSERT\s+INTO\s+assignment[\s\S]*\bSELECT\b")


class TestTheOtherTaskReadsAreReadOnly(unittest.TestCase):
    def test_no_other_picker_writes_an_assignment(self) -> None:
        others = [f"{f}:{l}" for f, l, s in _task_pickers()
                  if not INSERT_ASSIGNMENT.search(s) and not SKIP_LOCKED.search(s)
                  and re.search(r"\bINSERT\b|\bUPDATE\b|\bDELETE\b", s, re.I)]
        self.assertEqual([], others, f"잠금 없이 task 를 고르고 쓰는 SQL: {others}")

    def test_the_picker_count_is_pinned(self) -> None:
        """자리가 늘면 그중 하나가 잠금을 빠뜨렸을 수 있다 — 세어 보게 만든다."""
        self.assertEqual(4, len(_task_pickers()),
                         [f"{f}:{l}" for f, l, _ in _task_pickers()])


class TestTheRuleStaysWritten(unittest.TestCase):
    def test_pitfalls_still_requires_it(self) -> None:
        rule = "`FOR UPDATE SKIP LOCKED` 필수"
        self.assertTrue(rule in PITFALLS.read_text(encoding="utf-8"),
                        f"pitfalls §4 에서 규칙이 사라졌다: «{rule}»")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_sql_is_read(self) -> None:
        self.assertGreaterEqual(len(_sql_literals()), 20, len(_sql_literals()))

    def test_detector_discriminates(self) -> None:
        self.assertTrue(SKIP_LOCKED.search("ORDER BY created_at\n FOR UPDATE SKIP LOCKED"))
        self.assertTrue(FOR_UPDATE.search("SELECT 1 FROM task FOR UPDATE"))
        self.assertFalse(SKIP_LOCKED.search("SELECT 1 FROM task FOR UPDATE"))
        self.assertTrue(FROM_TASK.search("SELECT id FROM task WHERE 1=1"))
        self.assertFalse(FROM_TASK.search("SELECT id FROM task_input WHERE 1=1"))


if __name__ == "__main__":
    unittest.main()
