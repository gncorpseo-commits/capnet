r"""통합 검사(`tests/integration/check_*.py`)에 **건너뜀 통로가 없다** (배치 B #93 · `#215`/`#261` 옆).

## 왜 있는가

단위 검사의 skip 은 `test_skip_reasons` 가 사유를 `ALLOWED` 와 대조한다. 통합 검사는 `unittest` 가
아니라 **스크립트**라 그 그물 밖처럼 보였다. 실측(2026-09-06):

| 무엇 | 값 |
|---|---|
| `SkipTest`·`skipTest`·`skipUnless`·`@skip` 호출 | **0** (15 파일) |
| 판정(`check(`·`record(`)을 안 적고 `return 0`/`sys.exit(0)` 하는 `main` | **0** |
| `run_integration.sh` 의 집계 | `통과`·`실패` 둘뿐 — 건너뜀 칸이 **없다** |
| 「건너뛴다」는 말 | `check_capability_patch.py` 의 주석 하나 — 코드는 `check(False, …)` 로 **실패**를 적는다 → 주석을 사실대로 고쳤다 |

그러니 「스킵 메시지가 ALLOWED 와 같은 말인가」의 답은 **비교할 스킵이 없다**이고, 이 검사는 그 상태가
유지되게 한다 — 통합 검사가 환경 탓을 「건너뜀」으로 적기 시작하면 여기서 운다.

## 재현

```bash
python3 -m unittest tests.test_integration_checks_have_no_skip_channel
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "tests" / "integration"
RUNNER = ROOT / "scripts" / "run_integration.sh"
SKIP_NAMES = {"SkipTest", "skipTest", "skipUnless", "skipIf", "skip"}


def _checks() -> list[Path]:
    return sorted(INTEGRATION.glob("check_*.py"))


class TestNoSkipCalls(unittest.TestCase):
    def test_no_unittest_skip_shapes(self) -> None:
        files = _checks()
        self.assertGreaterEqual(len(files), 12, [p.name for p in files])
        hits = []
        for p in files:
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call):
                    name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                    if name in SKIP_NAMES:
                        hits.append(f"{p.name}:{node.lineno}")
                if isinstance(node, ast.Raise) and node.exc is not None and "SkipTest" in ast.dump(node.exc):
                    hits.append(f"{p.name}:{node.lineno}")
        self.assertEqual([], hits, f"통합 검사가 건너뛴다: {hits}")

    def test_every_main_calls_check_before_returning_zero(self) -> None:
        """`check(` 없이 `return 0` 하는 main 은 「아무것도 안 보고 통과」다."""
        for p in _checks():
            with self.subTest(file=p.name):
                src = p.read_text(encoding="utf-8")
                # 판정 기록 함수는 둘이다 — `check(` (14 파일) · `record(` (`check_pg_violations`).
                self.assertGreaterEqual(len(re.findall(r"\b(?:check|record)\(", src)), 3,
                                        f"{p.name} 이 판정을 거의 안 적는다")
                self.assertNotRegex(src, r"^\s*sys\.exit\(0\)", f"{p.name} 이 조기 exit(0) 한다")

    def test_the_word_skip_never_describes_a_pass(self) -> None:
        """「건너뛴다」고 적힌 줄이 있으면 그 자리는 실패를 적어야 한다."""
        for p in _checks():
            for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if "건너뛴다" in ln and "#" in ln and "except" in ln:
                    with self.subTest(site=f"{p.name}:{i}"):
                        self.assertIn("실패로 적는다", ln, f"{p.name}:{i} 주석이 건너뛴다고 말한다")


class TestRunnerCountsOnlyPassAndFail(unittest.TestCase):
    def test_no_skip_bucket(self) -> None:
        body = RUNNER.read_text(encoding="utf-8")
        self.assertIn("통합 검사: 통과 %d · 실패 %d", body)
        self.assertNotRegex(body, r"skip=|건너뜀|skipped", "러너에 건너뜀 칸이 생겼다 — 사유 대조가 필요하다")
        self.assertIn('if DATABASE_URL="$(url_for "$db")" python3 "$script"; then', body)


class TestUnitScannerStillCoversTheTree(unittest.TestCase):
    def test_skip_reasons_scans_integration_too(self) -> None:
        src = (ROOT / "tests" / "test_skip_reasons.py").read_text(encoding="utf-8")
        self.assertIn('rglob("*.py")', src, "단위 스캐너가 하위 폴더를 안 본다")


if __name__ == "__main__":
    unittest.main()
