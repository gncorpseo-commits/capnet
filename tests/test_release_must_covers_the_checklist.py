r"""`check_release.sh` 가 막는 것 ↔ 체크리스트의 「제출물·필수 파일」 (배치 C #123 · `#238` 형제).

## 실측 (2026-09-06)

| 무엇 | 체크리스트 | `check_release.sh` |
|---|---|---|
| 저장소 필수 파일 (S3) | LICENSE · NOTICE · README · THIRD-PARTY-LICENSES.md · sbom.json (5) | `must` 21 ⊇ 그 5 |
| 가중치 (S4-1) | 9종 + placeholder | `must` 의 `.safetensors` 10 = `check_submission.REQUIRED_WEIGHTS` 9 + placeholder |
| zip 상한 | 50MB 이하 | `LIMIT_MB=50` |
| `must` 전부 | — | 추적 파일이다 (0 누락) |

## 재현

```bash
python3 -m unittest tests.test_release_must_covers_the_checklist
bash scripts/check_release.sh
```
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_submission as cs  # noqa: E402

RELEASE = ROOT / "scripts" / "check_release.sh"
CHECKLIST = ROOT / "docs" / "ops" / "contest-submission-checklist.md"


def _must() -> list[str]:
    body = RELEASE.read_text(encoding="utf-8")
    block = body[body.index("must = ["):]
    block = block[:block.index("]")]
    return re.findall(r'"([^"]+)"', block)


class TestChecklistIsCoveredByTheScript(unittest.TestCase):
    def test_s3_files_are_all_in_must(self) -> None:
        s3 = next(l for l in CHECKLIST.read_text(encoding="utf-8").splitlines() if l.startswith("| S3 |"))
        named = re.findall(r"\b(LICENSE|NOTICE|README|THIRD-PARTY-LICENSES\.md|sbom\.json)\b", s3)
        self.assertEqual(5, len(set(named)), named)
        must = _must()
        for f in set(named):
            with self.subTest(file=f):
                self.assertTrue(any(m == f or m.startswith(f + ".") for m in must), f"{f} 가 check_release must 에 없다")

    def test_weights_in_must_equal_required_weights(self) -> None:
        weights = sorted(m for m in _must() if m.endswith(".safetensors"))
        self.assertIn("apps/node/weights/placeholder.safetensors", weights)
        # placeholder 는 REQUIRED_WEIGHTS 밖(실험 아님·게이트 불가)이라 따로 센다 — 9 + 1 = 10
        self.assertEqual(sorted(cs.REQUIRED_WEIGHTS), [w for w in weights if not w.endswith("placeholder.safetensors")])
        self.assertEqual(9, len(cs.REQUIRED_WEIGHTS))

    def test_zip_limit_agrees(self) -> None:
        self.assertIn("LIMIT_MB=50", RELEASE.read_text(encoding="utf-8"))
        self.assertIn("50MB 이하", CHECKLIST.read_text(encoding="utf-8"))

    def test_every_must_file_is_tracked(self) -> None:
        tracked = set(subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=ROOT, timeout=60).stdout.splitlines())
        must = _must()
        self.assertGreaterEqual(len(must), 20, must)
        self.assertEqual([], [m for m in must if m not in tracked], "must 인데 추적되지 않는 파일")


if __name__ == "__main__":
    unittest.main()
