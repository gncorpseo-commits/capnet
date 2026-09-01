"""로컬 설치가 만드는 빌드 잔여물이 **무시되는가**.

## 왜 있는가

`capreq/tests` 를 돌리려면 `pip install -e "./capreq[server]"` 가 필요하다
(`docs/guide/testing.md` §2). 그러면 `capreq/build/` 와 `capreq/src/capreq.egg-info/`
가 생기는데 **`.gitignore` 가 그걸 몰랐다 (2026-09-02 실측).**

제출 zip 은 안전하다 — `check_release.sh` 가 `git archive` 로 만들고, 그건 **추적 파일만**
담는다. 문제는 **작업트리**다: `git status` 가 지저분해지고, 실수로 커밋될 자리가 된다.

이 저장소는 `git add -A` 를 훅으로 막아 위험을 한 겹 줄여 뒀다. 그래도 무시 목록이
맞는 편이 낫다 — **훅은 마지막 방어선이지 첫 번째가 아니다.**

## 무엇을 보나

설치가 만드는 경로 셋이 `git check-ignore` 로 실제로 걸리는가.
**목록을 텍스트로 대조하지 않는다** — `.gitignore` 문법(뒤따르는 `/`·`*`·부정)을
직접 해석하면 틀린다. git 에게 묻는다.

## 무엇을 안 보나

**무시 목록 전체를 강제하지 않는다.** 이 파일이 막는 것은 「설치하면 생기는 것」 셋뿐이다.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# `pip install -e "./capreq[server]"` 가 만드는 것들.
BUILD_ARTIFACTS = (
    "capreq/build/lib/capreq/__init__.py",
    "capreq/dist/capreq-0.1.0.tar.gz",
    "capreq/src/capreq.egg-info/PKG-INFO",
)


def ignored(rel: str) -> bool:
    """git 에게 직접 묻는다 — `.gitignore` 문법을 우리가 다시 해석하지 않는다."""
    out = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", rel],
        cwd=ROOT, capture_output=True,
    )
    return out.returncode == 0


class TestBuildArtifactsAreIgnored(unittest.TestCase):
    def test_install_leftovers_are_ignored(self) -> None:
        missed = [p for p in BUILD_ARTIFACTS if not ignored(p)]
        self.assertEqual(missed, [], f"무시되지 않는 빌드 잔여물: {missed}")

    def test_source_is_still_tracked(self) -> None:
        """`capreq/` 를 통째로 무시해 버리면 제품이 사라진다."""
        self.assertFalse(ignored("capreq/src/capreq/server.py"), "소스가 무시된다")
        self.assertFalse(ignored("capreq/pyproject.toml"), "선언이 무시된다")

    def test_probe_actually_asks_git(self) -> None:
        """`git check-ignore` 가 안 돌면 위 검사가 전부 참이 된다."""
        self.assertTrue(ignored("__pycache__/x.pyc"), "이미 무시되는 것도 안 걸린다")


if __name__ == "__main__":
    unittest.main()
