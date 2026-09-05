r"""건너뛴 건수가 **배너까지 올라오는가** (큐 #58 · Wave Z 이어서).

## 왜 있는가

`OK (skipped=7)` 은 **초록으로 지나간다.** 2026-09-01 에 실제로 6건이 조용히 빠졌고
아무도 그 숫자를 안 읽었다 — 그래서 `run_tests.sh` 가 그 수를 맨 아래 배너로 끌어올린다.

**그런데 그 배너가 통과했을 때만 찍혔다.**

```bash
skipped="$(… sed -n 's/.*skipped=\([0-9][0-9]*\).*/\1/p' | tail -1)"   # FAILED 에서도 뽑는다
…
if [[ "$fail" -ne 0 ]]; then echo "실패 …" >&2; exit 1; fi              # ← 여기서 끝난다
echo "전부 통과."
if [[ "$skipped" -gt 0 ]]; then …                                       # ← 실패하면 안 찍힌다
```

`FAILED (failures=1, skipped=7)` 두 모양을 다 잡으라고 sed 를 고쳐 놓고, 정작 그 결과를
**실패한 회차에는 한 번도 안 보여 줬다.** 고칠 게 있는 회차일수록 「무엇이 안 돌았는가」가
필요하다. 순서를 바꿨다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| `tests/` 의 **정적 skip 자리** | **7** |
| 그 사유 | **2종** — `psycopg 없음`(5) · `capreq 를 못 읽었다`(2) |
| 이 환경의 런타임 건너뜀 | **7** — 전부 발동한다 |
| `ALLOWED` 의 사유 | **4** (나머지 둘은 `capreq/tests` 쪽) |

정적 자리 수는 **상한**이다 — 의존성이 있는 환경에서는 그만큼 덜 건너뛴다. 런타임이
상한을 넘으면 **목록에 없는 자리에서** 건너뛴 것이다.

## 무엇을 고정하나

1. 건너뜀 줄이 **실패 분기보다 앞**에 있다 — 실패해도 보인다
2. 배너가 `ALLOWED` 와 `testing.md` 를 **가리킨다**
3. sed 가 `OK (…)` · `FAILED (…)` **둘 다**에서 숫자를 뽑는다 (실제로 돌려 본다)
4. 정적 skip 자리의 사유가 전부 `ALLOWED` 에 있다 · 자리 수가 조용히 늘지 않는다
"""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402
RUN_TESTS = ROOT / "scripts" / "run_tests.sh"
TESTS = ROOT / "tests"

sys.path.insert(0, str(TESTS))
from test_skip_reasons import ALLOWED, SKIP_CALLS  # noqa: E402

# 오늘 실측. 의존성이 깔린 환경에서는 **덜** 건너뛴다 — 이 수는 상한이다.
STATIC_SITES = 7


def _skip_sites() -> list[tuple[str, int, str]]:
    """`(파일, 줄, 사유)` — `tests/` 안의 skip 자리 전부."""
    out: list[tuple[str, int, str]] = []
    for path in sorted(TESTS.rglob("test_*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else \
                (func.id if isinstance(func, ast.Name) else "")
            if name not in SKIP_CALLS:
                continue
            reasons = [a.value for a in node.args
                       if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if reasons:
                out.append((path.name, node.lineno, reasons[-1]))
    return out


def _sed(sample: str) -> str:
    """`run_tests.sh` 가 쓰는 **그 sed 그대로** 돌린다."""
    line = next(l for l in RUN_TESTS.read_text(encoding="utf-8").splitlines()
                if l.startswith("skipped="))
    script = f'unit_out={sample!r}\n{line}\nprintf "%s" "${{skipped:-}}"'
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                          timeout=60).stdout


class TestTheNumberIsPrintedEvenOnFailure(unittest.TestCase):
    def test_skip_block_comes_before_the_failure_exit(self) -> None:
        """**여기가 핵심이다.** 고칠 게 있는 회차일수록 그 수가 필요하다."""
        body = RUN_TESTS.read_text(encoding="utf-8")
        skip_at = body.index('if [[ "$skipped" -gt 0 ]]')
        fail_at = body.index('if [[ "$fail" -ne 0 ]]')
        self.assertLess(skip_at, fail_at,
                        "건너뜀 줄이 실패 분기 뒤에 있다 — 실패하면 아무도 못 본다")

    def test_the_banner_points_at_the_reason_list(self) -> None:
        body = RUN_TESTS.read_text(encoding="utf-8")
        self.assertIn("tests/test_skip_reasons.py", body)
        self.assertIn("docs/guide/testing.md", body)


class TestTheExtractionActuallyWorks(unittest.TestCase):
    """sed 를 눈으로 읽고 「맞겠지」 하지 않는다 — 돌려 본다."""

    def test_ok_form(self) -> None:
        self.assertEqual("7", _sed("Ran 835 tests in 9.4s\n\nOK (skipped=7)\n"))

    def test_failed_form(self) -> None:
        """이 모양을 뽑으라고 sed 를 고쳤는데, 쓰는 자리가 없었다."""
        self.assertEqual("7", _sed("FAILED (failures=1, skipped=7)\n"))

    def test_no_skips_gives_nothing(self) -> None:
        self.assertEqual("", _sed("Ran 10 tests in 0.1s\n\nOK\n"))

    def test_the_last_one_wins(self) -> None:
        """검사 **출력**에 그 낱말이 섞여도 요약이 마지막이다."""
        self.assertEqual("2", _sed("some test printed skipped=99\nOK (skipped=2)\n"))


class TestStaticSitesMatchTheAllowlist(unittest.TestCase):
    def test_every_site_reason_is_allowed(self) -> None:
        sites = _skip_sites()
        self.assertTrue(sites, "skip 자리를 하나도 못 찾았다 — 추출기가 죽었다")
        bad = sorted({f"{f}:{n} {r}" for f, n, r in sites if r not in ALLOWED})
        self.assertEqual([], bad, f"허가 안 된 사유로 건너뛴다: {bad}")

    def test_site_count_did_not_grow(self) -> None:
        """자리가 늘면 배너 숫자도 는다 — 근거와 함께 이 수를 다시 적는다."""
        self.assertLessEqual(len(_skip_sites()), STATIC_SITES,
                             f"skip 자리가 {len(_skip_sites())}개로 늘었다 (상한 {STATIC_SITES})")

    def test_todays_breakdown(self) -> None:
        got = Counter(r for _, _, r in _skip_sites())
        self.assertEqual({"psycopg 없음 — 의존성 있는 환경에서만 돈다": 5,
                          "capreq 를 못 읽었다": 2}, dict(got))


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_sites_are_seen(self) -> None:
        self.assertGreaterEqual(len(_skip_sites()), 5, _skip_sites())

    def test_sed_line_is_found(self) -> None:
        self.assertIn("skipped=", hash_comment_free(RUN_TESTS))
        self.assertEqual("3", _sed("OK (skipped=3)"))


if __name__ == "__main__":
    unittest.main()
