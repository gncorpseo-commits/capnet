r"""시드 SQL · 카탈로그 · 등록 스크립트 — **세 장이 같은 능력 이름을 말하는가** (배치 C #121).

## 실측 (2026-09-06)

| 장 | 능력 code |
|---|---|
| 시드 SQL (`apps/core/sql/seed.sql` v1 · `migrations/0006` v2) | `image.classify` |
| 데모 등록 스크립트 9 (`scripts/*_demo.sh` 의 `"code":"…"`) | `image.embed` … `timeseries.forecast` |
| 카탈로그 「구현됨」 | **10** = 위 둘의 합집합 |
| `apps/core`·`migrations`·`apps/core/sql` 의 code 리터럴 | 전부 카탈로그 52 안 (`demo_violations.sql` 의 `@99` 는 시연용 버전) |
| 실행기 | code 를 이름으로 안 부른다 — `ARCH_REGISTRY` 11 → 모달리티 (`test_arch_names_agree_everywhere` 가 본다) |

## 재현

```bash
python3 -m unittest tests.test_three_sheets_name_the_same_capabilities
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "spec" / "capability-catalog.md"
SEEDS = [ROOT / "apps" / "core" / "sql" / "seed.sql", *sorted((ROOT / "migrations").glob("*.sql"))]
CODE_SQL = re.compile(r"'([a-z_]+\.[a-z_]+)'\s*,\s*\d+")          # 'image.classify', 1
CODE_SH = re.compile(r'"code":\s*"([a-z_]+\.[a-z_]+)"')


def _catalog() -> tuple[set[str], set[str]]:
    text = CATALOG.read_text(encoding="utf-8")
    rows = re.findall(r"^\| \d+ \| `([a-z_]+\.[a-z_]+)`([^\n]*)$", text, re.M)
    return {c for c, _ in rows}, {c for c, rest in rows if "구현됨" in rest}


def _seeded() -> set[str]:
    out = set()
    for p in SEEDS:
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip().startswith("--"):
                out |= set(CODE_SQL.findall(ln))
    return out


def _demo_registered() -> set[str]:
    out = set()
    for p in sorted((ROOT / "scripts").glob("*_demo.sh")):
        out |= set(CODE_SH.findall(p.read_text(encoding="utf-8")))
    return out


class TestTheSheetsAgree(unittest.TestCase):
    def test_implemented_equals_seeded_plus_demo_registered(self) -> None:
        all_codes, implemented = _catalog()
        self.assertEqual(52, len(all_codes))
        self.assertEqual(10, len(implemented), sorted(implemented))
        self.assertEqual(implemented, _seeded() | _demo_registered())

    def test_every_literal_code_is_in_the_catalog(self) -> None:
        all_codes, _ = _catalog()
        lits = set()
        for p in [*SEEDS, ROOT / "scripts" / "demo_violations.sql", *sorted((ROOT / "apps" / "core" / "app").glob("*.py"))]:
            for ln in p.read_text(encoding="utf-8").splitlines():
                if ln.strip().startswith(("--", "#")):
                    continue
                lits |= set(CODE_SQL.findall(ln)) | set(re.findall(r'"([a-z_]+\.[a-z_]+)"\s*,\s*\d', ln))
        self.assertTrue(lits)
        self.assertEqual(set(), lits - all_codes, f"카탈로그에 없는 code: {lits - all_codes}")

    def test_probe_reads_both_sides(self) -> None:
        self.assertEqual({"image.classify"}, _seeded())
        self.assertEqual(9, len(_demo_registered()))


if __name__ == "__main__":
    unittest.main()
