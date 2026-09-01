"""`scripts/capreq_demo.sh` 가 **제품 입구 경로를 빠짐없이 밟는가**.

## 왜 있는가

다른 `*_demo.sh` 는 전부 **Core 를 직접** 부른다. 사람이 쓰는 입구는 `capreq` 인데
그 경로에는 종단 검사가 없었다.

없어서 무슨 일이 났나 — **첨부가 한 번도 동작하지 않았다** (`7936a0f`). 단위 검사도
`chat_flow_probe.js` 도 통과하고 있었다. `fetch` 를 스텁으로 막기 때문이다.
손으로 종단을 재고서야 잡혔고, **그 실측은 어디에도 남지 않았다.**

스크립트가 그 실측을 대신한다. 이 검사는 **스크립트가 검사를 빠뜨리지 않는지**를 본다.
실행 자체는 Ollama·살아 있는 스택이 필요해 CI 밖이다 (`route_bench` 와 같은 부류).

## 무엇을 고정하나

1. `input_id` 를 **본다** — 첨부가 Core 를 거쳤다는 유일한 증거다 (D8′)
2. 증적(assignment)과 **경계**(신뢰도메인·티어)를 낸다
3. 카탈로그를 **Core 와 대조**한다 — 정적 사본을 읽고 있으면 배선이 끊긴 것이다
4. **라우팅 정확도를 주장하지 않는다** — 빗나감은 종료 코드 2 로 따로 센다
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "scripts" / "capreq_demo.sh"


class TestScriptShape(unittest.TestCase):
    def setUp(self) -> None:
        self.text = DEMO.read_text(encoding="utf-8")

    def test_present_and_executable(self) -> None:
        self.assertTrue(DEMO.is_file(), "scripts/capreq_demo.sh 이 없다")
        self.assertTrue(os.access(DEMO, os.X_OK), "실행 권한이 없다")

    def test_fails_loudly(self) -> None:
        """`set -euo pipefail` 없이는 중간 실패가 exit 0 으로 묻힌다."""
        self.assertIn("set -euo pipefail", self.text)

    def test_goes_through_capreq_not_core(self) -> None:
        """Core 를 직접 부르면 이 스크립트가 존재할 이유가 없다."""
        self.assertIn("/api/chat", self.text, "제품 입구를 안 부른다")
        self.assertIn("/api/capabilities", self.text)

    def test_checks_core_mediated_upload(self) -> None:
        """`input_id` 를 안 보면 **첨부가 버려져도 초록으로 끝난다** — 그게 그 버그였다."""
        self.assertIn("input_id", self.text)

    def test_shows_evidence_and_boundary(self) -> None:
        for token in ("assignment", "task_trust_domain", "node_tier_max"):
            self.assertIn(token, self.text, f"증적/경계 항목이 빠졌다: {token}")

    def test_compares_catalog_against_core(self) -> None:
        """정적 사본을 읽고 있어도 「능력이 보인다」가 되면 안 된다."""
        self.assertIn("/v1/capabilities", self.text, "Core 카탈로그와 대조하지 않는다")

    def test_separates_routing_miss_from_wiring(self) -> None:
        """라우팅은 매번 같지 않다. 배선 실패와 같이 세면 검사가 흔들린다."""
        self.assertIn("exit 2", self.text, "라우팅 빗나감을 따로 세는 길이 없다")
        self.assertIn("route_bench", self.text, "정확도를 어디서 재는지 안 가리킨다")

    def test_cleans_up_only_what_it_started(self) -> None:
        """이미 떠 있던 사용자의 capreq 를 내리면 안 된다."""
        self.assertIn("trap cleanup EXIT", self.text)
        self.assertRegex(self.text, r'\[ -n "\$started" \]', "띄운 것만 내리는 분기가 없다")

    def test_no_secret_echo(self) -> None:
        """키를 출력하면 로그에 남는다. `http.sh` 가 헤더를 붙이고 여기서는 안 찍는다."""
        self.assertNotRegex(self.text, r"echo[^\n]*CAPNET_API_KEY")


class TestDocsPointAtIt(unittest.TestCase):
    """**세 곳이 가리켜야 한다.** 만든 사람 말고는 아무도 이 도구를 모른다.

    실제로 그랬다 — #145 가 머지된 뒤에도 `capreq_demo.sh` 는 `testing.md` **한 곳**에만
    있었다. `README` 의 실행 스크립트 표에도, 사용자 가이드 §1.5 에도 없었다.
    **읽는 사람이 셋 다 다르다** — 검사하는 사람 · 저장소를 처음 여는 사람 · 제품을 쓰는 사람.

    실패 메시지에 문서 전문을 쏟지 않는다 — 읽을 수 없는 출력은 검사를 죽인다.
    """

    TOOL = "scripts/capreq_demo.sh"

    def points(self, rel: str) -> bool:
        return self.TOOL in (ROOT / rel).read_text(encoding="utf-8")

    def test_testing_guide_lists_it(self) -> None:
        """CI 밖 도구는 검증 문서에 적히지 않으면 아무도 안 돌린다 (§4.6)."""
        self.assertTrue(self.points("docs/guide/testing.md"), "testing.md §4.6 이 안 가리킨다")

    def test_readme_lists_it(self) -> None:
        """저장소를 처음 여는 사람은 `README` 의 스크립트 표를 본다."""
        self.assertTrue(self.points("README.md"), "README 실행 스크립트 표에 없다")

    def test_user_guide_lists_it(self) -> None:
        """제품을 쓰는 사람은 `product_demo.sh` 옆에서 이것을 찾는다."""
        self.assertTrue(
            self.points("docs/guide/user-guide-ko.md"), "user-guide-ko.md §1.5 에 없다"
        )

    def test_user_guide_says_routing_is_not_a_score(self) -> None:
        """**같은 문장이 매번 같은 능력으로 가지 않는다.** 그걸 안 적으면 성적으로 읽힌다."""
        guide = (ROOT / "docs" / "guide" / "user-guide-ko.md").read_text(encoding="utf-8")
        self.assertIn("매번 같지 않습니다", guide, "라우팅이 흔들린다는 것을 안 적었다")


class TestProbeActuallyReadsTheScript(unittest.TestCase):
    def test_not_vacuous(self) -> None:
        """빈 파일을 상대로 통과하는 상태를 막는다."""
        self.assertGreater(len(DEMO.read_text(encoding="utf-8")), 2000)
        self.assertGreater(len(re.findall(r"^echo ", DEMO.read_text(encoding="utf-8"), re.M)), 5)


if __name__ == "__main__":
    unittest.main()
