r"""능력 종단 데모 아홉이 **clean_room 에 들어갈 준비가 됐는가** (배치 B #74 · `#229` 잔여).

## 왜 있는가

`#229`(큐 #46)는 `clean_room` 이 데모 **열셋 중 둘**만 돌리면서 「전부 재현된다」를 찍던
것을 잡고, 아홉을 **안 넣은 이유**를 「Docker 가 없어 재 볼 수 없다」로 적었다.

**그 문장은 「무엇이 더 필요한지 모른다」로도 읽힌다.** 재 봤다 — 필요한 것은
**Docker 하나뿐**이다.

## 실측 (2026-09-06)

| 데모 | 가중치 | 저장소에 있나 | Ollama |
|---|---|---|---|
| `embed_demo` | `text_embed_scratch` | ✅ | 아니오 |
| `image_embed_demo` | `eurosat_scratch` | ✅ | 아니오 |
| `ner_demo` | `rule_ner` | ✅ | 아니오 |
| `pii_demo` | `rule_pii` | ✅ | 아니오 |
| `series_demo` | `series_scratch` | ✅ | 아니오 |
| `table_demo` | `text_struct_scratch` | ✅ | 아니오 |
| `text_demo` | `text_struct_scratch` | ✅ | 아니오 |
| `text_extract_demo` | `rule_extract`·`rule_ner` | ✅ | 아니오 |
| `text_rank_demo` | `rule_extract`·`rule_ner`·`rule_rank` | ✅ | 아니오 |

**아홉 전부 추가 가능하다.** 새로 만들 가중치도, 내려받을 것도, Ollama 도 없다 —
`docker compose up` 하나가 서면 `clean_room` 에 `step` 아홉 줄을 얹으면 된다.

`capreq_demo` 는 다르다 — **Ollama 가 필요하다.** 그래서 `#229` 의 `OUTSIDE_CLEAN_ROOM`
에 그대로 둔다.

## 무엇을 고정하나

1. 아홉이 부르는 가중치가 **전부 저장소에 있다** — 하나라도 빠지면 그 데모는 추가 불가
2. 그 가중치가 `check_submission.REQUIRED_WEIGHTS`(제출 정본)와 어긋나지 않는다
3. 아홉은 **Ollama 를 안 쓴다** (쓰기 시작하면 `capreq_demo` 쪽으로 옮겨야 한다)
4. 세는 대상이 비지 않는다

## 무엇을 안 보나

**돌려 보지 않는다.** 아홉이 실제로 완주하는지는 `docker compose up` 이 서야 안다
(이 세션에는 데몬이 없다 — `docker info` 실패 · 규약 6).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
WEIGHTS = ROOT / "apps" / "node" / "weights"
SUBMISSION = ROOT / "scripts" / "check_submission.py"

# `clean_room` 에 넣을 후보 — 능력 종단 데모. `capreq_demo`·`product_demo` 는 아니다.
CANDIDATES = ("embed_demo.sh", "image_embed_demo.sh", "ner_demo.sh", "pii_demo.sh",
              "series_demo.sh", "table_demo.sh", "text_demo.sh",
              "text_extract_demo.sh", "text_rank_demo.sh")

SAFETENSORS = re.compile(r"([a-z0-9_]+\.safetensors)")
OLLAMA = re.compile(r"ollama|OLLAMA", re.I)


def _needs(name: str) -> set[str]:
    return set(SAFETENSORS.findall((SCRIPTS / name).read_text(encoding="utf-8")))


def _present() -> set[str]:
    return {p.name for p in WEIGHTS.glob("*.safetensors")}


class TestEveryCandidateCanBeAdded(unittest.TestCase):
    def test_all_needed_weights_are_in_the_repo(self) -> None:
        """**여기가 핵심이다.** 하나라도 없으면 그 데모는 추가할 수 없다."""
        have = _present()
        self.assertTrue(have, "가중치를 하나도 못 찾았다")
        bad = []
        for name in CANDIDATES:
            missing = _needs(name) - have
            if missing:
                bad.append(f"{name} ← {sorted(missing)}")
        self.assertEqual([], bad, f"저장소에 없는 가중치를 부른다: {bad}")

    def test_every_candidate_names_at_least_one_weight(self) -> None:
        """가중치를 안 부르면 이 표가 그 데모에 대해 아무 말도 안 한다."""
        bare = [n for n in CANDIDATES if not _needs(n)]
        self.assertEqual([], bare, f"가중치를 안 부르는 후보: {bare}")

    def test_none_of_them_needs_ollama(self) -> None:
        """Ollama 를 쓰기 시작하면 `capreq_demo` 쪽 분류로 옮겨야 한다."""
        bad = [n for n in CANDIDATES
               if OLLAMA.search((SCRIPTS / n).read_text(encoding="utf-8"))]
        self.assertEqual([], bad, f"Ollama 를 쓰는 후보: {bad}")

    def test_capreq_demo_does_need_it(self) -> None:
        """대비가 없으면 위 검사가 **무엇을 가르는지** 알 수 없다."""
        self.assertTrue(OLLAMA.search((SCRIPTS / "capreq_demo.sh").read_text(encoding="utf-8")),
                        "capreq_demo 가 Ollama 를 안 쓴다 — 분류 근거가 사라졌다")


class TestTheWeightsAgreeWithSubmission(unittest.TestCase):
    """제출 정본과 어긋나면 심사본에서 그 데모가 못 돈다."""

    def test_needed_weights_are_declared_required(self) -> None:
        body = SUBMISSION.read_text(encoding="utf-8")
        needed: set[str] = set()
        for name in CANDIDATES:
            needed |= _needs(name)
        missing = sorted(w for w in needed if w.replace(".safetensors", "") not in body)
        self.assertEqual([], missing,
                         f"데모가 쓰는데 REQUIRED_WEIGHTS 에 없다: {missing}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_all_candidates_exist(self) -> None:
        missing = [n for n in CANDIDATES if not (SCRIPTS / n).is_file()]
        self.assertEqual([], missing, f"없는 후보: {missing}")
        self.assertEqual(9, len(CANDIDATES))

    def test_the_weight_reader_discriminates(self) -> None:
        self.assertIn("rule_ner.safetensors", _needs("ner_demo.sh"))
        self.assertNotIn("rule_ner.safetensors", _needs("series_demo.sh"))


if __name__ == "__main__":
    unittest.main()
