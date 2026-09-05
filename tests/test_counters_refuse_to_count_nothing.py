r"""세는 도구가 **0건을 통과로 치지 않는가** (배치 B #78 · `#230`·`#228` 잔여).

## 왜 있는가

`floor_registry.py` 와 `room_check_count.py` 는 다른 검사가 기대는 **자**다.
자가 0 을 내면 그 위의 검사는 「어긋남 0건」·「9/9」를 믿는다. 실측(2026-09-06):

| 사각 | 전 | 후 |
|---|---|---|
| H1 `floor_registry.check()` — 추출기 0건 + 등록부 `{}` | `[]` = **통과** | 「추출기가 죽었다」 |
| H1′ `--write` 가 0건이면 | 등록부를 **비운다** → 그 뒤 `--check` 영원히 초록 | rc 1, 안 쓴다 |
| H2 `room_check_count` 방이 0건 | `0건` 찍고 **rc 0** | rc 1 |
| H3 목록 `for` 머리 뒤에 `; do` 가 없으면 | 조용히 세다 만다 | `ValueError` |

## 재현

```bash
python3 -m unittest tests.test_counters_refuse_to_count_nothing
```
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import floor_registry as fr  # noqa: E402
import room_check_count as rc  # noqa: E402


class TestFloorRegistryRefusesZero(unittest.TestCase):
    def test_check_with_no_floors_is_not_a_pass(self) -> None:
        """H1 — 추출기 0건 · 등록부 `{}` 는 「어긋남 0건」이 아니다."""
        with mock.patch.object(fr, "floors", lambda: {}), mock.patch.object(fr, "load", lambda: {}):
            bad = fr.check()
        self.assertTrue(bad, "0건 + 빈 등록부가 통과로 나왔다")
        self.assertIn("추출기", bad[0])

    def test_write_with_no_floors_keeps_the_registry(self) -> None:
        """H1′ — 0건이면 등록부를 비우지 않는다."""
        with tempfile.TemporaryDirectory() as td:
            reg = Path(td) / "floors.json"
            reg.write_text('{"keep": 1}\n', encoding="utf-8")
            with mock.patch.object(fr, "floors", lambda: {}), \
                 mock.patch.object(fr, "REGISTRY", reg), \
                 mock.patch.object(sys, "argv", ["floor_registry.py", "--write"]):
                rcode = fr.main()
            self.assertEqual(1, rcode)
            self.assertEqual('{"keep": 1}\n', reg.read_text(encoding="utf-8"), "등록부가 지워졌다")

    def test_real_extractor_still_finds_plenty(self) -> None:
        self.assertGreaterEqual(len(fr.floors()), 100, len(fr.floors()))


class TestRoomCounterRefusesZero(unittest.TestCase):
    def test_a_room_with_zero_checks_fails_the_cli(self) -> None:
        """H2 — 0건은 「검사가 없다」가 아니라 세는 쪽이 죽은 것이다."""
        with tempfile.TemporaryDirectory() as td:
            empty = Path(td) / "room.sh"
            empty.write_text("#!/bin/bash\necho hi\n", encoding="utf-8")
            with mock.patch.dict(rc.ROOMS, {"empty_room": (empty, "chk")}), \
                 mock.patch.object(sys, "argv", ["room_check_count.py"]):
                rcode = rc.main()
        self.assertEqual(1, rcode, "0건인 방이 있는데 rc 0")

    def test_for_head_without_do_raises(self) -> None:
        """H3 — 목록 for 의 `; do` 를 못 찾으면 조용히 세다 말지 않는다."""
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "room.sh"
            bad.write_text('for path in \\\n  "a" \\\n  "b"\nchk "x"\nchk "y"\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                rc.count(bad, "chk")

    def test_the_real_rooms_still_count(self) -> None:
        proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "room_check_count.py")],
                              capture_output=True, text=True, timeout=60, cwd=ROOT)
        self.assertEqual(0, proc.returncode, proc.stderr)
        got = rc.counts()
        self.assertTrue(got, "방을 하나도 못 셌다")
        for name, n in got.items():
            with self.subTest(room=name):
                self.assertGreater(n, 0)


if __name__ == "__main__":
    unittest.main()
