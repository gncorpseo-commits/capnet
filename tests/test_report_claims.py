"""보고서가 주장하는 것이 실물과 맞는가 (출품 트랙 · 1차는 서면으로 갈린다).

## 왜 있는가

원고 §주요기능 1-1) 이 **「능력 5종이 같은 사슬을 통과했다」**고 주장한다.
그 주장은 저장소 실물로 뒷받침돼야 한다 — 심사위원이 재현하면 바로 드러난다.

**주장과 실물이 갈리는 방향은 둘이다.**

1. 능력을 더 구현했는데 원고가 「5종」에 머문다 → 과소 주장. 손해지만 거짓은 아니다
2. **원고가 말한 능력의 데모가 없다** → 재현 불가. 이건 거짓이 된다

여기서 막는 것은 **2번**이다. 1번은 사람이 판단할 일이라 강제하지 않는다.

## 무엇을 고정하나

- 원고가 이름을 부른 능력은 **카탈로그에서 구현됨**이어야 한다
- 원고가 「재현된다」고 적은 데모 스크립트는 **실재**해야 한다
- 품질을 주장하지 않는다고 적었으면, 그 능력들이 실제로 `quality_profile='none'` 이어야 한다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "docs" / "ops" / "contest-report-form-draft.md"
DETAIL = ROOT / "docs" / "ops" / "contest-report-draft.md"
CATALOG = ROOT / "docs" / "spec" / "capability-catalog.md"

# 원고가 1-1) 에서 이름을 부르는 능력들.
CLAIMED = (
    "image.classify", "text.classify", "image.embed", "text.embed",
    "timeseries.forecast", "table.extract",
)

_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*`([a-z][a-z0-9_.]*)`\s*\|\s*[a-z]+\s*\|\s*`\w+`\s*\|"
    r"\s*\*{0,2}(golden|none)\*{0,2}\s*\|\s*(.+?)\s*\|$"
)


def _catalog_rows() -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        m = _ROW.match(line.strip())
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


class TestClaimedCapabilitiesExist(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = _catalog_rows()

    def test_all_claimed_are_marked_implemented(self) -> None:
        for code in CLAIMED:
            self.assertIn(code, self.rows, f"{code} 가 카탈로그에 없다")
            self.assertIn("구현됨", self.rows[code][1],
                          f"원고가 {code} 를 주장하는데 카탈로그는 구현됨이 아니다")

    def test_claim_count_matches_catalog(self) -> None:
        """원고의 「5종」과 카탈로그의 구현됨 개수가 같아야 한다."""
        implemented = [c for c, (_, gen) in self.rows.items() if "구현됨" in gen]
        self.assertEqual(
            sorted(implemented), sorted(CLAIMED),
            "구현된 능력 목록이 원고 주장과 다르다 — 원고를 갱신하거나 이 목록을 고친다",
        )
        for draft in (FORM, DETAIL):
            self.assertIn("6종", draft.read_text(encoding="utf-8"),
                          f"{draft.name} 이 「6종」이라고 적지 않았다")

    def test_only_one_claims_quality(self) -> None:
        """「다섯 중 넷은 품질을 주장하지 않는다」가 사실인가."""
        golden = [c for c in CLAIMED if self.rows[c][0] == "golden"]
        self.assertEqual(golden, ["image.classify"],
                         "품질 프로파일을 쓰는 능력이 image.classify 하나가 아니다")
        for draft in (FORM, DETAIL):
            self.assertIn("다섯은 품질을 주장하지 않는다", draft.read_text(encoding="utf-8"))


class TestClaimIsReproducible(unittest.TestCase):
    """원고가 「재현된다」고 적었으면 그 명령이 실재해야 한다."""

    DEMOS = ("text_demo", "embed_demo", "series_demo", "image_embed_demo", "table_demo")

    def test_demo_scripts_exist(self) -> None:
        for d in self.DEMOS:
            self.assertTrue((ROOT / "scripts" / f"{d}.sh").is_file(), f"{d}.sh 가 없다")

    def test_drafts_name_the_scripts(self) -> None:
        for draft in (FORM, DETAIL):
            text = draft.read_text(encoding="utf-8")
            for d in self.DEMOS:
                self.assertIn(f"{d}.sh", text, f"{draft.name} 이 {d}.sh 를 적지 않았다")

    def test_drafts_do_not_promise_powershell(self) -> None:
        """넷은 `.ps1` 이 없다. 원고가 「Windows는 동명 .ps1」을 이 넷에 걸면 거짓이 된다."""
        for d in self.DEMOS:
            self.assertFalse((ROOT / "scripts" / f"{d}.ps1").exists())
        self.assertIn("`bash` 전용", FORM.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
