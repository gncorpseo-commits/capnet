"""검사가 **빈 목록을 돌며 초록**이 되지 않는가 (큐 #21).

## 왜 있는가

이 회차들이 고쳐 온 결함의 원형이다 — [#181](https://github.com/gncorpseo-commits/capnet/pull/181)
은 통합 러너가 **0개를 돌고 「통과 0 · 실패 0」** 을 찍었고,
[#187](https://github.com/gncorpseo-commits/capnet/pull/187) 은 방 판정이 같은 모양이었다.
`for x in f(): self.assertX(...)` 는 **`f()` 가 비면 아무것도 안 보고 통과한다.**

### 결론부터 — 실제로 초록이 되는 검사는 **0건**이었다

훑기로 걸린 후보를 **대상을 비워서** 확인했다. 추출기가 아무것도 못 찾게 만들자
`test_text_extract` 는 **21건 중 6건이 실패**했고, PII 규칙을 비우자
`test_safety_pii` 는 **32건 중 11건이 실패**했다. **형제 검사가 받쳐 주고 있었다.**

**「스캐너가 세 자리」라고 적지 않았다** — #192 가 「결함 11건」이라고 적지 않은 것과 같다.

### 그래도 고친 이유

받쳐 주는 것이 **다른 검사**라는 것은, 그 형제를 지우는 순간 조용히 구멍이 난다는 뜻이다.
호출 결과를 도는 **여덟** 자리에 바닥 한 줄씩 넣어 **스스로 서게** 했다.

| 검사 | 무엇이 비면 초록이었나 |
|---|---|
| `test_migrate_lint::…lint_clean` | 마이그레이션 디렉터리를 못 읽을 때 |
| `test_modality_fallback::…is_decided` | 모달리티 어휘가 빌 때 |
| `test_node_core_unreachable` ×2 | **`except` 를 통째로 지웠을 때** |
| `test_node_routes_are_pinned::…credential` | `health` 가 빈 dict 일 때 |
| `test_pass_rate_script::…arch_names` | arch 목록이 빌 때 |
| `test_safety_pii::…original_span` | 스캐너가 아무것도 못 찾을 때 |
| `test_text_extract::…the_value` | 추출기가 아무것도 못 찾을 때 |

## 무엇을 고정하나

**단언이 전부 `for` 루프 안에 있고, 그 루프가 「호출 결과」를 돌면, 같은 함수 안에
바닥 단언이 있어야 한다.**

## 왜 이렇게 좁은가

- **호출 결과만** 본다 — 리터럴 튜플·모듈 상수는 비면 눈에 보인다
- **같은 함수 안**을 본다 — 형제 검사에 기대는 것이 이번에 고친 문제다
- 개수를 못박지 않는다 (`test_doc_counts` 규율)

훑기를 세 번 좁혔다: 721개 함수 → 루프 안에만 단언 **75** → 계산된 컬렉션 **31** →
**호출 결과 8**. 넓게 잡은 판은 리터럴 튜플을 「위험」으로 셌다 — 그대로 뒀으면
검사가 **일흔다섯 자리에 잔소리**를 했을 것이다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_DIRS = (ROOT / "tests", ROOT / "capreq" / "tests")


def _test_files() -> list[Path]:
    out: list[Path] = []
    for d in TEST_DIRS:
        out.extend(sorted(d.glob("test_*.py")))
    return out


def _assert_calls(node: ast.AST) -> list[ast.Call]:
    return [
        c for c in ast.walk(node)
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
        and c.func.attr.startswith("assert")
    ]


def _is_len(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len"


def _has_floor(fn: ast.AST) -> bool:
    """「비어 있지 않다」를 말하는 단언이 **이 함수 안에** 있는가."""
    for c in _assert_calls(fn):
        name = c.func.attr  # type: ignore[union-attr]
        if name in ("assertGreater", "assertGreaterEqual"):
            return True
        if name == "assertEqual" and len(c.args) >= 2 and _is_len(c.args[0]):
            return True
        if name == "assertTrue" and c.args and not isinstance(c.args[0], ast.Constant):
            return True
    return False


def _needs_floor(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """바닥이 필요한 루프들의 소스. 없으면 빈 목록."""
    loops = [n for n in ast.walk(fn) if isinstance(n, (ast.For, ast.AsyncFor))]
    if not loops:
        return []
    in_loop = sum(len(_assert_calls(loop)) for loop in loops)
    if in_loop == 0 or in_loop != len(_assert_calls(fn)):
        return []  # 루프 밖에도 단언이 있으면 그것이 바닥 노릇을 한다
    return [
        ast.unparse(loop.iter) for loop in loops
        if isinstance(loop.iter, (ast.Call, ast.Subscript))
    ]


def _offenders() -> list[str]:
    bad: list[str] = []
    for path in _test_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not fn.name.startswith("test_"):
                continue
            iters = _needs_floor(fn)
            if iters and not _has_floor(fn):
                bad.append(f"{path.name}:{fn.lineno} {fn.name} — {iters[0][:60]}")
    return sorted(bad)


class TestEveryLoopTestHasAFloor(unittest.TestCase):
    def test_no_test_can_pass_on_an_empty_result(self) -> None:
        """**여기가 핵심이다.** 대상이 아무것도 안 내놓아도 초록인 검사를 막는다."""
        bad = _offenders()
        self.assertEqual(
            [], bad,
            "호출 결과를 돌면서 바닥 단언이 없다 — 결과가 비면 조용히 통과한다. "
            f"`self.assertTrue(got, …)` 한 줄을 넣는다: {bad}",
        )


class TestProbeActuallyScans(unittest.TestCase):
    """훑는 범위가 비면 위 검사가 **공허하게** 통과한다 — 이 파일이 막는 것과 같은 모양이다."""

    def test_found_enough_test_files(self) -> None:
        self.assertGreater(len(_test_files()), 30,
                           f"검사 파일을 {len(_test_files())}개밖에 못 찾았다")

    def test_floor_detector_actually_discriminates(self) -> None:
        """탐지기가 **전부 통과**시키면 위 검사는 아무것도 안 지킨다."""
        with_floor = ast.parse(
            "def test_x(self):\n"
            "    got = f()\n"
            "    self.assertTrue(got, 'x')\n"
            "    for i in got:\n"
            "        self.assertEqual(1, i)\n"
        ).body[0]
        without = ast.parse(
            "def test_y(self):\n"
            "    for i in f():\n"
            "        self.assertEqual(1, i)\n"
        ).body[0]
        assert isinstance(with_floor, ast.FunctionDef) and isinstance(without, ast.FunctionDef)
        self.assertTrue(_has_floor(with_floor), "바닥이 있는데 없다고 본다")
        self.assertFalse(_has_floor(without), "바닥이 없는데 있다고 본다")
        self.assertTrue(_needs_floor(without), "바닥이 필요한 모양을 못 알아본다")

    def test_literal_loops_are_not_flagged(self) -> None:
        """리터럴 튜플은 비면 눈에 보인다. 잔소리하면 사람이 검사를 끈다."""
        fn = ast.parse(
            "def test_z(self):\n"
            "    for i in (1, 2, 3):\n"
            "        self.assertEqual(1, i)\n"
        ).body[0]
        assert isinstance(fn, ast.FunctionDef)
        self.assertEqual([], _needs_floor(fn))


if __name__ == "__main__":
    unittest.main()
