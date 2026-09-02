"""머지 충돌 마커가 **문서에 남은 채로 초록**이 되지 않는가.

## 왜 있는가

**이번 세션에 실측했다 (2026-09-02).** 머지 프로브가 `CHANGELOG.md` 에서 충돌했고,
그 **마커가 그대로 남은 트리**에서 전체 검증을 돌렸더니:

```text
Ran 518 tests · OK (skipped=7)
28/28 통과
```

**아무것도 안 걸렸다.** `<<<<<<< HEAD` · `=======` · `>>>>>>> origin/…` 세 줄이
파일 3·73·184 행에 그대로 있는데도.

`test_changelog_integrity` 는 **머지 사고**를 보라고 만든 검사인데(2026-09-01 에
두 번째 `# Changelog` 헤더와 159줄 중복이 생겼다), 보는 것은 **헤더 개수·제목 중복**이다.
**잘못 푼 머지의 다른 얼굴 — 안 푼 머지** 는 그 그물을 빠져나간다.

## 왜 문서만 보나

**코드는 이미 시끄럽다.** 파이썬에 마커가 남으면 `SyntaxError` 로 임포트가 죽고,
셸은 `bash -n` 이 잡는다 (`test_room_tally` 가 실제로 그렇게 본다).
**조용한 것은 마크다운뿐이다** — 그래서 머지가 자주 충돌하는 문서만 본다:

| 파일 | 왜 |
|---|---|
| `docs/history/CHANGELOG.md` | 코드 PR 마다 선두를 건드린다 — 이번 회차에만 두 번 충돌 |
| `STATE.md` | 세션마다 갱신된다 |
| `docs/bridge/inbox-*.md` | 블록을 **꼬리에** 덧붙인다 |

**리포 전체를 훑지 않는다.** 「X 를 쓰지 않는다」를 텍스트로 검사했다가
**X 를 설명한 문단이 걸린** 사고가 이 저장소에서 다섯 번 났다 (`tests/_srcguard.py`).
이 파일 자신도 마커를 설명하므로 **자기 자신을 대상에서 뺀다.**

## 무엇을 보나

`git` 이 실제로 찍는 모양만 본다 — **줄 맨 앞의 7글자 마커.**

- `<<<<<<< ` · `>>>>>>> ` (뒤에 이름이 붙는다)
- `||||||| ` (diff3 방식의 공통 조상)
- `=======` **단독 줄**은 마크다운 setext 제목 밑줄일 수 있어 **혼자서는 안 잡는다** —
  여는 마커가 같은 파일에 있을 때만 센다

## 무엇을 안 보나

**충돌을 「잘 풀었는지」는 못 본다.** 그건 사람이 읽는다. 여기서 보는 것은
**안 푼 것을 푼 것처럼 넘기지 않는가** 하나다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

# 머지가 자주 충돌하는 문서. 코드는 파서·`bash -n` 이 이미 잡는다.
WATCHED: tuple[Path, ...] = (
    ROOT / "docs" / "history" / "CHANGELOG.md",
    ROOT / "STATE.md",
    *sorted((ROOT / "docs" / "bridge").glob("inbox-*.md")),
)

OPEN_MARK = re.compile(r"^<<<<<<< ", re.M)
CLOSE_MARK = re.compile(r"^>>>>>>> ", re.M)
BASE_MARK = re.compile(r"^\|\|\|\|\|\|\| ", re.M)
SPLIT_MARK = re.compile(r"^=======$", re.M)


def markers(text: str) -> list[str]:
    """이 텍스트에 남은 충돌 마커. `=======` 는 여는 마커가 있을 때만 센다."""
    found = [m.group(0).rstrip() for m in OPEN_MARK.finditer(text)]
    found += [m.group(0).rstrip() for m in CLOSE_MARK.finditer(text)]
    found += [m.group(0).rstrip() for m in BASE_MARK.finditer(text)]
    if found:
        found += [m.group(0) for m in SPLIT_MARK.finditer(text)]
    return found


class TestWatchedDocsAreResolved(unittest.TestCase):
    def test_no_markers_left(self) -> None:
        for path in WATCHED:
            with self.subTest(doc=path.name):
                left = markers(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    left, [],
                    f"{path.relative_to(ROOT)} 에 머지 충돌 마커가 남아 있다: {left[:3]}",
                )

    def test_watch_list_points_at_real_files(self) -> None:
        missing = [str(p.relative_to(ROOT)) for p in WATCHED if not p.is_file()]
        self.assertEqual(missing, [], f"보기로 한 문서가 없다: {missing}")

    def test_probe_actually_watches_something(self) -> None:
        """0개를 훑으며 통과하는 상태를 막는다. **개수는 못박지 않는다.**"""
        self.assertGreater(len(WATCHED), 2, [p.name for p in WATCHED])
        self.assertNotIn(SELF, WATCHED, "이 파일은 마커를 설명하므로 대상이 아니다")


class TestDetectorActuallyDetects(unittest.TestCase):
    """검사가 **실제로 잡는지**를 가짜 텍스트로 확인한다 — 파일을 더럽히지 않는다."""

    CONFLICTED = (
        "# Changelog\n"
        "<<<<<<< HEAD\n"
        "## 이쪽\n"
        "=======\n"
        "## 저쪽\n"
        ">>>>>>> origin/other\n"
    )

    def test_detects_a_real_conflict(self) -> None:
        found = markers(self.CONFLICTED)
        self.assertIn("<<<<<<<", found)
        self.assertIn(">>>>>>>", found)
        self.assertIn("=======", found)

    def test_detects_diff3_base_marker(self) -> None:
        text = "<<<<<<< HEAD\na\n||||||| base\nb\n=======\nc\n>>>>>>> other\n"
        self.assertIn("|||||||", markers(text))

    def test_setext_underline_alone_is_not_a_conflict(self) -> None:
        """`=======` 만 있는 마크다운 제목 밑줄을 오탐하면 문서를 못 쓴다."""
        self.assertEqual(markers("제목\n=======\n본문\n"), [])

    def test_clean_text_is_clean(self) -> None:
        self.assertEqual(markers("# Changelog\n\n## 항목\n내용\n"), [])


if __name__ == "__main__":
    unittest.main()
