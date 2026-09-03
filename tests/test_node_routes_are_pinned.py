"""Node 의 라우트가 **닫혀 있는가** — 그리고 `/health` 가 증서를 흘리지 않는가.

## 왜 있는가

[#192](https://github.com/gncorpseo-commits/capnet/pull/192)·
[#193](https://github.com/gncorpseo-commits/capnet/pull/193)이 **Core** 의 라우트
46개를 전수해 못박았다. **Node 는 그 밖이었다.**

Node 는 라우트가 둘뿐이지만(`/health` · `POST /v1/execute`) 열리면 더 나쁘다.
`execute` 의 머리말이 그렇게 적고 있다:

> 이게 없으면 Node에 네트워크로 닿는 **누구나 추론을 시킬 수 있다.**
> Core의 도메인·티어 FK는 assignment 기록을 막지만 Node 직접 호출은 막지 못한다.

> **닫힌 실패.** NODE_ID 가 없으면 배정 여부를 확인할 수단이 없으므로 실행하지 않는다.
> **이전에는 `if NODE_ID and ...` 여서 NODE_ID 미설정 노드가 무방비였다.**

**그 「이전에는」이 실제로 있었던 버그다. 그런데 고친 것을 못박은 검사가 없다.**

## 무엇을 고정하나

1. 모든 Node 라우트가 **가드를 부르거나** 아래 `PUBLIC` 에 근거와 함께 적혀 있다
2. `execute` 는 **`NODE_ID` 가 없으면 실행하지 않는다** (닫힌 실패 · 503)
3. `execute` 는 `_my_assignment` 가 `None` 이면 **403** — 배정 없는 호출을 안 받는다
4. `/health` 는 **증서 값을 안 내보낸다** — `bool(...)` 로 감싼 보유 여부만

## 무엇을 안 보나

**Node 를 띄워서 눌러 보지 않는다** — 이 저장소에는 `fastapi` 가 없는 개발 환경이
있다 (`docs/guide/testing.md` §2). `scripts/prod_room.sh` 가 강제 모드에서 실제로
누르지만 **Docker 가 있어야** 돈다. 여기서는 `ast` 로 **구조**를 본다.

**역할 등급은 없다.** Node 에는 API 키 역할이 없고 Core 가 배정한 lease 가 신원이다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"

# Node 라우트의 가드. `_my_assignment` 는 Core 가 이 Node 에 배정한 lease 인지 본다.
GUARDS = frozenset({"_my_assignment", "_fetch_my_assignments"})

# 공개 라우트 — **왜 공개인지**를 적는다 (Core 쪽 #192 와 같은 규율).
PUBLIC: dict[tuple[str, str], str] = {
    ("GET", "/health"): (
        "살아 있는지·어떤 가중치를 갖고 있는지. 증서는 **보유 여부만** 나간다 — "
        "값도 prefix 도 아니다 (아래 test_health_never_leaks_the_credential)"
    ),
}


def _tree() -> ast.Module:
    return ast.parse(NODE_MAIN.read_text(encoding="utf-8"))


def _handlers() -> dict[tuple[str, str], ast.FunctionDef]:
    out: dict[tuple[str, str], ast.FunctionDef] = {}
    for fn in ast.walk(_tree()):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in fn.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if not (isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app"):
                continue
            if dec.func.attr not in ("get", "post", "put", "patch", "delete"):
                continue
            path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else "?"
            out[(dec.func.attr.upper(), str(path))] = fn
            break
    return out


def _called(fn: ast.AST) -> set[str]:
    return {
        n.func.id for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }


def _raised_status_codes(fn: ast.AST) -> set[int]:
    out: set[int] = set()
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call)):
            continue
        for kw in n.exc.keywords:
            if kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
                out.add(kw.value.value)
    return out


class TestEveryNodeRouteIsClassified(unittest.TestCase):
    def test_no_route_is_silently_open(self) -> None:
        """가드도 없고 `PUBLIC` 에도 없으면 **누구나 부를 수 있다.**"""
        open_routes = [
            f"{v} {p} ({fn.name})"
            for (v, p), fn in _handlers().items()
            if not (_called(fn) & GUARDS) and (v, p) not in PUBLIC
        ]
        self.assertEqual(
            open_routes, [],
            f"가드도 공개 선언도 없는 Node 라우트: {open_routes}",
        )

    def test_no_public_write_routes(self) -> None:
        writes = sorted(f"{v} {p}" for (v, p) in PUBLIC if v != "GET")
        self.assertEqual(writes, [], f"공개 쓰기 라우트: {writes}")

    def test_public_entries_are_real_and_reasoned(self) -> None:
        real = set(_handlers())
        ghosts = sorted(f"{v} {p}" for (v, p) in PUBLIC if (v, p) not in real)
        self.assertEqual(ghosts, [], f"`PUBLIC` 에만 있는 라우트: {ghosts}")
        thin = sorted(f"{v} {p}" for (v, p), why in PUBLIC.items() if len(why.strip()) < 12)
        self.assertEqual(thin, [], f"근거가 비었다: {thin}")

    def test_probe_actually_found_routes(self) -> None:
        self.assertGreaterEqual(len(_handlers()), 2, sorted(_handlers()))


class TestExecuteFailsClosed(unittest.TestCase):
    """**과거에 실제로 열려 있던 자리다** — 머리말이 그 경위를 적고 있다."""

    def setUp(self) -> None:
        self.fn = _handlers()[("POST", "/v1/execute")]

    def test_refuses_when_node_id_is_missing(self) -> None:
        """`if NODE_ID and …` 였을 때 NODE_ID 미설정 노드가 무방비였다."""
        codes = _raised_status_codes(self.fn)
        self.assertIn(503, codes, "NODE_ID 없을 때 거절(503)이 없다 — 열린 실패다")

    def test_refuses_when_not_leased_to_this_node(self) -> None:
        codes = _raised_status_codes(self.fn)
        self.assertIn(403, codes, "배정 없는 호출을 403 으로 막지 않는다")

    def test_asks_core_who_owns_the_assignment(self) -> None:
        self.assertIn("_my_assignment", _called(self.fn), "Core 에 배정을 안 묻는다")

    def test_the_guard_runs_before_the_work(self) -> None:
        """가드가 `_run` 뒤에 있으면 이미 추론한 다음에 거절하는 꼴이다."""
        body = ast.dump(self.fn)
        self.assertLess(
            body.index("_my_assignment"), body.index("'_run'"),
            "_my_assignment 가 _run 보다 뒤에 있다",
        )


class TestHealthDoesNotLeak(unittest.TestCase):
    def setUp(self) -> None:
        self.fn = _handlers()[("GET", "/health")]

    def _returned(self) -> ast.Dict:
        for n in ast.walk(self.fn):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
                return n.value
        raise AssertionError("health 가 dict 를 안 돌려준다 — 이 검사도 고친다")

    def test_health_never_leaks_the_credential(self) -> None:
        """증서는 **보유 여부만** 나간다. 값도 prefix 도 아니다."""
        returned = self._returned()
        # 바닥 — health 가 빈 dict 를 돌려주면 이 검사가 아무것도 안 보고 초록이 된다.
        self.assertTrue(returned.keys, "health 가 아무 칸도 안 돌려준다")
        for key, val in zip(returned.keys, returned.values):
            name = key.value if isinstance(key, ast.Constant) else "?"
            with self.subTest(field=name):
                if isinstance(val, ast.Name) and "CREDENTIAL" in val.id.upper():
                    self.fail(f"health 가 `{val.id}` 를 그대로 내보낸다")
                if isinstance(val, ast.Call) and isinstance(val.func, ast.Name):
                    # `bool(NODE_CREDENTIAL)` 은 허용 — 값이 아니라 유무다.
                    if "CREDENTIAL" in ast.dump(val).upper():
                        self.assertEqual(
                            val.func.id, "bool",
                            f"{name} 이 증서를 `bool()` 없이 가공해 내보낸다",
                        )

    def test_credential_presence_is_still_reported(self) -> None:
        """유무마저 빼면 운영자가 증서 상태를 못 본다 — 지우지 말라는 뜻이다."""
        keys = {k.value for k in self._returned().keys if isinstance(k, ast.Constant)}
        self.assertIn("credential_present", keys)

    def test_probe_actually_read_the_return(self) -> None:
        self.assertGreater(len(self._returned().keys), 3)


if __name__ == "__main__":
    unittest.main()
