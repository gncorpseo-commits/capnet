r"""DDL(마이그레이션)이 **어느 Decision 에서 왔는지** 머리에 적혀 있는가 — 브리지 PROTOCOL 위반의 정적 탐지 (배치 D #153).

## 왜 있는가

`PROTOCOL.md`: 「구현은 Decision 과 Confirm 이 일치할 때만」. 마이그레이션은 되돌리기 비싼 DDL 이라 그 근거가 파일 머리에
있어야 한다. 실측(2026-09-06): 18개 중 16개가 머리 6줄 안에 `D24`·`SD-013`·`B2`·`P2-1`·`I1`·`G2`·`Decision` 같은 표식을 갖는다.
`0001`·`0002` 는 브리지 이전(baseline·읽기 전용 뷰), `0015` 는 근거가 파일이 아니라 브리지 블록(`assignment-attempt-cap`)에 있다 —
`migrations/` 는 사람 몫이라 머리를 고치지 않고 여기 표에 적는다.

## 재현

```bash
python3 -m unittest tests.test_ddl_cites_its_decision
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = sorted((ROOT / "migrations").glob("*.sql"))
INBOX = ROOT / "docs" / "bridge" / "inbox-cursor.md"
TOKEN = re.compile(r"\bD\d{1,2}\b|\bSD-\d{3}\b|\bDecision\b|\bB\d\b|\bP\d-\d\b|\bG\d\b|\bI\d\b|\bD-\w+")
# 머리에 표식이 없어도 되는 것 — 이유가 여기 있다.
DECISION_CITED_ELSEWHERE = {
    "0001_baseline.sql": "브리지 이전 · no-op baseline",
    "0002_provenance_drift_view.sql": "브리지 이전 · 읽기 전용 뷰",
    "0015_attempt_cap.sql": "근거는 inbox 블록 `topic: assignment-attempt-cap` (PR 머지 대기 블록) — 머리는 사람 몫",
}


class TestEveryMigrationCitesADecision(unittest.TestCase):
    def test_headers(self) -> None:
        self.assertGreaterEqual(len(MIGRATIONS), 18)
        bad = []
        for p in MIGRATIONS:
            head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:6])
            if TOKEN.search(head) or p.name in DECISION_CITED_ELSEWHERE:
                continue
            bad.append(p.name)
        self.assertEqual([], bad, f"머리에 Decision 표식이 없는 DDL: {bad} — 근거를 적거나 표에 이유와 함께 올려라")

    def test_exceptions_are_real_and_the_bridge_block_exists(self) -> None:
        names = {p.name for p in MIGRATIONS}
        for f, why in DECISION_CITED_ELSEWHERE.items():
            with self.subTest(file=f):
                self.assertIn(f, names, f"표에 없는 파일이 남아 있다: {f}")
                self.assertTrue(why.strip())
        self.assertIn("topic: assignment-attempt-cap", INBOX.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
