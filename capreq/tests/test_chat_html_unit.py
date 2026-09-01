"""`chat.html` 정적 검사 — 서버 요약기와 화면이 같은 칸 이름을 쓰는가.

## 왜 있는가

이 파일이 없어서 생긴 일이 두 번이다. #110 이 `text.extract`(`fields`)를, #116 이
`text.rank`(`ranking`)를 들여왔는데 **화면은 몰랐다.** 두 결과는 `other` 폴백으로
떨어져 제품 입구에서 **원시 JSON 한 줄**로 보였고, 아무 검사도 그것을 말해 주지 않았다.
서버 경로에 검사가 0 이라 첨부 버그를 아무도 몰랐던 #112 와 같은 모양이다.

## 무엇을 보나 · 무엇을 못 보나

여기서 보는 것은 **요약기가 내보낼 수 있는 칸마다 화면에 그리는 자리가 있는가**다.
`summarize_result` 를 실제로 돌려 칸 이름을 얻고, 그 이름이 `chat.html` 에 있는지 본다 —
칸 목록을 손으로 두 번 적지 않는다.

**이 파일은 문자열 검사다.** 부분 문자열이라 **「반쯤 지운 렌더러」를 통과시킨다** —
실제로 확인했다(`result.pii` 분기만 남기고 몸통을 지우면 여기는 통과한다).
그 구멍은 **`test_chat_render.py` 가 렌더러를 실행해** 막는다 (같은 변이에서 7종 실패).

**그때 진단이 절반만 맞았다 (2026-09-01 정정).** `result.pii` 를 **통째로** 지웠을 때도
이 파일이 통과했는데, 원인은 부분 문자열이 아니라 **`EVERY_SHAPE` 픽스처에 `pii` 칸이
없어서**였다 — Wave L 이 요약기·화면을 고치면서 이 픽스처를 안 고쳤다.
지금은 픽스처가 그 칸을 만들고, `test_fixture_covers_every_summariser_branch` 가
**요약기 소스에서 키를 뽑아** 다음 능력에서 또 뒤처지지 않게 막는다.

**둘 다 실제 브라우저는 아니다** — CSS·레이아웃·사용자 상호작용은 여전히 못 본다.
「브라우저에서 봤다」고 쓰지 않는다. **본 것만 말한다.**
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from capreq.results import summarize_result

CHAT = Path(__file__).resolve().parents[1] / "src" / "capreq" / "static" / "chat.html"

RESULTS = Path(__file__).resolve().parents[1] / "src" / "capreq" / "results.py"

# **등록된 능력이 실제로 내는 칸**을 한데 넣은 결과. 여기서 요약기가 뽑아내는 키가
# 화면이 알아야 할 목록의 **정본**이다.
#
# 이 픽스처가 **뒤처진 적이 있다.** Wave L 이 `safety.pii` 를 더했을 때 `results.py` 와
# `chat.html` 은 고쳤는데 여기는 안 고쳤고, 그래서 **pii 렌더러가 이 검사의 대상이 아니었다**
# (`result.pii` 를 통째로 지워도 통과했다). 그때는 「부분 문자열 검사라 못 잡는다」로만
# 적었는데, 진짜 이유의 절반은 **픽스처가 그 칸을 안 만들었기 때문**이다.
#
# 그래서 아래 `test_fixture_covers_every_summariser_branch` 가 **요약기 소스에서 키를 뽑아**
# 이 픽스처가 그걸 다 만드는지 본다 — 다음 능력에서 또 뒤처지지 않게.
EVERY_SHAPE = {
    "label": "annual_crop",
    "confidence": 0.98,
    "entities": [{"label": "email", "start": 0, "end": 3, "text": "a@b"}],
    "vector": [0.1, 0.2, 0.3],
    "fields": [{"key": "Ticket", "value": "INC-1", "line": 0, "start": 8, "end": 13}],
    "query": "질의",
    "ranking": [{"rank": 1, "line": 1, "text": "t", "score": 0.5, "overlap": ["a"]}],
    "patterns_checked": ["email"],
    "findings": [{"label": "email", "start": 0, "end": 3, "text": "a**@b"}],
    "columns": [{"index": 0, "type": "int"}],
    "rows": [[1]],
    "dummy": False,
}

# 요약기가 **낼 수 있는** 키. 손으로 세지 않고 소스에서 뽑는다.
_OUT_KEY = re.compile(r'^\s*out\["(\w+)"\]', re.M)


def summariser_keys() -> set[str]:
    return set(_OUT_KEY.findall(RESULTS.read_text(encoding="utf-8")))


class TestViewKnowsEveryResultShape(unittest.TestCase):
    def setUp(self) -> None:
        self.html = CHAT.read_text(encoding="utf-8")

    def test_every_summary_key_has_a_renderer(self) -> None:
        keys = set(summarize_result(EVERY_SHAPE))
        self.assertNotIn("other", keys, "등록된 능력의 칸이 폴백으로 새면 안 된다")
        missing = [k for k in sorted(keys) if f"result.{k}" not in self.html]
        self.assertEqual(missing, [], f"화면이 모르는 결과 칸: {missing}")

    def test_fixture_covers_every_summariser_branch(self) -> None:
        """픽스처가 **요약기의 모든 칸**을 만들어 내는가.

        `EVERY_SHAPE` 가 어떤 칸을 안 만들면 그 렌더러는 **검사되지 않는다** —
        Wave L 에서 `pii` 가 실제로 그랬다. 요약기 소스에서 키를 뽑아 대조한다.
        """
        can_emit = summariser_keys() - {"other"}   # 폴백은 아래 검사가 따로 본다
        produced = set(summarize_result(EVERY_SHAPE))
        missing = sorted(can_emit - produced)
        self.assertEqual(missing, [], f"픽스처가 안 만드는 칸: {missing}")

    def test_the_key_probe_finds_things(self) -> None:
        """정규식이 0개를 찾으며 통과하는 상태를 막는다."""
        self.assertGreaterEqual(len(summariser_keys()), 8, sorted(summariser_keys()))

    def test_fallback_is_still_there(self) -> None:
        """다음에 또 새 칸이 오면 그때도 삼키지 않아야 한다."""
        self.assertIn("result.other", self.html)

    def test_fields_and_ranking_columns(self) -> None:
        for col in ('"key", "value", "line"', '"rank", "score", "overlap", "text"'):
            self.assertIn(col, self.html, f"표 머리 {col} 이 없다")

    def test_truncation_is_disclosed_on_screen(self) -> None:
        """화면 자르기를 말없이 하지 않는다 — `truncated` 를 보는 곳마다 「앞 N개만 표시」.

        개수를 손으로 세지 않는다. 렌더러가 하나 늘 때마다 이 숫자를 고치게 하면
        언젠가 **고치는 대신 검사를 지우게** 된다 — 실제로 Wave L 에서 4가 됐다.
        """
        guards = list(re.finditer(r"(\w+)\.truncated", self.html))
        self.assertGreaterEqual(len(guards), 4, [g.group(0) for g in guards])
        silent = []
        for g in guards:
            near = self.html[g.end() : g.end() + 200]
            # 목록은 「앞 N개만 표시」로, 벡터는 `…` 로 알린다 — 형태는 가리지 않는다.
            if "만 표시" not in near and "…" not in near:
                silent.append(g.group(0))
        self.assertEqual(silent, [], f"자른 사실을 말하지 않는 곳: {silent}")

    def test_rank_score_is_not_called_relevance(self) -> None:
        """`text.rank` 는 quality_profile='none' 이다 — 점수를 관련도로 팔지 않는다."""
        for word in ("관련도", "정확도", "유사도"):
            self.assertNotIn(f"{word}=", self.html)
        self.assertIn("뜻을 비교한 것이 아닙니다", self.html)


if __name__ == "__main__":
    unittest.main()
