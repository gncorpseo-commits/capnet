r"""compose 헬스체크가 **항상 성공하는 명령**은 아닌가 (큐 #61 · 옛 `#32`).

## 왜 있는가

헬스체크는 `depends_on: condition: service_healthy` 의 **유일한 근거**다. 그 명령이
언제나 0 을 내면 「기다렸다」가 거짓이 되고, 뒤 서비스는 **준비 안 된 DB 위에서** 뜬다.
`true` · `echo ok` · `ls` 같은 명령이 그렇게 쓰이는 자리다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| `compose.yaml` 의 `healthcheck` | **1** — `postgres` |
| 그 명령 | `pg_isready -U … -d …` — 준비 전에는 **0 이 아니다** ✅ |
| 항상 참인 헬스체크 | **0** ✅ |
| `condition: service_healthy` 를 쓰는 자리 | **2** — 둘 다 `postgres` |
| 헬스체크 없는 서비스를 `service_healthy` 로 기다리는 곳 | **0** ✅ |

**오늘 결함은 없다.**

## 적어 두는 것 — `core` 에는 헬스체크가 없다

Node 셋은 `depends_on: [core]` 를 **조건 없이** 쓴다. 그건 「컨테이너가 떴다」까지만
기다린다는 뜻이고, Core 가 요청을 받기 전일 수 있다. **그래도 괜찮은 이유**는 Node 가
하트비트를 **반복해서** 보내기 때문이다 — 한 번 실패해도 다음 주기에 붙는다.

여기에 헬스체크를 새로 다는 것은 이 큐의 범위가 아니다(`compose.yaml` 구조 변경).
**지금 모양을 못박고**, 누가 `core` 에 `condition: service_healthy` 를 걸면
**헬스체크부터 만들게** 한다 — 없는 서비스에 걸면 compose 가 기동에서 죽는다.

## 이미 문서화된 함정 — initdb 중의 유닉스 소켓

`pg_isready` 는 **initdb 중에도** 유닉스 소켓으로 통과할 수 있다 (그때 TCP 는 닫혀 있다).
그래서 `migrate` 는 `healthy` 만 믿지 않고 `migrate status` 가 실제로 될 때까지 기다린다.
그 주석이 사라지면 다음 사람이 그 대기 루프를 「군더더기」로 지운다 — 같이 못박는다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose.yaml"
PROD = ROOT / "compose.prod.yaml"

# 언제나 0 을 내는 명령. 헬스체크 자리에 오면 기다림이 거짓이 된다.
ALWAYS_TRUE = ("true", ":", "exit 0", "echo", "ls", "/bin/true", "sleep 0")


def _command(test: str) -> str:
    """`["CMD-SHELL", "pg_isready …"]` → `pg_isready …`.

    판정과 아래 탐지기 검사가 **같은 함수**를 쓴다 — 따로 적으면 갈린다
    (실제로 갈렸다: 쉼표가 남아 첫 낱말이 `,` 였다).
    """
    parts = [t.strip().strip('"').strip("'")
             for t in test.strip().strip("[]").split(",")]
    parts = [t for t in parts if t and t.upper() not in ("CMD", "CMD-SHELL", "NONE")]
    return " ".join(parts).strip()


def _services(path: Path) -> dict[str, list[str]]:
    """서비스 → 그 블록의 줄들."""
    out: dict[str, list[str]] = {}
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  ([a-z0-9][a-z0-9._-]*):\s*$", line)
        if m:
            current = m.group(1)
            out[current] = []
            continue
        if current is not None:
            if line and not line.startswith("   ") and not line.startswith("  #"):
                current = None
                continue
            out[current].append(line)
    return out


def _healthchecks(path: Path) -> dict[str, str]:
    """서비스 → `healthcheck.test` 한 줄."""
    got: dict[str, str] = {}
    for name, lines in _services(path).items():
        for i, line in enumerate(lines):
            if line.strip() == "healthcheck:":
                for follow in lines[i + 1:i + 6]:
                    if follow.strip().startswith("test:"):
                        got[name] = follow.split("test:", 1)[1].strip()
                        break
                break
    return got


def _healthy_waits(path: Path) -> list[str]:
    """`condition: service_healthy` 가 가리키는 서비스 이름들."""
    out = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if "condition: service_healthy" in line:
            for back in range(i - 1, max(i - 4, -1), -1):
                m = re.match(r"^\s{6}([a-z0-9][a-z0-9._-]*):\s*$", lines[back])
                if m:
                    out.append(m.group(1))
                    break
    return out


class TestNoHealthcheckAlwaysPasses(unittest.TestCase):
    def test_every_healthcheck_can_fail(self) -> None:
        """**여기가 핵심이다.** 늘 0 이면 「기다렸다」가 거짓이 된다."""
        checks = _healthchecks(COMPOSE)
        self.assertTrue(checks, "헬스체크를 하나도 못 찾았다 — 파서가 죽었다")
        bad = []
        for name, test in checks.items():
            cmd = _command(test)
            first = cmd.split()[0] if cmd.split() else ""
            if not cmd or first in ALWAYS_TRUE or cmd in ALWAYS_TRUE:
                bad.append(f"{name}: {test}")
        self.assertEqual([], bad, f"항상 성공하는 헬스체크: {bad}")

    def test_postgres_uses_pg_isready(self) -> None:
        self.assertIn("pg_isready", _healthchecks(COMPOSE).get("postgres", ""))


class TestWaitingOnHealthNeedsAHealthcheck(unittest.TestCase):
    """헬스체크 없는 서비스를 `service_healthy` 로 기다리면 compose 가 기동에서 죽는다."""

    def test_every_wait_points_at_a_real_healthcheck(self) -> None:
        for path in (COMPOSE, PROD):
            if not path.is_file():
                continue
            checks = set(_healthchecks(COMPOSE)) | set(_healthchecks(path))
            for target in _healthy_waits(path):
                with self.subTest(compose=path.name, service=target):
                    self.assertIn(target, checks,
                                  f"{target} 에 헬스체크가 없는데 service_healthy 로 기다린다")

    def test_the_waits_are_seen(self) -> None:
        self.assertGreaterEqual(len(_healthy_waits(COMPOSE)), 2, _healthy_waits(COMPOSE))


class TestTheInitdbTrapStaysWritten(unittest.TestCase):
    """`pg_isready` 는 initdb 중에도 통과할 수 있다 — 그래서 대기 루프가 있다."""

    def test_the_caveat_comment_is_there(self) -> None:
        note = "initdb 중에도 유닉스 소켓으로 통과할 수 있다"
        self.assertTrue(note in COMPOSE.read_text(encoding="utf-8"),
                        f"compose.yaml 에서 initdb 함정 주석이 사라졌다: «{note}»")

    def test_the_wait_loop_is_still_there(self) -> None:
        self.assertTrue("python -m app.migrate status" in COMPOSE.read_text(encoding="utf-8"),
                        "compose.yaml 에서 migrate 의 대기 루프가 사라졌다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_services_are_read(self) -> None:
        self.assertGreaterEqual(len(_services(COMPOSE)), 6, sorted(_services(COMPOSE)))

    def test_detector_would_catch_a_fake_healthcheck(self) -> None:
        """탐지기가 `true` 를 못 잡으면 위 검사는 아무것도 안 지킨다."""
        for fake in ('["CMD", "true"]', '["CMD-SHELL", "exit 0"]', '["CMD", "echo", "ok"]'):
            cmd = _command(fake)
            first = cmd.split()[0] if cmd.split() else ""
            with self.subTest(test=fake):
                self.assertTrue(first in ALWAYS_TRUE or cmd in ALWAYS_TRUE, cmd)
        # 진짜 헬스체크는 안 걸려야 한다 — 아니면 이 검사가 늘 빨갛다.
        real = _command('["CMD-SHELL", "pg_isready -U capnet -d capnet"]')
        self.assertNotIn(real.split()[0], ALWAYS_TRUE)


if __name__ == "__main__":
    unittest.main()
