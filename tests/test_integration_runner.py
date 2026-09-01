"""통합 검사 러너가 **아무것도 조용히 빠뜨리지 않는가**.

## 왜 있는가

`scripts/run_integration.sh` 는 `tests/integration/check_*.py` 를 **glob 으로** 집어간다:

    < <(find "$root/tests/integration" -name 'check_*.py' | sort)

`docs/guide/testing.md` §4.5 가 그것을 이렇게 약속한다 —
「이름 순으로 **전부** 집어간다. 파일을 놓기만 하면 CI 가 돈다 (**등록부가 따로 없다**)」.

**약속의 대가는 이름이다.** 패턴을 벗어난 이름으로 파일을 놓으면 **아무 말 없이 안 돈다.**
검사를 짜 놓고 돌지 않는 것은 검사가 없는 것보다 나쁘다 — 있다고 믿게 되기 때문이다.

이번 회차에 고친 다섯 결함이 전부 같은 모양이었다: **못 한 것이 안 한 것처럼 보인다.**
여기는 아직 그런 일이 없다(15개 전부 패턴에 맞는다). **나기 전에 막는다.**

## 무엇을 보나

1. `tests/integration/` 의 파이썬 파일이 **전부** 러너의 패턴에 맞는가
2. 러너가 **glob 을 쓰는가** — 하드코딩 목록으로 바뀌면 §4.5 가 거짓이 된다

## 무엇을 안 보나

**개수를 못박지 않는다.** 통합 검사는 능력·강제 경로를 더할 때마다 는다 —
`test_doc_counts` 가 같은 이유로 그 개수를 문서에 못박지 못하게 한다.
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "tests" / "integration"
RUNNER = ROOT / "scripts" / "run_integration.sh"

# 러너가 쓰는 패턴. 여기와 스크립트가 갈라지면 아래 검사가 걸린다.
PATTERN = "check_*.py"


class TestNothingIsSilentlySkipped(unittest.TestCase):
    def test_every_python_file_matches_the_runner_pattern(self) -> None:
        """패턴 밖 이름은 **아무 말 없이 안 돈다.**"""
        picked = {p.name for p in INTEGRATION.glob(PATTERN)}
        present = {
            p.name
            for p in INTEGRATION.glob("*.py")
            if p.name != "__init__.py"
        }
        skipped = sorted(present - picked)
        self.assertEqual(
            skipped,
            [],
            "러너가 안 집어가는 파일이 있다 — 이름을 `check_…py` 로 바꾸거나, "
            f"의도라면 여기 근거와 함께 적는다: {skipped}",
        )

    def test_runner_uses_a_glob_not_a_list(self) -> None:
        """하드코딩 목록으로 바뀌면 `testing.md` §4.5 의 「등록부가 없다」가 거짓이 된다."""
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("check_*.py", text, "러너가 패턴으로 안 집는다")
        self.assertIn("find", text, "glob 대신 목록을 쓰는 것으로 보인다")

    def test_probe_actually_finds_things(self) -> None:
        """0개를 비교하며 통과하는 상태를 막는다. **개수는 못박지 않는다.**"""
        self.assertGreater(len(list(INTEGRATION.glob(PATTERN))), 5)


if __name__ == "__main__":
    unittest.main()
