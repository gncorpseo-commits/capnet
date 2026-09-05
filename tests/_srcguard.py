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
| 5 | `app/work_units.py` | 「RSS 로 대체하지 않는다」 **응답 문자열 상수** |

5번은 이 헬퍼로도 못 막는다 — 주석도 docstring 도 아닌 **코드가 실제로 내보내는 값**이다.
거기서 배운 것: 단어 금지 대신 **「무엇을 했나」를 본다** (`test_work_units_wiring` 참조).

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


def hash_comment_free(path: str | Path) -> str:
    """YAML·셸에서 `#` 주석을 비운 문자열 (줄 번호 유지).

    ## 왜 필요한가

    위 `code_only` 는 **파이썬**만 본다. 그런데 이 저장소가 실제로 네 번 더 걸린 자리는
    **YAML 주석**이었다 (`#242` · `#248` · `#255`, 그리고 아래 둘):

        # restart: "no"  ← 주석으로 옮겨도 「restart: "no" 가 있다」 검사가 통과했다
        # NODE_CREDENTIAL_FILE: …  ← 같은 모양. 그 Node 는 증서 없이 돈다

    「설정이 있다」를 텍스트로 확인할 때는 **주석을 걷고** 봐야 한다.
    반대로 「그 이유가 적혀 있다」를 볼 때는 **원문**을 본다 — 그건 주석이 본체다.

    ## 따옴표 안의 `#` 는 안 지운다

    `key: "a#b"` · `printf '%s#%s'` 처럼 값에 든 것은 주석이 아니다.
    """
    out: list[str] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        quote = ""
        cut = len(raw)
        for i, ch in enumerate(raw):
            if quote:
                if ch == quote:
                    quote = ""
            elif ch in "\"'":
                quote = ch
            elif ch == "#":
                cut = i
                break
        out.append(raw[:cut].rstrip())
    return "\n".join(out) + "\n"
