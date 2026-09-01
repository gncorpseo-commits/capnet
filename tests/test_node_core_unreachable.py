"""Core 에 못 닿는 Node 가 **한가한 Node 처럼 보이지 않는가**.

## 왜 있는가

**실측 (2026-09-02).** `apps/node/app/main.py` 의 두 자리가 모든 예외를 삼켰다:

    def _fetch_my_assignments():
        try:  ...
        except Exception:
            return []          # ← 「일이 없다」와 **같은 값**이다

    def _send_heartbeat(...):
        try:  ...
        except Exception:
            pass

그래서 **Core 가 죽어도 Node 는 1초마다 한가한 척 돌기만 했다.** 바깥 루프의
`node: poll error` 도 안 뜬다 — 안에서 이미 삼켰기 때문이다.

운영에서 이 둘은 완전히 다른 상태다: 「할 일이 없다」와 「Core 와 끊겼다」.
로그가 같으면 **끊긴 것을 아무도 모른다.**

## 왜 「매번 찍기」가 답이 아닌가

폴링이 **1초 주기**다 (`NODE_POLL_INTERVAL_S` 기본 1.0). 실패마다 찍으면 로그가 잠기고,
그러면 사람이 로그를 끈다. **상태가 바뀔 때만** 알린다 — 끊길 때 한 줄, 돌아올 때 한 줄
(얼마나 오래 · 몇 번 실패했는지 함께).

끊긴 곳마다 **따로 센다** — 하트비트만 죽고 배정 조회는 되는 경우가 있다.

## 실측으로 확인한 것 (`docker compose stop core` → `start core`)

```text
node: Core 와 통신 실패 (assignments): URLError: <urlopen error ...>
node: Core 와 통신 실패 (heartbeat): URLError: <urlopen error ...>
node: Core 복구됨 (heartbeat) — 14초 동안 2회 실패
node: Core 복구됨 (assignments) — 19초 동안 3회 실패
```

**총 4줄.** 반복 스팸 없음.

## 무엇을 보나

소스에서 본다 — 이 검사가 도는 환경에는 Node 런타임이 없다.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"


def handler_bodies(func_name: str) -> list[str]:
    """함수 안 `except` 블록들의 소스."""
    tree = ast.parse(NODE_MAIN.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return [
                ast.unparse(h)
                for h in ast.walk(node)
                if isinstance(h, ast.ExceptHandler)
            ]
    raise AssertionError(f"{func_name} 을 못 찾았다 — 이름이 바뀌었으면 검사를 따라 고친다")


class TestUnreachableCoreIsReported(unittest.TestCase):
    def setUp(self) -> None:
        self.text = NODE_MAIN.read_text(encoding="utf-8")

    def test_fetch_does_not_swallow_silently(self) -> None:
        """`[]` 만 돌려주면 「일이 없다」와 구별되지 않는다."""
        for body in handler_bodies("_fetch_my_assignments"):
            self.assertIn("_note_core_error", body, "배정 조회 실패가 조용하다")

    def test_heartbeat_does_not_swallow_silently(self) -> None:
        for body in handler_bodies("_send_heartbeat"):
            self.assertIn("_note_core_error", body, "하트비트 실패가 조용하다")

    def test_reports_on_change_not_every_poll(self) -> None:
        """1초 주기다. 매번 찍으면 로그가 잠기고, 그러면 로그를 끄게 된다."""
        self.assertIn("_core_trouble", self.text, "상태를 안 들고 있다 — 매번 찍게 된다")
        self.assertIn("def _note_core_ok", self.text, "복구를 안 알린다")

    def test_counts_each_endpoint_separately(self) -> None:
        """하트비트만 죽고 배정 조회는 되는 경우가 있다 — 합치면 그걸 못 본다."""
        self.assertIn('_note_core_error("heartbeat"', self.text)
        self.assertIn('_note_core_error("assignments"', self.text)

    def test_recovery_says_how_long_and_how_many(self) -> None:
        """「복구됨」만으로는 얼마나 나빴는지 모른다."""
        block = self.text[self.text.index("def _note_core_ok"):][:600]
        self.assertIn("count", block)
        self.assertRegex(block, r"since|초", "얼마나 걸렸는지 안 적는다")

    def test_probe_actually_reads_the_module(self) -> None:
        self.assertGreater(len(self.text), 5000)
        self.assertGreater(len(re.findall(r"print\(", self.text)), 3)


if __name__ == "__main__":
    unittest.main()
