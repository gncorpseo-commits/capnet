"""배정 스냅샷 네 열이 **DB → API → 데모 출력**까지 이어져 있는지 본다.

## 왜 있는가

`assignment` 는 배정 시점의 `task_trust_domain`·`node_trust_domain`·`capability_tier`·
`node_tier_max` 를 스냅샷으로 들고 있고, 그 값들은 앱이 계산한 것이 아니라 **DB 가 복합 FK 로
검증한** 것이다. 제품 주장(「승인한 신뢰 도메인 안의 기기로만 간다」)의 증적이 바로 이 넷인데,
`GET /v1/tasks/{id}` 가 `id·status·agent_id·node_id·finished_at` 만 돌려주고 있었다.
**증적이 DB 에는 있는데 밖에서 볼 수 없었다.**

사슬은 세 칸이고 어느 한 칸만 빠져도 조용히 무의미해진다:
컬럼이 있다(schema) → API 가 준다(main.py) → 데모가 찍는다(demo.sh · demo.ps1).

`.sh` 만 고치고 `.ps1` 을 놓치는 사고는 이미 한 번 났다(G5 · `test_agent_arch_wiring`).
촬영은 PowerShell 로 한다. 그래서 두 계열을 **같이** 본다.

## 판정 방식과 그 한계

텍스트 검사다. SQL 을 파싱하지 않고 컬럼 이름이 그 파일 안에 있는지만 본다 —
「이름은 있지만 다른 쿼리에 실려 있는」 경우는 못 잡는다. 실행해서 확인하는 것은
`clean_room.sh` / `prod_room.sh` 의 몫이고, 이 검사는 그 둘을 **못 돌리는 환경에서도**
사슬이 끊긴 것을 알아채기 위한 것이다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 배정 판정의 근거가 된 스냅샷. 이 넷이 한 벌이다.
SNAPSHOT_COLUMNS = (
    "task_trust_domain",
    "node_trust_domain",
    "capability_tier",
    "node_tier_max",
)


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestAssignmentEvidenceWiring(unittest.TestCase):
    def test_schema_declares_snapshot_columns(self) -> None:
        """① DB — `assignment` 가 넷을 스냅샷으로 들고 있다."""
        schema = _read("docs/spec/schema.sql")
        block = re.search(r"CREATE TABLE assignment\b.*?\n\);", schema, re.S)
        self.assertIsNotNone(block, "schema.sql 에 assignment 정의가 없다")
        assert block is not None
        for col in SNAPSHOT_COLUMNS:
            self.assertIn(col, block.group(0), f"assignment 에 {col} 이 없다")

    def test_task_detail_api_returns_snapshot(self) -> None:
        """② API — `GET /v1/tasks/{id}` 의 assignment SELECT 가 넷을 싣는다.

        이 엔드포인트의 SELECT 만 본다. 파일 어딘가에 이름이 있는 것으로는 통과시키지 않는다 —
        그러면 `claim.py` 등 다른 쿼리 때문에 항상 통과해 검사가 죽는다.
        """
        main = _read("apps/core/app/main.py")
        anchor = main.find('@app.get("/v1/tasks/{task_id}")')
        self.assertNotEqual(anchor, -1, "get_task 엔드포인트를 못 찾았다")
        # `assignment = conn.execute(` 뒤부터 잘라야 앞쪽 task SELECT 를 삼키지 않는다.
        body = main[anchor:]
        start = body.find("assignment = conn.execute(")
        self.assertNotEqual(start, -1, "get_task 안에서 assignment 조회를 못 찾았다")
        select = re.search(
            r'"SELECT(?:(?!FROM task)[^;])*?FROM assignment WHERE id = %s"',
            body[start:],
            re.S,
        )
        self.assertIsNotNone(select, "get_task 안에서 assignment SELECT 를 못 찾았다")
        assert select is not None
        for col in SNAPSHOT_COLUMNS:
            self.assertIn(
                col, select.group(0),
                f"GET /v1/tasks/{{id}} 가 {col} 을 안 준다 — 증적이 밖에서 안 보인다",
            )

    def test_demo_scripts_print_snapshot(self) -> None:
        """③ 데모 — `.sh` 와 `.ps1` **둘 다** 넷을 찍는다.

        한쪽만 고치는 사고가 G5 에서 이미 났고, 촬영은 PowerShell 이다.
        """
        for rel in ("scripts/demo.sh", "scripts/demo.ps1"):
            body = _read(rel)
            for col in SNAPSHOT_COLUMNS:
                self.assertIn(
                    col, body,
                    f"{rel} 이 {col} 을 안 찍는다 — 촬영 화면에서 경계가 안 보인다",
                )

    def test_openapi_documents_snapshot(self) -> None:
        """④ 문서 — 응답 필드가 늘었으면 openapi 에도 적는다.

        `test_openapi_drift` 는 **경로만** 본다. 필드는 못 잡는다 — D24 때 `org_id` 셋이
        정확히 그렇게 새어 나갔다(#73). 그 구멍을 이 건에 한해 막는다.
        """
        for rel in ("apps/core/openapi.yaml", "docs/spec/openapi.yaml"):
            body = _read(rel)
            for col in SNAPSHOT_COLUMNS:
                self.assertIn(col, body, f"{rel} 에 {col} 이 안 적혀 있다")


if __name__ == "__main__":
    unittest.main()
