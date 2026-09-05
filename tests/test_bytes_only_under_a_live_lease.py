r"""Node 가 **lease 만료 뒤에도** 입력 바이트를 읽는 길은 0건 (배치 B #89 · SD-010 옆).

## 왜 있는가

「입력은 승인 도메인 안으로만 간다」는 바이트가 **살아 있는 lease 아래에서만** 나갈 때 성립한다.
lease 가 끝났는데도 같은 URL 이 열려 있으면, 배정이 끝난 기기가 남의 입력을 계속 읽는다.

## 실측 (2026-09-06)

| 길 | 문 |
|---|---|
| `GET /v1/internal/inputs/{id}/bytes` | `node_may_read` — `a.status = 'LEASED'` ∧ `a.lease_expires_at > now()` ∧ `a.node_id` 일치 ∧ `t.input_id` 일치 |
| `GET /v1/internal/capabilities/{id}/sample` | lease 가 아니라 **게이트러너 자격** — 계약 검증은 배정 전에 일어난다 (B2) |
| 그 밖에 `FileResponse` 를 돌려주는 곳 | **1** — `GET /openapi.yaml` (저장소의 정적 문서, 입력 아님) |
| Node 쪽 `_fetch_input` 호출 | **1** — 실행마다 받아 임시 파일에 두고 `finally` 에서 `os.unlink` |

## 재현

```bash
python3 -m unittest tests.test_bytes_only_under_a_live_lease
```
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_MAIN = ROOT / "apps" / "core" / "app" / "main.py"
INPUTS = ROOT / "apps" / "core" / "app" / "inputs.py"
NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"


def _handler(src: str, route: str) -> str:
    i = src.index(route)
    j = src.find("\n@app.", i + 1)
    return src[i:j if j > 0 else None]


class TestCoreHandsBytesOnlyUnderALease(unittest.TestCase):
    def test_node_may_read_requires_a_live_lease(self) -> None:
        m = re.search(r'NODE_MAY_READ_SQL = """(.*?)"""', INPUTS.read_text(encoding="utf-8"), re.S)
        self.assertIsNotNone(m, "NODE_MAY_READ_SQL 을 못 찾았다")
        assert m is not None
        sql = m.group(1)
        for clause in (r"a\.node_id\s*=\s*%\(node_id\)s", r"t\.input_id\s*=\s*%\(input_id\)s",
                       r"a\.status\s*=\s*'LEASED'", r"a\.lease_expires_at\s*>\s*now\(\)"):
            with self.subTest(clause=clause):
                self.assertRegex(sql, clause)

    def test_bytes_route_calls_it_before_responding(self) -> None:
        h = _handler(CORE_MAIN.read_text(encoding="utf-8"), '@app.get("/v1/internal/inputs/{input_id}/bytes")')
        self.assertIn("_assert_node_matches(node_id, authorization)", h)
        self.assertLess(h.index("node_may_read("), h.index("FileResponse("), "lease 확인이 응답 뒤에 온다")

    def test_every_file_response_is_one_of_the_two(self) -> None:
        src = CORE_MAIN.read_text(encoding="utf-8")
        sites = [src[:m.start()].count("\n") + 1 for m in re.finditer(r"\bFileResponse\(", src)]
        # 셋째는 `GET /openapi.yaml` — 저장소의 정적 문서지 입력 바이트가 아니다.
        self.assertEqual(3, len(sites), f"FileResponse 자리가 셋이 아니다: {sites}")
        self.assertIn("FileResponse(_OPENAPI_YAML", _handler(src, '@app.get("/openapi.yaml"'))
        # 같은 경로에 POST(set_sample) 가 있어 **GET 데코레이터**로 찾는다.
        for route, gate in (('@app.get("/v1/internal/inputs/{input_id}/bytes")', "node_may_read("),
                            ('@app.get("/v1/internal/capabilities/{capability_id}/sample")', "is_gate_runner(")):
            with self.subTest(route=route):
                h = _handler(src, route)
                self.assertIn("FileResponse(", h)
                self.assertIn(gate, h, f"{route} 가 {gate} 없이 바이트를 준다")


class TestNodeFetchesOncePerRunAndForgets(unittest.TestCase):
    def test_one_fetch_site_and_it_is_unlinked_in_finally(self) -> None:
        src = NODE_MAIN.read_text(encoding="utf-8")
        calls = [ln for ln in src.splitlines() if "_fetch_input(" in ln and "def " not in ln]
        self.assertEqual(1, len(calls), calls)
        tail = src[src.index(calls[0]):]
        fin = tail.index("finally:")
        self.assertIn("os.unlink(fetched)", tail[fin:fin + 400], "받은 바이트를 finally 에서 지우지 않는다")

    def test_fetch_goes_through_the_lease_gated_route_only(self) -> None:
        src = NODE_MAIN.read_text(encoding="utf-8")
        urls = re.findall(r'/v1/internal/inputs/[^"]*', src)
        self.assertEqual(["/v1/internal/inputs/{input_id}/bytes?node_id={NODE_ID}"], urls, urls)


if __name__ == "__main__":
    unittest.main()
