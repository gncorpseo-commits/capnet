"""Node 가 **실행 실패를 Core 에 알리는가** (0015).

## 왜 있는가

큐 #33 — 「고쳤다고 주석에 적혀 있는데 못박은 검사가 없는 자리」 전수에서 나온 둘째.

`apps/node/app/main.py:180` 의 주석:

    보고하지 않으면 실패가 **lease 만료(60초)로만** 드러나고, 그 동안 같은 배정을
    계속 재시도한다 — 로그에만 쌓이고 증적에는 없다.
    **실측으로 채널 불일치 38건이 그렇게 쌓였다.**

실측 숫자까지 적힌 과거 사고인데 **못박은 검사가 없었다** (2026-09-03):

```text
grep -rl "_report_failure" tests/ capreq/tests  → 없음
```

이 배선이 조용히 빠지면 증상이 「느리다」로만 보인다 — 실패가 60초 뒤에야 드러나고
그 사이 같은 배정을 계속 잡는다. **로그에는 쌓이고 증적에는 없다.**

## 왜 `ast` 로 보나

`apps/node/app/main.py` 는 임포트에 `fastapi` 가 필요하고 CI 단위 잡은 의존성이 0이다
(`test_openapi_drift`·`test_every_route_declares_its_auth` 와 같은 이유).
**돌려서 보는 것은 `prod_room`·통합 잡의 몫**이고, 여기서는 배선이 있는지만 본다.

## 무엇을 고정하나

1. `_report_failure` 가 **있다**
2. Core 의 **실패 보고 경로**(`/v1/internal/assignments/{id}/fail`)를 부른다
3. 배정 실행의 `except` 에서 **실제로 호출된다** — 정의만 있고 안 부르면 같은 사고다
4. **보고 실패를 삼킨다** — 보고가 죽어서 루프가 죽으면 더 나빠진다
5. Core 쪽에 **받는 라우트가 있다**

## 무엇을 고정하지 **않나**

재시도 횟수·타임아웃 값. 정책 숫자라 여기서 정하지 않는다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = ROOT / "apps" / "node" / "app" / "main.py"
CORE = ROOT / "apps" / "core" / "app" / "main.py"

FAIL_PATH = "/v1/internal/assignments/{assignment_id}/fail"


def _tree() -> ast.Module:
    return ast.parse(NODE.read_text(encoding="utf-8"))


def _func(name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for n in ast.walk(_tree()):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _calls(node: ast.AST) -> set[str]:
    return {
        c.func.id for c in ast.walk(node)
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
    }


class TestReporterExists(unittest.TestCase):
    def test_function_is_defined(self) -> None:
        self.assertIsNotNone(_func("_report_failure"), "_report_failure 가 사라졌다")

    def test_it_targets_the_failure_route(self) -> None:
        fn = _func("_report_failure")
        assert fn is not None
        src = ast.get_source_segment(NODE.read_text(encoding="utf-8"), fn) or ""
        self.assertIn("/v1/internal/assignments/", src, "실패 보고 경로를 안 부른다")
        self.assertIn("/fail", src, "완료 경로와 실패 경로를 혼동했다")
        self.assertIn("POST", src, "POST 가 아니다")

    def test_it_swallows_its_own_errors(self) -> None:
        """보고가 죽어서 실행 루프가 죽으면 **더 나빠진다.**"""
        fn = _func("_report_failure")
        assert fn is not None
        self.assertTrue(
            any(isinstance(n, ast.Try) for n in ast.walk(fn)),
            "보고 실패를 안 삼킨다 — 루프가 같이 죽는다",
        )


class TestReporterIsActuallyWired(unittest.TestCase):
    """**정의만 있고 안 부르면 같은 사고다.**"""

    def test_called_from_an_exception_handler(self) -> None:
        src = NODE.read_text(encoding="utf-8")
        handlers = [
            h for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Try) for h in n.handlers
        ]
        self.assertTrue(
            any("_report_failure" in _calls(h) for h in handlers),
            "_report_failure 를 except 절에서 부르지 않는다 — 실패가 lease 만료로만 드러난다",
        )

    def test_it_is_not_only_defined(self) -> None:
        """호출부가 **하나도** 없으면 위 검사가 통과할 길이 없지만, 명시적으로 센다."""
        src = NODE.read_text(encoding="utf-8")
        calls = sum(
            1 for c in ast.walk(ast.parse(src))
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
            and c.func.id == "_report_failure"
        )
        self.assertGreaterEqual(calls, 1, "_report_failure 를 아무도 안 부른다")


class TestCoreAcceptsIt(unittest.TestCase):
    def test_core_has_the_route(self) -> None:
        """Node 가 부르는데 Core 에 없으면 **매번 조용히 실패**한다."""
        self.assertIn(f'"{FAIL_PATH}"', CORE.read_text(encoding="utf-8"),
                      f"Core 에 {FAIL_PATH} 가 없다")


class TestProbeActuallyWorks(unittest.TestCase):
    def test_parser_found_the_module(self) -> None:
        """`ast` 가 빈 트리를 훑으며 통과하지 않는가."""
        fns = [n for n in ast.walk(_tree())
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        self.assertGreater(len(fns), 10, f"함수를 {len(fns)}개밖에 못 찾았다")


if __name__ == "__main__":
    unittest.main()
