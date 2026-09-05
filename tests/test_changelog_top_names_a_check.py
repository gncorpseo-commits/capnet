r"""CHANGELOG **선두 주장이 실재하는 검사를 지목하는가** (큐 #69 · G4).

## 왜 있는가

`measured-claims` 규율은 「**측정 숫자는 재현 명령 없이 쓰지 않는다**」다. CHANGELOG 는
그 규율이 가장 자주 깨지는 자리다 — 항목마다 숫자가 있고, 그 숫자를 **다시 낼 방법**은
쓰는 사람만 안다.

G4 는 그것을 한 줄로 좁힌다: **선두 항목이 테스트와 같은 말을 하는가.**

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| CHANGELOG 항목 | **186** |
| 최근 12개 중 **재현 대상을 지목한 것** | **12** |
| 지목한 이름 중 **실재하지 않는 것** | **0** |

## 무엇을 고정하나

1. **선두 항목**이 `tests.<모듈>` · `tests/<파일>` · `scripts/<도구>` 중 하나를 지목한다
2. 최근 열두 항목이 지목한 이름이 **전부 실재한다** (오타가 나면 재현이 거짓이 된다)
3. 선두 항목에 **날짜**가 있다

## 왜 열둘만 보나

옛 항목은 이 규율이 서기 전에 쓰였다. **거슬러 올라가 고쳐 쓰지 않는다** — 그건
`#238` 이 체크리스트에서 하지 않기로 한 것과 같다. 규율은 **지금부터** 지킨다.

## 무엇을 안 보나

- **주장과 검사가 같은 것을 말하는가.** 그건 사람이 읽어야 한다. 여기는 「지목했는가 ·
  그것이 있는가」만 본다 — 없는 것을 가리키는 재현 명령은 **없는 것보다 나쁘다**
- 숫자 자체. 다시 내는 것은 그 명령의 몫이다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "docs" / "history" / "CHANGELOG.md"

RECENT = 12
DATE = re.compile(r"—\s*(\d{4}-\d{2}-\d{2})\s*$")
# `tests.모듈` · `tests/파일.py` · `scripts/도구`
TEST_MODULE = re.compile(r"tests\.(test_[a-z0-9_]+)")
TEST_FILE = re.compile(r"tests/(test_[a-z0-9_]+\.py)")
SCRIPT = re.compile(r"scripts/([a-z0-9_]+\.(?:sh|py))")
CAPREQ = re.compile(r"discover -s capreq/tests")


def _entries() -> list[tuple[str, str]]:
    """`(제목, 본문)` — 최신이 앞."""
    body = CHANGELOG.read_text(encoding="utf-8")
    out = []
    for chunk in re.split(r"^## ", body, flags=re.M)[1:]:
        lines = chunk.splitlines()
        out.append((lines[0].strip(), chunk))
    return out


def _named(text: str) -> set[str]:
    """그 항목이 지목한 **재현 대상**."""
    found = {f"tests/{m}.py" for m in TEST_MODULE.findall(text)}
    found |= {f"tests/{m}" for m in TEST_FILE.findall(text)}
    found |= {f"scripts/{m}" for m in SCRIPT.findall(text)}
    if CAPREQ.search(text):
        found.add("capreq/tests")
    return found


class TestTheTopEntryPointsSomewhere(unittest.TestCase):
    def test_it_names_a_reproduction_target(self) -> None:
        """**여기가 핵심이다.** 숫자만 있고 다시 낼 길이 없으면 주장이 아니다."""
        entries = _entries()
        self.assertTrue(entries, "CHANGELOG 항목을 하나도 못 읽었다")
        title, text = entries[0]
        self.assertTrue(_named(text), f"선두 항목이 재현 대상을 안 지목한다: {title}")

    def test_it_has_a_date(self) -> None:
        title, _ = _entries()[0]
        self.assertRegex(title, DATE.pattern, f"선두 항목에 날짜가 없다: {title}")


class TestNamedTargetsExist(unittest.TestCase):
    """없는 것을 가리키는 재현 명령은 **없는 것보다 나쁘다**."""

    def test_recent_entries_name_real_files(self) -> None:
        entries = _entries()[:RECENT]
        self.assertEqual(RECENT, len(entries), f"항목이 {len(entries)}개뿐이다")
        missing = []
        for title, text in entries:
            for name in sorted(_named(text)):
                if not (ROOT / name).exists():
                    missing.append(f"{title[:40]} → {name}")
        self.assertEqual([], missing, "없는 것을 재현 대상으로 적었다: " + "; ".join(missing))

    def test_every_recent_entry_names_something(self) -> None:
        bare = [t for t, x in _entries()[:RECENT] if not _named(x)]
        self.assertEqual([], bare, f"재현 대상이 없는 최근 항목: {bare}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_entries_are_read(self) -> None:
        self.assertGreaterEqual(len(_entries()), 100, f"{len(_entries())}개만 읽었다")

    def test_the_extractor_discriminates(self) -> None:
        """아무 이름이나 잡거나 하나도 못 잡으면 위 검사가 공허하다."""
        self.assertEqual({"tests/test_x.py"}, _named("재현: `python3 -m unittest tests.test_x`"))
        self.assertEqual({"scripts/run_tests.sh"}, _named("`bash scripts/run_tests.sh`"))
        self.assertEqual(set(), _named("그냥 문장이다. 숫자는 42."))
        self.assertIn("capreq/tests", _named("`… discover -s capreq/tests -p \"test_*.py\"`"))


if __name__ == "__main__":
    unittest.main()
