r"""SBOM 생성 도구의 버전이 **핀돼 있고 sbom.json 이 기록한 버전과 같은가** (배치 D #151 · `#239` 형제).

## 왜 있는가

두 생성기가 `pip install cyclonedx-bom` 을 **무버전**으로 깔았다. 도구 메이저가 바뀌면 같은 의존성으로도 SBOM 의 모양(specVersion·
필드)이 달라지고, `test_sbom_coverage` 는 이름만 보므로 조용하다. `sbom.json` 의 `metadata.tools` 가 실제로 쓴 버전을 기록하니
그 값으로 핀했다.

## 실측 (2026-09-06)

| 어디 | 값 |
|---|---|
| `sbom.json` `metadata.tools.components[cyclonedx-bom].version` | 기록돼 있다 |
| `generate_sbom.sh` · `generate_sbom.ps1` | `cyclonedx-bom==<그 버전>` — 둘이 같다 |

## 재현

```bash
python3 -m unittest tests.test_sbom_tool_version_pinned
```
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

SBOM = ROOT / "sbom.json"
GENERATORS = (ROOT / "scripts" / "generate_sbom.sh", ROOT / "scripts" / "generate_sbom.ps1")


def _recorded() -> str:
    d = json.loads(SBOM.read_text(encoding="utf-8"))
    comps = d["metadata"]["tools"]["components"]
    return next(c["version"] for c in comps if "cyclonedx" in c.get("name", ""))


def _pinned(p: Path) -> list[str]:
    return re.findall(r'cyclonedx-bom==([\w.]+)', hash_comment_free(p))


class TestToolVersionIsPinned(unittest.TestCase):
    def test_both_generators_pin_the_recorded_version(self) -> None:
        want = _recorded()
        self.assertRegex(want, r"^\d+\.\d+")
        for p in GENERATORS:
            with self.subTest(generator=p.name):
                self.assertEqual([want], _pinned(p), f"{p.name} 의 cyclonedx-bom 핀이 sbom.json 기록({want})과 다르거나 없다")

    def test_no_unpinned_install_remains(self) -> None:
        for p in GENERATORS:
            with self.subTest(generator=p.name):
                self.assertNotRegex(hash_comment_free(p), r"pip install -q cyclonedx-bom\s*$")


if __name__ == "__main__":
    unittest.main()
