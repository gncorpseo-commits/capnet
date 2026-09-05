r"""`.ps1` 만 있는 경로를 **WSL 문서가 「돌린다」고 적지 않는가** (배치 B #97 · `#206`/`#240` 옆).

## 왜 있는가

`#206`·`#240` 은 런북이 없는 PowerShell 쌍둥이를 부르던 것을 잡았다. 반대 방향도 있다 — WSL 에서
따라 하는 안내가 `.ps1` 만 있는 스크립트를 셸처럼 부르면 그 줄은 리눅스에서 안 돈다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `.sh` 쌍둥이가 없는 `.ps1` | **1** — `smoke_w1.ps1` |
| WSL 안내(`docs/guide/*.md` · `CONTRIBUTING.md`)의 `pwsh`·`.ps1` 지시 | **0** |
| `smoke_w1` 을 부르는 문서 | README 표 1행 — 확장자 `.ps1` 을 드러내 적는다 |
| 문서가 부르는 `scripts\X.ps1` 중 실재하지 않는 것 | **0** (런북 · 제출 패킷 · README) |

## 재현

```bash
python3 -m unittest tests.test_ps1_only_paths_are_labelled
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
WSL_GUIDES = sorted((ROOT / "docs" / "guide").glob("*.md")) + [ROOT / "CONTRIBUTING.md"]
PS_DOCS = [ROOT / "README.md", ROOT / "docs" / "ops" / "shoot-day-runbook.md",
           ROOT / "docs" / "ops" / "contest-submission-pack.md", ROOT / "docs" / "ops" / "contest-submission-checklist.md"]


def _ps1_only() -> list[str]:
    return sorted(p.stem for p in SCRIPTS.glob("*.ps1") if not (SCRIPTS / f"{p.stem}.sh").is_file())


class TestTheLonelyPs1IsKnownAndLabelled(unittest.TestCase):
    def test_exactly_smoke_w1(self) -> None:
        self.assertEqual(["smoke_w1"], _ps1_only())

    def test_every_mention_shows_the_extension(self) -> None:
        """`smoke_w1` 이라고만 적으면 셸 스크립트처럼 읽힌다 — `.ps1` 을 붙여 적는다."""
        seen = 0
        for doc in PS_DOCS + WSL_GUIDES:
            for i, ln in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
                for name in _ps1_only():
                    if name in ln:
                        seen += 1
                        with self.subTest(site=f"{doc.name}:{i}"):
                            self.assertIn(f"{name}.ps1", ln, f"{doc.name}:{i} 가 {name} 을 확장자 없이 부른다")
        self.assertGreaterEqual(seen, 1, "smoke_w1 을 부르는 문서를 하나도 못 찾았다")


class TestWslGuidesNeverAskForPowershell(unittest.TestCase):
    def test_no_pwsh_or_ps1_instruction(self) -> None:
        self.assertGreaterEqual(len(WSL_GUIDES), 5, [p.name for p in WSL_GUIDES])
        for doc in WSL_GUIDES:
            with self.subTest(doc=doc.name):
                body = doc.read_text(encoding="utf-8")
                self.assertNotRegex(body, r"pwsh|powershell|\.ps1\b", f"{doc.name} 이 PowerShell 을 부른다 — WSL 안내다")


class TestEveryCalledPs1Exists(unittest.TestCase):
    def test_no_phantom_twin(self) -> None:
        called = set()
        for doc in PS_DOCS:
            called |= set(re.findall(r"scripts[\\/]([\w]+)\.ps1", doc.read_text(encoding="utf-8")))
        self.assertGreaterEqual(len(called), 3, called)
        missing = sorted(n for n in called if not (SCRIPTS / f"{n}.ps1").is_file())
        self.assertEqual([], missing, f"문서가 부르는데 없는 .ps1: {missing}")


if __name__ == "__main__":
    unittest.main()
