"""촬영·심사 문서의 수치가 실물과 맞는가 (출품 트랙).

## 왜 있는가

촬영 런북과 README 가 **내가 늘린 수치를 못 따라왔다.** 실행기를 하나 얹을 때마다
단위 검사가 붙고(68 → 191) 마이그레이션이 늘었는데(17 → 18), 문서는 그대로였다.

심사위원은 README 를 그대로 따라 하고, 촬영 전날은 런북 표로 대조한다.
**숫자가 어긋나면 「고장인가?」로 멈춘다** — 실제로는 정상인데도.

## 무엇을 고정하나

1. **마이그레이션 개수** — 파일 수와 문서 표기가 같아야 한다. 이건 **정확히** 맞아야 한다
2. **촬영에 넣지 않는 데모** — 런북이 그렇게 적었으면 그 근거(각 데모가 스스로
   「주장하지 않는다」를 출력)가 실제로 있어야 한다

## 무엇을 고정하지 **않나**

`run_tests` 개수는 **자라는 값**이다. 정확히 못박으면 실행기를 얹을 때마다 검사가 깨지고,
그러면 사람이 숫자만 고치게 된다 — 검사가 일을 시키는 꼴이다.
대신 런북이 **「숫자가 달라도 이상이 아니다」를 적어 두었는지**만 본다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
RUNBOOK = ROOT / "docs" / "ops" / "shoot-day-runbook.md"

DEMOS = ("text_demo", "embed_demo", "series_demo", "image_embed_demo")


class TestMigrationCount(unittest.TestCase):
    """세대 표기는 **정확히** 맞아야 한다 — 심사위원이 눈으로 대조하는 값이다."""

    def setUp(self) -> None:
        self.n = len(list((ROOT / "migrations").glob("*.sql")))

    def test_readme_migrate_log_line(self) -> None:
        self.assertIn(f'"완료 — {self.n}개 적용"', README.read_text(encoding="utf-8"),
                      f"README 의 migrate 예상 출력이 실제 개수({self.n})와 다르다")

    def test_readme_generation_note(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn(f"스키마 세대 {self.n}", text)
        self.assertIn(f"`0001`–`{self.n:04d}`", text)

    def test_runbook_migrate_line(self) -> None:
        self.assertIn(f'"완료 — {self.n}개 적용"', RUNBOOK.read_text(encoding="utf-8"))

    def test_runbook_migrate_status_hint(self) -> None:
        self.assertIn(f"스키마 세대 확인 ({self.n})", RUNBOOK.read_text(encoding="utf-8"))


class TestGrowingCountsAreNotPinned(unittest.TestCase):
    """자라는 값을 「같아야 하는 값」으로 읽지 않게 적어 뒀는가."""

    def test_runbook_says_counts_grow(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("검사 수는 계속 늘어난다", text)
        self.assertIn("숫자가 위와 달라도 그 자체는 이상이 아니다", text)

    def test_runbook_names_what_must_hold(self) -> None:
        """대신 **무엇이 유지돼야 하는지**는 말해야 한다."""
        text = RUNBOOK.read_text(encoding="utf-8")
        for must in ("clean_room", "prod_room", "acc=0.8500"):
            self.assertIn(must, text)


class TestShootScopeIsHonest(unittest.TestCase):
    """런북이 「촬영에 안 넣는다」고 적은 근거가 실물에 있는가."""

    def test_runbook_lists_excluded_demos(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        for d in DEMOS:
            self.assertIn(f"{d}.sh", text, f"런북이 {d} 를 언급하지 않는다")

    def test_each_demo_disclaims_at_the_end(self) -> None:
        """런북의 근거 ③ — 각 데모가 스스로 「주장하지 않는다」를 출력한다."""
        for d in DEMOS:
            tail = (ROOT / "scripts" / f"{d}.sh").read_text(encoding="utf-8").rstrip().splitlines()[-1]
            self.assertIn("주장하지 않는다", tail, f"{d}.sh 마지막 줄에 한계 문구가 없다")

    def test_excluded_demos_have_no_powershell_twin(self) -> None:
        """런북의 근거 ② — PowerShell 판이 없다. 생기면 런북을 고쳐야 한다."""
        for d in DEMOS:
            self.assertFalse((ROOT / "scripts" / f"{d}.ps1").exists(),
                             f"{d}.ps1 이 생겼다 — 런북의 「PowerShell 판이 없다」가 거짓이 된다")


class TestExpectedOutputStillMatchesSpec(unittest.TestCase):
    """골든 기대 수치는 `demo-expectation.json` 이 정본이다 (`check_submission` 도 본다)."""

    def test_readme_matches_spec(self) -> None:
        import json

        exp = json.loads((ROOT / "docs" / "spec" / "demo-expectation.json").read_text(encoding="utf-8"))
        readme = README.read_text(encoding="utf-8")
        found = re.findall(r"acc=(0\.\d{4})", readme)
        self.assertTrue(found, "README 에 acc= 예상 출력이 없다")
        for value in found:
            self.assertEqual(value, exp["accuracy"])


if __name__ == "__main__":
    unittest.main()
