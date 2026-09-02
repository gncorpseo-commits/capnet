"""**모르는 모달리티가 데모 데이터로 떨어지지 않는가.**

## 왜 있는가

`main._run` 이 「Core 중개 입력이 없을 때」를 이렇게 갈랐다:

    elif modality in (
        "text", "text_embed", "series", "table_extract", "text_ner", "text_extract",
        "text_rank", "text_pii",
    ):
        raise HTTPException(400, "… Core 가 중개한 입력이 필요하다")
    else:
        cid = _case_id(input_ref)          # ← 로컬 골든셋(EuroSAT 이미지)으로 떨어진다

**포함식이라 기본값이 「골든 폴백」이었다.** 오늘 그 목록은 정확히
`ARCH_MODALITY` 값에서 이미지 둘을 뺀 것이라 **맞다.** 문제는 자라는 방향이다:

| 어긋나는 길 | 결과 |
|---|---|
| `ARCH_MODALITY` 에 새 모달리티를 더하고 이 목록을 안 고친다 | **골든 폴백** |
| DB `agent_arch` 에는 있는데 `ARCH_MODALITY` 에 없는 arch | `_modality_of` 가 `"image"` 로 → **골든 폴백** |

둘 다 **사용자 입력 대신 데모 이미지가 돌고, 그럴듯한 결과가 나온다** —
[#154](https://github.com/gncorpseo-commits/capnet/pull/154)(빈 첨부 → 데모 데이터)와
같은 모양이고, 손으로 적은 목록이 카탈로그를 못 따라간
[#171](https://github.com/gncorpseo-commits/capnet/pull/171)과 같은 자리다.

**아직 그런 일은 없다** — 아래 `test_todays_vocabulary_is_covered` 가 그것을 잰다.
**나기 전에 막는다** (#169 와 같은 말).

## 무엇을 고정하나

1. `requires_core_input` 은 **모르는 모달리티에 True** — 거절이 기본이다
2. 폴백을 가진 것은 **이미지 계열뿐**이다 (골든셋이 EuroSAT 이미지라서)
3. 폴백 목록에 `ARCH_MODALITY` 에 없는 유령이 없다
4. `main.py` 가 **옛 포함식으로 되돌아가지 않았다**

## 무엇을 안 보나

**개수를 못박지 않는다.** 모달리티도 이미지 계열도 늘 수 있다.
`ARCH_MODALITY` 는 `torch` 를 끌고 오는 `tiny_cnn.py` 에 있어 **정규식으로 읽는다** —
`tests/test_pass_rate_script.py` 가 같은 이유로 같은 방식을 쓴다.
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TINY = ROOT / "apps" / "node" / "app" / "tiny_cnn.py"
NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"
MODALITY = ROOT / "apps" / "node" / "app" / "modality.py"

MODALITY_BLOCK = re.compile(r"ARCH_MODALITY:[^{]*\{(.*?)\n\}", re.S)
ARCH_TO_MODALITY = re.compile(r'"(\w+)"\s*:\s*"(\w+)"')


def _load_modality():
    """`app.modality` 는 표준 라이브러리만 쓴다 — 그래서 그냥 불러온다."""
    spec = importlib.util.spec_from_file_location("_capnet_modality_probe", MODALITY)
    assert spec and spec.loader, MODALITY
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


modality = _load_modality()


def vocabulary() -> set[str]:
    """`ARCH_MODALITY` 의 **값** 집합 = 지금 있는 모달리티 어휘."""
    m = MODALITY_BLOCK.search(TINY.read_text(encoding="utf-8"))
    assert m is not None, "ARCH_MODALITY 를 못 읽었다"
    return {v for _arch, v in ARCH_TO_MODALITY.findall(m.group(1))}


class TestUnknownIsRefused(unittest.TestCase):
    def test_unknown_modality_requires_core_input(self) -> None:
        """**여기가 핵심이다.** 모르는 것은 데모 데이터로 떨어지지 않는다."""
        for unknown in ("audio", "video", "text_summarize", "", "image_but_not_really"):
            with self.subTest(modality=unknown):
                self.assertTrue(
                    modality.requires_core_input(unknown),
                    f"{unknown!r} 이 골든 폴백으로 간다 — 데모 데이터가 대신 돈다",
                )

    def test_image_modalities_keep_the_fallback(self) -> None:
        """이미지 계열은 종전대로 `caseId` → 로컬 골든셋 (D22 · 동작 변경 0)."""
        for name in ("image", "image_embed"):
            with self.subTest(modality=name):
                self.assertFalse(modality.requires_core_input(name))

    def test_text_modalities_still_require_core_input(self) -> None:
        """옛 포함식이 막던 것을 그대로 막는가 (동작 변경 0)."""
        for name in (
            "text", "text_embed", "series", "table_extract",
            "text_ner", "text_extract", "text_rank", "text_pii",
        ):
            with self.subTest(modality=name):
                self.assertTrue(modality.requires_core_input(name))


class TestFallbackSetIsJustified(unittest.TestCase):
    def test_fallback_is_image_only(self) -> None:
        """골든셋은 EuroSAT **이미지**다 — 폴백은 그걸 먹을 수 있는 것뿐이어야 한다."""
        for name in modality.GOLDEN_FALLBACK_MODALITIES:
            with self.subTest(modality=name):
                self.assertTrue(
                    name.startswith("image"),
                    f"{name!r} 에 이미지 골든셋 폴백을 준 근거가 없다",
                )

    def test_no_ghost_entries(self) -> None:
        """어휘에 없는 이름이 폴백 목록에 남아 있으면 아무도 모른다."""
        ghosts = sorted(modality.GOLDEN_FALLBACK_MODALITIES - vocabulary())
        self.assertEqual(ghosts, [], f"ARCH_MODALITY 에 없는 폴백 항목: {ghosts}")

    def test_probe_actually_read_the_vocabulary(self) -> None:
        """0개를 훑으며 통과하는 상태를 막는다. **개수는 못박지 않는다.**"""
        self.assertGreater(len(vocabulary()), 5, sorted(vocabulary()))


class TestTodaysVocabularyIsCovered(unittest.TestCase):
    def test_every_modality_is_decided(self) -> None:
        """어휘의 모든 값이 둘 중 하나로 확실히 간다 — 「모르겠다」가 없다."""
        for name in sorted(vocabulary()):
            with self.subTest(modality=name):
                self.assertIsInstance(modality.requires_core_input(name), bool)

    def test_nothing_leaks_to_the_golden_path_by_accident(self) -> None:
        """폴백으로 가는 것은 **선언된 것뿐**이다 — 오늘 실측."""
        leaking = {n for n in vocabulary() if not modality.requires_core_input(n)}
        self.assertEqual(
            leaking, set(modality.GOLDEN_FALLBACK_MODALITIES),
            "선언하지 않은 모달리티가 골든 폴백으로 간다",
        )


class TestMainUsesIt(unittest.TestCase):
    def test_node_main_calls_the_helper(self) -> None:
        body = NODE_MAIN.read_text(encoding="utf-8")
        self.assertIn("requires_core_input(modality)", body, "Node main 이 안 부른다")

    def test_old_inclusion_list_is_gone(self) -> None:
        """포함식이 남아 있으면 기본값이 다시 「골든 폴백」이 된다.

        **`elif modality in (...)` 자체를 금지하지 않는다** — 아래 실행기 분기
        (`elif modality in ("text", "text_embed")`)는 정상이다. 지운 목록에만
        있던 조합을 본다. (넓게 잡았다가 그 정상 분기가 걸렸다.)
        """
        body = NODE_MAIN.read_text(encoding="utf-8")
        self.assertNotIn(
            '"series", "table_extract"', body,
            "옛 포함식(Core 입력을 요구하는 모달리티 나열)이 남아 있다",
        )


if __name__ == "__main__":
    unittest.main()
