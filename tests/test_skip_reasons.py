"""테스트를 건너뛰는 **사유**는 허가된 것만 쓴다.

## 왜 있는가

**`skip` 은 통과가 아니다.** 그런데 출력에서는 통과처럼 보인다 — `OK (skipped=7)`.

**실제로 가려졌다 (2026-09-01).** 세션 도중 환경이 바뀌어 `node` 가 사라졌고,
`capreq` 스위트가 **68 → 50 ran / 6 skipped** 로 줄었다. 줄어든 6건은
`chat.html` 렌더러와 흐름을 **실제로 실행**하는 프로브 — 이 저장소가
「문자열 검사로는 반쯤 지운 렌더러를 못 잡는다」고 판단해 일부러 넣은 것들이다.
아무 경고도 없었다. **가장 값나가는 검사가 조용히 빠져 있었다.**

## 무엇을 하나

사유 문자열을 **허가 목록**으로 만든다. 새 `skip` 을 넣으려면 사유를 여기 적어야 한다 —
그때 「이건 환경 문제인가, 아니면 깨진 검사를 덮는 것인가」를 한 번 묻게 된다.

`testing.md` §4.6 이 이미 글로 정한 규칙(「이 부류를 늘릴 때의 규칙」)을 기계가 잇는 것이다.

## 무엇을 안 하나

- **개수를 못박지 않는다.** 몇 건이 건너뛰어지는지는 환경마다 다르다 — 그게 정상이다.
  못박으면 psycopg 가 있는 환경에서 거짓 실패가 난다
- **`skip` 자체를 금지하지 않는다.** 「의존성 설치 없음」을 지키는 수단이라 필요하다
- 텍스트로 훑지 않는다 — `ast` 로 **호출**만 본다. 설명 문단에 `skip` 이라 적었다고
  걸리면 안 된다 (`tests/_srcguard.py` 의 사고 5건)
"""

from __future__ import annotations

import ast
import re
import warnings
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREES = (ROOT / "tests", ROOT / "capreq" / "tests")

# `raise unittest.SkipTest(…)` 도 센다 (큐 #60) — 모듈 전체를 건너뛰는 자리가
# 여기 셋 있고, 그건 「사유를 안 적어도 되는 문법」이 아니다.
SKIP_CALLS = {"skip", "skipIf", "skipUnless", "skipTest", "SkipTest"}

# 사유 → **왜 건너뛰어도 되는가**. 새 줄을 넣기 전에 이 물음에 답한다:
#   「이건 그 환경에 없는 것인가, 아니면 깨진 검사를 덮는 것인가?」
# **어디서 도는가**를 함께 적는다 (큐 #26 · 2026-09-03).
#
# 「CI 가 본다」고 적어 두면 그 순간부터 아무도 다시 안 센다. 실제로 그랬다 —
# 아래 첫 줄은 「CI 의 migrate 잡에서는 실제로 돈다」였는데 **거짓이었다.**
# migrate 잡은 `scripts/run_integration.sh`(= `tests/integration/check_*.py`)를 돌리지
# `tests/` 를 discover 하지 않는다. `tests/` 를 보는 것은 `unit` 잡 하나뿐이고
# 그 잡은 **아무것도 설치하지 않는다.**
#
# `runs_in` 값의 뜻:
#   "<잡 이름>"  — 그 CI 잡이 이 검사를 **실제로 돌린다** (아래 검사가 대조한다)
#   None         — **어디에서도 안 돈다.** 숨기지 않는다
ALLOWED: dict[str, tuple[str, str | None]] = {
    "psycopg 없음 — 의존성 있는 환경에서만 돈다": (
        "루트 `run_tests` 의 「의존성 설치 없음」을 지킨다. **CI 어디에서도 안 돈다** — "
        "`tests/` 를 보는 것은 unit 잡뿐이고 그 잡은 아무것도 설치하지 않는다. "
        "같은 경로를 DB 로 보는 `tests/integration/check_*.py` 는 **다른 파일**이다.",
        None,
    ),
    "capreq 를 못 읽었다": (
        "`route_bench` 하네스 검사는 capreq 를 import 한다. 별 모듈이라 없을 수 있다. "
        "capreq 잡은 `capreq/tests` 만 discover 하므로 **이 파일은 거기서도 안 돈다.**",
        None,
    ),
    "node 가 없다 — 렌더러 실행 검사를 건너뛴다": (
        "`chat.html` 을 최소 DOM 스텁으로 실행한다.",
        "capreq",
    ),
    "node 가 없다 — 흐름 실행 검사를 건너뛴다": (
        "위와 같다 — 보내기→라우팅→폴링→결과 경로 전체.",
        "capreq",
    ),
    "httpx 없음 — capreq 런타임 핀이 깔린 환경에서만 돈다": (
        "`capnet` 어댑터·라우터 검사가 `httpx` 를 import 한다. 예전에는 그대로 터져 "
        "로컬 실행이 `FAILED (errors=3)` 였다 — 그건 「코드가 깨졌다」처럼 보인다 (큐 #60). "
        "capreq 잡은 핀을 깔므로 **거기서는 실제로 돈다.**",
        "capreq",
    ),
    "fastapi 없음 — capreq 런타임 핀이 깔린 환경에서만 돈다": (
        "서버 경로 검사가 `fastapi.testclient` 를 쓴다. 위와 같은 이유·같은 잡.",
        "capreq",
    ),
}

# 각 CI 잡이 **discover 하는 트리**. `runs_in` 대조에 쓴다.
CI = ROOT / ".github" / "workflows" / "ci.yml"
JOB_TREES = {
    "unit": "tests",
    "capreq": "capreq/tests",
}


def skip_reasons() -> list[tuple[str, int, str]]:
    """`(파일, 줄, 사유)` — `ast` 로 호출만 본다."""
    found: list[tuple[str, int, str]] = []
    for tree_root in TREES:
        for path in sorted(tree_root.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # 문법이 깨졌으면 다른 검사가 잡는다
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                if name not in SKIP_CALLS:
                    continue
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.append((str(path.relative_to(ROOT)), node.lineno, arg.value))
    return found


def _ci_text() -> str:
    return CI.read_text(encoding="utf-8")


def _job_block(job: str) -> str:
    """`ci.yml` 의 한 잡 블록. 다음 잡(두 칸 들여쓴 `이름:`)까지."""
    text = _ci_text()
    start = text.find(f"\n  {job}:\n")
    if start < 0:
        return ""
    rest = text[start + 1:]
    nxt = re.search(r"^  [a-z][a-z0-9_-]*:\s*$", rest[len(f"  {job}:") :], re.M)
    return rest if nxt is None else rest[: len(f"  {job}:") + nxt.start()]


class TestWhereEachSkipActuallyRuns(unittest.TestCase):
    """**「CI 가 본다」를 적어 두면 아무도 다시 안 센다.**

    실제로 그랬다 — `psycopg 없음` 의 근거가 「CI 의 migrate 잡에서는 실제로 돈다」였는데
    migrate 잡은 `tests/` 를 **discover 하지 않는다** (`run_integration.sh` = 다른 파일).
    이 검사는 그 주장을 `ci.yml` 과 대조한다.
    """

    def test_named_job_exists_and_covers_the_tree(self) -> None:
        for reason, (_why, job) in ALLOWED.items():
            if job is None:
                continue
            with self.subTest(reason=reason):
                block = _job_block(job)
                self.assertTrue(block, f"ci.yml 에 `{job}` 잡이 없다")
                tree = JOB_TREES.get(job)
                self.assertIsNotNone(tree, f"`{job}` 이 어느 트리를 보는지 안 적혀 있다")
                self.assertIn(f"discover -s {tree}", block,
                              f"`{job}` 잡이 {tree} 를 discover 하지 않는다")

    def test_skips_live_in_the_tree_their_job_covers(self) -> None:
        """사유가 「그 잡에서 돈다」면 그 사유를 쓰는 파일이 **그 트리 안**에 있어야 한다."""
        bad: list[str] = []
        for path, _line, reason in skip_reasons():
            entry = ALLOWED.get(reason)
            if entry is None or entry[1] is None:
                continue
            tree = JOB_TREES.get(entry[1], "")
            if not path.startswith(tree + "/"):
                bad.append(f"{path} 의 사유는 `{entry[1]}` 잡(={tree})에서 돈다고 적혀 있다")
        self.assertEqual([], bad, "\n".join(bad))

    def test_never_run_skips_say_so(self) -> None:
        """**어디에서도 안 도는 것은 그렇게 적는다.** 「못 봤다」를 숨기지 않는다."""
        thin = [
            reason for reason, (why, job) in ALLOWED.items()
            if job is None and "안 돈다" not in why
        ]
        self.assertEqual(
            [], thin,
            "CI 어디에서도 안 도는 사유인데 근거가 그렇게 말하지 않는다: " f"{thin}",
        )

    def test_every_reason_has_a_why(self) -> None:
        thin = [r for r, (why, _j) in ALLOWED.items() if len(why.strip()) < 20]
        self.assertEqual([], thin, f"근거가 너무 짧다: {thin}")

    def test_ci_probe_actually_reads_jobs(self) -> None:
        """`ci.yml` 모양이 바뀌어 잡을 못 읽으면 위 검사들이 **공허하게** 통과한다."""
        for job in JOB_TREES:
            with self.subTest(job=job):
                self.assertTrue(_job_block(job), f"`{job}` 잡 블록을 못 읽었다")
        self.assertEqual("", _job_block("nope-not-a-job"))


class TestSourcesAreClean(unittest.TestCase):
    """검사 소스에 **파이썬 경고**가 남아 있지 않은가.

    `test_input_contract_rejections_actually_run` 의 머리말에 `grep … "a\\|b"` 를 적었더니
    `SyntaxWarning: invalid escape sequence` 가 났다. 지금은 경고지만 **다음 세대에서는
    에러**다. 검사 스위트가 경고를 흘리면 진짜 경고가 묻힌다.
    """

    def test_no_syntax_warnings_in_test_sources(self) -> None:
        noisy: list[str] = []
        for tree_root in TREES:
            for path in sorted(tree_root.rglob("*.py")):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    try:
                        ast.parse(path.read_text(encoding="utf-8"))
                    except SyntaxError:
                        continue
                    for w in caught:
                        if issubclass(w.category, SyntaxWarning):
                            noisy.append(f"{path.relative_to(ROOT)}: {w.message}")
        self.assertEqual([], noisy, "\n".join(noisy))


class TestSkipReasonsAreDeclared(unittest.TestCase):
    def test_every_reason_is_allowed(self) -> None:
        """허가 목록에 없는 사유 — 「환경이 없다」가 아니라 「검사를 덮었다」일 수 있다."""
        unknown = [(f, ln, r) for f, ln, r in skip_reasons() if r not in ALLOWED]
        self.assertEqual(
            unknown, [],
            "허가되지 않은 skip 사유. 환경 문제가 맞으면 ALLOWED 에 **왜 괜찮은지**와 함께 적는다: "
            f"{unknown}",
        )

    def test_no_dead_entries(self) -> None:
        """안 쓰이는 사유가 남으면 목록이 곧 낡는다 — 지운 검사의 흔적이다."""
        used = {r for _f, _ln, r in skip_reasons()}
        dead = sorted(set(ALLOWED) - used)
        self.assertEqual(dead, [], f"아무도 안 쓰는 사유 {len(dead)}개 — 지운다: {dead}")

    def test_probe_actually_finds_things(self) -> None:
        """0건을 훑으며 통과하는 상태를 막는다 — 파서가 조용히 죽으면 이 검사가 무의미하다."""
        found = skip_reasons()
        self.assertGreater(len(found), 5, f"skip 호출을 {len(found)}개밖에 못 찾았다")
        self.assertGreaterEqual(len({f for f, _ln, _r in found}), 3, "한 파일에서만 찾았다")


if __name__ == "__main__":
    unittest.main()
