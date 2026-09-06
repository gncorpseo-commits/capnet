r"""이중 claim 이 **불가능한 이유 넷**을 못박는다 (배치 C #101 · 절대규칙 2 · pitfalls §4).

## 왜 있는가

`test_claim_takes_the_lock` 은 `FOR UPDATE SKIP LOCKED` 와 「lock 이 INSERT 보다 먼저」를 본다.
그런데 lock 은 **트랜잭션이 끝날 때까지만** 잡힌다. 다음 넷 중 하나만 무너져도 두 워커가 같은 작업을 집는다:

| # | 무엇 | 실측 (2026-09-06) |
|---|---|---|
| 1 | 연결이 `autocommit=False` 다 (풀·직결 둘 다) | `db.py` 두 자리 |
| 2 | `claim_next` 가 lock → INSERT → MARK 사이에 `commit()` 을 안 부른다 | 0 |
| 3 | 스키마의 마지막 방어선 — `assignment_one_live_per_task` (task 당 LEASED/RUNNING 하나) | `schema.sql` |
| 4 | 늦은 완료 보고는 `status IN ('LEASED','RUNNING')` 만 받는다 — EXPIRED 뒤 재배정된 작업을 옛 Node 가 못 닫는다 | `complete.py` |

RECLAIM 은 `LEASED AND lease_expires_at <= now()` 만 뒤집는다. Docker 가 없어 두 워커를 실제로 붙여 보지는 못했다 —
`tests/integration/check_pg_violations.py` 가 DB 에서 3 을 실측한다(CI 마이그레이션 잡).

## 재현

```bash
python3 -m unittest tests.test_claim_cannot_double
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "apps" / "core" / "app"
SCHEMA = ROOT / "docs" / "spec" / "schema.sql"


def _claim_next_body() -> str:
    src = (CORE / "claim.py").read_text(encoding="utf-8")
    i = src.index("def claim_next(")
    j = src.find("\n# ", i)
    return src[i:j if j > 0 else None]


class TestTheLockLivesUntilCommit(unittest.TestCase):
    def test_connections_are_not_autocommit(self) -> None:
        body = (CORE / "db.py").read_text(encoding="utf-8")
        sites = re.findall(r"autocommit\"?\s*[:=]\s*(\w+)", body)
        self.assertEqual(2, len(sites), sites)
        self.assertEqual({"False"}, set(sites), "autocommit 이 켜지면 lock 이 INSERT 전에 풀린다")

    def test_no_commit_between_lock_and_mark(self) -> None:
        body = _claim_next_body()
        for name in ("LOCK_SQL", "CLAIM_SQL", "MARK_SQL"):
            self.assertIn(name, body)
        self.assertNotRegex(body, r"\.commit\(\)|\.rollback\(\)", "claim_next 안에서 트랜잭션을 끊는다")


class TestTheSchemaIsTheLastLine(unittest.TestCase):
    def test_one_live_assignment_per_task(self) -> None:
        schema = SCHEMA.read_text(encoding="utf-8")
        m = re.search(r"CREATE UNIQUE INDEX (\w+)\s+ON assignment \(task_id\)\s+WHERE status IN \('LEASED', 'RUNNING'\)", schema)
        self.assertIsNotNone(m, "task 당 살아 있는 배정 하나를 강제하는 부분 유니크가 없다")
        assert m is not None
        self.assertEqual("assignment_one_live_per_task", m.group(1))


class TestLateReportsCannotCloseAReassignedTask(unittest.TestCase):
    def test_complete_requires_a_live_status(self) -> None:
        body = (CORE / "complete.py").read_text(encoding="utf-8")
        m = re.search(r"UPDATE assignment a\s+SET status = 'SUCCEEDED'.*?WHERE(.*?)RETURNING", body, re.S)
        self.assertIsNotNone(m)
        assert m is not None
        self.assertRegex(m.group(1), r"a\.status IN \('LEASED', 'RUNNING'\)", "EXPIRED 배정도 완료로 닫힌다")

    def test_reclaim_only_flips_expired_leases(self) -> None:
        body = (CORE / "claim.py").read_text(encoding="utf-8")
        m = re.search(r'RECLAIM_SQL = """(.*?)"""', body, re.S)
        assert m is not None
        self.assertRegex(m.group(1), r"a\.status = 'LEASED'")
        self.assertRegex(m.group(1), r"a\.lease_expires_at <= now\(\)")


if __name__ == "__main__":
    unittest.main()
