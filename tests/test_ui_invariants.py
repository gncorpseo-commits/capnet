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

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "apps" / "core" / "app" / "static"
PAGES = sorted(STATIC.glob("*.html"))

# 서버 카탈로그가 주는 값. 화면이 이것을 **스스로 만들어 내면** 안 된다.
# 두 검사가 같은 목록을 본다 — 갈리면 한쪽만 지켜진다.
INVENTED = ("eurosat-rgb", "image.classify", "text.classify", "safety.pii")
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

    def test_invented_list_is_real_and_not_empty(self) -> None:
        """**목록을 비우면 위 두 검사가 공허하게 통과한다.**

        실제로 그랬다 — 뮤테이션으로 `INVENTED = ()` 를 넣었더니 둘 다 초록이었다.
        이 회차가 고쳐 온 「0건을 훑으며 통과」와 같은 모양을 **내 검사가 하고 있었다.**

        그래서 목록이 **실물**인지 본다 — 카탈로그의 능력 코드이거나 allowlist 의
        데이터셋 id 여야 한다. 비우면 여기서 걸리고, 가짜를 넣어도 걸린다.
        """
        self.assertTrue(INVENTED, "INVENTED 가 비었다 — 위 두 검사가 아무것도 안 본다")
        catalog = (ROOT / "docs" / "spec" / "capability-catalog.md").read_text(encoding="utf-8")
        allowlist = (ROOT / "apps" / "core" / "app" / "allowlist.py").read_text(encoding="utf-8")
        for value in INVENTED:
            with self.subTest(value=value):
                self.assertTrue(
                    f"`{value}`" in catalog or f'"{value}"' in allowlist,
                    f"{value!r} 은 카탈로그에도 allowlist 에도 없다 — 실물이 아니다",
                )

    def test_no_domain_value_is_used_as_a_fallback(self) -> None:
        """`||` **기본값**으로도 서버 값을 지어내지 않는다.

        위 검사는 `catch` 블록만 봤다. 그래서 이것을 놓쳤다 (2026-09-03 · `call.html`):

            const [code, version] = ($("c-cap").value || "image.classify|1").split("|");

        `/v1/capabilities` 를 못 받아 `(없음)` 이 떠 있어도 **사용자가 시키지 않은
        `image.classify` 로 작업이 만들어졌다.** 바로 아래 데이터셋은 같은 함정을
        이미 고쳤는데(#184·#189), 이쪽은 `catch` 밖이라 **검사가 못 봤다.**

        빈 값이면 **거절**하는 것이 맞다 — `caseId` 가 이미 그렇게 한다.
        """
        bad: list[str] = []
        for p in PAGES:
            s = code(p)
            for m in re.finditer(r"\|\|\s*[\"']([^\"']+)[\"']", s):
                literal = m.group(1)
                if any(v in literal for v in INVENTED):
                    line = s[: m.start()].count("\n") + 1
                    bad.append(f"{p.name}:{line} — `|| {literal!r}`")
        self.assertEqual(
            [], bad,
            "서버가 준 적 없는 값을 기본값으로 쓴다 — 빈 값이면 거절한다: " + "; ".join(bad),
        )

    def test_catch_never_invents_server_data(self) -> None:
        """**못 받았으면 못 받았다고 한다.** 실패 자리에 서버 값을 박아 넣지 않는다.

        `call.html` 의 데이터셋 목록이 그랬다 (2026-09-02):

            } catch { $("c-dataset").innerHTML = '<option>eurosat-rgb</option>'; }

        `/v1/datasets` 를 못 받아도 **서버가 준 적 없는 `eurosat-rgb`** 를
        서버가 준 것처럼 보여 줬다. 바로 위 `c-cap` 은 처음부터 에러를 올렸으니
        **같은 함수 안에서 규약이 갈려 있었다.**

        여기서 보는 것은 **`catch` 블록 안에 도메인 값 리터럴이 있는가** 하나다.
        에러 메시지·빈 표시(`(없음)`)는 서버 데이터가 아니므로 대상이 아니다.
        """
        invented = INVENTED
        for p in PAGES:
            s = code(p)
            for m in re.finditer(r"\bcatch\b[^{]*\{", s):
                # 중괄호 균형으로 블록 끝을 찾는다 — 정규식 하나로는 못 자른다.
                i = s.index("{", m.start())
                depth, j = 0, i
                while j < len(s):
                    if s[j] == "{":
                        depth += 1
                    elif s[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                block = s[i : j + 1]
                for bad in invented:
                    self.assertNotIn(
                        bad,
                        block,
                        f"{p.name}: catch 안에서 `{bad}` 를 지어낸다 — "
                        "못 받은 것을 받은 것처럼 보여 준다",
                    )

    def test_finder_actually_finds_things(self) -> None:
        self.assertGreaterEqual(len(PAGES), 4)

    def test_catch_probe_actually_sees_catches(self) -> None:
        """`catch` 를 하나도 못 찾으면 위 검사는 0건을 훑고 통과한다."""
        total = sum(len(re.findall(r"\bcatch\b", code(p))) for p in PAGES)
        self.assertGreater(total, 5, f"catch 를 {total}개밖에 못 찾았다 — 검사가 헛돈다")


if __name__ == "__main__":
    unittest.main()
