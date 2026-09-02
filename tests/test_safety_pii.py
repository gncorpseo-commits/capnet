"""`safety.pii` — 규칙 기반 PII **참고** (Wave L).

## 왜 있는가

이 능력은 **이름이 위험하다.** 「PII 를 찾는다」가 놓치면 없느니만 못하고, 사람은 결과가
비면 「검사했으니 없다」로 읽는다. 그래서 여기서 고정하는 것은 규칙이 도는가 **말고도**
셋이다:

1. **결과가 자기 한계를 들고 다니는가** — `patterns_checked` 가 항상 나오는가
2. **원문이 결과로 새지 않는가** — span 의 `text` 가 가려져 있고 **복원 불가**인가
3. **`_like` 가 판정이 아닌가** — Luhn·날짜꼴을 못 지나는 것이 걸러지는가

종단(게이트→Task→증적)은 `scripts/pii_demo.sh` 가 본다 — DB 가 필요해서 여기 넣지 않는다.
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

INFER = ROOT / "apps" / "node" / "app" / "infer_pii.py"
RULES = ROOT / "apps" / "node" / "app" / "pii_rules.py"
DEMO = ROOT / "scripts" / "pii_demo.sh"
GATE = ROOT / "apps" / "core" / "app" / "gate.py"
TINY = ROOT / "apps" / "node" / "app" / "tiny_cnn.py"
NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"
CONTRACT = ROOT / "apps" / "node" / "app" / "contract_check.py"
CATALOG = ROOT / "docs" / "spec" / "capability-catalog.md"


def _purge() -> None:
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]


class NodeApp(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = list(sys.path)
        _purge()
        sys.path.insert(0, str(ROOT / "apps" / "node"))

    def tearDown(self) -> None:
        sys.path[:] = self._saved
        _purge()

    @staticmethod
    def scan(text: str):
        return importlib.import_module("app.pii_rules").find_pii(text)

    @staticmethod
    def mod():
        return importlib.import_module("app.pii_rules")


class TestResultCarriesItsLimits(NodeApp):
    """빈 결과가 「깨끗하다」로 읽히지 않게 하는 장치."""

    def test_patterns_checked_is_always_present(self) -> None:
        for text in ("", "아무것도 없는 문장", "ops@example.dev"):
            out = self.scan(text)
            self.assertTrue(out["patterns_checked"], f"{text!r} 에서 비었다")

    def test_patterns_checked_matches_the_label_list(self) -> None:
        """찾아본 목록의 정본은 `PII_LABELS` 다 — 두 벌을 만들지 않는다."""
        out = self.scan("x")
        self.assertEqual(out["patterns_checked"], sorted(self.mod().PII_LABELS))

    def test_empty_findings_is_not_a_clean_claim(self) -> None:
        out = self.scan("여기엔 아무 패턴도 없다")
        self.assertEqual(out["findings"], [])
        self.assertIn("email", out["patterns_checked"])


class TestOriginalTextDoesNotLeak(NodeApp):
    """결과가 **새 유출면**이 되지 않아야 한다."""

    def test_email_is_masked(self) -> None:
        out = self.scan("문의 ops@example.dev 로")
        got = out["findings"][0]["text"]
        self.assertNotIn("ops@example.dev", got)
        self.assertIn("*", got)
        self.assertTrue(got.endswith(".dev"), got)

    def test_krrn_hides_the_birthdate_part(self) -> None:
        """앞 6자리도 가린다 — 생년월일 꼴이라 그 자체가 개인정보다."""
        out = self.scan("주민 900101-1234567")
        got = out["findings"][0]["text"]
        self.assertNotIn("900101", got)
        self.assertNotIn("1234567", got)

    def test_card_keeps_only_the_last_four(self) -> None:
        out = self.scan("카드 4111 1111 1111 1111")
        got = out["findings"][0]["text"]
        self.assertTrue(got.endswith("1111"))
        self.assertNotIn(" ", got)
        self.assertEqual(got.count("*"), 12)

    def test_no_finding_text_equals_the_original_span(self) -> None:
        """어떤 라벨이든 **가려지지 않은 채로 나가면 안 된다.**"""
        text = ("ops@example.dev 010-1234-5678 900101-1234567 "
                "4111111111111111 10.0.0.1 7f3a9c21-1b2c-4d3e-8f90-aabbccddeeff")
        for f in self.scan(text)["findings"]:
            original = text[f["start"]:f["end"]]
            self.assertNotEqual(f["text"], original, f["label"])
            self.assertIn("*", f["text"], f["label"])

    def test_offsets_still_point_at_the_original(self) -> None:
        """가리는 것은 `text` 뿐 — 위치는 원문 그대로여야 쓸모가 있다."""
        text = "문의 ops@example.dev 로"
        f = self.scan(text)["findings"][0]
        self.assertEqual(text[f["start"]:f["end"]], "ops@example.dev")


class TestLikeIsNotAVerdict(NodeApp):
    def test_card_needs_luhn(self) -> None:
        self.assertEqual(self.scan("카드 1234 5678 9012 3456")["findings"], [])
        self.assertTrue(self.scan("카드 4111 1111 1111 1111")["findings"])

    def test_krrn_needs_a_calendar_shaped_date(self) -> None:
        self.assertEqual(self.scan("991301-1234567")["findings"], [])
        self.assertTrue(self.scan("900101-1234567")["findings"])

    def test_luhn_is_documented_as_a_typo_check(self) -> None:
        self.assertIn("오타 검사", RULES.read_text(encoding="utf-8"))

    def test_ipv4_octets_are_bounded(self) -> None:
        self.assertEqual(self.scan("999.999.999.999")["findings"], [])


class TestRules(NodeApp):
    def test_overlaps_go_to_the_first_pattern(self) -> None:
        """UUID 안의 숫자가 카드로 다시 잡히면 안 된다."""
        out = self.scan("7f3a9c21-1b2c-4d3e-8f90-aabbccddeeff")
        self.assertEqual([f["label"] for f in out["findings"]], ["uuid"])

    def test_findings_are_sorted_by_position(self) -> None:
        out = self.scan("10.0.0.1 그리고 ops@example.dev")
        starts = [f["start"] for f in out["findings"]]
        self.assertEqual(starts, sorted(starts))

    def test_phone_is_found(self) -> None:
        labels = [f["label"] for f in self.scan("연락 010-1234-5678")["findings"]]
        self.assertIn("phone_kr_like", labels)

    def test_output_has_no_foreign_keys(self) -> None:
        out = self.scan("ops@example.dev")
        self.assertEqual(set(out), {"patterns_checked", "findings"})
        self.assertEqual(set(out["findings"][0]), {"label", "start", "end", "text"})


class TestWiring(unittest.TestCase):
    def test_arch_is_a_reference_arch(self) -> None:
        self.assertIn('"RuleTextPii"', code_only(GATE))

    def test_arch_registry_and_modality(self) -> None:
        tiny = TINY.read_text(encoding="utf-8")
        self.assertIn('"RuleTextPii": _rule_pii()', tiny)
        self.assertIn('"RuleTextPii": "text_pii"', tiny)

    def test_runner_dispatches_the_modality(self) -> None:
        code = code_only(NODE_MAIN)
        self.assertIn('modality == "text_pii"', code)
        self.assertIn("from app.infer_pii import scan_pii", code)

    def test_runner_has_no_local_fallback(self) -> None:
        """이미지 밖 모달리티는 입력이 Core 중개로만 온다 (D8′).

        예전에는 `main.py` 의 **포함식**(Core 입력을 요구하는 모달리티 나열)에
        이름이 있는지를 봤다. 그 목록은 `app/modality.py` 로 옮겨지면서 **뜻이
        뒤집혔다** — 이제 **폴백을 가진 쪽**만 적는다. 불변식은 그대로고,
        여기서 보는 자리만 옮긴다.
        """
        self.assertNotIn(
            '"text_pii"',
            code_only(ROOT / "apps" / "node" / "app" / "modality.py"),
            "text_pii 에 로컬 골든셋 폴백이 열려 있다",
        )

    def test_contract_gate_covers_the_modality(self) -> None:
        self.assertIn("text_pii", code_only(CONTRACT))

    def test_executor_rejects_unknown_arch(self) -> None:
        self.assertIn("unknown pii arch", code_only(INFER))

    def test_limit_throws_instead_of_truncating(self) -> None:
        code = code_only(INFER)
        self.assertIn("MAX_FINDINGS", code)
        self.assertIn("raise TextResourceLimitExceeded", code)


class TestHonestClaims(unittest.TestCase):
    def test_sources_disclaim_detection(self) -> None:
        for path in (INFER, RULES, DEMO):
            text = path.read_text(encoding="utf-8")
            self.assertIn("탐지가 아니라", text, f"{path.name}")

    def test_sources_disclaim_completeness(self) -> None:
        for path in (RULES, DEMO, CATALOG):
            self.assertIn("놓친 것이 없다고 말하지 않는", path.read_text(encoding="utf-8"),
                          f"{path.name}")

    def test_no_compliance_claim(self) -> None:
        """「개인정보 보호 준수」를 파는 문장이 없어야 한다."""
        for path in (RULES, CATALOG, DEMO):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("컴플라이언스를 보장", text, f"{path.name}")
            self.assertNotIn("준수를 보장", text, f"{path.name}")
            self.assertIn("보증하지 않는", text, f"{path.name}")

    def test_rules_name_the_neighbours(self) -> None:
        cat = CATALOG.read_text(encoding="utf-8")
        for neighbour in ("text.ner", "text.extract"):
            self.assertIn(neighbour, cat)

    def test_catalog_marks_implemented(self) -> None:
        self.assertIn("| 49 | `safety.pii` | text | `structured` | none | v제품-1 ✅ **구현됨** |",
                      CATALOG.read_text(encoding="utf-8"))

    def test_catalog_records_identical_weights(self) -> None:
        self.assertIn("넷 다 바이트가 같다", CATALOG.read_text(encoding="utf-8"))

    def test_demo_syncs_description(self) -> None:
        """Wave K 규율 — 새 데모도 등록 시 description 을 맞춘다."""
        demo = DEMO.read_text(encoding="utf-8")
        self.assertIn("cap_body=", demo)
        self.assertIn("-X PATCH", demo)


class TestWeightsAreTracked(unittest.TestCase):
    def test_weights_and_meta_exist(self) -> None:
        w = ROOT / "apps" / "node" / "weights" / "rule_pii.safetensors"
        m = ROOT / "apps" / "node" / "weights" / "rule_pii.meta.json"
        self.assertTrue(w.is_file())
        self.assertTrue(m.is_file())

    def test_meta_declares_no_pretraining_and_matches_sha(self) -> None:
        import hashlib
        import json

        w = ROOT / "apps" / "node" / "weights" / "rule_pii.safetensors"
        meta = json.loads(
            (ROOT / "apps" / "node" / "weights" / "rule_pii.meta.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["arch"], "RuleTextPii")
        self.assertFalse(meta["pretrained"], "사전학습 가중치를 쓰지 않는다 (D6)")
        self.assertEqual(meta["weights_sha256"], hashlib.sha256(w.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
