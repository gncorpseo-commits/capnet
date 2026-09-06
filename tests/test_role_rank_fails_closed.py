r"""역할 판정이 **닫힌 쪽으로 실패하는가** (배치 C #110 · `#193` 양방향 재전수).

## 왜 있는가

양방향(developer→admin 거절 · admin→user 허용)은 `tests/integration/check_api_key.py` 가 DB 에서,
라우트↔역할은 `test_route_roles_are_pinned` 가 정적으로 본다. 남은 것은 **기본값**이다 —
모르는 역할·오타 난 최소역할이 「아무도 못 함」이 아니라 「아무나 됨」으로 떨어지면 두 검사 사이로 샌다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `ROLE_RANK` | `{"user": 1, "developer": 2, "admin": 3}` — 정확히 셋 |
| 모르는 역할 | `.get(role, 0)` → 어떤 최소역할도 못 넘는다 |
| 모르는 최소역할 (`_require("admn")` 오타) | `.get(minimum, 99)` → 아무도 못 넘는다 (열리지 않고 닫힌다) |
| `_require` 에 적힌 최소역할 리터럴 | 전부 `ROLE_RANK` 의 키 — 오타 0 |
| 키가 있으면 강제 꺼짐이어도 역할을 본다 | `_require` 가 `actor is not None` 이면 무조건 `assert_role` |
| 남의 작업 조회 | `developer` 는 같은 org 만 · org 없는 `admin` 만 전체 (D24) |

## 재현

```bash
python3 -m unittest tests.test_role_rank_fails_closed
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APIKEY = ROOT / "apps" / "core" / "app" / "apikey.py"
MAIN = ROOT / "apps" / "core" / "app" / "main.py"


def _role_rank() -> dict[str, int]:
    for node in ast.parse(APIKEY.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "ROLE_RANK":
            return ast.literal_eval(node.value)
    raise AssertionError("ROLE_RANK 를 못 찾았다")


class TestDefaultsAreClosed(unittest.TestCase):
    def test_rank_is_exactly_three(self) -> None:
        self.assertEqual({"user": 1, "developer": 2, "admin": 3}, _role_rank())

    def test_unknown_role_and_unknown_minimum_both_deny(self) -> None:
        src = APIKEY.read_text(encoding="utf-8")
        fn = src[src.index("def assert_role"):]
        fn = fn[:fn.index("\ndef ", 1)]
        self.assertRegex(fn, r'have = ROLE_RANK\.get\(str\(actor\.get\("role"\)\), 0\)')
        self.assertRegex(fn, r"need = ROLE_RANK\.get\(minimum, 99\)")
        self.assertRegex(fn, r"if have < need:\s*\n\s*raise Forbidden")

    def test_every_require_literal_is_a_real_role(self) -> None:
        src = MAIN.read_text(encoding="utf-8")
        used = sorted(set(re.findall(r'_require\("(\w+)"', src)))
        self.assertGreaterEqual(len(re.findall(r'_require\("(\w+)"', src)), 30)
        self.assertEqual([], [u for u in used if u not in _role_rank()], f"ROLE_RANK 에 없는 최소역할: {used}")

    def test_require_checks_the_role_whenever_a_key_is_present(self) -> None:
        src = MAIN.read_text(encoding="utf-8")
        fn = src[src.index("def _require("):]
        fn = fn[:fn.index("\n# ", 1)]
        self.assertIn("if actor is None:\n        return None", fn)
        self.assertIn("assert_role(actor, minimum)", fn)
        self.assertNotIn("REQUIRE_API_KEY", fn, "_require 가 강제 플래그로 역할 검사를 건너뛴다")


class TestOperatorViewIsOrgScoped(unittest.TestCase):
    def test_developer_needs_same_org_and_only_orgless_admin_sees_all(self) -> None:
        src = MAIN.read_text(encoding="utf-8")
        self.assertIn('(rank >= ROLE_RANK["developer"] and same_org)', src)
        self.assertIn('(rank >= ROLE_RANK["admin"] and my_org is None)', src)


if __name__ == "__main__":
    unittest.main()
