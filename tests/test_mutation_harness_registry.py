r"""뮤테이션 하네스의 등록부가 **낡지 않았는가** (배치 D #135).

## 왜 있는가

`scripts/mutation_harness.py` 는 「핀 검사가 정말 무는가」를 다시 돌리는 유일한 길이다. 등록된 변이의 찾을 문자열이
소스에서 사라지면 그 변이는 조용히 못 심어지고, 검사 모듈이 이름을 바꾸면 「운다」가 거짓이 된다. 여기서 실재만 본다 —
실제로 심고 돌리는 것은 파일을 고쳤다 되돌리므로 `run_tests` 밖(수동)이다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| 등록된 변이 | 12 — 전부 심어지고 전부 운다 (`python3 scripts/mutation_harness.py` → `12/12 운다`) |
| 찾을 문자열이 소스에 없는 것 · 검사 모듈이 없는 것 · id 중복 | 0 · 0 · 0 |

## 재현

```bash
python3 -m unittest tests.test_mutation_harness_registry
python3 scripts/mutation_harness.py          # 수동 · 깨끗한 트리에서
```
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from mutation_harness import MUTATIONS  # noqa: E402


class TestRegistryIsFresh(unittest.TestCase):
    def test_enough_and_unique(self) -> None:
        ids = [m["id"] for m in MUTATIONS]
        self.assertGreaterEqual(len(ids), 10, ids)
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_find_string_still_exists(self) -> None:
        self.assertTrue(MUTATIONS)
        for m in MUTATIONS:
            with self.subTest(id=m["id"]):
                p = ROOT / str(m["file"])
                self.assertTrue(p.is_file(), f"{m['file']} 없음")
                if m["find"] is not None:
                    self.assertIn(str(m["find"]), p.read_text(encoding="utf-8"), f"{m['id']}: 찾을 문자열이 사라졌다")

    def test_every_test_module_exists(self) -> None:
        for m in MUTATIONS:
            with self.subTest(id=m["id"]):
                mod = str(m["test"]).split(".")[-1]
                self.assertTrue((ROOT / "tests" / f"{mod}.py").is_file(), f"{m['id']}: 검사 모듈 {mod} 없음")


if __name__ == "__main__":
    unittest.main()
