r"""`scripts/*.sh` 가 **중간 실패를 삼키지 않는가** (큐 #44).

## 왜 있는가

`set -e` 없이 돌면 중간 명령이 실패해도 **다음 줄로 넘어간다.** 마지막 줄이
`echo "전부 통과"` 라면 그 스크립트는 **실패한 채 초록**이다. 이 회차가 계속
잡아 온 모양이다 — `#180`(누출 검사) · `#181`(통합 러너) · `tally.sh`(0건 통과).

`set -u` 는 오타 난 변수를 빈 문자열로 흘리지 않게, `pipefail` 은 파이프
중간의 실패가 마지막 명령의 0 에 가려지지 않게 한다. 셋은 **한 줄로 같이** 쓴다.

## 실측 (2026-09-05)

| 무엇 | 수 |
|---|---|
| `scripts/*.sh` | **37** |
| 그중 `set -euo pipefail` | **36** |
| `-e` 가 빠진 것 | **1** — `prod_room.sh` (`set -uo pipefail`) |
| `scripts/lib/*.sh` (source 되는 것) | **3** — `set` 없음이 **맞다** |
| 이것을 세던 검사 | **0** |

## `prod_room.sh` 는 결함인가 — **오늘은 못 쟀다**

`chk()` 는 `if "$@"; then …` 이다. **`if` 조건 안의 실패는 `-e` 를 발동하지
않는다** — 그래서 `clean_room.sh` 는 같은 모양으로 `set -euo pipefail` 을 켜고도
집계가 멀쩡하다. 즉 `prod_room.sh` 도 켤 수 있어 **보인다.**

그러나 켠 채로 **돌려 보지 못했다.** 이 세션에는 Docker 가 없다
(`docker info` 실패 — 10회차에는 있었다). 켜면 지금 세지 않는 중간 단계
(`dc run … apikey_cli issue` 등)의 실패가 **전체를 중단**시킬 수 있고,
그건 51/51 을 다시 재 보고 정해야 한다.

**그래서 고치지 않고 못박는다.** 아래 `WITHOUT_ERREXIT` 는 오늘의 예외
**하나**를 고정한다. 새 스크립트가 조용히 `-e` 를 빼면 이 검사가 운다.

## `scripts/lib/*.sh` 는 왜 예외인가 — `set -e` 가 **호출자에게 샌다**

`source` 된 파일의 `set -e` 는 그 파일에서 끝나지 않고 **부른 셸의 옵션을
바꾼다.** 라이브러리가 호출자의 오류 처리를 바꾸면 안 된다. 그래서 셋은
`set` 을 아예 두지 않는 것이 **맞다** — 예외가 아니라 규칙이다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
LIB = SCRIPTS / "lib"

REQUIRED = "set -euo pipefail"

# 오늘의 예외. **이유가 파일 안에도 적혀 있어야** 한다 — 목록에만 적으면
# 스크립트를 읽는 사람은 왜 다른지 모른다 (`#221` 손 허용 목록과 같은 규율).
WITHOUT_ERREXIT = {
    "prod_room.sh": "큐 #44",
}


def _scripts() -> list[Path]:
    return sorted(SCRIPTS.glob("*.sh"))


def _libs() -> list[Path]:
    return sorted(LIB.glob("*.sh")) if LIB.is_dir() else []


def _set_line(path: Path) -> str | None:
    """맨 위의 `set …` 한 줄. 주석·빈 줄·shebang 은 건너뛴다."""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("set "):
            return line
        return None      # 첫 실행 줄이 `set` 이 아니면 **없는 것**이다
    return None


class TestScriptsFailLoudly(unittest.TestCase):
    def test_every_script_sets_euo_pipefail(self) -> None:
        """중간 실패를 삼키면 마지막 `echo` 하나로 **초록**이 된다."""
        bad = []
        for path in _scripts():
            if path.name in WITHOUT_ERREXIT:
                continue
            got = _set_line(path)
            if got is None or REQUIRED not in got:
                bad.append(f"{path.name}: {got!r}")
        self.assertEqual([], bad, f"`{REQUIRED}` 가 없다: {bad}")

    def test_set_line_comes_before_any_command(self) -> None:
        """`set` 이 스무 줄 아래 있으면 그 위는 **보호받지 않는다**."""
        bad = [p.name for p in _scripts() if _set_line(p) is None]
        self.assertEqual([], bad, f"첫 실행 줄이 `set` 이 아니다: {bad}")

    def test_exceptions_carry_their_reason_in_the_file(self) -> None:
        """목록에만 적힌 예외는 스크립트를 읽는 사람에게 보이지 않는다."""
        for name, marker in WITHOUT_ERREXIT.items():
            path = SCRIPTS / name
            with self.subTest(script=name):
                self.assertTrue(path.is_file(), f"{name} 이 없다")
                self.assertIn(marker, path.read_text(encoding="utf-8"),
                              f"{name} 안에 예외 근거({marker})가 없다")

    def test_exception_list_does_not_grow_silently(self) -> None:
        """오늘 예외는 **하나**다. 늘리려면 이 줄을 같이 고쳐야 한다."""
        self.assertEqual({"prod_room.sh"}, set(WITHOUT_ERREXIT))

    def test_the_exception_still_sets_u_and_pipefail(self) -> None:
        """`-e` 를 뺀 것이지 전부 끈 것이 아니다."""
        got = _set_line(SCRIPTS / "prod_room.sh") or ""
        self.assertIn("-uo", got, got)
        self.assertIn("pipefail", got, got)


class TestSourcedLibrariesDoNotSetOptions(unittest.TestCase):
    """`source` 된 `set -e` 는 **호출자의 셸 옵션을 바꾼다**."""

    def test_libs_set_nothing(self) -> None:
        bad = [p.name for p in _libs() if _set_line(p) is not None]
        self.assertEqual([], bad, f"source 되는 파일이 셸 옵션을 바꾼다: {bad}")

    def test_libs_are_actually_sourced(self) -> None:
        """아무도 안 부르는 파일이면 위 규칙은 **공허하다**."""
        libs = _libs()
        self.assertTrue(libs, "scripts/lib/*.sh 를 하나도 못 찾았다")
        text = "\n".join(p.read_text(encoding="utf-8") for p in _scripts())
        for path in libs:
            with self.subTest(lib=path.name):
                self.assertRegex(text, rf"source\s+[^\n]*lib/{re.escape(path.name)}")


class TestProbeActuallyScans(unittest.TestCase):
    """범위가 비면 위 검사가 **공허하게** 통과한다."""

    def test_enough_scripts_are_seen(self) -> None:
        self.assertGreaterEqual(len(_scripts()), 30, f"{len(_scripts())}개만 봤다")

    def test_libs_are_seen(self) -> None:
        self.assertGreaterEqual(len(_libs()), 3, f"{len(_libs())}개만 봤다")

    def test_detector_finds_a_missing_set(self) -> None:
        """`set` 이 없는 파일을 못 잡으면 위 전부가 쓸모없다."""
        self.assertIsNotNone(_set_line(SCRIPTS / "clean_room.sh"))
        self.assertIsNone(_set_line(LIB / "tally.sh"))


if __name__ == "__main__":
    unittest.main()
