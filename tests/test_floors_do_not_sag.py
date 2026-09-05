r"""**바닥을 내리면 초록인가** (큐 #50 · `#210` 계열).

## 왜 있는가

이 회차들이 반복해서 잡아 온 결함은 **「0건인데 통과」**다 —
`#180`(누출 검사가 아무것도 안 보고 「깨끗하다」) · `#181`(통합 검사 0개도 초록) ·
`tally.sh`(`pass=0 · fail=0` 이 「전부 재현된다」).

고치는 방법은 늘 같았다: **바닥**을 둔다.

```python
self.assertGreaterEqual(len(_sites()), 3, _sites())      # 이번 회차 #220
REFERENCE_FLOOR = 355                                     # #221 · 큐 #41
```

**그런데 바닥 자체를 내리면 아무도 울지 않는다.** `355` → `0`,
`3` → `0` 으로 한 줄 고치면 전부 초록이고, 그 검사들은 **지키는 척**만 하게 된다.
`#210` 이 「바닥을 내리면 초록」을 잡은 자리와 같은 모양이고, 이번에는 그 **바닥들 자체**다.

## 실측 (2026-09-05)

| 무엇 | 수 |
|---|---|
| `tests/` 의 바닥 단언 (`assertGreater[Equal](…, N)`) | **90** |
| 이름 붙은 바닥 상수 (`…FLOOR…` · `…MIN…`) | **2** — `REFERENCE_FLOOR` · `MIN_LIMIT` |
| 그것이 든 파일 | **48** |
| 바닥이 **내려가는 것**을 막던 검사 | **0** |

**상수를 안 세면 절반만 지킨다.** 첫 판은 단언의 리터럴만 봤고, 그래서
`REFERENCE_FLOOR = 355` 를 `0` 으로 바꾸는 뮤테이션이 **그대로 통과했다.**
`self.REFERENCE_FLOOR` 는 단언 자리에 숫자로 보이지 않기 때문이다.

## 어떻게 막나 — 등록부

`scripts/floor_registry.py` 가 바닥을 전부 뽑아 `tests/floors.json` 에 적는다.
이 검사는 **지금 값이 등록 값보다 낮지 않은가**만 본다.

- **올리는 것은 자유다** — 실측이 늘면 바닥도 따라 올라간다. 등록부를 갱신하면 된다
- **내리려면 등록부를 같이 고쳐야 한다** — 한 줄로 조용히 못 낮춘다
- **새 바닥은 등록된다** — 등록 안 된 바닥이 있으면 운다
- **사라진 바닥은 등록부에서 빠진다** — 지워진 검사를 「지키고 있다」고 세지 않는다

키는 `파일::함수#순번` 이다. 줄 번호로 잡으면 **한 줄만 넣어도 전부 어긋난다.**

## 무엇을 안 보나

- 바닥이 **옳은 값인가.** `3` 이 맞는지 `30` 이 맞는지는 각 검사가 말한다.
  여기가 보는 것은 **소리 없이 낮아졌는가** 하나다
- 이름이 `FLOOR`·`MIN` 을 안 품은 상수. `EXPECTED_TOTAL = 52` 같은 **정확한 기대값**은
  올라가도 내려가도 틀린 것이라 「내리면 운다」가 맞지 않는다 — 그 파일이 직접 지킨다
- 계산해서 넣는 바닥 (`len(x) // 2` 등). 오늘 `tests/` 에는 없다
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tests" / "floors.json"

sys.path.insert(0, str(ROOT / "scripts"))
from floor_registry import check, floors, load  # noqa: E402


class TestFloorsAreRegistered(unittest.TestCase):
    def test_registry_exists(self) -> None:
        self.assertTrue(REGISTRY.is_file(),
                        "tests/floors.json 이 없다 — `python3 scripts/floor_registry.py --write`")

    def test_no_floor_was_lowered(self) -> None:
        """**여기가 핵심이다.** 한 줄로 바닥을 낮추면 검사가 지키는 척만 한다."""
        self.assertEqual(
            [], check(),
            "바닥 등록부와 어긋난다. 올린 것이라면 "
            "`python3 scripts/floor_registry.py --write` 로 갱신한다:\n  "
            + "\n  ".join(check()),
        )

    def test_every_floor_is_registered(self) -> None:
        now, was = floors(), load()
        self.assertTrue(now, "바닥을 하나도 못 찾았다 — 추출기가 죽었다")
        missing = sorted(k for k in now if k not in was)
        self.assertEqual([], missing, f"등록 안 된 바닥: {missing}")

    def test_registry_has_no_ghosts(self) -> None:
        """지워진 검사가 남아 있으면 「88건을 지킨다」가 거짓이 된다."""
        now, was = floors(), load()
        self.assertTrue(was, "등록부가 비었다")
        ghosts = sorted(k for k in was if k not in now)
        self.assertEqual([], ghosts, f"사라진 바닥이 등록부에 남아 있다: {ghosts}")


class TestProbeActuallyScans(unittest.TestCase):
    """추출기가 죽으면 위 검사가 **공허하게** 통과한다."""

    def test_enough_floors_are_seen(self) -> None:
        self.assertGreaterEqual(len(floors()), 80, f"바닥 {len(floors())}건만 봤다")

    def test_enough_files_have_one(self) -> None:
        files = {k.split("::", 1)[0] for k in floors()}
        self.assertGreaterEqual(len(files), 40, f"{len(files)}개 파일에서만 찾았다")

    def test_this_file_is_covered_too(self) -> None:
        """자기 자신을 안 세면 여기 바닥도 조용히 내려간다."""
        mine = [k for k in floors() if k.startswith("test_floors_do_not_sag.py::")]
        self.assertTrue(mine, "이 파일의 바닥이 등록부 밖이다")

    def test_named_floor_constants_are_seen(self) -> None:
        """리터럴만 보면 `self.REFERENCE_FLOOR` 를 쓰는 검사는 **한 줄로 0 이 된다**."""
        keys = floors()
        self.assertIn("test_core_sql_columns_exist.py::REFERENCE_FLOOR", keys)
        self.assertIn("test_gh_list_is_never_truncated.py::MIN_LIMIT", keys)

    def test_registry_values_are_ints(self) -> None:
        was = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertTrue(was, "등록부가 비었다")
        bad = sorted(k for k, v in was.items() if type(v) is not int)
        self.assertEqual([], bad, f"정수가 아닌 등록 값: {bad}")


if __name__ == "__main__":
    unittest.main()
