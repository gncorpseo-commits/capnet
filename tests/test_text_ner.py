"""`text.ner` — 규칙 기반 structured span (PR-B).

## 왜 있는가

`table.extract` 가 **여러 칸**을 낸 것처럼, `text.ner` 는 **배열+객체**(`entities[]`)를 낸다.
D-out 검증이 중첩 객체까지 본다 — 이 능력이 그 경로를 타는지 고정한다.

**일반 NER 성능을 주장하지 않는다** — 사람·조직명은 다루지 않는다.
"""

from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

CORE_MAIN = ROOT / "apps" / "core" / "app" / "main.py"
COMPLETE = ROOT / "apps" / "core" / "app" / "complete.py"
INFER = ROOT / "apps" / "node" / "app" / "infer_ner.py"
DEMO = ROOT / "scripts" / "ner_demo.sh"
GATE = ROOT / "apps" / "core" / "app" / "gate.py"
TINY = ROOT / "apps" / "node" / "app" / "tiny_cnn.py"


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
    def mod(name: str):
        return importlib.import_module(f"app.{name}")


class TestPatterns(NodeApp):
    def test_finds_structural_spans(self) -> None:
        find = self.mod("ner_patterns").find_entities
        text = "mail ops@example.dev ip 10.0.0.1 date 2026-08-27"
        ents = find(text)
        labels = {e["label"] for e in ents}
        self.assertIn("email", labels)
        self.assertIn("ipv4", labels)
        self.assertIn("iso_date", labels)
        for e in ents:
            self.assertEqual(text[e["start"]:e["end"]], e["text"])

    def test_invalid_ipv4_skipped(self) -> None:
        find = self.mod("ner_patterns").find_entities
        ents = find("bad 999.999.999.999")
        self.assertEqual(ents, [])


class TestRuleArch(unittest.TestCase):
    def test_reference_arch_registered(self) -> None:
        gate = GATE.read_text(encoding="utf-8")
        self.assertIn("RuleTextNer", gate)
        tiny = TINY.read_text(encoding="utf-8")
        self.assertIn('"RuleTextNer": _rule_ner()', tiny)
        self.assertIn('"RuleTextNer": "text_ner"', tiny)

    def test_demo_uses_rule_weights(self) -> None:
        demo = DEMO.read_text(encoding="utf-8")
        self.assertIn("rule_ner.safetensors", demo)
        self.assertIn("RuleTextNer", demo)

    def test_no_plain_label_in_output_schema(self) -> None:
        demo = DEMO.read_text(encoding="utf-8")
        self.assertIn('"entities"', demo)
        self.assertNotIn('"plain"', demo.split("enum")[1][:200])


class TestHonestClaims(unittest.TestCase):
    def test_source_disclaims_general_ner(self) -> None:
        self.assertIn("주장하지 않", INFER.read_text(encoding="utf-8"))
        self.assertIn("주장하지 않", DEMO.read_text(encoding="utf-8"))

    def test_core_output_key_set_match(self) -> None:
        code = code_only(COMPLETE)
        self.assertIn("given != required", code)


if __name__ == "__main__":
    unittest.main()
