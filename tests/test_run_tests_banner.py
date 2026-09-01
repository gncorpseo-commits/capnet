"""`run_tests.sh` 가 **건너뛴 건수를 배너까지 끌고 올라오는가**.

## 왜 있는가

`skip` 은 통과가 아니다. 그런데 `OK (skipped=7)` 은 초록으로 지나가고, 그 줄은
**출력 한복판**에 있다 — 뒤에 `check_golden_sha`·`check_release`·`check_submission` 이
더 찍히고 맨 아래엔 「전부 통과.」만 남는다. 읽는 사람은 마지막 줄을 본다.

**실제로 그래서 놓쳤다 (2026-09-01).** 환경이 바뀌어 `node` 가 사라졌고 capreq 가
**6건을 건너뛴 채** 돌고 있었다. 빠진 것이 `chat.html` 을 실제로 실행하는 프로브였는데
아무 경고도 없었다. `tests/test_skip_reasons.py` 가 **사유**를 허가제로 만들었다면,
이쪽은 **건수가 눈에 띄게** 한다.

## 무엇을 보나

1. 단위 테스트 출력에서 `skipped=N` 을 **뽑는다**
2. 0 보다 크면 **맨 아래 배너에 다시 적는다**
3. 「전부 통과.」 문구는 **그대로 둔다** — 촬영 런북이 그 줄을 기대한다
   (`docs/ops/shoot-day-runbook.md` · `test_shoot_docs`)

## 무엇을 안 보나

**건수를 못박지 않는다.** 환경마다 다른 것이 정상이다 (`test_skip_reasons` 와 같은 태도).
여기서 보는 것은 **그 숫자가 배너에 오르는가**뿐이다.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_tests.sh"

# 스크립트가 실제로 쓰는 sed 식과 **같은 것**을 파이썬으로 다시 쓰지 않는다 —
# 두 벌이 되면 한쪽만 고쳐진다. 스크립트에서 뽑아 쓴다.
SED_LINE = re.compile(r"skipped=\\\(\[0-9\]\[0-9\]\*\\\)")


class TestRunnerSurfacesSkips(unittest.TestCase):
    def setUp(self) -> None:
        self.text = RUNNER.read_text(encoding="utf-8")

    def test_extracts_the_skip_count(self) -> None:
        self.assertRegex(self.text, r"skipped=", "건너뛴 건수를 뽑지 않는다")
        self.assertIn('skipped="$(', self.text, "뽑은 값을 변수에 담지 않는다")

    def test_banner_mentions_it_when_nonzero(self) -> None:
        """0 건이면 조용해야 한다 — 늘 떠들면 아무도 안 읽는다."""
        self.assertRegex(self.text, r'if \[\[ "\$skipped" -gt 0 \]\]', "0 초과일 때만 적는 분기가 없다")
        self.assertIn("건너뛰었다", self.text)

    def test_points_at_where_reasons_live(self) -> None:
        """건수만 보여 주면 「그래서 뭘 깔라는 건가」로 끝난다."""
        self.assertIn("test_skip_reasons.py", self.text)
        self.assertIn("testing.md", self.text)

    def test_keeps_the_pass_banner_verbatim(self) -> None:
        """촬영 런북이 이 줄을 기대한다 — 바꾸면 문서가 거짓이 된다."""
        self.assertIn('echo "전부 통과."', self.text)

    def test_still_fails_loudly(self) -> None:
        """출력을 변수에 담느라 실패 전파가 끊기면 안 된다."""
        self.assertIn("|| fail=1", self.text)
        self.assertIn("set -euo pipefail", self.text)


class TestSkipParserOnRealShapes(unittest.TestCase):
    """스크립트의 sed 식을 **실제 unittest 출력 모양**에 돌려 본다."""

    def extract(self, line: str) -> str:
        out = subprocess.run(
            ["sed", "-n", r"s/.*skipped=\([0-9][0-9]*\).*/\1/p"],
            input=line, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()

    def test_ok_with_skips(self) -> None:
        self.assertEqual(self.extract("OK (skipped=7)"), "7")

    def test_failed_with_skips(self) -> None:
        """실패했을 때도 뽑혀야 한다 — 그때가 더 알고 싶은 순간이다."""
        self.assertEqual(self.extract("FAILED (failures=1, skipped=7)"), "7")

    def test_plain_ok(self) -> None:
        self.assertEqual(self.extract("OK"), "")


class TestProbeActuallyReadsTheScript(unittest.TestCase):
    def test_not_vacuous(self) -> None:
        self.assertTrue(RUNNER.is_file())
        self.assertGreater(len(RUNNER.read_text(encoding="utf-8")), 800)


if __name__ == "__main__":
    unittest.main()
