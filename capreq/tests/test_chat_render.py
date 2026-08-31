"""`chat.html` 렌더러를 **실행**해 본다 — `node` 가 있을 때만.

## 왜 있는가

옆 파일 `test_chat_html_unit.py` 는 **문자열 검사**다. 서버 요약의 칸마다 `result.X` 가
파일에 있는지만 보므로 **「반쯤 지운 렌더러」를 통과시킨다** — 그 한계를 그 파일이 스스로
적어 뒀다. 여기는 `capreq/tests/chat_render_probe.js` 를 **실제로 돌려** 만들어진 DOM 을 본다.

#107 · #112 · #118 · #128 — 네 번 연속으로 「브라우저 렌더링은 못 봤다」고 적은 자리다.

## 왜 파이썬이 JS 를 부르나

루트 `run_tests` 는 **의존성을 설치하지 않는다.** `node` 가 있는 곳에서만 돌고 없으면
**건너뛴다** — 기존 skip 7 과 같은 취급이다. CI 의 `capreq` 잡에는 `node` 가 있으므로
거기서는 **실제로 돈다.**

## 여전히 못 보는 것

실제 브라우저의 **CSS·레이아웃**과 **사용자 상호작용**(드래그앤드롭·폼 제출).
그래서 이게 통과해도 **「브라우저에서 봤다」고 쓰지 않는다.**
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "chat_render_probe.js"
NODE = shutil.which("node")


@unittest.skipIf(NODE is None, "node 가 없다 — 렌더러 실행 검사를 건너뛴다")
class TestChatRendersForReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.proc = subprocess.run(  # noqa: S603 — 저장소 안의 파일만 돌린다
            [NODE, str(PROBE)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(HERE),
        )

    def test_probe_succeeds(self) -> None:
        self.assertEqual(
            self.proc.returncode, 0,
            f"렌더러 실행 실패\n--- stdout ---\n{self.proc.stdout}\n--- stderr ---\n{self.proc.stderr}",
        )

    def test_probe_actually_asserted_things(self) -> None:
        """0건을 통과시키는 상태를 막는다."""
        self.assertIn("결과: 통과", self.proc.stdout, self.proc.stderr)
        line = [x for x in self.proc.stdout.splitlines() if "결과: 통과" in x][-1]
        passed = int(line.split("통과")[1].split("·")[0].strip())
        self.assertGreaterEqual(passed, 25, line)

    def test_probe_says_what_it_did_not_see(self) -> None:
        """「브라우저에서 봤다」로 읽히지 않게 도구가 스스로 말한다."""
        self.assertIn("브라우저에서 본 것은 아니다", self.proc.stdout)


class TestProbeIsHonest(unittest.TestCase):
    """`node` 없이도 볼 수 있는 것 — 프로브가 무엇을 주장하는지."""

    def setUp(self) -> None:
        self.text = PROBE.read_text(encoding="utf-8")

    def test_no_npm_dependency(self) -> None:
        """Playwright·jsdom 을 들이지 않는다 — 최소 스텁만 쓴다."""
        for pkg in ("playwright", "jsdom", "puppeteer", "require(\"@"):
            self.assertNotIn(pkg, self.text, f"{pkg} 를 들였다")

    def test_only_stdlib_requires(self) -> None:
        import re

        mods = set(re.findall(r'require\("([^"]+)"\)', self.text))
        self.assertTrue(mods <= {"fs", "path"}, f"node 표준 모듈 밖: {mods - {'fs', 'path'}}")

    def test_records_the_limits(self) -> None:
        self.assertIn("못 보나", self.text)
        self.assertIn("CSS", self.text)


if __name__ == "__main__":
    unittest.main()
