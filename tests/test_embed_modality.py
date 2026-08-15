"""`text.embed` — `structured` 출력이 사슬을 타는가 (단계 6 ①).

## 왜 있는가

`text.embed` 는 **`structured` 의 첫 사례**다. D-out(배열·중첩 검증)이 실제로 도는지가
이 능력 하나로 드러난다 — 임베딩 계약은 「차원이 맞는가 · 수치인가」가 전부다.

여기서 고정하는 것은 넷이다.

1. **라벨이 없는 결과에 라벨을 지어내지 않는가** — 빈 문자열로 채우면
   증적이 「라벨이 있었다」고 거짓말한다
2. **아무것도 안 낸 실행이 COMPLETED 가 되지 않는가** — `label`·`vector` 둘 다 비면 거절
3. **특징 추출을 `text.classify` 와 공유하는가** — 두 벌이면 한쪽만 고쳐진다 (D3)
4. **의미적 유사도를 주장하지 않는가** — 이건 학습된 임베딩이 아니다

## 한계

torch 가 필요한 것(사영 로드·실행)은 여기서 돌리지 않는다. 그쪽은
`scripts/embed_demo.sh` 가 격리 스택에서 실측했다 — 2026-08-16 결과를 문서에 적어 뒀다.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"
CORE_MAIN = ROOT / "apps" / "core" / "app" / "main.py"
COMPLETE = ROOT / "apps" / "core" / "app" / "complete.py"
META = ROOT / "apps" / "node" / "weights" / "text_embed_scratch.meta.json"


class TestNoFakeLabel(unittest.TestCase):
    """라벨이 없는 능력에 라벨을 지어내지 않는다."""

    def test_result_omits_label_when_absent(self) -> None:
        code = code_only(COMPLETE)
        self.assertIn("if label is not None:", code,
                      "라벨이 없어도 무조건 result 에 넣고 있다")

    def test_complete_body_allows_null_label(self) -> None:
        code = code_only(CORE_MAIN)
        block = code.split("class CompleteBody")[1].split("\nclass ")[0]
        self.assertIn("label: str | None", block)
        self.assertIn("vector: list[float] | None", block)

    def test_empty_result_is_rejected(self) -> None:
        """`label`·`vector` 둘 다 비면 거절 — 아무것도 안 낸 실행이 COMPLETED 가 되면 안 된다."""
        code = code_only(CORE_MAIN)
        self.assertIn("body.label is None and body.vector is None", code)

    def test_dummy_is_exempted(self) -> None:
        """dummy 는 예외다 — 「placeholder 라 답을 못 낸다」가 이미 증적에 남는다."""
        code = code_only(CORE_MAIN)
        i = code.index("body.label is None and body.vector is None")
        self.assertIn("not body.dummy", code[max(0, i - 120):i])


class TestSharedFeatures(unittest.TestCase):
    def test_embedder_uses_same_features(self) -> None:
        """`text.classify` 와 **같은** 특징 추출을 쓴다 — 두 벌을 만들지 않는다."""
        code = code_only(ROOT / "apps" / "node" / "app" / "infer_embed.py")
        self.assertIn("from app.text_features import features", code)

    def test_embedder_uses_same_preprocess(self) -> None:
        code = code_only(ROOT / "apps" / "node" / "app" / "infer_embed.py")
        self.assertIn("resolve_text_preprocess", code)


class TestDispatch(unittest.TestCase):
    def test_modality_registered(self) -> None:
        src = (ROOT / "apps" / "node" / "app" / "tiny_cnn.py").read_text(encoding="utf-8")
        block = src.split("ARCH_MODALITY")[1].split("}")[0]
        self.assertIn('"TinyTextEmbedder": "text_embed"', block)

    def test_run_handles_embed(self) -> None:
        code = code_only(NODE_MAIN)
        self.assertIn("from app.infer_embed import embed_text", code)
        self.assertIn('modality in ("text", "text_embed")', code)

    def test_label_and_vector_initialised(self) -> None:
        """셋 다 초기화해야 한다.

        임베딩 분기는 `label`·`confidence` 를 채우지 않는데 결과 보고가 그 이름을
        무조건 읽는다. 초기화가 없으면 **배정이 전부 FAILED 가 된다** — 실측했다.
        """
        code = code_only(NODE_MAIN)
        i = code.index("vector: list[float] | None = None")
        head = code[max(0, i - 400):i]
        self.assertIn("label: str | None = None", head)
        self.assertIn("confidence: float | None = None", head)


class TestNoSimilarityClaim(unittest.TestCase):
    def test_meta_disclaims(self) -> None:
        meta = json.loads(META.read_text(encoding="utf-8"))
        self.assertIs(meta["pretrained"], False)
        self.assertIn("주장하지 않는다", meta["note"])
        self.assertIn("라벨 학습을 하지 않는다", meta["dataset"])

    def test_meta_records_determinism(self) -> None:
        """약속하는 것은 재현성뿐이다 — 같은 입력이 같은 벡터."""
        meta = json.loads(META.read_text(encoding="utf-8"))
        self.assertIs(meta["deterministic_same_input"], True)
        self.assertIs(meta["differs_on_different_input"], True)

    def test_source_says_it_is_not_trained(self) -> None:
        src = (ROOT / "apps" / "node" / "app" / "tiny_embed.py").read_text(encoding="utf-8")
        self.assertIn("의미적 유사도", src)


if __name__ == "__main__":
    unittest.main()
