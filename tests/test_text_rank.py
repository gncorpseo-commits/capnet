"""`text.rank` — 규칙 기반 어휘 겹침 순위 (Wave G).

## 왜 있는가

카탈로그에 텍스트를 읽는 능력이 넷이 됐다. 넷이 **무엇을 내놓는지**가 갈리지 않으면
「능력이 늘었다」가 「같은 것을 이름만 바꿔 늘렸다」가 된다.

| 능력 | 내놓는 것 |
|---|---|
| `text.ner` | 타입 있는 span — 키가 없다 |
| `text.extract` | `키: 값` 필드 — 줄에 적힌 이름표 |
| `table.extract` | 격자 (행 × 열) |
| **`text.rank`** | 후보 줄의 **순위** — 질의와 겹친 낱말이 근거다 |

그래서 여기서 고정하는 것은 **규칙이 문서대로 도는가**와 **배선이 이어져 있는가**다.
종단(게이트→Task→증적)은 `scripts/text_rank_demo.sh` 가 본다 — DB 가 필요해서
여기 넣지 않는다.

**뜻을 이해한다고 주장하지 않는다.** 어휘가 겹치는 정도만 센다.
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

INFER = ROOT / "apps" / "node" / "app" / "infer_rank.py"
RULES = ROOT / "apps" / "node" / "app" / "rank_rules.py"
DEMO = ROOT / "scripts" / "text_rank_demo.sh"
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
    def rank(text: str):
        return importlib.import_module("app.rank_rules").rank_lines(text)

    @staticmethod
    def tokens(line: str):
        return importlib.import_module("app.rank_rules").tokenize(line)


class TestRules(NodeApp):
    def test_first_nonblank_line_is_the_query(self) -> None:
        out = self.rank("\n\n  ipv4 주소  \n후보 하나\n")
        self.assertEqual(out["query"], "ipv4 주소")
        self.assertEqual([r["text"] for r in out["ranking"]], ["후보 하나"])

    def test_ranks_by_overlap(self) -> None:
        out = self.rank("apple banana\ncherry\napple banana\napple")
        self.assertEqual([r["text"] for r in out["ranking"]],
                         ["apple banana", "apple", "cherry"])
        self.assertEqual(out["ranking"][0]["score"], 1.0)
        self.assertEqual(out["ranking"][2]["score"], 0.0)

    def test_overlap_lists_the_shared_tokens(self) -> None:
        """왜 그 점수인지 사람이 대조할 수 있어야 한다."""
        out = self.rank("apple banana\nbanana apple durian")
        self.assertEqual(out["ranking"][0]["overlap"], ["apple", "banana"])

    def test_score_is_jaccard(self) -> None:
        # 질의 {apple,banana} · 후보 {banana,cherry} → 교집합 1 / 합집합 3
        out = self.rank("apple banana\nbanana cherry")
        self.assertEqual(out["ranking"][0]["score"], round(1 / 3, 4))

    def test_repeats_do_not_inflate_the_score(self) -> None:
        """집합이라 한 줄에 같은 낱말이 여러 번 나와도 한 번으로 센다."""
        once = self.rank("apple\napple")["ranking"][0]["score"]
        many = self.rank("apple\napple apple apple")["ranking"][0]["score"]
        self.assertEqual(once, many)

    def test_ties_keep_original_line_order(self) -> None:
        """같은 입력이면 언제나 같은 순서 — 순위에 우연이 없어야 증적이 뜻을 갖는다."""
        out = self.rank("q\nb one\na one\nc one")
        self.assertEqual([r["line"] for r in out["ranking"]], [1, 2, 3])
        self.assertEqual([r["rank"] for r in out["ranking"]], [1, 2, 3])

    def test_line_is_the_original_line_number(self) -> None:
        """빈 줄이 후보 번호를 밀지 않는다 — `line` 은 원본 줄 번호다."""
        out = self.rank("q\n\n\nlate candidate")
        self.assertEqual(out["ranking"][0]["line"], 3)

    def test_case_is_folded(self) -> None:
        self.assertEqual(self.rank("Apple\napple")["ranking"][0]["score"], 1.0)

    def test_punctuation_is_a_boundary(self) -> None:
        self.assertEqual(self.tokens("a-b_c, d!"), {"a", "b", "c", "d"})

    def test_korean_tokens_survive(self) -> None:
        self.assertEqual(self.tokens("로그에서 ipv4 주소"), {"로그에서", "ipv4", "주소"})

    def test_inflection_does_not_match(self) -> None:
        """**뜻을 모른다.** 어형이 다르면 안 겹친다 — 이것이 이 능력의 한계다."""
        out = self.rank("자동차\n차량")
        self.assertEqual(out["ranking"][0]["score"], 0.0)
        self.assertEqual(out["ranking"][0]["overlap"], [])

    def test_query_without_tokens_scores_everything_zero(self) -> None:
        out = self.rank("!!! ???\napple\nbanana")
        self.assertEqual([r["score"] for r in out["ranking"]], [0.0, 0.0])
        self.assertEqual([r["line"] for r in out["ranking"]], [1, 2])

    def test_no_candidates_is_not_an_error(self) -> None:
        out = self.rank("질의만 있다\n\n")
        self.assertEqual(out["query"], "질의만 있다")
        self.assertEqual(out["ranking"], [])

    def test_empty_input_yields_empty_query(self) -> None:
        self.assertEqual(self.rank("\n \n"), {"query": "", "ranking": []})

    def test_rank_is_dense_and_starts_at_one(self) -> None:
        out = self.rank("q\na\nb\nc")
        self.assertEqual([r["rank"] for r in out["ranking"]], [1, 2, 3])

    def test_output_has_no_foreign_keys(self) -> None:
        """`label`·`vector`·`entities`·`fields` 는 다른 능력의 칸이다."""
        out = self.rank("q\na")
        self.assertEqual(set(out), {"query", "ranking"})
        self.assertEqual(set(out["ranking"][0]), {"rank", "line", "text", "score", "overlap"})


class TestWiring(unittest.TestCase):
    def test_arch_is_a_reference_arch(self) -> None:
        self.assertIn('"RuleTextRank"', code_only(GATE))

    def test_arch_registry_and_modality(self) -> None:
        tiny = TINY.read_text(encoding="utf-8")
        self.assertIn('"RuleTextRank": _rule_rank()', tiny)
        self.assertIn('"RuleTextRank": "text_rank"', tiny)

    def test_runner_dispatches_the_modality(self) -> None:
        code = code_only(NODE_MAIN)
        self.assertIn('modality == "text_rank"', code)
        self.assertIn("from app.infer_rank import rank_text", code)

    def test_runner_has_no_local_fallback(self) -> None:
        """이미지 밖 모달리티는 입력이 Core 중개로만 온다 (D8′)."""
        self.assertIn('"text_rank",', code_only(NODE_MAIN))

    def test_contract_gate_covers_the_modality(self) -> None:
        code = code_only(CONTRACT)
        self.assertIn("text_rank", code)

    def test_executor_rejects_unknown_arch(self) -> None:
        self.assertIn("unknown rank arch", code_only(INFER))

    def test_demo_uses_rule_weights(self) -> None:
        demo = DEMO.read_text(encoding="utf-8")
        self.assertIn("rule_rank.safetensors", demo)
        self.assertIn("RuleTextRank", demo)
        self.assertIn('"ranking"', demo)


class TestHonestClaims(unittest.TestCase):
    def test_sources_disclaim_understanding(self) -> None:
        for path in (INFER, RULES, DEMO):
            self.assertIn("주장하지 않", path.read_text(encoding="utf-8"),
                          f"{path.name} 이 무엇을 주장하지 않는지 적지 않았다")

    def test_rules_name_the_neighbours(self) -> None:
        """이웃 능력과 경계를 긋는다 — 라우팅이 섞이지 않게 (#112 교훈)."""
        rules = RULES.read_text(encoding="utf-8")
        for neighbour in ("text.embed", "retrieve.dense", "text.ner", "text.extract"):
            self.assertIn(neighbour, rules, f"{neighbour} 와의 경계가 적혀 있지 않다")

    def test_catalog_marks_implemented(self) -> None:
        cat = CATALOG.read_text(encoding="utf-8")
        self.assertIn("| 24 | `text.rank` | text | `structured` | none | v제품-1 ✅ **구현됨** |", cat)

    def test_catalog_records_identical_weights(self) -> None:
        """규칙 실행기들의 가중치가 바이트가 같다는 사실을 숨기지 않는다.

        Wave L 에서 `safety.pii` 가 붙어 **넷**이 됐다. 개수를 손으로 세는 대신
        「N 다 바이트가 같다」가 있는지만 본다 — 다음 규칙 실행기에서 또 고치지 않게.
        """
        self.assertRegex(CATALOG.read_text(encoding="utf-8"), r"[가-힣]+ 다 바이트가 같다")

    def test_limit_throws_instead_of_truncating(self) -> None:
        """자르면 「전부 줄 세웠다」가 거짓이 된다 (`text.extract` 와 같은 규율)."""
        code = code_only(INFER)
        self.assertIn("MAX_CANDIDATES", code)
        self.assertIn("raise TextResourceLimitExceeded", code)


class TestWeightsAreTracked(unittest.TestCase):
    def test_weights_and_meta_exist(self) -> None:
        w = ROOT / "apps" / "node" / "weights" / "rule_rank.safetensors"
        m = ROOT / "apps" / "node" / "weights" / "rule_rank.meta.json"
        self.assertTrue(w.is_file(), "rule_rank.safetensors 이 없다")
        self.assertTrue(m.is_file(), "rule_rank.meta.json 이 없다")

    def test_meta_declares_no_pretraining(self) -> None:
        import json

        meta = json.loads(
            (ROOT / "apps" / "node" / "weights" / "rule_rank.meta.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["arch"], "RuleTextRank")
        self.assertFalse(meta["pretrained"], "사전학습 가중치를 쓰지 않는다 (D6)")

    def test_meta_sha_matches_the_file(self) -> None:
        import hashlib
        import json

        w = ROOT / "apps" / "node" / "weights" / "rule_rank.safetensors"
        meta = json.loads(
            (ROOT / "apps" / "node" / "weights" / "rule_rank.meta.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["weights_sha256"], hashlib.sha256(w.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
