"""`image.embed` — 이미지가 `structured` 를 낸다 (단계 6 ③).

## 왜 있는가

그동안 **이미지 모달리티는 `closed_set_labels` 만** 냈다. 「이미지 × structured」는
검증된 적이 없는 조합이고, 검증되지 않은 조합에서 형판이 깨지는 것을 이미 두 번 봤다
(출력 이름 · 로더 불일치).

고정하는 것은 넷이다.

1. **새 가중치를 만들지 않았는가** — `eurosat_scratch.safetensors` 를 그대로 쓴다
2. **`strict=False` 로 조용히 넘기지 않는가** — 트렁크 키가 빠져도 통과하면
   랜덤 초기화 층으로 추론하면서 벡터는 그럴듯하게 나온다
3. **검증과 실행이 같은 로더를 쓰는가** — 계약 게이트가 다르게 로드하면
   통과할 Agent 를 떨어뜨리거나 그 반대가 된다 (실제로 떨어뜨렸다)
4. **전처리를 분류와 공유하는가** — 두 벌이면 한쪽만 고쳐진다 (D3)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

EMBED = ROOT / "apps" / "node" / "app" / "tiny_image_embed.py"
INFER_EMBED = ROOT / "apps" / "node" / "app" / "infer_image_embed.py"
INFER = ROOT / "apps" / "node" / "app" / "infer.py"
CONTRACT = ROOT / "apps" / "node" / "app" / "contract_check.py"


class TestNoNewWeights(unittest.TestCase):
    def test_reuses_existing_file(self) -> None:
        """데모가 **기존** 가중치를 가리킨다 — 새로 학습·커밋하지 않았다."""
        demo = (ROOT / "scripts" / "image_embed_demo.sh").read_text(encoding="utf-8")
        self.assertIn("eurosat_scratch.safetensors", demo)

    def test_no_new_weight_file_added(self) -> None:
        committed = {p.name for p in (ROOT / "apps" / "node" / "weights").glob("*.safetensors")}
        self.assertNotIn("image_embed_scratch.safetensors", committed,
                         "이미지 임베딩용 가중치를 새로 만들었다 — 재사용이 목적이었다")

    def test_no_training_script(self) -> None:
        self.assertFalse((ROOT / "apps" / "train" / "train_image_embed.py").exists())


class TestExplicitTrunkLoad(unittest.TestCase):
    def test_no_strict_false(self) -> None:
        """`strict=False` 는 트렁크 키가 빠져도 통과시킨다 — 조용히 틀린다."""
        code = code_only(EMBED)
        self.assertNotIn("strict=False", code)

    def test_missing_key_raises(self) -> None:
        code = code_only(EMBED)
        self.assertIn("missing = wanted - set(trunk)", code)
        self.assertIn("raise ValueError", code)

    def test_only_trunk_prefix_used(self) -> None:
        code = code_only(EMBED)
        self.assertIn("TRUNK_PREFIX", code)


class TestGateUsesSameLoader(unittest.TestCase):
    """검증과 실행이 갈리면 통과할 Agent 를 떨어뜨린다 — 실제로 떨어뜨렸다."""

    def test_contract_check_delegates(self) -> None:
        code = code_only(CONTRACT)
        self.assertIn("from app.tiny_image_embed import load_trunk", code)
        self.assertIn('modality == "image_embed"', code)

    def test_executor_uses_same_loader(self) -> None:
        code = code_only(INFER_EMBED)
        self.assertIn("load_trunk", code)


class TestSharedPreprocess(unittest.TestCase):
    def test_single_image_tensor_helper(self) -> None:
        """분류와 임베딩이 **같은** 전처리 함수를 쓴다 (D3)."""
        self.assertIn("def load_image_tensor", code_only(INFER))
        self.assertIn("load_image_tensor", code_only(INFER_EMBED))

    def test_pixel_limit_is_in_shared_helper(self) -> None:
        """픽셀 상한이 공용 함수에 있어야 한다 — 임베딩만 상한이 없으면 그쪽으로 들어온다."""
        code = code_only(INFER)
        i = code.index("def load_image_tensor")
        body = code[i:i + 900]
        self.assertIn("MAX_INPUT_PIXELS", body)


class TestDispatch(unittest.TestCase):
    def test_modality_registered(self) -> None:
        src = (ROOT / "apps" / "node" / "app" / "tiny_cnn.py").read_text(encoding="utf-8")
        block = src.split("ARCH_MODALITY")[1].split("}")[0]
        self.assertIn('"TinyEuroSATEmbed": "image_embed"', block)

    def test_core_knows_the_arch(self) -> None:
        code = code_only(ROOT / "apps" / "core" / "app" / "gate.py")
        self.assertIn("TinyEuroSATEmbed", code)


class TestNoSimilarityClaim(unittest.TestCase):
    def test_source_disclaims(self) -> None:
        src = EMBED.read_text(encoding="utf-8")
        self.assertIn("의미적 유사도", src)

    def test_demo_disclaims(self) -> None:
        demo = (ROOT / "scripts" / "image_embed_demo.sh").read_text(encoding="utf-8")
        self.assertIn("주장하지 않는다", demo)


if __name__ == "__main__":
    unittest.main()
