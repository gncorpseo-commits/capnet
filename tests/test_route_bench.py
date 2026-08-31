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
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "scripts" / "route_bench.py"
CATALOG = ROOT / "docs" / "spec" / "capability-catalog.md"

# `capreq` 는 루트 검사의 의존성이 아니다. `adapters.base` 는 dataclass 뿐이라
# 설치 없이 읽힌다 — 그래도 못 읽으면 그 검사만 건너뛴다.
sys.path.insert(0, str(ROOT / "capreq" / "src"))
try:
    from capreq.adapters.base import CapabilityInfo
except Exception:  # pragma: no cover
    CapabilityInfo = None

# 「구현됨」 목록을 **손으로 세지 않는다.**
#
# 처음엔 아홉 개를 적어 뒀는데, Wave L 이 `safety.pii` 를 더했을 때 **여기가 뒤처져도
# 검사가 통과했다** — 그래서 라우팅 벤치가 새 능력을 덮지 않는 것을 아무도 몰랐다.
# 이 저장소가 이번 달에 네 번 겪은 모양이다(데모 목록 · 자른 사실 고지 · 바이트 동일 문구 ·
# 그리고 여기). **정본은 카탈로그의 「✅ 구현됨」 행**이고 여기는 그걸 읽는다.
_IMPL_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*`([a-z][a-z0-9_.]*)`\s*\|.*✅\s*\*\*구현됨\*\*", re.M
)


def implemented_capabilities() -> frozenset[str]:
    return frozenset(_IMPL_ROW.findall(CATALOG.read_text(encoding="utf-8")))


IMPLEMENTED = implemented_capabilities()


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

    def test_the_catalog_probe_finds_things(self) -> None:
        """정규식이 0개를 찾으며 통과하는 상태를 막는다."""
        self.assertGreaterEqual(len(IMPLEMENTED), 10, sorted(IMPLEMENTED))

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


class TestPatchedCatalogIsFaithful(unittest.TestCase):
    """`--descriptions repo` 가 **설명만** 바꿔야 한다.

    처음 판은 `CapabilityInfo(...)` 를 새로 지어 `output_kind` 를 떨어뜨렸다. 라우터
    프롬프트가 `kind=` 를 넣으므로 그 조건은 「설명만 바꾼 카탈로그」가 아니었고,
    그렇게 잰 값이 비교표에 들어가 있었다. 다시 그러지 않게 못 박는다.
    """

    def setUp(self) -> None:
        self.m = _load()

    @unittest.skipIf(CapabilityInfo is None, "capreq 를 못 읽었다")
    def test_only_description_changes(self) -> None:
        import dataclasses

        original = CapabilityInfo(
            code="text.ner", version=1, name="n", description="옛 설명",
            output_kind="structured", trust_domain_min="team", extra={"id": "x"},
        )

        class Inner:
            def list_capabilities(self):
                return [original]

        got = self.m._Patched(Inner(), {"text.ner": "새 설명"}).list_capabilities()[0]
        self.assertEqual(got.description, "새 설명")
        for field in dataclasses.fields(CapabilityInfo):
            if field.name == "description":
                continue
            self.assertEqual(
                getattr(got, field.name), getattr(original, field.name),
                f"{field.name} 이 조용히 바뀌었다",
            )

    @unittest.skipIf(CapabilityInfo is None, "capreq 를 못 읽었다")
    def test_unpatched_capability_is_untouched(self) -> None:
        original = CapabilityInfo(code="a.b", version=2, name="n", description="그대로",
                                  output_kind="freeform")

        class Inner:
            def list_capabilities(self):
                return [original]

        got = self.m._Patched(Inner(), {"other.code": "x"}).list_capabilities()[0]
        self.assertEqual(got, original)


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

    def test_the_broken_wrapper_number_is_retracted(self) -> None:
        """`40/60` 은 `output_kind` 를 떨어뜨린 래퍼로 잰 값이다 — 되살리지 않는다."""
        self.assertIn("철회한다", self.text)
        self.assertIn("output_kind", self.text)

    def test_variance_is_stated_not_hidden(self) -> None:
        """같은 조건이 흔들린다는 사실이 숫자 옆에 있어야 한다."""
        self.assertIn("흔들린다", self.text)

    def test_retracted_miss_is_marked_retracted(self) -> None:
        self.assertIn("그 미스 보고는 취소한다", self.text)

    def test_points_at_the_harness(self) -> None:
        self.assertIn("scripts/route_bench.py", self.text)


if __name__ == "__main__":
    unittest.main()
