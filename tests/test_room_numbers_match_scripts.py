r"""문서의 **방 통과 숫자**가 스크립트와 맞는가 (큐 #48).

## 왜 있는가

`clean_room` · `prod_room` 의 통과 수는 문서 여러 곳에 **손으로** 적혀 있다.
스크립트가 자라면 그 숫자가 낡는데, **아무도 세고 있지 않았다.**

실제로 갈려 있었다 — 같은 것을 두 숫자로 부르고 있었다:

| 어디 | 뭐라고 |
|---|---|
| `docs/ops/shoot-day-runbook.md` | `prod_room` **통과 51** |
| `docs/bridge/queue-batches.md` | `prod_room 51/51` |
| **`docs/ops/contest-submission-checklist.md`** | `prod_room` **27/27** ← 낡았다 |

`#205` 가 프로브 라우트를 **5 → 24** 로 늘리면서 27 이 51 이 됐다. 런북은 따라갔고
**제출 정본 체크리스트는 안 따라갔다.** 심사자가 읽는 쪽이 낡은 것이다.

## 어떻게 세나 — 실행 없이

`scripts/room_check_count.py` 가 소스에서 센다. 최상위 `chk`/`step` 은 한 건,
`for path in … ; do … chk … done` 은 **경로 수 × 루프 안 chk 수**.

```bash
python3 scripts/room_check_count.py
# clean_room   9건
# prod_room    51건
```

### 파이썬 `for` 를 세다가 두 건을 잃을 뻔했다 (적어 둔다)

`prod_room.sh` 안에는 `python3 -c '…'` 로 넘기는 코드가 있고, 그 안의
`for n in d["nodes"]:` 도 **열 0 에서 시작한다.** 그것을 셸 루프로 잡으면 그 뒤의
최상위 `chk` **두 건이 통째로 사라져** 49 가 나온다. 실제로 그렇게 나왔다.
셸 `for` 는 줄이 `\\` 나 `; do` 로 끝난다 — 그걸로 가른다.

**세는 도구도 틀릴 수 있다.** 그래서 아래 `test_the_counter_is_not_fooled` 가 그 함정을
그대로 심어 둔다.

## 무엇을 안 보나

- **실행 결과가 아니다.** 「몇 건을 돌리기로 적었는가」다. 실제 통과 수는 Docker 가
  있어야 알고, 둘이 같아야 문서의 `N/N` 이 참이다
- **인용은 안 본다.** 런북은 「옛 27/27 은 낡았다」고 **적는다** — 그건 주장이 아니라
  설명이다. `「…」` 안을 걷어내고 본다 (`#220` 이 백틱을 걷어낸 것과 같은 규율)
- **연대기는 안 본다.** `STATE.md` · `CHANGELOG` · 브리지 우편함은 **그때의 실측**을
  일부러 보존한다 — 강제하면 역사를 고쳐 쓰게 된다 (`#226` 의 `ARCHIVES` 와 같은 이유)
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTER = ROOT / "scripts" / "room_check_count.py"

sys.path.insert(0, str(ROOT / "scripts"))
from room_check_count import ROOMS, count, counts  # noqa: E402

# 「지금 이렇다」를 말하는 문서. 여기 적힌 숫자는 스크립트와 같아야 한다.
CURRENT_DOCS = (
    ROOT / "docs" / "ops" / "contest-submission-checklist.md",
    ROOT / "docs" / "ops" / "shoot-day-runbook.md",
    ROOT / "README.md",
    ROOT / "docs" / "guide" / "operate-production.md",
)

# 연대기 — **그때의 실측**을 보존한다. 강제하면 역사를 고쳐 쓰게 된다.
OUTSIDE_THE_CHECK = {
    "STATE.md": "회차 기록 — 지난 회차의 숫자를 그대로 둔다",
    "docs/history/CHANGELOG.md": "버전 이력 — 같은 이유",
    "docs/bridge/inbox-cursor.md": "우편함 아카이브 (#226 의 ARCHIVES 와 같은 이유)",
    "docs/bridge/inbox-claude.md": "같음",
    "docs/bridge/queue-batches.md": "회차 큐 기록 — 배치가 바뀌면 같이 바뀐다",
    "docs/bridge/queue-expansion.md": "같음",
}

# `clean_room` 9/9 · `prod_room` **27/27** · 통과 51 · 실패 0 …
# 「…」 안의 숫자는 **인용**이다 — 런북이 「옛 27/27 은 낡았다」고 적는 자리가 그렇다.
# `#220` 이 백틱을 걷어낸 것과 같은 규율: **말하는 문장은 위반이 아니다.**
QUOTED_OLD = re.compile(r"「[^」]*」")
SLASH = re.compile(r"(clean_room|prod_room)[^\n]{0,40}?\*{0,2}(\d+)\s*/\s*(\d+)")
TALLY = re.compile(r"(clean_room|prod_room)[^\n]{0,60}?통과\s*\*{0,2}(\d+)")


def _claims(path: Path) -> list[tuple[str, int, str]]:
    """(방, 주장한 수, 원문). 표의 `| clean_room | 통과 9 |` 도 잡는다."""
    out: list[tuple[str, int, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = QUOTED_OLD.sub(" ", raw)
        for m in SLASH.finditer(line):
            out.append((m.group(1), int(m.group(2)), line.strip()))
            if m.group(2) != m.group(3):
                out.append((m.group(1), int(m.group(3)), line.strip()))
        for m in TALLY.finditer(line):
            out.append((m.group(1), int(m.group(2)), line.strip()))
    return out


class TestCurrentDocsMatchTheScripts(unittest.TestCase):
    def test_no_stale_room_number(self) -> None:
        """**여기가 핵심이다.** 심사자가 읽는 쪽이 낡으면 그게 제품 주장이 된다."""
        expected = counts()
        bad = []
        for path in CURRENT_DOCS:
            if not path.is_file():
                continue
            for room, claimed, raw in _claims(path):
                if claimed != expected[room]:
                    rel = path.relative_to(ROOT).as_posix()
                    bad.append(f"{rel}: {room} {claimed} ≠ {expected[room]} — {raw[:70]}")
        self.assertEqual([], bad, "문서의 방 숫자가 스크립트와 다르다: " + "; ".join(bad))

    def test_the_docs_actually_say_something(self) -> None:
        """아무 문서도 숫자를 안 적으면 위 검사가 **공허하게** 통과한다."""
        found = sum(len(_claims(p)) for p in CURRENT_DOCS if p.is_file())
        self.assertGreaterEqual(found, 2, f"현재형 문서에서 방 숫자를 {found}건만 찾았다")

    def test_history_is_left_alone(self) -> None:
        """연대기를 강제하면 역사를 고쳐 쓰게 된다 — 제외 목록을 못박는다."""
        current = {p.relative_to(ROOT).as_posix() for p in CURRENT_DOCS}
        self.assertEqual(set(), current & set(OUTSIDE_THE_CHECK))
        for rel in OUTSIDE_THE_CHECK:
            with self.subTest(doc=rel):
                self.assertTrue((ROOT / rel).is_file(), f"{rel} 이 없다")


class TestTheCounterItself(unittest.TestCase):
    def test_counts_match_todays_measurement(self) -> None:
        got = counts()
        self.assertEqual({"clean_room": 9, "prod_room": 51}, got,
                         "방 검사 수가 바뀌었다 — 문서와 이 줄을 같이 고친다")

    def test_the_counter_is_not_fooled(self) -> None:
        """`python3 -c '…'` 안의 파이썬 `for` 를 세면 최상위 chk 두 건이 사라진다."""
        fake = ROOT / "tests" / "__room_counter_probe.sh"
        fake.write_text(
            'x=$(python3 -c \'\n'
            'for n in d["nodes"]:\n'
            '    print(n)\')\n'
            'chk "하나" test 1 = 1\n'
            'chk "둘" test 1 = 1\n'
            'for path in \\\n'
            '  "/a" \\\n'
            '  "/b" ; do\n'
            '  chk "루프 $path" test 1 = 1\n'
            'done\n',
            encoding="utf-8",
        )
        try:
            self.assertEqual(4, count(fake, "chk"), "파이썬 for 에 속았다")
        finally:
            fake.unlink()

    def test_the_tool_runs(self) -> None:
        """검사만 되고 도구가 죽어 있으면 재현 명령이 거짓이 된다."""
        proc = subprocess.run([sys.executable, str(COUNTER), "--json"],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("prod_room", proc.stdout)

    def test_both_rooms_are_seen(self) -> None:
        self.assertGreaterEqual(len(ROOMS), 2, sorted(ROOMS))


if __name__ == "__main__":
    unittest.main()
