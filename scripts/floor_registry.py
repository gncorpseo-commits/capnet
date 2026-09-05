#!/usr/bin/env python3
"""검사의 **바닥**(`assertGreater[Equal](…, N)`)을 모아 등록부를 만든다 (큐 #50).

바닥은 「대상이 비면 조용히 통과」를 막는 장치다 (`#210` 계열). 그런데 **바닥 자체를
내리면** 아무도 울지 않는다 — `REFERENCE_FLOOR = 355` 를 `0` 으로 바꾸면 전부 초록이다.

이 도구는 바닥을 전부 뽑아 `tests/floors.json` 에 적는다.
`tests/test_floors_do_not_sag.py` 가 그 값보다 **낮아졌는지** 본다.
올리는 것은 자유다 — 실측이 늘면 바닥도 따라 올라간다.

    python3 scripts/floor_registry.py --write    # 등록부 갱신 (올릴 때만)
    python3 scripts/floor_registry.py --print    # 지금 값 보기
    python3 scripts/floor_registry.py --check    # 등록부와 대조 (검사와 같은 판정)
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
REGISTRY = TESTS / "floors.json"

FLOOR_CALLS = ("assertGreaterEqual", "assertGreater")


# 이름 붙은 바닥 상수 — `REFERENCE_FLOOR = 355` 처럼 단언에서 리터럴로 안 보이는 것.
# 이것을 안 세면 `self.REFERENCE_FLOOR` 를 쓰는 검사는 **한 줄로 0 이 된다.**
FLOOR_NAME = re.compile(r"(?:^|_)(?:FLOOR|MIN|MINIMUM)(?:$|_)")


def floors(tests_dir: Path = TESTS) -> dict[str, int]:
    """`파일::함수#순번` (단언의 리터럴) · `파일::이름` (바닥 상수) → 값.

    줄 번호로 키를 잡으면 **한 줄만 넣어도 전부 어긋난다.** 함수 안 순번은
    그 함수를 고칠 때만 바뀐다.
    """
    out: dict[str, int] = {}
    for path in sorted(tests_dir.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for name, value in _floor_constants(tree):
            out[f"{path.name}::{name}"] = value
        for func in _functions(tree):
            n = 0
            for node in ast.walk(func):
                if not (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr in FLOOR_CALLS
                        and len(node.args) >= 2):
                    continue
                arg = node.args[1]
                if isinstance(arg, ast.Constant) and type(arg.value) is int:
                    out[f"{path.name}::{func.name}#{n}"] = arg.value
                    n += 1
    return out


def _functions(tree: ast.AST) -> list[ast.FunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]


def _floor_constants(tree: ast.AST) -> list[tuple[str, int]]:
    """모듈·클래스 자리의 `…FLOOR… = <정수>`. 함수 안 지역 변수는 세지 않는다."""
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if not (isinstance(target, ast.Name) and target.id.isupper()):
            continue
        if not FLOOR_NAME.search(target.id):
            continue
        if isinstance(value, ast.Constant) and type(value.value) is int:
            out.append((target.id, value.value))
    return out


def load() -> dict[str, int]:
    if not REGISTRY.is_file():
        return {}
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def check() -> list[str]:
    """등록부와 어긋난 것. 빈 목록이면 통과."""
    now, was = floors(), load()
    # 추출기가 0건이면 「어긋남 0건」이 아니라 **추출기가 죽은 것**이다 (큐 #78).
    if not now:
        return ["바닥을 하나도 못 찾았다 — 추출기가 죽었다 (등록부와 대조하지 않는다)"]
    bad = [f"{k}: 등록 안 됨 (지금 {v})" for k, v in now.items() if k not in was]
    bad += [f"{k}: 사라진 바닥이 등록부에 남아 있다 (등록 {v})"
            for k, v in was.items() if k not in now]
    bad += [f"{k}: 바닥이 내려갔다 {was[k]} → {v}"
            for k, v in now.items() if k in was and v < was[k]]
    return sorted(bad)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="등록부를 지금 값으로 갱신")
    g.add_argument("--print", dest="show", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if a.show:
        print(json.dumps(floors(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if a.write:
        # 0건을 쓰면 등록부가 통째로 비고, 그 뒤 `--check` 는 영원히 초록이다.
        if not floors():
            print("바닥을 하나도 못 찾았다 — 등록부를 비우지 않는다", file=sys.stderr)
            return 1
        REGISTRY.write_text(
            json.dumps(floors(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"{REGISTRY.relative_to(ROOT)} — 바닥 {len(floors())}건")
        return 0

    bad = check()
    for line in bad:
        print(line, file=sys.stderr)
    print(f"바닥 {len(floors())}건 · 어긋남 {len(bad)}건")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
