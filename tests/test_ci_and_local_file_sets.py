r"""CI 3잡과 로컬 `run_tests` 가 **어느 파일 집합을 보는가** — diff 를 표로 고정한다 (배치 D #133 · G5 확장).

## 실측 (2026-09-06)

| 누가 | 파일 집합 | 수 |
|---|---|---|
| 로컬 `run_tests.sh` | `tests/test_*.py`(discover) + `check_golden_sha.py` · `check_release.sh` · `check_submission.py --skip-tree` | 검사 파일 1xx + 도구 3 |
| CI `unit` | **같은** 넷 (`check_submission` 은 `--verbose --skip-tree`; `test_ci_and_run_tests_call_the_same_way` 가 같은 말인지 본다) | = 로컬 |
| CI `capreq` | `capreq/tests/test_*.py` (httpx·fastapi 핀 설치 뒤) | 7 — **로컬은 안 돈다** (`testing.md` §4.6) |
| CI `migrate` | `tests/integration/check_*.py` (`run_integration.sh`) + 마이그레이션 단계 | 15 — **로컬은 안 돈다** (DB 필요) |
| 세 나무 밖의 `test_*.py`·`check_*.py` | **0** (`scripts/check_*.py` 는 도구) | — |

즉 CI 합집합 = 저장소의 검사 파일 전부, 로컬은 그중 `tests/` 만. 잡을 늘리는 것은 `ci.yml` 이라 Proposal 만
(`round9-ci-coverage-proposal`). 여기서는 **집합이 새지 않는지**만 본다.

## 재현

```bash
python3 -m unittest tests.test_ci_and_local_file_sets
```
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

CI = ROOT / ".github" / "workflows" / "ci.yml"
RUN_TESTS = ROOT / "scripts" / "run_tests.sh"
TREES = {"tests": ROOT / "tests", "capreq": ROOT / "capreq" / "tests", "integration": ROOT / "tests" / "integration"}


def _ci_run_lines() -> list[str]:
    return [l.strip() for l in hash_comment_free(CI).splitlines() if re.match(r"^\s+run: ", l)]


class TestEveryTestFileIsInACiTree(unittest.TestCase):
    def test_no_test_like_file_outside_the_three_trees(self) -> None:
        stray = []
        for p in ROOT.rglob("*.py"):
            if any(part in (".git", "node_modules", ".venv", "__pycache__") for part in p.parts):
                continue
            if not (p.name.startswith("test_") or p.name.startswith("check_")):
                continue
            rel = p.relative_to(ROOT)
            if rel.parts[0] == "scripts" and p.name.startswith("check_"):
                continue                                                   # 도구
            if p.parent in (TREES["tests"], TREES["capreq"], TREES["integration"]):
                continue
            stray.append(str(rel))
        self.assertEqual([], stray, f"CI 어느 잡도 안 보는 검사 파일: {stray}")

    def test_ci_runs_each_tree(self) -> None:
        runs = "\n".join(_ci_run_lines())
        self.assertIn("unittest discover -s tests", runs)
        self.assertIn('unittest discover -s capreq/tests -p "test_*.py"', runs)
        self.assertIn("scripts/run_integration.sh", runs)

    def test_local_runs_only_the_unit_tree_and_says_so(self) -> None:
        body = hash_comment_free(RUN_TESTS)
        self.assertIn("unittest discover -s tests", body)
        self.assertNotIn("capreq/tests", body)
        self.assertNotIn("run_integration", body)
        guide = (ROOT / "docs" / "guide" / "testing.md").read_text(encoding="utf-8")
        self.assertIn("## 4.6", guide, "로컬이 안 도는 둘을 설명하는 절이 없다")

    def test_tree_sizes_are_what_we_measured(self) -> None:
        self.assertEqual(7, len(list(TREES["capreq"].glob("test_*.py"))))
        self.assertEqual(15, len(list(TREES["integration"].glob("check_*.py"))))
        self.assertGreaterEqual(len(list(TREES["tests"].glob("test_*.py"))), 120)


if __name__ == "__main__":
    unittest.main()
