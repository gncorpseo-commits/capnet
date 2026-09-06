r"""`queue-batches.md` §0 의 **활성 배치**와 `STATE.md` 의 첫 「다음:」이 같은 배치를 말하는가 (배치 D #155).

## 왜 있는가

두 파일은 역할이 다르다 — 큐 정본은 `queue-batches`, 세션 상태는 `STATE`. Step 0 마다 둘을 같이 고치는데, 하나만 고치면
다음 세션이 「상태확인」에서 엇갈린 배치를 읽는다.

## 실측 (2026-09-06)

| 어디 | 값 |
|---|---|
| `queue-batches.md` §0 「활성 — 지금 여기」 행 | 배치 한 글자 (A–D) 또는 「최종」 |
| `STATE.md` 「지금 어디인가」의 **첫** 「다음:」 줄 | 같은 글자를 말한다 |

## 재현

```bash
python3 -m unittest tests.test_active_batch_agrees_with_state
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "docs" / "bridge" / "queue-batches.md"
STATE = ROOT / "STATE.md"


def _active_letter() -> str:
    """배치 글자(A–D) 또는 「최종」 — 시드가 끝나면 §7 최종이 활성 행이다 (배치 D Step 0 에서 넓혔다)."""
    rows = re.findall(r"^\| \**(?:배치 ([A-D])|(최종))\** \| [^|]+\| \**활성 — 지금 여기", QUEUE.read_text(encoding="utf-8"), re.M)
    assert len(rows) == 1, rows
    letter, final = rows[0]
    return letter or final


def _state_next() -> str:
    text = STATE.read_text(encoding="utf-8")
    body = text[text.index("## 지금 어디인가"):]
    m = re.search(r"\*\*다음:\*\*([^\n]*)", body)
    assert m, "STATE 에 「다음:」이 없다"
    return m.group(1)


class TestTheyAgree(unittest.TestCase):
    def test_state_next_names_the_active_batch(self) -> None:
        letter = _active_letter()
        nxt = _state_next()
        needle = "최종" if letter == "최종" else f"배치 {letter}"
        self.assertIn(needle, nxt, f"STATE 의 다음 「{nxt.strip()[:60]}」 이 활성 {needle} 을 말하지 않는다")


if __name__ == "__main__":
    unittest.main()
