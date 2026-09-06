r"""`CORE_URL` 이 가리키는 스택과 `docker compose` 가 고를 프로젝트가 **엇갈리면 멈추는가** (배치 R · R3).

## 왜 있는가

운영 스크립트는 축이 둘이다.

| 무엇 | 어디서 오나 |
|---|---|
| Core 주소 | `CORE_URL` |
| 가중치 해시 · `psql` | `docker compose exec` — **프로젝트 이름**(디렉터리 또는 `COMPOSE_PROJECT_NAME`) |

**둘은 서로를 모른다.** R3 실측(2026-09-06):

```
CORE_URL=http://127.0.0.1:18800 bash scripts/product_demo.sh   # 격리 방(clean_room)을 가리켰다
...
== 4) Agent 등록 ==
service "node-m-team" is not running                            # 운영 프로젝트를 봤다
```

그때는 운영 스택이 꺼져 있어 「없다」로 끝났다. **켜져 있었으면 조용히 성공했을 것이다** —
격리 방에 등록할 Agent 의 가중치 해시를 다른 스택에서 읽어서. 배치 R 이 「운영 스택을
건드리지 마」라고 적어 둔 바로 그 사고이고, 조용하기 때문에 더 나쁘다.

## 무엇을 고정하나

1. 루프백 `CORE_URL` 의 포트를 **다른 프로젝트의 core** 가 물고 있으면 **exit 1**
2. 짝이 맞으면 그대로 진행한다
3. **스택이 안 떠 있으면 판단하지 않는다** — 종전의 「service … is not running」이 그대로 나야 한다
4. **원격 Core 는 보지 않는다** — 거기엔 compose 가 없다
5. 탈출구(`CAPNET_SKIP_COMPOSE_GUARD`)가 있다
6. 가드가 **정의만 되고 불리지 않는** 상태가 아니다

## 어떻게 보나

`docker` 를 **가짜로 세워** 본다. 진짜 데몬을 요구하지 않으므로 CI 에서도 돈다.
`docker compose port` 가 설정이 아니라 **런타임**을 답한다는 것은 실측으로 확인했다
(`CORE_PORT=18999` 를 줘도 실제로 뜬 `8000` 을 답한다) — 그래서 이 축이 판정 근거가 된다.

## 재현

```bash
python3 -m unittest tests.test_compose_project_follows_core_url
```
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

HTTP_SH = ROOT / "scripts" / "lib" / "http.sh"

SHIM = """#!/usr/bin/env bash
# `docker compose … port core 8000` 만 흉내낸다. 그 밖에는 아무것도 하지 않는다.
if [ "${1:-}" = "compose" ]; then
  for a in "$@"; do [ "$a" = "port" ] && { printf '%s\\n' "$FAKE_PUBLISHED"; exit 0; }; done
fi
exit 0
"""


def _source_http_sh(core_url: str | None, published: str, **env: str):
    """가짜 docker 를 PATH 앞에 두고 http.sh 를 source 한다."""
    with tempfile.TemporaryDirectory() as d:
        shim = Path(d) / "docker"
        shim.write_text(SHIM, encoding="utf-8")
        shim.chmod(0o755)
        e = dict(os.environ)
        e.pop("CORE_URL", None)
        e.pop("CAPNET_SKIP_COMPOSE_GUARD", None)
        if core_url is not None:
            e["CORE_URL"] = core_url
        e["FAKE_PUBLISHED"] = published
        e["PATH"] = f"{d}:{e['PATH']}"
        e.update(env)
        return subprocess.run(
            ["bash", "-c", f'source "{HTTP_SH}"; echo REACHED'],
            cwd=ROOT, env=e, capture_output=True, text=True, timeout=120,
        )


class TestMismatchStops(unittest.TestCase):
    def test_other_project_holds_the_port(self) -> None:
        r = _source_http_sh("http://127.0.0.1:18800", "0.0.0.0:8000")
        self.assertNotEqual(r.returncode, 0, "엇갈린 스택인데 그대로 갔다:\n" + r.stdout + r.stderr)
        self.assertNotIn("REACHED", r.stdout)
        self.assertIn("COMPOSE_PROJECT_NAME", r.stderr, "고치는 법을 안 알려준다:\n" + r.stderr)


class TestTheseMustNotStop(unittest.TestCase):
    def test_matching_pair_goes_through(self) -> None:
        r = _source_http_sh("http://127.0.0.1:8000", "0.0.0.0:8000")
        self.assertIn("REACHED", r.stdout, r.stderr)

    def test_stack_not_running_is_not_a_verdict(self) -> None:
        r = _source_http_sh("http://127.0.0.1:18800", "")
        self.assertIn("REACHED", r.stdout, "안 떠 있는 스택을 엇갈림으로 읽었다:\n" + r.stderr)

    def test_remote_core_is_not_judged(self) -> None:
        r = _source_http_sh("http://10.1.2.3:18800", "0.0.0.0:8000")
        self.assertIn("REACHED", r.stdout, "원격 Core 를 compose 로 판정했다:\n" + r.stderr)

    def test_no_core_url_is_not_judged(self) -> None:
        r = _source_http_sh(None, "0.0.0.0:8000")
        self.assertIn("REACHED", r.stdout, r.stderr)

    def test_the_escape_hatch_works(self) -> None:
        r = _source_http_sh("http://127.0.0.1:18800", "0.0.0.0:8000", CAPNET_SKIP_COMPOSE_GUARD="1")
        self.assertIn("REACHED", r.stdout, r.stderr)


class TestTheGuardIsActuallyCalled(unittest.TestCase):
    """정의만 하고 안 부르면 아무것도 막지 못한다. 주석을 걷고 본다."""

    def test_defined_and_invoked(self) -> None:
        body = hash_comment_free(HTTP_SH)
        calls = [
            ln for ln in body.splitlines()
            if ln.strip() == "_capnet_assert_compose_matches_core"
        ]
        self.assertTrue(calls, "가드가 정의만 되고 불리지 않는다 (주석 제외)")


if __name__ == "__main__":
    unittest.main()
