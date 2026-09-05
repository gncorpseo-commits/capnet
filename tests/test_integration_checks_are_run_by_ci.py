r"""통합 검사 **열다섯을 누가 돌리는가** (큐 #42 · `#215` 옆).

## 왜 있는가

`#215` 가 잡은 것은 「**CI 가 본다**」가 거짓이던 자리였다 — 건너뛴 일곱은 어디에서도
안 돌고 있었다. 같은 질문을 `tests/integration/` 에 물었다.

| 무엇 | 답 (2026-09-05 실측) |
|---|---|
| `tests/integration/check_*.py` | **15** |
| `scripts/run_tests.sh` 가 부르는가 | **아니다** — DB 가 필요하다 |
| 그럼 누가 부르는가 | `.github/workflows/ci.yml` 의 **`migrate` 잡 한 줄** |
| 그 한 줄을 못박은 검사 | **0** |

```yaml
      - name: 통합 검사 (검사마다 깨끗한 DB)
        run: scripts/run_integration.sh      # ← 이 줄이 유일한 실행 경로다
```

**그 줄을 지우면 검사 열다섯이 조용히 안 돈다.** `test_integration_runner` 는 러너의
glob 만 보고, `test_ci_matches_run_tests` 는 `run_tests.sh` 가 부르는 도구만 본다 —
`run_integration.sh` 는 `run_tests.sh` 밖이라 **둘 사이로 빠진다.**

「검사를 짜 놓고 돌지 않는 것은 검사가 없는 것보다 나쁘다 — 있다고 믿게 되기
때문이다」(`test_integration_runner` 머리말). 그 문장이 러너 자신에게도 해당한다.

## 무엇을 고정하나

1. CI 에 `scripts/run_integration.sh` 를 **실제로 돌리는 단계**가 있다
2. 그 단계가 **조건부로 꺼지지 않는다** (`if:` 로 건너뛰면 없는 것과 같다)
3. 러너가 **`check_*.py` 를 하나도 못 찾으면 실패**한다 — 0건은 통과가 아니다
4. 세는 대상이 비지 않는다

## 무엇을 안 보나

- **`ci.yml` 을 고치지 않는다.** 잡·설치 추가는 열린 Decision(`round9-ci-coverage-proposal`)이다.
  여기는 **오늘 있는 것을 못박기만** 한다
- 검사 **개수**를 못박지 않는다 — 능력·강제 경로를 더할 때마다 는다 (`test_doc_counts` 규율)
- 검사가 **무엇을 보는가**. 그건 각 `check_*.py` 가 말한다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"
RUNNER = ROOT / "scripts" / "run_integration.sh"
INTEGRATION = ROOT / "tests" / "integration"

RUN_LINE = re.compile(r"^\s*run:\s*(?:bash\s+)?scripts/run_integration\.sh\s*$", re.M)
# 단계 블록 안의 `if:` — 줄 단위로 본다 (기본 `^` 는 문자열 처음만 맞는다)
IF_LINE = re.compile(r"^\s*if:", re.M)


def _checks() -> list[Path]:
    return sorted(INTEGRATION.glob("check_*.py"))


def _ci_text() -> str:
    return CI.read_text(encoding="utf-8")


def _step_block(text: str, at: int) -> str:
    """그 `run:` 이 속한 단계 블록 — 앞의 `- name:` 부터 다음 `- ` 까지."""
    lines = text[:at].splitlines()
    start = 0
    for i in range(len(lines) - 1, -1, -1):
        if re.match(r"^\s*- ", lines[i]):
            start = i
            break
    rest = text[at:].splitlines()
    end = len(rest)
    for j, line in enumerate(rest[1:], 1):
        if re.match(r"^\s*- ", line):
            end = j
            break
    return "\n".join(lines[start:] + rest[:end])


class TestCiActuallyRunsThem(unittest.TestCase):
    def test_ci_has_a_step_that_runs_the_runner(self) -> None:
        """이 한 줄이 유일한 실행 경로다 — 지우면 열다섯이 조용히 멈춘다."""
        self.assertTrue(CI.is_file(), "ci.yml 을 못 찾았다")
        hits = RUN_LINE.findall(_ci_text())
        self.assertTrue(hits, "CI 어디에서도 scripts/run_integration.sh 를 안 부른다")

    def test_that_step_is_not_conditional(self) -> None:
        """`if:` 로 꺼지면 초록인 채 아무것도 안 돈다."""
        text = _ci_text()
        m = RUN_LINE.search(text)
        self.assertIsNotNone(m, "실행 단계를 못 찾았다")
        assert m is not None
        block = _step_block(text, m.start())
        self.assertIsNone(IF_LINE.search(block), "통합 검사 단계가 조건부다:\n" + block)

    def test_run_tests_does_not_run_them(self) -> None:
        """여기가 바뀌면 이 파일의 전제가 바뀐다 — 그때 머리말을 같이 고친다."""
        body = (ROOT / "scripts" / "run_tests.sh").read_text(encoding="utf-8")
        self.assertNotIn("run_integration.sh", body,
                         "run_tests 가 통합 검사를 부른다면 이 검사의 전제를 다시 적는다")


class TestTheRunnerRefusesToBeEmpty(unittest.TestCase):
    """0건이 통과면 CI 단계가 남아 있어도 지키는 게 없다."""

    def test_runner_fails_when_it_finds_nothing(self) -> None:
        body = RUNNER.read_text(encoding="utf-8")
        self.assertTrue("통합 검사를 하나도 못 찾았다" in body,
                        f"{RUNNER.name}: 러너가 0건을 통과로 넘긴다")

    def test_runner_still_globs(self) -> None:
        body = RUNNER.read_text(encoding="utf-8")
        self.assertTrue("check_*.py" in body,
                        f"{RUNNER.name}: glob 을 안 쓴다 — 하드코딩 목록이면 빠뜨린다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_checks_exist(self) -> None:
        self.assertGreaterEqual(len(_checks()), 12, f"통합 검사 {len(_checks())}개만 봤다")

    def test_step_block_reader_works(self) -> None:
        """블록을 못 읽으면 `if:` 검사가 **공허하게** 통과한다."""
        fake = "jobs:\n  x:\n    steps:\n      - name: a\n        if: false\n        run: scripts/run_integration.sh\n      - name: b\n"
        m = RUN_LINE.search(fake)
        assert m is not None
        self.assertIsNotNone(IF_LINE.search(_step_block(fake, m.start())))


if __name__ == "__main__":
    unittest.main()
