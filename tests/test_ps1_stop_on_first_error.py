r"""`.ps1` 전부가 **첫 명령 전에** `$ErrorActionPreference = "Stop"` 을 둔다 (배치 D #132 · `#206` 형제).

## 왜 있는가

PowerShell 은 기본이 `Continue` 다 — 실패한 명령 뒤로 그냥 흐른다. `.sh` 쪽은 `test_scripts_set_errexit` 가 `set -euo pipefail`
을 보는데 `.ps1` 은 `generate_sbom.ps1` 하나만 봤다(#86). `pwsh` 가 이 환경에 없어 **소스만** 본다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `scripts/*.ps1` | 11 |
| `$ErrorActionPreference = "Stop"` 있음 | 11/11 |
| 그 줄이 첫 명령(주석·빈 줄·`param(` 제외) 앞에 옴 | 11/11 |
| `-ErrorAction SilentlyContinue` (탐색용 `Get-Command`·`Test-Path` 류) | 있는 곳은 그 줄에 `Get-Command`/`Test-Path`/`Get-Item` 만 |

## 재현

```bash
python3 -m unittest tests.test_ps1_stop_on_first_error
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PS1 = sorted((ROOT / "scripts").glob("*.ps1"))
STOP = re.compile(r'^\s*\$ErrorActionPreference\s*=\s*"Stop"\s*$')


def _first_statement_index(lines: list[str]) -> int:
    depth = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if s.lower().startswith("param(") or depth:
            depth += s.count("(") - s.count(")")
            continue
        return i
    return len(lines)


class TestEveryPs1StopsOnFirstError(unittest.TestCase):
    def test_eleven_scripts(self) -> None:
        self.assertEqual(11, len(PS1), [p.name for p in PS1])

    def test_stop_is_present_and_first(self) -> None:
        for p in PS1:
            with self.subTest(script=p.name):
                lines = p.read_text(encoding="utf-8-sig").splitlines()
                hits = [i for i, ln in enumerate(lines) if STOP.match(ln)]
                self.assertTrue(hits, f"{p.name} 에 $ErrorActionPreference = \"Stop\" 이 없다")
                self.assertEqual(_first_statement_index(lines), hits[0],
                                 f"{p.name}: Stop 이 첫 명령 뒤에 온다 (앞 명령은 Continue 로 돈다)")

    def test_silently_continue_only_on_probes(self) -> None:
        for p in PS1:
            for i, ln in enumerate(p.read_text(encoding="utf-8-sig").splitlines(), 1):
                if "SilentlyContinue" in ln:
                    with self.subTest(site=f"{p.name}:{i}"):
                        self.assertRegex(ln, r"Get-Command|Test-Path|Get-Item|Get-Process", f"{p.name}:{i} 가 실패를 조용히 넘긴다")


if __name__ == "__main__":
    unittest.main()
