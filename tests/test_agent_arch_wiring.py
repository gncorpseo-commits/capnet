"""Agent 를 등록하는 스크립트가 `arch` 를 싣는지 본다 (G5).

## 왜 있는가

`POST /v1/agents` 가 `arch` 를 요구하게 바꾸면서 **셸 스크립트 넷은 고치고 PowerShell 둘을
놓쳤다** (`demo.ps1` · `smoke_w1.ps1`). 리눅스에서 도는 검증 3종은 `.sh` 만 만지므로
그 누락이 **아무 검사에도 안 걸렸다.** 촬영은 Windows 에서 한다 — 촬영일에 HTTP 400 을
만났을 것이다.

같은 종류의 누락(«한쪽 계열만 고침»)은 또 생긴다. 그래서 텍스트로 고정한다.

## 판정 방식과 그 한계

`POST …/v1/agents` 를 부르는 파일에 `arch` 가 **한 번도 없으면** 실패로 본다.
셸·PowerShell 을 파싱하지 않는 **느슨한 검사**다 — 「같은 파일 안에 arch 가 있지만
다른 요청에 실려 있는」 경우는 못 잡는다. 그래도 이번에 놓친 것은 정확히 이 모양이었고,
파서를 정교하게 만드는 비용보다 값이 크다고 봤다.

`/v1/agents/{id}/bindings` 는 등록이 아니므로 대상이 아니다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# POST 대상이 /v1/agents 자체인 줄만 (뒤에 /bindings 같은 게 붙으면 제외)
POST_AGENTS = re.compile(r'/v1/agents(?![/\w])')

# 일부러 불완전한 본문을 보내는 곳. 이유를 여기 적지 않으면 예외로 두지 않는다.
EXEMPT = {
    # 「무인증 Agent 등록 → 401」을 보는 검사다. 인증이 arch 검사보다 먼저 도는 것이
    # 요점이므로(G5), 본문은 최소로 둔다. 여기에 arch 를 넣으면 검사의 뜻이 흐려진다.
    "prod_room.sh",
}


def registering_scripts() -> list[Path]:
    out = []
    for path in sorted(SCRIPTS.glob("*.sh")) + sorted(SCRIPTS.glob("*.ps1")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if POST_AGENTS.search(line) and (
                "-X POST" in line or "-Method Post" in line
            ):
                out.append(path)
                break
    return out


class AgentArchWiring(unittest.TestCase):
    def test_registering_scripts_declare_arch(self) -> None:
        missing = [
            p.name
            for p in registering_scripts()
            if p.name not in EXEMPT
            and "arch" not in p.read_text(encoding="utf-8", errors="replace")
        ]
        self.assertEqual(
            missing, [], f"arch 없이 Agent 를 등록하는 스크립트: {missing} (G5 → HTTP 400)"
        )

    def test_both_families_are_covered(self) -> None:
        """`.sh` 만 보고 통과하는 상태를 막는다 — 이번 누락이 정확히 그거였다."""
        names = [p.name for p in registering_scripts()]
        self.assertTrue(any(n.endswith(".sh") for n in names), names)
        self.assertTrue(any(n.endswith(".ps1") for n in names), names)

    def test_finder_actually_finds_things(self) -> None:
        self.assertGreaterEqual(len(registering_scripts()), 5)

    def test_exemptions_still_exist(self) -> None:
        """예외 목록이 낡아 조용히 무의미해지는 것을 막는다."""
        found = {p.name for p in registering_scripts()}
        stale = sorted(EXEMPT - found)
        self.assertEqual(stale, [], f"예외로 적힌 스크립트가 더는 등록하지 않는다: {stale}")


if __name__ == "__main__":
    unittest.main()
