r"""등록된 바닥이 **실제로 무는가** (배치 B #77 · `#230` 잔여).

## 왜 있는가

`#230`(큐 #50)은 바닥 92건을 등록부에 적어 **내려가면 운다**고 했다. 그런데 애초에
**물지 않는 바닥**이 등록되면 등록부는 그것을 「지킨다」고 센다.

물지 않는 모양은 하나다 — `assertGreaterEqual(len(x), 0)`. 길이는 음수가 없으니
**언제나 참**이고, 그걸 바닥이라 부르면 `#210` 이 잡은 「바닥을 내리면 초록」의
**처음부터 내려간 판**이다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| 등록된 바닥 | **140** |
| 값이 0 인 것 | **2** — 둘 다 `assertGreater(…, 0)` (**strict** · 실효 바닥 1) |
| `assertGreaterEqual(…, 0)` (공허) | **0** ✅ |

## 무엇을 고정하나

1. `tests/` 어디에도 `assertGreaterEqual(…, 0)` 이 없다
2. 값 0 으로 등록된 바닥은 전부 **strict**(`assertGreater`)다
3. 세는 대상이 비지 않는다
"""

from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
sys.path.insert(0, str(ROOT / "scripts"))
from floor_registry import floors  # noqa: E402


def _floor_calls() -> list[tuple[str, str, int]]:
    """`(파일:줄, 호출 이름, 바닥 값)` — 리터럴 바닥 전부."""
    out = []
    for path in sorted(TESTS.glob("test_*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            if node.func.attr not in ("assertGreaterEqual", "assertGreater") or len(node.args) < 2:
                continue
            arg = node.args[1]
            if isinstance(arg, ast.Constant) and type(arg.value) is int:
                out.append((f"{path.name}:{node.lineno}", node.func.attr, arg.value))
    return out


class TestNoFloorIsVacuous(unittest.TestCase):
    def test_no_greater_equal_zero(self) -> None:
        """**여기가 핵심이다.** 길이는 음수가 없다 — `>= 0` 은 바닥이 아니다."""
        calls = _floor_calls()
        self.assertTrue(calls, "바닥 호출을 하나도 못 찾았다")
        bad = [where for where, kind, v in calls if kind == "assertGreaterEqual" and v <= 0]
        self.assertEqual([], bad, f"언제나 참인 바닥: {bad}")

    def test_zero_valued_floors_are_strict(self) -> None:
        zeros = [(where, kind) for where, kind, v in _floor_calls() if v == 0]
        self.assertTrue(zeros, "0 바닥이 하나도 없다 — 이 검사의 전제가 바뀌었다")
        loose = [where for where, kind in zeros if kind != "assertGreater"]
        self.assertEqual([], loose, f"0 인데 strict 가 아닌 바닥: {loose}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_registry_and_scan_agree_on_scale(self) -> None:
        self.assertGreaterEqual(len(floors()), 100, len(floors()))
        self.assertGreaterEqual(len(_floor_calls()), 100, len(_floor_calls()))

    def test_detector_would_catch_a_vacuous_floor(self) -> None:
        fn = ast.parse("def t(self):\n    self.assertGreaterEqual(len(x), 0)\n").body[0]
        found = [n for n in ast.walk(fn) if isinstance(n, ast.Call)]
        self.assertEqual(0, found[0].args[1].value)


if __name__ == "__main__":
    unittest.main()
