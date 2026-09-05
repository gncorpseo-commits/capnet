#!/usr/bin/env python3
"""방 스크립트가 **몇 건을 검사하는지** 소스에서 센다 (큐 #48).

`clean_room.sh` · `prod_room.sh` 의 통과 수는 문서 여러 곳에 손으로 적혀 있다.
스크립트가 자라면 그 숫자가 낡는데, **아무도 세고 있지 않았다** — 실제로
`prod_room` 이 `27/27` 과 `51/51` 로 **갈려** 있었다 (`#205` 가 라우트를 5 → 24 로 늘린 뒤).

이 도구는 Docker 없이 **정적으로** 센다:

- 최상위 `chk "…"` · `step "…"` 는 **한 건**
- `for path in … ; do … chk … done` 은 **경로 수 × 루프 안 chk 수**

    python3 scripts/room_check_count.py            # 방마다 한 줄
    python3 scripts/room_check_count.py --json     # {"clean_room": 9, "prod_room": 51}

**실행 결과가 아니다.** 「몇 건을 돌리기로 적었는가」이고, 실제 통과 수는 Docker 가
있어야 안다. 둘이 같아야 문서의 `N/N` 이 참이다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOMS = {
    "clean_room": (ROOT / "scripts" / "clean_room.sh", "step"),
    "prod_room": (ROOT / "scripts" / "prod_room.sh", "chk"),
}

# **셸** for 만 본다. `python3 -c '…'` 안의 `for n in d["nodes"]:` 도 열 0 에서
# 시작해 걸린다 — 그걸 세면 그 뒤 최상위 chk 두 건이 통째로 사라진다 (실제로 겪었다).
FOR_HEAD = re.compile(r"^for\s+\w+\s+in\b.*(?:\\|;\s*do)\s*$")
QUOTED = re.compile(r'^\s*"')


def count(path: Path, verb: str) -> int:
    """그 스크립트가 돌리기로 적은 검사 수."""
    lines = path.read_text(encoding="utf-8").splitlines()
    call = re.compile(rf'^\s*{re.escape(verb)}\s+"')
    top = re.compile(rf'^{re.escape(verb)}\s+"')
    total, i = 0, 0
    while i < len(lines):
        line = lines[i]
        # `for i in $(seq 1 60); do …; done` 같은 한 줄짜리는 목록 루프가 아니다.
        if FOR_HEAD.match(line):
            j = i
            while j < len(lines) and "; do" not in lines[j]:
                j += 1
            if j >= len(lines):
                i += 1
                continue
            paths = sum(1 for raw in lines[i + 1:j] if QUOTED.match(raw))
            if re.match(r'^\s*"[^"]*"\s*;\s*do', lines[j]):
                paths += 1
            inner, k = 0, j + 1
            while k < len(lines) and lines[k].strip() != "done":
                if call.match(lines[k]):
                    inner += 1
                k += 1
            total += paths * inner
            i = k + 1
            continue
        if top.match(line):
            total += 1
        i += 1
    return total


def counts() -> dict[str, int]:
    return {name: count(path, verb) for name, (path, verb) in ROOMS.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    got = counts()
    if a.json:
        print(json.dumps(got, ensure_ascii=False, sort_keys=True))
        return 0
    for name, n in sorted(got.items()):
        print(f"{name:12s} {n}건 ({ROOMS[name][0].relative_to(ROOT)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
