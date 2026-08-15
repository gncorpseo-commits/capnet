"""텍스트 모달리티 — 특징·전처리·디스패치를 고정한다 (단계 5).

## 왜 있는가

`text.classify` 실행기를 붙이면서 **모달리티 디스패치**가 생겼다. 이미지 하나만 돌 때는
없던 갈림길이고, 갈림길은 조용히 잘못 든다. 여기서 보는 것은 넷이다.

1. **특징 추출이 실행마다 같은가** — 파이썬 `hash()` 를 쓰면 `PYTHONHASHSEED` 때문에
   실행마다 달라져서 **학습한 모델을 다음 실행에서 못 쓴다.** 조용히 정확도만 떨어진다
2. **학습과 추론이 같은 함수를 쓰는가** — 두 벌이면 한쪽만 고쳐진다 (D3 의 이유)
3. **전처리 선언이 망가지면 던지는가** — 조용히 기본값으로 떨어지면
   「선언한 대로 돌았다」가 거짓이 된다
4. **디스패치 정본이 `arch` 인가** — Core 가 말한 값이고 게이트가 그 값으로 승인했다 (I1)

## 한계

torch 가 필요한 것(모델 로드·실추론)은 여기서 돌리지 않는다 — 이 리포의 단위 잡은
의존성 0 이다. 그쪽은 `scripts/text_demo.sh` 가 계약 게이트로 실측한다.
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402


def _purge() -> None:
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]


class NodeApp(unittest.TestCase):
    """`apps/node` 의 `app` 패키지를 검사 동안만 올린다 (core 와 이름이 겹친다)."""

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


class TestFeatureStability(NodeApp):
    def test_same_input_same_vector(self) -> None:
        f = self.mod("text_features").features
        self.assertEqual(f("hello@example.com"), f("hello@example.com"))

    def test_hashing_is_pinned(self) -> None:
        """해시 결과를 **기준값으로 고정**한다.

        처음에는 `PYTHONHASHSEED` 를 바꿔 가며 하위 프로세스로 확인했는데,
        **그 검사가 믿을 수 없었다** — 변이를 넣어도 통과하는 경우가 있었다
        (하위 프로세스가 낡은 `__pycache__` 를 집었다). 불안정한 가드는 없느니만 못하다.

        그래서 값을 못박는다. 버킷 함수를 파이썬 `hash()` 로 바꾸거나 n-gram·차원을
        건드리면 **결정적으로** 여기서 걸린다.
        """
        tf = self.mod("text_features")
        self.assertEqual(tf.HASH_DIM, 4096)
        self.assertEqual(tf.NGRAMS, (2, 3))
        self.assertEqual(tf._bucket("ab"), 136)
        self.assertEqual(tf._bucket("hello@example.com"), 3379)
        v = tf.features("hello@example.com")
        self.assertEqual(sum(1 for x in v if x), 35)
        self.assertAlmostEqual(sum(v), 5.916079783099615, places=9)

    def test_bucket_does_not_use_builtin_hash(self) -> None:
        """`hash()` 는 실행마다 값이 달라진다 — 학습한 모델을 다음 실행에서 못 쓰게 된다.

        기준값 검사가 이미 잡지만, **왜 안 되는지**를 소스에서도 못박아 둔다.
        """
        code = code_only(ROOT / "apps" / "node" / "app" / "text_features.py")
        body = code.split("def _bucket")[1].split("\ndef ")[0]
        self.assertNotIn("hash(", body.replace("hashlib.", ""))
        self.assertIn("blake2b", body)

    def test_different_inputs_differ(self) -> None:
        f = self.mod("text_features").features
        self.assertNotEqual(f("hello@example.com"), f("192.168.0.1"))

    def test_normalize_applies_max_chars(self) -> None:
        n = self.mod("text_features").normalize
        self.assertEqual(n("abcdef", max_chars=3), "abc")

    def test_vector_is_unit_norm(self) -> None:
        f = self.mod("text_features").features
        v = f("https://example.org/a/b")
        self.assertAlmostEqual(sum(x * x for x in v) ** 0.5, 1.0, places=6)


class TestTextPreprocess(NodeApp):
    def test_defaults(self) -> None:
        r = self.mod("preprocess").resolve_text_preprocess
        self.assertEqual(r(None), ("utf-8", "NFC", 8000))

    def test_declared_is_applied(self) -> None:
        r = self.mod("preprocess").resolve_text_preprocess
        self.assertEqual(
            r({"encoding": "utf-8", "normalize": "NFKC", "max_chars": 10}),
            ("utf-8", "NFKC", 10),
        )

    def test_bad_normalize_raises(self) -> None:
        r = self.mod("preprocess").resolve_text_preprocess
        with self.assertRaises(ValueError):
            r({"normalize": "NFZ"})

    def test_bad_max_chars_raises(self) -> None:
        r = self.mod("preprocess").resolve_text_preprocess
        with self.assertRaises(ValueError):
            r({"max_chars": 0})


class TestModalityDispatch(NodeApp):
    def test_registry_and_modality_cover_same_archs(self) -> None:
        """빌더가 있는 arch 는 모달리티도 있어야 한다 — 한쪽만 늘면 조용히 image 로 간다."""
        src = (ROOT / "apps" / "node" / "app" / "tiny_cnn.py").read_text(encoding="utf-8")
        import re

        reg = set(re.findall(r'"(\w+)":', src.split("ARCH_REGISTRY")[1].split("}")[0]))
        mod = set(re.findall(r'"(\w+)":', src.split("ARCH_MODALITY")[1].split("}")[0]))
        self.assertEqual(reg, mod, "ARCH_REGISTRY 와 ARCH_MODALITY 가 다르다")

    def test_text_arch_is_text(self) -> None:
        src = (ROOT / "apps" / "node" / "app" / "tiny_cnn.py").read_text(encoding="utf-8")
        block = src.split("ARCH_MODALITY")[1].split("}")[0]
        self.assertIn('"TinyTextClassifier": "text"', block)

    def test_run_dispatches_on_arch(self) -> None:
        """실행 경로가 **arch 로** 갈리는가. 전처리 어휘로 짐작하지 않는다 (I1)."""
        code = code_only(ROOT / "apps" / "node" / "app" / "main.py")
        self.assertIn("_modality_of(arch)", code)
        self.assertIn("from app.infer_text import", code)

    def test_text_has_no_local_golden_fallback(self) -> None:
        """텍스트에는 `caseId` → 로컬 골든 폴백이 없다 — 입력은 Core 중개로만 (D8′)."""
        src = (ROOT / "apps" / "node" / "app" / "main.py").read_text(encoding="utf-8")
        self.assertIn("text 실행에는 Core 가 중개한 입력이 필요하다", src)


class TestNoQualityClaim(NodeApp):
    """`quality_profile='none'` 인 능력에 품질 주장을 붙이지 않는다."""

    def test_meta_records_but_disclaims(self) -> None:
        import json

        meta = json.loads(
            (ROOT / "apps" / "node" / "weights" / "text_struct_scratch.meta.json")
            .read_text(encoding="utf-8")
        )
        self.assertIs(meta["pretrained"], False)
        self.assertIn("holdout_accuracy", meta)
        self.assertIn("품질 보장이 아니다", meta["note"])

    def test_dataset_is_self_generated(self) -> None:
        """외부 말뭉치를 쓰지 않았다 — 절대규칙 6 · 2차 라이선스 검증."""
        import json

        meta = json.loads(
            (ROOT / "apps" / "node" / "weights" / "text_struct_scratch.meta.json")
            .read_text(encoding="utf-8")
        )
        self.assertIn("규칙 생성", meta["dataset"])


if __name__ == "__main__":
    unittest.main()
