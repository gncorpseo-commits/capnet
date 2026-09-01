"""`scripts/pass_rate.sh` 가 **이미지 후보만** 고르는가.

## 왜 있는가

**실제로 깨져 있었다 (2026-09-02).** 이 스크립트는 Node health 의 non-placeholder
가중치를 **전부** `image.classify@1` 후보로 봤다. 규칙 기반 실행기가 들어오면서
`rule_extract.safetensors`(파라미터 0 · `forward` 없음)까지 집어 이렇게 죽었다:

    NotImplementedError: Module [RuleTextExtract] is missing the required "forward" function
    score_gate failed rc=1 (rule_extract.safetensors)

**카탈로그가 자라면서 도구의 가정이 조용히 깨진 것**이다. 다행히 크래시라 시끄러웠지만,
분모(통과율의 분모)가 잘못 잡히는 쪽으로 어긋났으면 **숫자만 틀린 채 통과**했을 것이다.

## 무엇을 고정하나

1. **손으로 센 arch 목록을 두지 않는다** — 정본은 `apps/node/app/tiny_cnn.py` 의
   `ARCH_MODALITY` 이고 스크립트가 거기서 뽑는다. 새 이미지 arch 는 저절로 따라온다
2. **뺀 것을 말한다** — 조용히 분모를 줄이면 숫자가 달라진 것을 아무도 모른다
3. `"image_embed"` 를 `"image"` 로 잘못 집지 않는다

## 무엇을 안 보나

**개수를 못박지 않는다.** 후보 가중치는 학습을 돌릴 때마다 는다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pass_rate.sh"
TINY = ROOT / "apps" / "node" / "app" / "tiny_cnn.py"

# 스크립트가 쓰는 것과 **같은** 추출식. 두 벌이 되지 않게 여기서도 소스를 본다.
MODALITY_BLOCK = re.compile(r"ARCH_MODALITY:[^{]*\{(.*?)\n\}", re.S)
IMAGE_ARCH = re.compile(r'"(\w+)"\s*:\s*"image"')


def image_arches() -> set[str]:
    m = MODALITY_BLOCK.search(TINY.read_text(encoding="utf-8"))
    assert m is not None, "ARCH_MODALITY 를 못 읽었다"
    return set(IMAGE_ARCH.findall(m.group(1)))


class TestCandidateFilter(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_derives_from_arch_modality(self) -> None:
        """손으로 센 목록을 두면 다음 이미지 arch 에서 또 어긋난다."""
        self.assertIn("ARCH_MODALITY", self.text, "정본에서 뽑지 않는다")
        self.assertIn("tiny_cnn.py", self.text)

    def test_does_not_hardcode_arch_names(self) -> None:
        """`TinyEuroSAT` 를 스크립트에 적어 두면 그 순간 정본이 둘이 된다."""
        for name in sorted(image_arches()):
            self.assertNotIn(
                f'"{name}"', self.text, f"arch 이름을 스크립트에 박아 넣었다: {name}"
            )

    def test_says_what_it_skipped(self) -> None:
        """조용히 분모를 줄이면 숫자가 달라진 것을 아무도 모른다."""
        self.assertIn("뺀 것", self.text, "무엇을 뺐는지 안 말한다")

    def test_image_embed_is_not_matched_as_image(self) -> None:
        """`"image_embed"` 를 `"image"` 로 집으면 분모가 틀린다."""
        arches = image_arches()
        self.assertIn("TinyEuroSAT", arches)
        self.assertNotIn("TinyEuroSATEmbed", arches, "image_embed 를 image 로 집었다")

    def test_probe_actually_finds_things(self) -> None:
        self.assertGreater(len(image_arches()), 1, sorted(image_arches()))


if __name__ == "__main__":
    unittest.main()
