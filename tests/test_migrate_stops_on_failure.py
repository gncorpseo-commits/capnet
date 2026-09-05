r"""마이그레이션이 **실패하면 멈추는가** (큐 #57).

## 왜 있는가

세대 하나가 실패했는데 다음 세대로 넘어가면, DB 는 **어느 상태도 아니게** 된다.
`0012` 가 만든 컬럼을 `0013` 이 쓰는데 `0012` 가 없으면, 오류는 `0013` 에서 나고
사람은 엉뚱한 파일을 본다. 「반쯤 올라간 스키마」는 이 저장소가 가장 비싸게 치를 상태다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| `cmd_up` 의 실패 처리 | `rollback()` → 메시지 → **`return 1`** ✅ 다음 파일로 안 간다 |
| 실패 메시지가 말하는 것 | 「이 파일은 롤백됐다. **앞 파일들은 적용된 채로 남는다.**」 ✅ |
| `core` 가 `migrate` 를 기다리는 조건 | `service_completed_successfully` ✅ |
| `migrate` 의 재시작 정책 | `restart: "no"` ✅ (한 번만 돈다) |
| `scripts/migrate.sh` | `set -euo pipefail` · 종료 코드를 그대로 넘긴다 ✅ |

**넘어가는 분기는 없다.**

## 고친 것 하나 — 대기가 **조용히** 만료됐다

compose 의 `migrate` 는 baseline 이 보일 때까지 60초 기다린 뒤 `up` 을 돈다.
그 루프가 **성공했는지 만료됐는지 아무 말도 안 했다.**

```sh
for i in $(seq 1 60); do
  python -m app.migrate status >/dev/null 2>&1 && break     # ← 만료도 여기로 나온다
done
exec python -m app.migrate up
```

흐름을 바꾸지 않았다 — `up` 은 그대로 돈다(거기서 나는 오류가 더 구체적이다). 다만
**「60초를 기다렸다」가 로그에 남는다.** 그게 없으면 「왜 baseline 이 없지」를 처음부터
다시 찾게 된다.

## 무엇을 안 보나

**실제 실패를 재현하지 않는다** — 깨진 마이그레이션을 실제로 적용해 보는 것은 DB 가
필요하고, CI `migrate` 잡의 「체크섬 잠금」 단계가 그 계열을 본다.
"""

from __future__ import annotations

import ast
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402
MIGRATE = ROOT / "apps" / "core" / "app" / "migrate.py"
WRAPPER = ROOT / "scripts" / "migrate.sh"
COMPOSE = ROOT / "compose.yaml"


def _cmd_up() -> ast.FunctionDef:
    for node in ast.walk(ast.parse(MIGRATE.read_text(encoding="utf-8"))):
        if isinstance(node, ast.FunctionDef) and node.name == "cmd_up":
            return node
    raise AssertionError("cmd_up 을 못 찾았다")


class TestFailureStopsTheLoop(unittest.TestCase):
    def test_the_handler_returns_instead_of_continuing(self) -> None:
        """**여기가 핵심이다.** `continue` 면 반쯤 올라간 스키마가 된다."""
        handlers = [n for n in ast.walk(_cmd_up()) if isinstance(n, ast.ExceptHandler)]
        self.assertTrue(handlers, "cmd_up 에 예외 처리가 없다")
        bad = []
        for handler in handlers:
            has_return = any(isinstance(s, ast.Return) for s in ast.walk(handler))
            has_continue = any(isinstance(s, ast.Continue) for s in ast.walk(handler))
            if has_continue or not has_return:
                bad.append(f"L{handler.lineno}")
        self.assertEqual([], bad, f"실패하고도 다음 세대로 넘어간다: {bad}")

    def test_it_rolls_back_the_failing_file(self) -> None:
        src = ast.unparse(_cmd_up())
        self.assertIn("conn.rollback()", src, "실패한 파일을 롤백하지 않는다")

    def test_the_message_says_what_survived(self) -> None:
        """「앞 파일들은 적용된 채로 남는다」를 안 적으면 사람이 전체 롤백으로 읽는다."""
        note = "앞 파일들은 적용된 채로 남는다"
        self.assertTrue(note in MIGRATE.read_text(encoding="utf-8"),
                        f"실패 메시지에서 사실이 사라졌다: «{note}»")


class TestNothingRunsOnAHalfMigratedDb(unittest.TestCase):
    def test_core_waits_for_success_not_completion(self) -> None:
        # **주석을 걷고 본다.** 걷지 않으면 설정을 주석으로 옮겨도 통과한다 (G1).
        body = hash_comment_free(COMPOSE)
        self.assertIn("condition: service_completed_successfully", body,
                      "core 가 migrate 의 **성공**을 기다리지 않는다")

    def test_migrate_does_not_restart(self) -> None:
        """재시작하면 실패한 세대를 무한히 다시 민다.

        `# restart: "no"` 로 주석 처리해도 통과하던 자리다 (G1) — 주석을 걷고 본다.
        """
        self.assertIn('restart: "no"', hash_comment_free(COMPOSE))

    def test_the_wrapper_propagates_the_exit_code(self) -> None:
        body = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", body)
        # `shift || true` 는 인자가 없을 때라 정상이다 (`#239` 의 ALLOWED_SWALLOW).
        # 삼키면 안 되는 것은 **러너를 부르는 줄**이다.
        runner = [l for l in body.splitlines() if "app.migrate" in l]
        self.assertTrue(runner, "러너를 부르는 줄을 못 찾았다")
        for line in runner:
            self.assertNotIn("|| true", line, f"래퍼가 실패를 삼킨다: {line.strip()}")


class TestTheWaitDoesNotExpireSilently(unittest.TestCase):
    """만료를 안 말하면 「왜 baseline 이 없지」를 처음부터 다시 찾는다 (큐 #57)."""

    def test_the_loop_reports_expiry(self) -> None:
        body = hash_comment_free(COMPOSE)
        self.assertIn("baseline 을 60초 안에 못 봤다", body,
                      "대기 루프가 만료를 조용히 넘긴다")
        self.assertIn("ok=1", body, "성공 여부를 기록하지 않는다")

    def test_it_still_runs_up_afterwards(self) -> None:
        """만료했다고 안 돌리면 **거기서 나는 더 구체적인 오류**를 못 본다."""
        body = hash_comment_free(COMPOSE)
        self.assertLess(body.index("baseline 을 60초 안에 못 봤다"),
                        body.index("exec python -m app.migrate up"))


class TestProbeActuallyScans(unittest.TestCase):
    def test_cmd_up_is_found_and_loops(self) -> None:
        fn = _cmd_up()
        loops = [n for n in ast.walk(fn) if isinstance(n, ast.For)]
        self.assertTrue(loops, "cmd_up 에 적용 루프가 없다")

    def test_the_detector_would_catch_a_continue(self) -> None:
        fn = ast.parse("def f():\n    for x in y:\n        try:\n            g()\n"
                       "        except Exception:\n            continue\n").body[0]
        handlers = [n for n in ast.walk(fn) if isinstance(n, ast.ExceptHandler)]
        self.assertTrue(any(isinstance(s, ast.Continue) for s in ast.walk(handlers[0])))


if __name__ == "__main__":
    unittest.main()
