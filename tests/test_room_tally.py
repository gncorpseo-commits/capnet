"""`clean_room`·`prod_room` 이 **0건을 통과로 세지 않는가.**

## 왜 있는가

두 스크립트 다 이렇게 끝났다:

    printf '===== 결과: 통과 %d · 실패 %d =====\\n' "$pass" "$fail"
    [ "$fail" -eq 0 ] || exit 1
    echo "…에서 전부 재현된다."

`pass=0 · fail=0` 이면 `fail -eq 0` 이 참이라 **「전부 재현된다」를 찍고 `exit 0`** 한다.
**한 건도 안 돌린 것이 초록이었다.**

이 회차가 고쳐 온 것과 같은 모양이다 — [#180](https://github.com/gncorpseo-commits/capnet/pull/180)
(누출 검사가 0건을 보고 「깨끗하다」) · [#181](https://github.com/gncorpseo-commits/capnet/pull/181)
(통합 러너가 0개를 보고 「통과 0 · 실패 0」).

**#180·#181 보다 가볍다.** 두 스크립트의 `chk` 호출은 **인라인 하드코딩**이라
0건이 되려면 스무 줄 넘게 지워야 한다 — glob 이 빗나가는 #181 과 다르다.
**과장하지 않는다.** 다만 `set -e` 가 없는 `prod_room` 은 앞 단계가 죽어도 계속 가므로
「빠져나갔는데 초록」이 아주 먼 이야기는 아니다.

## 왜 함수로 뺐나

**두 스크립트는 Docker 가 있어야 끝까지 돈다.** 판정이 스크립트 맨 끝에 인라인으로
있으면 그 줄을 **검사할 방법이 없다** — 이 세션에는 Docker 가 없다.
판정 한 줄을 `scripts/lib/tally.sh` 로 빼면 **그냥 부를 수 있다.**
여기서는 실제로 부른다.

## 무엇을 고정하나

1. `pass+fail == 0` → **non-zero** · 「0건은 통과가 아니다」를 말한다
2. 실패가 있으면 non-zero · **성공 문구를 안 찍는다**
3. 한 건 이상 돌고 실패 0 → 0 · 성공 문구를 찍는다
4. 두 스크립트가 **실제로 이 함수를 쓴다** (인라인으로 되돌아가면 걸린다)

## 무엇을 안 보나

**개수를 못박지 않는다.** `clean_room` 9 · `prod_room` 27 은 검사가 늘면 바뀐다.
보는 것은 **0 이 통과가 아니라는 것** 하나다.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "scripts" / "lib" / "tally.sh"
ROOMS = (ROOT / "scripts" / "clean_room.sh", ROOT / "scripts" / "prod_room.sh")
OK_LINE = "전부 재현된다."


def verdict(pass_n: int, fail_n: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", f'source "{LIB}"; tally_verdict {pass_n} {fail_n} "{OK_LINE}"'],
        capture_output=True, text=True, timeout=60,
    )


class TestZeroIsNotPass(unittest.TestCase):
    def test_zero_checks_fails(self) -> None:
        r = verdict(0, 0)
        self.assertNotEqual(r.returncode, 0, f"0건인데 통과했다:\n{r.stdout}")
        self.assertIn("0건은 통과가 아니다", r.stderr + r.stdout)

    def test_zero_checks_does_not_print_the_success_line(self) -> None:
        """「전부 재현된다」가 찍히면 사람이 그걸 읽고 넘어간다."""
        self.assertNotIn(OK_LINE, verdict(0, 0).stdout)

    def test_failures_fail_and_stay_quiet_about_success(self) -> None:
        r = verdict(2, 1)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(OK_LINE, r.stdout)

    def test_real_run_passes(self) -> None:
        r = verdict(3, 0)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(OK_LINE, r.stdout)

    def test_counts_are_still_printed(self) -> None:
        """숫자를 지우면 사람이 몇 건 돌았는지 못 본다 — 그게 이 결함의 출발점이었다."""
        self.assertIn("통과 3 · 실패 0", verdict(3, 0).stdout)


class TestRoomsUseIt(unittest.TestCase):
    """인라인으로 되돌아가면 위 검사가 **아무것도 안 지키게 된다.**"""

    def test_both_rooms_source_and_call_it(self) -> None:
        for path in ROOMS:
            with self.subTest(script=path.name):
                body = path.read_text(encoding="utf-8")
                self.assertIn("scripts/lib/tally.sh", body, f"{path.name}: 안 부른다")
                self.assertIn("tally_verdict", body, f"{path.name}: 함수를 안 쓴다")

    def test_no_room_keeps_the_old_inline_verdict(self) -> None:
        for path in ROOMS:
            with self.subTest(script=path.name):
                body = path.read_text(encoding="utf-8")
                self.assertNotIn(
                    '"$fail" -eq 0 ] || exit 1', body,
                    f"{path.name}: 옛 인라인 판정이 남아 있다",
                )

    def test_scripts_are_syntactically_valid(self) -> None:
        """`source` 를 잘못 넣으면 Docker 가 있는 곳에서만 터진다."""
        for path in (*ROOMS, LIB):
            with self.subTest(script=path.name):
                r = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
