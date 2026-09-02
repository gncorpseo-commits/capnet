"""깨진 계약이 **출력 칸 검사를 조용히 끄지 않는가.**

## 왜 있는가

`complete.py` 는 「Node 가 칸 이름을 주장하지 못한다」를 지키는 자리다:

    required = set(_required_keys(conn, assignment_id))
    given = set(output)
    if required and given != required:      # ← `required` 가 비면 통째로 꺼진다
        raise OutputKeysMismatch(...)

그리고 `_required_keys` 는 **「선언 안 함」과 「선언이 깨졌다」를 구분하지 않았다:**

    if isinstance(required, list) and all(isinstance(k, str) for k in required):
        return required
    return []                                # ← ["label", 5] 도 여기로 떨어졌다

실측 (2026-09-02 · 이 검사와 같은 스텁으로):

| `output_schema.required` | 옛 `_required_keys` | 옛 `_output_key` |
|---|---|---|
| `["label"]` | `["label"]` | `"label"` |
| `["label", 5]` | **`[]`** | **`"vector"`** |
| `"label"` (문자열) | **`[]`** | **`"vector"`** |

그래서 계약 하나가 깨져 있으면 **두 가지가 동시에 조용히** 일어났다:

1. 칸 검사가 통째로 꺼져 **Node 가 아무 칸이나 보고해도 그대로 받아 적혔다**
2. `_output_key` 가 계약과 무관한 `"vector"` 로 떨어져 **「게이트가 검증한 출력」과
   「증적에 남는 출력」이 갈라졌다** — 바로 그 갈라짐을 막으려고 있는 코드가
   계약이 깨지면 **스스로 열렸다**

오늘 등록된 능력 10종은 전부 `required` 를 문자열 목록으로 선언한다(데모 9 + seed 1).
**그러니 지금 새고 있지는 않다. 나기 전에 막는다** (#169 와 같은 자리).

## 무엇을 고정하나

1. 깨진 `required` 는 **`BrokenOutputContract`** — 조용히 `[]` 가 되지 않는다
2. 그 예외는 `OutputKeysMismatch` 의 하위형이다 — `main.py` 가 이미 잡아 **422** 로 돌린다
3. **선언이 아예 없는 것**(`None`·`[]`)은 그대로 `[]` — 그쪽은 부르는 쪽이 로그로 남긴다
4. 정상 선언은 순서를 지켜 그대로 돌아온다 (`_output_key` 는 첫 항목)

## 무엇을 안 보나

**「required 가 없으면 거절할지」는 정하지 않는다.** 그건 정책이라 브리지 Decision 이다.
여기서 보는 것은 **깨진 것을 없는 것처럼 다루지 않는가** 하나다.

DB 없이 돈다 — `complete.py` 의 `psycopg` 는 **주석에만** 쓰이므로(`from __future__ import
annotations`) 빈 모듈로 세우고 가짜 커넥션을 넣는다.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps" / "core" / "app" / "complete.py"


def _load_complete():
    """`complete.py` 를 **파일 경로로** 불러온다.

    `psycopg` 는 이 파일에서 **주석용**이라(`from __future__ import annotations`)
    빈 모듈로도 그대로 돈다. 다만 그 스텁을 `sys.modules` 에 **남기면 안 된다** —
    남기면 psycopg 가 진짜로 필요한 다른 검사들이 스텁을 집어 깨진다
    (실제로 그렇게 깨뜨렸다: `run_tests` 가 skip 7 → 2 로 줄고 5건이 에러였다).
    그래서 넣었던 것만 되돌리고, `sys.path` 도 건드리지 않는다.
    """
    added = "psycopg" not in sys.modules
    if added:
        sys.modules["psycopg"] = types.ModuleType("psycopg")
    try:
        spec = importlib.util.spec_from_file_location("_capnet_complete_probe", SOURCE)
        assert spec and spec.loader, SOURCE
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        if added:
            sys.modules.pop("psycopg", None)


complete = _load_complete()


class _Cur:
    def __init__(self, row: dict | None) -> None:
        self._row = row

    def fetchone(self) -> dict | None:
        return self._row


class _Conn:
    """`conn.execute(...).fetchone()` 만 흉내 낸다."""

    def __init__(self, row: dict | None) -> None:
        self._row = row

    def execute(self, *_a, **_k) -> _Cur:
        return _Cur(self._row)


def keys_for(required: object) -> list[str]:
    return complete._required_keys(_Conn({"required": required}), uuid.uuid4())


def output_key_for(required: object) -> str:
    return complete._output_key(_Conn({"required": required}), uuid.uuid4())


class TestBrokenContractIsNotSilent(unittest.TestCase):
    BROKEN = (["label", 5], "label", {"a": 1}, 7, [None], [["label"]])

    def test_broken_required_raises(self) -> None:
        for required in self.BROKEN:
            with self.subTest(required=required):
                with self.assertRaises(complete.BrokenOutputContract):
                    keys_for(required)

    def test_broken_required_does_not_fall_back_to_vector(self) -> None:
        """예전에는 `_output_key` 가 계약과 무관한 `"vector"` 를 골랐다."""
        for required in self.BROKEN:
            with self.subTest(required=required):
                with self.assertRaises(complete.BrokenOutputContract):
                    output_key_for(required)

    def test_broken_contract_is_caught_by_the_existing_handler(self) -> None:
        """`main.py` 는 `OutputKeysMismatch` 만 잡는다 — 상속이 끊기면 500 이 된다."""
        self.assertTrue(
            issubclass(complete.BrokenOutputContract, complete.OutputKeysMismatch)
        )

    def test_message_names_the_broken_value(self) -> None:
        """무엇이 깨졌는지 안 적으면 고칠 사람이 계약을 찾아 헤맨다."""
        with self.assertRaises(complete.BrokenOutputContract) as ctx:
            keys_for(["label", 5])
        self.assertIn(json.dumps(["label", 5]), str(ctx.exception))


class TestUndeclaredIsStillEmpty(unittest.TestCase):
    """**선언 안 함**은 깨진 것이 아니다 — 동작을 바꾸지 않는다."""

    def test_none_and_empty_stay_empty(self) -> None:
        for required in (None, []):
            with self.subTest(required=required):
                self.assertEqual(keys_for(required), [])
                self.assertEqual(output_key_for(required), "vector")

    def test_missing_row_stays_empty(self) -> None:
        self.assertEqual(complete._required_keys(_Conn(None), uuid.uuid4()), [])


class TestDeclaredContractIsUsed(unittest.TestCase):
    def test_string_list_passes_through_in_order(self) -> None:
        self.assertEqual(keys_for(["query", "ranking"]), ["query", "ranking"])
        self.assertEqual(output_key_for(["query", "ranking"]), "query")

    def test_probe_actually_exercises_both_sides(self) -> None:
        """정상·깨짐 양쪽을 실제로 밟는지 — 한쪽만 돌면 이 파일은 헛돈다."""
        self.assertEqual(keys_for(["label"]), ["label"])
        with self.assertRaises(complete.BrokenOutputContract):
            keys_for(["label", 5])


class _RoutingConn:
    """`complete_assignment` 가 쓰는 세 질의만 흉내 낸다.

    `COMPLETE_SQL` → assignment 행 · `OUTPUT_KEY_SQL` → 계약의 `required` ·
    `MARK_TASK_SQL` → task 행. SQL 본문으로 갈라서 **실제 함수를 그대로 돌린다.**
    """

    def __init__(self, required: object) -> None:
        self.required = required
        self.result_ref: str | None = None

    def execute(self, sql: str, params: dict | None = None) -> _Cur:
        if "UPDATE assignment" in sql:
            return _Cur({
                "id": uuid.uuid4(), "task_id": uuid.uuid4(), "agent_id": uuid.uuid4(),
                "node_id": uuid.uuid4(), "status": "SUCCEEDED",
                "weights_sha256": "a" * 64,
            })
        if "output_schema -> 'required'" in sql:
            return _Cur({"required": self.required})
        if "UPDATE task" in sql:
            self.result_ref = (params or {}).get("result_ref")
            return _Cur({
                "id": uuid.uuid4(), "status": "COMPLETED",
                "result_ref": self.result_ref, "current_assignment_id": uuid.uuid4(),
            })
        raise AssertionError(f"예상 못 한 질의: {sql[:60]}")


def run_complete(required: object, output: dict) -> _RoutingConn:
    conn = _RoutingConn(required)
    complete.complete_assignment(
        conn, assignment_id=uuid.uuid4(), weights_sha256="a" * 64,
        label=None, output=output, confidence=None, dummy=False, duration_ms=1,
    )
    return conn


class TestTheGuardItself(unittest.TestCase):
    """`complete_assignment` 의 칸 검사를 **돌려서** 본다 (DB 없이)."""

    def test_matching_keys_are_recorded(self) -> None:
        conn = run_complete(["label"], {"label": "x"})
        self.assertIn('"label":"x"', conn.result_ref or "")

    def test_mismatching_keys_are_refused(self) -> None:
        with self.assertRaises(complete.OutputKeysMismatch):
            run_complete(["label"], {"labl": "x"})

    def test_broken_contract_is_refused_not_skipped(self) -> None:
        """예전에는 여기서 **검사가 통째로 꺼져** `{"labl": "x"}` 가 그대로 적혔다."""
        with self.assertRaises(complete.BrokenOutputContract):
            run_complete(["label", 5], {"labl": "x"})

    def test_undeclared_contract_says_it_did_not_check(self) -> None:
        """받는 것은 그대로 두되 **안 봤다는 사실을 남긴다.**"""
        with self.assertLogs(complete.logger.name, level="WARNING") as cm:
            conn = run_complete(None, {"anything": 1})
        self.assertTrue(
            any("unchecked" in m for m in cm.output),
            f"검사하지 않았다는 기록이 없다: {cm.output}",
        )
        self.assertIn('"anything":1', conn.result_ref or "")


class TestTodaysCapabilitiesDeclareRequired(unittest.TestCase):
    """오늘 새고 있지 않다는 근거 — 데모가 등록하는 능력이 전부 선언한다.

    **개수를 못박지 않는다.** 능력은 는다. 보는 것은 「`output_schema` 를 쓰는
    데모는 전부 `required` 도 쓴다」는 관계다.
    """

    def test_every_demo_output_schema_declares_required(self) -> None:
        missing = []
        seen = 0
        for path in sorted((ROOT / "scripts").glob("*_demo.sh")):
            body = path.read_text(encoding="utf-8")
            if '"output_schema"' not in body:
                continue
            seen += 1
            if '"required"' not in body.split('"output_schema"', 1)[1][:400]:
                missing.append(path.name)
        self.assertGreater(seen, 5, f"output_schema 를 쓰는 데모를 {seen}개밖에 못 찾았다")
        self.assertEqual(missing, [], f"required 를 선언하지 않는 데모: {missing}")


if __name__ == "__main__":
    unittest.main()
