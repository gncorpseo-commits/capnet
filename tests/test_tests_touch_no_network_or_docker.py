r"""단위 검사가 **네트워크·Docker 를 몰래 부르지 않는가** (배치 D #144).

## 왜 있는가

`run_tests` 는 「의존성 설치 없음 · DB 없음」이 약속이다. 검사 하나가 `urlopen`·`docker` 를 부르면 그 약속이 조용히 깨지고,
오프라인·Docker 없는 곳(이 세션)에서 결과가 달라진다.

## 실측 (2026-09-06) — `tests/test_*.py` AST 전수

| 무엇 | 값 |
|---|---|
| `urlopen`·`socket`·`httpx`·`requests` 호출 | **0** |
| `subprocess` 의 argv[0] | `bash` · `git` · `sed` · `sys.executable` 뿐 — `docker`·`curl`·`pip`·`gh` **0** |
| `bash` 로 도는 것 | 저장소의 `scripts/lib/*.sh` 함수 · `bash -n` 문법 검사 · 임시 사본 |

## 재현

```bash
python3 -m unittest tests.test_tests_touch_no_network_or_docker
```
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
NET_FUNCS = ("urlopen", "create_connection", "getaddrinfo")
NET_MODULES = ("httpx.", "requests.", "socket.", "aiohttp.")
SUBPROCESS = ("subprocess.run", "subprocess.check_output", "subprocess.Popen", "subprocess.call", "subprocess.check_call")
LOCAL_TOOLS_ARGV0 = ("bash", "git", "sed", "sys.executable")


def _calls():
    for p in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                yield p.name, n.lineno, ast.unparse(n.func), n


class TestNoHiddenNetworkOrDocker(unittest.TestCase):
    def test_no_network_call(self) -> None:
        bad = [f"{f}:{l} {fn}" for f, l, fn, _ in _calls()
               if fn.endswith(NET_FUNCS) or fn.startswith(NET_MODULES)]
        self.assertEqual([], bad, f"검사가 네트워크를 부른다: {bad}")

    def test_subprocess_targets_are_local_tools_only(self) -> None:
        seen, bad = 0, []
        for f, l, fn, call in _calls():
            if fn not in SUBPROCESS or not call.args:
                continue
            seen += 1
            argv = call.args[0]
            first = ast.unparse(argv.elts[0]) if isinstance(argv, ast.List) and argv.elts else ast.unparse(argv)
            first = first.strip("'\"")
            if first not in LOCAL_TOOLS_ARGV0:
                bad.append(f"{f}:{l} {first}")
            joined = ast.unparse(argv)
            if any(tok in joined for tok in ("'docker'", '"docker"', "'curl'", '"curl"', "'pip'", '"pip"', "'gh'", '"gh"')):
                bad.append(f"{f}:{l} {joined[:60]}")
        self.assertGreaterEqual(seen, 15, seen)
        self.assertEqual([], bad, f"검사가 외부 도구를 부른다: {bad}")


if __name__ == "__main__":
    unittest.main()
