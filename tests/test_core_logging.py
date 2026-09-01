"""Core 의 `logger.*` 가 **실제로 어디론가 나가는가**.

## 왜 있는가

`apps/core/app/main.py` 는 `logging.getLogger(__name__)` 만 하고 **핸들러를 붙이지
않았다.** uvicorn 은 자기 로거만 설정하고 앱 로거는 건드리지 않는다. 그래서 이 파일의
`logger.info`·`logger.exception` **15곳이 한 줄도 안 나왔다** (2026-09-02 실측 —
컨테이너 로그에 `core gc started` 도 `gc: purged=…` 도 없었다).

**무엇이 안 보였나가 중요하다.**

| 안 보이던 것 | 왜 필요한가 |
|---|---|
| `gc: purged=N freed=N bytes` | **D22 보존 정책이 실제로 도는 유일한 증거** |
| `gc: task exhausted …` | `0015` 가 「조용한 무한 재시도를 운영에서 보이게」 하려던 것 |
| `gc: pass failed` · `worker: claim failed` | **예외 경로.** 둘 다 「죽지 않는다」로 삼키고 로그로만 알린다 |

마지막 줄이 가장 나쁘다 — GC 나 워커가 **매 패스마다 터져도 아무도 몰랐을 것이다.**

고친 뒤 실측 (같은 스택 · 재기동):

```text
2026-09-01 16:26:34 INFO app.main: core gc started (interval=300s batch=50)
2026-09-01 16:26:34 INFO app.main: gc: task exhausted id=03d1de15… capability=table.extract attempts=5/5
2026-09-01 16:26:34 INFO app.main: gc: timed_out=0 exhausted=1 purged=0 freed=0 bytes
```

## 무엇을 보나

소스에서 본다 — 이 검사가 도는 환경에는 `fastapi`·`psycopg` 가 없어서 `app.main` 을
import 할 수 없다 (루트 `run_tests` 의 「의존성 설치 없음」).

1. 모듈 수준에서 **로깅을 설정**하는가
2. 레벨을 **환경변수로** 받는가 (운영에서 낮출 수 있어야 한다)
3. **`force=True` 를 쓰지 않는가** — uvicorn 이 붙인 핸들러를 걷어내면 접근 로그가 사라진다
4. 예외 경로가 **여전히 로그를 남기는가**
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"


class TestSwallowedFailuresAreObserved(unittest.TestCase):
    """**삼키는 것은 되는데, 조용히 삼키는 것은 안 된다.**

    `complete.py` 가 정한 규약은 두 절반이다 — 「`audit_log` 삽입 실패는 **관측 공백으로
    남기고** Task 를 뒤집지 않는다」. 호출부가 `logger.warning(..., exc_info=True)` 를 남긴다.

    `gate.py` 의 폐기 경로는 「complete.py 와 같은 규약」이라 적어 놓고 `pass` 만 했다 —
    **관측 절반이 빠져 있었다** (2026-09-02). 능력이 폐기됐는데 그 사실이 `audit_log` 에도
    로그에도 없는 상태가 될 수 있었다.
    """

    def swallow_sites(self) -> list[tuple[str, str]]:
        import ast

        out: list[tuple[str, str]] = []
        for path in sorted((ROOT / "apps" / "core" / "app").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler):
                    continue
                if any(isinstance(x, ast.Raise) for x in ast.walk(node)):
                    continue
                logs = any(
                    isinstance(x, ast.Attribute)
                    and x.attr in ("info", "warning", "error", "exception", "debug")
                    for x in ast.walk(node)
                )
                prints = any(
                    isinstance(x, ast.Call) and getattr(x.func, "id", "") == "print"
                    for x in ast.walk(node)
                )
                if not logs and not prints:
                    out.append((path.name, f"{path.name}:{node.lineno}"))
        return out

    def test_gate_revoke_audit_swallow_is_logged(self) -> None:
        """폐기는 됐는데 `audit_log` 에도 로그에도 없는 상태를 막는다.

        `complete.py` 자신은 삼키지 않는다 — 삼킴은 `main.py` 호출부에 있고
        거기서는 `logger.warning(..., exc_info=True)` 를 남긴다. 빠져 있던 것은
        `gate.py` 쪽 한 자리다.
        """
        src = (ROOT / "apps" / "core" / "app" / "gate.py").read_text(encoding="utf-8")
        self.assertIn("logging.getLogger", src, "gate.py 에 로거가 없다")
        self.assertIn("audit_log insert failed", src, "삼킨 것을 알리지 않는다")

    def test_known_silent_sites_do_not_grow(self) -> None:
        """조용한 자리가 **늘지 않는가.**

        전부 없애자는 것이 아니다 — 제어 흐름으로 쓰는 것(`FileNotFoundError → False`)은
        정상이다. 이 검사는 **새로 느는 것**을 보게 하려는 것이다.
        """
        sites = {s for _f, s in self.swallow_sites()}
        allowed = {
            # 제어 흐름 — 「시작할 수 없다」를 None 으로 알린다. 호출부가 4xx 로 바꾼다.
            "gate.py:210",
            # 파일이 없으면 「없다」가 답이다 — 예외가 아니다.
            "inputs.py:182",
            # 롤백 뒤 stderr 로 알리고 종료 코드 1 을 낸다 (CLI 라 print 가 맞다).
            "migrate.py:265",
        }
        new = sorted(sites - allowed)
        self.assertEqual(
            new, [], f"조용히 삼키는 자리가 늘었다 — 로그를 남기거나 여기 근거와 함께 적는다: {new}"
        )


class TestCoreConfiguresLogging(unittest.TestCase):
    def setUp(self) -> None:
        self.text = MAIN.read_text(encoding="utf-8")

    def test_logging_is_configured(self) -> None:
        """설정이 없으면 `logger.*` 는 **조용히 버려진다.**"""
        self.assertIn("logging.basicConfig(", self.text, "앱 로거에 핸들러가 안 붙는다")

    def test_configured_before_first_use(self) -> None:
        """`getLogger` 뒤에 설정해도 되지만, 첫 **사용**보다는 앞이어야 한다."""
        cfg = self.text.index("logging.basicConfig(")
        first_use = re.search(r"^\s*logger\.(info|warning|error|exception)\(", self.text, re.M)
        self.assertIsNotNone(first_use, "로그를 남기는 곳이 하나도 없다")
        assert first_use is not None
        self.assertLess(cfg, first_use.start(), "설정보다 먼저 로그를 쓴다")

    def test_level_comes_from_env(self) -> None:
        """운영에서 낮출 수 없으면 소음이 되고, 그러면 다시 끄게 된다."""
        self.assertRegex(self.text, r'CORE_LOG_LEVEL', "레벨을 환경변수로 못 받는다")

    def test_does_not_rip_out_uvicorn_handlers(self) -> None:
        """`force=True` 는 이미 붙은 핸들러를 **걷어낸다** — 접근 로그가 사라진다."""
        block = self.text[self.text.index("logging.basicConfig("):][:400]
        self.assertNotIn("force=True", block)

    def test_exception_paths_still_log(self) -> None:
        """「죽지 않는다」로 삼키는 자리는 **반드시** 로그를 남겨야 한다."""
        for marker in ("gc: pass failed", "worker: claim failed"):
            self.assertIn(marker, self.text, f"예외 보고가 사라졌다: {marker}")
        self.assertGreaterEqual(
            self.text.count("logger.exception("), 2, "예외를 삼키고 조용해졌다"
        )

    def test_probe_actually_reads_the_module(self) -> None:
        self.assertGreater(len(self.text), 10000)
        self.assertGreater(len(re.findall(r"logger\.\w+\(", self.text)), 5)


if __name__ == "__main__":
    unittest.main()
