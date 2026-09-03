"""카탈로그 「구현됨」이 **실제로 등록되는 길을 갖는가** (큐 #27).

## 왜 있는가

`test_report_claims` 는 **원고가 부른 능력**이 카탈로그에서 「구현됨」인지 본다.
그 반대 방향은 아무도 안 봤다 — **카탈로그가 「구현됨」이라고 적은 능력이
실제로 등록되는 길이 있는가.**

길이 없으면 그 능력은 **문서에만 있다.** 심사위원이 재현하면 `GET /v1/capabilities`
에 안 나오고, 그때 다른 아홉의 신뢰도까지 같이 떨어진다.

전수했다 (2026-09-03). **오늘 빠진 것은 없다** — 그래서 이 검사를 만든다
(7회차 #192–#196 과 같은 자리: 「오늘 0 · 지키는 것이 없어서 → 검사」).

| 능력 | 등록 경로 |
|---|---|
| `image.classify` | `call.sh` · `seed.sql` |
| `image.embed` | `image_embed_demo.sh` |
| `text.classify` | `text_demo.sh` |
| `text.extract` | `text_extract_demo.sh` |
| `text.ner` | `ner_demo.sh` · `product_demo.sh` |
| `text.embed` | `embed_demo.sh` |
| `text.rank` | `text_rank_demo.sh` |
| `table.extract` | `table_demo.sh` |
| `timeseries.forecast` | `series_demo.sh` |
| `safety.pii` | `pii_demo.sh` |

## 무엇을 고정하나

「구현됨」으로 적힌 능력은 **`scripts/` 의 데모 또는 `seed.sql` 에 이름이 나와야 한다.**
카탈로그에 줄을 더하면서 길을 안 만들면 걸린다.

## 무엇을 고정하지 **않나**

- **개수** (`10`). 자라는 값이라 못박으면 사람이 숫자만 고친다 (`test_doc_counts` 규율).
  `test_report_claims` 가 원고와의 관계를 이미 본다
- 「구현됨이 **아닌**」 줄. 선언만 있는 능력은 정상이다 (D27 `retrieve.*` 가 그 예다)
- 그 데모가 **실제로 도는지** — Docker 가 필요하다. 여기서 보는 것은 **길의 존재**다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "spec" / "capability-catalog.md"
SEED = ROOT / "apps" / "core" / "sql" / "seed.sql"
SCRIPTS = ROOT / "scripts"

_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*`([a-z][a-z0-9_.]*)`\s*\|\s*[a-z]+\s*\|\s*`\w+`\s*\|"
    r"\s*\*{0,2}(?:golden|none)\*{0,2}\s*\|\s*(.+?)\s*\|$"
)


def _implemented() -> list[str]:
    out: list[str] = []
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        m = _ROW.match(line.strip())
        if m and "구현됨" in m.group(2):
            out.append(m.group(1))
    return out


def _paths_for(code: str) -> list[str]:
    """그 능력의 이름을 **문자열로** 들고 있는 등록 경로들."""
    quoted = re.compile(rf"""["']{re.escape(code)}["']""")
    found = [p.name for p in sorted(SCRIPTS.glob("*.sh"))
             if quoted.search(p.read_text(encoding="utf-8", errors="replace"))]
    if quoted.search(SEED.read_text(encoding="utf-8")):
        found.append("seed.sql")
    return found


class TestEveryImplementedCapabilityIsReachable(unittest.TestCase):
    def test_each_has_a_registration_path(self) -> None:
        """**여기가 핵심이다.** 길이 없으면 그 능력은 문서에만 있다."""
        orphans = [c for c in _implemented() if not _paths_for(c)]
        self.assertEqual(
            [], orphans,
            "카탈로그가 「구현됨」이라 적었는데 등록하는 길이 없다 — "
            f"`scripts/` 데모나 `seed.sql` 에 넣는다: {orphans}",
        )


class TestProbeActuallyReads(unittest.TestCase):
    """훑기가 0개를 훑으며 통과하지 않는가."""

    def test_catalog_rows_are_parsed(self) -> None:
        impl = _implemented()
        self.assertGreater(len(impl), 5,
                           f"카탈로그에서 「구현됨」을 {len(impl)}개밖에 못 읽었다 — 표 모양이 바뀌었다")

    def test_scripts_are_readable(self) -> None:
        self.assertGreater(len(list(SCRIPTS.glob("*.sh"))), 15, "데모 스크립트를 못 찾았다")

    def test_lookup_discriminates(self) -> None:
        """찾기가 **아무거나 참**이면 위 검사가 헛돈다."""
        self.assertEqual([], _paths_for("nope.nothing"),
                         "없는 능력에도 등록 경로가 있다고 한다")
        self.assertTrue(_paths_for(_implemented()[0]), "있는 능력의 경로를 못 찾는다")


if __name__ == "__main__":
    unittest.main()
