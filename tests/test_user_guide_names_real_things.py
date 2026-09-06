r"""사용자 안내가 부르는 **스크립트·능력 code 가 실재하는가** (배치 D #140).

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `docs/guide/user-guide-ko.md` 가 부르는 `scripts/*.sh` | 2 (`product_demo.sh` · `capreq_demo.sh`) — 전부 존재 |
| 백틱으로 부르는 능력 code (`x.y`) | 2 (`text.ner` · `text.extract`) — 전부 카탈로그 52 안 |
| `/v1/…` 라우트 언급 | 0 — 안내는 라우트가 아니라 제품 입구(capreq)로 말한다 |

## 재현

```bash
python3 -m unittest tests.test_user_guide_names_real_things
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "guide" / "user-guide-ko.md"
CATALOG = ROOT / "docs" / "spec" / "capability-catalog.md"


class TestGuideNamesRealThings(unittest.TestCase):
    def test_scripts_exist(self) -> None:
        names = sorted(set(re.findall(r"scripts/([\w.]+\.(?:sh|ps1|py))", GUIDE.read_text(encoding="utf-8"))))
        self.assertGreaterEqual(len(names), 2, names)
        self.assertEqual([], [n for n in names if not (ROOT / "scripts" / n).is_file()], "안내가 없는 스크립트를 부른다")

    def test_capability_codes_are_in_the_catalog(self) -> None:
        codes = sorted(set(re.findall(r"`([a-z_]+\.[a-z_]+)`", GUIDE.read_text(encoding="utf-8"))))
        codes = [c for c in codes if not c.endswith((".sh", ".py", ".ps1", ".md", ".json", ".yaml"))]
        self.assertGreaterEqual(len(codes), 2, codes)
        catalog = set(re.findall(r"^\| \d+ \| `([a-z_]+\.[a-z_]+)`", CATALOG.read_text(encoding="utf-8"), re.M))
        self.assertEqual([], [c for c in codes if c not in catalog], "안내가 카탈로그에 없는 능력을 말한다")

    def test_no_route_claims(self) -> None:
        self.assertEqual([], re.findall(r"/v1/[\w/{}-]+", GUIDE.read_text(encoding="utf-8")),
                         "안내에 라우트가 생겼다 — 실라우트와 대조하는 검사를 붙여라")


if __name__ == "__main__":
    unittest.main()
