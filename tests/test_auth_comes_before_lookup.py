r"""**인증이 조회보다 먼저 오는가** (큐 #64 · `#223` 일반화).

## 왜 있는가

`#223` 은 `prod_room` 이 두 라우트에서 **401 이 아니라 422** 를 받고 있던 것을 잡았다.
구멍이 아니라 **검사가 인증에 닿지 못한** 것이었다 — FastAPI 가 핸들러 본문보다 먼저
파라미터를 검증했기 때문이다.

그 사건을 **규칙 두 줄**로 일반화한다.

### 규칙 1 — 인증 헬퍼가 `get_conn()` 보다 먼저 온다

조회를 먼저 하면 무인증 요청이 **404** 로 끝난다. 401 과 404 는 다른 말이다:

- **401** 「너는 누구인지 모르겠다」 — 그 id 가 있는지 **말하지 않는다**
- **404** 「그런 건 없다」 — 이미 **DB 를 봤다**는 뜻이고, 존재 여부가 샌다

`GET /v1/tasks/{task_id}` 는 소유자가 아니면 404 를 준다 — **403 은 「그 id 는 존재한다」를
흘리기 때문**이다(핸들러 주석). 그 설계가 성립하려면 **인증이 먼저**여야 한다.

### 규칙 2 — 경로 파라미터는 파싱되는 타입이다

`prod_room` §14 는 존재하지 않는 더미 id 로 누른다. 그 더미가 **파싱 안 되면 422** 고,
그 절은 다시 **인증을 재지 못한다.** 오늘 경로 파라미터는 **19건 전부 `uuid.UUID`** 라
더미 UUID 하나로 전부 인증까지 닿는다.

## 실측 (2026-09-05)

| 무엇 | 수 |
|---|---|
| 인증 헬퍼를 부르는 라우트 | **40** |
| 그중 **조회가 인증보다 먼저** | **0** ✅ |
| 경로 파라미터를 받는 인증 라우트 | **19** |
| 파라미터 타입이 `uuid.UUID` 인 것 | **19** — 전부 ✅ |
| 이 순서를 세던 검사 | **0** |

**오늘은 0 이다.** 나기 전에 막는다 — `test_integration_runner` 가 같은 이유로 섰다.

## 무엇을 안 보나

- **응답 코드를 여기서 재지 않는다.** 실제 401 은 `prod_room` §13·§14 가 강제 모드에서
  잰다 (Docker 필요). 여기는 **소스의 순서**만 본다
- `get_conn` 을 안 쓰는 조회 경로(캐시·상수). 오늘 그런 인증 라우트는 없다
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "scripts" / "prod_room.sh"

sys.path.insert(0, str(ROOT / "tests"))
from test_every_route_declares_its_auth import AUTH_HELPERS, MAIN  # noqa: E402

# DB 로 들어가는 문. 이 저장소의 모든 핸들러는 여기를 지난다.
DB_DOOR = "get_conn"
PATH_PARAM = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


def _authenticated_routes() -> list[tuple[str, str, ast.FunctionDef]]:
    """`(verb, path, 함수)` — 인증 헬퍼를 부르는 라우트만."""
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    out = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in fn.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if not (isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app"):
                continue
            if dec.func.attr not in ("get", "post", "put", "patch", "delete"):
                continue
            if not _first_call(fn, AUTH_HELPERS):
                break
            path = dec.args[0].value if dec.args else "?"
            out.append((dec.func.attr.upper(), str(path), fn))
            break
    return out


def _first_call(fn: ast.AST, names: frozenset[str] | set[str]) -> int | None:
    lines = [n.lineno for n in ast.walk(fn)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in names]
    return min(lines) if lines else None


def _param_type(fn: ast.FunctionDef, name: str) -> str | None:
    for arg in fn.args.args + fn.args.kwonlyargs:
        if arg.arg == name and arg.annotation is not None:
            return ast.unparse(arg.annotation)
    return None


class TestAuthRunsFirst(unittest.TestCase):
    def test_no_route_looks_up_before_authenticating(self) -> None:
        """**여기가 핵심이다.** 조회가 먼저면 무인증이 404 로 끝나고 존재 여부가 샌다."""
        routes = _authenticated_routes()
        self.assertTrue(routes, "인증 라우트를 하나도 못 찾았다 — 추출기가 죽었다")
        bad = []
        for verb, path, fn in routes:
            auth = _first_call(fn, AUTH_HELPERS)
            door = _first_call(fn, {DB_DOOR})
            if auth is not None and door is not None and door < auth:
                bad.append(f"{verb} {path} ({fn.name}): {DB_DOOR} L{door} < 인증 L{auth}")
        self.assertEqual([], bad, "조회가 인증보다 먼저다: " + "; ".join(bad))


class TestPathParamsAlwaysParse(unittest.TestCase):
    """파싱 안 되는 더미는 **422** 라 인증을 못 잰다 (`#223` 이 겪은 자리)."""

    def test_every_path_param_is_a_uuid(self) -> None:
        bad = []
        for verb, path, fn in _authenticated_routes():
            for name in PATH_PARAM.findall(path):
                kind = _param_type(fn, name)
                if kind != "uuid.UUID":
                    bad.append(f"{verb} {path}: {name}={kind}")
        self.assertEqual([], bad,
                         "경로 파라미터가 UUID 가 아니다 — prod_room 의 더미로는 422 가 난다: "
                         + "; ".join(bad))

    def test_prod_room_dummy_is_a_real_uuid(self) -> None:
        """더미가 UUID 가 아니면 §14 전체가 인증 대신 **파싱**을 재게 된다."""
        m = re.search(r"^dummy=([0-9a-fA-F-]+)\s*$", PROD.read_text(encoding="utf-8"), re.M)
        self.assertIsNotNone(m, "prod_room 에서 dummy 를 못 찾았다")
        assert m is not None
        uuid.UUID(m.group(1))          # 못 파싱하면 여기서 터진다

    def test_enough_path_routes_are_seen(self) -> None:
        n = sum(1 for _, path, _ in _authenticated_routes() if PATH_PARAM.search(path))
        self.assertGreaterEqual(n, 15, f"경로 파라미터 라우트 {n}개만 봤다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_authenticated_routes_are_seen(self) -> None:
        self.assertGreaterEqual(len(_authenticated_routes()), 35,
                                f"{len(_authenticated_routes())}개만 봤다")

    def test_order_detector_discriminates(self) -> None:
        """순서를 못 읽으면 위 검사가 **공허하게** 통과한다."""
        good = ast.parse("def f():\n    _require('user', a)\n    with get_conn() as c:\n        pass\n").body[0]
        bad = ast.parse("def f():\n    with get_conn() as c:\n        pass\n    _require('user', a)\n").body[0]
        self.assertLess(_first_call(good, AUTH_HELPERS), _first_call(good, {DB_DOOR}))
        self.assertGreater(_first_call(bad, AUTH_HELPERS), _first_call(bad, {DB_DOOR}))


if __name__ == "__main__":
    unittest.main()
