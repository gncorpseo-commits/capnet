"""capreq 가 **루프백에만 뜨는가** — 그리고 응답에 키를 흘리지 않는가.

## 왜 있는가

[#192](https://github.com/gncorpseo-commits/capnet/pull/192)·
[#193](https://github.com/gncorpseo-commits/capnet/pull/193)이 **Core** 를,
[#194](https://github.com/gncorpseo-commits/capnet/pull/194)가 **Node** 를
전수해 못박았다. **capreq 는 그 밖이었다.**

capreq 의 라우트 다섯(`/` · `/api/health` · `/api/capabilities` ·
`/api/tasks/{id}` · `/api/chat`)에는 **인증이 없다.** 그게 맞다 — 운영자가
자기 기계에서 띄우는 도구다. **그 전제가 바로 「루프백에만 뜬다」이다.**

```python
ps.add_argument("--host", default="127.0.0.1")
```

**이 기본값이 조용히 `0.0.0.0` 이 되면** 망에 닿는 누구나 이 프로세스를 통해
Core 를 부를 수 있다 — capreq 는 **운영자의 `CAPNET_API_KEY` 를 헤더에 실어**
보내기 때문이다 (`adapters/capnet.py`). 인증 없는 창구가 **키를 가진 대리인**이 된다.

**오늘은 루프백이다.** 이 검사는 **그게 조용히 바뀌지 않게** 하는 것이다.

## 무엇을 고정하나

1. `serve` · `gemma` 의 `--host` 기본값이 **루프백**이다
2. 소스 어디에도 `0.0.0.0` 을 **기본값으로** 쓰지 않는다
3. 서버 응답에 **API 키가 실리지 않는다** — 키는 헤더로만 나간다
4. 라우트가 다섯 다 **선언돼 있다** (새로 늘면 분류하게 만든다)

## 무엇을 안 보나

**`--host 0.0.0.0` 을 금지하지 않는다.** 운영자가 일부러 열 수 있어야 한다 —
막는 것은 **말없이 기본값이 바뀌는 것**이다.

`fastapi`·`uvicorn` 없이 돌아야 해서 `ast` 로 소스를 읽는다 — capreq 소스를
**데이터로** 읽을 뿐 import 하지 않는다.

**`capreq/tests` 가 아니라 여기(`tests/`)에 둔다.** 그쪽은 `run_tests.sh` 가
부르지 않고 CI 의 capreq 잡에서만 돈다 (`docs/guide/testing.md` §2). 이건
**보안 기본값**이라 어디서든 돌아야 한다. 의존성이 하나도 없으니 여기 둘 수 있다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "capreq" / "src" / "capreq"
CLI = SRC / "cli.py"
SERVER = SRC / "server.py"
ADAPTER = SRC / "adapters" / "capnet.py"

LOOPBACK = {"127.0.0.1", "localhost", "::1"}

# capreq 가 여는 라우트. 인증이 없으므로 **늘어나면 여기 적어야** 통과한다.
DECLARED_ROUTES = {
    ("GET", "/"),
    ("GET", "/api/health"),
    ("GET", "/api/capabilities"),
    ("GET", "/api/tasks/{task_id}"),
    ("POST", "/api/chat"),
}


def _host_defaults() -> list[str]:
    """`add_argument("--host", default=…)` 의 기본값들."""
    out: list[str] = []
    for node in ast.walk(ast.parse(CLI.read_text(encoding="utf-8"))):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr != "add_argument":
            continue
        if not (node.args and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "--host"):
            continue
        for kw in node.keywords:
            if kw.arg == "default" and isinstance(kw.value, ast.Constant):
                out.append(str(kw.value.value))
    return out


def _routes(path: Path) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for fn in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in fn.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if dec.func.attr not in ("get", "post", "put", "patch", "delete"):
                continue
            if not (dec.args and isinstance(dec.args[0], ast.Constant)):
                continue
            out.add((dec.func.attr.upper(), str(dec.args[0].value)))
    return out


class TestServeBindsLoopback(unittest.TestCase):
    def test_every_host_default_is_loopback(self) -> None:
        """**여기가 핵심이다.** 인증 없는 창구가 망에 뜨면 키를 가진 대리인이 된다."""
        defaults = _host_defaults()
        self.assertTrue(defaults, "`--host` 기본값을 하나도 못 찾았다 — 이 검사가 헛돈다")
        bad = sorted(d for d in defaults if d not in LOOPBACK)
        self.assertEqual(bad, [], f"루프백이 아닌 `--host` 기본값: {bad}")

    def test_probe_found_both_servers(self) -> None:
        """`serve` 와 `gemma` 둘 다 봐야 한다 — 하나만 고쳐지는 일이 생긴다."""
        self.assertGreaterEqual(len(_host_defaults()), 2, _host_defaults())

    def test_no_wildcard_default_anywhere(self) -> None:
        """`0.0.0.0` 이 **기본값**으로 적힌 곳이 없다 (인자로 주는 것은 막지 않는다)."""
        for path in (CLI, SERVER):
            with self.subTest(file=path.name):
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                    if isinstance(node, ast.Constant) and node.value == "0.0.0.0":
                        self.fail(f"{path.name} 에 `0.0.0.0` 이 상수로 적혀 있다")


class TestKeyNeverLeavesInTheBody(unittest.TestCase):
    """키는 **헤더로만** 나간다 (`adapters/capnet.py`). 응답에 실리면 안 된다."""

    def test_adapter_puts_the_key_in_a_header(self) -> None:
        src = ADAPTER.read_text(encoding="utf-8")
        self.assertIn("authorization", src.lower(), "키를 헤더로 안 보낸다")

    def test_server_returns_never_reference_the_key(self) -> None:
        tree = ast.parse(SERVER.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)):
                continue
            dumped = ast.dump(node.value)
            for bad in ("api_key", "CAPNET_API_KEY", "authorization"):
                with self.subTest(token=bad):
                    self.assertNotIn(
                        bad, dumped, f"서버 응답이 `{bad}` 를 담는다 — 키가 화면으로 나간다"
                    )


class TestRoutesAreDeclared(unittest.TestCase):
    def test_routes_match_the_declaration(self) -> None:
        """인증이 없으므로 **라우트가 늘면 반드시 눈에 띄어야** 한다."""
        found = _routes(SERVER)
        self.assertEqual(
            found, DECLARED_ROUTES,
            "capreq 라우트가 선언과 다르다 — 인증이 없는 창구라 늘 때마다 본다\n"
            f"  더 생김: {sorted(found - DECLARED_ROUTES)}\n"
            f"  사라짐: {sorted(DECLARED_ROUTES - found)}",
        )

    def test_probe_actually_found_routes(self) -> None:
        self.assertGreaterEqual(len(_routes(SERVER)), 4, sorted(_routes(SERVER)))


if __name__ == "__main__":
    unittest.main()
