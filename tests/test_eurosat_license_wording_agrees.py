r"""EuroSAT 데이터 라이선스 문구가 **기계 핀과 문서에서 같은가** (배치 D #150 · 절대규칙 6 옆).

## 실측 (2026-09-06)

| 어디 | 문구 |
|---|---|
| `docs/spec/golden/eurosat-rgb.json` (기계 핀) | `"license": "MIT"` · Zenodo `7711810` |
| `README.md` | 「EuroSAT RGB(Zenodo `7711810`, MIT)」 |
| `docs/ops/regulation-compliance.md` | 「EuroSAT MIT」 |
| 원본 zip 안의 LICENSE 파일 | **못 봤다** — `data/eurosat/` 은 저장소 밖(미동봉, `.gitignore`) |

## 재현

```bash
python3 -m unittest tests.test_eurosat_license_wording_agrees
```
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "docs" / "spec" / "golden" / "eurosat-rgb.json"
DOCS = (ROOT / "README.md", ROOT / "docs" / "ops" / "regulation-compliance.md")


class TestWordingAgrees(unittest.TestCase):
    def test_pin_has_license_and_record(self) -> None:
        pin = json.loads(PIN.read_text(encoding="utf-8"))
        self.assertEqual("MIT", pin["license"])
        self.assertEqual("7711810", pin["zenodo_record"])
        self.assertIn(pin["zenodo_record"], pin["download_url"])

    def test_docs_say_the_same_license(self) -> None:
        pin = json.loads(PIN.read_text(encoding="utf-8"))
        for doc in DOCS:
            with self.subTest(doc=doc.name):
                text = doc.read_text(encoding="utf-8")
                m = re.search(r"EuroSAT[^\n]{0,60}?\b(MIT|CC[- ]BY[\w.-]*|Apache[\w.-]*|GPL[\w.-]*)\b", text)
                self.assertIsNotNone(m, f"{doc.name} 이 EuroSAT 라이선스를 말하지 않는다")
                assert m is not None
                self.assertEqual(pin["license"], m.group(1), f"{doc.name} 의 EuroSAT 라이선스가 기계 핀과 다르다")

    def test_readme_names_the_record(self) -> None:
        self.assertIn("7711810", (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
