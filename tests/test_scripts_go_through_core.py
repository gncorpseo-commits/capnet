r"""스크립트가 **Core 를 우회해 Node 를 부르지 않는가** (큐 #29).

## 왜 있는가

제품 주장의 한 줄이다 — 「사용자는 기기 주소를 모른다. 기기는 Core 가 배정하지 않은
실행을 거부한다.」 #200 이 그 주장을 **틀린 파일에 붙여 놓은 것**을 고쳤다.
이건 그 옆자리다 — **말이 아니라 스크립트가 실제로 무엇을 부르는가.**

전수했다 (2026-09-03).

| 무엇 | 수 |
|---|---|
| Node 주소를 **부르는** 스크립트 | **9** |
| 그중 **`/health` 만** 부르는 것 | **8** |
| **실행·claim 을 직접 부르는 것** | **1** — `smoke_w1.ps1` |

`/health` 는 준비 단계다 — 가중치 해시·`arch` 를 **그 기기의 증언**에서 뽑는다(운영자 몫).
남은 하나가 `POST $node/v1/execute` 와 `POST $core/v1/internal/claim` 을 직접 부른다.

**그건 결함이 아니다.** `README` 가 그 스크립트를 「**dummy 게이트 배관** + placeholder
추론」이라고 적는다 — 제품 경로가 아니라 **배관 smoke** 다. `main.py` 의 주석이
「이전에는 클라이언트가 claim 을 직접 호출하고 Node 에도 직접 접속했다」고 적는
바로 그 시절의 도구이고, 그 사실이 문서에 남아 있다.

**과장하지 않는다** — 「Core 우회 1건」이 아니라 「의도된 배관 smoke 하나」다.

## 무엇을 고정하나

`/health` 밖으로 Node 를 부르거나 `internal/claim` 을 부르는 스크립트는
아래 `PLUMBING` 에 **근거와 함께** 적혀 있어야 한다.
목록이 조용히 늘면 걸린다 — `test_every_route_declares_its_auth` 의 `PUBLIC` 과 같은 방식이다.

## 무엇을 고정하지 **않나**

`/health` 호출. 준비 단계에서 기기의 증언을 읽는 것은 정상이고,
막으면 `demo.sh` 가 가중치 해시를 어디서도 못 얻는다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# **URL 호출만** 잡는다 — 변수 뒤에 `/` 가 와야 한다.
#
# 처음 판은 `\$\{?(?:node|NODE_URL)\}?` 였고 여섯 자리를 오탐했다:
# `$node_id`(UUID 변수) · `"${node_port}:8001"`(compose 포트) ·
# `$core + $node`(SBOM 목록) · `\"$node\"`(JSON 본문의 node_id).
# **뒤에 `/` 를 요구하니 여섯이 한 번에 빠졌다** — 「Node 를 언급한다」와
# 「Node 를 부른다」는 다르다.
NODE_CALL = re.compile(r"\$\{?(?:node|NODE_URL)\}?/")
# 준비 단계에서 허용되는 유일한 Node 경로.
HEALTH_ONLY = re.compile(r"\$\{?(?:node|NODE_URL)\}?/health\b")
# Core 워커의 몫 — 스크립트가 부르면 그 시절의 배관이다.
CLAIM = re.compile(r"/v1/internal/claim\b")

# **제품 경로가 아닌 배관 도구.** 근거를 적어야 통과한다.
PLUMBING: dict[str, str] = {
    "smoke_w1.ps1": (
        "W1 배관 smoke — `README` 가 「dummy 게이트 배관 + placeholder 추론」이라 적는다. "
        "`main.py` 주석의 「이전에는 클라이언트가 claim 을 직접 호출하고 Node 에도 "
        "직접 접속했다」가 가리키는 그 시절의 도구다. 제품 경로는 `product_demo.sh`"
    ),
}


def _scripts() -> list[Path]:
    return sorted(p for p in SCRIPTS.iterdir() if p.suffix in (".sh", ".ps1"))


def _bypasses(path: Path) -> list[str]:
    """`/health` 밖으로 Node 를 부르거나 claim 을 부르는 줄."""
    hits: list[str] = []
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if CLAIM.search(line):
            hits.append(f"{i}: claim")
            continue
        if not NODE_CALL.search(line):
            continue
        # 주소를 **정의**하는 줄은 호출이 아니다 (`node="${NODE_URL:-…}"`).
        if re.match(r"""\s*(?:\$node\s*=|node=|export\s+NODE_URL=)""", line):
            continue
        if HEALTH_ONLY.search(line):
            continue
        hits.append(f"{i}: {stripped[:60]}")
    return hits


class TestOnlyDeclaredToolsBypassCore(unittest.TestCase):
    def test_no_undeclared_script_calls_the_node_directly(self) -> None:
        """**여기가 핵심이다.** 새 스크립트가 조용히 Node 를 직접 몰면 걸린다."""
        bad: list[str] = []
        for path in _scripts():
            hits = _bypasses(path)
            if hits and path.name not in PLUMBING:
                bad.append(f"{path.name} → {hits}")
        self.assertEqual(
            [], bad,
            "Core 를 우회해 Node·claim 을 직접 부른다 — 제품 경로면 Core 로 보내고, "
            f"배관 도구면 `PLUMBING` 에 근거와 함께 적는다: {bad}",
        )

    def test_no_ghost_in_the_plumbing_list(self) -> None:
        """더 이상 우회하지 않는 이름이 남으면 다음 사람이 「이건 원래 그런 거였지」로 넘어간다."""
        ghosts = sorted(
            name for name in PLUMBING
            if not (SCRIPTS / name).is_file() or not _bypasses(SCRIPTS / name)
        )
        self.assertEqual([], ghosts, f"목록에만 있는 배관 도구: {ghosts}")

    def test_every_entry_carries_a_reason(self) -> None:
        thin = sorted(n for n, why in PLUMBING.items() if len(why.strip()) < 30)
        self.assertEqual([], thin, f"근거가 너무 짧다: {thin}")

    def test_readme_names_it_as_plumbing(self) -> None:
        """근거가 `README` 를 인용한다. 그 문장이 사라지면 근거가 빈다."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("배관", readme, "README 가 배관 도구를 그렇게 부르지 않는다")
        for name in PLUMBING:
            with self.subTest(script=name):
                self.assertIn(name, readme, f"README 실행 스크립트 표에 {name} 이 없다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_found_scripts_that_touch_the_node(self) -> None:
        """훑기가 Node 를 부르는 스크립트를 **하나도 못 찾으면** 이 검사는 헛돈다."""
        touching = [p.name for p in _scripts()
                    if NODE_CALL.search(p.read_text(encoding="utf-8", errors="replace"))]
        self.assertGreater(len(touching), 5, f"Node 를 부르는 스크립트가 {touching}")

    def test_health_calls_are_not_flagged(self) -> None:
        """`/health` 를 막으면 `demo.sh` 가 가중치 해시를 어디서도 못 얻는다."""
        self.assertEqual([], _bypasses(SCRIPTS / "demo.sh"),
                         "준비 단계의 /health 호출을 우회로 센다")

    def test_detector_catches_a_direct_execute(self) -> None:
        """탐지기가 **아무것도 안 잡으면** 위 검사가 공허하다."""
        self.assertTrue(_bypasses(SCRIPTS / "smoke_w1.ps1"),
                        "알려진 배관 도구조차 못 잡는다 — 정규식이 눈멀었다")


if __name__ == "__main__":
    unittest.main()
