#!/usr/bin/env python3
"""검사 순서에 기대는 공유 상태가 있는가 — **역순**과 **모듈 단독**으로 돌려 본다 (큐 #127).

`unittest discover` 는 언제나 같은 순서(파일 이름순)로 돈다. 그래서 「앞 검사가 `sys.modules` 에 스텁을
꽂아 둔 덕에 뒤 검사가 통과」하는 모양은 평소엔 안 보인다. 이 도구는 세 번 돈다:

1. 정순 (run_tests 와 같은 순서)
2. **역순**
3. `--isolated` 를 주면 **모듈마다 새 프로세스**로 (느리다 · 2–3분)

셋 중 하나라도 실패·오류가 있으면 exit 1. 실측 2026-09-06: 정순 1184 · 역순 1184 · 단독 120/120 — 전부 0 실패.

    python3 scripts/check_test_order.py              # 정순 + 역순
    python3 scripts/check_test_order.py --isolated   # + 모듈 단독
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def _flat() -> list[unittest.TestCase]:
    out: list[unittest.TestCase] = []

    def walk(s: unittest.TestSuite) -> None:
        for t in s:
            if isinstance(t, unittest.TestSuite):
                walk(t)
            else:
                out.append(t)

    walk(unittest.TestLoader().discover(str(TESTS)))
    return out


def _run(tests: list[unittest.TestCase], label: str) -> int:
    r = unittest.TextTestRunner(verbosity=0, stream=io.StringIO()).run(unittest.TestSuite(tests))
    bad = len(r.failures) + len(r.errors)
    print(f"{label}: ran {r.testsRun} · failures {len(r.failures)} · errors {len(r.errors)} · skipped {len(r.skipped)}")
    for t, _ in r.failures + r.errors:
        print(f"  X {t.id()}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--isolated", action="store_true", help="모듈마다 새 프로세스로도 돌린다 (느림)")
    a = ap.parse_args()
    tests = _flat()
    if not tests:
        print("검사를 하나도 못 실었다", file=sys.stderr)
        return 1
    bad = _run(tests, "정순")
    bad += _run(list(reversed(tests)), "역순")
    if a.isolated:
        mods = sorted(p.stem for p in TESTS.glob("test_*.py"))
        failed = []
        for m in mods:
            proc = subprocess.run([sys.executable, "-m", "unittest", "-q", m], cwd=TESTS, capture_output=True, text=True, timeout=600)
            if proc.returncode != 0:
                failed.append(m)
        print(f"단독: {len(mods) - len(failed)}/{len(mods)} 통과" + (f" · 실패 {failed}" if failed else ""))
        bad += len(failed)
    print("순서 의존 없음" if bad == 0 else f"순서 의존 의심 {bad}건")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
