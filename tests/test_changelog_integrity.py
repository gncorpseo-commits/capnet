"""`CHANGELOG.md` 가 머지에서 다치지 않았는가.

## 왜 있는가

**실제로 다쳤다 (2026-09-01).** 야간에 PR 다섯을 동시에 열었고, 코드 PR 마다 `CHANGELOG`
최상단에 항목이 들어가서 **셋이 충돌**했다. 충돌을 「둘 다 남긴다」로 풀다가

- 파일 **중간에 두 번째 `# Changelog` 헤더**가 생기고
- 그 아래로 Wave M·N·O 가 **통째로 되풀이**됐다 (159줄)

`run_tests` 도 `check_submission` 도 **아무것도 걸리지 않았다** — 아무도 이 파일의
**모양**을 보지 않았기 때문이다. 문서가 두 배로 늘어나도 조용하다.

## 무엇을 보나

`CHANGELOG` 는 **버전 이력의 정본**이다(`CLAUDE.md`). 정본이 조용히 중복되면 「무엇이
언제 들어갔나」를 못 읽는다. 그래서 **모양만** 본다 — 내용은 사람이 쓴다.

1. `# Changelog` 헤더가 **하나**뿐인가
2. `## ` 항목 제목이 **겹치지 않는가**
3. 맨 위가 `# Changelog` 인가 (앞에 딴 것이 붙지 않았는가)

## 왜 「최신이 위」를 검사하지 않나

날짜 역순을 강제하면 **같은 날 여러 항목**의 순서까지 검사가 정하게 된다. 그건 사람이
읽기 좋게 두는 편이 낫고, 이번에 다친 것도 순서가 아니라 **중복**이었다.
**다친 것만 본다.**
"""

from __future__ import annotations

import collections
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "docs" / "history" / "CHANGELOG.md"


class TestChangelogShape(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = CHANGELOG.read_text(encoding="utf-8").split("\n")

    def test_one_top_header(self) -> None:
        """머지가 파일 중간에 두 번째 `# Changelog` 를 만든 적이 있다."""
        n = sum(1 for line in self.lines if line.strip() == "# Changelog")
        self.assertEqual(n, 1, f"`# Changelog` 헤더가 {n}개 — 머지 사고를 의심한다")

    def test_starts_with_the_header(self) -> None:
        self.assertEqual(self.lines[0].strip(), "# Changelog", self.lines[0])

    def test_no_duplicate_entry_titles(self) -> None:
        """같은 제목이 두 번 있으면 **충돌을 잘못 푼 것**이다."""
        titles = [line for line in self.lines if line.startswith("## ")]
        dupes = sorted({t for t, n in collections.Counter(titles).items() if n > 1})
        self.assertEqual(dupes, [], f"중복된 항목 {len(dupes)}개: {dupes[:3]}")

    def test_probe_actually_finds_entries(self) -> None:
        """0개를 세며 통과하는 상태를 막는다."""
        titles = [line for line in self.lines if line.startswith("## ")]
        self.assertGreater(len(titles), 50, len(titles))


if __name__ == "__main__":
    unittest.main()
