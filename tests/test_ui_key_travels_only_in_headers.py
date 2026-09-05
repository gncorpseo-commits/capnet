r"""UI 의 관리 키는 **요청 헤더로만** 나간다 (배치 B #80 · `test_ui_invariants` 보강).

## 왜 있는가

`test_ui_invariants.test_key_never_in_url` 은 리터럴 `?key=`·`&token=` 만 본다.
`url.searchParams.set("key", k)` 나 페이지가 `getKey()` 를 직접 읽어 본문에 넣는 모양은
그 정규식에 안 걸린다. 여기서는 **키가 지나갈 수 있는 길**을 센다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `static/` 전체의 `fetch(` | **1** — `app.js` 의 `_send()` 뿐 |
| `_send` 가 `path` 를 건드리는가 | 아니다 — `fetch(path, {…headers})` 그대로 |
| 페이지(`*.html`) 가 `getKey(`·`sessionStorage` 를 직접 읽는 곳 | **0** |
| `searchParams`·`URLSearchParams` | **0** |
| `getKey()` 를 값으로 쓰는 줄 | **2** — `keyPrefix()`(`.` 앞 접두만 표시) · `api()`(`Authorization` 헤더) |

## 재현

```bash
python3 -m unittest tests.test_ui_key_travels_only_in_headers
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "apps" / "core" / "app" / "static"
APP_JS = STATIC / "app.js"
PAGES = sorted(STATIC.glob("*.html"))


def code(p: Path) -> str:
    """`//` 줄 주석을 뺀 본문 — 주석의 설명 문구를 위반으로 잡지 않는다."""
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in p.read_text(encoding="utf-8").splitlines())


class TestOneNetworkDoor(unittest.TestCase):
    def test_fetch_is_called_in_exactly_one_place(self) -> None:
        sites = [(p.name, i) for p in PAGES + [APP_JS]
                 for i, ln in enumerate(code(p).splitlines(), 1) if "fetch(" in ln]
        self.assertEqual([("app.js", 34)], [(n, i) for n, i in sites] if len(sites) == 1 else sites,
                         f"fetch 가 한 곳이 아니다: {sites}")

    def test_send_does_not_rewrite_the_path(self) -> None:
        """키를 URL 에 붙이려면 `path` 를 고쳐야 한다 — `_send` 는 받은 그대로 넘긴다."""
        m = re.search(r"async function _send\(path, opts, headers\) \{\n(.*?)\n\}", code(APP_JS), re.S)
        self.assertIsNotNone(m, "_send 를 못 찾았다")
        assert m is not None
        body = m.group(1)
        self.assertIn("fetch(path, {", body, "fetch 가 path 를 그대로 받지 않는다")
        self.assertNotRegex(body, r"path\s*[+=]", "_send 가 path 를 고친다")


class TestKeyNeverLeavesAppJs(unittest.TestCase):
    def test_pages_do_not_read_the_key(self) -> None:
        self.assertTrue(PAGES, "페이지를 하나도 못 찾았다")
        for p in PAGES:
            with self.subTest(page=p.name):
                s = code(p)
                self.assertNotIn("getKey(", s, f"{p.name} 이 키를 직접 읽는다")
                self.assertNotIn("sessionStorage", s, f"{p.name} 이 저장소를 직접 읽는다")

    def test_no_query_string_builder_anywhere(self) -> None:
        for p in PAGES + [APP_JS]:
            with self.subTest(file=p.name):
                self.assertNotRegex(code(p), r"searchParams|URLSearchParams",
                                    f"{p.name}: 쿼리스트링을 조립한다 — 키가 거기로 갈 길이 생긴다")

    def test_the_key_is_used_on_one_authorization_line_only(self) -> None:
        lines = [ln for ln in code(APP_JS).splitlines() if "getKey()" in ln and "function" not in ln]
        self.assertTrue(lines, "app.js 가 getKey() 를 쓰지 않는다")
        # 키를 **값으로 소비하는** 줄은 둘뿐이다 — `keyPrefix()` 는 `.` 앞 접두만 화면에
        # 보여 주고, `api()` 는 그 아래 줄에서 헤더에 싣는다. 셋째가 생기면 여기서 운다.
        uses = [ln.strip() for ln in lines]
        self.assertEqual(["const k = v || getKey();", "const k = getKey();"], uses, uses)
        body = code(APP_JS)
        self.assertIn('return k ? k.split(".")[0] : "";', body, "keyPrefix 가 접두만 돌려주지 않는다")
        self.assertIn('Authorization: "CapNet-Key " + k', body)


class TestProbeActuallyScans(unittest.TestCase):
    def test_pages_and_helper_are_seen(self) -> None:
        self.assertGreaterEqual(len(PAGES), 4, [p.name for p in PAGES])
        self.assertGreaterEqual(len(code(APP_JS).splitlines()), 60)


if __name__ == "__main__":
    unittest.main()
