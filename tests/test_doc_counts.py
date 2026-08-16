"""문서가 **자라는 숫자**를 못박지 않았는가 (출품 트랙 위생).

## 왜 있는가

검사 개수는 능력·강제 경로를 더할 때마다 는다. 그런데 문서 표에 그 숫자를 적어 두면
**다음 사람이 숫자만 고치게** 되고, 안 고치면 조용히 어긋난다.

실제로 `safety-chain.md` 의 네 칸이 전부 어긋나 있었다 —
`check_api_key` 23→**22** · `check_node_credential` 17→**18** ·
`check_enforcement` 20→**30** · `prod_room.sh` 14→**27**.

**숫자를 맞추는 대신 표에서 뺐다.** 봐야 할 것은 「전부 통과」이고, 개수는
`run_tests.sh` 와 `prod_room.sh` 출력이 그때그때 말한다.

## 무엇을 고정하나

1. **자라는 개수를 문서에 다시 못박지 않았는가** — `check_*(N)` 꼴이 돌아오면 실패
2. **고정돼야 할 개수는 실물과 맞는가** — 마이그레이션 세대처럼 눈으로 대조하는 값
3. **새 산출물이 문서 지도에 올라갔는가** — 안 올리면 다음 사람이 못 찾는다

## 무엇을 고정하지 않나

`run_tests` 총 개수. 그건 자라는 값이고, 런북이 이미 「숫자가 달라도 이상이 아니다」를
적어 뒀다(`test_shoot_docs`).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAFETY = ROOT / "docs" / "design" / "safety-chain.md"
INDEX = ROOT / "docs" / "INDEX.md"

# 「자라는 개수」를 표에 적으면 안 되는 검사들.
GROWING = ("check_api_key", "check_node_credential", "check_enforcement", "prod_room.sh")


class TestGrowingCountsNotPinned(unittest.TestCase):
    def test_safety_chain_has_no_pinned_counts(self) -> None:
        """`check_enforcement (20)` 같은 표기가 돌아오면 실패한다."""
        text = SAFETY.read_text(encoding="utf-8")
        offenders = []
        for name in GROWING:
            # 「(숫자)」가 바로 뒤에 붙은 경우만 본다. 본문에서 이력을 말하는 것은 허용
            # (예: 「20→30 으로 어긋나 있었다」) — 그건 설명이지 현재 값 주장이 아니다.
            for m in re.finditer(re.escape(f"`{name}`") + r"\s*\((\d+)\)", text):
                offenders.append(f"{name}({m.group(1)})")
        self.assertFalse(
            offenders,
            "자라는 검사 개수를 표에 못박았다: " + ", ".join(offenders)
            + " — 개수는 run_tests·prod_room 출력이 말한다",
        )

    def test_reason_is_written_down(self) -> None:
        """왜 안 적는지가 문서에 있어야 한다 — 없으면 다음 사람이 「빠졌네」 하고 채운다."""
        self.assertIn("개수를 적지 않는다", SAFETY.read_text(encoding="utf-8"))


class TestPinnedCountsAreTrue(unittest.TestCase):
    """반대로, **고정돼야 하는** 개수는 실물과 맞아야 한다."""

    def test_migration_generation(self) -> None:
        n = len(list((ROOT / "migrations").glob("*.sql")))
        for doc in (ROOT / "README.md", ROOT / "docs" / "ops" / "shoot-day-runbook.md"):
            self.assertIn(f'"완료 — {n}개 적용"', doc.read_text(encoding="utf-8"),
                          f"{doc.name} 의 마이그레이션 개수가 실물({n})과 다르다")


class TestNewArtifactsAreIndexed(unittest.TestCase):
    """새 산출물이 문서 지도에 올라갔는가 — 안 올리면 다음 사람이 못 찾는다."""

    def test_release_check_is_indexed(self) -> None:
        self.assertIn("check_release.sh", INDEX.read_text(encoding="utf-8"))

    def test_catalog_and_step6_are_indexed(self) -> None:
        text = INDEX.read_text(encoding="utf-8")
        for name in ("capability-catalog.md", "step6-executors.md"):
            self.assertIn(name, text)


class TestDocDatesAreNotAncient(unittest.TestCase):
    """갱신일이 내용보다 오래되면 읽는 사람이 신뢰도를 잘못 잡는다.

    「오늘」을 요구하지는 않는다 — 그건 매일 실패한다.
    **최근 CHANGELOG 항목보다 오래되지 않았는가**만 본다.
    """

    def test_updated_dates_track_changelog(self) -> None:
        changelog = (ROOT / "docs" / "history" / "CHANGELOG.md").read_text(encoding="utf-8")
        latest = re.search(r"— (\d{4}-\d{2}-\d{2})\n", changelog)
        self.assertIsNotNone(latest, "CHANGELOG 최신 날짜를 못 찾았다")
        assert latest is not None
        newest = latest.group(1)

        for rel in ("STATE.md", "docs/ops/shoot-day-runbook.md",
                    "docs/spec/capability-catalog.md",
                    "docs/ops/contest-submission-checklist.md"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            m = re.search(r"갱신:?\*{0,2}\s*(\d{4}-\d{2}-\d{2})", text)
            self.assertIsNotNone(m, f"{rel} 에 갱신일이 없다")
            assert m is not None
            self.assertGreaterEqual(
                m.group(1), newest,
                f"{rel} 갱신일({m.group(1)})이 최신 CHANGELOG({newest})보다 오래됐다",
            )


if __name__ == "__main__":
    unittest.main()
