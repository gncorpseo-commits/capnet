r"""배치 B 이후의 새 검사 파일이 **머리말 규약**을 따르는가 (배치 C #128 · `#215` 계열).

## 왜 있는가

검사 파일의 docstring 이 곧 문서다. 「왜 있는가 · 실측 · 재현」이 빠진 검사는 숫자를 다시 낼 길이 없고,
skip 사유가 자유 문장이면 `test_skip_reasons` 의 허가제 밖으로 샌다. 규약은 `docs/guide/testing.md` §4.8.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| 모듈 docstring 없는 검사 | **0** / 121 |
| 「배치 B/C/D」·「G 라운드」·「큐 #N」·「최종 G」를 말하는 새 검사 | 전부 `## 재현` + 자기 모듈을 부르는 `python3 -m unittest` 줄 (G1 에서 표식을 넓혔다) |
| skip 사유 | `test_skip_reasons.ALLOWED` 가 본다 (여기서 다시 안 센다) |

## 재현

```bash
python3 -m unittest tests.test_new_tests_follow_the_header_convention
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
# G1 (2026-09-07): 「배치 X」만 보면 「큐 #N」·「최종」만 적은 새 검사가 규약을 비켜간다 — 표식을 넓혔다.
NEW_MARK = re.compile(r"배치 [BCDR]|G 라운드|배치 B 뒤|큐 #(?:7\d|8\d|9\d|1\d\d)\b|최종 G|G[1-5] ")   # 큐 #71(배치 B) 부터 · 배치 R


def _docstrings() -> dict[str, str]:
    return {p.stem: (ast.get_docstring(ast.parse(p.read_text(encoding="utf-8"))) or "") for p in sorted(TESTS.glob("test_*.py"))}


class TestHeaders(unittest.TestCase):
    def test_every_module_has_a_docstring(self) -> None:
        docs = _docstrings()
        self.assertGreaterEqual(len(docs), 100)
        self.assertEqual([], [m for m, d in docs.items() if len(d.strip()) < 40], "머리말이 없거나 한 줄뿐인 검사")

    def test_new_modules_carry_why_and_reproduce(self) -> None:
        new = {m: d for m, d in _docstrings().items() if NEW_MARK.search(d)}
        self.assertGreaterEqual(len(new), 30, sorted(new))
        bad = []
        for m, d in new.items():
            if "## 재현" not in d:
                bad.append(f"{m}: 재현 절 없음")
            elif f"python3 -m unittest tests.{m}" not in d:
                bad.append(f"{m}: 재현 명령이 자기 모듈을 안 부른다")
            if "왜 있는가" not in d and "실측" not in d:
                bad.append(f"{m}: 왜 있는가/실측 없음")
        self.assertEqual([], bad, "\n  ".join(bad))

    def test_the_guide_states_the_convention(self) -> None:
        self.assertIn("## 4.8 새 검사 파일의 머리말 규약", (ROOT / "docs" / "guide" / "testing.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
