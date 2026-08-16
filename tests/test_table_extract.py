"""`table.extract` — 여러 칸을 내는 출력 (단계 6 ④).

## 왜 있는가

지금까지 출력은 **한 칸**이었다(`label` 하나 · `vector` 하나 · `forecast` 하나).
`table.extract` 는 `columns`·`rows`·`header_detected` **셋**을 낸다 — 그래서
「출력 이름은 계약이 정한다」를 **집합으로** 지켜야 한다.

고정하는 것은 넷이다.

1. **Node 가 칸 이름을 주장하지 못하는가** — Core 가 계약의 `required` 와 대조하고
   다르면 422. 이걸 없애면 게이트가 검증한 모양과 증적이 갈린다
2. **새 가중치를 만들지 않았는가** — 열 타입 추론은 `text.classify` 가 이미 하는 일이다
3. **자르지 않고 던지는가** — 행/열 상한을 넘으면 잘라서 돌려주면
   「표를 다 읽었다」가 거짓이 된다
4. **못 하는 것을 할 수 있다고 하지 않는가** — PDF 는 새 의존성이라 받지 않는다
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
INFER = ROOT / "apps" / "node" / "app" / "infer_table.py"
DEMO = ROOT / "scripts" / "table_demo.sh"


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

    def _write(self, text: str) -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        fh.write(text)
        fh.close()
        self.addCleanup(lambda: Path(fh.name).unlink(missing_ok=True))
        return fh.name


class TestParsing(NodeApp):
    def test_csv(self) -> None:
        p = self.mod("table_features").parse_table
        self.assertEqual(
            p(self._write("a,b\n1,2\n"), encoding="utf-8", max_rows=None, max_cols=None),
            [["a", "b"], ["1", "2"]],
        )

    def test_markdown_pipe_and_separator_skipped(self) -> None:
        p = self.mod("table_features").parse_table
        rows = p(self._write("| a | b |\n|---|:-:|\n| 1 | 2 |\n"),
                 encoding="utf-8", max_rows=None, max_cols=None)
        self.assertEqual(rows, [["a", "b"], ["1", "2"]])

    def test_ragged_rows_are_padded_not_truncated(self) -> None:
        """짧은 행은 **채운다**. 자르면 정보를 잃는다."""
        p = self.mod("table_features").parse_table
        rows = p(self._write("a,b,c\n1,2\n"), encoding="utf-8", max_rows=None, max_cols=None)
        self.assertEqual(rows[1], ["1", "2", ""])

    def test_row_limit_raises_not_truncates(self) -> None:
        p = self.mod("table_features").parse_table
        with self.assertRaises(ValueError):
            p(self._write("1\n2\n3\n"), encoding="utf-8", max_rows=2, max_cols=None)

    def test_col_limit_raises(self) -> None:
        p = self.mod("table_features").parse_table
        with self.assertRaises(ValueError):
            p(self._write("a,b,c\n"), encoding="utf-8", max_rows=None, max_cols=2)

    def test_empty_input_raises(self) -> None:
        p = self.mod("table_features").parse_table
        with self.assertRaises(ValueError):
            p(self._write("\n\n"), encoding="utf-8", max_rows=None, max_cols=None)

    def test_header_heuristic_is_loose_and_named_so(self) -> None:
        h = self.mod("table_features").looks_like_header
        self.assertTrue(h(["name", "contact"]))
        self.assertFalse(h(["1", "2"]))


class TestOutputKeysAreContractOwned(unittest.TestCase):
    """**Node 가 칸 이름을 주장하지 못한다.**"""

    def test_core_compares_key_sets(self) -> None:
        code = code_only(COMPLETE)
        self.assertIn("_required_keys(conn, assignment_id)", code)
        self.assertIn("given != required", code)
        self.assertIn("OutputKeysMismatch", code)

    def test_mismatch_becomes_422(self) -> None:
        code = code_only(CORE_MAIN)
        self.assertIn("except OutputKeysMismatch", code)
        self.assertIn("status_code=422", code)

    def test_empty_report_still_rejected(self) -> None:
        """`output` 을 더하면서 「아무것도 안 냈다」 구멍을 열지 않았다."""
        code = code_only(CORE_MAIN)
        self.assertIn("body.vector is None and body.output is None", code)


class TestNoNewWeights(unittest.TestCase):
    def test_reuses_text_classifier_weights(self) -> None:
        self.assertIn("text_struct_scratch.safetensors", DEMO.read_text(encoding="utf-8"))

    def test_arch_maps_to_existing_class(self) -> None:
        src = (ROOT / "apps" / "node" / "app" / "tiny_cnn.py").read_text(encoding="utf-8")
        self.assertIn('"TinyTableTyper": _text_classifier()', src)

    def test_no_new_weight_file(self) -> None:
        names = {p.name for p in (ROOT / "apps" / "node" / "weights").glob("*.safetensors")}
        self.assertNotIn("table_scratch.safetensors", names)


class TestHonestLimits(unittest.TestCase):
    def test_pdf_is_not_promised(self) -> None:
        """PDF 는 새 의존성이라 못 받는다 — 계약이 `text/plain` 만 선언해야 한다."""
        demo = DEMO.read_text(encoding="utf-8")
        self.assertIn('"mediaTypes":["text/plain"]', demo)
        self.assertNotIn("application/pdf", demo)

    def test_source_says_why_no_pdf(self) -> None:
        src = (ROOT / "apps" / "node" / "app" / "table_features.py").read_text(encoding="utf-8")
        self.assertIn("PDF 는 받지 않는다", src)

    def test_support_is_reported(self) -> None:
        """다수결이면 얼마나 우세했는지 **값으로** 같이 낸다 — 3/3 과 2/3 을 같게 보이지 않게.

        키 이름만 찾으면 계약 스키마 문자열에도 있어서 통과한다(변이 검사에서 새어 나갔다).
        **실제로 계산해 담는 줄**을 본다.
        """
        code = code_only(INFER)
        self.assertIn('"support": round(', code)
        self.assertIn("n / len(cells)", code)

    def test_header_detection_is_exposed(self) -> None:
        self.assertIn('"header_detected"', code_only(INFER))

    def test_demo_disclaims(self) -> None:
        self.assertIn("주장하지 않는다", DEMO.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
