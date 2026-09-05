r"""non-GET 라우트의 **요청 본문 필수 여부**가 핸들러와 문서에서 같은가 (배치 B #82).

## 왜 있는가

`test_openapi_drift` 는 `(메서드, 경로)` 를, `test_openapi_request_schema_agrees` 는 본문
**필드**를 본다. 그 사이에 하나가 비어 있었다 — **본문 자체가 필수인가.** OpenAPI 의
`requestBody.required` 는 **빠지면 false** 다. 핸들러가 `body: InviteCreate` 로 받으면
본문 없는 요청은 422 인데, 문서만 보고 붙이는 쪽은 「없어도 된다」고 읽는다.

## 실측 (2026-09-06) — non-GET 22

| 축 | 값 |
|---|---|
| 핸들러가 본문을 **필수**로 받는 곳 | **19** — 그중 1 은 `inputs` 의 raw 스트림(`request: Request`) |
| 핸들러가 본문을 **선택**으로 받는 곳 (`X \| None = None`) | **2** — `internal/claim` · `nodes/{id}/credentials` |
| 본문이 없는 곳 | **1** — `inputs/{id}/purge` |
| 문서가 `required: true` 를 빠뜨렸던 곳 | **2** → 고쳤다 — `nodes/invites` · `nodes/invites/{id}/revoke` |
| 문서에 `security`·`securitySchemes` | **0** — 22 전부 Authorization 을 요구하는데 문서는 말하지 않는다 (브리지 표 · 스펙 모양이라 여기서 안 고친다) |

인증 축(참고): admin 12 · developer 4 · user 2 · node 증서 3 · invite 토큰 1.

## 재현

```bash
python3 -m unittest tests.test_write_routes_request_body_agrees
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"
SPEC = ROOT / "apps" / "core" / "openapi.yaml"

WRITE = ("post", "put", "patch", "delete")
# 본문이 아닌 매개변수 — 경로·헤더·요청 객체·업로드 조각.
NOT_A_BODY = re.compile(r"Header\(|^Request$|^uuid\.|^str\b|^int\b|UploadFile|Form\(|^bytes\b")


def _handlers() -> dict[tuple[str, str], str | None]:
    """`(메서드, 경로)` → `"required"` · `"optional"` · `None`(본문 없음)."""
    src = MAIN.read_text(encoding="utf-8")
    out: dict[tuple[str, str], str | None] = {}
    for fn in ast.parse(src).body:
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for d in fn.decorator_list:
            if not (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in WRITE):
                continue
            if any(k.arg == "include_in_schema" for k in d.keywords):
                continue
            kind: str | None = None
            # `request: Request` 로 raw 스트림을 읽는 핸들러(`/v1/inputs`, D8′)는 본문이 **필수**다.
            if any(a.annotation is not None and ast.unparse(a.annotation) == "Request" for a in fn.args.args):
                kind = "required"
            args = fn.args.args
            defaults = [None] * (len(args) - len(fn.args.defaults)) + list(fn.args.defaults)
            for a, default in zip(args, defaults):
                ann = ast.unparse(a.annotation) if a.annotation else ""
                if not ann or NOT_A_BODY.search(ann):
                    continue
                optional = default is not None or "| None" in ann
                kind = "optional" if optional else "required"
            out[(d.func.attr, d.args[0].value)] = kind
    return out


def _documented() -> dict[tuple[str, str], str | None]:
    """문서의 `(메서드, 경로)` → `requestBody.required` 판정. `required` 가 없으면 optional."""
    out: dict[tuple[str, str], str | None] = {}
    path = key = None
    in_body = False
    for ln in SPEC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  (/\S+):\s*$", ln)
        if m:
            path = m.group(1)
            continue
        m = re.match(r"^    (get|post|put|patch|delete):\s*$", ln)
        if m and path:
            key = (m.group(1), path) if m.group(1) in WRITE else None
            in_body = False
            if key:
                out[key] = None
            continue
        if key is None:
            continue
        if re.match(r"^      requestBody:", ln):
            in_body = True
            out[key] = "optional"
            continue
        if re.match(r"^      \w", ln):
            in_body = False
        if in_body and re.match(r"^        required:\s*true", ln):
            out[key] = "required"
    return out


class TestBodyRequirementAgrees(unittest.TestCase):
    def test_every_write_route_says_the_same_thing(self) -> None:
        code, doc = _handlers(), _documented()
        self.assertTrue(code, "핸들러를 하나도 못 찾았다")
        self.assertEqual(sorted(code), sorted(doc), "라우트 집합이 다르다 — test_openapi_drift 가 먼저 운다")
        bad = [f"{m.upper()} {p}: 코드={code[(m, p)]} 문서={doc[(m, p)]}"
               for (m, p) in sorted(code) if code[(m, p)] != doc[(m, p)]]
        self.assertEqual([], bad, "본문 필수 여부가 갈린다:\n  " + "\n  ".join(bad))

    def test_todays_shape(self) -> None:
        code = _handlers()
        kinds = {k: sum(1 for v in code.values() if v == k) for k in ("required", "optional", None)}
        self.assertEqual({"required": 19, "optional": 2, None: 1}, kinds, kinds)
        self.assertEqual({("post", "/v1/internal/claim"), ("post", "/v1/nodes/{node_id}/credentials")},
                         {k for k, v in code.items() if v == "optional"})
        self.assertEqual({("post", "/v1/inputs/{input_id}/purge")}, {k for k, v in code.items() if v is None})


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_routes_are_seen(self) -> None:
        self.assertGreaterEqual(len(_handlers()), 20, sorted(_handlers()))
        self.assertGreaterEqual(len(_documented()), 20, sorted(_documented()))

    def test_parser_reads_required_only_inside_request_body(self) -> None:
        doc = _documented()
        self.assertEqual("required", doc[("post", "/v1/tasks")])
        self.assertEqual("optional", doc[("post", "/v1/internal/claim")])
        self.assertIsNone(doc[("post", "/v1/inputs/{input_id}/purge")])


if __name__ == "__main__":
    unittest.main()
