r"""「상태확인」 절차 S0–S7 — 정본(`queue-batches.md` §1)과 그것을 부르는 문서들이 같은가 (배치 D #156).

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `queue-batches.md` §1 의 단계 | S0 … S7 — 여덟, 번호 연속 |
| S5 가 읽으라는 파일 | 전부 실재 (`queue-batches` · `queue-expansion` · `autonomous-mode` · handoff · inbox 둘 · `CLAUDE.md`) |
| `handoff-long-mode-claude.md` · `autonomous-mode.md` | 「S0–S7」로 §1 을 가리킨다 (자기 절차를 따로 적지 않는다) |

## 재현

```bash
python3 -m unittest tests.test_status_check_steps_agree
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "docs" / "bridge"
QUEUE = BRIDGE / "queue-batches.md"
CALLERS = (BRIDGE / "handoff-long-mode-claude.md", BRIDGE / "autonomous-mode.md")
S5_FILES = ("queue-batches.md", "queue-expansion", "autonomous-mode", "handoff", "inbox-claude", "inbox-cursor", "CLAUDE.md")


def _steps() -> list[int]:
    text = QUEUE.read_text(encoding="utf-8")
    sec = text[text.index("## 1."):text.index("## 2.")]
    return [int(n) for n in re.findall(r"^S(\d)\.", sec, re.M)]


class TestStepsAgree(unittest.TestCase):
    def test_eight_contiguous_steps(self) -> None:
        self.assertEqual(list(range(8)), _steps())

    def test_s5_names_files_that_exist(self) -> None:
        text = QUEUE.read_text(encoding="utf-8")
        sec = text[text.index("## 1."):text.index("## 2.")]
        s5 = sec[sec.index("S5."):sec.index("S6.")]
        for name in S5_FILES:
            with self.subTest(name=name):
                self.assertIn(name, s5, f"S5 가 {name} 을 안 읽는다")
        self.assertTrue((ROOT / "CLAUDE.md").is_file())
        for f in ("queue-batches.md", "queue-expansion.md", "autonomous-mode.md", "handoff-long-mode-claude.md", "inbox-claude.md", "inbox-cursor.md"):
            self.assertTrue((BRIDGE / f).is_file(), f)

    def test_callers_point_at_the_canonical_steps(self) -> None:
        for c in CALLERS:
            with self.subTest(doc=c.name):
                body = c.read_text(encoding="utf-8")
                self.assertRegex(body, r"S0[–\-~]S7")
                self.assertNotRegex(body, r"(?m)^S[0-7]\. ", "부르는 문서가 자기 절차를 따로 적는다 — 정본이 둘이 된다")   # (?m): 머지 직후 뮤테이션이 안 울어 고침


if __name__ == "__main__":
    unittest.main()
