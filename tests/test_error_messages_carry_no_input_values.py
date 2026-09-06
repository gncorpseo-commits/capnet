r"""예외 문구·로그 인자에 **사용자 입력 값**이 실리지 않는가 (배치 C #125 · `#196` 형제).

## 왜 있는가

Node 는 실행기 예외를 `print(f"… failed: {exc}")` 로 stdout 에, `_report_failure(str(exc))` 로 Core `audit_log` 에 싣는다.
그러니 예외 **문구**에 입력 값이 들어가면 그 값은 로그와 증적에 남는다. 실측(2026-09-06) — `series_features.py` 가
CSV 셀·JSON 원소를 `{cell!r}`·`{v!r}` 로 문구에 넣고 있었다 (숫자 열의 「숫자 아님」은 전화번호일 수 있다). 타입·길이로 바꿨다.

| 무엇 | 값 |
|---|---|
| Node `raise …(f"…")` 중 입력 이름을 포맷하는 것 | **0** (예외: `preprocess.py` 의 `raw` = 계약 설정값) |
| Core `logger.*` 인자 중 내용 낱말(`text`·`body`·`payload`·`content`·`input_ref`) | **0** |

## 재현

```bash
python3 -m unittest tests.test_error_messages_carry_no_input_values
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = ROOT / "apps" / "node" / "app"
CORE = ROOT / "apps" / "core" / "app"
INPUT_NAMES = {"v", "cell", "line", "row", "text", "value", "item", "data", "raw", "obj", "record", "token", "word"}
# 이름은 입력처럼 보이지만 값은 **계약 설정**인 자리 — 이유를 적는다.
CONFIG_VALUES_LOOKING_LIKE_INPUT = {("preprocess.py", "raw"): "preprocess 선언의 설정값(resize 등) — 사용자 데이터가 아니다"}
CONTENT_WORDS = re.compile(r"\b(text|body|payload|content|input_ref|chunk)\b")


def _formatted_names(fs: ast.JoinedStr) -> set[str]:
    """값을 **그대로**(또는 `!r`·첨자·속성으로) 싣는 자리만 — `len(cell)`·`type(v).__name__` 은 값이 아니다."""
    out = set()
    for part in fs.values:
        if not isinstance(part, ast.FormattedValue):
            continue
        v = part.value
        while isinstance(v, (ast.Subscript, ast.Attribute)):
            v = v.value
        if isinstance(v, ast.Name):
            out.add(v.id)
    return out


class TestNodeExceptionsNameNoInputValue(unittest.TestCase):
    def test_zero_raises_format_an_input_name(self) -> None:
        bad, seen = [], 0
        for p in sorted(NODE.glob("*.py")):
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if not (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)):
                    continue
                for a in node.exc.args:
                    if isinstance(a, ast.JoinedStr):
                        seen += 1
                        names = _formatted_names(a) & INPUT_NAMES
                        names = {n for n in names if (p.name, n) not in CONFIG_VALUES_LOOKING_LIKE_INPUT}
                        if names:
                            bad.append(f"{p.name}:{node.lineno} {sorted(names)}")
        self.assertGreaterEqual(seen, 15, seen)
        self.assertEqual([], bad, f"예외 문구에 입력 값이 실린다: {bad}")

    def test_exemption_is_real(self) -> None:
        for (fname, name), why in CONFIG_VALUES_LOOKING_LIKE_INPUT.items():
            self.assertTrue(why)
            self.assertIn(f"{{{name}!r}}", (NODE / fname).read_text(encoding="utf-8"))


class TestCoreLogArgumentsAreNotContent(unittest.TestCase):
    def test_no_content_word_in_log_args(self) -> None:
        bad, seen = [], 0
        for p in sorted(CORE.glob("*.py")):
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("info", "warning", "error", "exception", "debug") \
                        and isinstance(node.func.value, ast.Name) and node.func.value.id == "logger":
                    seen += 1
                    for a in node.args[1:]:
                        if CONTENT_WORDS.search(ast.unparse(a)):
                            bad.append(f"{p.name}:{node.lineno} {ast.unparse(a)}")
        self.assertGreaterEqual(seen, 15, seen)
        self.assertEqual([], bad, f"로그 인자에 내용이 실린다: {bad}")


if __name__ == "__main__":
    unittest.main()
