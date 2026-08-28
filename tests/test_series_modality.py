"""`timeseries.forecast` — 세 번째 모달리티 어휘 (단계 6 ②).

## 왜 있는가

텍스트·이미지가 아닌 입력이 **같은 계약 형판**(선언 → 러너가 적용 → 실추론 → 출력 대조)으로
도는지를 여기서 본다. 형판이 두 모달리티에만 맞춰져 있었다면 세 번째에서 드러난다.

고정하는 것은 넷이다.

1. **출력 이름을 계약이 정하는가** — Node 가 보낸 필드명을 그대로 쓰면 게이트가 검증한
   출력(`forecast`)과 증적에 남는 출력(`vector`)이 갈라진다. 실제로 그랬다
2. **표본이 모자라면 던지는가** — 0 으로 채우면 모델이 **없는 과거**를 본 것이 되고,
   터지지 않고 조용히 틀린 예측이 나온다
3. **전처리 선언이 망가지면 던지는가** — `window` 는 모델이 보는 과거 길이라,
   바뀌면 같은 가중치가 다른 것을 본다
4. **실제 시계열 성능을 주장하지 않는가** — 합성 데이터로 학습했다

## 한계

torch 가 필요한 것(모델 로드·예측)은 여기서 돌리지 않는다. 그쪽은
`scripts/series_demo.sh` 가 격리 스택에서 실측했다.
"""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

META = ROOT / "apps" / "node" / "weights" / "series_scratch.meta.json"


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


class TestParsing(NodeApp):
    def _write(self, text: str, suffix: str = ".csv") -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
        fh.write(text)
        fh.close()
        self.addCleanup(lambda: Path(fh.name).unlink(missing_ok=True))
        return fh.name

    def test_csv_with_header(self) -> None:
        p = self.mod("series_features").parse_series
        self.assertEqual(p(self._write("value\n1\n2\n3\n"), encoding="utf-8", max_rows=None),
                         [1.0, 2.0, 3.0])

    def test_json_array(self) -> None:
        p = self.mod("series_features").parse_series
        self.assertEqual(p(self._write("[1, 2.5, 3]", ".json"), encoding="utf-8", max_rows=None),
                         [1.0, 2.5, 3.0])

    def test_non_numeric_rejected(self) -> None:
        p = self.mod("series_features").parse_series
        with self.assertRaises(ValueError):
            p(self._write("value\n1\nnot-a-number\n"), encoding="utf-8", max_rows=None)

    def test_max_rows_enforced(self) -> None:
        p = self.mod("series_features").parse_series
        with self.assertRaises(ValueError):
            p(self._write("1\n2\n3\n"), encoding="utf-8", max_rows=2)

    def test_bool_in_json_rejected(self) -> None:
        """`True` 는 파이썬에서 `int` 하위형이다 — 숫자로 통과시키지 않는다."""
        p = self.mod("series_features").parse_series
        with self.assertRaises(ValueError):
            p(self._write("[1, true, 3]", ".json"), encoding="utf-8", max_rows=None)


class TestWindow(NodeApp):
    def test_short_series_raises(self) -> None:
        """0 으로 채우지 않는다 — 없는 과거를 본 것이 되고 조용히 틀린다."""
        w = self.mod("series_features").window_features
        with self.assertRaises(ValueError):
            w([1.0, 2.0], window=24)

    def test_normalises_tail(self) -> None:
        w = self.mod("series_features").window_features
        feat, mean, std = w([float(i) for i in range(30)], window=24)
        self.assertEqual(len(feat), 24)
        self.assertAlmostEqual(sum(feat) / 24, 0.0, places=6)

    def test_constant_series_does_not_divide_by_zero(self) -> None:
        w = self.mod("series_features").window_features
        feat, _, _ = w([5.0] * 24, window=24)
        self.assertEqual(feat, [0.0] * 24)


class TestTablePreprocess(NodeApp):
    def test_defaults(self) -> None:
        r = self.mod("preprocess").resolve_table_preprocess
        self.assertEqual(r(None), ("utf-8", 10000, 24))

    def test_bad_window_raises(self) -> None:
        r = self.mod("preprocess").resolve_table_preprocess
        with self.assertRaises(ValueError):
            r({"window": 1})

    def test_bad_max_rows_raises(self) -> None:
        r = self.mod("preprocess").resolve_table_preprocess
        with self.assertRaises(ValueError):
            r({"max_rows": 0})


class TestOutputKeyComesFromContract(unittest.TestCase):
    """**이름은 계약이 정한다.** Node 가 보낸 필드명을 그대로 쓰지 않는다."""

    def test_core_derives_key(self) -> None:
        code = code_only(ROOT / "apps" / "core" / "app" / "complete.py")
        self.assertIn("_output_key(conn, assignment_id)", code)
        self.assertIn("output_schema -> 'required'", code)

    def test_reason_is_written_down(self) -> None:
        src = (ROOT / "apps" / "core" / "app" / "complete.py").read_text(encoding="utf-8")
        self.assertIn("이름은 계약이 정한다", src)


class TestDispatch(unittest.TestCase):
    def test_modality_registered(self) -> None:
        src = (ROOT / "apps" / "node" / "app" / "tiny_cnn.py").read_text(encoding="utf-8")
        block = src.split("ARCH_MODALITY")[1].split("}")[0]
        self.assertIn('"TinySeriesForecaster": "series"', block)

    def test_run_handles_series(self) -> None:
        code = code_only(ROOT / "apps" / "node" / "app" / "main.py")
        self.assertIn("from app.infer_series import forecast_series", code)

    def test_no_local_golden_fallback(self) -> None:
        """이미지 밖 모달리티에는 로컬 골든 폴백이 없다 — 입력은 Core 중개로만 (D8′)."""
        code = code_only(ROOT / "apps" / "node" / "app" / "main.py")
        self.assertIn(
            'modality in ("text", "text_embed", "series", "table_extract", "text_ner")', code
        )


class TestNoPerformanceClaim(unittest.TestCase):
    def test_meta_disclaims(self) -> None:
        meta = json.loads(META.read_text(encoding="utf-8"))
        self.assertIs(meta["pretrained"], False)
        self.assertIn("규칙 생성", meta["dataset"])
        self.assertIn("주장하지 않는다", meta["note"])

    def test_meta_records_baseline(self) -> None:
        """기준선을 같이 남긴다 — 숫자 하나만 있으면 좋은지 나쁜지 알 수 없다."""
        meta = json.loads(META.read_text(encoding="utf-8"))
        self.assertIn("holdout_mse", meta)
        self.assertIn("holdout_mse_naive_baseline", meta)


if __name__ == "__main__":
    unittest.main()
