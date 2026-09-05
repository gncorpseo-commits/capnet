r"""`rc=$?` 가 **`set -e` 아래서 죽지 않는가** (배치 B #71 · `#44`·`#228` 잔여).

## 왜 있는가

`#228`(큐 #44)은 `prod_room.sh` 만 `set -e` 를 안 켠 것을 찾고 **「못 쟀다」**로 남겼다 —
Docker 가 없어 `-e` 를 켠 채 51/51 을 다시 못 돌렸기 때문이다. 이번에는 **왜 못 켜는지를
정적으로** 증명했다.

## `-e` 를 켜면 §12 에서 죽는다 — 재 볼 필요 없이 확실하다

```bash
CAPNET_API_KEY="$key" bash "$root/scripts/demo.sh" > "…/prod_demo.log" 2>&1
rc=$?                                   # ← set -e 면 여기 못 온다
chk "demo.sh 강제 모드 통과" test "$rc" = "0"
```

`demo.sh` 가 실패하는 **바로 그때** `-e` 가 셸을 죽인다. `rc=$?` 도, 로그 tail 도,
`chk` 도 안 돈다 — **tally 한 줄조차 안 찍힌다.** 실패를 세려고 만든 자리가
실패할 때 사라지는 것이다.

`clean_room.sh` 가 `-e` 를 켜고도 멀쩡한 이유는 **전부 `step "…" cmd` → `if "$@"`** 이기
때문이다. `if` 조건 안의 실패는 errexit 를 발동하지 않는다.

**그래서 `prod_room` 의 `-e` 없음은 결함이 아니라 구조의 결과다.** 켜려면 §12 를 먼저
`chk` 어법으로 옮겨야 하고, 그건 Docker 가 있는 회차에 51/51 을 다시 재면서 할 일이다.

## `rc=$?` 전수 (2026-09-06)

| 무엇 | 수 |
|---|---|
| `scripts/*.sh` 의 `rc=$?` | **10** |
| `set -e` 인 스크립트 안 | **9** |
| 그중 **보호되지 않은 것** | **0** ✅ |
| 보호 방법 | `$( )` 안(치환은 죽지 않는다) · `set +e` 블록 · `\|\|` |

첫 훑기는 `pass_rate.sh`·`score_n300.sh` 를 **위반 둘**로 셀 뻔했다 — 둘 다 앞에
`set +e` 가 있는데 내 창이 여섯 줄이라 못 봤다. **창을 넓히지 않았으면 거짓 결함 둘을
적을 뻔했다.**

## 무엇을 안 보나

**실행하지 않는다.** `-e` 를 실제로 켜고 `prod_room` 을 돌리는 것은 Docker 가 필요하다
(이 세션에는 데몬이 없다 — `docker info` 실패). 여기는 **어법**만 본다.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

RC = re.compile(r"^\s*[a-z_]*rc[a-z_]*=\$\?\s*$")
SET_LINE = re.compile(r"^\s*set\s+([-+][a-z]+)")


def _lines(path: Path) -> list[str]:
    return hash_comment_free(path).splitlines()


def _errexit_on(lines: list[str], upto: int) -> bool:
    """그 줄 시점에 `-e` 가 켜져 있는가. `set +e` / `set -e` 를 순서대로 따른다."""
    on = False
    for line in lines[:upto]:
        m = SET_LINE.match(line)
        if not m:
            continue
        flags = m.group(1)
        if flags.startswith("-") and "e" in flags:
            on = True
        elif flags.startswith("+") and "e" in flags:
            on = False
    return on


def _prev_command(lines: list[str], i: int) -> str:
    for j in range(i - 1, -1, -1):
        if lines[j].strip():
            return lines[j].strip()
    return ""


def _captures() -> list[tuple[str, int, bool, str]]:
    """`(파일, 줄, errexit 켜짐, 앞 명령)`."""
    out = []
    for path in sorted(SCRIPTS.glob("*.sh")):
        lines = _lines(path)
        for i, line in enumerate(lines):
            if RC.match(line):
                out.append((path.name, i + 1, _errexit_on(lines, i), _prev_command(lines, i)))
    return out


class TestNoExitCaptureIsDeadCode(unittest.TestCase):
    """`-e` 아래 맨몸 명령 뒤의 `rc=$?` 는 **절대 안 도는 줄**이다."""

    def test_every_capture_is_protected(self) -> None:
        got = _captures()
        self.assertTrue(got, "`rc=$?` 를 하나도 못 찾았다 — 탐지기가 죽었다")
        bad = []
        for name, lineno, errexit, prev in got:
            if not errexit:
                continue
            protected = ("||" in prev) or prev.endswith(")") or prev.startswith("fi")
            if not protected:
                bad.append(f"{name}:{lineno} ← {prev[:60]}")
        self.assertEqual([], bad, "`set -e` 아래 보호 없는 종료 코드 포착: " + "; ".join(bad))

    def test_the_set_tracker_follows_toggles(self) -> None:
        """`set +e` 를 못 따라가면 **거짓 결함 둘**을 적게 된다 (실제로 겪었다)."""
        lines = ["set -euo pipefail", "x=1", "set +e", "cmd", "rc=$?", "set -e"]
        self.assertTrue(_errexit_on(lines, 1))
        self.assertFalse(_errexit_on(lines, 4), "set +e 뒤인데 켜졌다고 본다")
        self.assertTrue(_errexit_on(lines, 6))

    def test_the_two_that_looked_broken_are_fine(self) -> None:
        """`pass_rate` · `score_n300` — 둘 다 `set +e` 블록 안이다."""
        for name in ("pass_rate.sh", "score_n300.sh"):
            with self.subTest(script=name):
                lines = _lines(SCRIPTS / name)
                spots = [i for i, l in enumerate(lines) if RC.match(l)]
                self.assertTrue(spots, f"{name} 에서 rc=$? 를 못 찾았다")
                for i in spots:
                    self.assertFalse(_errexit_on(lines, i),
                                     f"{name}:{i + 1} 이 errexit 아래에 있다")


class TestProdRoomCannotTurnErrexitOnYet(unittest.TestCase):
    """`#228` 의 「못 쟀다」를 **구조의 결과**로 승격한다."""

    def test_the_blocking_shape_is_still_there(self) -> None:
        lines = _lines(SCRIPTS / "prod_room.sh")
        spots = [i for i, l in enumerate(lines) if RC.match(l)]
        self.assertTrue(spots, "prod_room 에서 rc=$? 를 못 찾았다")
        prev = _prev_command(lines, spots[0])
        self.assertIn("demo.sh", prev,
                      "§12 의 모양이 바뀌었다 — `-e` 판단을 다시 한다")
        self.assertNotIn("||", prev, "이미 보호됐다면 `-e` 를 켤 수 있다 — 재측하고 켠다")

    def test_clean_room_wraps_everything_in_a_condition(self) -> None:
        body = hash_comment_free(SCRIPTS / "clean_room.sh")
        self.assertIn('if "$@"; then', body,
                      "clean_room 이 조건 어법을 안 쓴다 — 그러면 그쪽도 -e 가 위험하다")

    def test_the_exception_reason_is_written(self) -> None:
        body = (SCRIPTS / "prod_room.sh").read_text(encoding="utf-8")
        self.assertIn("chk 는 `if \"$@\"`", body, "왜 -e 가 없는지 설명이 사라졌다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_captures_are_seen(self) -> None:
        self.assertGreaterEqual(len(_captures()), 8, len(_captures()))

    def test_comments_do_not_count(self) -> None:
        """주석 속 `rc=$?` 를 세면 위 검사가 엉뚱한 곳을 가리킨다."""
        probe = ROOT / "tests" / "__rc_probe.sh"
        probe.write_text("set -e\n# rc=$?\ncmd || rc=$?\nbare\nrc=$?\n", encoding="utf-8")
        try:
            lines = _lines(probe)
            hits = [i + 1 for i, l in enumerate(lines) if RC.match(l)]
            # 주석은 걷혀 안 세고, `cmd || rc=$?` 도 맨몸 포착이 아니다 — 마지막 하나만.
            self.assertEqual([5], hits, lines)
            self.assertTrue(_errexit_on(lines, 4), "set -e 를 못 따라간다")
        finally:
            probe.unlink()


if __name__ == "__main__":
    unittest.main()
