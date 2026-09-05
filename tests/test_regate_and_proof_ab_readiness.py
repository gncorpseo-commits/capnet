r"""`regate.sh` · `proof_ab.sh` — **무엇이 있어야 도는가** (배치 B #75 · `#254` 잔여).

## 왜 있는가

`#254`(큐 #63)는 둘을 「본실행 못 봄」으로 남겼다. `#268`(큐 #74)에서 데모 아홉에 같은
물음을 던졌더니 **막는 것이 Docker 하나뿐**이라는 답이 나왔다. 둘에도 물었다.

## 실측 (2026-09-06)

| 스크립트 | 필요한 것 | 저장소가 주는가 |
|---|---|---|
| `proof_ab.sh` | `eurosat_scratch` · `eurosat_scratch_b` 가중치 **둘** | ✅ 둘 다 있다 |
| | 살아 있는 스택 + `CAPNET_API_KEY` | ❌ Docker |
| `regate.sh` | `provenance_drift` 에 **라우팅 가능한 드리프트 행** | ❌ DB (그리고 **보통 0 이다**) |
| | 대상 Agent 의 `weights_sha256` 파일이 Node 에 | ❌ Docker |

**둘은 다르다.**

- `proof_ab` 는 **자료가 다 있다.** Docker 만 서면 돈다 — 데모 아홉과 같은 자리다.
- `regate` 는 **재현 자료를 만들 수 없다.** `clean_room` 이 「증적 드리프트 0」을 확인하는
  것이 정상이므로, 재게이트 대상이 **있으려면 골든셋을 실제로 교체**해야 한다.
  그건 Docker 가 있어도 **한 단계 더** 필요하다.

그래서 `regate` 는 「Docker 가 생기면 돈다」가 **아니다.** `--dry-run` 으로 「대상 0」을
확인하는 것까지가 현실적인 첫 걸음이고, 그 사실을 적어 둔다.

## 무엇을 고정하나

1. `proof_ab` 가 부르는 A·B 가중치가 **저장소에 있다** (하나라도 빠지면 못 돈다)
2. `regate` 에 **`--dry-run` 이 있다** — 대상 0 을 확인하는 유일한 무해한 첫 걸음
3. 둘 다 사전 조건을 **머리말에 적는다**
4. 세는 대상이 비지 않는다

## 무엇을 안 보나

**돌려 보지 않는다** (`docker info` 실패 · 규약 6). 「무엇이 있어야 도는가」만 답한다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
WEIGHTS = ROOT / "apps" / "node" / "weights"

SAFETENSORS = re.compile(r"([a-z0-9_]+\.safetensors)")


class TestProofAbHasItsMaterials(unittest.TestCase):
    """A/B 교차 실행은 **가중치 둘**이 있어야 한다 — 없으면 Docker 가 있어도 못 돈다."""

    def test_both_weights_are_in_the_repo(self) -> None:
        needs = SAFETENSORS.findall((SCRIPTS / "proof_ab.sh").read_text(encoding="utf-8"))
        self.assertTrue(needs, "proof_ab 이 가중치를 안 부른다")
        have = {p.name for p in WEIGHTS.glob("*.safetensors")}
        missing = sorted(set(needs) - have)
        self.assertEqual([], missing, f"저장소에 없는 가중치: {missing}")

    def test_it_names_two_distinct_weights(self) -> None:
        """하나만 부르면 그건 A/B 가 아니다."""
        needs = set(SAFETENSORS.findall((SCRIPTS / "proof_ab.sh").read_text(encoding="utf-8")))
        self.assertGreaterEqual(len(needs), 2, sorted(needs))


class TestRegateNeedsMoreThanDocker(unittest.TestCase):
    """재게이트 **대상**은 골든셋을 실제로 교체해야 생긴다 — 그래서 Docker 만으로 부족하다."""

    def test_it_has_a_dry_run(self) -> None:
        """대상 0 을 확인하는 **무해한 첫 걸음**이다. 없으면 첫 실행이 곧 본실행이다."""
        body = (SCRIPTS / "regate.sh").read_text(encoding="utf-8")
        self.assertTrue("--dry-run" in body, "regate.sh 에 --dry-run 이 없다")

    def test_it_reads_the_drift_view(self) -> None:
        body = (SCRIPTS / "regate.sh").read_text(encoding="utf-8")
        self.assertIn("provenance_drift", body,
                      "regate 가 드리프트 뷰를 안 본다 — 대상 판정 근거가 바뀌었다")

    def test_the_clean_room_expects_zero_drift(self) -> None:
        """`clean_room` 이 「드리프트 0」을 확인한다 — 그래서 재게이트 대상이 **보통 없다**."""
        body = (SCRIPTS / "clean_room.sh").read_text(encoding="utf-8")
        self.assertIn("증적 드리프트 0", body,
                      "clean_room 이 드리프트 0 을 안 본다 — 이 절의 전제가 바뀌었다")


class TestBothStateTheirPreconditions(unittest.TestCase):
    def test_each_says_what_it_needs(self) -> None:
        for name in ("regate.sh", "proof_ab.sh"):
            with self.subTest(script=name):
                body = (SCRIPTS / name).read_text(encoding="utf-8")
                self.assertIn("docker compose up -d", body,
                              f"{name} 이 사전 조건을 안 적는다")

    def test_they_are_still_run_by_nobody(self) -> None:
        """누가 돌리기 시작하면 이 절의 「못 봄」이 거짓이 된다 (`#254` 와 이어진다)."""
        # **말하는 문장은 호출이 아니다.** `sanity.sh` 는 `echo` 로 「A/B 교체는
        # scripts/proof_ab.sh」라고 안내한다 — 그걸 호출로 세면 거짓 결함이 된다
        # (`#220` 이후 이 회차에 네 번째다). `bash …` 로 **실행하는** 줄만 본다.
        run = re.compile(r"(?:^|[;&|]|\$\()\s*(?:bash|sh)\s+[^\n]*scripts/(?:regate|proof_ab)\.sh")
        callers = []
        for path in SCRIPTS.glob("*.sh"):
            if path.name in ("regate.sh", "proof_ab.sh"):
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith(("#", "echo", "printf")):
                    continue
                if run.search(line):
                    callers.append(path.name)
        self.assertEqual([], sorted(set(callers)), f"이제 누가 부른다: {sorted(set(callers))}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_both_scripts_exist(self) -> None:
        for name in ("regate.sh", "proof_ab.sh"):
            with self.subTest(script=name):
                self.assertTrue((SCRIPTS / name).is_file())

    def test_the_weight_reader_works(self) -> None:
        self.assertIn("eurosat_scratch_b.safetensors",
                      SAFETENSORS.findall((SCRIPTS / "proof_ab.sh").read_text(encoding="utf-8")))
        self.assertEqual([], SAFETENSORS.findall("no weights here"))


if __name__ == "__main__":
    unittest.main()
