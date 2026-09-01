"""테스트를 건너뛰는 **사유**는 허가된 것만 쓴다.

## 왜 있는가

**`skip` 은 통과가 아니다.** 그런데 출력에서는 통과처럼 보인다 — `OK (skipped=7)`.

**실제로 가려졌다 (2026-09-01).** 세션 도중 환경이 바뀌어 `node` 가 사라졌고,
`capreq` 스위트가 **68 → 50 ran / 6 skipped** 로 줄었다. 줄어든 6건은
`chat.html` 렌더러와 흐름을 **실제로 실행**하는 프로브 — 이 저장소가
「문자열 검사로는 반쯤 지운 렌더러를 못 잡는다」고 판단해 일부러 넣은 것들이다.
아무 경고도 없었다. **가장 값나가는 검사가 조용히 빠져 있었다.**

## 무엇을 하나

사유 문자열을 **허가 목록**으로 만든다. 새 `skip` 을 넣으려면 사유를 여기 적어야 한다 —
그때 「이건 환경 문제인가, 아니면 깨진 검사를 덮는 것인가」를 한 번 묻게 된다.

`testing.md` §4.6 이 이미 글로 정한 규칙(「이 부류를 늘릴 때의 규칙」)을 기계가 잇는 것이다.

## 무엇을 안 하나

- **개수를 못박지 않는다.** 몇 건이 건너뛰어지는지는 환경마다 다르다 — 그게 정상이다.
  못박으면 psycopg 가 있는 환경에서 거짓 실패가 난다
- **`skip` 자체를 금지하지 않는다.** 「의존성 설치 없음」을 지키는 수단이라 필요하다
- 텍스트로 훑지 않는다 — `ast` 로 **호출**만 본다. 설명 문단에 `skip` 이라 적었다고
  걸리면 안 된다 (`tests/_srcguard.py` 의 사고 5건)
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREES = (ROOT / "tests", ROOT / "capreq" / "tests")

SKIP_CALLS = {"skip", "skipIf", "skipUnless", "skipTest"}

# 사유 → **왜 건너뛰어도 되는가**. 새 줄을 넣기 전에 이 물음에 답한다:
#   「이건 그 환경에 없는 것인가, 아니면 깨진 검사를 덮는 것인가?」
ALLOWED = {
    "psycopg 없음 — 의존성 있는 환경에서만 돈다":
        "루트 `run_tests` 의 「의존성 설치 없음」을 지킨다. CI 의 migrate 잡에서는 실제로 돈다.",
    "capreq 를 못 읽었다":
        "`route_bench` 하네스 검사는 capreq 를 import 한다. 별 모듈이라 없을 수 있다.",
    "node 가 없다 — 렌더러 실행 검사를 건너뛴다":
        "`chat.html` 을 최소 DOM 스텁으로 실행한다. CI 의 capreq 잡에는 setup-node 가 있다.",
    "node 가 없다 — 흐름 실행 검사를 건너뛴다":
        "위와 같다 — 보내기→라우팅→폴링→결과 경로 전체.",
}


def skip_reasons() -> list[tuple[str, int, str]]:
    """`(파일, 줄, 사유)` — `ast` 로 호출만 본다."""
    found: list[tuple[str, int, str]] = []
    for tree_root in TREES:
        for path in sorted(tree_root.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # 문법이 깨졌으면 다른 검사가 잡는다
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                if name not in SKIP_CALLS:
                    continue
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.append((str(path.relative_to(ROOT)), node.lineno, arg.value))
    return found


class TestSkipReasonsAreDeclared(unittest.TestCase):
    def test_every_reason_is_allowed(self) -> None:
        """허가 목록에 없는 사유 — 「환경이 없다」가 아니라 「검사를 덮었다」일 수 있다."""
        unknown = [(f, ln, r) for f, ln, r in skip_reasons() if r not in ALLOWED]
        self.assertEqual(
            unknown, [],
            "허가되지 않은 skip 사유. 환경 문제가 맞으면 ALLOWED 에 **왜 괜찮은지**와 함께 적는다: "
            f"{unknown}",
        )

    def test_no_dead_entries(self) -> None:
        """안 쓰이는 사유가 남으면 목록이 곧 낡는다 — 지운 검사의 흔적이다."""
        used = {r for _f, _ln, r in skip_reasons()}
        dead = sorted(set(ALLOWED) - used)
        self.assertEqual(dead, [], f"아무도 안 쓰는 사유 {len(dead)}개 — 지운다: {dead}")

    def test_probe_actually_finds_things(self) -> None:
        """0건을 훑으며 통과하는 상태를 막는다 — 파서가 조용히 죽으면 이 검사가 무의미하다."""
        found = skip_reasons()
        self.assertGreater(len(found), 5, f"skip 호출을 {len(found)}개밖에 못 찾았다")
        self.assertGreaterEqual(len({f for f, _ln, _r in found}), 3, "한 파일에서만 찾았다")


if __name__ == "__main__":
    unittest.main()
