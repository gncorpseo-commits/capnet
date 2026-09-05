"""제출 체크리스트가 실물과 맞는가 (출품 트랙 · 일정·제출 정본).

## 왜 있는가

`contest-submission-checklist.md` 는 **일정·제출 정본**이다. 8/25–26 에 패킹하는 사람이
이 표를 보고 움직인다. 그런데 두 종류로 어긋나 있었다.

1. **모순** — S4 가 「넣지 않는 것: … 학습 가중치 바이너리」인데 제품은 가중치를
   **넣어야** 돌아간다(`check_submission.REQUIRED_WEIGHTS` 가 요구). 패킹하는 사람이
   지워야 하나 망설인다
2. **낡은 수치** — 「자체 scratch 가중치 **2종**」은 능력이 `image.classify` 하나였을 때
   값이다. 지금은 **5종**이 필요하다

**한 번은 더 나쁜 방식으로 새어 나갔다.** 이 문서를 고친 편집이 커밋 전에
`git reset --hard`(다른 작업의 변이 검사)로 사라졌는데, **어느 검사도 잡지 못했다** —
문서를 보는 검사가 없었기 때문이다. 그래서 만든다.

## 무엇을 고정하나

- 가중치 개수가 `REQUIRED_WEIGHTS` **실물과 같은가**
- S4-1(반드시 넣는 것)이 **있는가** — S4 만 있으면 「가중치를 빼라」로 읽힌다
- D-2 재현 기록이 **현재 세대**를 가리키는가
- `check_release.sh` 가 **실재**하고 체크리스트가 그것을 부르는가
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402
CHECKLIST = ROOT / "docs" / "ops" / "contest-submission-checklist.md"
SUBMISSION = ROOT / "scripts" / "check_submission.py"


def _required_weights() -> list[str]:
    """`check_submission.REQUIRED_WEIGHTS` 를 소스에서 읽는다 (import 하면 부작용이 있다)."""
    src = SUBMISSION.read_text(encoding="utf-8")
    block = src.split("REQUIRED_WEIGHTS = [", 1)[1].split("]", 1)[0]
    return re.findall(r'"([^"]+\.safetensors)"', block)


class TestWeightPolicyIsConsistent(unittest.TestCase):
    def setUp(self) -> None:
        self.text = CHECKLIST.read_text(encoding="utf-8")
        self.required = _required_weights()

    def test_required_weights_are_actually_committed(self) -> None:
        """정본이 요구하는 가중치가 **git 에 있는가.** 없으면 zip 에도 없다."""
        tracked = subprocess.run(
            ["git", "ls-files", "apps/node/weights"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
        for w in self.required:
            self.assertIn(w, tracked, f"{w} 이 커밋돼 있지 않다")

    def test_checklist_count_matches_reality(self) -> None:
        """「가중치 N종」이 실물 개수와 같아야 한다.

        「2종」으로 멈춰 있었다 — 능력이 하나였을 때의 값이다.
        """
        n = len(self.required)
        self.assertIn(f"가중치 **{n}종**", self.text,
                      f"체크리스트가 가중치 {n}종이라고 말하지 않는다")
        self.assertNotIn("가중치 2종", self.text, "낡은 「2종」이 남아 있다")

    def test_must_include_rule_exists(self) -> None:
        """S4 만 있으면 「가중치를 빼라」로 읽힌다 — S4-1 이 짝이다."""
        self.assertIn("| S4-1 |", self.text)
        self.assertIn("반드시 넣는 것", self.text)

    def test_exclusion_says_experiment_weights(self) -> None:
        """제외 대상은 **실험** 가중치다 — 그냥 「가중치」면 필수분까지 읽힌다."""
        line = next(ln for ln in self.text.splitlines() if ln.startswith("| S4 |"))
        self.assertIn("실험", line)
        self.assertNotIn("학습 가중치 바이너리", line)


class TestReproductionRecordIsCurrent(unittest.TestCase):
    def test_d2_record_names_a_recent_commit(self) -> None:
        """재현 기록이 **어느 커밋에서** 확인한 것인지 말해야 한다."""
        text = CHECKLIST.read_text(encoding="utf-8")
        m = re.search(r"깨끗한 환경 재현 확인 \(([^)]*)\)", text)
        self.assertIsNotNone(m, "D-2 재현 기록을 못 찾았다")
        assert m is not None
        self.assertIn("main", m.group(1), "어느 커밋인지 안 적혀 있다")

    def test_d2_mentions_both_gates(self) -> None:
        text = CHECKLIST.read_text(encoding="utf-8")
        for gate in ("clean_room", "prod_room"):
            self.assertIn(gate, text, f"재현 기록에 {gate} 가 없다")


class TestReleaseCheckIsWired(unittest.TestCase):
    def test_script_exists_and_is_executable(self) -> None:
        p = ROOT / "scripts" / "check_release.sh"
        self.assertTrue(p.is_file())
        self.assertTrue(p.stat().st_mode & 0o111, "실행 권한이 없다")

    def test_checklist_points_at_it(self) -> None:
        self.assertIn("check_release.sh", CHECKLIST.read_text(encoding="utf-8"))

    def test_run_tests_runs_it(self) -> None:
        """매번 돌아야 한다 — 8/25 에 처음 보면 늦다."""
        self.assertIn("check_release.sh",
                      hash_comment_free((ROOT / "scripts" / "run_tests.sh")))


if __name__ == "__main__":
    unittest.main()
