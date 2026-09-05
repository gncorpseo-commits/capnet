r"""`acc=`·`f1=` 를 적은 줄 **옆에 재는 도구가 있는가** — §7 이 정한 좁은 검사 (배치 B #98 · `#30` 재전수).

## 왜 있는가

`docs/guide/measured-claims.md` §7 은 「이 규칙 자체는 검사되지 않는다 … 지키지 않는 커밋이 나오면
좁은 검사를 붙인다 — 파일 단위 · `acc=`/`f1=`/홀드아웃 `N/M` 패턴만 · 신규 줄만」이라 했다.
2026-09-03 이후 `STATE.md`·카탈로그에 들어온 측정 숫자 줄을 재전수하니 위반은 **0** 이었다 — 전부
같은 줄이나 바로 옆 줄에 `clean_room.sh`·`demo.sh`·`pass_rate.sh`·`route_bench.py` 가 있다.
그 상태를 §7 의 모양 그대로 고정한다. **넓히지 않는다** — `acc=`·`f1=` 두 패턴, 두 파일, ±2 줄.
(G1 · 2026-09-06: 처음 정규식 `acc=\d` 는 `acc=**0.85**` · `acc = 0.85` 를 못 봤다 — 굵게·띄어쓰기를 허용했다.)

## 재현

```bash
python3 -m unittest tests.test_measured_values_name_their_tool
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (ROOT / "STATE.md", ROOT / "docs" / "spec" / "capability-catalog.md")
# `acc=0.85` 만이 아니라 `acc=**0.85**` · `acc = 0.85` 도 값이다 — G1: 처음 정규식은 이 둘을 못 봤다.
VALUE = re.compile(r"\b(?:acc|f1)\s*=\s*[*`]*\d")
TOOL = re.compile(r"scripts/|\.sh\b|\.py\b|run_tests|check_submission|route_bench|demo_expectation")
WINDOW = 2


def _bare(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for i, ln in enumerate(lines):
        if not VALUE.search(ln):
            continue
        near = "\n".join(lines[max(0, i - WINDOW): i + WINDOW + 1])
        if not TOOL.search(near):
            out.append(f"{path.name}:{i + 1}: {ln.strip()[:80]}")
    return out


class TestEveryAccOrF1HasAToolNearby(unittest.TestCase):
    def test_zero_bare_values(self) -> None:
        seen = sum(len(VALUE.findall(p.read_text(encoding="utf-8"))) for p in FILES)
        self.assertGreaterEqual(seen, 5, f"acc=/f1= 를 {seen}건만 봤다 — 패턴이 눈멀었다")
        bare = [b for p in FILES for b in _bare(p)]
        self.assertEqual([], bare, "재는 도구 없이 적힌 측정값 (measured-claims §2):\n  " + "\n  ".join(bare))

    def test_the_guide_says_this_check_exists(self) -> None:
        guide = (ROOT / "docs" / "guide" / "measured-claims.md").read_text(encoding="utf-8")
        self.assertIn("test_measured_values_name_their_tool", guide, "§7 이 아직 「검사되지 않는다」고 말한다")


if __name__ == "__main__":
    unittest.main()
