r"""`clean_room.sh` 가 **무엇을 재현한다고 말하는가** (큐 #46 · `#223` 형제).

## 왜 있는가

`#223` 은 `prod_room.sh` 가 라우트 **스물넷 중 다섯**만 눌러 보면서 「제품 프로파일에서
전부 재현된다」를 찍고 있던 것을 잡았다. **형제 자리가 남아 있었다** — `clean_room.sh` 다.

## 실측 (2026-09-05)

| 무엇 | 수 |
|---|---|
| `scripts/` 의 데모 스크립트 | **13** |
| `clean_room.sh` 가 부르는 것 | **2** — `demo.sh` · `demo_violations.sh` |
| `prod_room.sh` 가 부르는 것 | **1** — `demo.sh` |
| 카탈로그 「구현됨」 능력 | **10** |
| 깨끗한 환경에서 **종단으로** 도는 능력 | **1** — `image.classify` |

그런데 마지막 줄은 이렇게 찍혔다:

```text
깨끗한 환경에서 전부 재현된다.
```

**「전부」가 무엇의 전부인지 적혀 있지 않았다.** 읽는 사람은 능력 열 종이 빈 볼륨에서
재현된 것으로 읽는다. 실제로는 하나다.

## 무엇을 고쳤나 — **문구를 실제 범위에 맞췄다**

데모 열하나를 `clean_room.sh` 에 **넣지 않았다.** 이 세션에는 Docker 가 없어
(`docker info` 실패) 넣은 단계가 실제로 도는지 **재 볼 수 없다.** 재 보지 않은 단계를
게이트에 넣는 것은 이 저장소가 계속 잡아 온 「됐을 것」이다.

대신 **말과 사실을 맞추고**, 새 데모가 조용히 게이트 밖에서 태어나지 못하게 못박는다.

## 무엇을 고정하나

1. 모든 데모 스크립트는 **clean_room 이 부르거나** 아래 `OUTSIDE_CLEAN_ROOM` 에
   **이유와 함께** 있다 — 새 데모는 둘 중 하나를 반드시 거친다
2. 목록은 **조용히 늘 수 없다** (`#221` 손 허용 목록 규율)
3. `clean_room.sh` 의 통과 문구가 **범위를 밝힌다** — 「전부」만 남기지 않는다
4. 세는 대상이 0 이 아니다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CLEAN_ROOM = SCRIPTS / "clean_room.sh"

# clean_room 밖에 있는 데모와 **그 이유**. 늘리려면 아래 핀도 같이 고쳐야 한다.
OUTSIDE_CLEAN_ROOM = {
    "capreq_demo.sh": "제품 입구(설치형 CLI) — 빈 볼륨 배터리가 아니라 패키지 경로다",
    "product_demo.sh": "같음 — 사용자 시나리오 재생이라 게이트가 아니다",
    "embed_demo.sh": "text.embed 종단 — Docker 없이 못 재 봐서 넣지 않았다 (큐 #46)",
    "image_embed_demo.sh": "image.embed 종단 — 같은 이유 (큐 #46)",
    "ner_demo.sh": "text.ner 종단 — 같은 이유 (큐 #46)",
    "pii_demo.sh": "safety.pii 종단 — 같은 이유 (큐 #46)",
    "series_demo.sh": "timeseries.forecast 종단 — 같은 이유 (큐 #46)",
    "table_demo.sh": "table.extract 종단 — 같은 이유 (큐 #46)",
    "text_demo.sh": "text.classify 종단 — 같은 이유 (큐 #46)",
    "text_extract_demo.sh": "text.extract 종단 — 같은 이유 (큐 #46)",
    "text_rank_demo.sh": "text.rank 종단 — 같은 이유 (큐 #46)",
}


def _demos() -> list[str]:
    return sorted(p.name for p in SCRIPTS.glob("*demo*.sh"))


def _called_by(path: Path) -> set[str]:
    """그 스크립트가 **실제로 부르는** 다른 스크립트 이름."""
    body = path.read_text(encoding="utf-8")
    return {m.group(1) for m in re.finditer(r"scripts/([a-z_]+\.sh)", body)} - {path.name}


class TestEveryDemoIsAccountedFor(unittest.TestCase):
    def test_no_demo_is_silently_outside_the_gate(self) -> None:
        """새 데모가 게이트 밖에서 태어나면 아무도 모른다."""
        demos = _demos()
        self.assertTrue(demos, "데모 스크립트를 하나도 못 찾았다")
        called = _called_by(CLEAN_ROOM)
        orphan = [d for d in demos if d not in called and d not in OUTSIDE_CLEAN_ROOM]
        self.assertEqual([], orphan, f"clean_room 도 목록도 모르는 데모: {orphan}")

    def test_the_outside_list_is_pinned(self) -> None:
        """오늘 밖에 있는 것은 **열하나**다. 늘리려면 이 줄을 같이 고친다."""
        self.assertEqual(11, len(OUTSIDE_CLEAN_ROOM), sorted(OUTSIDE_CLEAN_ROOM))

    def test_the_outside_list_names_only_real_files(self) -> None:
        """지워진 파일이 목록에 남으면 「해명했다」가 거짓이 된다."""
        missing = [n for n in OUTSIDE_CLEAN_ROOM if not (SCRIPTS / n).is_file()]
        self.assertEqual([], missing, f"없는 파일을 해명하고 있다: {missing}")

    def test_every_excuse_says_something(self) -> None:
        blank = [n for n, why in OUTSIDE_CLEAN_ROOM.items() if len(why.strip()) < 4]
        self.assertEqual([], blank, f"이유가 비었다: {blank}")


class TestTheClaimMatchesTheScope(unittest.TestCase):
    """「전부 재현된다」는 **무엇의 전부인지** 말해야 한다 (`#223` 이 잡은 모양)."""

    def test_clean_room_states_its_scope(self) -> None:
        line = [l for l in CLEAN_ROOM.read_text(encoding="utf-8").splitlines()
                if "tally_verdict" in l and "재현된다" in l]
        self.assertEqual(1, len(line), f"통과 문구를 못 찾았다: {line}")
        self.assertIn("image.classify", line[0],
                      "통과 문구가 능력 종단의 범위를 안 밝힌다: " + line[0])

    def test_clean_room_still_runs_the_two_it_claims(self) -> None:
        """문구만 고치고 단계를 지우면 그건 후퇴다."""
        called = _called_by(CLEAN_ROOM)
        self.assertIn("demo.sh", called)
        self.assertIn("demo_violations.sh", called)


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_demos_are_seen(self) -> None:
        self.assertGreaterEqual(len(_demos()), 12, f"{len(_demos())}개만 봤다")

    def test_caller_detector_works(self) -> None:
        """부르는 것을 못 읽으면 위 전부가 공허하다."""
        self.assertIn("demo.sh", _called_by(CLEAN_ROOM))
        self.assertNotIn("text_demo.sh", _called_by(CLEAN_ROOM))


if __name__ == "__main__":
    unittest.main()
