r"""강제 모드 키가 **어디에 어떤 값으로** 있는가 — 커밋된 `.env` 0 · 프로드 오버레이만 `"1"` (배치 D #143).

## 실측 (2026-09-06)

| 어디 | `REQUIRE_API_KEY` | `REQUIRE_NODE_CREDENTIAL` |
|---|---|---|
| `compose.prod.yaml` (제품) | `"1"` | `"1"` |
| `compose.yaml` (데모) | 없음 → 코드 기본 `0` | 없음 → `0` |
| `.env.example` | `0` | `0` |
| 추적된 `.env*` | `.env.example` 하나 — 실제 `.env` **0** |

강제 키는 시크릿이 아니라 토글이다. 문제는 「제품에서 꺼져 있는가」이고, 여기서 프로드 오버레이의 `"1"` 둘을 고정한다.

## 재현

```bash
python3 -m unittest tests.test_enforcement_toggles_live_in_prod_only
```
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

KEYS = ("REQUIRE_API_KEY", "REQUIRE_NODE_CREDENTIAL")


def _value(body: str, key: str) -> str | None:
    m = re.search(rf"^\s*{key}[:=]\s*\"?([^\"\s]*)\"?", body, re.M)
    return m.group(1) if m else None


class TestTogglesAreWhereTheyShouldBe(unittest.TestCase):
    def test_prod_overlay_forces_both(self) -> None:
        body = hash_comment_free(ROOT / "compose.prod.yaml")
        for k in KEYS:
            with self.subTest(key=k):
                self.assertEqual("1", _value(body, k), f"프로드 오버레이가 {k} 를 강제하지 않는다")

    def test_demo_compose_sets_neither(self) -> None:
        body = hash_comment_free(ROOT / "compose.yaml")
        for k in KEYS:
            with self.subTest(key=k):
                self.assertIsNone(_value(body, k), f"데모 compose 가 {k} 를 정한다 — 심사용 기본이 바뀐다")

    def test_env_example_defaults_off_and_no_real_env_is_tracked(self) -> None:
        body = (ROOT / ".env.example").read_text(encoding="utf-8")
        for k in KEYS:
            self.assertEqual("0", _value(body, k), f".env.example 의 {k}")
        tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=ROOT, timeout=60).stdout.splitlines()
        self.assertEqual([".env.example"], [f for f in tracked if f.startswith(".env")], "실제 .env 가 추적된다")


if __name__ == "__main__":
    unittest.main()
