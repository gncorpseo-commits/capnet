"""`sbom.json` 이 **선언된 의존성을 다 담고 있는가**.

## 왜 있는가

`sbom.json` 은 제출 필수 파일이다 (`check_submission.REQUIRED_FILES`). SBOM 의 존재
이유가 **「이 배포물에 무엇이 들어 있나」**인데, 생성기가 그 목록을 덜 모으면
**있는 척하는 문서**가 된다.

**실제로 덜 모으고 있었다 (2026-09-02 실측).** `scripts/generate_sbom.sh` 는
`apps/core`·`apps/node` 의 `requirements.txt` 와 Dockerfile 의 torch 핀만 모았다.
`capreq` 는 저장소와 함께 배포되는데 자기 의존성을 `pyproject.toml` 로 선언한다 —
그래서 **`httpx` 와 `python-multipart` 가 SBOM 에 없었다.**

`check_submission` 의 라이선스 고지 검사도 **같은 사각지대**였다 (별 PR 로 고쳤다).
같은 원인 하나가 두 도구를 동시에 덜 보게 만들고 있었다.

## 무엇을 보나

**이름만** 본다 — 선언된 의존성이 SBOM 에 하나도 빠지지 않았는가.

## 무엇을 안 보나

- **버전 대조를 강제하지 않는다.** `capreq` 는 범위로 선언한다(`httpx>=0.27`) —
  핀이 없으므로 SBOM 에도 버전이 없는 것이 **정확한 기록**이다. 없는 핀을 지어내지 않는다
- **개수를 못박지 않는다.** 의존성은 늘 수 있다
- SBOM 의 나머지 필드(해시·라이선스·purl)는 생성기와 `enrich_sbom.py` 몫이다
"""

from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SBOM = ROOT / "sbom.json"
DOCKERFILE = ROOT / "apps" / "node" / "Dockerfile"


def declared_names() -> set[str]:
    names: set[str] = set()
    for rel in ("apps/core/requirements.txt", "apps/node/requirements.txt"):
        p = ROOT / rel
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                names.add(re.split(r"[\[=<>!~;]", line)[0].strip().lower())

    pyproject = ROOT / "capreq" / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as fh:
            doc = tomllib.load(fh)
        project = doc.get("project") or {}
        specs = list(project.get("dependencies") or [])
        for extra in (project.get("optional-dependencies") or {}).values():
            specs.extend(extra)
        for spec in specs:
            names.add(re.split(r"[\[=<>!~;\s]", spec)[0].strip().lower())

    # torch 핀의 정본은 Dockerfile 의 ARG 다 (생성기와 같은 자리를 본다).
    if DOCKERFILE.is_file():
        text = DOCKERFILE.read_text(encoding="utf-8")
        for name, arg in (("torch", "TORCH_VERSION"), ("torchvision", "TORCHVISION_VERSION")):
            if re.search(rf"^ARG {arg}=", text, re.M):
                names.add(name)
    return {n for n in names if n}


def sbom_names() -> set[str]:
    doc = json.loads(SBOM.read_text(encoding="utf-8"))
    return {(c.get("name") or "").lower() for c in (doc.get("components") or [])}


class TestSbomCoversDeclaredDeps(unittest.TestCase):
    def test_nothing_declared_is_missing(self) -> None:
        missing = sorted(declared_names() - sbom_names())
        self.assertEqual(missing, [], f"SBOM 에 없는 선언 의존성: {missing}")

    def test_no_duplicate_components(self) -> None:
        """`fastapi==0.116.1` 과 `fastapi>=0.110` 을 줄 단위로 dedupe 하면 둘 다 남는다."""
        doc = json.loads(SBOM.read_text(encoding="utf-8"))
        names = [(c.get("name") or "").lower() for c in (doc.get("components") or [])]
        dupes = sorted({n for n in names if names.count(n) > 1})
        self.assertEqual(dupes, [], f"같은 구성요소가 두 번 있다: {dupes}")

    def test_generator_reads_capreq(self) -> None:
        """`sbom.json` 만 고치면 다음 생성에서 되돌아간다."""
        gen = (ROOT / "scripts" / "generate_sbom.sh").read_text(encoding="utf-8")
        self.assertIn("capreq/pyproject.toml", gen, "생성기가 capreq 를 안 본다")

    def test_probe_actually_finds_things(self) -> None:
        self.assertGreater(len(declared_names()), 5)
        self.assertGreater(len(sbom_names()), 5)


if __name__ == "__main__":
    unittest.main()
