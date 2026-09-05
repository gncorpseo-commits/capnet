r"""**손으로 적은 허용 목록**이 근거 없이 자라지 않는가 (큐 #43).

## 왜 있는가

이 회차가 세운 검사들은 거의 전부 **예외 목록**을 하나씩 달고 있다:

```python
ARCHIVES = ("inbox-cursor.md", "inbox-claude.md")        # #226
WITHOUT_ERREXIT = {"prod_room.sh": "큐 #44"}              # #228
OUTSIDE_CLEAN_ROOM = {…열하나…}                           # #229
ALLOWED_READERS = {"_headers"}                            # #196
```

**목록에 한 줄 더 넣으면 검사가 조용히 약해진다.** 그게 이 저장소가 계속 잡아 온
「지키는 척」의 마지막 통로다 — `#210`(바닥을 내리면 초록) · `#230`(바닥 등록부)과
같은 자리이고, 이번에는 **예외 목록** 쪽이다.

## 실측 (2026-09-05)

| 무엇 | 수 |
|---|---|
| `tests/` 의 허용 목록성 상수 | **14** |
| 그것이 든 파일 | **9** |
| 원소 합 | **40** |
| 그중 **진짜 예외 목록** | **12** |
| **어휘 집합**(예외가 아님) | **2** — `SKIP_PARTS` · `SKIP_CALLS` |
| 늘어나는 것을 막던 검사 | **0** |

`SKIP_PARTS = {"__pycache__", "node_modules"}` 와
`SKIP_CALLS = {"skip", "skipIf", …}` 는 **무엇을 봐줄지**가 아니라 **무엇을 부르는지**를
적은 어휘다. 이름에 `SKIP` 이 들어가서 걸릴 뿐이라, 예외로 세면 「예외 열넷」이라는
틀린 숫자를 적게 된다 — `#218` 이 `$node_id` 를 세어 「우회 일곱」이 될 뻔한 것과 같다.

## 무엇을 고정하나

1. **새 허용 목록은 등록된다** — 표에 없으면 운다
2. **원소가 늘면 운다** — 줄이는 것은 자유다 (예외가 줄어드는 건 개선이다)
3. **예외 목록은 근거를 옆에 둔다** — 바로 위에 주석이 있거나, 값이 이유 문자열이다
4. 사라진 목록은 표에서 빠진다 — 없는 것을 「지키고 있다」고 세지 않는다
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

# 이름이 이걸 품으면 「허용 목록일 수 있다」로 본다. 진짜인지는 아래 표가 가른다.
CANDIDATE = re.compile(r"ALLOW|EXEMPT|WITHOUT|OUTSIDE|ARCHIVE|IGNORE|SKIP|LOCKED|WAIVE|NOT_")

EXEMPT, VOCAB = "예외", "어휘"

# `파일::이름` → (종류, 오늘 원소 수, 무엇을 봐주는가)
# **늘리려면 이 표를 같이 고쳐야 한다.** 줄이는 것은 자유다.
REGISTRY: dict[str, tuple[str, int, str]] = {
    "test_agent_arch_wiring.py::EXEMPT":
        (EXEMPT, 1, "일부러 불완전한 본문을 보내는 자리"),
    "test_capability_catalog.py::LOCKED_UNTIL_ISOLATION":
        (EXEMPT, 3, "격리 전에는 라우팅을 열지 않는 능력 셋"),
    "test_capreq_binds_loopback.py::ALLOWED_READERS":
        (EXEMPT, 1, "API 키를 읽어도 되는 함수 — `_headers()` 하나"),
    "test_clean_room_covers_demos.py::OUTSIDE_CLEAN_ROOM":
        (EXEMPT, 11, "clean_room 밖의 데모 — 각자 이유를 든다 (큐 #46)"),
    "test_gh_list_is_never_truncated.py::ARCHIVES":
        (EXEMPT, 2, "우편함 — 고쳐진 결함의 「이전」을 보존한다"),
    "test_no_silent_exception_swallowing.py::ALLOWED":
        (EXEMPT, 1, "본문이 pass/continue 뿐이어도 되는 자리"),
    "test_no_silent_exception_swallowing.py::ALLOWED_SUPPRESS":
        (EXEMPT, 1, "`contextlib.suppress` 가 허용되는 자리"),
    "test_scripts_set_errexit.py::WITHOUT_ERREXIT":
        (EXEMPT, 1, "`set -e` 없이 도는 스크립트 — prod_room 하나 (큐 #44)"),
    "test_secrets_never_reach_output.py::ALLOWED_PY":
        (EXEMPT, 1, "시크릿 낱말을 출력해도 되는 파이썬 자리"),
    "test_secrets_never_reach_output.py::ALLOWED_SH":
        (EXEMPT, 1, "같은 것의 셸 쪽"),
    "test_secrets_never_reach_output.py::NOT_SECRET":
        (EXEMPT, 7, "이름에 시크릿 낱말이 들지만 값은 경로·존재 여부인 접미"),
    "test_skip_reasons.py::ALLOWED":
        (EXEMPT, 4, "건너뛰어도 되는 사유 — 허가제 (Wave W)"),
    "test_secrets_never_reach_output.py::SKIP_PARTS":
        (VOCAB, 2, "훑지 않는 디렉터리 이름 — 봐주는 목록이 아니다"),
    "test_skip_reasons.py::SKIP_CALLS":
        (VOCAB, 4, "`skip`·`skipIf` 등 호출 이름 — 봐주는 목록이 아니다"),
}


def _found() -> dict[str, tuple[int, int]]:
    """`파일::이름` → (원소 수, 줄 번호)."""
    out: dict[str, tuple[int, int]] = {}

    def walk(path: Path, body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                walk(path, node.body)
            name = value = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name):
                name, value = node.targets[0].id, node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name, value = node.target.id, node.value
            if not (name and name.isupper() and CANDIDATE.search(name)):
                continue
            if not isinstance(value, (ast.Set, ast.List, ast.Tuple, ast.Dict)):
                continue
            size = len(value.keys) if isinstance(value, ast.Dict) else len(value.elts)
            out[f"{path.name}::{name}"] = (size, node.lineno)

    for path in sorted(TESTS.glob("test_*.py")):
        walk(path, ast.parse(path.read_text(encoding="utf-8")).body)
    return out


def _has_reason(key: str) -> bool:
    """바로 위 주석 **또는** 값 안의 이유 문자열."""
    filename, _ = key.split("::", 1)
    size_line = _found()[key]
    lines = (TESTS / filename).read_text(encoding="utf-8").splitlines()
    for prev in range(size_line[1] - 2, max(size_line[1] - 6, -1), -1):
        if lines[prev].strip().startswith("#"):
            return True
        if lines[prev].strip():
            break
    src = "\n".join(lines[size_line[1] - 1: size_line[1] + 40])
    return bool(re.search(r':\s*"[^"]{4,}"|,\s*"[^"]{4,}"', src))


class TestEveryAllowlistIsAccountedFor(unittest.TestCase):
    def test_no_allowlist_is_unregistered(self) -> None:
        """새 허용 목록이 표 밖에서 생기면 아무도 모른다."""
        found = _found()
        self.assertTrue(found, "허용 목록을 하나도 못 찾았다 — 추출기가 죽었다")
        new = sorted(k for k in found if k not in REGISTRY)
        self.assertEqual([], new, f"표에 없는 허용 목록: {new}")

    def test_registry_has_no_ghosts(self) -> None:
        found = _found()
        ghosts = sorted(k for k in REGISTRY if k not in found)
        self.assertEqual([], ghosts, f"사라진 목록이 표에 남아 있다: {ghosts}")

    def test_no_allowlist_grew(self) -> None:
        """**여기가 핵심이다.** 한 줄 더 넣으면 검사가 조용히 약해진다."""
        grown = sorted(
            f"{k}: {REGISTRY[k][1]} → {size}"
            for k, (size, _) in _found().items()
            if k in REGISTRY and size > REGISTRY[k][1]
        )
        self.assertEqual([], grown,
                         "허용 목록이 늘었다. 근거와 함께 이 표도 같이 고친다: " + "; ".join(grown))

    def test_every_exemption_says_what_it_waives(self) -> None:
        blank = sorted(k for k, (kind, _, why) in REGISTRY.items()
                       if kind == EXEMPT and len(why.strip()) < 8)
        self.assertEqual([], blank, f"무엇을 봐주는지 안 적혔다: {blank}")

    def test_every_exemption_carries_its_reason_in_the_code(self) -> None:
        """표에만 적힌 근거는 그 파일을 읽는 사람에게 보이지 않는다."""
        bare = sorted(k for k, (kind, _, _) in REGISTRY.items()
                      if kind == EXEMPT and k in _found() and not _has_reason(k))
        self.assertEqual([], bare, f"코드 옆에 근거가 없다: {bare}")


class TestVocabularyIsNotCountedAsAnExemption(unittest.TestCase):
    """어휘를 예외로 세면 **틀린 숫자**를 적게 된다 (`#218` 함정)."""

    def test_the_two_vocab_sets_are_marked(self) -> None:
        vocab = sorted(k for k, (kind, _, _) in REGISTRY.items() if kind == VOCAB)
        self.assertEqual(
            ["test_secrets_never_reach_output.py::SKIP_PARTS",
             "test_skip_reasons.py::SKIP_CALLS"], vocab)

    def test_exemption_count_is_twelve(self) -> None:
        n = sum(1 for kind, _, _ in REGISTRY.values() if kind == EXEMPT)
        self.assertEqual(12, n, "예외 목록 수가 바뀌었다 — 표와 머리말을 같이 고친다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_allowlists_are_seen(self) -> None:
        self.assertGreaterEqual(len(_found()), 12, sorted(_found()))

    def test_detector_discriminates(self) -> None:
        """상수를 아무거나 잡거나 하나도 못 잡으면 위 전부가 쓸모없다."""
        found = _found()
        self.assertIn("test_gh_list_is_never_truncated.py::ARCHIVES", found)
        self.assertNotIn("test_core_sql_columns_exist.py::KEYWORDS", found)
        self.assertNotIn("test_room_tally.py::ROOMS", found)


if __name__ == "__main__":
    unittest.main()
