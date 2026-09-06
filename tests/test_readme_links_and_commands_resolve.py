r"""README 의 **상대 링크와 명령이 부르는 경로**가 전부 실재하는가 (배치 D #139 · 원고 제외).

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| README 링크 | 29 — 상대 27 전부 존재 · 외부(http) 2 는 **오프라인이라 못 봤다** |
| README 의 명령 줄 (`bash`·`python`·`docker`·`curl`·`powershell`) | 12 — 부르는 `scripts/…`·`docs/…` 경로 전부 존재 |
| `docs/INDEX.md` 상대 링크 | 전부 존재 (`test_doc_counts` 가 일부를 본다 — 여기서 전수) |

## 재현

```bash
python3 -m unittest tests.test_readme_links_and_commands_resolve
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = (ROOT / "README.md", ROOT / "docs" / "INDEX.md")
LINK = re.compile(r"\]\(([^)\s]+?)(?:#[^)]*)?\)")
CMD = re.compile(r"^\s*(?:\$ )?((?:bash|python3?|docker|curl|powershell|pwsh) [^\n]+)", re.M)
PATH_IN_CMD = re.compile(r"(?<![\w/])(scripts/[\w.\\-]+|docs/[\w./-]+\.md|compose[\w.]*\.yaml)")


def _links(doc: Path) -> list[str]:
    return [l for l in LINK.findall(doc.read_text(encoding="utf-8")) if not l.startswith(("http://", "https://", "mailto:"))]


class TestEveryRelativeLinkResolves(unittest.TestCase):
    def test_links(self) -> None:
        for doc in DOCS:
            links = _links(doc)
            self.assertGreaterEqual(len(links), 20, f"{doc.name}: 링크 {len(links)}")
            with self.subTest(doc=doc.name):
                missing = [l for l in links if not (doc.parent / l).exists()]
                self.assertEqual([], missing, f"{doc.name} 의 깨진 링크: {missing}")


class TestEveryCommandPathExists(unittest.TestCase):
    def test_readme_commands(self) -> None:
        cmds = CMD.findall((ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cmds), 10, cmds)
        paths = sorted({p.replace("\\", "/") for c in cmds for p in PATH_IN_CMD.findall(c)})
        self.assertGreaterEqual(len(paths), 5, paths)
        self.assertEqual([], [p for p in paths if not (ROOT / p).exists()], "README 명령이 없는 파일을 부른다")


if __name__ == "__main__":
    unittest.main()
