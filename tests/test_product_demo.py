"""제품 데모 한 파일이 **제품 주장 순서를 그대로 밟는가** (Wave D).

## 왜 있는가

이 스크립트는 「능력만 말하고, 파일을 붙이면, 승인 Node 에서 실행되고, 증적이 조회된다」를
한 파일로 보이는 것이다. 그 순서에서 한 칸이라도 빠지면 **주장의 일부가 증명되지 않은 채**
데모가 초록으로 끝난다 — 그게 이 검사가 막는 유일한 사고다.

DB·Docker 가 필요한 실행 자체는 `bash scripts/product_demo.sh` 가 한다. 여기서는
**무엇을 부르는지와 무엇을 주장하지 않는지**만 텍스트로 고정한다 (CI 단위 잡은 의존성 0).
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "scripts" / "product_demo.sh"
README = ROOT / "README.md"
GUIDE = ROOT / "docs" / "guide" / "user-guide-ko.md"


class TestScriptExists(unittest.TestCase):
    def test_present_and_executable(self) -> None:
        self.assertTrue(DEMO.is_file(), "scripts/product_demo.sh 이 없다")
        self.assertTrue(os.access(DEMO, os.X_OK), "실행 권한이 없다")

    def test_fails_loudly(self) -> None:
        """`set -euo pipefail` 없이는 중간 실패가 exit 0 으로 묻힌다."""
        self.assertIn("set -euo pipefail", DEMO.read_text(encoding="utf-8"))


class TestClaimOrder(unittest.TestCase):
    """제품 주장 다섯 칸이 **전부** 있는가."""

    def setUp(self) -> None:
        self.text = DEMO.read_text(encoding="utf-8")

    def test_calls_every_step(self) -> None:
        for endpoint, why in (
            ("/health", "살아 있나"),
            ("/v1/capabilities", "무엇을 할 수 있나"),
            ("/v1/inputs", "파일은 Core 가 받는다 (D22 · D8′)"),
            ("/v1/tasks", "능력만 말한다"),
            ("/v1/ops/work-units", "얼마나 돌았나 (D26)"),
        ):
            self.assertIn(endpoint, self.text, f"{endpoint} 를 부르지 않는다 — {why}")

    def test_shows_the_assignment_evidence(self) -> None:
        """증적 네 값이 화면에 나와야 한다 — 그게 「어디로 갔는지 답할 수 있다」의 증거다."""
        for col in ("node_id", "agent_id", "task_trust_domain", "node_trust_domain",
                    "capability_tier", "node_tier_max"):
            self.assertIn(col, self.text, f"증적 {col} 을 찍지 않는다")

    def test_rejects_dummy_run(self) -> None:
        """placeholder 로 돈 것을 성공으로 세면 데모가 거짓말한다."""
        self.assertIn("dummy", self.text)

    def test_no_device_address_in_request(self) -> None:
        """요청 본문에 기기를 지목하는 칸이 없어야 한다 — Core 가 정한다."""
        self.assertNotIn("requestedAgentId", self.text)
        self.assertNotIn("node_id\\\":", self.text)


class TestHonestClaims(unittest.TestCase):
    def test_disclaims_quality(self) -> None:
        text = DEMO.read_text(encoding="utf-8")
        self.assertIn("주장하지 않", text)
        self.assertIn("quality_profile='none'", text)


class TestDocumented(unittest.TestCase):
    def test_readme_points_at_it(self) -> None:
        self.assertIn("product_demo.sh", README.read_text(encoding="utf-8"))

    def test_user_guide_points_at_it(self) -> None:
        guide = GUIDE.read_text(encoding="utf-8")
        self.assertIn("product_demo.sh", guide)
        self.assertIn("정확도가 아닙니다", guide)

    def test_no_powershell_twin_is_claimed(self) -> None:
        """`.ps1` 이 없다는 것을 README 가 말해야 한다 — 촬영은 PowerShell 로 한다."""
        self.assertFalse((ROOT / "scripts" / "product_demo.ps1").exists())
        self.assertIn("`.ps1` 판은 없다", README.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
