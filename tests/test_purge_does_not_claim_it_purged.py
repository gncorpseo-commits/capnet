"""`POST /v1/inputs/{id}/purge` 가 **안 지웠으면서 지웠다고 말하지 않는가.**

## 왜 있는가

**실제로 그렇게 말하고 있었다 (2026-09-02).** 엔드포인트가 이랬다:

    marked = mark_purged(conn, input_id)      # STORED 인 것만 바꾼다 → 0행이면 None
    removed = purge_blob(input_id)
    return {**(marked or row), "purged_now": True, "file_removed": removed}

`mark_purged` 가 `None` 을 줘도 — 즉 **UPDATE 가 한 행도 안 바꿔도** —
`purged_now: True` 를 돌려줬다. 더 나쁜 것은 `marked or row` 다: 위에서 읽어 둔
**옛 행**을 함께 실어 보내서, 응답이 이렇게 **자기모순**이 됐다.

    {"storage_state": "STORED", "bytes_purged_at": null, "purged_now": true}

## 가상의 경우가 아니다

`storage_state` 는 `STORED` · `PURGED` 둘뿐이고(0011), 위에 `PURGED` 조기 반환이 있다.
그러니 `marked is None` 은 **경쟁**뿐이다 — 읽은 뒤 UPDATE 하기 전에 다른 쪽이 지웠다.

그 「다른 쪽」이 **같은 프로세스의 배경 스레드**다. `_gc_loop` 가 주기적으로
`task_input_purge_due` 를 훑어 `mark_purged` 를 부른다. 관리자 purge 와 GC 가
같은 입력을 동시에 집는 것은 구조상 가능하다.

바이트는 어느 쪽이든 지워지므로 **데이터 피해는 없다.** 거짓말하는 것은 **응답**이다 —
이번 회차가 계속 고쳐 온 「못 했다를 됐다로 뭉뚱그린다」와 같은 자리다.

## 무엇을 고정하나

1. `marked is None` 을 **보는 분기가 있다**
2. `marked or row` 로 옛 행을 실어 보내지 않는다
3. `purged_now: True` 는 `marked` 가 있는 경로에서만 나온다

## 무엇을 안 보나

**응답 스키마를 못박지 않는다.** 여기서 보는 것은 「0행일 때 했다고 말하는가」 하나다.
DB 를 띄우는 검사는 `tests/integration/check_input_purge.py` 가 따로 한다.

`ast` 로 본다 — `app.main` 은 fastapi 를 import 하므로 의존성 없는 환경에서
**모듈을 불러올 수 없다.** 파싱은 표준 라이브러리로 된다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"


def _purge_fn() -> ast.FunctionDef:
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "input_purge":
            return node
    raise AssertionError("input_purge 를 못 찾았다 — 이름이 바뀌었으면 이 검사도 고친다")


def _returns_with_purged_now_true(fn: ast.FunctionDef) -> list[ast.Dict]:
    """`purged_now: True` 를 담아 돌려주는 return 들."""
    found: list[ast.Dict] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
            continue
        for k, v in zip(node.value.keys, node.value.values):
            if (
                isinstance(k, ast.Constant)
                and k.value == "purged_now"
                and isinstance(v, ast.Constant)
                and v.value is True
            ):
                found.append(node.value)
    return found


class TestPurgeTellsTheTruth(unittest.TestCase):
    def test_zero_row_update_is_branched_on(self) -> None:
        """`mark_purged` 가 `None` 이면 **다른 길로 가야 한다.**"""
        fn = _purge_fn()
        guarded = False
        for node in ast.walk(fn):
            if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
                continue
            t = node.test
            if (
                isinstance(t.left, ast.Name)
                and t.left.id == "marked"
                and len(t.ops) == 1
                and isinstance(t.ops[0], ast.Is)
                and isinstance(t.comparators[0], ast.Constant)
                and t.comparators[0].value is None
            ):
                guarded = True
        self.assertTrue(guarded, "`marked is None` 을 보는 분기가 없다 — 0행인데 성공을 말한다")

    def test_old_row_is_not_smuggled_into_the_response(self) -> None:
        """`marked or row` 는 **옛 행**을 성공 응답에 실어 보낸다."""
        src = MAIN.read_text(encoding="utf-8")
        self.assertNotIn(
            "{**(marked or row)",
            src,
            "`marked or row` 가 남아 있다 — storage_state:STORED 와 purged_now:true 가 같이 나간다",
        )

    def test_purged_now_true_never_spreads_a_fallback(self) -> None:
        """`purged_now: True` 를 내는 자리는 `marked` **하나만** 펼쳐야 한다."""
        fn = _purge_fn()
        dicts = _returns_with_purged_now_true(fn)
        self.assertTrue(dicts, "`purged_now: True` 를 내는 return 이 없다 — 검사가 헛돌고 있다")
        for d in dicts:
            spreads = [v for k, v in zip(d.keys, d.values) if k is None]
            self.assertTrue(spreads, "성공 응답이 아무 행도 안 싣는다")
            for s in spreads:
                self.assertIsInstance(
                    s,
                    ast.Name,
                    "성공 응답이 `x or y` 같은 대체값을 펼친다 — 못 한 것을 했다고 말할 수 있다",
                )
                self.assertEqual(
                    s.id, "marked", f"성공 응답이 `marked` 가 아니라 `{s.id}` 를 싣는다"
                )


if __name__ == "__main__":
    unittest.main()
