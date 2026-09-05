r"""Core 가 죽었을 때 Node 가 **혼자 성공으로 끝내지 않는가** (큐 #67 · `#194`·`#207` 옆).

## 왜 있는가

`#207` 은 「Core 와 끊긴 Node 가 **한가한 Node 처럼** 보였다」를 고쳤다 — 조회 쪽이다.
**쓰기 쪽 질문이 남아 있었다**: 추론은 됐는데 Core 에 못 알리면 무엇이 되는가?

로컬만 성공으로 끝나면 사용자에게는 **결과가 있는데 증적이 없다.** 이 제품의 한 줄이
「누가·무엇으로 실행했는지 증적이 남고 조회된다」이므로, 그건 결과가 아니라 **거짓말**이다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| `/v1/execute` 가 응답에 싣는 것 | `"core": reported` — **Core 왕복 없이는 못 돌아온다** ✅ |
| `_post_complete` 의 예외 삼킴 | **0** — `HTTPError` 는 502 로 올리고 나머지는 그대로 터진다 ✅ |
| `contextlib.suppress` | **3** — 파일 정리 둘(`OSError`) · 실패 보고 하나 |
| 그중 Core 호출을 덮는 것 | **1** — `_report_failure` 뿐이고 **이유가 적혀 있다** |

**오늘 0건이다.**

## `_report_failure` 만 삼키는 이유 — 그건 결함이 아니다

```text
보고 자체가 실패해도 삼킨다 — 그때는 종전처럼 lease 만료로 회수된다.
```

보고는 **원래 실패를 알리는 길**이다. 그 길이 막혔다고 원래 실패를 덮으면 안 되므로
삼키고 로그만 남긴다. 회수는 lease 만료(60초)가 한다. **삼키는 것과 성공으로 끝내는
것은 다르다** — 그 차이를 이 검사가 지킨다.

## 무엇을 안 보나

**실제 단절을 재지 않는다.** Core 를 죽이고 Node 를 돌리는 것은 살아 있는 스택이
필요하다. 여기는 **코드의 모양**만 본다 — `_post_complete` 가 예외를 삼키지 않고,
성공 응답이 Core 의 답을 싣는가.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = ROOT / "apps" / "node" / "app" / "main.py"

CORE_CALLERS = ("_post_complete", "_report_failure", "_send_heartbeat",
                "_fetch_my_assignments")


def _tree() -> ast.Module:
    return ast.parse(NODE.read_text(encoding="utf-8"))


def _func(name: str) -> ast.FunctionDef:
    for node in ast.walk(_tree()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node  # type: ignore[return-value]
    raise AssertionError(f"{name} 을 못 찾았다")


def _swallows(fn: ast.AST) -> list[str]:
    """본문이 `pass`/`return` 뿐인 `except` — 예외를 지운다."""
    out = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if all(isinstance(s, (ast.Pass, ast.Return)) for s in node.body):
            out.append(f"L{node.lineno}")
    return out


class TestExecuteCannotReturnWithoutCore(unittest.TestCase):
    def test_the_response_carries_the_core_reply(self) -> None:
        """**여기가 핵심이다.** Core 의 답이 응답에 실리면 왕복 없이는 못 돌아온다."""
        body = NODE.read_text(encoding="utf-8")
        self.assertTrue('"core": reported' in body,
                        "execute 응답이 Core 의 답을 안 싣는다 — 로컬만으로 끝날 수 있다")
        self.assertTrue("reported = _post_complete(" in body,
                        "execute 가 _post_complete 를 안 부른다")

    def test_post_complete_does_not_swallow(self) -> None:
        """삼키면 그 자리에서 「됐다」가 된다."""
        self.assertEqual([], _swallows(_func("_post_complete")),
                         "_post_complete 가 예외를 삼킨다")

    def test_post_complete_raises_on_http_error(self) -> None:
        src = ast.unparse(_func("_post_complete"))
        self.assertIn("HTTPError", src)
        self.assertIn("raise HTTPException", src)


class TestOnlyTheReporterMaySwallow(unittest.TestCase):
    """삼키는 것과 **성공으로 끝내는 것**은 다르다."""

    def test_the_reporter_says_why_it_swallows(self) -> None:
        doc = ast.get_docstring(_func("_report_failure")) or ""
        # 「lease 만료」만 보면 **앞 문단에도 있어서** 이유가 지워져도 통과한다
        # (뮤테이션에서 실제로 통과했다). 삼킴을 해명하는 그 문장을 본다.
        reason = "보고 자체가 실패해도 삼킨다"
        self.assertTrue(reason in doc,
                        f"_report_failure 가 삼키는 이유가 안 적혀 있다: «{reason}»")

    def test_no_other_core_caller_swallows_silently(self) -> None:
        bad = []
        for name in CORE_CALLERS:
            if name == "_report_failure":
                continue
            for where in _swallows(_func(name)):
                bad.append(f"{name}:{where}")
        # `_fetch_my_assignments` 는 `return []` 앞에 `_note_core_error` 를 부른다 (#207).
        for name in ("_send_heartbeat", "_fetch_my_assignments"):
            with self.subTest(function=name):
                self.assertIn("_note_core_error", ast.unparse(_func(name)),
                              f"{name} 이 단절을 기록하지 않는다 (#207 이 세운 것)")
        self.assertEqual([], bad, f"Core 호출이 조용히 삼킨다: {bad}")

    def test_suppress_is_only_for_cleanup_and_the_reporter(self) -> None:
        """`contextlib.suppress` 가 Core 호출을 덮으면 성공으로 끝날 수 있다."""
        bad = []
        for node in ast.walk(_tree()):
            if not isinstance(node, ast.With):
                continue
            heads = [ast.unparse(i.context_expr) for i in node.items]
            if not any("suppress" in h for h in heads):
                continue
            inner = ast.unparse(node)
            if "OSError" in " ".join(heads):
                continue                      # 파일 정리 — Core 와 무관
            if "_report_failure" in inner:
                continue                      # 위 검사가 이유를 지킨다
            bad.append(f"L{node.lineno}: {' '.join(heads)}")
        self.assertEqual([], bad, f"Core 호출을 suppress 로 덮는다: {bad}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_the_core_callers_all_exist(self) -> None:
        for name in CORE_CALLERS:
            with self.subTest(function=name):
                self.assertIsNotNone(_func(name))

    def test_the_swallow_detector_works(self) -> None:
        fn = ast.parse("def f():\n    try:\n        g()\n    except Exception:\n        pass\n").body[0]
        self.assertTrue(_swallows(fn))
        ok = ast.parse("def f():\n    try:\n        g()\n    except Exception as e:\n        raise X from e\n").body[0]
        self.assertEqual([], _swallows(ok))

    def test_enough_suppress_sites_are_seen(self) -> None:
        n = sum(1 for node in ast.walk(_tree()) if isinstance(node, ast.With)
                and any("suppress" in ast.unparse(i.context_expr) for i in node.items))
        self.assertGreaterEqual(n, 3, f"suppress 자리 {n}곳만 봤다")


if __name__ == "__main__":
    unittest.main()
