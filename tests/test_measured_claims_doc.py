"""`measured-claims.md` 가 **없는 도구를 가리키지 않는가**.

## 왜 있는가

이 문서는 「새 숫자를 쓸 자리가 이 목록에 없으면 **숫자를 쓰기 전에 도구를 만든다**」고
적는다. 그러니 **그 목록이 실물과 맞아야** 규칙이 성립한다.

실제로 어긋나 있었다 (2026-09-02): `scripts/capreq_demo.sh` 가 들어온 지 하루가 지나도록
이 문서의 도구 표에 없었다. 그러면 「제품 입구 종단 숫자」를 쓰려는 사람이
**「자리가 없으니 도구를 만들라」**는 잘못된 안내를 받는다 — 이미 있는데.

## 무엇을 보나

1. 문서가 이름을 적은 `scripts/`·`tests/` 파일이 **실재하는가**
2. 도구 표가 **0개를 세며 통과하지 않는가**

## 무엇을 안 보나

- **개수.** 이 문서 자신이 §2 에서 개수 고정을 금지한다
- 서사 문단 (`_srcguard` 사고 5건)
- 「모든 `scripts/*_demo.sh` 가 표에 있어야 한다」 — 그 표는 **숫자를 내는 도구**의
  목록이지 데모 전체 목록이 아니다. 넓히면 표의 뜻이 바뀐다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "guide" / "measured-claims.md"

NAMED = re.compile(r"`((?:scripts|tests|docs|apps|capreq)/[\w./*-]+?\.(?:py|sh|js|md))`")


def named_paths() -> set[str]:
    return set(NAMED.findall(DOC.read_text(encoding="utf-8")))


class TestNamedToolsExist(unittest.TestCase):
    def test_every_named_path_exists(self) -> None:
        """`*` 가 든 것(`scripts/*_demo.sh`)은 글롭이라 따로 본다."""
        missing = sorted(
            p for p in named_paths()
            if "*" not in p and not (ROOT / p).exists()
        )
        self.assertEqual(missing, [], f"문서에만 있는 경로 {len(missing)}개: {missing}")

    def test_globs_match_something(self) -> None:
        """`scripts/*_demo.sh` 가 0개를 가리키면 표가 거짓말한다."""
        for pattern in (p for p in named_paths() if "*" in p):
            head, tail = pattern.split("/", 1)
            self.assertTrue(
                list((ROOT / head).glob(tail)), f"{pattern} 에 맞는 파일이 없다"
            )

    def test_probe_actually_finds_things(self) -> None:
        self.assertGreater(len(named_paths()), 5, sorted(named_paths()))


if __name__ == "__main__":
    unittest.main()
