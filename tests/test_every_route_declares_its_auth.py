"""Core 의 **모든 라우트**가 인증을 거치거나, 공개라고 **적혀 있는가.**

## 왜 있는가

인증 검사가 **엔드포인트마다 임시로** 붙어 있다 — `test_arch_registry` 가
`POST /v1/arches` 를, `test_capability_patch_wiring` 이 `PATCH /v1/capabilities/{id}`
를 본다. **새 라우트를 인증 없이 넣으면 아무것도 안 걸린다.**

`scripts/prod_room.sh` 가 몇 개를 실제로 눌러 보지만 **Docker 가 있어야** 돌고,
보는 것도 **손으로 고른 여섯 개**다.

실측 (2026-09-02 · `ast` 전수):

| | 수 |
|---|---|
| Core 라우트 | **46** |
| 인증 헬퍼를 부른다 | **40** |
| 공개 | **6** — 전부 `GET`, 전부 아래 `PUBLIC` 에 근거가 적혀 있다 |

**오늘은 새는 곳이 없다.** 이 검사는 **다음에 새지 않게** 하는 것이다 —
[#169](https://github.com/gncorpseo-commits/capnet/pull/169) ·
[#189](https://github.com/gncorpseo-commits/capnet/pull/189) ·
[#191](https://github.com/gncorpseo-commits/capnet/pull/191)과 같은 자리다.

STATE 가 적은 「열린 조회면 15개 중 8개에 역할(공개는 `/health`·카탈로그·allowlist만)」
(2026-08-14 · D24 · read-auth)을 **기계가 잇는다.**

## 무엇을 고정하나

1. 모든 라우트가 **인증 헬퍼를 부르거나** `PUBLIC` 에 **근거와 함께** 적혀 있다
2. **쓰기(POST·PUT·PATCH·DELETE)는 공개가 하나도 없다** — 공개는 전부 조회다
3. `PUBLIC` 에 **없는 라우트**(유령)가 남아 있지 않다

## 무엇을 안 보나

**역할의 높낮이는 안 본다** (`admin` 인지 `developer` 인지). 그건 엔드포인트마다
다르고 이미 개별 검사가 있다 (`test_arch_registry` 의 뮤테이션 교훈 참조).
여기서 보는 것은 **인증을 거치기는 하는가** 하나다.

`fastapi` 없이 돌아야 해서 **`ast` 로 소스를 읽는다.** 데코레이터가 `@app.<verb>(…)`
꼴이 아니게 바뀌면 아래 `test_probe_actually_found_routes` 가 먼저 걸린다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"

# 인증을 실제로 거치게 하는 헬퍼들.
#   `_require`             관리 키 + 역할 (강제가 꺼져 있어도 키가 오면 역할까지 본다)
#   `_actor`               키 해석 (강제 모드면 키 없을 때 401)
#   `_authenticated_node`  Node 증서
#   `_assert_node_matches` Node 증서 + URL 이 주장하는 node_id 대조 (SD-010)
#   `redeem_invite`        초대 토큰 (`node_redeem` 이 `looks_like_invite` 로 먼저 401)
AUTH_HELPERS = frozenset({
    "_require", "_actor", "_authenticated_node", "_assert_node_matches",
    "redeem_invite", "verify_invite", "looks_like_invite",
})

WRITE_VERBS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# 공개 라우트 — **왜 공개인지**를 여기 적는다. 적지 않으면 이 검사가 막는다.
PUBLIC: dict[tuple[str, str], str] = {
    ("GET", "/"): "UI 로 보내는 리다이렉트 — 데이터가 없다",
    ("GET", "/health"): "살아 있는지 묻는 자리. 시크릿·목록을 내지 않는다",
    ("GET", "/openapi.yaml"): "계약 문서 자체 — 저장소에도 같은 파일이 있다",
    ("GET", "/v1/capabilities"): (
        "능력 카탈로그는 공개다 — 제품 입구(capreq)가 **키 없이** 읽어 라우팅한다. "
        "무엇을 할 수 있는지는 숨기는 것이 아니다"
    ),
    ("GET", "/v1/capabilities/{capability_id}"): "위와 같은 카탈로그, 한 건 조회",
    ("GET", "/v1/datasets"): (
        "입력 allowlist — 데모·카탈로그 보조 경로다 (D8′ · 절대규칙 7). "
        "고정 목록이라 기기·작업 정보가 없다"
    ),
}


def _routes() -> list[tuple[str, str, str, set[str]]]:
    """`(verb, path, 핸들러 이름, 그 안에서 부른 이름들)`."""
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    out: list[tuple[str, str, str, set[str]]] = []
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
            path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else "?"
            called = {
                n.func.id for n in ast.walk(fn)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            }
            out.append((dec.func.attr.upper(), str(path), fn.name, called))
            break
    return out


def _authenticated(called: set[str]) -> bool:
    return bool(called & AUTH_HELPERS)


class TestEveryRouteIsClassified(unittest.TestCase):
    def test_no_route_is_silently_public(self) -> None:
        """**여기가 핵심이다.** 인증도 안 하고 `PUBLIC` 에도 없는 라우트는 조용히 열려 있다."""
        undeclared = [
            f"{verb} {path} ({name})"
            for verb, path, name, called in _routes()
            if not _authenticated(called) and (verb, path) not in PUBLIC
        ]
        self.assertEqual(
            undeclared, [],
            "인증도 안 하고 공개 선언도 없는 라우트 — 인증을 붙이거나 "
            f"`PUBLIC` 에 근거와 함께 적는다: {undeclared}",
        )

    def test_no_public_write_routes(self) -> None:
        """공개는 **조회뿐**이다. 쓰기가 공개면 아무나 상태를 바꾼다."""
        writes = sorted(f"{v} {p}" for (v, p) in PUBLIC if v in WRITE_VERBS)
        self.assertEqual(writes, [], f"공개 쓰기 라우트: {writes}")

    def test_public_entries_are_real_routes(self) -> None:
        """유령이 남으면 다음 사람이 「이건 공개였지」로 넘어간다."""
        real = {(v, p) for v, p, _n, _c in _routes()}
        ghosts = sorted(f"{v} {p}" for (v, p) in PUBLIC if (v, p) not in real)
        self.assertEqual(ghosts, [], f"`PUBLIC` 에만 있는 라우트: {ghosts}")

    def test_public_entries_carry_a_reason(self) -> None:
        """근거 없는 공개는 다음에 아무 근거 없이 늘어난다."""
        thin = sorted(f"{v} {p}" for (v, p), why in PUBLIC.items() if len(why.strip()) < 12)
        self.assertEqual(thin, [], f"근거가 비었거나 너무 짧다: {thin}")


class TestProbeActuallyWorks(unittest.TestCase):
    """이 검사가 **0개를 훑으며 통과**하지 않는가."""

    def test_probe_actually_found_routes(self) -> None:
        routes = _routes()
        self.assertGreater(len(routes), 20, f"라우트를 {len(routes)}개밖에 못 찾았다")

    def test_most_routes_are_authenticated(self) -> None:
        """공개가 다수가 되면 이 검사의 뜻이 뒤집힌다. **개수는 못박지 않는다.**"""
        routes = _routes()
        authed = [r for r in routes if _authenticated(r[3])]
        self.assertGreater(
            len(authed), len(routes) // 2,
            f"인증 라우트가 절반 이하다 ({len(authed)}/{len(routes)})",
        )

    def test_auth_helpers_exist_in_source(self) -> None:
        """헬퍼 이름이 바뀌면 이 검사가 **전부 공개로 보게** 된다."""
        src = MAIN.read_text(encoding="utf-8")
        for name in ("_require", "_assert_node_matches"):
            with self.subTest(helper=name):
                self.assertIn(f"def {name}(", src, f"{name} 가 사라졌다 — 이 검사도 고친다")


if __name__ == "__main__":
    unittest.main()
