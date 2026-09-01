"""`docs/guide/testing.md` 가 실물과 어긋나지 않는가.

## 왜 있는가

**실제로 어긋나 있었다 (2026-09-01).** 이 문서는 capreq 테스트를 돌리는 법으로 오래
**`httpx` 하나**만 적었다. 그 사이 서버 경로(첨부) 검사가 들어오면서 CI 는
`fastapi`·`python-multipart` 까지 깔게 됐는데, **문서는 그대로였다.**

문서대로 깔고 돌리면 첨부 검사 **3건이 실패한다.** 그런데 실패 메시지는
`AssertionError: The python-multipart library must be installed` 이라 **제품 결함처럼 보인다** —
이번에 실제로 그렇게 오해했다가, `pyproject.toml` 의 `server` extra 를 보고 되짚었다.

「검증 방법을 적은 문서」가 틀리면 **검증이 통째로 헛돈다.** 그래서 여기만 기계가 잇는다.

## 무엇을 보나

1. **의존성 줄이 CI 와 같은가** — 정본은 `.github/workflows/ci.yml` 의 `capreq` 잡이다.
   문서가 **덜 적는 것**을 막는다 (이번에 다친 방향).
2. **문서가 가리키는 파일이 실재하는가** — 이름을 바꾸면 문서가 걸린다.

## 무엇을 안 보나

**개수·목록을 문서에 강제하지 않는다.** 반대다 — §3 에서 손으로 센 목록을 **걷어냈다**.
파일이 늘 때마다 문서를 고치게 만드는 검사는 이 저장소가 이미 금지한다
(`test_doc_counts.TestSafetyChainCountsAreNotPinned`).

서사 문단도 안 본다. 「X 를 쓰지 않는다」를 텍스트로 검사했다가 **그렇게 적어 둔 설명이
걸린** 사고가 다섯 번 났다 (`tests/_srcguard.py`).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "guide" / "testing.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"

# `pip install "httpx>=0.27" "fastapi>=0.110"` 에서 이름만 — 버전 핀은 비교하지 않는다
# (핀을 올릴 때마다 문서를 고치게 만들면 아무도 안 지킨다).
PIP_LINE = re.compile(r"pip install ((?:\"[^\"]+\"\s*)+)")
PKG = re.compile(r"\"([A-Za-z0-9_.-]+)")


def pip_packages(text: str) -> list[set[str]]:
    """`pip install` 줄마다 패키지 **이름** 집합."""
    return [set(PKG.findall(group)) for group in PIP_LINE.findall(text)]


def ci_job(name: str) -> str:
    """`ci.yml` 에서 잡 하나의 본문. `migrate` 잡도 pip 를 쓰므로 범위를 좁혀야 한다."""
    text = CI.read_text(encoding="utf-8")
    parts = re.split(r"^  ([A-Za-z][\w-]*):$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        if parts[i] == name:
            return parts[i + 1]
    raise AssertionError(f"ci.yml 에 `{name}` 잡이 없다 — 이름이 바뀌었으면 검사를 따라 고친다")


class TestingDocMatchesCI(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = DOC.read_text(encoding="utf-8")
        self.ci = CI.read_text(encoding="utf-8")

    def test_capreq_deps_match_ci(self) -> None:
        """문서가 CI 보다 **덜 적으면** 그대로 따라한 사람이 3건을 실패로 본다."""
        in_ci = pip_packages(ci_job("capreq"))
        in_doc = pip_packages(self.doc)
        self.assertEqual(len(in_ci), 1, f"CI 의 pip install 줄이 {len(in_ci)}개 — 검사를 손봐야 한다")
        self.assertIn(
            in_ci[0], in_doc,
            f"CI 는 {sorted(in_ci[0])} 를 깔는데 문서에 같은 줄이 없다 — 문서: {[sorted(d) for d in in_doc]}",
        )

    def test_named_files_exist(self) -> None:
        """문서가 없는 파일을 가리키면 따라가는 사람이 막힌다."""
        named = set(re.findall(r"`((?:tests|scripts|capreq|apps|docs)/[\w./-]+\.(?:py|sh|js|yml|md))`", self.doc))
        missing = sorted(p for p in named if not (ROOT / p).exists())
        self.assertEqual(missing, [], f"문서에만 있는 파일 {len(missing)}개: {missing}")

    def test_probe_actually_finds_things(self) -> None:
        """0개를 비교하며 통과하는 상태를 막는다."""
        self.assertEqual(len(pip_packages(ci_job("capreq"))), 1)
        self.assertGreater(
            len(re.findall(r"`tests/[\w./-]+\.py`", self.doc)), 2, "문서가 테스트 파일을 하나도 안 가리킨다"
        )


if __name__ == "__main__":
    unittest.main()
