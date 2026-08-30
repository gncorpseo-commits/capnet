"""`result_ref` 요약 — Core·Ollama 없이."""

from __future__ import annotations

import json
import unittest

from capreq.results import LIST_HEAD, extract_label, parse_result_ref, summarize_result


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

    def test_fields_are_summarised(self) -> None:
        """`text.extract` — #110 이후 요약기가 이 칸을 몰라 원시 JSON 으로 새어 나갔다."""
        out = summarize_result({
            "fields": [
                {"key": "Ticket", "value": "INC-4021", "line": 0, "start": 8, "end": 16},
                {"key": "Severity", "value": "high", "line": 1, "start": 11, "end": 15},
            ]
        })
        self.assertEqual(out["fields"]["count"], 2)
        self.assertEqual(out["fields"]["items"][0]["key"], "Ticket")
        self.assertFalse(out["fields"]["truncated"])
        self.assertNotIn("other", out, "fields 가 other 로 새면 안 된다")

    def test_fields_keep_offsets_for_cross_checking(self) -> None:
        """`start`·`end` 를 지우지 않는다 — 증적을 사람이 대조하는 값이다."""
        out = summarize_result({"fields": [{"key": "k", "value": "v", "line": 0,
                                            "start": 3, "end": 4}]})
        self.assertEqual(out["fields"]["items"][0]["start"], 3)

    def test_long_field_list_is_truncated_for_display(self) -> None:
        """화면 자르기다 — `count` 는 전체를 말하고 `truncated` 가 사실을 밝힌다."""
        many = [{"key": f"k{i}", "value": "v", "line": i} for i in range(LIST_HEAD + 5)]
        out = summarize_result({"fields": many})
        self.assertEqual(len(out["fields"]["items"]), LIST_HEAD)
        self.assertEqual(out["fields"]["count"], LIST_HEAD + 5)
        self.assertTrue(out["fields"]["truncated"])

    def test_empty_fields_is_not_missing(self) -> None:
        """빈 목록과 「칸이 없다」는 다르다."""
        out = summarize_result({"fields": []})
        self.assertEqual(out["fields"]["count"], 0)

    def test_ranking_is_summarised(self) -> None:
        """`text.rank` — #116 이후 요약기가 이 칸을 몰랐다."""
        out = summarize_result({
            "query": "느린 쿼리 인덱스",
            "ranking": [
                {"rank": 1, "line": 3, "text": "인덱스 없이 느린 쿼리",
                 "score": 0.75, "overlap": ["느린", "인덱스", "쿼리"]},
                {"rank": 2, "line": 1, "text": "무관한 줄", "score": 0.0, "overlap": []},
            ],
        })
        self.assertEqual(out["ranking"]["query"], "느린 쿼리 인덱스")
        self.assertEqual(out["ranking"]["count"], 2)
        self.assertEqual(out["ranking"]["items"][0]["overlap"], ["느린", "인덱스", "쿼리"])
        self.assertNotIn("other", out, "ranking·query 가 other 로 새면 안 된다")

    def test_ranking_order_is_not_recomputed(self) -> None:
        """Core 가 준 순서를 그대로 둔다 — 표시 계층이 순위를 다시 매기지 않는다."""
        out = summarize_result({"ranking": [
            {"rank": 1, "score": 0.1, "text": "a"},
            {"rank": 2, "score": 0.9, "text": "b"},
        ]})
        self.assertEqual([i["text"] for i in out["ranking"]["items"]], ["a", "b"])

    def test_long_ranking_is_truncated_for_display(self) -> None:
        many = [{"rank": i + 1, "score": 0.0, "text": "t", "overlap": []}
                for i in range(LIST_HEAD + 3)]
        out = summarize_result({"ranking": many})
        self.assertEqual(len(out["ranking"]["items"]), LIST_HEAD)
        self.assertEqual(out["ranking"]["count"], LIST_HEAD + 3)
        self.assertTrue(out["ranking"]["truncated"])

    def test_query_without_ranking_is_not_swallowed(self) -> None:
        """소비하지 않은 칸은 `other` 로 그대로 내보낸다 — 이름만 안다고 빼지 않는다."""
        out = summarize_result({"query": "고아 질의"})
        self.assertNotIn("ranking", out)
        self.assertEqual(out["other"], {"query": "고아 질의"})

    def test_summariser_adds_no_new_claim(self) -> None:
        """점수를 해석하지 않는다 — 「관련도」 같은 파생 칸을 만들지 않는다."""
        out = summarize_result({"ranking": [{"rank": 1, "score": 0.5, "text": "a"}]})
        self.assertEqual(set(out["ranking"]), {"items", "count", "truncated"})
        self.assertEqual(set(out["ranking"]["items"][0]), {"rank", "score", "text"})

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
