r"""역할 가드를 **새 모양으로 우회하지 않는가** (큐 #65 · `#192`·`#193` 이후).

## 왜 있는가

`#192`·`#193` 은 **그때 있던** 우회를 닫았다. 우회는 새 문법으로 다시 열린다 —
FastAPI 는 인증을 **여러 방식**으로 붙일 수 있고, 방식이 늘 때마다 「이 라우트가
인증을 하는가」를 세는 검사가 눈을 감는다.

`test_every_route_declares_its_auth` 는 **본문에서 헬퍼를 불렀는가**만 본다. 그 전제가
깨지는 모양 넷을 여기서 센다.

| 모양 | 왜 위험한가 | 오늘 |
|---|---|---|
| `Depends(...)` | 인증이 **시그니처**로 옮겨가면 본문 스캔이 못 본다 | **0** |
| 라우트를 감싸는 커스텀 데코레이터 | 같음 — 데코레이터를 빼면 조용히 열린다 | **0** |
| `if …: _require(…)` | **조건이 거짓이면 인증이 아예 안 돈다** | **0** |
| `_require(변수, …)` | 역할이 정적으로 안 보인다 — 무엇을 요구하는지 못 센다 | **0** |

**넷 다 0 이다.** 인증 호출 **41**건은 전부 함수 본문의 무조건 호출이고 역할은 리터럴이다.

## 왜 「0」을 검사로 남기나

`test_integration_runner` 머리말과 같은 이유다 — **여기는 아직 그런 일이 없다.
나기 전에 막는다.** 이 넷 중 하나라도 생기면 그때는 「인증을 선언했는가」를 세는 검사가
**이미 눈이 먼 뒤**다.

## 무엇을 안 보나

`Depends` 로 인증을 붙이는 것이 **나쁘다**고 말하지 않는다. 그렇게 바꾸려면
`test_every_route_declares_its_auth` 의 탐지기를 **같이** 고쳐야 한다는 뜻이다 —
이 검사는 그 순간에 운다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"

AUTH = frozenset({"_require", "_actor", "_authenticated_node", "_assert_node_matches",
                  "redeem_invite", "verify_invite"})


def _route_functions() -> list[ast.FunctionDef]:
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    out = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
               and isinstance(d.func.value, ast.Name) and d.func.value.id == "app"
               for d in fn.decorator_list):
            out.append(fn)
    return out


def _auth_calls(fn: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in AUTH]


def _conditional_auth() -> list[str]:
    """`if …: _require(…)` — 조건이 거짓이면 **인증이 아예 안 돈다**."""
    bad = []
    for fn in _route_functions():
        for node in ast.walk(fn):
            if not isinstance(node, (ast.If, ast.IfExp)):
                continue
            for call in _auth_calls(node):
                bad.append(f"{fn.name}:{call.lineno} ({call.func.id})")  # type: ignore[union-attr]
    return sorted(set(bad))


def _non_literal_roles() -> list[str]:
    bad = []
    for fn in _route_functions():
        for call in _auth_calls(fn):
            if call.func.id != "_require" or not call.args:  # type: ignore[union-attr]
                continue
            first = call.args[0]
            if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                bad.append(f"{fn.name}:{call.lineno} {ast.unparse(first)}")
    return sorted(bad)


def _custom_decorators() -> list[str]:
    """`@app.<verb>` 밖의 데코레이터. 라우트를 감싸면 본문 스캔이 못 본다."""
    bad = []
    for fn in _route_functions():
        for dec in fn.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) \
                    and isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app":
                continue
            bad.append(f"{fn.name}: @{ast.unparse(dec)}")
    return sorted(bad)


class TestAuthStaysWhereTheScannerLooks(unittest.TestCase):
    def test_no_dependency_injection_for_auth(self) -> None:
        """인증이 시그니처로 옮겨가면 **본문 스캔이 못 본다**."""
        self.assertFalse("Depends(" in MAIN.read_text(encoding="utf-8"),
                         "main.py 에 Depends() 가 생겼다 — 인증 탐지기를 같이 고쳐야 한다")

    def test_no_custom_decorator_wraps_a_route(self) -> None:
        self.assertEqual([], _custom_decorators(),
                         f"라우트에 커스텀 데코레이터가 붙었다: {_custom_decorators()}")

    def test_no_auth_call_sits_inside_a_condition(self) -> None:
        """**여기가 핵심이다.** 조건이 거짓이면 인증이 안 돈다."""
        self.assertEqual([], _conditional_auth(),
                         f"조건문 안에서 인증한다: {_conditional_auth()}")

    def test_every_required_role_is_a_literal(self) -> None:
        """역할이 변수면 **무엇을 요구하는지** 정적으로 못 센다."""
        self.assertEqual([], _non_literal_roles(),
                         f"역할이 리터럴이 아니다: {_non_literal_roles()}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_routes_and_calls_are_seen(self) -> None:
        fns = _route_functions()
        self.assertGreaterEqual(len(fns), 40, f"라우트 {len(fns)}개만 봤다")
        calls = sum(len(_auth_calls(fn)) for fn in fns)
        self.assertGreaterEqual(calls, 35, f"인증 호출 {calls}건만 봤다")

    def test_the_conditional_detector_works(self) -> None:
        """탐지기가 조건부 인증을 못 잡으면 위 검사가 **공허하게** 통과한다."""
        fn = ast.parse("def f(a):\n    if a:\n        _require('admin', a)\n").body[0]
        found = [n for n in ast.walk(fn) if isinstance(n, (ast.If, ast.IfExp))]
        self.assertTrue(found)
        self.assertTrue(_auth_calls(found[0]))

    def test_the_role_detector_works(self) -> None:
        fn = ast.parse("def f(r, a):\n    _require(r, a)\n").body[0]
        call = _auth_calls(fn)[0]
        self.assertFalse(isinstance(call.args[0], ast.Constant))


if __name__ == "__main__":
    unittest.main()
