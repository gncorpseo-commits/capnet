"""라우트가 요구하는 **역할이 조용히 내려가지 않는가.**

## 왜 있는가

[#192](https://github.com/gncorpseo-commits/capnet/pull/192)는 **「인증을 거치는가」**
만 본다. `_require("admin")` 을 `_require("developer")` 로 바꿔도 **통과한다** —
여전히 인증 헬퍼를 부르기 때문이다.

그 변이는 **이 저장소가 이미 놓친 적이 있다.** `tests/test_arch_registry.py` 가
그 경위를 적고 있다:

> 고정 길이로 자르면 창이 **다음 핸들러까지 넘친다.** 실제로 그래서
> `_require("admin")` 을 `developer` 로 바꾸는 변이를 놓쳤다 — 바로 뒤
> `capabilities_create` 의 `_require("admin")` 이 창 안에 들어와 통과시켰다.

그 뒤로도 **개별 엔드포인트 검사 몇 개**만 역할을 못박는다
(`/v1/arches` · `PATCH /v1/capabilities/{id}`). **나머지 서른 몇 개는 아무도 안 본다.**

## 실측 (2026-09-02 · `ast` 전수)

| 등급 | 수 | 무엇 |
|---|---|---|
| `admin` | **15** | 신원·증서·초대·계약·정책 — **만들거나 지우는 것** |
| `developer` | **14** | Agent 등록·게이트런·운영 조회 |
| `user` | **4** | 제품 경로 — 입력 올리기, 작업 만들기·보기 |
| Node 증서 | **6** | `/v1/internal/…` (역할이 아니라 기기 신원) |
| 초대 토큰 | **1** | `POST /v1/nodes/redeem` |
| 공개 | **6** | #192 의 `PUBLIC` 이 근거와 함께 갖는다 |

**오늘 어긋난 곳은 없다.** 이 검사는 **다음에 내려가지 않게** 하는 것이다.

## 무엇을 고정하나

1. 라우트 → 등급이 **아래 선언과 정확히 같다** (내려가도, 올라가도 걸린다)
2. 선언에 **유령**(실재하지 않는 라우트)이 없다
3. 한 핸들러가 **`_require` 를 두 번 다른 역할로** 부르지 않는다 (모호하다)

## 무엇을 안 보나

**역할이 「맞는지」는 판단하지 않는다.** 그건 정책이고 사람이 정한다
(`docs/context-handoff.md` D24 · read-auth). 여기서 보는 것은
**정해 둔 것에서 말없이 움직이지 않는가** 하나다.

새 라우트를 넣으면 이 검사가 **분류를 요구한다** — #192 의 `PUBLIC` 과 같은 규율이다.
`fastapi` 없이 돌아야 해서 `ast` 로 소스를 읽는다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"

# ── 선언 ────────────────────────────────────────────────────────────────────
#
# `admin` — **신원·증서·계약·정책을 만들거나 지운다.** 되돌리기가 비싸고,
#   잘못 열리면 「누가 내 데이터를 돌릴 수 있나」의 답이 바뀐다.
ADMIN = {
    ("GET", "/v1/api-keys"),
    ("POST", "/v1/arches"),
    ("POST", "/v1/capabilities"),
    ("PATCH", "/v1/capabilities/{capability_id}"),
    ("POST", "/v1/capabilities/{capability_id}/sample"),
    ("POST", "/v1/inputs/{input_id}/purge"),
    ("POST", "/v1/internal/agent-capabilities/revoke"),
    ("POST", "/v1/internal/claim"),
    ("POST", "/v1/nodes"),
    ("GET", "/v1/nodes-credentials"),
    ("GET", "/v1/nodes/invites"),
    ("POST", "/v1/nodes/invites"),
    ("POST", "/v1/nodes/invites/{invite_id}/revoke"),
    ("POST", "/v1/nodes/{node_id}/credentials"),
    ("POST", "/v1/nodes/{node_id}/credentials/revoke"),
}

# `developer` — **Agent 를 올리고 게이트를 돌리고 운영을 본다.** 남의 데이터를
#   읽거나 신원을 바꾸지 않는다. 조회면도 여기 있다 (D24 read-auth — 열지 않는다).
DEVELOPER = {
    ("GET", "/v1/agents"),
    ("POST", "/v1/agents"),
    ("GET", "/v1/agents/{agent_id}"),
    ("POST", "/v1/agents/{agent_id}/bindings"),
    ("GET", "/v1/arches"),
    ("POST", "/v1/internal/gate-runs"),
    ("GET", "/v1/internal/gate-runs/{gate_run_id}"),
    ("POST", "/v1/internal/gate-runs/{gate_run_id}/finish"),
    ("GET", "/v1/nodes"),
    ("GET", "/v1/nodes-liveness"),
    ("GET", "/v1/nodes/{node_id}"),
    ("GET", "/v1/ops/safety"),
    ("GET", "/v1/ops/status"),
    ("GET", "/v1/ops/work-units"),
}

# `user` — **제품 경로.** 입력을 올리고 작업을 만들고 자기 결과를 본다.
USER = {
    ("POST", "/v1/inputs"),
    ("GET", "/v1/inputs/{input_id}"),
    ("POST", "/v1/tasks"),
    ("GET", "/v1/tasks/{task_id}"),
}

DECLARED: dict[tuple[str, str], str] = {
    **{r: "admin" for r in ADMIN},
    **{r: "developer" for r in DEVELOPER},
    **{r: "user" for r in USER},
}


def _routes_with_roles() -> dict[tuple[str, str], list[str]]:
    """`_require(<역할>)` 을 부르는 라우트만 → 그 라우트가 부른 역할들."""
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    out: dict[tuple[str, str], list[str]] = {}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        route = None
        for dec in fn.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if not (isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app"):
                continue
            if dec.func.attr not in ("get", "post", "put", "patch", "delete"):
                continue
            path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else "?"
            route = (dec.func.attr.upper(), str(path))
            break
        if route is None:
            continue
        roles = [
            n.args[0].value
            for n in ast.walk(fn)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "_require"
            and n.args
            and isinstance(n.args[0], ast.Constant)
        ]
        if roles:
            out[route] = roles
    return out


def observed() -> dict[tuple[str, str], str]:
    return {r: roles[0] for r, roles in _routes_with_roles().items()}


class TestRolesMatchTheDeclaration(unittest.TestCase):
    def test_no_role_moved(self) -> None:
        """**여기가 핵심이다.** admin → developer 는 인증 검사(#192)를 통과한다."""
        obs, dec = observed(), DECLARED
        moved = sorted(
            f"{v} {p}: 선언 {dec[(v, p)]} → 실제 {obs[(v, p)]}"
            for (v, p) in set(obs) & set(dec)
            if obs[(v, p)] != dec[(v, p)]
        )
        self.assertEqual(moved, [], f"요구 역할이 선언과 다르다: {moved}")

    def test_no_unclassified_route(self) -> None:
        """새 라우트는 **분류돼야** 한다 — #192 의 `PUBLIC` 과 같은 규율."""
        extra = sorted(f"{v} {p}" for (v, p) in set(observed()) - set(DECLARED))
        self.assertEqual(
            extra, [],
            f"`_require` 를 쓰는데 등급 선언이 없는 라우트 — 위 세 묶음 중 하나에 적는다: {extra}",
        )

    def test_no_ghost_declarations(self) -> None:
        """사라진 라우트가 선언에 남으면 다음 사람이 있는 줄 안다."""
        ghosts = sorted(f"{v} {p}" for (v, p) in set(DECLARED) - set(observed()))
        self.assertEqual(ghosts, [], f"선언에만 있는 라우트: {ghosts}")

    def test_no_ambiguous_handler(self) -> None:
        """한 핸들러가 서로 다른 역할을 두 번 요구하면 무엇이 참인지 모른다."""
        ambiguous = sorted(
            f"{v} {p}: {sorted(set(roles))}"
            for (v, p), roles in _routes_with_roles().items()
            if len(set(roles)) > 1
        )
        self.assertEqual(ambiguous, [], f"역할 요구가 모호하다: {ambiguous}")


class TestDeclarationIsSane(unittest.TestCase):
    def test_three_groups_are_disjoint(self) -> None:
        self.assertEqual(ADMIN & DEVELOPER, set())
        self.assertEqual(ADMIN & USER, set())
        self.assertEqual(DEVELOPER & USER, set())

    def test_probe_actually_found_roles(self) -> None:
        """0개끼리 비교하며 통과하는 상태를 막는다. **개수는 못박지 않는다.**"""
        self.assertGreater(len(observed()), 20, sorted(observed()))
        self.assertGreater(len(ADMIN), 5)
        self.assertGreater(len(DEVELOPER), 5)

    def test_admin_only_ranks_above_developer(self) -> None:
        """등급 이름이 실재해야 한다 — 오타면 `assert_role` 이 `need=99` 로 다 막는다."""
        src = (ROOT / "apps" / "core" / "app" / "apikey.py").read_text(encoding="utf-8")
        for role in ("admin", "developer", "user"):
            with self.subTest(role=role):
                self.assertIn(f'"{role}"', src, f"{role} 가 ROLE_RANK 에 없다")


if __name__ == "__main__":
    unittest.main()
