r"""세 데모가 **같은 주장을 서로 다른 경로로** 보이는가 (큐 #54 · `#200` 옆).

## 왜 있는가

`#200` 은 README 가 「**기기 주소가 없다**」고 부른 **파일이 틀렸던 것**을 고쳤다.
말과 파일을 맞춘 것이다. 이번에는 그 옆자리 — **세 데모가 각자 무엇을 보이기로 했고,
그게 지금도 참인가.**

| 스크립트 | 문서가 말하는 것 | 경로 |
|---|---|---|
| `demo.sh` | 실게이트 → Task 완주 · 증적 두 줄 | Core 직접 (+ 준비 단계에서 Node `/health`) |
| `product_demo.sh` | 「**어디에도 기기 주소가 없다**」 | Core 공개 API 만 |
| `capreq_demo.sh` | 사람이 쓰는 **입구**로 같은 것을 한다 | capreq → Core |

**같은 주장을 세 번 말하는데 경로가 다르다.** 그래서 하나가 조용히 어긋나도
나머지 둘이 초록이면 아무도 모른다. 셋의 **모양**을 각각 못박는다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| `product_demo.sh` 안의 Node 주소 | **0** ✅ |
| `demo.sh` 의 Node 주소 사용 | **2줄** — 기본값(L8) · `/health`(L13) |
| 그 둘이 `POST /v1/tasks`(L70) **앞인가** | **그렇다** ✅ |
| `capreq_demo.sh` 의 Core 직접 `POST /v1/tasks` | **0** ✅ — 입구를 지난다 |

셋 다 참이다. **오늘 결함은 없다** — 나기 전에 막는다.

## 무엇을 안 보나

- 실행 결과. 셋 다 살아 있는 스택이 필요하다 (`capreq_demo` 는 Ollama 까지)
- 무엇을 **출력**하는가. `test_product_demo` · `test_capreq_demo` 가 각자 본다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
README = ROOT / "README.md"

NODE_REF = re.compile(r"\$node\b|NODE_URL|:8001")
POST_TASKS = re.compile(r"-X\s+POST\b[^\n]*\$core[^\n]*?/v1/tasks\b")


def _lines(name: str) -> list[str]:
    return (SCRIPTS / name).read_text(encoding="utf-8").splitlines()


def _hits(name: str, pattern: re.Pattern[str]) -> list[int]:
    """주석이 아닌 줄에서 맞은 **줄 번호**."""
    return [i + 1 for i, line in enumerate(_lines(name))
            if not line.strip().startswith("#") and pattern.search(line)]


class TestProductDemoHasNoDeviceAddress(unittest.TestCase):
    """README 가 그렇게 적는다 — 그 문장이 파일과 맞아야 한다 (`#200` 이 고친 자리)."""

    def test_no_node_address_anywhere(self) -> None:
        hits = _hits("product_demo.sh", NODE_REF)
        self.assertEqual([], hits, f"product_demo.sh 에 기기 주소가 있다: {hits}")

    def test_the_readme_still_makes_that_claim(self) -> None:
        """주장이 사라지면 이 검사는 **아무 말도 안 지키게 된다.**"""
        claim = "`scripts/product_demo.sh` **어디에도 기기 주소가 없다**"
        self.assertTrue(claim in README.read_text(encoding="utf-8"),
                        f"README 에서 그 주장이 사라졌다: {claim}")


class TestDemoTouchesTheNodeOnlyBeforeTheTask(unittest.TestCase):
    """`demo.sh` 는 준비 단계에서만 Node 를 본다 — 작업부터는 Core 하고만 말한다."""

    def test_node_use_is_all_before_the_first_task(self) -> None:
        node = _hits("demo.sh", NODE_REF)
        task = _hits("demo.sh", POST_TASKS)
        self.assertTrue(node, "demo.sh 가 Node 를 안 부른다 — 전제가 바뀌었다")
        self.assertTrue(task, "demo.sh 에서 POST /v1/tasks 를 못 찾았다")
        late = [n for n in node if n > min(task)]
        self.assertEqual([], late, f"작업 생성 뒤에 Node 를 부른다: {late}")

    def test_node_is_only_health(self) -> None:
        """`/health` 밖으로 나가면 「사용자는 기기 주소를 모른다」가 깨진다."""
        bad = []
        for lineno in _hits("demo.sh", NODE_REF):
            line = _lines("demo.sh")[lineno - 1]
            if "NODE_URL" in line or "/health" in line:
                continue
            bad.append(f"L{lineno}: {line.strip()[:70]}")
        self.assertEqual([], bad, f"demo.sh 가 Node 의 다른 경로를 부른다: {bad}")


class TestCapreqDemoGoesThroughTheEntrance(unittest.TestCase):
    """입구를 지나지 않으면 그건 다른 데모 둘과 **같은 경로**가 된다."""

    def test_it_does_not_create_the_task_on_core(self) -> None:
        hits = _hits("capreq_demo.sh", POST_TASKS)
        self.assertEqual([], hits, f"capreq_demo 가 Core 에 직접 작업을 만든다: {hits}")

    def test_it_talks_to_capreq(self) -> None:
        body = (SCRIPTS / "capreq_demo.sh").read_text(encoding="utf-8")
        self.assertIn("capreq", body)
        self.assertRegex(body, r"\$capreq\b", "capreq 주소를 안 쓴다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_all_three_exist(self) -> None:
        for name in ("demo.sh", "product_demo.sh", "capreq_demo.sh"):
            with self.subTest(script=name):
                self.assertTrue((SCRIPTS / name).is_file())

    def test_the_detector_finds_node_use(self) -> None:
        """탐지기가 아무것도 못 잡으면 위 검사가 **공허하게** 통과한다."""
        self.assertGreaterEqual(len(_hits("demo.sh", NODE_REF)), 2)
        self.assertTrue(NODE_REF.search('nh="$(ccurl -sf "$node/health")"'))
        self.assertFalse(NODE_REF.search('ccurl -sf "$core/v1/capabilities"'))

    def test_the_task_detector_discriminates(self) -> None:
        self.assertTrue(POST_TASKS.search('ccurl -sf -X POST "$core/v1/tasks" -d @-'))
        self.assertFalse(POST_TASKS.search('ccurl -sf "$core/v1/tasks/$tid"'))


if __name__ == "__main__":
    unittest.main()
