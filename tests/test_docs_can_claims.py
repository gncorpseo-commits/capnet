"""`README` · 사용자 가이드가 「할 수 있다」고 적은 것이 **실물과 이어지는가**.

## 왜 있는가

측정 숫자는 이미 전수했다 (`test_shoot_docs` · `test_doc_counts` — 마이그레이션 세대,
`acc=`). 남아 있던 것은 **서술형 주장**이다: 「이 스크립트에는 기기 주소가 없다」,
「이 명령을 치면 이렇게 나온다」, 「이 형식은 안 받는다」. 숫자가 아니라 **문장**이라
아무도 안 보고 있었다.

전수해 보니 **한 종이 어긋나 있었다.**

    README     「`scripts/demo.sh` 어디에도 기기 주소가 없다」
    실물        scripts/demo.sh:8   node="${NODE_URL:-http://127.0.0.1:8001}"
                scripts/demo.sh:13  ccurl -sf "$node/health"

거짓이었다. `demo.sh` 는 **준비 단계에서 Node 를 직접 부른다** — 가중치 해시와 `arch`
를 그 기기의 증언에서 뽑기 때문이고, 그건 운영자 몫이라 정상이다. 기기 주소가 정말로
한 줄도 없는 것은 `product_demo.sh` 쪽이다 (실측 0건).

**심사위원은 README 를 그대로 따라 한다.** 「어디에도 없다」고 적힌 파일을 열어 8행에서
`8001` 을 보면, 그 순간 다른 주장도 같이 의심받는다. 그래서 이 검사는 **문장을 읽고
그 문장이 이름을 부른 파일을 실제로 재는** 방식으로 만들었다.

## 무엇을 고정하나

1. **「기기 주소가 없다」의 대상** — 문서가 이름을 부른 스크립트는 Node 주소 참조가 0건
2. **부르는 것이 실재하는가** — 스크립트 · 라우트 · 강제 플래그 · 상대 링크
3. **거절한다고 적은 것이 실제로 거절하는가** — 403 문구 · 오버레이 넷 · 형식 계약
4. **고정 개수** — `demo_violations` 6건은 SQL 의 `REJECTED` 통지 수와 같아야 한다

## 무엇을 고정하지 **않나**

문장 자체의 표현. 문서는 다시 쓰인다 — 검사가 문체를 붙잡으면 사람이 검사를 피해
쓰게 된다. 여기서는 **이름을 부른 대상**과 **실물**만 대조한다.

## 스캐너 한계 (적어 둔다)

`grep` 은 주석 안의 주소와 진짜 호출을 구분하지 못한다. 그래서 2번 항목은 「참조 0건」
이라는 **더 센 조건**으로 잡는다 — 주석에라도 주소가 있으면 「어디에도 없다」는 못 쓴다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GUIDE = ROOT / "docs" / "guide" / "user-guide-ko.md"
CORE = ROOT / "apps" / "core" / "app" / "main.py"
NODE = ROOT / "apps" / "node" / "app" / "main.py"

# Node 를 지목하는 흔적. 포트도 환경변수도 둘 다 본다 — 하나만 보면 다른 쪽으로 샌다.
_NODE_ADDR = re.compile(r"NODE_URL|:800[1-9]\b|\$node\b|\$\{node\}")

# 「… 어디에도 기기 주소가 없다」에서 **이름 불린 스크립트**를 뽑는다.
_NO_ADDR_CLAIM = re.compile(r"`(?:scripts/)?([A-Za-z0-9_.-]+\.(?:sh|ps1))`[^\n]{0,40}어디에도 기기 주소가 없다")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class TestNoDeviceAddressClaim(unittest.TestCase):
    """「어디에도 기기 주소가 없다」 — 그 문장이 부른 파일을 **연다**."""

    def test_claim_is_made_somewhere(self) -> None:
        """주장이 사라지면 이 검사는 아무것도 안 지킨다 — 공허한 통과를 막는다."""
        self.assertTrue(
            _NO_ADDR_CLAIM.search(_read(README)),
            "README 에 「어디에도 기기 주소가 없다」 주장이 없다 — 검사가 헛돈다",
        )

    def test_named_script_really_has_none(self) -> None:
        for doc in (README, GUIDE):
            text = _read(doc)
            for m in _NO_ADDR_CLAIM.finditer(text):
                name = m.group(1)
                script = ROOT / "scripts" / name
                self.assertTrue(script.is_file(), f"{doc.name} 이 없는 {name} 를 부른다")
                hits = [
                    f"{i}: {ln.strip()}"
                    for i, ln in enumerate(_read(script).splitlines(), 1)
                    if _NODE_ADDR.search(ln)
                ]
                self.assertEqual(
                    [], hits,
                    f"{doc.name} 은 {name} 에 「기기 주소가 없다」고 적는데 실제로 있다:\n"
                    + "\n".join(hits),
                )

    def test_demo_sh_is_not_the_one_claimed(self) -> None:
        """`demo.sh` 는 준비 단계에서 Node `/health` 를 본다 — 그게 정상이고, 그래서 이름을 못 준다.

        실물이 바뀌어 정말로 주소가 없어지면 이 검사가 실패한다. 그때는 문서에 이름을
        되돌리고 이 검사를 지우면 된다 — **실물이 먼저이고 문서가 따라간다.**
        """
        demo = _read(ROOT / "scripts" / "demo.sh")
        self.assertTrue(
            _NODE_ADDR.search(demo),
            "demo.sh 에 기기 주소가 없어졌다 — README 문장과 이 검사를 같이 고친다",
        )


class TestReferencedThingsExist(unittest.TestCase):
    """문서가 부르는 것이 **실재하는가.**"""

    def test_scripts_exist(self) -> None:
        pat = re.compile(r"`?scripts/([A-Za-z0-9_.-]+\.(?:sh|ps1|py))`?")
        missing: list[str] = []
        for doc in (README, GUIDE):
            for m in pat.finditer(_read(doc)):
                rel = f"scripts/{m.group(1)}"
                if not (ROOT / rel).is_file() and rel not in missing:
                    missing.append(f"{doc.name} -> {rel}")
        self.assertEqual([], missing, "문서가 없는 스크립트를 부른다: " + ", ".join(missing))

    def test_relative_links_resolve(self) -> None:
        pat = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        broken: list[str] = []
        for doc in (README, GUIDE):
            for m in pat.finditer(_read(doc)):
                target = m.group(1).split("#")[0]
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (doc.parent / target).resolve().exists():
                    broken.append(f"{doc.name} -> {target}")
        self.assertEqual([], broken, "깨진 링크: " + ", ".join(broken))

    def test_routes_exist(self) -> None:
        """README 가 `curl` 로 치라고 적은 경로는 코드에 있어야 한다."""
        core, node = _read(CORE), _read(NODE)
        for route in ("/v1/nodes-liveness", "/v1/ops/work-units", "/v1/inputs", "/v1/tasks"):
            self.assertIn(f'"{route}"', core, f"Core 에 {route} 가 없다")
        self.assertIn('"/v1/execute"', node, "Node 에 /v1/execute 가 없다")

    def test_enforcement_flags_exist(self) -> None:
        core = _read(CORE)
        for flag in ("REQUIRE_API_KEY", "REQUIRE_NODE_CREDENTIAL"):
            self.assertIn(f'os.environ.get("{flag}"', core, f"{flag} 를 읽는 코드가 없다")
            self.assertIn(flag, _read(README), f"README 가 {flag} 를 말하지 않는다")


class TestRejectionClaims(unittest.TestCase):
    """「거절된다」고 적은 것이 **실제로 거절하는가.**"""

    def test_403_message_matches_node(self) -> None:
        """README 는 403 본문을 **인용**한다. 문구가 갈리면 심사위원이 「다른 오류」로 읽는다."""
        m = re.search(r'HTTP 403\s+"([^"]+)"', _read(README))
        self.assertIsNotNone(m, "README 의 403 예상 출력이 없다")
        assert m is not None
        self.assertIn(m.group(1), _read(NODE), "README 가 인용한 403 문구가 Node 코드에 없다")

    def test_prod_overlay_flips_all_four(self) -> None:
        """README 는 오버레이가 **넷**을 뒤집는다고 적는다. 실물을 연다."""
        prod = _read(ROOT / "compose.prod.yaml")
        self.assertIn('REQUIRE_API_KEY: "1"', prod, "관리 API 인증을 안 켠다")
        self.assertIn('REQUIRE_NODE_CREDENTIAL: "1"', prod, "Node 증서를 안 켠다")
        self.assertIn("ports: !override []", prod, "postgres 를 호스트에서 안 뗀다")
        self.assertIn("CAPNET_AUTO_MIGRATE: ${CAPNET_AUTO_MIGRATE:-0}", prod,
                      "마이그레이션 자동 적용을 안 끈다")

    def test_undeclared_input_contract_is_refused(self) -> None:
        """가이드 §5.1 — 「과목이 정해 두지 않았으면 파일을 아예 받지 않습니다」."""
        inputs = _read(ROOT / "apps" / "core" / "app" / "inputs.py")
        self.assertIn("if allowed is None:", inputs, "형식 미선언을 통과시킨다")
        self.assertIn("업로드를 받지 않는다", inputs)
        self.assertIn("과목이 받겠다고 한 것만", _read(GUIDE), "가이드가 그 규칙을 안 적었다")

    def test_case_number_path_is_image_only(self) -> None:
        """가이드 §5.1 — 「번호를 고른다」는 **사진 과목에만**.

        allowlist 가 늘면 그 문장이 거짓이 된다. 늘리는 것 자체는 막지 않는다 —
        **문서를 같이 고치게** 만든다.
        """
        allow = _read(ROOT / "apps" / "core" / "app" / "allowlist.py")
        ids = set(re.findall(r'"([a-z0-9-]+)"', allow.split("ALLOWED_DATASET_IDS")[1].split("\n")[0]))
        self.assertEqual({"eurosat-rgb"}, ids,
                         "번호 경로가 사진 밖으로 늘었다 — user-guide §5.1 을 같이 고친다")
        self.assertIn("사진 과목에만", _read(GUIDE))


class TestFixedCounts(unittest.TestCase):
    """자라지 않는 개수만 못박는다 (`test_doc_counts` 규율)."""

    def test_violation_demo_count(self) -> None:
        sql = _read(ROOT / "scripts" / "demo_violations.sql")
        n = len(re.findall(r"RAISE NOTICE 'TEST\d+ REJECTED", sql))
        self.assertIn(f"**{n}건**", _read(README),
                      f"README 의 REJECTED 건수가 실물({n})과 다르다")
        self.assertIn(f"expect {n} REJECTED", _read(ROOT / "scripts" / "demo_violations.sh"),
                      f"demo_violations.sh 의 안내가 실물({n})과 다르다")

    def test_pg_violations_kinds(self) -> None:
        """README 「위반 14종 실측」 — 표 행 수와 같아야 한다."""
        doc = _read(ROOT / "docs" / "error" / "pg-violations.md")
        rows = len(re.findall(r"^\|\s*\d+\s*\|", doc, re.M))
        self.assertIn(f"위반 {rows}종 실측", _read(README),
                      f"README 의 위반 종수가 표 행 수({rows})와 다르다")


if __name__ == "__main__":
    unittest.main()
