"""스크립트가 **기기·Core 주소를 환경에서 받는가** (격리 방이 성립하는 조건).

## 왜 있는가

`clean_room.sh` 는 별도 compose 프로젝트와 **다른 포트**(18800/18801)로 스택을 띄운 뒤
`demo.sh`·`sanity.sh` 를 **그대로** 돌린다. `prod_room.sh` 도 같다(18830/18831).
그게 되는 이유는 하나다 — **스크립트가 `CORE_URL`·`NODE_URL` 을 환경에서 받기 때문이다.**

주소를 박아 두면 **격리 방을 띄워 놓고도 운영 스택을 친다.** 조용히, 초록으로.

실측 (2026-09-03):

| | 수 |
|---|---|
| 주소를 쓰는 스크립트 | **23** |
| 환경에서 받는다 | **21** |
| **박아 뒀다** | **2** — `demo.ps1` · `smoke_w1.ps1` |

`.sh` 는 **20/20 전부** 받는다. `.ps1` 셋 중에서는 `proof_ab.ps1` 만 따라갔다.
`CHANGELOG` 는 `demo.sh`·`proof_ab.sh`·`pass_rate.sh` 를 파라미터화한 것을 적어 뒀는데,
**같은 이름의 `.ps1` 짝은 그때 안 따라갔고 아무도 못 봤다.**

`README` 는 「**Windows** — 동명 `.ps1`」이라고 적는다. 동명인데 **동작이 다르다.**

## 무엇을 고정하나

주소(`127.0.0.1:800x` · `localhost:800x`)를 **쓰는** 스크립트는 그 주소를
`CORE_URL`/`NODE_URL`(`.ps1` 은 `$env:`)로 **덮을 수 있어야 한다.**

주소를 안 쓰는 스크립트(`sanity.ps1` 은 `docker exec` 만 한다)는 대상이 아니다 —
**쓰는 것만** 본다.

## 무엇을 고정하지 **않나**

기본값의 포트 번호. `8000`/`8001` 은 compose 가 정하고 여기서 다시 못박으면
포트를 옮길 때 검사가 일을 시킨다.

## 못 쟀다

**`.ps1` 을 실제로 돌리지 못했다** — 이 환경에 `pwsh` 가 없다.
고친 두 줄은 같은 저장소의 `proof_ab.ps1` 이 이미 쓰는 **문법 그대로**다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# 하드코딩된 로컬 주소.
ADDR = re.compile(r"(?:127\.0\.0\.1|localhost):(?:800[0-9]|8090)")
# 덮어쓰기 통로.
SH_ENV = re.compile(r"\$\{(?:CORE_URL|NODE_URL|CAPREQ_URL)(?::-)?")
PS_ENV = re.compile(r"\$env:(?:CORE_URL|NODE_URL|CAPREQ_URL)")


def _scripts() -> list[Path]:
    return sorted(p for p in SCRIPTS.glob("*") if p.suffix in (".sh", ".ps1"))


def _uses_address(text: str) -> bool:
    return bool(ADDR.search(text))


def _takes_env(path: Path, text: str) -> bool:
    return bool((PS_ENV if path.suffix == ".ps1" else SH_ENV).search(text))


class TestAddressesAreOverridable(unittest.TestCase):
    def test_every_script_with_an_address_takes_it_from_env(self) -> None:
        """**여기가 핵심이다.** 박아 두면 격리 방이 운영 스택을 친다."""
        bad: list[str] = []
        for p in _scripts():
            text = p.read_text(encoding="utf-8", errors="replace")
            if _uses_address(text) and not _takes_env(p, text):
                bad.append(p.name)
        self.assertEqual(
            [], sorted(bad),
            "주소를 박아 둔 스크립트 — CORE_URL/NODE_URL 로 덮을 수 있게 한다 "
            f"(선례: scripts/proof_ab.ps1): {sorted(bad)}",
        )

    def test_powershell_twins_match_their_shell_twins(self) -> None:
        """`README` 가 「동명 `.ps1`」이라고 적는다. 동명이면 **덮는 방식도 같아야** 한다."""
        for name in ("demo", "proof_ab"):
            sh, ps = SCRIPTS / f"{name}.sh", SCRIPTS / f"{name}.ps1"
            if not (sh.is_file() and ps.is_file()):
                continue
            with self.subTest(pair=name):
                sh_t = sh.read_text(encoding="utf-8", errors="replace")
                ps_t = ps.read_text(encoding="utf-8", errors="replace")
                if _uses_address(sh_t) and _takes_env(sh, sh_t):
                    self.assertTrue(
                        _takes_env(ps, ps_t),
                        f"{sh.name} 은 환경에서 받는데 {ps.name} 은 주소를 박아 뒀다",
                    )


class TestIsolatedRoomsRelyOnIt(unittest.TestCase):
    """이 검사가 지키는 것이 **실제로 쓰이고 있는지** 확인한다.

    격리 방이 환경 변수로 주소를 넘기지 않게 되면 위 검사는 아무것도 안 지킨다.
    """

    def test_rooms_export_the_urls(self) -> None:
        for rel in ("scripts/clean_room.sh", "scripts/prod_room.sh"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(room=rel):
                self.assertRegex(text, r"export CORE_URL=", f"{rel} 이 CORE_URL 을 안 내보낸다")
                self.assertRegex(text, r"export NODE_URL=", f"{rel} 이 NODE_URL 을 안 내보낸다")

    def test_rooms_use_non_default_ports(self) -> None:
        """같은 포트를 쓰면 격리가 아니다 — 덮을 수 있어도 의미가 없다."""
        for rel in ("scripts/clean_room.sh", "scripts/prod_room.sh"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(room=rel):
                self.assertRegex(
                    text, r"(?:core_port|node_port)\s*=\s*\"?\$?\{?[A-Z_]*:?-?18\d{3}",
                    f"{rel} 이 격리 포트(18xxx)를 안 쓴다",
                )


class TestProbeActuallyFindsThings(unittest.TestCase):
    def test_found_enough_scripts(self) -> None:
        with_addr = [
            p.name for p in _scripts()
            if _uses_address(p.read_text(encoding="utf-8", errors="replace"))
        ]
        self.assertGreater(
            len(with_addr), 15,
            f"주소를 쓰는 스크립트를 {len(with_addr)}개밖에 못 찾았다 — 정규식이 눈멀었다",
        )

    def test_env_pattern_actually_matches_something(self) -> None:
        """`_takes_env` 가 **아무것도 못 잡으면** 위 검사가 전부 실패해야 정상이다.

        반대로 패턴이 너무 헐거워 **전부 잡아도** 검사가 헛돈다. 알려진 두 모양을 못박는다.
        """
        self.assertTrue(_takes_env(Path("x.sh"), 'core="${CORE_URL:-http://127.0.0.1:8000}"'))
        self.assertTrue(_takes_env(Path("x.ps1"), '$core = if ($env:CORE_URL) { $env:CORE_URL }'))
        self.assertFalse(_takes_env(Path("x.ps1"), '$core = "http://127.0.0.1:8000"'))
        self.assertFalse(_takes_env(Path("x.sh"), 'core="http://127.0.0.1:8000"'))


if __name__ == "__main__":
    unittest.main()
