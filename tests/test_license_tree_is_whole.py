r"""LICENSE·NOTICE 트리 — **빠진 것과 어긋난 것** (배치 D #152).

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| 루트 `LICENSE` | Apache License 2.0 |
| 루트 `NOTICE` | 「Third-party components → THIRD-PARTY-LICENSES.md」 · EuroSAT(Zenodo 7711810) 출처·인용 |
| `capreq/pyproject.toml` | `license = Apache-2.0` — 루트와 같다 |
| `capreq/README.md` 의 라이선스 문장 | **없음** — `capreq/` 는 내 경계 밖이라 표로만 남긴다 (한 줄이면 된다) |
| 추적된 LICENSE/NOTICE 파일 | 루트 둘뿐 (하위 패키지 별도 파일 없음 — 같은 저장소·같은 라이선스) |

## 재현

```bash
python3 -m unittest tests.test_license_tree_is_whole
```
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestLicenseTree(unittest.TestCase):
    def test_root_license_is_apache_2(self) -> None:
        head = "\n".join((ROOT / "LICENSE").read_text(encoding="utf-8").splitlines()[:4])
        self.assertIn("Apache License", head)
        self.assertIn("Version 2.0", head)

    def test_notice_points_at_the_table_and_the_dataset(self) -> None:
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("THIRD-PARTY-LICENSES.md", notice)
        self.assertIn("7711810", notice)
        self.assertIn("EuroSAT", notice)

    def test_capreq_declares_the_same_license(self) -> None:
        py = (ROOT / "capreq" / "pyproject.toml").read_text(encoding="utf-8")
        self.assertRegex(py, r'license\s*=\s*\{\s*text\s*=\s*"Apache-2\.0"\s*\}')

    def test_tracked_license_files_are_exactly_the_root_pair(self) -> None:
        tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=ROOT, timeout=60).stdout.splitlines()
        lic = sorted(f for f in tracked if re.search(r"(^|/)(LICENSE|NOTICE)(\.\w+)?$", f))
        self.assertEqual(["LICENSE", "NOTICE"], lic, lic)


if __name__ == "__main__":
    unittest.main()
