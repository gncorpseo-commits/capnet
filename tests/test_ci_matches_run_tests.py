"""CI 가 `run_tests.sh` 와 **같은 것을 보는가**.

## 왜 있는가

`scripts/run_tests.sh` 는 로컬 전체 검증이고 CI 의 `unit` 잡은 같은 일을 한다.
**그런데 둘이 갈려 있었다 (2026-09-02 실측)** — `run_tests.sh` 는
`scripts/check_release.sh`(제출 zip 사전 검증)를 부르는데 **CI 에는 없었다.**

로컬에서만 도는 검사는 결국 **안 도는 검사**다. 사람은 `run_tests` 를 매번 돌리지 않고,
PR 은 CI 초록만 보고 지나간다. 0.25초짜리라 뺄 이유도 없었다.

이번 회차에 고친 결함 아홉과 같은 모양이다 — **보고 있다고 믿는데 안 보고 있다.**

## 무엇을 보나

`run_tests.sh` 가 부르는 **`scripts/` 도구**가 CI `unit` 잡에도 있는가.

## 무엇을 안 보나

- **순서·이름·형태를 강제하지 않는다.** CI 는 잡을 나눠 돌 수 있고 그건 정상이다
- **CI 에만 있는 것을 막지 않는다.** CI 가 더 보는 것은 좋은 일이다 (migrate 잡이 그렇다)
- `run_tests.sh` 안의 `python3 -m unittest` 는 CI 가 같은 명령으로 돈다 — 도구 파일만 본다
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402
RUNNER = ROOT / "scripts" / "run_tests.sh"
CI = ROOT / ".github" / "workflows" / "ci.yml"

# `scripts/<name>` 꼴로 불리는 것만 본다.
TOOL = re.compile(r"scripts/([A-Za-z0-9_.-]+\.(?:sh|py))")


def _without_comments(text: str) -> str:
    """`#` 로 시작하는 줄을 비운다 (셸·YAML 공통).

    **주석까지 세면 헛돈다.** `run_tests.sh` 머리말은 「통합 검증은 `scripts/migrate.sh` 와
    CI 가 한다」고 **설명**하는데, 그걸 호출로 세면 「CI 가 migrate.sh 를 안 부른다」는
    거짓 실패가 난다 — 실제로 처음 짰을 때 그렇게 났다.

    이 저장소가 `tests/_srcguard.code_only()` 로 파이썬에 하는 일을 셸·YAML 에 한다.
    줄 끝 주석은 건드리지 않는다 — 따옴표 안의 `#` 를 잘못 자르는 쪽이 더 나쁘다.
    """
    return "\n".join("" if line.lstrip().startswith("#") else line
                      for line in text.splitlines())


def tools_in(path: Path) -> set[str]:
    return set(TOOL.findall(_without_comments(path.read_text(encoding="utf-8"))))


class TestCiSeesWhatRunTestsSees(unittest.TestCase):
    def test_no_tool_is_local_only(self) -> None:
        """`run_tests` 가 부르는데 CI 가 안 부르는 도구 — 그게 갈린 자리다."""
        local = tools_in(RUNNER)
        # `run_tests.sh` 자기 자신은 CI 가 부르지 않는다 (잡을 나눠 돈다).
        local.discard("run_tests.sh")
        ci = tools_in(CI)
        missing = sorted(local - ci)
        self.assertEqual(
            missing,
            [],
            f"로컬에서만 도는 검사 {len(missing)}개 — CI 에 넣거나 왜 뺐는지 적는다: {missing}",
        )

    def test_probe_actually_finds_tools(self) -> None:
        """0개를 비교하며 통과하는 상태를 막는다."""
        self.assertGreater(len(tools_in(RUNNER)), 2, sorted(tools_in(RUNNER)))
        self.assertGreater(len(tools_in(CI)), 2, sorted(tools_in(CI)))

    def test_ci_still_runs_the_unit_suite(self) -> None:
        """도구만 맞추고 정작 테스트를 안 돌리면 뜻이 없다."""
        self.assertIn("unittest discover -s tests", hash_comment_free(CI))


if __name__ == "__main__":
    unittest.main()
