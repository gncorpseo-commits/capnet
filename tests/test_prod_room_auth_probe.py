"""`prod_room.sh` 가 **강제 모드에서 라우트를 빠짐없이 눌러 보는가.**

## 왜 있는가

`test_every_route_declares_its_auth` 는 `ast` 로 **「인증 헬퍼를 불렀는가」** 만 본다.
그것으로 충분하지 않다 — 헬퍼를 부르고도 강제 모드에서 401 이 안 나올 수 있고,
반대로 **공개여야 하는 자리가 잠기면** 제품 입구(capreq)가 통째로 죽는다.

**실제 응답 코드를 재는 것은 `prod_room.sh` 뿐이다.** 그런데 실측해 보니 손으로 고른
몇 개만 누르고 있었다 (2026-09-03):

| | 코드에 있는 것 | `prod_room` 이 누르던 것 |
|---|---|---|
| 공개 GET | **6** | **1** (`/health`) |
| 인증 GET | **18** | **4** |

공개 GET 다섯은 **강제 모드에서 한 번도 안 눌러 봤다.** `PUBLIC` 주석은
「제품 입구가 **키 없이** 읽어 라우팅한다」고 적는데, 그 전제가 제품 프로파일에서
참인지 아무도 재지 않았다.

## `000` — 공개 프로브가 조용히 초록이 되는 자리

`prod_room.sh` 의 `code()` 는 `curl` 이 실패하면 **`000`** 을 낸다.
인증 프로브는 `= 401` 이라 `000` 이 실패로 떨어진다. 그런데 공개 프로브는
「401 이 아니면 통과」다 — 그대로 쓰면 **Core 가 안 떠 있을 때 「공개 GET 정상」** 이 된다.

이 회차들이 고쳐 온 것과 같은 모양이라(0건·0행·공허 `any`), 판정을
`scripts/lib/authprobe.sh` 로 빼고 **여기서 실제로 부른다** (`lib/tally.sh` 와 같은 이유 —
`prod_room.sh` 는 Docker 가 있어야 돌지만 함수는 그냥 돈다).

## 무엇을 고정하나

1. `probe_verdict` 의 **판정표** — `000`·빈 값·비숫자는 **실패**
2. `prod_room.sh` 가 **공개 GET 전부**를 누른다 (라우트가 늘면 스크립트도 고치게 된다)
3. `prod_room.sh` 가 **인증 GET 전부**를 무인증으로 누른다
4. 판정이 **인라인으로 되돌아가지 않았다**

## 무엇을 고정하지 **않나**

`chk` 개수. 자라는 값이라 못박으면 사람이 숫자만 고친다 (`test_doc_counts` 규율).
그리고 **실행 결과는 안 본다** — Docker 없이는 못 돈다. 여기서 보는 것은
「무엇을 누르기로 적었는가」와 「그 판정이 옳은가」 둘이다.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "scripts" / "prod_room.sh"
LIB = ROOT / "scripts" / "lib" / "authprobe.sh"

sys.path.insert(0, str(ROOT / "tests"))
from test_every_route_declares_its_auth import (  # noqa: E402
    PUBLIC, _authenticated, _routes,
)

# 경로 파라미터를 한 모양으로 만든다 — `{agent_id}` 도 `$dummy` 도 「파라미터」다.
_BRACE = re.compile(r"\{[^}]+\}")
_SHVAR = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?")


def _norm(path: str) -> str:
    return _SHVAR.sub("<p>", _BRACE.sub("<p>", path))


def _probed(section: str) -> set[str]:
    """`prod_room.sh` 의 한 절이 `for path in … ; do` 로 나열한 경로들."""
    text = PROD.read_text(encoding="utf-8")
    m = re.search(rf"== {section}\).*?for path in(.*?)\bdo\b", text, re.S)
    if not m:
        return set()
    return {_norm(q) for q in re.findall(r'"([^"]+)"', m.group(1))}


def _bash(kind: str, code: str) -> int:
    """`probe_verdict` 를 **실제로 부른다.**"""
    return subprocess.run(
        ["bash", "-c", f'source "{LIB}"; probe_verdict {kind!r} {code!r}'],
        capture_output=True, text=True,
    ).returncode


class TestVerdictTable(unittest.TestCase):
    """판정 한 줄을 **직접 부른다.**"""

    def test_public_passes_when_open(self) -> None:
        for code in ("200", "204", "404", "500"):
            with self.subTest(code=code):
                self.assertEqual(0, _bash("public", code))

    def test_public_fails_when_locked(self) -> None:
        for code in ("401", "403"):
            with self.subTest(code=code):
                self.assertEqual(1, _bash("public", code), f"공개인데 {code} 를 통과시켰다")

    def test_authed_passes_only_on_401(self) -> None:
        self.assertEqual(0, _bash("authed", "401"))
        for code in ("200", "403", "404"):
            with self.subTest(code=code):
                self.assertEqual(1, _bash("authed", code), f"인증 자리인데 {code} 를 통과시켰다")

    def test_no_response_is_never_a_pass(self) -> None:
        """**여기가 핵심이다.** `000` 은 「열려 있다」가 아니라 「못 물어봤다」다."""
        for kind in ("public", "authed"):
            for code in ("000", "", "abc", "40", "4011"):
                with self.subTest(kind=kind, code=code):
                    self.assertEqual(
                        1, _bash(kind, code),
                        f"{kind} 가 응답 아닌 값 {code!r} 을 통과시켰다",
                    )

    def test_unknown_kind_fails(self) -> None:
        """오타 난 종류가 조용히 통과하면 그 프로브는 아무것도 안 본 것이다."""
        self.assertEqual(1, _bash("publik", "200"))


class TestProdRoomCoversEveryRoute(unittest.TestCase):
    def setUp(self) -> None:
        self.routes = _routes()

    def test_covers_every_public_get(self) -> None:
        want = {_norm(p) for v, p, _n, _c in self.routes if v == "GET" and (v, p) in PUBLIC}
        missing = sorted(want - _probed("13"))
        self.assertEqual(
            [], missing,
            "공개 GET 인데 prod_room §13 이 안 누른다 — 강제 모드에서 잠겨도 아무도 모른다: "
            f"{missing}",
        )

    def test_covers_every_authenticated_get(self) -> None:
        want = {_norm(p) for v, p, _n, c in self.routes if v == "GET" and _authenticated(c)}
        missing = sorted(want - _probed("14"))
        self.assertEqual(
            [], missing,
            "인증 GET 인데 prod_room §14 가 무인증으로 안 눌러 본다: " f"{missing}",
        )

    def test_probe_lists_are_not_empty(self) -> None:
        """절을 통째로 지우면 위 둘이 **빈 집합끼리 비교**하며 통과한다."""
        self.assertGreaterEqual(len(_probed("13")), 5, "§13 목록이 비었거나 너무 짧다")
        self.assertGreaterEqual(len(_probed("14")), 10, "§14 목록이 비었거나 너무 짧다")

    def test_does_not_probe_ghosts(self) -> None:
        """지운 라우트를 계속 누르면 다음 사람이 「이건 있는 거였지」로 넘어간다."""
        real = {_norm(p) for _v, p, _n, _c in self.routes}
        ghosts = sorted((_probed("13") | _probed("14")) - real)
        self.assertEqual([], ghosts, f"라우트가 없는 경로를 누른다: {ghosts}")


class TestVerdictIsShared(unittest.TestCase):
    def test_prod_room_sources_the_lib(self) -> None:
        """인라인으로 되돌아가면 이 검사가 판정을 못 본다."""
        text = PROD.read_text(encoding="utf-8")
        self.assertIn("lib/authprobe.sh", text, "prod_room 이 판정 lib 를 안 쓴다")
        self.assertIn("probe_verdict", text, "prod_room 이 probe_verdict 를 안 부른다")

    def test_lib_is_syntactically_valid(self) -> None:
        r = subprocess.run(["bash", "-n", str(LIB)], capture_output=True, text=True)
        self.assertEqual(0, r.returncode, r.stderr)

    def test_prod_room_is_syntactically_valid(self) -> None:
        r = subprocess.run(["bash", "-n", str(PROD)], capture_output=True, text=True)
        self.assertEqual(0, r.returncode, r.stderr)


if __name__ == "__main__":
    unittest.main()
