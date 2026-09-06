r"""공개 GET 여섯이 **네 곳에서 같은가** — 코드 · `PUBLIC` · `prod_room` · D24 (배치 C #109 · `#192` 핀).

## 실측 (2026-09-06)

| 어디 | 무엇 | 수 |
|---|---|---|
| 코드 | `authorization` 을 받지 않는 `@app.get` 핸들러 | 6 |
| `test_every_route_declares_its_auth.PUBLIC` | 이유가 붙은 공개 목록 | 6 |
| `scripts/prod_room.sh` | 「공개 GET … (키 없음)」 루프 | 6 |
| D24 (`docs/context-handoff.md`) | 「Agent 는 org 를 갖지 않는다 (공용 카탈로그)」 — 카탈로그가 공개인 근거 | 문장 |

`STATE.md` 의 「공개 GET 6→1」 같은 숫자는 연대기라 여기서 맞추지 않는다.

## 재현

```bash
python3 -m unittest tests.test_public_get_set_agrees_everywhere
```
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402
from test_every_route_declares_its_auth import PUBLIC  # noqa: E402

MAIN = ROOT / "apps" / "core" / "app" / "main.py"
PROD_ROOM = ROOT / "scripts" / "prod_room.sh"
HANDOFF = ROOT / "docs" / "context-handoff.md"


def _code_public_gets() -> set[str]:
    out = set()
    for fn in ast.parse(MAIN.read_text(encoding="utf-8")).body:
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for d in fn.decorator_list:
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "get":
                if not any(a.arg == "authorization" for a in fn.args.args):
                    out.add(d.args[0].value)
    return out


def _prod_room_public_gets() -> set[str]:
    body = hash_comment_free(PROD_ROOM)
    i = body.index('chk "공개 GET')
    head = body[:i]
    loop = head[head.rfind("for path in"):]
    return {p.replace("$capid", "{capability_id}") for p in re.findall(r'"(/[^"]*)"', loop)}


class TestFourPlacesAgree(unittest.TestCase):
    def test_code_equals_the_pinned_list(self) -> None:
        code = _code_public_gets()
        self.assertEqual(6, len(code), sorted(code))
        self.assertEqual({p for m, p in PUBLIC if m == "GET"}, code)

    def test_prod_room_probes_exactly_those(self) -> None:
        self.assertEqual(_code_public_gets(), _prod_room_public_gets())

    def test_d24_says_the_catalog_is_shared(self) -> None:
        d24 = next(l for l in HANDOFF.read_text(encoding="utf-8").splitlines() if l.startswith("| D24 |"))
        self.assertIn("공용 카탈로그", d24)


if __name__ == "__main__":
    unittest.main()
