r"""API 오류 문구·Node 예외에 **내부 경로**가 실리지 않는가 (배치 D #146).

## 실측 (2026-09-06) — `apps/core/app`·`apps/node/app` 의 `HTTPException(detail=…)`·`raise …(…)` 247개

| 무엇 | 값 |
|---|---|
| 문구에 `path`·`file`·`dir`·`weights`·`blob` 이름의 값을 포맷 | **0** (API·Node) |
| 문구 리터럴에 `/app/`·`/weights/`·`/inputs/`·`/golden/`·`/tmp/` | **0** |
| 예외 | `migrate_lint.py` — CLI 린트 도구가 마이그레이션 **파일 이름**(basename)을 말한다. 응답이 아니다 |

## 재현

```bash
python3 -m unittest tests.test_error_messages_carry_no_internal_path
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [p for p in sorted((ROOT / "apps" / "core" / "app").glob("*.py")) + sorted((ROOT / "apps" / "node" / "app").glob("*.py"))
         if p.name != "migrate_lint.py"]      # CLI 린트 도구 — 파일 이름(basename)을 말하는 게 일이다
PATHY = re.compile(r"\b(path|file|dir|weights_path|blob|filename)\b", re.I)
LITERAL = re.compile(r"/(app|weights|inputs|golden|tmp)/")


def _messages():
    for p in FILES:
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            msg = None
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "HTTPException":
                for k in node.keywords:
                    if k.arg == "detail":
                        msg = k.value
            elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and node.exc.args:
                msg = node.exc.args[0]
            if msg is not None:
                yield p.name, node.lineno, msg


class TestNoInternalPathInMessages(unittest.TestCase):
    def test_no_path_value_is_formatted(self) -> None:
        bad, seen = [], 0
        for f, l, msg in _messages():
            seen += 1
            if isinstance(msg, ast.JoinedStr):
                for v in msg.values:
                    if isinstance(v, ast.FormattedValue) and PATHY.search(ast.unparse(v.value)):
                        bad.append(f"{f}:{l} {{{ast.unparse(v.value)}}}")
        self.assertGreaterEqual(seen, 200, seen)
        self.assertEqual([], bad, f"오류 문구가 경로를 싣는다: {bad}")

    def test_no_literal_internal_path(self) -> None:
        bad = [f"{f}:{l}" for f, l, msg in _messages()
               if isinstance(msg, ast.Constant) and isinstance(msg.value, str) and LITERAL.search(msg.value)]
        self.assertEqual([], bad, f"오류 문구 리터럴에 내부 경로: {bad}")


if __name__ == "__main__":
    unittest.main()
