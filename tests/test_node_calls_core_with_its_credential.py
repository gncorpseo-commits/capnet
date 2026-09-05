r"""Node 가 Core 를 부르는 **모든 자리**가 증서 헤더를 싣는가 (G2 · `#89`·`#81` 의 형제 전수).

## 왜 있는가

`#89` 는 바이트 경로 하나를, `#81` 은 증서가 문자열로 합쳐지는 한 줄을 봤다. 형제는 「Core 로 나가는
요청 전부」다 — 하나라도 `_core_headers()` 없이 나가면 강제 모드에서 401 이 되거나, 반대로 증서를 다른
방식으로 실어 새는 길이 생긴다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `urllib.request.Request(` | **5** — 전부 `headers=_core_headers()` |
| 다른 HTTP 클라이언트(`httpx`·`requests`) | **0** |
| 증서를 헤더에 싣는 함수 | `_core_headers()` 하나 |

## 재현

```bash
python3 -m unittest tests.test_node_calls_core_with_its_credential
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = ROOT / "apps" / "node" / "app"


def _requests() -> list[tuple[int, bool]]:
    """`urllib.request.Request(` 호출마다 (줄, `headers=_core_headers()` 인가)."""
    src = (NODE / "main.py").read_text(encoding="utf-8")
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "urllib.request.Request":
            ok = any(k.arg == "headers" and ast.unparse(k.value) == "_core_headers()" for k in node.keywords)
            out.append((node.lineno, ok))
    return out


class TestEveryCoreCallCarriesTheCredential(unittest.TestCase):
    def test_all_requests_use_core_headers(self) -> None:
        reqs = _requests()
        self.assertEqual(5, len(reqs), reqs)
        self.assertEqual([], [ln for ln, ok in reqs if not ok], "증서 헤더 없이 나가는 Core 호출")

    def test_no_other_http_client(self) -> None:
        files = sorted(NODE.glob("*.py"))
        self.assertTrue(files, "Node 모듈을 못 찾았다")
        for p in files:
            with self.subTest(file=p.name):
                self.assertNotRegex(p.read_text(encoding="utf-8"), r"(?m)^\s*(?:import|from)\s+(?:httpx|requests|aiohttp)\b",
                                    f"{p.name} 이 다른 HTTP 클라이언트를 쓴다 — 헤더 규약 밖")

    def test_core_headers_is_the_only_place_the_credential_becomes_a_header(self) -> None:
        src = (NODE / "main.py").read_text(encoding="utf-8")
        sites = [i for i, ln in enumerate(src.splitlines(), 1) if "Authorization" in ln and "CapNet-Node" in ln]
        self.assertEqual(1, len(sites), sites)


if __name__ == "__main__":
    unittest.main()
