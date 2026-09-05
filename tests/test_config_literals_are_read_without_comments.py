r"""`#` 주석 파일에서 **설정을 볼 때는 주석을 걷는다** (배치 B #76 · G1 확장).

## 왜 있는가

`#258`(G1)이 `_srcguard.hash_comment_free()` 를 만들며 두 자리를 고쳤다. **나머지는
안 봤다.** 이번에 훑었더니 `.sh`·`.yaml` 에서 리터럴을 「있는가」로 보는 자리가 **열넷**
있었고, 그중 **셋이 실제로 속았다**:

| 심은 것 | 그 전 | 무엇이 되나 |
|---|---|---|
| `# python -m app.migrate status` | 통과 | migrate 가 baseline 을 **못 본 채 `up`** 을 돈다 |
| `# source …/lib/tally.sh` | 통과 | `tally_verdict` 가 없어 **「0건 통과」 방어가 사라진다** |
| `# source …/lib/http.sh` (`node_bind`) | 통과 | 키가 **공통 래퍼를 안 거친다** |

`!override`(`#233`)와 `check_release` 호출(`#215` 계열)은 **다른 검사가 잡았다** — 셋만
구멍이었다.

## 규칙

| 무엇을 보나 | 어떻게 |
|---|---|
| 설정이 **있다** (`source …` · `restart:` · `ports:` …) | `hash_comment_free` 로 **걷고** |
| **이유·경고가 적혀 있다** (initdb 함정 · `-e` 를 안 켠 근거) | **원문** — 주석이 본체다 |

아래 `COMMENT_IS_THE_POINT` 가 후자를 **함수 단위로** 못박는다. 새로 생긴 자리가 그 표에
없으면 운다.

## 무엇을 안 보나

- **파이썬**을 읽는 검사 — `code_only()` 가 따로 있다 (`_srcguard`)
- **문서**(README·INDEX·체크리스트)를 읽는 검사 — 거기선 산문이 본체다
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
sys.path.insert(0, str(TESTS))
from _srcguard import code_only  # noqa: E402

# `#` 이 주석인 파일을 가리키는 이름·경로 조각.
HASH_FILE = re.compile(
    r"\.sh['\"]|\.ya?ml['\"]|workflows|\bCOMPOSE\b|\bPROD\b|\bRUN_TESTS\b|"
    r"\bWRAPPER\b|\bBIND\b|\bONBOARD\b|\bRUNNER\b|\bCI\b")
READS = re.compile(r"read_text|\bbody\b")

# **주석이 본체인** 자리 — 걷으면 안 된다. `테스트파일::함수` 로 못박는다.
COMMENT_IS_THE_POINT = {
    "test_compose_healthchecks_can_fail.py::test_the_caveat_comment_is_there":
        "initdb 함정 주석이 남아 있는가 — 주석 자체를 본다",
    "test_node_secrets_live_in_files.py::test_the_reason_stays_written":
        "「환경변수로 주면 docker inspect 에 뜬다」가 적혀 있는가 — 같은 부류",
    "test_capability_demos_are_ready_to_add.py::test_capreq_demo_does_need_it":
        "`capreq_demo` 가 Ollama 를 쓴다는 표시 — 주석이어도 맞다",
    "test_checklist_claims.py::test_checklist_points_at_it":
        "체크리스트(문서)를 읽는다 — 거기선 산문이 본체다",
    "test_doc_counts.py::test_release_check_is_indexed":
        "INDEX(문서)를 읽는다 — 같은 이유",
    "test_product_demo.py::test_readme_points_at_it":
        "README(문서)를 읽는다 — 같은 이유",
}


def _offenders() -> list[str]:
    """`#` 주석 파일의 리터럴을 **안 걷고** 보는 자리."""
    out: list[str] = []
    for path in sorted(TESTS.glob("test_*.py")):
        src = code_only(path)
        try:
            tree = ast.parse(src)
        except SyntaxError:                       # 걷어낸 뒤 깨지면 원문으로
            tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef):
                continue
            # **함수 단위로** 본다 — 한 줄만 걷어도 그 함수는 걷는 쪽이다.
            # 줄 단위로 보면 같은 함수에서 원문·걷은 것을 같이 쓰는 자리를 못 읽는다.
            if "hash_comment_free" in ast.unparse(fn):
                continue
            for node in ast.walk(fn):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                    continue
                if node.func.attr not in ("assertIn", "assertTrue", "assertNotIn"):
                    continue
                code = ast.unparse(node)
                if "hash_comment_free" in code:
                    continue
                if not (HASH_FILE.search(code) and READS.search(code)):
                    continue
                out.append(f"{path.name}::{fn.name}")
                break
    return sorted(set(out))


class TestSettingsAreReadCommentFree(unittest.TestCase):
    def test_no_unguarded_setting_check(self) -> None:
        """**여기가 핵심이다.** 설정을 `#` 로 꺼도 통과하는 검사를 못 만들게 한다."""
        found = _offenders()
        self.assertTrue(found, "탐지기가 아무것도 못 찾았다 — 패턴이 죽었다")
        new = [f for f in found if f not in COMMENT_IS_THE_POINT]
        self.assertEqual([], new,
                         "주석을 안 걷고 설정을 본다 — `hash_comment_free` 를 쓰거나 "
                         f"`COMMENT_IS_THE_POINT` 에 이유와 함께 적는다: {new}")

    def test_the_exception_table_has_no_ghosts(self) -> None:
        found = set(_offenders())
        self.assertTrue(found, "탐지기가 아무것도 못 찾았다")
        ghosts = sorted(k for k in COMMENT_IS_THE_POINT if k not in found)
        self.assertEqual([], ghosts, f"사라진 자리가 표에 남아 있다: {ghosts}")

    def test_every_exception_says_why(self) -> None:
        blank = sorted(k for k, why in COMMENT_IS_THE_POINT.items() if len(why.strip()) < 8)
        self.assertEqual([], blank, f"이유가 비었다: {blank}")


class TestTheGuardIsActuallyUsed(unittest.TestCase):
    """고친 셋이 되돌아가면 다시 속는다."""

    FIXED = {
        "test_compose_healthchecks_can_fail.py": "migrate 대기 루프",
        "test_room_tally.py": "방이 tally 를 부르는가",
        "test_node_secrets_live_in_files.py": "node_bind 가 공통 래퍼를 부르는가",
    }

    def test_each_fixed_file_uses_the_guard(self) -> None:
        fixed = self.FIXED.items()
        self.assertTrue(fixed, "고친 자리 목록이 비었다")
        for name, what in fixed:
            with self.subTest(check=name, sees=what):
                self.assertIn("hash_comment_free", code_only(TESTS / name),
                              f"{name} 이 주석을 다시 안 걷는다 — {what}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_the_detector_finds_something(self) -> None:
        found = _offenders()
        self.assertTrue(found, "탐지기가 아무것도 못 찾았다 — 패턴이 죽었다")
        self.assertGreaterEqual(len(found), 4, found)

    def test_the_detector_ignores_guarded_calls(self) -> None:
        """걷은 호출을 위반으로 세면 고친 자리가 다시 걸린다."""
        self.assertNotIn("test_room_tally.py::test_both_rooms_source_and_call_it", _offenders())


if __name__ == "__main__":
    unittest.main()
