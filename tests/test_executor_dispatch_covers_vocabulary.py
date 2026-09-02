"""어휘의 **모든 모달리티에 실행기 분기가 있는가.**

## 왜 있는가

Node 의 실행기 선택이 이렇게 끝났다 (`main._run`):

    elif modality == "series":
        ...
    elif modality in ("text", "text_embed"):
        ...
    else:
        label, confidence = predict_image(...)      # ← 이름 없는 것은 전부 여기로

**기본값이 「이미지 분류기」였다.** 오늘은 `else` 로 가는 것이 `image` 하나뿐이라
맞다 (아래 실측). 문제는 **자라는 방향**이다 — `ARCH_MODALITY` 에 새 모달리티를
더하고 위에 분기를 안 만들면 그 능력이 **조용히 이미지 분류기로 돈다.**
arch 는 등록돼 있으니 `build_model` 도 통과한다.

[#189](https://github.com/gncorpseo-commits/capnet/pull/189)가 **입력 선택**의
같은 모양을 고쳤다 (포함식 → 폴백 목록). 이건 그 **실행기 쪽 짝**이다.

## 무엇을 바꿨나

`else` 를 **`elif modality == "image"`** 로 이름 붙이고, 남는 `else` 는
**501** 로 「실행기가 없다」고 말한다. `arch=None` 인 legacy Agent 는
`_modality_of` 가 `"image"` 로 떨어뜨리므로 **종전 동작 그대로**다.

## 무엇을 고정하나

1. `ARCH_MODALITY` 의 **모든 값**이 실행기 분기에 **이름으로** 나온다
2. 이름 없는 모달리티는 `predict_image` 로 안 가고 **거절**된다
3. 분기가 부르는 모듈이 실재한다

## 무엇을 안 보나

**개수를 못박지 않는다.** 모달리티는 는다 — 보는 것은 **어휘와 분기가 같은가**다.
`torch`·`fastapi` 없이 돌아야 해서 **소스를 파싱한다**
(`tests/test_pass_rate_script.py` 가 같은 이유로 같은 방식을 쓴다).
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"
TINY = ROOT / "apps" / "node" / "app" / "tiny_cnn.py"

MODALITY_BLOCK = re.compile(r"ARCH_MODALITY:[^{]*\{(.*?)\n\}", re.S)
ARCH_TO_MODALITY = re.compile(r'"(\w+)"\s*:\s*"(\w+)"')
BRANCH = re.compile(r'modality (?:==|in) (\([^)]*\)|"\w+")')


def vocabulary() -> set[str]:
    m = MODALITY_BLOCK.search(TINY.read_text(encoding="utf-8"))
    assert m is not None, "ARCH_MODALITY 를 못 읽었다"
    return {v for _a, v in ARCH_TO_MODALITY.findall(m.group(1))}


_HEAD = "from app.infer import ResourceLimitExceeded"
_TAIL = "except ResourceLimitExceeded"


def _slice(src: str) -> str:
    assert _HEAD in src and _TAIL in src, "실행기 구간을 못 찾았다 — 이 검사도 고친다"
    return src.split(_HEAD, 1)[1].split(_TAIL, 1)[0]


def dispatch_segment() -> str:
    """`_run` 의 실행기 선택 구간 (원문)."""
    return _slice(NODE_MAIN.read_text(encoding="utf-8"))


def dispatch_code() -> str:
    """같은 구간에서 **주석을 뺀 것.**

    주석에는 「예전에는 `predict_image` 로 떨어졌다」 같은 **설명**이 적힌다.
    그걸 위반으로 잡으면 **설명을 지워야 통과하는 검사**가 된다 — 이 저장소에서
    다섯 번 난 사고다 (`tests/_srcguard.py`). 실제로 이 파일도 처음에 그렇게 걸렸다.
    """
    return _slice(code_only(NODE_MAIN))


def dispatched() -> set[str]:
    """실행기 분기가 **이름으로** 잡는 모달리티."""
    out: set[str] = set()
    for group in BRANCH.findall(dispatch_code()):
        out |= set(re.findall(r'"(\w+)"', group))
    return out


class TestEveryModalityHasAnExecutor(unittest.TestCase):
    def test_vocabulary_is_fully_dispatched(self) -> None:
        """**여기가 핵심이다.** 이름 없는 모달리티는 조용히 이미지로 간다."""
        missing = sorted(vocabulary() - dispatched())
        self.assertEqual(
            missing, [],
            f"실행기 분기에 이름이 없는 모달리티 {missing} — `else` 로 떨어진다",
        )

    def test_no_ghost_branches(self) -> None:
        """어휘에 없는 모달리티를 분기가 잡고 있으면 죽은 코드다."""
        ghosts = sorted(dispatched() - vocabulary())
        self.assertEqual(ghosts, [], f"ARCH_MODALITY 에 없는 분기: {ghosts}")

    def test_probe_actually_read_both_sides(self) -> None:
        """0개끼리 비교하며 통과하는 상태를 막는다. **개수는 못박지 않는다.**"""
        self.assertGreater(len(vocabulary()), 5, sorted(vocabulary()))
        self.assertGreater(len(dispatched()), 5, sorted(dispatched()))


class TestUnknownModalityIsRefused(unittest.TestCase):
    def test_image_is_named_not_default(self) -> None:
        """`image` 가 `else` 에 숨어 있으면 새 모달리티가 그 자리를 물려받는다."""
        self.assertIn('modality == "image"', dispatch_code())

    def test_fallthrough_refuses_instead_of_guessing(self) -> None:
        seg = dispatch_code()
        tail = seg[seg.rindex("else:"):]
        self.assertNotIn("predict_image", tail, "남는 else 가 아직 이미지로 떨어진다")
        self.assertIn("실행기가", tail, "실행기가 없다고 말하지 않는다")
        self.assertIn("501", tail, "거절 상태 코드가 없다")


class TestBranchesPointAtRealModules(unittest.TestCase):
    def test_imported_executors_exist(self) -> None:
        seg = dispatch_code()
        mods = sorted(set(re.findall(r"from (app\.infer\w*) import", seg)))
        self.assertGreater(len(mods), 3, mods)
        for m in mods:
            with self.subTest(module=m):
                path = ROOT / "apps" / "node" / (m.replace(".", "/") + ".py")
                self.assertTrue(path.is_file(), f"{m} 가 없다 ({path})")


if __name__ == "__main__":
    unittest.main()
