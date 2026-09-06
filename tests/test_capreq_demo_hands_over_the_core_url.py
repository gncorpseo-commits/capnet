r"""`capreq_demo.sh` 가 **자기가 띄운 capreq 에 Core 주소를 넘기는가** (배치 R · R4).

## 왜 있는가

R4 실측(2026-09-06)에서 잡혔다. 스크립트 머리말은 `CORE_URL` 을 환경으로 광고하는데,
정작 capreq 를 띄울 때 그 값을 넘기지 않았다. capreq 는 `CAPREQ_CORE_URL` 만 읽으므로
(`capreq/src/capreq/config.py`) 우리가 띄운 capreq 는 **기본 `:8000`** 을 봤다.

    CORE_URL=http://127.0.0.1:18800 bash scripts/capreq_demo.sh
    ...
    == 1) capreq 가 Core 의 살아 있는 카탈로그를 읽는가 ==
    카탈로그를 못 읽는다 — capreq→Core 배선이 끊겼다      ← exit 1

**배선은 멀쩡했다.** 격리 방(clean_room · 18800)을 가리켰는데 capreq 가 다른 Core 를
본 것이고, 스크립트는 그것을 「배선이 끊겼다」(고칠 버그)로 보고했다. 종료 코드 규약이
1(배선) / 2(라우팅)로 나뉘어 있는데 **환경 전달 누락이 1 로 새어 나온 것**이라 더 나쁘다.
`CAPREQ_CORE_URL` 을 손으로 같이 준 뒤 같은 명령이 exit 0 으로 완주했다.

## 무엇을 고정하나

1. capreq 를 띄우는 그 명령줄이 `CAPREQ_CORE_URL` 을 넘긴다 — 값은 이 스크립트의 `$core`
2. 강제 모드의 관리 키도 같이 넘어간다 (`CAPREQ_API_KEY`)
3. **이름이 실물과 같다** — capreq 가 읽는 환경변수 이름을 `config.py` 에서 확인한다.
   한쪽만 바뀌면 조용히 다시 끊기므로 여기서 운다

## 무엇을 안 보나

capreq 를 **띄워 보지 않는다**. Ollama·살아 있는 스택이 필요한 종단은 `capreq_demo.sh`
자신의 몫이다. 여기는 「주소가 건네지는가」만 본다.

## 재현

```bash
python3 -m unittest tests.test_capreq_demo_hands_over_the_core_url
```
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import code_only, hash_comment_free  # noqa: E402

DEMO = ROOT / "scripts" / "capreq_demo.sh"
CONFIG = ROOT / "capreq" / "src" / "capreq" / "config.py"


def _serve_command(body: str) -> str:
    """capreq 를 띄우는 그 한 덩어리 (여러 줄에 걸쳐 있다)."""
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if "python3 -m capreq serve" in line:
            start = i
            while start > 0 and lines[start - 1].rstrip().endswith("\\"):
                start -= 1
            return "\n".join(lines[start : i + 1])
    raise AssertionError("capreq 를 띄우는 줄을 못 찾았다 — 스크립트가 바뀌었다")


class TestTheCoreUrlIsHandedOver(unittest.TestCase):
    def setUp(self) -> None:
        self.body = hash_comment_free(DEMO)
        self.serve = _serve_command(self.body)

    def test_core_url_reaches_the_capreq_process(self) -> None:
        self.assertIn(
            "CAPREQ_CORE_URL=",
            self.serve,
            "capreq 를 띄우면서 Core 주소를 안 넘긴다 — 기본 :8000 을 보게 된다:\n" + self.serve,
        )

    def test_the_handed_over_value_comes_from_this_script(self) -> None:
        m = re.search(r'CAPREQ_CORE_URL="\$\{CAPREQ_CORE_URL:-([^"}]+)\}"', self.serve)
        self.assertIsNotNone(m, "CAPREQ_CORE_URL 이 이 스크립트의 주소에서 오지 않는다:\n" + self.serve)
        assert m is not None
        self.assertIn(
            "core",
            m.group(1),
            f"넘기는 값이 `$core`(=CORE_URL) 가 아니다: {m.group(1)}",
        )

    def test_the_admin_key_is_handed_over_too(self) -> None:
        self.assertIn(
            "CAPREQ_API_KEY=",
            self.serve,
            "강제 모드에서 capreq 가 무인증으로 나간다 — 관리 키를 안 넘긴다:\n" + self.serve,
        )


class TestTheNamesAgreeWithCapreq(unittest.TestCase):
    """스크립트가 넘기는 이름 = capreq 가 읽는 이름. 한쪽만 바뀌면 조용히 끊긴다."""

    def test_capreq_reads_exactly_these_names(self) -> None:
        cfg = code_only(CONFIG)
        for name in ("CAPREQ_CORE_URL", "CAPREQ_API_KEY"):
            self.assertIn(
                f'"{name}"',
                cfg,
                f"{name} 을 capreq 가 안 읽는다 — 스크립트가 넘기는 이름이 낡았다",
            )


if __name__ == "__main__":
    unittest.main()
