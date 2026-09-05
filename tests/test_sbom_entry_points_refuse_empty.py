r"""SBOM 을 만드는 진입점 셋이 **의존성 없이 성공하지 않는가** (배치 B #86 · `#245` 잔여).

## 왜 있는가

`#245`(큐 #55)는 `generate_sbom.sh` 에 「의존성 파일을 못 읽으면 멈춘다」를 달았다. 그런데
SBOM 이 나오는 길은 셋이다 — `.sh` · `.ps1` 쌍둥이 · 둘이 공유하는 `enrich_sbom.py`.
나머지 둘을 봤다 (2026-09-06):

| 진입점 | 전 | 후 |
|---|---|---|
| `generate_sbom.ps1` | `capreq/pyproject.toml` 을 **안 읽는다** — Windows 에서 만든 SBOM 은 `httpx`·`python-multipart` 가 빠진 채 exit 0 | `.sh` 와 같은 목록 · 이름 기준 중복 제거 |
| `enrich_sbom.py` | raw 에 구성요소가 **0개**여도 `sbom.json` 을 쓰고 exit 0 | 0개면 exit 1, 아무것도 안 쓴다 |
| `generate_sbom.sh` | `#245` 가 이미 막았다 | — |

`.ps1` 은 이 환경에 `pwsh` 가 없어 **소스만** 본다. `enrich_sbom.py` 는 실제로 돌린다.

## 재현

```bash
python3 -m unittest tests.test_sbom_entry_points_refuse_empty
```
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

SH = ROOT / "scripts" / "generate_sbom.sh"
PS1 = ROOT / "scripts" / "generate_sbom.ps1"
ENRICH = ROOT / "scripts" / "enrich_sbom.py"

# 두 생성기가 **같은 자리**에서 목록을 모아야 한다.
SOURCES = ("apps/core/requirements.txt", "apps/node/requirements.txt", "capreq/pyproject.toml",
           "TORCH_VERSION", "TORCHVISION_VERSION")


def _enrich(components: list[dict]) -> tuple[int, bool, str]:
    with tempfile.TemporaryDirectory() as td:
        raw, out = Path(td) / "raw.json", Path(td) / "out.json"
        raw.write_text(json.dumps({"bomFormat": "CycloneDX", "components": components}), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(ENRICH), str(raw), str(out)],
                              capture_output=True, text=True, timeout=60)
        return proc.returncode, out.is_file(), proc.stdout + proc.stderr


class TestEnrichRefusesAnEmptyBom(unittest.TestCase):
    def test_zero_components_is_a_failure(self) -> None:
        rc, written, log = _enrich([])
        self.assertNotEqual(0, rc, "구성요소 0개인데 성공했다")
        self.assertFalse(written, "0개인데 sbom 을 썼다")
        self.assertIn("0개", log)

    def test_one_component_still_works(self) -> None:
        rc, written, log = _enrich([{"type": "library", "name": "fastapi", "version": "0.116.1"}])
        self.assertEqual(0, rc, log)
        self.assertTrue(written)


class TestBothGeneratorsReadTheSameSources(unittest.TestCase):
    def test_every_source_is_named_on_both_sides(self) -> None:
        # 주석을 벗긴다 — 「capreq 는 pyproject.toml 로 선언한다」는 설명이지 읽는 것이 아니다.
        sh = hash_comment_free(SH)
        ps1 = hash_comment_free(PS1)
        self.assertTrue(SOURCES)
        for src in SOURCES:
            with self.subTest(source=src):
                self.assertIn(src.split("/")[-1], sh, f".sh 가 {src} 를 안 본다")
                self.assertIn(src.split("/")[-1], ps1, f".ps1 이 {src} 를 안 본다")
        self.assertIn("$core + $node + $capreq +", ps1, "capreq 목록이 요구 파일에 안 들어간다")

    def test_ps1_stops_on_the_first_error_and_dedups_by_name(self) -> None:
        ps1 = hash_comment_free(PS1)
        self.assertIn('$ErrorActionPreference = "Stop"', ps1)
        self.assertIn("-not $capreq", ps1, "capreq 목록이 비어도 계속 간다")
        self.assertRegex(ps1, r"-split '\[=<>!~;\\\[\]'", "이름 기준 중복 제거가 없다 — fastapi 가 두 번 들어간다")
        self.assertNotIn("Select-Object -Unique", ps1, "줄 단위 중복 제거는 같은 이름·다른 핀을 못 거른다")

    def test_sh_dedups_by_name_too(self) -> None:
        self.assertIn("!seen[name]++", hash_comment_free(SH))


class TestProbeActuallyRuns(unittest.TestCase):
    def test_enrich_is_the_shared_tail_of_both(self) -> None:
        for p in (SH, PS1):
            with self.subTest(file=p.name):
                self.assertIn("enrich_sbom.py", hash_comment_free(p))

    def test_enough_sources(self) -> None:
        self.assertGreaterEqual(len(SOURCES), 5)


if __name__ == "__main__":
    unittest.main()
