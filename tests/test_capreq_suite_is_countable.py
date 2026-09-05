r"""capreq 검사가 **어디서 몇 개 도는가** (큐 #60 · `#11` 잔여).

## 왜 있는가

`STATE` 는 「capreq **72**」라고 적고 옆에 「정본은 CI」라고 단다. 그 72 는 **이 환경에서
재현되지 않는다** — `pip` 이 없어 `httpx`·`fastapi` 를 못 깐다.

그건 괜찮다. **문제는 로컬에서 돌렸을 때 무엇이 나오느냐였다:**

```text
$ PYTHONPATH=capreq/src python3 -m unittest discover -s capreq/tests -p "test_*.py"
ERROR: test_capnet_unit  ModuleNotFoundError: No module named 'httpx'
ERROR: test_router_unit  ModuleNotFoundError: No module named 'httpx'
ERROR: test_server_unit  ModuleNotFoundError: No module named 'fastapi'
Ran 52 tests — FAILED (errors=3)
```

**`FAILED` 는 「코드가 깨졌다」처럼 보인다.** `docs/guide/testing.md` §4.6 은 그 경우를
「**없으면 건너뛴다**」로 정해 뒀는데, 세 모듈만 그 규약 밖이었다.

## 고친 뒤 (2026-09-05 실측)

```text
Ran 52 tests — OK (skipped=3)
```

| 무엇 | 값 |
|---|---|
| `capreq/tests` 의 검사 파일 | **7** |
| 런타임 핀 없이 도는 것 | **4** (검사 **52**) |
| 핀이 있어야 도는 것 | **3** — `capnet`·`router`(httpx) · `server`(fastapi) |
| CI 의 capreq 잡이 깔고 도는 수 | **72** — 정본은 그 잡의 로그다 |

**52 + 핀이 필요한 셋 = 72.** 이 환경에서 **셋을 못 돌린다**는 사실은 그대로다 —
숫자를 지어내지 않고, 어디서 나오는지 못박는다.

## 재현

```bash
PYTHONPATH=capreq/src python3 -m unittest discover -s capreq/tests -p "test_*.py"   # 52 · skipped=3
```

핀이 깔린 환경(= CI `capreq` 잡)에서는 같은 명령이 72 를 낸다.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPREQ_TESTS = ROOT / "capreq" / "tests"
CI = ROOT / ".github" / "workflows" / "ci.yml"

# 런타임 핀이 있어야 도는 모듈과 **무엇이 없어서인가**.
NEEDS_A_PIN = {
    "test_capnet_unit.py": "httpx",
    "test_router_unit.py": "httpx",
    "test_server_unit.py": "fastapi",
}


def _test_files() -> list[Path]:
    return sorted(p for p in CAPREQ_TESTS.glob("test_*.py"))


class TestMissingPinsSkipInsteadOfErroring(unittest.TestCase):
    """`FAILED` 는 「코드가 깨졌다」처럼 보인다 — 규약은 「건너뛴다」다."""

    def test_each_pinned_module_guards_its_import(self) -> None:
        pinned = NEEDS_A_PIN.items()
        self.assertTrue(pinned, "핀이 필요한 모듈 목록이 비었다")
        for name, module in pinned:
            with self.subTest(file=name):
                body = (CAPREQ_TESTS / name).read_text(encoding="utf-8")
                self.assertIn("except ModuleNotFoundError", body,
                              f"{name} 이 import 실패를 그대로 터뜨린다")
                self.assertIn("raise unittest.SkipTest", body)
                self.assertIn(f"{module} 없음", body,
                              f"{name} 의 건너뛴 사유가 무엇이 없는지 안 말한다")

    def test_the_suite_runs_green_without_pins(self) -> None:
        """**실제로 돌려 본다** — 정적 검사만으로는 초록인지 모른다."""
        env = {"PYTHONPATH": str(ROOT / "capreq" / "src"), "PATH": "/usr/bin:/bin"}
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover",
             "-s", str(CAPREQ_TESTS), "-p", "test_*.py"],
            capture_output=True, text=True, timeout=300, cwd=ROOT, env=env,
        )
        tail = proc.stdout + proc.stderr
        self.assertIn("OK", tail, f"핀 없이 초록이 아니다:\n{tail[-600:]}")
        self.assertNotIn("ModuleNotFoundError", tail, "import 오류가 그대로 샌다")
        m = re.search(r"Ran (\d+) tests", tail)
        self.assertIsNotNone(m, tail[-300:])
        assert m is not None
        self.assertGreaterEqual(int(m.group(1)), 45, f"핀 없이 {m.group(1)}개만 돌았다")


class TestTheNumberHasAnOwner(unittest.TestCase):
    """숫자를 옮겨 적지 않는다 — **어디서 나오는지**를 못박는다."""

    def test_ci_installs_the_pins_and_runs_the_suite(self) -> None:
        body = CI.read_text(encoding="utf-8")
        # **설치 줄만** 본다. 파일 전체를 보면 바로 위 주석에 `fastapi` 가 있어서,
        # 설치에서 빼는 뮤테이션이 그대로 통과한다 — `#242` 에서 겪은 것과 같다.
        install = [l for l in body.splitlines() if "pip install" in l and "httpx" in l]
        self.assertEqual(1, len(install), f"capreq 핀 설치 줄을 못 찾았다: {install}")
        for pin in ("httpx", "fastapi", "python-multipart"):
            with self.subTest(pin=pin):
                self.assertIn(pin, install[0], f"capreq 잡이 {pin} 을 안 깐다")
        self.assertIn("discover -s capreq/tests", body,
                      "capreq 잡이 그 스위트를 안 돌린다")

    def test_the_pinned_list_matches_reality(self) -> None:
        names = {p.name for p in _test_files()}
        ghosts = sorted(n for n in NEEDS_A_PIN if n not in names)
        self.assertEqual([], ghosts, f"없는 파일이 목록에 있다: {ghosts}")

    def test_unpinned_modules_import_nothing_heavy(self) -> None:
        """핀 없이 도는 넷이 무거운 것을 import 하면 이 표가 거짓이 된다."""
        heavy = {"httpx", "fastapi", "psycopg", "torch"}
        files = _test_files()
        self.assertTrue(files, "capreq 검사 파일을 하나도 못 찾았다")
        bad = []
        for path in files:
            if path.name in NEEDS_A_PIN:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [(node.module or "").split(".")[0]]
                else:
                    continue
                for n in names:
                    if n in heavy:
                        bad.append(f"{path.name}: {n}")
        self.assertEqual([], bad, f"핀 없이 도는 모듈이 무거운 것을 부른다: {bad}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_files_are_seen(self) -> None:
        self.assertGreaterEqual(len(_test_files()), 7, [p.name for p in _test_files()])

    def test_three_need_pins(self) -> None:
        self.assertEqual(3, len(NEEDS_A_PIN))


if __name__ == "__main__":
    unittest.main()
