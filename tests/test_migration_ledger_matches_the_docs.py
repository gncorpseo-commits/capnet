r"""`migrations/*.sql` 과 `docs/guide/migrations.md` 의 세대 표가 **같은가** (배치 D #137).

## 왜 있는가

문서 표가 0003 에서 멈춰 있었다 — 파일은 0018 까지 열여덟. 「DB 세대 번호」를 사람이 읽는 곳이 낡으면 어느 볼륨이
어디까지 올라왔는지 문서로는 알 수 없다. 표를 채우고, 파일 ↔ 행을 서로 묶는다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `migrations/NNNN_name.sql` | 18 (0001–0018, 빈 번호 없음) |
| 문서 표의 행 | 18 — 번호·이름이 파일과 같다 (`README`·런북의 「완료 — 18개 적용」은 `test_doc_counts` 가 본다) |

## 재현

```bash
python3 -m unittest tests.test_migration_ledger_matches_the_docs
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted((ROOT / "migrations").glob("*.sql"))
DOC = ROOT / "docs" / "guide" / "migrations.md"


def _files() -> dict[str, str]:
    out = {}
    for p in FILES:
        m = re.match(r"(\d{4})_(\w+)\.sql$", p.name)
        assert m, p.name
        out[m.group(1)] = m.group(2)
    return out


def _rows() -> dict[str, str]:
    return {n: name for n, name in re.findall(r"^\| (\d{4}) \| `(\w+)` \|", DOC.read_text(encoding="utf-8"), re.M)}


class TestLedgerAndDocsAgree(unittest.TestCase):
    def test_numbers_are_contiguous(self) -> None:
        nums = sorted(int(n) for n in _files())
        self.assertEqual(list(range(1, len(nums) + 1)), nums)
        self.assertGreaterEqual(len(nums), 18)

    def test_every_file_has_a_row_with_the_same_name(self) -> None:
        files, rows = _files(), _rows()
        self.assertEqual(files, rows, "파일과 문서 표가 다르다")


if __name__ == "__main__":
    unittest.main()
