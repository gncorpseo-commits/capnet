r"""Node 운영 안내가 보여 주는 **플래그**를 스크립트가 실제로 받는가 (배치 D #142).

## 실측 (2026-09-06)

| 문서 줄 (`operate-node.md`) | 플래그 | 스크립트 `case` |
|---|---|---|
| `node_onboard.sh --name … --domain … --tier …` (3줄) | `--name` `--domain` `--tier` | 받는다 (+ `--device` `--source` `--gate-runner` `--out`) |
| `node_bind.sh --node … --weights …` (2줄) | `--node` `--weights` | 받는다 (+ `--name` `--arch` `--capability-id`) |

## 재현

```bash
python3 -m unittest tests.test_node_docs_flags_match_scripts
```
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

DOC = ROOT / "docs" / "guide" / "operate-node.md"
SCRIPTS = ("node_onboard.sh", "node_bind.sh")


def _accepted(script: str) -> set[str]:
    return set(re.findall(r"^\s+(--[a-z-]+)\)", hash_comment_free(ROOT / "scripts" / script), re.M))


def _shown(script: str) -> list[tuple[int, set[str]]]:
    out = []
    for i, ln in enumerate(DOC.read_text(encoding="utf-8").splitlines(), 1):
        if f"scripts/{script}" in ln:
            out.append((i, set(re.findall(r"(--[a-z-]+)", ln))))
    return out


class TestDocFlagsAreReal(unittest.TestCase):
    def test_every_shown_flag_is_accepted(self) -> None:
        for script in SCRIPTS:
            shown = _shown(script)
            self.assertGreaterEqual(len(shown), 2, f"{script}: 문서 호출 줄 {len(shown)}")
            accepted = _accepted(script)
            self.assertGreaterEqual(len(accepted), 5, f"{script}: case 목록 {accepted}")
            for lineno, flags in shown:
                with self.subTest(script=script, line=lineno):
                    self.assertTrue(flags, f"{script} 호출 줄에 플래그가 없다")
                    self.assertEqual(set(), flags - accepted, f"{script} 가 안 받는 플래그를 문서가 보여 준다")


if __name__ == "__main__":
    unittest.main()
