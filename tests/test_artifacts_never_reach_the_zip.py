r"""채점 산출물·골든 데이터·키가 **저장소와 제출 zip 에 들어올 수 없는가** (배치 C #122).

## 실측 (2026-09-06)

| 축 | 값 |
|---|---|
| `score_n300.sh` 가 쓰는 곳 | `$root/artifacts/…json` 만 · `compare_ab.sh` 도 거기서 읽는다 · `pass_rate`·`proof_ab` 는 파일을 안 쓴다 |
| `.gitignore` | `artifacts/` · `data/golden-n300/` · `data/golden-n300-*/` · `data/golden-G2/` · `data/golden-V/` · `data/golden-n600-*/` · `*.credential` · `*.key` |
| 추적 파일 중 산출물·골든·키 | **0** |
| `check_release.sh` 금지 목록 | `.git/` · `.env` · 실험 가중치 + (이번에) `artifacts/` · `data/golden*` · `*.credential` · `*.key` — `git add -f` 로 들어와도 zip 에서 걸린다 |

## 재현

```bash
python3 -m unittest tests.test_artifacts_never_reach_the_zip
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
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

IGNORE = ROOT / ".gitignore"
RELEASE = ROOT / "scripts" / "check_release.sh"
PATTERNS_THAT_MUST_BE_LISTED = ("artifacts/", "data/golden-n300/", "data/golden-n300-*/", "data/golden-G2/", "data/golden-V/",
                  "data/golden-n600-*/", "*.credential", "*.key")


class TestScoresGoToArtifactsOnly(unittest.TestCase):
    def test_score_script_writes_under_artifacts(self) -> None:
        body = hash_comment_free(ROOT / "scripts" / "score_n300.sh")
        self.assertIn('out_path="$root/artifacts/$OUT_NAME"', body)
        writes = [l for l in body.splitlines() if re.search(r"(?<![2&])>\s*\"?\$", l) and "/dev/null" not in l]
        self.assertEqual(['printf \'%s\\n\' "$raw" > "$out_path"'], [w.strip() for w in writes], writes)

    def test_compare_reads_from_artifacts(self) -> None:
        body = hash_comment_free(ROOT / "scripts" / "compare_ab.sh")
        self.assertEqual(2, len(re.findall(r':-artifacts/score-n300-', body)))


class TestNothingOfTheKindIsTracked(unittest.TestCase):
    def test_gitignore_names_them(self) -> None:
        lines = {l.strip() for l in IGNORE.read_text(encoding="utf-8").splitlines()}
        missing = [p for p in PATTERNS_THAT_MUST_BE_LISTED if p not in lines]
        self.assertEqual([], missing, f".gitignore 에 없다: {missing}")

    def test_git_tracks_none(self) -> None:
        out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=ROOT, timeout=60).stdout.splitlines()
        self.assertGreater(len(out), 300)
        bad = [f for f in out if f.startswith("artifacts/") or f.startswith("data/golden")
               or f.endswith((".credential", ".key")) or re.search(r"score-n300.*\.json$", f)]
        self.assertEqual([], bad, f"추적 중인 산출물·골든·키: {bad}")


class TestTheZipRuleNamesThem(unittest.TestCase):
    def test_check_release_forbids_them_by_name(self) -> None:
        body = hash_comment_free(RELEASE)
        i = body.index("bad = [")
        block = body[i:body.index("]", i)]
        for needle in ('n.startswith("artifacts/")', 'n.startswith("data/golden")', 'n.endswith(".credential")', 'n.endswith(".key")', 'n.startswith(".git/")'):
            with self.subTest(needle=needle):
                self.assertIn(needle, block, f"check_release 의 금지 목록에 없다: {needle}")


if __name__ == "__main__":
    unittest.main()
