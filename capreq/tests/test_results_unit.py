"""`result_ref` 요약 — Core·Ollama 없이."""

from __future__ import annotations

import json
import unittest

from capreq.results import extract_label, parse_result_ref, summarize_result


class TestParse(unittest.TestCase):
    def test_task_with_json_string(self) -> None:
        task = {"id": "t1", "result_ref": json.dumps({"label": "email"})}
        self.assertEqual(parse_result_ref(task), {"label": "email"})

    def test_broken_json_is_none(self) -> None:
        self.assertIsNone(parse_result_ref({"result_ref": "{not json"}))

    def test_missing_result_ref_is_none(self) -> None:
        self.assertIsNone(parse_result_ref({"id": "t1", "result_ref": None}))


class TestSummarize(unittest.TestCase):
    def test_label_and_confidence(self) -> None:
        out = summarize_result(
            {"label": "email", "confidence": 0.75, "dummy": False, "weights_sha256": "ab"}
        )
        self.assertEqual(out["label"], "email")
        self.assertAlmostEqual(out["confidence"], 0.75)
        # 증적 칸은 결과로 새지 않는다.
        self.assertNotIn("weights_sha256", out)
        self.assertNotIn("other", out)

    def test_entities(self) -> None:
        ents = [{"label": "email", "start": 8, "end": 22, "text": "a@example.dev"}]
        out = summarize_result({"entities": ents, "dummy": False, "weights_sha256": "ab"})
        self.assertEqual(out["entities"], ents)
        self.assertNotIn("vector", out)

    def test_forecast_named_by_contract(self) -> None:
        out = summarize_result({"forecast": [1.0, 2.0, 3.0, 4.0], "weights_sha256": "ab"})
        self.assertEqual(out["vector"]["name"], "forecast")
        self.assertEqual(out["vector"]["dim"], 4)
        self.assertFalse(out["vector"]["truncated"])

    def test_long_vector_is_truncated(self) -> None:
        out = summarize_result({"vector": [float(i) for i in range(64)]})
        self.assertEqual(out["vector"]["dim"], 64)
        self.assertEqual(len(out["vector"]["head"]), 8)
        self.assertTrue(out["vector"]["truncated"])

    def test_table(self) -> None:
        out = summarize_result(
            {
                "columns": [{"index": 0, "type": "text", "support": 3}],
                "rows": [["a"], ["b"]],
                "header_detected": True,
            }
        )
        self.assertEqual(out["table"]["row_count"], 2)
        self.assertTrue(out["table"]["header_detected"])
        self.assertFalse(out["table"]["truncated"])

    def test_unknown_key_is_kept(self) -> None:
        out = summarize_result({"segments": [1, 2], "weights_sha256": "ab"})
        self.assertEqual(out["other"], {"segments": [1, 2]})

    def test_empty_when_unparseable(self) -> None:
        self.assertEqual(summarize_result({"result_ref": "nope"}), {})


class TestExtractLabel(unittest.TestCase):
    def test_from_task(self) -> None:
        task = {"result_ref": json.dumps({"label": "url"})}
        self.assertEqual(extract_label(task), "url")

    def test_none_without_label(self) -> None:
        self.assertIsNone(extract_label({"result_ref": json.dumps({"vector": [1.0]})}))


if __name__ == "__main__":
    unittest.main()
