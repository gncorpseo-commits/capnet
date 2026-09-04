r"""세션 런북의 `gh … list` 가 **조용히 잘리지 않는가** (큐 #36).

## 왜 있는가

`gh pr list` 의 **기본 상한은 30** 이다. 넘으면 오류가 아니라 **조용히 잘린다.**

이 저장소는 그것에 **이미 한 번 당했다** — `docs/bridge/inbox-cursor.md:7084` 에
그 시절의 명령이 남아 있다:

```bash
for b in $(gh pr list -R … --json headRefName -q '.[].headRefName'); do …
```

열린 PR 이 31 이 된 순간부터 **한 개가 조용히 빠진 채** 「전부 충돌 0」이라고
적고 있었다 (`inbox-cursor.md:7087`·`7216`). 9회차에는 열린 PR 이 **열여덟**까지
갔다 — 30 은 멀지 않다.

고친 뒤 **못박지는 않았다.** 세 런북이 「`--limit 100` 필수」라고 글로만 적고 있고,
그 문장이 지워지거나 복붙 블록에서 옵션이 빠져도 **아무 검사도 울지 않는다.**
`#194` 가 연 자리와 같은 모양이다 — 고치고 못박지 않은 과거 버그.

## 실측 (2026-09-04)

| 무엇 | 수 |
|---|---|
| 저장소 전체 `gh … list` | **22** |
| 그중 **복붙 런북 코드블록** 안 | **4** |
| 그 넷 중 `--limit` 없는 것 | **0** |
| 그 0 을 **지키던** 검사 | **0** |

## 무엇을 세지 않나 — **말하는 문장은 위반이 아니다**

처음 훑기는 **여덟 건**을 잡았다. 전부 오탐이었다:

```text
- `gh pr list` without `--limit 100`          금지 규칙을 적은 줄
**`gh pr list` 의 기본 상한은 30 이다.**       왜 붙이는지 설명하는 줄
36. … `--limit 100` 없이 쓰는가 — 강제         큐 항목 자체
for b in $(gh pr list -R … --json …)          과거 결함의 인용 (고쳐진 것)
```

**「명령을 말한다」와 「명령을 돌린다」는 다르다.** 그대로 뒀으면
**「위반 여덟 건」**이라고 적을 뻔했다 — `#218` 이 `$node_id`·포트 문자열을
세어 「우회 일곱 건」이 될 뻔한 것과 같은 함정이다.

그래서 **인라인 코드(백틱)를 걷어낸 뒤** 본다. 위 넷은 전부 `` `gh pr list` `` 처럼
백틱 안에 있고, 실제로 돌아가는 명령은 코드블록 안에 **맨몸으로** 있다.

### 첫 판은 펜스를 셌고, 그게 틀렸다 (적어 둔다)

처음에는 「펜스 친 블록 안쪽만」으로 짰다. **`handoff-long-mode-claude.md` 에서 뒤집혔다** —
그 파일은 **전체가 하나의 ` ```markdown ` 블록**이고 그 안에 ` ```bash ` 가 또 있다.
여는/닫는 짝만 세면 **안과 밖이 반대로** 뒤집힌다:

| 줄 | 무엇 | 펜스 파서가 본 것 |
|---|---|---|
| 29 · 40 · 162 | 산문·표 | **안쪽**(=명령) ❌ |
| 48 | 진짜 복붙 명령 | **바깥**(=산문) ❌ |

그래서 `--limit 30` 으로 낮춘 뮤테이션이 **그대로 통과했다.** 산문 셋이 우연히
`--limit 100` 이라는 글자를 품고 있어 초록이었던 것 — **검사가 지키는 척만 하고 있었다.**
백틱을 걷어내는 쪽은 문서 구조에 기대지 않는다.

## 범위에서 뺀 것 — `inbox-cursor.md`

**우편함 아카이브다.** 8천 줄이 지나간 회차의 기록이고, 위 인용처럼 **고쳐진
결함의 「이전」**을 일부러 보존한다. 여기를 강제하면 **역사를 고쳐 쓰게 된다.**

보는 것은 **세션이 실제로 복붙하는 세 런북**과 **돌아가는 스크립트·CI** 다.

## 무엇을 고정하나

1. 런북 본문(백틱 제외)·`scripts/*.sh`·워크플로의 `gh … list` 에 **`--limit` 이 있다**
2. 그 값이 **100 이상**이다 — 세 런북이 이미 그렇게 적었다 (새 정책 숫자가 아니다)
3. 세는 대상이 **0 이 아니다** — 비면 위 둘이 공허하게 통과한다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 세션이 **복붙하는** 런북. 아카이브(`inbox-cursor.md`)는 위 머리말대로 뺀다.
RUNBOOKS = (
    ROOT / "docs" / "bridge" / "autonomous-mode.md",
    ROOT / "docs" / "bridge" / "handoff-long-mode-claude.md",
    ROOT / "docs" / "bridge" / "queue-expansion.md",
)

# `gh pr list` · `gh issue list` · `gh run list` · `gh release list`
GH_LIST = re.compile(r"gh\s+(?:pr|issue|run|release)\s+list\b([^\n|;&]*)")
LIMIT = re.compile(r"--limit[=\s]+(\d+)")

# 세 런북이 이미 적은 값. 여기서 새로 정하는 정책이 아니다.
MIN_LIMIT = 100


# 인라인 코드 — `…` 와 ``…`` . 산문은 명령을 **백틱에 넣어** 말한다.
INLINE_CODE = re.compile(r"`{1,2}[^`]*`{1,2}")


def _runnable_lines(path: Path) -> list[tuple[int, str]]:
    """명령으로 **돌아갈 수 있는** 줄. 인라인 코드는 지워서 본다.

    펜스 짝은 세지 않는다 — `handoff-long-mode-claude.md` 는 전체가 하나의
    ` ```markdown ` 블록이고 그 안에 ` ```bash ` 가 또 있어 짝이 뒤집힌다(머리말 참조).
    """
    out: list[tuple[int, str]] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        if path.suffix in (".sh", ".yml", ".yaml") and line.startswith("#"):
            continue
        stripped = INLINE_CODE.sub(" ", raw)
        if stripped.strip():
            out.append((i, stripped))
    return out


def _sites() -> list[tuple[str, int, str]]:
    """`gh … list` 가 **돌아가는** 자리 전부."""
    found: list[tuple[str, int, str]] = []

    def scan(path: Path, lines: list[tuple[int, str]]) -> None:
        rel = path.relative_to(ROOT).as_posix()
        for lineno, line in lines:
            if GH_LIST.search(line):
                found.append((rel, lineno, line.strip()))

    for path in RUNBOOKS:
        if path.is_file():
            scan(path, _runnable_lines(path))
    scripts = ROOT / "scripts"
    if scripts.is_dir():
        for path in sorted(scripts.glob("*.sh")):
            scan(path, _runnable_lines(path))
    workflows = ROOT / ".github" / "workflows"
    if workflows.is_dir():
        for path in sorted(p for p in workflows.iterdir() if p.suffix in (".yml", ".yaml")):
            scan(path, _runnable_lines(path))
    return found


class TestGhListAlwaysAsksForEnough(unittest.TestCase):
    def test_every_call_passes_a_limit(self) -> None:
        """상한을 안 주면 30 에서 **조용히** 잘린다 — 오류가 아니라 침묵이다."""
        bad = [
            f"{rel}:{lineno} {text[:70]}"
            for rel, lineno, text in _sites()
            for m in [GH_LIST.search(text)]
            if m and not LIMIT.search(m.group(1))
        ]
        self.assertEqual([], bad, "`gh … list` 에 `--limit` 이 없다: " + "; ".join(bad))

    def test_every_limit_is_big_enough(self) -> None:
        bad: list[str] = []
        for rel, lineno, text in _sites():
            m = GH_LIST.search(text)
            if not m:
                continue
            lim = LIMIT.search(m.group(1))
            if lim and int(lim.group(1)) < MIN_LIMIT:
                bad.append(f"{rel}:{lineno} --limit {lim.group(1)}")
        self.assertEqual([], bad, f"`--limit` 이 {MIN_LIMIT} 보다 작다: {bad}")


class TestProbeActuallyScans(unittest.TestCase):
    """범위가 비면 위 둘이 **공허하게** 통과한다."""

    def test_runbooks_exist(self) -> None:
        missing = [p.name for p in RUNBOOKS if not p.is_file()]
        self.assertEqual([], missing, f"런북을 못 찾았다: {missing}")

    def test_runbook_lines_are_read(self) -> None:
        total = sum(len(_runnable_lines(p)) for p in RUNBOOKS if p.is_file())
        self.assertGreater(total, 200, f"런북에서 {total}줄밖에 못 읽었다")

    def test_at_least_one_call_is_seen(self) -> None:
        """실제로 세고 있다는 증거. 0 이면 위 검사는 아무것도 안 지킨다."""
        self.assertGreaterEqual(len(_sites()), 3, _sites())

    def test_detector_discriminates(self) -> None:
        """산문을 잡거나 명령을 놓치면 이 검사는 쓸모가 없다."""
        self.assertTrue(GH_LIST.search("gh pr list --state open --limit 100"))
        self.assertTrue(GH_LIST.search("for b in $(gh pr list --json headRefName)"))
        self.assertFalse(GH_LIST.search("gh pr view 123"))
        # **산문은 백틱에 들어 있다.** 걷어내면 남지 않는다 — 이게 오탐 여덟을 지운 한 줄이다.
        self.assertFalse(GH_LIST.search(INLINE_CODE.sub(" ", "- `gh pr list` without `--limit 100`")))
        self.assertFalse(GH_LIST.search(INLINE_CODE.sub(" ", "| `gh pr list --state open --limit 100` |")))
        self.assertTrue(GH_LIST.search(INLINE_CODE.sub(" ", "gh pr list --state open --limit 100")))
        # `--limit` 유무를 **옵션 부분에서만** 본다.
        m = GH_LIST.search("gh pr list --state open --limit 100")
        assert m is not None
        self.assertTrue(LIMIT.search(m.group(1)))
        m = GH_LIST.search("gh pr list --json headRefName")
        assert m is not None
        self.assertFalse(LIMIT.search(m.group(1)))


if __name__ == "__main__":
    unittest.main()
