"""`text.extract` — 규칙 기반 `키: 값` 필드 추출 (Wave C).

## 왜 있는가

카탈로그에 텍스트를 읽는 능력이 셋이 됐다. 셋이 **무엇을 찾는지**가 갈리지 않으면
「능력이 늘었다」가 「같은 것을 이름만 바꿔 늘렸다」가 된다.

| 능력 | 찾는 것 |
|---|---|
| `text.ner` | 타입 있는 span — 키가 없다 |
| **`text.extract`** | `키: 값` 필드 — 줄에 적힌 이름표 |
| `table.extract` | 격자 (행 × 열) |

그래서 여기서 고정하는 것은 **규칙이 문서대로 도는가**와 **배선이 이어져 있는가**다.
종단(게이트→Task→증적)은 `scripts/text_extract_demo.sh` 가 본다 — DB 가 필요해서
여기 넣지 않는다.

**자연어 이해를 주장하지 않는다.**
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

INFER = ROOT / "apps" / "node" / "app" / "infer_extract.py"
PATTERNS = ROOT / "apps" / "node" / "app" / "extract_patterns.py"
DEMO = ROOT / "scripts" / "text_extract_demo.sh"
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
    def find(text: str):
        return importlib.import_module("app.extract_patterns").find_fields(text)


class TestRules(NodeApp):
    def test_finds_labelled_fields(self) -> None:
        text = "Title: Q3 report\nOwner = ops@example.dev"
        got = self.find(text)
        self.assertEqual([f["key"] for f in got], ["Title", "Owner"])
        self.assertEqual(got[0]["value"], "Q3 report")
        self.assertEqual(got[1]["value"], "ops@example.dev")

    def test_offsets_point_at_the_value(self) -> None:
        """`text[start:end] == value` — `text.ner` 과 같은 규약이라 사람이 대조할 수 있다."""
        text = "- Owner: ops@example.dev\nHost = 10.0.0.1\n"
        for f in self.find(text):
            self.assertEqual(text[f["start"]:f["end"]], f["value"])

    def test_bullet_is_stripped_from_key(self) -> None:
        self.assertEqual(self.find("- Owner: x")[0]["key"], "Owner")
        self.assertEqual(self.find("* Owner: x")[0]["key"], "Owner")

    def test_time_is_not_a_field(self) -> None:
        """키에 글자가 없으면 버린다 — `12:30` 을 필드로 읽지 않는다."""
        self.assertEqual(self.find("12:30"), [])

    def test_url_scheme_is_not_a_key(self) -> None:
        """구분자 뒤가 `//` 면 버린다 — `https` 를 키로 읽지 않는다."""
        self.assertEqual(self.find("https://example.com/a"), [])

    def test_url_as_value_survives(self) -> None:
        got = self.find("Home = https://example.com/a")
        self.assertEqual(got[0]["key"], "Home")
        self.assertEqual(got[0]["value"], "https://example.com/a")

    def test_first_separator_wins_value_keeps_the_rest(self) -> None:
        got = self.find("Note: 값에 : 콜론이 있다")
        self.assertEqual(got[0]["key"], "Note")
        self.assertIn(":", got[0]["value"])

    def test_duplicate_keys_are_all_kept(self) -> None:
        """마지막 것만 남기면 「한 번만 있었다」가 된다."""
        got = self.find("Owner: a@example.dev\nOwner: b@example.dev")
        self.assertEqual(len(got), 2)
        self.assertEqual([f["line"] for f in got], [0, 1])

    def test_empty_value_is_dropped(self) -> None:
        self.assertEqual(self.find("Empty:"), [])

    def test_line_without_label_is_not_a_field(self) -> None:
        self.assertEqual(self.find("not a field line"), [])

    def test_overlong_key_is_dropped(self) -> None:
        from app.extract_patterns import MAX_KEY_CHARS

        self.assertEqual(self.find("k" * (MAX_KEY_CHARS + 1) + ": v"), [])
        self.assertEqual(len(self.find("k" * MAX_KEY_CHARS + ": v")), 1)


class TestArchWiring(unittest.TestCase):
    def test_reference_arch_registered(self) -> None:
        self.assertIn("RuleTextExtract", GATE.read_text(encoding="utf-8"))
        tiny = TINY.read_text(encoding="utf-8")
        self.assertIn('"RuleTextExtract": _rule_extract()', tiny)
        self.assertIn('"RuleTextExtract": "text_extract"', tiny)

    def test_runner_dispatches_the_modality(self) -> None:
        code = code_only(NODE_MAIN)
        self.assertIn('modality == "text_extract"', code)
        self.assertIn("from app.infer_extract import extract_fields", code)

    def test_contract_gate_covers_the_modality(self) -> None:
        code = code_only(CONTRACT)
        self.assertIn("text_extract", code)

    def test_demo_uses_rule_weights(self) -> None:
        demo = DEMO.read_text(encoding="utf-8")
        self.assertIn("rule_extract.safetensors", demo)
        self.assertIn("RuleTextExtract", demo)
        self.assertIn('"fields"', demo)


class TestHonestClaims(unittest.TestCase):
    def test_sources_disclaim_understanding(self) -> None:
        for path in (INFER, PATTERNS, DEMO):
            self.assertIn("주장하지 않", path.read_text(encoding="utf-8"),
                          f"{path.name} 이 무엇을 주장하지 않는지 적지 않았다")

    def test_catalog_marks_implemented(self) -> None:
        cat = CATALOG.read_text(encoding="utf-8")
        self.assertIn("| 14 | `text.extract` | text | `structured` | none | v제품-1 ✅ **구현됨** |", cat)

    def test_catalog_records_identical_weights(self) -> None:
        """`rule_ner` 과 바이트가 같다는 사실을 숨기지 않는다."""
        self.assertIn("rule_ner.safetensors` 와 바이트가 같다",
                      CATALOG.read_text(encoding="utf-8"))

    def test_limit_throws_instead_of_truncating(self) -> None:
        """자르면 「필드를 다 읽었다」가 거짓이 된다 (`table.extract` 와 같은 규율)."""
        code = code_only(INFER)
        self.assertIn("MAX_FIELDS", code)
        self.assertIn("raise TextResourceLimitExceeded", code)


class TestWeightsAreTracked(unittest.TestCase):
    def test_weights_and_meta_exist(self) -> None:
        w = ROOT / "apps" / "node" / "weights" / "rule_extract.safetensors"
        m = ROOT / "apps" / "node" / "weights" / "rule_extract.meta.json"
        self.assertTrue(w.is_file(), "rule_extract.safetensors 이 없다")
        self.assertTrue(m.is_file(), "rule_extract.meta.json 이 없다")

    def test_meta_declares_no_pretraining(self) -> None:
        import json

        meta = json.loads(
            (ROOT / "apps" / "node" / "weights" / "rule_extract.meta.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["arch"], "RuleTextExtract")
        self.assertFalse(meta["pretrained"], "사전학습 가중치를 쓰지 않는다 (D6)")


if __name__ == "__main__":
    unittest.main()
