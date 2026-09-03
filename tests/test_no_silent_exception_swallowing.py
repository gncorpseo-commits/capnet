"""**조용히 삼키는 자리**가 근거 없이 늘지 않는가 (큐 #20).

## 왜 있는가

이 회차들이 고쳐 온 결함은 한 모양이다 — **아무것도 못 봤는데 초록으로 끝난다**
(#180 누출 검사 0건 · #181 통합 러너 0개 · #187 방 판정 · #205 공개 프로브의 `000`).
`except Exception: pass` 는 그 모양을 **한 줄로** 만든다.

전수했다 (2026-09-03). **오늘 새는 곳은 없다.**

| 무엇 | 수 |
|---|---|
| 광범위 `except` (`Exception`·`BaseException`) | **25** |
| **bare `except:`** | **0** |
| 본문이 `pass`/`continue` **뿐** | **1** — `compare_ab.py` 의 stdout 인코딩 |
| `contextlib.suppress(Exception)` | **1** — Node 실패 보고 |
| 삼키고 **성공값**을 돌려주는 자리 | **0** — `db.py` 하나는 경고를 남기고 폴백한다 |

나머지 스물셋은 전부 **재던지거나 · 로그하거나 · 실패 상태를 기록한다**
(`checks[...] = False` · `r.error = …` · `ok=False` · `_note_core_error`).

## 무엇을 고정하나

1. **bare `except:` 는 0** — 어떤 근거로도 허용하지 않는다. `KeyboardInterrupt` 까지 먹는다
2. 본문이 `pass`/`continue` 뿐인 광범위 `except` 는 아래 `ALLOWED` 에 **근거와 함께** 적는다
3. `contextlib.suppress(Exception)` 도 같은 규율 (`ALLOWED_SUPPRESS`)
4. **유령이 없다** — 사라진 자리가 목록에 남으면 다음 사람이 「이건 허용된 거였지」로 넘어간다

`test_every_route_declares_its_auth` 의 `PUBLIC` 과 같은 방식이다 —
**막지 않고, 근거를 적게 만든다.**

## 무엇을 고정하지 **않나**

광범위 `except` 자체. 그건 여기서 정할 일이 아니고(경계면에서는 필요하다),
개수를 못박으면 사람이 숫자만 고친다.

## 스캐너가 `return 1` 을 **성공**으로 셌다 (적어 둔다)

「삼키고 성공으로 끝나는 자리」를 찾으려고 `x.value in (True, 0)` 으로 걸렀더니
`main()` 의 **실패 종료 코드** `return 1` 이 잡혔다 — 파이썬에서 `1 == True` 이기 때문이다.
**뜻이 정반대인 것을 같은 것으로 셌다.** `is True` 로 고치고 나서야 실제 후보가
`db.py` 하나로 좁혀졌고, 그마저 경고를 남기는 폴백이었다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_ROOTS = (ROOT / "apps", ROOT / "capreq" / "src", ROOT / "scripts")

BROAD = frozenset({"Exception", "BaseException"})

# 본문이 `pass`/`continue` 뿐인 자리 — **왜 그래도 되는지**를 적는다.
# 키는 `(파일, 감싸는 함수)` 다. 줄 번호로 잡으면 위쪽을 한 줄만 고쳐도 깨진다.
ALLOWED: dict[tuple[str, str], str] = {
    ("scripts/compare_ab.py", "main"): (
        "stdout 을 utf-8 로 다시 여는 시도. 실패해도 출력이 조금 깨질 뿐이고 "
        "판정에는 영향이 없다 — 여기서 죽으면 비교 자체를 못 돌린다"
    ),
}

# `contextlib.suppress(Exception)` — 같은 규율.
ALLOWED_SUPPRESS: dict[tuple[str, str], str] = {
    ("apps/node/app/main.py", "_poll_loop"): (
        "Core 로의 **실패 보고**를 감싼다. 보고가 죽어서 실행 루프까지 죽으면 "
        "실패가 lease 만료로만 드러난다 — 그게 0015 가 고친 사고다"
    ),
}


def _py_files() -> list[Path]:
    out: list[Path] = []
    for r in CODE_ROOTS:
        out.extend(sorted(p for p in r.rglob("*.py") if "__pycache__" not in p.parts))
    return out


def _enclosing(tree: ast.Module) -> dict[int, str]:
    """노드 id → 감싸는 함수 이름 (없으면 `<module>`)."""
    owner: dict[int, str] = {}

    def walk(node: ast.AST, name: str) -> None:
        for child in ast.iter_child_nodes(node):
            here = child.name if isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef)) else name
            owner[id(child)] = here
            walk(child, here)

    walk(tree, "<module>")
    return owner


def _scan() -> tuple[list[str], list[tuple[str, str, int]], list[tuple[str, str, int]], int]:
    """(bare, pass뿐, suppress, 광범위 총수)."""
    bare: list[str] = []
    silent: list[tuple[str, str, int]] = []
    suppressed: list[tuple[str, str, int]] = []
    broad_total = 0
    for path in _py_files():
        rel = str(path.relative_to(ROOT))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        owner = _enclosing(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Try):
                for h in n.handlers:
                    if h.type is None:
                        bare.append(f"{rel}:{h.lineno}")
                        broad_total += 1
                        continue
                    if not (isinstance(h.type, ast.Name) and h.type.id in BROAD):
                        continue
                    broad_total += 1
                    if len(h.body) == 1 and isinstance(h.body[0], (ast.Pass, ast.Continue)):
                        silent.append((rel, owner.get(id(h), "<module>"), h.lineno))
            if isinstance(n, ast.withitem) and isinstance(n.context_expr, ast.Call):
                fn = n.context_expr.func
                nm = fn.attr if isinstance(fn, ast.Attribute) else (
                    fn.id if isinstance(fn, ast.Name) else "")
                if nm != "suppress":
                    continue
                args = [a.id for a in n.context_expr.args if isinstance(a, ast.Name)]
                if any(a in BROAD for a in args):
                    suppressed.append(
                        (rel, owner.get(id(n.context_expr), "<module>"),
                         n.context_expr.lineno))
    return bare, silent, suppressed, broad_total


class TestNoBareExcept(unittest.TestCase):
    def test_zero_bare_except(self) -> None:
        """`except:` 는 `KeyboardInterrupt` 까지 먹는다. 근거로도 허용하지 않는다."""
        bare, _s, _p, _t = _scan()
        self.assertEqual([], bare, f"bare except 가 있다: {bare}")


class TestSilentSwallowsAreDeclared(unittest.TestCase):
    def setUp(self) -> None:
        _b, self.silent, self.suppressed, self.total = _scan()

    def test_every_silent_handler_has_a_reason(self) -> None:
        undeclared = sorted(
            f"{rel}:{line} ({fn})" for rel, fn, line in self.silent
            if (rel, fn) not in ALLOWED
        )
        self.assertEqual(
            undeclared, [],
            "본문이 pass/continue 뿐인 except — 실패를 기록하거나 "
            f"ALLOWED 에 근거와 함께 적는다: {undeclared}",
        )

    def test_every_suppress_has_a_reason(self) -> None:
        undeclared = sorted(
            f"{rel}:{line} ({fn})" for rel, fn, line in self.suppressed
            if (rel, fn) not in ALLOWED_SUPPRESS
        )
        self.assertEqual(
            undeclared, [], f"근거 없는 suppress(Exception): {undeclared}"
        )

    def test_no_ghost_entries(self) -> None:
        """사라진 자리가 남으면 다음 사람이 「이건 허용된 거였지」로 넘어간다."""
        real = {(rel, fn) for rel, fn, _l in self.silent}
        real_sup = {(rel, fn) for rel, fn, _l in self.suppressed}
        ghosts = sorted(f"{r}::{f}" for (r, f) in ALLOWED if (r, f) not in real)
        ghosts += sorted(f"{r}::{f}" for (r, f) in ALLOWED_SUPPRESS if (r, f) not in real_sup)
        self.assertEqual([], ghosts, f"목록에만 있는 자리: {ghosts}")

    def test_reasons_are_not_empty(self) -> None:
        thin = sorted(
            f"{r}::{f}" for d in (ALLOWED, ALLOWED_SUPPRESS)
            for (r, f), why in d.items() if len(why.strip()) < 20
        )
        self.assertEqual([], thin, f"근거가 너무 짧다: {thin}")


class TestProbeActuallyScans(unittest.TestCase):
    """범위가 비면 위 검사 **전부**가 공허하게 통과한다."""

    def test_found_broad_handlers(self) -> None:
        _b, _s, _p, total = _scan()
        self.assertGreater(total, 10, f"광범위 except 를 {total}개밖에 못 찾았다")

    def test_enclosing_function_is_resolved(self) -> None:
        """함수 이름을 못 풀면 전부 `<module>` 로 뭉쳐 목록이 무의미해진다."""
        _b, silent, suppressed, _t = _scan()
        names = {fn for _r, fn, _l in silent + suppressed}
        self.assertTrue(names, "훑은 자리가 없다 — 목록이 비었으면 이 검사도 헛돈다")
        self.assertNotEqual({"<module>"}, names, "감싸는 함수를 하나도 못 풀었다")


if __name__ == "__main__":
    unittest.main()
