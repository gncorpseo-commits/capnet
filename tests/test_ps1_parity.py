r"""동명 `*.sh` ↔ `*.ps1` 이 **같은 입력을 받는가** (큐 #53 · `#206` 재전수).

## 왜 있는가

README 는 「**Windows** — 동명 `.ps1`」이라고 적는다. **동명인데 동작이 달랐다** —
`#206` 이 주소(`CORE_URL`·`NODE_URL`)에서 그걸 잡았다. 이번에는 **입력 이름과 기본값**을
다시 훑었다.

## 실측 (2026-09-05)

| 무엇 | 수 |
|---|---|
| `.ps1` | **11** |
| 동명 `.sh` 가 있는 것 | **10** (`smoke_w1` 만 `.ps1` 단독) |
| 입력 이름·기본값이 맞는 쌍 | **9** |
| **어긋난 쌍** | **1** — `score_n300` |

### 어긋난 것 둘 — 같은 뿌리

**① `score_n300.ps1` 에는 `GOLDEN` 이 없었다.**

`.sh` 는 `GOLDEN=…` 으로 **홀드아웃**을 잰다 (주석에 그 용례가 적혀 있다).
`.ps1` 은 `data\golden-n300` 이 박혀 있었다 — Windows 에서는 홀드아웃을 **못 잰다.**
`STATE` 가 홀드아웃 숫자를 적는데 심사자가 그걸 재현할 방법이 한쪽에만 있었다.

**② 산출물 이름이 갈렸고, `compare_ab` 는 옛 이름을 기본값으로 들고 있었다.**

```text
score_n300.sh  → artifacts/score-n300-eurosat_scratch-golden-n300.json
score_n300.ps1 → artifacts/score-n300-eurosat_scratch.json          (골든셋 이름 없음)
compare_ab.*   기본값: artifacts/score-n300-eurosat_scratch.json    ← .sh 산출물과 안 맞는다
```

즉 **bash 에서 문서대로 돌리면** `score_n300.sh` → `compare_ab.sh` 가
`missing … — run score_n300.sh first` 로 끝났다. 방금 돌린 그 스크립트를 다시 돌리라고
말하는 것이다. 셋을 한 이름으로 맞췄다.

## 무엇을 고정하나

1. `.ps1` 의 `param()` 이름이 동명 `.sh` 의 입력 변수와 **대응**한다
2. 그 **기본값이 같다**
3. `compare_ab` 의 기본 입력이 `score_n300` 의 **기본 산출물 이름과 같다** (양쪽 다)

## 못 쟀다

**`.ps1` 을 돌리지 못했다** — 이 환경에 `pwsh` 가 없다 (`#206` 과 같은 조건).
고친 줄은 같은 파일이 이미 쓰는 문법(`param([string]$X = "…")` · `Split-Path -Leaf`)
그대로다. 문자열 정합은 아래 검사가 **양쪽 소스에서 뽑아** 대조한다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# `.ps1` param ↔ `.sh` 환경변수. 이름 규약이 다르므로 여기서 잇는다.
PARAM_MAP = {
    "compare_ab": {"ScoreA": "SCORE_A", "ScoreB": "SCORE_B",
                   "MaxDeviation": "MAX_DEVIATION", "MinN": "MIN_N"},
    "score_n300": {"Weights": "WEIGHTS", "OutName": "OUT_NAME", "Golden": "GOLDEN"},
    "train_scratch": {"Arch": "ARCH", "OutName": "OUT_NAME", "ExtraEpochs": "EXTRA_EPOCHS"},
}

PS_PARAM = re.compile(r"\[\s*(?:string|int|double|switch)\s*\]\s*\$(\w+)\s*=\s*(.+?)\s*(?:,|\)\s*$)",
                      re.M)
SH_DEFAULT = re.compile(r'^\s*(?:[a-z_]+|[A-Z_]+)="\$\{([A-Z_]+):-(.*?)\}"', re.M)


def pairs() -> list[tuple[str, Path, Path]]:
    out = []
    for ps in sorted(SCRIPTS.glob("*.ps1")):
        sh = SCRIPTS / f"{ps.stem}.sh"
        if sh.is_file():
            out.append((ps.stem, sh, ps))
    return out


def ps_params(path: Path) -> dict[str, str]:
    """`param( … )` 블록만 읽는다.

    첫 `)` 로 자르면 **주석 안의 괄호**에서 끊긴다 — `(큐 #53)` 하나에 걸려
    그 뒤 파라미터를 통째로 못 봤다. 닫는 `)` 만 있는 줄에서 끝낸다.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip().startswith("param("))
    except StopIteration:
        return {}
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == ")"), len(lines))
    head = "\n".join(lines[start:end]) + "\n)"
    return {m.group(1): m.group(2).strip().strip('"') for m in PS_PARAM.finditer(head)}


def sh_defaults(path: Path) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in SH_DEFAULT.finditer(path.read_text(encoding="utf-8"))}


class TestSameInputsOnBothPlatforms(unittest.TestCase):
    def test_every_mapped_param_exists_on_both_sides(self) -> None:
        for stem, sh, ps in pairs():
            if stem not in PARAM_MAP:
                continue
            got_ps, got_sh = ps_params(ps), sh_defaults(sh)
            for ps_name, sh_name in PARAM_MAP[stem].items():
                with self.subTest(script=stem, param=ps_name):
                    self.assertIn(ps_name, got_ps, f"{ps.name} 에 -{ps_name} 이 없다")
                    self.assertIn(sh_name, got_sh, f"{sh.name} 에 {sh_name} 이 없다")

    def test_defaults_agree_where_they_are_plain_values(self) -> None:
        """기본값이 갈리면 **같은 명령이 다른 결과**를 낸다."""
        bad = []
        for stem, sh, ps in pairs():
            if stem not in PARAM_MAP:
                continue
            got_ps, got_sh = ps_params(ps), sh_defaults(sh)
            for ps_name, sh_name in PARAM_MAP[stem].items():
                a, b = got_ps.get(ps_name, ""), got_sh.get(sh_name, "")
                if "$" in a or "$" in b or not a or not b:
                    continue                      # 계산해서 만드는 기본값은 아래에서 따로 본다
                if a.replace("\\", "/") != b.replace("\\", "/"):
                    bad.append(f"{stem}.{ps_name}: ps1={a!r} sh={b!r}")
        self.assertEqual([], bad, "기본값이 갈린다: " + "; ".join(bad))


class TestTheAbChainFindsItsOwnArtifacts(unittest.TestCase):
    """`score_n300` 이 쓴 파일을 `compare_ab` 가 **기본값으로** 찾아야 한다."""

    def _score_default_name(self, weights_stem: str) -> str:
        sh = (SCRIPTS / "score_n300.sh").read_text(encoding="utf-8")
        golden = re.search(r'golden="\$\{GOLDEN:-\$root/(.+?)\}"', sh)
        self.assertIsNotNone(golden, "score_n300.sh 에서 GOLDEN 기본값을 못 읽었다")
        assert golden is not None
        return f"score-n300-{weights_stem}-{Path(golden.group(1)).name}.json"

    def test_compare_ab_sh_defaults_match(self) -> None:
        got = sh_defaults(SCRIPTS / "compare_ab.sh")
        self.assertEqual(f"artifacts/{self._score_default_name('eurosat_scratch')}",
                         got.get("SCORE_A"))
        self.assertEqual(f"artifacts/{self._score_default_name('eurosat_scratch_b')}",
                         got.get("SCORE_B"))

    def test_compare_ab_ps1_defaults_match(self) -> None:
        got = ps_params(SCRIPTS / "compare_ab.ps1")
        self.assertEqual(f"artifacts/{self._score_default_name('eurosat_scratch')}",
                         got.get("ScoreA"))

    def test_score_ps1_names_the_golden_set_too(self) -> None:
        """이름에 골든셋이 안 들어가면 홀드아웃 결과가 **기본 결과를 덮어쓴다**."""
        body = (SCRIPTS / "score_n300.ps1").read_text(encoding="utf-8")
        self.assertIn("Split-Path -Leaf $golden", body,
                      "score_n300.ps1 의 기본 산출물 이름에 골든셋이 없다")

    def test_score_ps1_takes_a_golden_path(self) -> None:
        body = (SCRIPTS / "score_n300.ps1").read_text(encoding="utf-8")
        self.assertIn("$golden = Join-Path $root $Golden", body,
                      "score_n300.ps1 이 골든셋 경로를 박아 두고 있다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_pairs_are_seen(self) -> None:
        self.assertGreaterEqual(len(pairs()), 9, [p[0] for p in pairs()])

    def test_the_ps1_only_script_is_known(self) -> None:
        """짝이 없는 것을 「맞다」고 세면 표가 거짓이 된다."""
        alone = sorted(p.stem for p in SCRIPTS.glob("*.ps1")
                       if not (SCRIPTS / f"{p.stem}.sh").is_file())
        self.assertEqual(["smoke_w1"], alone, f"짝 없는 .ps1 이 바뀌었다: {alone}")

    def test_parsers_read_something(self) -> None:
        self.assertGreaterEqual(len(ps_params(SCRIPTS / "score_n300.ps1")), 3)
        self.assertGreaterEqual(len(sh_defaults(SCRIPTS / "score_n300.sh")), 3)


if __name__ == "__main__":
    unittest.main()
