r"""`run_tests.sh` 의 discover 가 **검사 파일을 빠뜨리지 않는가** (배치 B #94 · G5 옆).

## 왜 있는가

`python3 -m unittest discover -s tests` 는 기본 패턴 `test*.py` 로 **최상위만** 본다 — 하위 폴더는
`__init__.py` 가 있어야 들어가고, `foo_test.py` 는 이름이 안 맞아 조용히 빠진다. 파일이 빠져도
「전부 통과」가 찍힌다. 정적 스캔은 못 믿는다 — 처음 세어 봤을 때 상속으로 검사를 받는 두 파일이
「검사 0」으로 나왔다. 그래서 **같은 로더**로 실제로 싣고 센다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `tests/test_*.py` | 120 |
| 로더가 실은 모듈 | 120 — 빠진 것 **0** · 검사 0 인 모듈 **0** · 적재 실패 **0** |
| 패턴 밖 이름(`*_test.py` · `test` 로 안 시작) | 0 |
| `__init__.py` 없는 하위 폴더의 `test*.py` | 0 (`integration/` 은 `check_*.py` — 다른 러너) |
| `run_tests.sh` 의 discover 에 `-p` 좁힘 | 없음 |

## 재현

```bash
python3 -m unittest tests.test_discover_loads_every_test_file
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
RUN_TESTS = ROOT / "scripts" / "run_tests.sh"


def _loaded() -> dict[str, int]:
    """run_tests 와 같은 모양(`discover -s tests`, 기본 패턴)으로 싣고 모듈별 검사 수를 센다."""
    per: dict[str, int] = {}

    def walk(s: unittest.TestSuite) -> None:
        for t in s:
            if isinstance(t, unittest.TestSuite):
                walk(t)
            else:
                mod = type(t).__module__.split(".")[-1]
                per[mod] = per.get(mod, 0) + 1

    walk(unittest.TestLoader().discover(str(TESTS)))
    return per


class TestEveryFileIsLoaded(unittest.TestCase):
    def test_glob_and_loader_agree(self) -> None:
        files = {p.stem for p in TESTS.glob("test_*.py")}
        per = _loaded()
        self.assertGreaterEqual(len(files), 100, len(files))
        self.assertEqual([], sorted(files - set(per)), "discover 가 빠뜨린 파일")
        self.assertEqual([], sorted(m for m in per if m not in files and not m.startswith("unittest")),
                         "glob 밖에서 실린 모듈 — 이름 규약이 새는 곳")

    def test_no_module_loads_zero_tests_and_none_fails_to_load(self) -> None:
        per = _loaded()
        self.assertTrue(per)
        self.assertEqual([], sorted(m for m, n in per.items() if n == 0))
        self.assertEqual([], sorted(m for m in per if "Failed" in m or "_FailedTest" in m), "임포트에 실패한 모듈")


class TestNothingSitsOutsideThePattern(unittest.TestCase):
    def test_no_test_file_with_a_name_the_pattern_misses(self) -> None:
        stray = sorted(p.name for p in TESTS.glob("*.py")
                       if p.name.endswith("_test.py") or (p.name.startswith("test") and not p.name.startswith("test_")))
        self.assertEqual([], stray, f"discover 패턴이 못 보는 이름: {stray}")

    def test_no_test_file_in_a_folder_without_init(self) -> None:
        stray = sorted(str(p.relative_to(TESTS)) for p in TESTS.rglob("test*.py")
                       if p.parent != TESTS and not (p.parent / "__init__.py").is_file())
        self.assertEqual([], stray, f"__init__.py 없는 폴더의 검사 — discover 가 안 들어간다: {stray}")

    def test_run_tests_does_not_narrow_the_pattern(self) -> None:
        line = next(l for l in RUN_TESTS.read_text(encoding="utf-8").splitlines() if "unittest discover" in l)
        self.assertIn("-s tests", line)
        self.assertNotRegex(line, r"-p\s+", f"discover 에 -p 좁힘이 생겼다: {line.strip()}")


if __name__ == "__main__":
    unittest.main()
