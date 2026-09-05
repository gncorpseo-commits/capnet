r"""capreq 라우터가 **카탈로그에 없는 것으로 조용히 넘어가지 않는가** (배치 B #92 · `#216` 옆).

## 왜 있는가

LLM 이 지어낸 code 가 실행으로 이어지면 「등록 능력만 라우팅한다」가 무너진다. 실측(2026-09-06):

| 경우 | 동작 |
|---|---|
| 카탈로그에 없는 `code` | `rejected=True` — 실행 안 함 ✅ |
| `code` 는 있고 **버전**이 없음 | 같은 code 의 첫 등록 버전으로 감 — **reason 에 흔적이 없었다** → 이제 `버전 @7 은 카탈로그에 없다 → @1 로 라우팅` 을 남긴다 |
| code 비교 | `c.code != code` **정확 일치** — 대소문자·유사도 폴백 없음 ✅ |

capreq 단위 검사(`capreq/tests/test_router_unit.py`)가 실제로 돌리지만 `httpx` 가 있어야 한다 —
여기서는 **소스**를 본다.

## 재현

```bash
python3 -m unittest tests.test_capreq_router_never_falls_back_silently
PYTHONPATH=capreq/src python3 -m unittest capreq.tests.test_router_unit   # httpx 있는 환경
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "capreq" / "src" / "capreq" / "router.py"
UNIT = ROOT / "capreq" / "tests" / "test_router_unit.py"


def _route_src() -> str:
    src = ROUTER.read_text(encoding="utf-8")
    i = src.index("    def route(")
    return src[i:src.index("    def route_and_maybe_execute(")]


class TestUnknownCodeIsRejected(unittest.TestCase):
    def test_no_match_returns_rejected(self) -> None:
        body = _route_src()
        m = re.search(r"if matched is None:\s*\n\s*return RouteDecision\((.*?)\)", body, re.S)
        self.assertIsNotNone(m, "미등록 code 의 반환을 못 찾았다")
        assert m is not None
        self.assertIn("rejected=True", m.group(1))
        self.assertIn("allowlist에 없음", m.group(1))

    def test_find_matches_code_exactly(self) -> None:
        fn = next(n for n in ast.walk(ast.parse(ROUTER.read_text(encoding="utf-8")))
                  if isinstance(n, ast.FunctionDef) and n.name == "_find")
        src = ast.get_source_segment(ROUTER.read_text(encoding="utf-8"), fn) or ""
        self.assertIn("if c.code != code:", src, "code 비교가 정확 일치가 아니다")
        self.assertNotRegex(src, r"lower\(\)|startswith|in c\.code|difflib", "느슨한 비교가 들어왔다")


class TestVersionFallbackIsSaidOutLoud(unittest.TestCase):
    def test_reason_names_both_versions(self) -> None:
        body = _route_src()
        self.assertIn("matched = _find(caps, code, None)", body, "버전 폴백 자체가 사라졌다 — 표를 고쳐라")
        self.assertRegex(body, r"reason = f\"버전 @\{ver_i\} 은 카탈로그에 없다 → @\{matched\.version\} 로 라우팅",
                         "버전 폴백이 reason 에 남지 않는다")

    def test_unit_suite_exercises_it(self) -> None:
        self.assertIn("def test_version_fallback_is_said_out_loud", UNIT.read_text(encoding="utf-8"))


class TestProbeActuallyReads(unittest.TestCase):
    def test_route_is_found(self) -> None:
        self.assertGreaterEqual(len(_route_src().splitlines()), 40)


if __name__ == "__main__":
    unittest.main()
