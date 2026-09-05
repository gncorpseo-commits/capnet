r"""문서가 적은 「**CI 가 본다**」가 실제 워크플로와 같은가 (큐 #59 · `#215` 옆).

## 왜 있는가

`#215` 가 잡은 것은 「**CI 가 본다**」가 **거짓**이던 자리였다 — 건너뛴 일곱은 어디에서도
안 돌고 있었다. 이번에는 그 문장이 적힌 **목록 자체**를 실제 `ci.yml` 과 대조했다.

## 실측 (2026-09-05)

| job | `ci.yml` 의 단계 | `testing.md` §4 가 적던 것 |
|---|---|---|
| `unit` | **4** | **3** — `check_release.sh`(G9) 가 빠졌다 |
| `capreq` | 2 | 2 |
| `migrate` | **9** (의존성 설치 · 통합 검사 포함) | **6 + 통합** — SD-015 가 빠졌다 |

빠진 둘은 **실제로 도는데 문서에 없다.** 「CI 가 본다」고 적힌 목록이 실제보다 짧으면,
안 적힌 단계는 **없는 것처럼 읽힌다** — 그러면 지우거나 옮겨도 아무도 못 본다.
`#217`(시크릿 검사가 CI 워크플로를 안 보고 있었다)과 같은 모양이다.

## `ci.yml` 은 고치지 않았다

잡·설치·단계 추가는 열린 Decision (`round9-ci-coverage-proposal`)이다.
여기서 고친 것은 **문서**뿐이고, 검사는 **양쪽을 대조**만 한다.

## 무엇을 고정하나

1. `ci.yml` 의 모든 단계가 `testing.md` §4 에 **대응**을 갖는다
2. 문서가 **없는 단계를 말하지 않는다** (유령)
3. 대응표가 조용히 늘지 않는다

## 무엇을 안 보나

문구가 **똑같은지**. 문서는 사람이 읽는 글이라 표현이 다르다 — 아래 `STEP_KEYWORD` 가
단계마다 「문서에 반드시 있어야 하는 낱말」을 하나씩 잇는다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"
TESTING = ROOT / "docs" / "guide" / "testing.md"

# `ci.yml` 의 단계 이름 → 문서에 있어야 하는 낱말. 새 단계는 여기와 문서를 같이 고친다.
STEP_KEYWORD = {
    "단위 테스트": "단위 테스트",
    "골든셋 sha 정합": "check_golden_sha.py",
    "제출 zip 사전 검증 (G9)": "check_release.sh",
    "출품 패키지 기계 점검 (SD-005)": "check_submission.py",
    "러너 의존성 (capreq 런타임 핀)": "python-multipart",
    "capreq 단위 테스트": "capreq/tests",
    "러너 의존성 (core 와 동일 핀)": "설치 없음",          # unit 이 안 까는 이유를 적는 자리
    "baseline 가드 — 빈 DB 에서는 아무것도 쓰지 않는다": "baseline 가드",
    "schema + seed (새 볼륨 경로 = initdb 가 하는 일)": "schema + seed",
    "verify → up → verify → up (멱등)": "verify → up → verify → up",
    "새 볼륨이면 증적 드리프트가 0 이어야 한다": "증적 드리프트 0",
    "체크섬 잠금 — 적용된 파일을 고치면 거부한다": "체크섬 잠금",
    "기존 볼륨 경로 — 구 sha 에서 0003 이 올려준다": "기존 볼륨 경로",
    "새 볼륨에는 placeholder Agent 의 라우팅 증서가 없다 (SD-015)": "SD-015",
    "통합 검사 (검사마다 깨끗한 DB)": "통합 검사",
}

STEP = re.compile(r"^\s+- name:\s*(.+?)\s*$", re.M)


def ci_steps() -> list[str]:
    return STEP.findall(CI.read_text(encoding="utf-8"))


def section4() -> str:
    """`testing.md` §4 부터 §5 앞까지."""
    body = TESTING.read_text(encoding="utf-8")
    start = body.index("## 4. CI")
    end = body.index("## 5", start) if "## 5" in body[start:] else len(body)
    return body[start:end]


class TestDocsCoverEveryCiStep(unittest.TestCase):
    def test_every_step_is_mentioned(self) -> None:
        """**여기가 핵심이다.** 안 적힌 단계는 없는 것처럼 읽힌다."""
        steps = ci_steps()
        self.assertTrue(steps, "ci.yml 에서 단계를 하나도 못 읽었다")
        text = section4()
        missing = []
        for step in steps:
            word = STEP_KEYWORD.get(step)
            if word is None:
                missing.append(f"{step} (대응표에 없다)")
            elif word not in text:
                missing.append(f"{step} → 문서에 «{word}» 가 없다")
        self.assertEqual([], missing, "문서가 안 적은 CI 단계: " + "; ".join(missing))

    def test_the_map_has_no_ghosts(self) -> None:
        """사라진 단계가 표에 남으면 「대조했다」가 거짓이 된다."""
        ghosts = sorted(set(STEP_KEYWORD) - set(ci_steps()))
        self.assertEqual([], ghosts, f"없는 단계가 대응표에 남아 있다: {ghosts}")

    def test_the_map_is_pinned(self) -> None:
        self.assertEqual(15, len(STEP_KEYWORD),
                         "CI 단계 수가 바뀌었다 — 표와 문서를 같이 고친다")


class TestTheDocDoesNotOverclaim(unittest.TestCase):
    def test_migrate_step_count_matches(self) -> None:
        """「마이그레이션 N단계」는 세면 나오는 값이라 문서와 CI 가 같아야 한다."""
        migrate = [s for s in ci_steps()
                   if s not in ("단위 테스트", "골든셋 sha 정합", "제출 zip 사전 검증 (G9)",
                                "출품 패키지 기계 점검 (SD-005)",
                                "러너 의존성 (capreq 런타임 핀)", "capreq 단위 테스트",
                                "러너 의존성 (core 와 동일 핀)", "통합 검사 (검사마다 깨끗한 DB)")]
        m = re.search(r"마이그레이션 \*{0,2}(\d+)\s*단계", section4())
        self.assertIsNotNone(m, "문서에서 「마이그레이션 N단계」를 못 찾았다")
        assert m is not None
        self.assertEqual(len(migrate), int(m.group(1)),
                         f"문서 {m.group(1)}단계 ≠ ci.yml {len(migrate)}단계")

    def test_numbered_list_has_the_same_count(self) -> None:
        block = section4().split("migrate job 이 보는 것", 1)[-1].split("\n---", 1)[0]
        numbered = re.findall(r"^\d+\. ", block, re.M)
        self.assertEqual(7, len(numbered), f"번호 목록이 {len(numbered)}개다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_ci_steps_are_seen(self) -> None:
        self.assertGreaterEqual(len(ci_steps()), 12, ci_steps())

    def test_section_is_found_and_not_empty(self) -> None:
        self.assertGreater(len(section4()), 800, "§4 를 제대로 못 잘랐다")
        self.assertIn("ci.yml", section4())


if __name__ == "__main__":
    unittest.main()
