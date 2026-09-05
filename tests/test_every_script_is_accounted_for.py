r"""스크립트 **누가 돌리나** — 그리고 아무도 안 돌리는 것이 깨져 있지 않은가 (큐 #63).

## 왜 있는가

`#63` 은 `regate.sh`·`proof_ab.sh` 를 「본실행 or **못 봄** 명시」로 남겼다. 재려고 보니
더 큰 사실이 나왔다 — **스크립트 서른넷 중 스물여섯은 아무것도 안 돌린다.**

| 누가 | 무엇을 |
|---|---|
| `run_tests.sh` | `check_release.sh` · `migrate.sh` |
| `clean_room.sh` | `demo.sh` · `demo_violations.sh` · `sanity.sh` · `call.sh` · `node_onboard.sh` |
| `prod_room.sh` | `demo.sh` |
| `ci.yml` | `run_integration.sh` · `check_release.sh` |
| **아무도** | **26** |

**스물여섯이 전부 결함은 아니다.** 학습(`train_*`)·내려받기·수동 데모는 사람이 부르는
도구다. 문제는 **그게 어디에도 안 적혀 있어서**, 게이트에 있어야 할 것이 빠져도 티가 안
난다는 것이다 — `#229`(clean_room 이 데모 13 중 2만 돈다)와 같은 자리, 이번에는 전수다.

## 그래서 무엇을 했나

1. **표를 만들었다** — 스물여섯이 각자 왜 수동인지 적는다. 새 스크립트는 둘 중 하나다:
   무언가가 부르거나, 표에 이유가 있거나
2. **문법을 전수했다** — `bash -n` 34/34 통과. 아무도 안 돌리는 스크립트가 **깨져
   있으면 아무도 모른다.** 이 저장소에서 처음 센 값이다

## `regate.sh` · `proof_ab.sh` — **못 봤다**

둘 다 `docker compose up -d` 와 Node 의 실제 가중치 파일이 있어야 돈다. 이 세션에는
**Docker 데몬이 없다** (`docker info` 실패 · compose CLI 는 v5.3.1 로 있다).

| 스크립트 | 오늘 잰 것 | 못 잰 것 |
|---|---|---|
| `regate.sh` | 문법 · 머리말의 사전 조건 명시 | 본실행 (재게이트 대상·새 `gate_run`) |
| `proof_ab.sh` | 같음 | 본실행 (A·B 교차 배정) |

Docker 가 있는 회차의 줄로 남긴다. **「돌 것이다」로 적지 않는다.**
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CI = ROOT / ".github" / "workflows" / "ci.yml"

RUNNERS = ("run_tests.sh", "clean_room.sh", "prod_room.sh")

# 아무도 안 부르는 스크립트와 **왜 수동인가**. 새 스크립트는 여기 오거나 불려야 한다.
# 이름에 `WITHOUT` 이 있어야 `#231` 의 허용목록 표가 이것을 **본다** — `WITHOUT_A_CALLER` 로 뒀더니
# 탐지 패턴에 안 걸려 표에 유령으로 남았다 (큐 #63 에서 겪었다).
WITHOUT_A_CALLER = {
    "backfill_agent_arch.sh": "일회성 백필 — 세대가 지나면 안 쓴다",
    "capreq_demo.sh": "제품 입구 종단 — Ollama + 살아 있는 스택 (큐 #46)",
    "compare_ab.sh": "A/B 오프라인 비교 — 채점 산출물이 있어야 한다",
    "contract_bind.sh": "계약 샘플 부착 — 살아 있는 스택",
    "download_eurosat.sh": "원본 zip 내려받기 — 저장소에 동봉하지 않는다",
    "embed_demo.sh": "능력 종단 데모 — 살아 있는 스택 (큐 #46)",
    "extract_golden_n300.sh": "골든셋 추출 — 원본 zip 필요",
    "generate_sbom.sh": "SBOM 생성 — `pip install cyclonedx-bom` 필요 (큐 #55)",
    "image_embed_demo.sh": "능력 종단 데모 (큐 #46)",
    "ner_demo.sh": "능력 종단 데모 (큐 #46)",
    "node_bind.sh": "온보딩 2단계 — 살아 있는 스택",
    "pass_rate.sh": "합격률 재측정 — 살아 있는 스택",
    "pii_demo.sh": "능력 종단 데모 (큐 #46)",
    "product_demo.sh": "제품 주장 한 파일 — 살아 있는 스택 (큐 #46)",
    "proof_ab.sh": "UC-7 교차 실행 — 살아 있는 스택 + A·B 가중치 (큐 #63 · **못 봤다**)",
    "regate.sh": "골든셋 교체 후 재게이트 — 살아 있는 스택 (큐 #63 · **못 봤다**)",
    "score_n300.sh": "n=300 채점 — 가중치와 골든셋 필요",
    "series_demo.sh": "능력 종단 데모 (큐 #46)",
    "table_demo.sh": "능력 종단 데모 (큐 #46)",
    "text_demo.sh": "능력 종단 데모 (큐 #46)",
    "text_extract_demo.sh": "능력 종단 데모 (큐 #46)",
    "text_rank_demo.sh": "능력 종단 데모 (큐 #46)",
    "train_scratch.sh": "EuroSAT scratch 학습 — 원본 zip + 시간",
    "train_series_scratch.sh": "같음 (timeseries)",
    "train_text_embed.sh": "같음 (text.embed)",
    "train_text_scratch.sh": "같음 (text.classify)",
}

# 오늘 Docker 데몬이 없어 **본실행을 못 한** 둘.
NOT_MEASURED_TODAY = ("regate.sh", "proof_ab.sh")


def _scripts() -> list[Path]:
    return sorted(SCRIPTS.glob("*.sh"))


def _callers() -> dict[str, list[str]]:
    texts = {name: (SCRIPTS / name).read_text(encoding="utf-8") for name in RUNNERS}
    texts["ci.yml"] = CI.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    for path in _scripts():
        out[path.name] = sorted(who for who, body in texts.items()
                                if who != path.name and path.name in body)
    return out


class TestEveryScriptIsCalledOrExplained(unittest.TestCase):
    def test_no_script_is_silently_unrun(self) -> None:
        """**여기가 핵심이다.** 게이트에 있어야 할 것이 빠져도 티가 안 난다."""
        called = _callers()
        self.assertTrue(called, "스크립트를 하나도 못 찾았다")
        orphan = sorted(name for name, who in called.items()
                        if not who and name not in WITHOUT_A_CALLER and name not in RUNNERS)
        self.assertEqual([], orphan, f"아무도 안 부르고 이유도 없는 스크립트: {orphan}")

    def test_the_manual_table_has_no_ghosts(self) -> None:
        names = {p.name for p in _scripts()}
        ghosts = sorted(n for n in WITHOUT_A_CALLER if n not in names)
        self.assertEqual([], ghosts, f"없는 스크립트를 해명하고 있다: {ghosts}")

    def test_manual_entries_are_not_actually_called(self) -> None:
        """불리게 됐는데 표에 남으면 「수동이다」가 거짓이 된다."""
        called = _callers()
        stale = sorted(n for n in WITHOUT_A_CALLER if called.get(n))
        self.assertEqual([], stale, f"이제 불리는데 수동으로 적혀 있다: {stale}")

    def test_every_reason_says_something(self) -> None:
        blank = sorted(n for n, why in WITHOUT_A_CALLER.items() if len(why.strip()) < 6)
        self.assertEqual([], blank, f"이유가 비었다: {blank}")


class TestUnrunScriptsAtLeastParse(unittest.TestCase):
    """아무도 안 돌리는 스크립트가 **깨져 있으면 아무도 모른다**."""

    def test_every_script_parses(self) -> None:
        bad = []
        for path in _scripts() + sorted((SCRIPTS / "lib").glob("*.sh")):
            proc = subprocess.run(["bash", "-n", str(path)],
                                  capture_output=True, text=True, timeout=60)
            if proc.returncode != 0:
                bad.append(f"{path.name}: {proc.stderr.strip()[:80]}")
        self.assertEqual([], bad, "문법 오류: " + "; ".join(bad))

    def test_enough_scripts_are_parsed(self) -> None:
        self.assertGreaterEqual(len(_scripts()), 30, f"{len(_scripts())}개만 봤다")


class TestTheTwoWeCouldNotRunSayWhy(unittest.TestCase):
    """「돌 것이다」로 적지 않는다 — 못 쟀으면 못 쟀다고 적는다."""

    def test_both_are_in_the_manual_table(self) -> None:
        for name in NOT_MEASURED_TODAY:
            with self.subTest(script=name):
                self.assertIn(name, WITHOUT_A_CALLER)
                self.assertIn("못 봤다", WITHOUT_A_CALLER[name])

    def test_they_state_their_precondition(self) -> None:
        for name in NOT_MEASURED_TODAY:
            with self.subTest(script=name):
                body = (SCRIPTS / name).read_text(encoding="utf-8")
                self.assertIn("docker compose up -d", body,
                              f"{name} 이 사전 조건을 안 적는다")


if __name__ == "__main__":
    unittest.main()
