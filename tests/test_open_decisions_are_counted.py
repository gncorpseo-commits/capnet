r"""inbox 의 `expects: decision` **열린 수를 기계가 센다** (배치 D #154 · `#39`/`#222` 계열).

## 왜 있는가

「열린 Decision 스물」 같은 수는 지금까지 사람이 세어 적었다. 세는 법(헤더 블록 · `expects: decision` · `status: open`)을
코드로 두면 다음 Step 0 이 같은 수를 낸다. **status 는 내리지 않는다** — 이 검사는 세기만 한다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| 헤더 블록(`---` … `---`) | 126 |
| `expects: decision` ∧ `status: open` | **23** |

수가 바뀌면(사람이 닫거나 새 Proposal 이 열리면) 아래 상수를 같이 고친다 — 그게 「누가 언제 바꿨나」의 기록이 된다.

## 재현

```bash
python3 -m unittest tests.test_open_decisions_are_counted
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "docs" / "bridge" / "inbox-cursor.md"
OPEN_DECISIONS_TODAY = 23


def _open_decision_topics() -> list[str]:
    text = INBOX.read_text(encoding="utf-8")
    out = []
    for block in re.findall(r"^---\n(from:.*?)\n---", text, re.S | re.M):
        if re.search(r"^expects: decision\s*$", block, re.M) and re.search(r"^status: open\s*$", block, re.M):
            m = re.search(r"^topic: (\S+)", block, re.M)
            out.append(m.group(1) if m else "?")
    return out


class TestTheCountIsMechanical(unittest.TestCase):
    def test_count(self) -> None:
        topics = _open_decision_topics()
        self.assertTrue(topics, "열린 Decision 을 하나도 못 셌다 — 헤더 모양이 바뀌었나")
        self.assertEqual(OPEN_DECISIONS_TODAY, len(topics),
                         f"열린 expects:decision 이 {len(topics)} — 닫혔거나 새로 열렸다. 상수를 같이 고쳐라: {topics}")

    def test_each_has_a_topic(self) -> None:
        self.assertNotIn("?", _open_decision_topics())


if __name__ == "__main__":
    unittest.main()
