r"""CI 와 로컬 `run_tests` 가 **같은 도구를 같은 인자로** 부르는가 (G5).

G5 는 「CI 3잡이 로컬 `run_tests` 와 다른 파일을 보는가」다. `#215`(`test_ci_matches_run_tests`)가
**도구 목록**을 이미 맞췄다 — 남은 것은 **인자**다. 같은 도구를 다른 인자로 부르면 한쪽만
약해지고, 사람은 로컬 초록을 믿는다.

## 실측 (2026-09-05)

| 도구 | `run_tests.sh` | CI `unit` |
|---|---|---|
| `unittest discover` | `-s tests "$@"` | `-s tests -v` |
| `check_golden_sha.py` | (인자 없음) | (인자 없음) — `migrate` 잡의 `$(… --print)` 은 **값 읽기**라 뺀다 |
| `check_release.sh` | (인자 없음) | (인자 없음) |
| `check_submission.py` | **`--skip-tree`** | `--verbose` **`--skip-tree`** |

`-v`·`--verbose` 는 출력만 바꾼다. **실질적으로 다른 인자는 없다.**

## 그런데 **둘 다 빼는** 검사가 하나 있다

```text
python3 scripts/check_submission.py --skip-tree   → 28/28
python3 scripts/check_submission.py               → 29/29
```

`--skip-tree` 가 빼는 **「워킹트리 깨끗 (패키징 전)」** 한 건은 **로컬에서도 CI 에서도 안
돈다.** 그건 의도다 — 작업 중에는 늘 더러우니까. 대신 그 한 건은 **사람이 패키징 직전에**
맨몸으로 돌려야 하고, `contest-submission-checklist.md` §가 그렇게 적는다.

**문제는 「하나」가 조용히 늘 때다.** `--skip-tree` 뒤에 검사가 더 숨으면, 「28/28 통과」는
그대로인데 안 도는 것이 둘·셋이 된다. 그래서 **그 차이를 1 로 못박는다.**

## 무엇을 안 보나

- CI 가 **더 보는 것**은 막지 않는다 (`migrate`·`capreq` 잡이 그렇다 — `#215` 규율)
- 출력 인자(`-v`·`--verbose`)
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_TESTS = ROOT / "scripts" / "run_tests.sh"
CI = ROOT / ".github" / "workflows" / "ci.yml"
CHECKLIST = ROOT / "docs" / "ops" / "contest-submission-checklist.md"

# 출력만 바꾸는 인자 — 차이로 세지 않는다.
COSMETIC = {"-v", "--verbose"}

# `--skip-tree` 가 빼는 검사 수. 늘면 안 도는 것이 는다.
SKIPPED_BY_SKIP_TREE = 1


def _args_in(text: str, tool: str) -> set[str]:
    """그 도구를 **검사로** 부르는 줄들의 인자 (출력 인자는 뺀다).

    `$(python3 … --print)` 처럼 **값을 읽는** 호출은 뺀다 — `ci.yml` 의 migrate 잡이
    골든 sha 를 그렇게 읽는데, 그걸 인자 차이로 세면 늘 빨갛다. 검사로 부르는 것과
    값으로 읽는 것은 다르다.
    """
    found: set[str] = set()
    for line in text.splitlines():
        if tool not in line or line.strip().startswith("#") or "$(" in line:
            continue
        tail = line.split(tool, 1)[1]
        found |= {a for a in re.findall(r"--?[a-z-]+", tail) if a not in COSMETIC}
    return found


def _count(args: list[str]) -> int:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_submission.py"), *args],
                          capture_output=True, text=True, timeout=300, cwd=ROOT)
    m = re.search(r"(\d+)/(\d+) 통과", proc.stdout + proc.stderr)
    assert m, (proc.stdout + proc.stderr)[-400:]
    return int(m.group(2))


class TestSameToolSameArgs(unittest.TestCase):
    def test_check_submission_is_called_the_same(self) -> None:
        """**여기가 핵심이다.** 한쪽만 약한 인자를 주면 로컬 초록이 거짓말이 된다."""
        local = _args_in(RUN_TESTS.read_text(encoding="utf-8"), "check_submission.py")
        ci = _args_in(CI.read_text(encoding="utf-8"), "check_submission.py")
        self.assertTrue(local or ci, "check_submission 호출을 못 찾았다")
        self.assertEqual(local, ci, f"인자가 갈린다 — 로컬={sorted(local)} CI={sorted(ci)}")

    def test_the_other_tools_take_no_weakening_args(self) -> None:
        for tool in ("check_golden_sha.py", "check_release.sh"):
            with self.subTest(tool=tool):
                local = _args_in(RUN_TESTS.read_text(encoding="utf-8"), tool)
                ci = _args_in(CI.read_text(encoding="utf-8"), tool)
                self.assertEqual(local, ci, f"{tool} 의 인자가 갈린다")

    def test_both_discover_the_same_tree(self) -> None:
        for text, who in ((RUN_TESTS.read_text(encoding="utf-8"), "run_tests"),
                          (CI.read_text(encoding="utf-8"), "ci.yml")):
            with self.subTest(who=who):
                self.assertIn("discover -s tests", text, f"{who} 가 tests 를 안 훑는다")


class TestTheSkippedCheckIsExactlyOne(unittest.TestCase):
    """「하나」가 조용히 늘면 「28/28 통과」는 그대로인데 안 도는 것이 는다."""

    def test_skip_tree_hides_exactly_one_check(self) -> None:
        full, skipped = _count([]), _count(["--skip-tree"])
        self.assertEqual(SKIPPED_BY_SKIP_TREE, full - skipped,
                         f"--skip-tree 가 {full - skipped}건을 뺀다 (전체 {full})")

    def test_the_checklist_tells_the_human_to_run_the_full_one(self) -> None:
        """그 한 건은 **사람만** 돌린다 — 어디에도 안 적혀 있으면 아무도 안 돌린다."""
        body = CHECKLIST.read_text(encoding="utf-8")
        self.assertTrue("check_submission.py" in body, "체크리스트가 그 도구를 안 부른다")
        self.assertTrue(re.search(r"check_submission\.py\s+#[^\n]*패키징", body) is not None,
                        "체크리스트에 「패키징 직전에 맨몸으로」 안내가 없다")

    def test_run_tests_says_why_it_skips(self) -> None:
        body = RUN_TESTS.read_text(encoding="utf-8")
        self.assertTrue("--skip-tree" in body, "run_tests 가 --skip-tree 를 안 쓴다")
        self.assertTrue("패키징 직전에는" in body,
                        "run_tests 에 왜 워킹트리 검사를 빼는지 안 적혀 있다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_the_arg_reader_works(self) -> None:
        self.assertEqual({"--skip-tree"},
                         _args_in("run: python3 scripts/x.py --verbose --skip-tree", "x.py"))
        self.assertEqual(set(), _args_in("# python3 scripts/x.py --danger", "x.py"))
        # 값 읽기는 검사 호출이 아니다 — 이걸 안 빼면 늘 빨갛다.
        self.assertEqual(set(), _args_in("want=$(python3 scripts/x.py --print)", "x.py"))

    def test_the_counter_reads_a_number(self) -> None:
        self.assertGreaterEqual(_count(["--skip-tree"]), 25)


if __name__ == "__main__":
    unittest.main()
