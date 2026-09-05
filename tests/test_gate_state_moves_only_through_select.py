r"""게이트 사슬의 **상태 전이를 앱이 손으로 쓰는 UPDATE 는 0건** (배치 B #88 · 절대규칙 2 옆).

## 왜 있는가

절대규칙 2 는 `assignment`·`gate_run` 의 **INSERT** 만 말한다 (`test_absolute_rules_are_enforced`).
사슬의 나머지 — `gate_run_passed`·`agent_capability`·`agent_capability_passed` — 와 **UPDATE** 는
그 검사 밖이었다. `UPDATE agent_capability SET gate_status = 'PASSED'` 한 줄이면 게이트 없이 증서가
생기는데, 그걸 막는 것은 스키마 FK 사슬뿐이었고 앱 쪽에서 세어 본 사람은 없었다.

## 실측 (2026-09-06) — `apps/core/app/gate.py`

| 문장 | 모양 | 전이를 정하는 것 |
|---|---|---|
| `INSERT INTO gate_run` | `INSERT … SELECT` | 러너 자격 (`is_gate_runner`) |
| `UPDATE gate_run … SET status = %(status)s` | `WHERE … AND status = 'RUNNING'` | 이전 상태 RUNNING · 값은 `assert_real_finish`/`assert_contract_finish` 가 임계와 대조한 **뒤** |
| `INSERT INTO gate_run_passed` | `INSERT … SELECT … WHERE gr.status = 'PASSED'` | gate_run 의 PASSED |
| `INSERT INTO agent_capability` (PASSED) | `INSERT … SELECT FROM gate_run_passed` + `ON CONFLICT DO UPDATE … EXCLUDED` | gate_run_passed 행 |
| `INSERT INTO agent_capability` (FAILED) | `… SELECT FROM gate_run WHERE status = 'FAILED'` + `WHERE agent_capability.gate_status <> 'PASSED'` | FAILED gate_run · PASSED 를 덮지 않는다 |
| `INSERT INTO agent_capability_passed` | `INSERT … SELECT … JOIN gate_run_passed` | 증서 사슬 |
| `UPDATE agent_capability_passed … SET revoked_at` | `WHERE … AND revoked_at IS NULL` · 근거 `REVOKE_EVIDENCE_SQL` (FAILED gate_run) | 행을 지우지 않는다 (D15) |
| 그 밖의 `UPDATE`/`DELETE` | **0** | — |

## 재현

```bash
python3 -m unittest tests.test_gate_state_moves_only_through_select
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "apps" / "core" / "app"
CHAIN = ("gate_run", "gate_run_passed", "agent_capability", "agent_capability_passed")
STMT = re.compile(r"(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(\w+)\b", re.I)


def _statements() -> list[tuple[str, str, str, str]]:
    """(파일, 동사, 표, 문장 본문) — 사슬 네 표를 건드리는 SQL 문장 전부."""
    out = []
    for p in sorted(CORE.glob("*.py")):
        src = p.read_text(encoding="utf-8")
        for m in STMT.finditer(src):
            table = m.group(2).lower()
            if table not in CHAIN:
                continue
            tail = src[m.start():m.start() + 900]
            end = tail.find('"""', 3)
            body = tail if end < 0 else tail[:end]
            out.append((p.name, m.group(1).split()[0].upper(), table, body))
    return out


class TestNoHandWrittenTransition(unittest.TestCase):
    def test_every_insert_is_a_select(self) -> None:
        inserts = [s for s in _statements() if s[1] == "INSERT"]
        self.assertGreaterEqual(len(inserts), 4, inserts)
        bad = [f"{f}:{t}" for f, _, t, body in inserts
               if not re.search(r"INSERT\s+INTO\s+\w+\s*\([^)]*\)\s*SELECT", body, re.S | re.I)]
        self.assertEqual([], bad, f"사슬 표에 값을 손으로 넣는 INSERT: {bad}")

    def test_every_update_pins_the_previous_state(self) -> None:
        updates = [s for s in _statements() if s[1] == "UPDATE"]
        self.assertEqual(2, len(updates), [(f, t) for f, _, t, _ in updates])
        guards = {"gate_run": r"AND\s+status\s*=\s*'RUNNING'",
                  "agent_capability_passed": r"AND\s+revoked_at\s+IS\s+NULL"}
        for f, _, table, body in updates:
            with self.subTest(table=table):
                self.assertIn(table, guards, f"{f}: 예상 밖의 UPDATE {table}")
                self.assertRegex(body, guards[table], f"{f}: UPDATE {table} 가 이전 상태를 고정하지 않는다")

    def test_no_delete(self) -> None:
        self.assertEqual([], [(f, t) for f, v, t, _ in _statements() if v == "DELETE"])

    def test_passed_is_only_ever_selected_from_the_chain(self) -> None:
        """`'PASSED'` 를 값으로 쓰는 INSERT 는 반드시 `gate_run_passed` 에서 SELECT 한다."""
        seen = 0
        for f, v, table, body in _statements():
            # `<> 'PASSED'` 는 값이 아니라 배제다 — 빼고 본다.
            if v != "INSERT" or "'PASSED'" not in re.sub(r"<>\s*'PASSED'", "", body):
                continue
            seen += 1
            with self.subTest(table=table):
                self.assertRegex(body, r"(FROM|JOIN)\s+gate_run_passed|\bstatus\s*=\s*'PASSED'",
                                 f"{f}: {table} 에 PASSED 를 근거 없이 넣는다")
        self.assertGreaterEqual(seen, 2, "PASSED 를 넣는 INSERT 를 못 찾았다")

    def test_failed_never_overwrites_passed(self) -> None:
        body = next(b for f, v, t, b in _statements() if t == "agent_capability" and "'FAILED'" in b)
        self.assertRegex(body, r"WHERE\s+agent_capability\.gate_status\s*<>\s*'PASSED'")


class TestFinishValidatesBeforeWriting(unittest.TestCase):
    def test_thresholds_are_asserted_before_the_update(self) -> None:
        src = (CORE / "gate.py").read_text(encoding="utf-8")
        fn = src[src.index("def finish_gate_run"):]
        fn = fn[:fn.index("\ndef ", 10)]
        self.assertIn('if status not in ("PASSED", "FAILED", "ERROR")', fn)
        first_write = fn.index("FINISH_SQL")
        for name in ("assert_real_finish", "assert_contract_finish"):
            with self.subTest(check=name):
                self.assertLess(fn.index(name), first_write, f"{name} 이 UPDATE 뒤에 온다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_todays_shape(self) -> None:
        shape = sorted((f, v, t) for f, v, t, _ in _statements())
        self.assertEqual([
            ("gate.py", "INSERT", "agent_capability"), ("gate.py", "INSERT", "agent_capability"),
            ("gate.py", "INSERT", "agent_capability_passed"), ("gate.py", "INSERT", "gate_run"),
            ("gate.py", "INSERT", "gate_run_passed"),
            ("gate.py", "UPDATE", "agent_capability_passed"), ("gate.py", "UPDATE", "gate_run"),
        ], shape)


if __name__ == "__main__":
    unittest.main()
