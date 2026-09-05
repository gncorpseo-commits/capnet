r"""`check_submission` 의 **「28/28」** 은 어디서 나오는 숫자인가 (배치 B #83).

## 왜 있는가

`STATE.md` 는 회차마다 `check_submission **28/28**` 을 적는다. 그 28 은 **두 조건**에 묶여 있다:

1. `--skip-tree` 로 돌린 값이다 — 플래그 없이 깨끗한 트리에서 돌리면 **29/29** 다
   (`check_clean_tree` 한 건이 더 붙는다). `run_tests.sh` 가 `--skip-tree` 로 부르니 STATE 의
   숫자는 그 경로다.
2. 정적 `check(` 자리는 **16** 인데 결과가 28 인 것은 셋이 **상수 목록을 도는 루프** 안이어서다 —
   `FORBIDDEN_TRACKED` 4 · `REQUIRED_WEIGHTS` 9 · `REQUIRED_FILES` 4 = **17건**. 목록이 줄면
   28 도 조용히 준다. 나머지 13 자리 중 둘은 정본이 없을 때만, 하나는 트리 검사다.

이 검사는 그 둘을 못박고, `STATE.md` 「지금 어디인가」 절의 숫자가 **오늘 실행값**과 같은지 본다.

## 재현

```bash
python3 scripts/check_submission.py --skip-tree | tail -3     # 28/28
python3 -m unittest tests.test_check_submission_count_is_reproducible
```
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_submission.py"
STATE = ROOT / "STATE.md"
sys.path.insert(0, str(ROOT / "scripts"))
import check_submission as cs  # noqa: E402

SKIP_TREE_TOTAL = 28
LOOP_LISTS = {"FORBIDDEN_TRACKED": 4, "REQUIRED_WEIGHTS": 9, "REQUIRED_FILES": 4}


def _run(*flags: str) -> tuple[int, int]:
    proc = subprocess.run([sys.executable, str(SCRIPT), *flags], capture_output=True, text=True,
                          timeout=300, cwd=ROOT)
    m = re.search(r"^(\d+)/(\d+) 통과$", proc.stdout, re.M)
    assert m, proc.stdout[-400:] + proc.stderr[-400:]
    return int(m.group(1)), int(m.group(2))


class TestTheNumberIsReproducible(unittest.TestCase):
    def test_skip_tree_total_is_today_s_value(self) -> None:
        passed, total = _run("--skip-tree")
        self.assertEqual(SKIP_TREE_TOTAL, total, f"--skip-tree 총수가 {total} — STATE 의 28 이 낡았다")
        self.assertEqual(passed, total, f"{passed}/{total} — 통과가 아니면 STATE 에 못 적는다")

    def test_full_run_adds_exactly_the_tree_check(self) -> None:
        """플래그 없이는 `check_clean_tree` **하나만** 더 붙는다 — 통과 여부는 트리 상태라 안 본다."""
        _, total = _run()
        self.assertEqual(SKIP_TREE_TOTAL + 1, total, total)

    def test_loop_lists_keep_their_size(self) -> None:
        """루프가 도는 목록이 줄면 28 도 조용히 준다 — 크기를 적어 둔다."""
        self.assertTrue(LOOP_LISTS, "루프 목록 표가 비었다")
        for name, n in LOOP_LISTS.items():
            with self.subTest(list=name):
                self.assertEqual(n, len(getattr(cs, name)), f"{name} 이 {len(getattr(cs, name))} 이다")

    def test_static_sites_and_loops(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "check"]
        self.assertEqual(16, len(calls), len(calls))
        in_loop = [n.lineno for f in ast.walk(tree) if isinstance(f, ast.For)
                   for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "check"]
        self.assertEqual(3, len(in_loop), in_loop)


class TestStateQuotesTheRunValue(unittest.TestCase):
    def test_current_section_matches_the_script(self) -> None:
        text = STATE.read_text(encoding="utf-8")
        start = text.index("## 지금 어디인가")
        end = text.find("\n## ", start + 1)
        section = text[start:end if end > 0 else None]
        m = re.search(r"check_submission[`*]*\s+\*\*(\d+)/(\d+)\*\*", section)
        self.assertIsNotNone(m, "「지금 어디인가」 절에 check_submission N/N 이 없다")
        assert m is not None
        self.assertEqual((SKIP_TREE_TOTAL, SKIP_TREE_TOTAL), (int(m.group(1)), int(m.group(2))),
                         f"STATE 는 {m.group(1)}/{m.group(2)} 라 하는데 실행값은 {SKIP_TREE_TOTAL}")

    def test_run_tests_calls_it_with_skip_tree(self) -> None:
        body = (ROOT / "scripts" / "run_tests.sh").read_text(encoding="utf-8")
        self.assertIn("check_submission.py --skip-tree", body)


if __name__ == "__main__":
    unittest.main()
