"""최소 UI 가 지켜야 하는 것 — 화면은 못 눌러 봐도 **불변식은 볼 수 있다**.

## 왜 텍스트로 보나

브라우저가 CI 에 없고, 단위 잡은 의존성 0 이다(헤드리스 브라우저를 못 쓴다).
그래서 **눌러서 되는지**는 못 본다. 대신 **되면 안 되는 것**을 본다 —
소진 화면이 관리 키를 만지는지, 등급 입력칸이 생겼는지, 키가 URL 로 새는지.
이 셋은 텍스트로 판별되고, 셋 다 **정책 위반**이다.

## 무엇을 고정하나

1. **소진 화면은 관리 키를 만지지 않는다** — 초대 토큰이 인증이다. `api(` 도 쓰지 않는다
2. **소진 화면에 등급·조직·티어 입력칸이 없다** — 초대장이 정한다 (절대규칙 4)
3. **키가 URL 에 실리지 않는다** — 쿼리스트링은 서버 로그·기록·Referer 로 샌다
4. **외부 자산이 없다** — 내부망·오프라인에서 그대로 떠야 한다
5. 키는 `sessionStorage` 에만 둔다 — `localStorage` 를 쓰지 않는다 (탭 닫으면 사라진다)
6. 모든 페이지가 공용 `app.js` 를 쓰고, 헬퍼를 다시 정의하지 않는다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "apps" / "core" / "app" / "static"
PAGES = sorted(STATIC.glob("*.html"))
REDEEM = STATIC / "redeem.html"
APP_JS = STATIC / "app.js"


def text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def code(p: Path) -> str:
    """`//` 줄 주석을 뺀 본문.

    주석에는 「왜 그걸 안 쓰는지」가 적힌다 — 그 설명 문구를 위반으로 잡으면
    설명을 지워야 통과하는 검사가 된다. 실제로 한 번 그렇게 걸렸다.
    """
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in text(p).splitlines())


class UiInvariants(unittest.TestCase):
    def test_pages_exist(self) -> None:
        names = {p.name for p in PAGES}
        self.assertLessEqual(
            {"nodes.html", "call.html", "invite.html", "redeem.html"}, names, names
        )
        self.assertTrue(APP_JS.is_file())

    def test_redeem_never_touches_admin_key(self) -> None:
        """소진은 관리 키 없이 되는 유일한 경로다 — 화면이 키를 만지면 안 된다."""
        s = code(REDEEM)
        for bad in ("CapNet-Key", "mountKeyBar", "getKey(", "sessionStorage", "apiKey"):
            self.assertNotIn(bad, s, f"redeem.html 이 관리 키를 만진다: {bad}")
        self.assertIn("apiInvite(", s)
        # `api(` 는 키를 붙이는 래퍼다. 소진 화면에서는 쓰지 않는다.
        self.assertIsNone(
            re.search(r"[^a-zA-Z]api\(", s), "redeem.html 이 키 붙는 api() 를 쓴다"
        )

    def test_redeem_has_no_grade_inputs(self) -> None:
        """등급·조직·티어는 초대장이 정한다. 화면에 입력칸이 있으면 주장할 자리가 생긴다."""
        s = text(REDEEM)
        forms = re.findall(r"<(?:input|select)\b[^>]*>", s)
        blob = " ".join(forms)
        for bad in ("trust_domain", "org_id", "compute_tier", "r-domain", "r-org", "r-tier"):
            self.assertNotIn(bad, blob, f"소진 화면에 {bad} 입력칸이 있다")

    def test_key_never_in_url(self) -> None:
        for p in PAGES + [APP_JS]:
            s = text(p)
            self.assertIsNone(
                re.search(r"[?&](key|api_key|apiKey|token)=", s),
                f"{p.name}: 키·토큰이 쿼리스트링에 실린다",
            )

    def test_no_external_assets(self) -> None:
        """외부 자산(CDN·폰트)을 쓰지 않는다 — 내부망·오프라인에서 그대로 뜬다."""
        for p in PAGES:
            for m in re.findall(r'(?:src|href)="([^"]+)"', text(p)):
                self.assertFalse(
                    m.startswith(("http://", "https://", "//")),
                    f"{p.name}: 외부 자산 {m}",
                )

    def test_key_lives_in_session_storage_only(self) -> None:
        s = code(APP_JS)
        self.assertIn("sessionStorage.", s)
        self.assertNotIn("localStorage.", s, "localStorage 는 탭을 닫아도 남는다")

    def test_pages_share_one_helper(self) -> None:
        """헬퍼를 페이지마다 다시 정의하면 한쪽만 고쳐지는 일이 생긴다."""
        for p in PAGES:
            s = text(p)
            self.assertIn('src="/ui/app.js"', s, f"{p.name}: app.js 를 안 쓴다")
            self.assertNotIn("async function api(", s, f"{p.name}: api() 를 다시 정의한다")

    def test_finder_actually_finds_things(self) -> None:
        self.assertGreaterEqual(len(PAGES), 4)


if __name__ == "__main__":
    unittest.main()
