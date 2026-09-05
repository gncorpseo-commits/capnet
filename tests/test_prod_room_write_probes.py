r"""**쓰기 라우트의 무인증 401** 을 `prod_room` 이 재는가 (큐 #49 · `#205` 옆).

## 왜 있는가

`#223` 은 조회면(`GET`)에서 같은 것을 잡았다 — 인증 GET **열여덟 중 넷**만 눌러 보고
있었다. 고치고 나서 **쓰기 쪽은 그대로 남았다.**

쓰기가 더 위험하다. 조회면이 열리면 정보가 새고, **쓰기가 열리면 남이 내 플릿에
Node·Agent·작업을 만든다.**

## 실측 (2026-09-05)

| 무엇 | 수 |
|---|---|
| 라우트 전체 | **46** |
| 쓰기 (`POST`/`PUT`/`PATCH`/`DELETE`) | **22** |
| 그중 인증을 부르는 것 | **22** — 공개 쓰기는 **0** ✅ |
| `prod_room` 이 **무인증으로** 눌러 보는 것 | **3** |

무인증으로 재는 셋:

```text
POST /v1/nodes          (키 없음) → 401     §5
POST /v1/agents         (키 없음) → 401     §5
POST /v1/nodes/redeem   (토큰 없음) → 401   §8-2
```

나머지 **열아홉**은 강제 모드에서 **한 번도 안 눌러 봤다.** `ast` 검사는
「인증 헬퍼를 불렀는가」만 보므로, 헬퍼를 부르고도 401 이 안 나오는 경우를 못 잡는다 —
`#223` 이 실제로 그 자리에서 **두 건**을 찾았다.

## 왜 이번에 프로브를 안 늘렸나 — **몸통이 필요하고, 재 볼 수 없다**

`#223` 이 남긴 교훈이 여기서 더 크다. FastAPI 는 **핸들러 본문보다 먼저** 파라미터와
**요청 본문**을 검증한다. 그래서 몸통 없이 `POST` 하면 인증에 닿기도 전에 **422** 다 —
이 절이 **인증을 재지 못한다.** 지금 도는 셋이 401 을 받는 것은 전부 **유효한 몸통**을
같이 보내기 때문이다:

```bash
code -X POST "$CORE_URL/v1/nodes" -H 'content-type: application/json' \
  -d '{"name":"intruder","device_type":"SERVER",…}'      # ← 이게 있어야 401 이 나온다
```

열아홉을 늘리려면 **라우트마다 유효한 최소 몸통**을 만들어야 하고, 그게 맞는지는
**돌려 봐야** 안다. 이 세션에는 Docker 데몬이 없다 (`docker info` 실패). 몸통을 잘못
지으면 게이트가 **422 를 인증 실패로 세며 빨개진다** — 재 보지 않은 프로브를 게이트에
얹는 것은 이 저장소가 계속 잡아 온 「됐을 것」이다.

**그래서 표를 만들고 못박는다.** 지금 재는 셋은 줄 수 없고, 공개 쓰기는 0 을 유지하며,
새 쓰기 라우트가 생기면 이 표가 운다.

## 무엇을 고정하나

1. **공개 쓰기 라우트는 0** — 하나라도 생기면 운다
2. `prod_room` 이 **무인증으로 재는 셋**이 줄지 않는다
3. 새 쓰기 라우트는 아래 표에 **등록**된다 (조용히 늘지 않는다)
4. 세는 대상이 비지 않는다
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "scripts" / "prod_room.sh"

sys.path.insert(0, str(ROOT / "tests"))
from test_every_route_declares_its_auth import _authenticated, _routes  # noqa: E402

WRITE_VERBS = ("POST", "PUT", "PATCH", "DELETE")

# 강제 모드에서 **무인증으로 실제로 눌러 보는** 쓰기 라우트. 줄이면 운다.
PROBED_UNAUTHENTICATED = {
    ("POST", "/v1/nodes"),
    ("POST", "/v1/agents"),
    ("POST", "/v1/nodes/redeem"),
}

# 아직 안 눌러 보는 것들. **유효한 최소 몸통이 있어야** 401 이 나오고, 그건 돌려 봐야
# 안다 (머리말 참조). Docker 가 있는 회차에 채운다 — 그때 이 집합이 줄어든다.
NOT_PROBED_YET = 19


def _write_routes() -> list[tuple[str, str]]:
    return sorted({(verb, path) for verb, path, _, called in _routes()
                   if verb in WRITE_VERBS and _authenticated(called)})


def _public_writes() -> list[tuple[str, str]]:
    return sorted({(verb, path) for verb, path, _, called in _routes()
                   if verb in WRITE_VERBS and not _authenticated(called)})


def _unauthenticated_write_probes() -> set[tuple[str, str]]:
    """`prod_room` 이 **Authorization 없이** 부르는 쓰기."""
    body = PROD.read_text(encoding="utf-8")
    found: set[tuple[str, str]] = set()
    # `ccode`/`ccurl` 은 **키를 붙이는** 호출이다 (큐 #72 이후). 이름이 `code`·`curl` 로
    # 끝나 그냥 세면 무인증으로 오인한다 — 앞 글자를 함께 본다.
    call = re.compile(r'(?<![a-z])(?:code|curl)[^\n]*?-X\s+(POST|PUT|PATCH|DELETE)\s+"\$CORE_URL([^"]+)"(.*?)\)\n',
                      re.S)
    for m in call.finditer(body):
        verb, path, rest = m.group(1), m.group(2), m.group(3)
        head = body[:m.start()].rsplit("\n", 1)[-1] + m.group(0)[:40]
        if "Authorization" in rest or "CAPNET_API_KEY" in head:
            continue
        found.add((verb, re.sub(r"\$\{?[a-z_]+\}?", "{id}", path)))
    return found


class TestWritesAreNeverPublic(unittest.TestCase):
    def test_no_write_route_is_public(self) -> None:
        """조회면이 열리면 정보가 새고, **쓰기가 열리면 남이 내 플릿에 만든다.**"""
        self.assertEqual([], _public_writes(),
                         f"인증을 안 부르는 쓰기 라우트: {_public_writes()}")


class TestProdRoomKeepsWhatItMeasures(unittest.TestCase):
    def test_the_three_unauthenticated_probes_are_still_there(self) -> None:
        """지금 재는 셋을 지우면 강제 모드에서 **아무 쓰기도 안 재게 된다.**"""
        probes = _unauthenticated_write_probes()
        self.assertTrue(probes, "prod_room 에서 무인증 쓰기 프로브를 하나도 못 찾았다")
        missing = sorted(PROBED_UNAUTHENTICATED - probes)
        self.assertEqual([], missing, f"무인증 쓰기 프로브가 사라졌다: {missing}")

    def test_the_gap_is_stated_honestly(self) -> None:
        """표의 숫자와 실측이 갈리면 머리말이 거짓이 된다."""
        gap = len(_write_routes()) - len(PROBED_UNAUTHENTICATED & set(_write_routes()))
        self.assertEqual(NOT_PROBED_YET, gap,
                         f"안 눌러 본 쓰기 라우트가 {gap} 이다 — 표와 머리말을 같이 고친다")

    def test_probed_routes_are_real_routes(self) -> None:
        known = set(_write_routes())
        ghosts = sorted(PROBED_UNAUTHENTICATED - known)
        self.assertEqual([], ghosts, f"없는 라우트를 재고 있다고 적었다: {ghosts}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_write_routes_are_seen(self) -> None:
        self.assertGreaterEqual(len(_write_routes()), 20, sorted(_write_routes()))

    def test_the_probe_reader_discriminates(self) -> None:
        """키를 붙인 호출을 무인증으로 세면 「재고 있다」가 거짓이 된다."""
        probes = _unauthenticated_write_probes()
        self.assertIn(("POST", "/v1/nodes"), probes)
        # §8 은 admin 키로 같은 경로를 부른다 — 그건 무인증이 아니다.
        # 큐 #72 이후 그 자리는 `ccode`/`ccurl` 이라 헤더가 argv 에 안 보인다.
        body = PROD.read_text(encoding="utf-8")
        self.assertIn("ccode -X POST", body, "기준 파일이 바뀌었다")
        self.assertNotIn("Authorization: CapNet-Key $key", body,
                         "키가 다시 argv 로 넘어간다 (큐 #72)")
        self.assertNotIn(("POST", "/v1/tasks"), probes)


if __name__ == "__main__":
    unittest.main()
