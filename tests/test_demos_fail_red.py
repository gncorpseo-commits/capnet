r"""데모 스크립트가 **실패했는데 초록으로 끝나는 모양이 없는가** (배치 C #126 · 「0건 초록」 계열).

## 실측 (2026-09-06) — 작업을 돌리는 데모 10 (`capreq_demo.sh` 는 자기 판정 13개를 따로 갖는다)

| 모양 | 값 |
|---|---|
| `set -euo pipefail` | 10/10 |
| 폴링 루프 상한 (`for _ in $(seq 1 N)`) | 있는 곳 전부 (product 는 폴링 없음) |
| 최종 판정 `if d["status"] != "COMPLETED": raise SystemExit` | 10/10 |
| `\|\| true` 가 판정·작업 조회 줄에 | **0** — capid 조회(없으면 새로 등록) 에만 |

## 재현

```bash
python3 -m unittest tests.test_demos_fail_red
```
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

DEMOS = sorted(p for p in (ROOT / "scripts").glob("*_demo.sh") if p.name != "capreq_demo.sh")


class TestEveryDemoFailsRed(unittest.TestCase):
    def test_ten_demos(self) -> None:
        self.assertEqual(10, len(DEMOS), [p.name for p in DEMOS])

    def test_errexit_and_pipefail(self) -> None:
        for p in DEMOS:
            with self.subTest(demo=p.name):
                self.assertRegex(hash_comment_free(p), r"(?m)^set -euo pipefail$")

    def test_final_verdict_raises(self) -> None:
        for p in DEMOS:
            with self.subTest(demo=p.name):
                body = hash_comment_free(p)
                self.assertIn('if d["status"] != "COMPLETED":', body, f"{p.name} 이 최종 상태를 판정하지 않는다")
                after = body[body.index('if d["status"] != "COMPLETED":'):]
                self.assertIn("raise SystemExit", after[:200], f"{p.name} 의 판정이 종료하지 않는다")

    def test_poll_loops_are_bounded(self) -> None:
        seen = 0
        for p in DEMOS:
            body = hash_comment_free(p)
            if 'st" == "COMPLETED"' not in body:
                continue
            seen += 1
            with self.subTest(demo=p.name):
                self.assertRegex(body, r"for _ in \$\(seq 1 \d+\); do\s*\n\s*tr=", f"{p.name} 의 폴링에 상한이 없다")
        self.assertEqual(9, seen)

    def test_or_true_never_touches_the_verdict(self) -> None:
        for p in DEMOS:
            with self.subTest(demo=p.name):
                for i, ln in enumerate(hash_comment_free(p).splitlines(), 1):
                    if "|| true" in ln and re.search(r"status|/v1/tasks|SystemExit", ln):
                        self.fail(f"{p.name}:{i} 판정 줄에 || true")


if __name__ == "__main__":
    unittest.main()
