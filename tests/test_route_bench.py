"""`scripts/route_bench.py` — 라우팅 측정 하네스의 정적 검사.

## 왜 있는가

이 저장소는 라우팅 숫자를 두 번 적고 두 번 다 **재현할 수 없었다** (#110 「4/5 → 5/5」 ·
#116 n=5 표). 세 번째로 잴 때 그 결론 하나가 뒤집혔다 — 작은 자기 선택 표본이었기 때문이다.
하네스를 넣는 이유가 그것이므로, 여기서는 **하네스가 그 교훈을 잃지 않았는지**를 본다.

Core·Ollama 가 필요한 실행 자체는 여기서 하지 않는다 (수동 도구다). 보는 것은 세 가지다 —
**홀드아웃이 튜닝과 겹치지 않는가** · **두 세트가 실행 능력을 다 덮는가** · **품질을
주장하지 않는다고 적혀 있는가**.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "scripts" / "route_bench.py"
CATALOG = ROOT / "docs" / "spec" / "capability-catalog.md"

# `capability-catalog.md` 가 「구현됨」으로 표시한 능력. 하네스는 이것을 다 덮어야 한다.
IMPLEMENTED = frozenset({
    "image.classify", "text.classify", "text.embed", "timeseries.forecast",
    "image.embed", "table.extract", "text.ner", "text.extract", "text.rank",
})


def _load():
    spec = importlib.util.spec_from_file_location("route_bench", BENCH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["route_bench"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestPromptSets(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()

    def test_holdout_shares_no_prompt_with_tuning(self) -> None:
        """겹치면 홀드아웃이 아니다 — 판정이 튜닝 결과를 되풀이할 뿐이다."""
        tuning = {p for p, _ in self.m.TUNING}
        holdout = {p for p, _ in self.m.HOLDOUT}
        self.assertEqual(tuning & holdout, set())

    def test_both_sets_cover_every_implemented_capability(self) -> None:
        """한 능력이라도 빠지면 그 능력의 회귀를 못 본다."""
        for name in ("TUNING", "HOLDOUT"):
            wants = {w for _, w in getattr(self.m, name)}
            self.assertEqual(IMPLEMENTED - wants, set(), f"{name} 이 안 덮는 능력이 있다")

    def test_expected_codes_are_real_capabilities(self) -> None:
        """기대값에 카탈로그에 없는 능력을 적어 두면 영원히 실패한다."""
        for name in ("TUNING", "HOLDOUT"):
            for prompt, want in getattr(self.m, name):
                self.assertIn(want, IMPLEMENTED, f"{name}: {prompt!r} → {want}")

    def test_confusable_pair_is_probed_from_both_sides(self) -> None:
        """`text.ner` ↔ `text.extract` 는 실제로 서로를 가져간 자리다."""
        for name in ("TUNING", "HOLDOUT"):
            wants = [w for _, w in getattr(self.m, name)]
            self.assertGreaterEqual(wants.count("text.ner"), 2, f"{name}")
            self.assertGreaterEqual(wants.count("text.extract"), 2, f"{name}")

    def test_sets_are_registered(self) -> None:
        self.assertEqual(set(self.m.SETS), {"tuning", "holdout"})


class TestHonestClaims(unittest.TestCase):
    def setUp(self) -> None:
        self.text = BENCH.read_text(encoding="utf-8")

    def test_disclaims_accuracy(self) -> None:
        self.assertIn("주장하지 않는다", self.text)

    def test_says_the_prompts_are_hand_picked(self) -> None:
        """정답표가 아니라는 것을 도구가 스스로 말해야 한다."""
        self.assertIn("사람이 고른", self.text)

    def test_default_set_is_holdout(self) -> None:
        """기본값이 튜닝이면 좋아 보이는 숫자가 먼저 나온다."""
        self.assertIn('default="holdout"', self.text)

    def test_records_why_the_harness_exists(self) -> None:
        for mark in ("4/5", "재현할 수 없었다"):
            self.assertIn(mark, self.text)


class TestCatalogClaimsAreQualified(unittest.TestCase):
    """정정한 문구가 다시 지워지지 않게 고정한다."""

    def setUp(self) -> None:
        self.text = CATALOG.read_text(encoding="utf-8")

    def test_old_numbers_carry_the_holdout_context(self) -> None:
        self.assertIn("손으로 고른 프롬프트", self.text)
        self.assertIn("40/60", self.text)

    def test_retracted_miss_is_marked_retracted(self) -> None:
        self.assertIn("그 미스 보고는 취소한다", self.text)

    def test_points_at_the_harness(self) -> None:
        self.assertIn("scripts/route_bench.py", self.text)


if __name__ == "__main__":
    unittest.main()
