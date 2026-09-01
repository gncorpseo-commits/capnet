"""`scripts/regate.sh` 가 **폐기된 증서를 재게이트 대상으로 집지 않는가**.

## 왜 있는가

**실측으로 어긋나 있었다 (2026-09-02).**

    provenance_drift 뷰:  라우팅되는 드리프트 0
    regate.sh --dry-run:  재게이트 대상 1 건

같은 사실인데 답이 달랐다. 원인은 **정의가 두 곳에 있었기 때문**이다 — 스크립트가 뷰의
조인을 손으로 다시 쓰면서 **`acp.revoked_at IS NULL` 을 빠뜨렸다.**

그 1건은 `seed-agent` 이고 `revoked_at = 2026-08-10` 인 **폐기된 증서**였다.

## 왜 이게 위험한가

폐기된 것을 재게이트하면 `gate.py` 의 `UPSERT_AC_PASSED` 가
`agent_capability.gate_run_id` 를 새 run 으로 옮긴다 — **폐기가 되돌려질 수 있다.**

지금까지 안 터진 이유는 Node 에 그 가중치가 없어 「건너뜀」 으로 빠졌기 때문이다.
**우연이지 방어가 아니었다.**

폐기는 이 저장소의 안전 주장 가운데 하나다 (`tests/integration/check_revocation.py`).
그 주장을 운영 도구가 우회할 수 있으면 안 된다.

## 무엇을 고정하나

1. 스크립트가 **`provenance_drift` 뷰를 읽는가** — 조인을 다시 짜지 않는다
2. 스크립트가 **조인을 재구현하지 않는가** (`agent_capability_passed` 를 직접 조인하면
   같은 실수가 되풀이된다)
3. 뷰가 **`revoked_at IS NULL` 을 본다** — 정본 쪽이 무너지면 파생도 무너진다

## 실측으로 확인한 것

`revoked_at` 을 (롤백되는 트랜잭션 안에서) 지우면 뷰가 **1**, 유지하면 **0** 이다.
뷰의 `still_routable` 이 곧 폐기를 아는 정의다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "regate.sh"
# 뷰의 마지막 정의가 있는 마이그레이션 (0002 가 만들고 0004 가 폐기 인식을 더한다)
VIEW_SQL = ROOT / "migrations" / "0004_capability_revocation.sql"


class TestRegateUsesTheCanonicalView(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_reads_the_view(self) -> None:
        self.assertIn("provenance_drift", self.text, "정본 뷰를 안 읽는다")
        self.assertIn("still_routable", self.text, "뷰의 판정을 안 쓴다")

    def test_does_not_rebuild_the_join(self) -> None:
        """조인을 다시 짜면 `revoked_at` 을 또 빠뜨린다 — 실제로 그랬다."""
        self.assertNotIn(
            "agent_capability_passed",
            self.text,
            "뷰의 조인을 스크립트가 다시 구현했다 — 정의가 둘이 된다",
        )

    def test_view_definition_knows_about_revocation(self) -> None:
        """정본이 무너지면 파생도 무너진다."""
        sql = VIEW_SQL.read_text(encoding="utf-8")
        i = sql.find("CREATE OR REPLACE VIEW provenance_drift AS")
        self.assertGreater(i, -1, "0004 가 뷰를 다시 정의하지 않는다 — 검사를 따라 고친다")
        body = sql[i:]
        self.assertIn(
            "revoked_at IS NULL", body, "뷰가 폐기를 안 본다 — regate 가 폐기를 되살릴 수 있다"
        )

    def test_probe_actually_reads_the_script(self) -> None:
        self.assertGreater(len(self.text), 1500)
        # 들여쓴 것까지 센다 — 대부분 `if` 안에 있다.
        self.assertGreater(len(re.findall(r"\becho ", self.text)), 3)


if __name__ == "__main__":
    unittest.main()
