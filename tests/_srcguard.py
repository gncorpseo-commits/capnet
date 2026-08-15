"""소스 텍스트 검사용 헬퍼 — **주석과 docstring 을 걷어낸다.**

## 왜 있는가

「이 코드가 X 를 쓰지 않는다」를 텍스트로 검사할 때, **X 를 쓰지 않는다고 적어 둔 설명이
검사에 걸리는** 사고가 이 리포에서 **네 번** 났다.

| # | 어디 | 걸린 문구 |
|---|------|-----------|
| 1 | `test_ui_invariants` | 「`localStorage` 를 쓰지 않는 이유」 주석 |
| 2 | `migrations/0018` | 「`NOT VALID` 로 우회하지 않는다」 주석 |
| 3 | `app/arch.py` | 「`ON CONFLICT DO NOTHING` 으로 넘기지 않는다」 docstring |
| 4 | `app/text_features.py` | 「`hash()` 를 쓰지 않는다」 docstring |

매번 그 자리에서 고치면 다섯 번째가 온다. 그래서 한 곳으로 모았다.
**설명을 지워야 통과하는 검사를 만들지 않는다** — 그건 문서를 벌주는 검사다.

## 왜 삼중따옴표를 통째로 지우지 않나

SQL 이 삼중따옴표 리터럴이다. 같이 지우면 `UPDATE`·`DELETE` 검사가 무력해진다.
`ast` 로 **docstring 위치만** 골라 비운다.
"""

from __future__ import annotations

import ast
from pathlib import Path

_DOC_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _docstring_lines(tree: ast.AST) -> set[int]:
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, _DOC_OWNERS):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return lines


def code_only(path: str | Path) -> str:
    """파이썬 소스에서 `#` 주석과 docstring 을 비운 문자열.

    줄 번호는 유지된다(비운 줄은 빈 줄로 남는다) — 오류 메시지에서 위치를 잃지 않게.
    """
    src = Path(path).read_text(encoding="utf-8")
    doc = _docstring_lines(ast.parse(src))
    return "\n".join(
        "" if (i + 1) in doc else line.split("#", 1)[0]
        for i, line in enumerate(src.splitlines())
    )
