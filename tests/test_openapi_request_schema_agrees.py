"""`openapi.yaml` 의 **요청 본문**이 핸들러가 실제로 받는 것과 맞는가 (큐 #24).

## 왜 있는가

경로·메서드는 `#142` 가, 머리말(`info`)은 `#201` 이 못박았다. **요청 본문은 아직 밖이었다.**

전수했다 (2026-09-03). `requestBody` 스키마가 있는 오퍼레이션 **11** 중 **하나가 깨져 있었다**:

```text
POST /v1/internal/assignments/{assignment_id}/fail
  문서:  properties: { reason }
  모델:  FailBody(node_id: uuid.UUID = Field(alias="nodeId"), reason: str = "")
```

**`nodeId` 가 통째로 빠져 있었고 기본값이 없어 필수다.** 문서를 그대로 따라
`{"reason": "…"}` 만 보내면 **422** 다. Node 는 `_report_failure` 에서 `nodeId` 를
보내고 있어 동작했고, **그래서 아무도 몰랐다** — 문서만 보고 붙이는 쪽만 막힌다.

`required` 도 없었다. 두 사본 다 고쳤다.

## 무엇을 고정하나

1. 문서가 적은 속성은 **모델이 받는 이름**이어야 한다 (필드명 **또는** alias)
2. 모델의 **필수 필드**(기본값 없음)는 문서에 있어야 한다 — **이게 위를 잡은 검사다**
3. 스키마가 있는 오퍼레이션은 핸들러가 **실재**해야 한다

## 왜 alias 를 둘 다 받나

세 모델이 `model_config = {"populate_by_name": True}` 다 — `input_id` 도 `inputId` 도
받는다. 그래서 문서가 `input_id` 라고 적은 것은 **틀린 것이 아니다.**
표기를 한쪽으로 모으는 것은 **계약의 모양**을 정하는 일이라 여기서 하지 않는다
(`CLAUDE.md` 브리지절). 여기서 막는 것은 **문서대로 보내면 실패하는 것** 하나다.

## 무엇을 고정하지 **않나**

**응답 스키마.** 오늘 45개 오퍼레이션에 2xx 스키마가 **0건**이고, 그것을 채우는 것은
`openapi-response-schemas` **Decision** 대기다 (#202). 부재를 검사로 못박으면
채우는 것을 막는 꼴이라 손대지 않는다.

타입도 안 본다 — 문서의 `type: string`/`format: uuid` 와 파이썬 타입을 잇는 것은
별개의 배관이다. **이름과 필수 여부**만 본다.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "apps" / "core" / "openapi.yaml"
MAIN = ROOT / "apps" / "core" / "app" / "main.py"

WRITE = ("post", "put", "patch", "delete")


def _tree() -> ast.Module:
    return ast.parse(MAIN.read_text(encoding="utf-8"))


def _routes() -> dict[tuple[str, str], tuple[str, str | None]]:
    """`(메서드, 경로) → (핸들러, 본문 모델 이름)`."""
    out: dict[tuple[str, str], tuple[str, str | None]] = {}
    for fn in ast.walk(_tree()):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in fn.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                    and isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app"):
                continue
            if dec.func.attr not in ("get", *WRITE):
                continue
            path = dec.args[0].value if dec.args and isinstance(
                dec.args[0], ast.Constant) else "?"
            model: str | None = None
            for arg in fn.args.args:
                ann = arg.annotation
                if ann is None or arg.arg not in ("body", "payload"):
                    continue
                # `Body | None = None` 형태도 잡는다.
                if isinstance(ann, ast.Name):
                    model = ann.id
                elif isinstance(ann, ast.BinOp) and isinstance(ann.left, ast.Name):
                    model = ann.left.id
            out[(dec.func.attr.upper(), str(path))] = (fn.name, model)
            break
    return out


def _models() -> dict[str, dict[str, tuple[str, bool]]]:
    """`모델 → {필드명: (alias 또는 필드명, 필수인가)}`."""
    out: dict[str, dict[str, tuple[str, bool]]] = {}
    for node in ast.walk(_tree()):
        if not isinstance(node, ast.ClassDef):
            continue
        fields: dict[str, tuple[str, bool]] = {}
        for st in node.body:
            if not (isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)):
                continue
            alias: str | None = None
            required = st.value is None
            if isinstance(st.value, ast.Call):
                # `Field(...)` — `default=` 가 있으면 선택.
                required = not any(kw.arg == "default" for kw in st.value.keywords)
                if st.value.args:
                    required = False
                for kw in st.value.keywords:
                    if kw.arg == "alias" and isinstance(kw.value, ast.Constant):
                        alias = str(kw.value.value)
            fields[st.target.id] = (alias or st.target.id, required)
        if fields:
            out[node.name] = fields
    return out


# `openapi.yaml` 은 **손으로** 읽는다 — CI 단위 잡은 아무것도 설치하지 않는다
# (`pip install` 단계가 없다). `pyyaml` 을 쓰면 거기서 죽는다.
# `test_openapi_drift` 가 같은 이유로 텍스트 파싱을 쓴다.
_PATH = re.compile(r"^  (/\S*):\s*$")
_METHOD = re.compile(r"^    (get|post|put|patch|delete):\s*$")
_PROP = re.compile(r"^                (\w+):")
_REQUIRED = re.compile(r"^              required:\s*\[([^\]]*)\]\s*$")


def _documented() -> list[tuple[str, str, dict]]:
    """`(메서드, 경로, {properties, required})` — `properties` 가 있는 요청 본문만.

    들여쓰기가 이 파일의 규약이다 (경로 2 · 메서드 4 · `schema` 밑 속성 16).
    모양이 바뀌면 `test_found_documented_bodies` 가 **먼저** 걸린다.
    """
    out: list[tuple[str, str, dict]] = []
    path = method = None
    in_body = in_props = False
    props: list[str] = []
    required: list[str] = []

    def flush() -> None:
        if path and method and props:
            out.append((method.upper(), path,
                        {"properties": list(props), "required": list(required)}))

    for line in SPEC.read_text(encoding="utf-8").splitlines():
        m = _PATH.match(line)
        if m:
            flush()
            path, method, in_body, in_props = m.group(1), None, False, False
            props, required = [], []
            continue
        m = _METHOD.match(line)
        if m:
            flush()
            method = m.group(1) if m.group(1) in WRITE else None
            in_body = in_props = False
            props, required = [], []
            continue
        if line.strip() == "requestBody:":
            in_body, in_props = True, False
            continue
        if in_body:
            if line.strip() == "properties:":
                in_props = True
                continue
            m = _REQUIRED.match(line)
            if m:
                required = [x.strip() for x in m.group(1).split(",") if x.strip()]
                continue
            if in_props:
                m = _PROP.match(line)
                if m:
                    props.append(m.group(1))
                    continue
                if line.strip() and not line.startswith("                "):
                    in_props = False
            if line.strip() == "responses:":
                in_body = in_props = False
    flush()
    return out


class TestDocumentedPropertiesAreAccepted(unittest.TestCase):
    def test_every_documented_property_is_a_name_the_model_takes(self) -> None:
        routes, models = _routes(), _models()
        bad: list[str] = []
        for method, path, schema in _documented():
            handler = routes.get((method, path))
            if handler is None or handler[1] is None:
                continue
            fields = models.get(handler[1], {})
            accepted = set(fields) | {alias for alias, _r in fields.values()}
            for prop in schema["properties"]:
                if prop not in accepted:
                    bad.append(f"{method} {path}: 문서의 {prop!r} 을 {handler[1]} 이 안 받는다")
        self.assertEqual([], bad, "\n".join(bad))


class TestRequiredFieldsAreDocumented(unittest.TestCase):
    """**이 검사가 `nodeId` 누락을 잡았다.**"""

    def test_no_required_field_is_missing_from_the_doc(self) -> None:
        routes, models = _routes(), _models()
        bad: list[str] = []
        for method, path, schema in _documented():
            handler = routes.get((method, path))
            if handler is None or handler[1] is None:
                continue
            props = set(schema["properties"])
            for field, (alias, required) in models.get(handler[1], {}).items():
                if required and not ({field, alias} & props):
                    bad.append(
                        f"{method} {path}: {handler[1]}.{field} 는 **필수**인데 문서에 없다 "
                        f"— 문서대로 보내면 422 다"
                    )
        self.assertEqual([], bad, "\n".join(bad))

    def test_required_list_matches_when_present(self) -> None:
        """`required:` 를 적었으면 그 이름도 모델이 받는 이름이어야 한다."""
        routes, models = _routes(), _models()
        bad: list[str] = []
        for method, path, schema in _documented():
            handler = routes.get((method, path))
            if handler is None or handler[1] is None:
                continue
            fields = models.get(handler[1], {})
            accepted = set(fields) | {alias for alias, _r in fields.values()}
            for name in schema.get("required") or []:
                if name not in accepted:
                    bad.append(f"{method} {path}: required 의 {name!r} 을 모델이 안 받는다")
        self.assertEqual([], bad, "\n".join(bad))


class TestDocumentedOperationsExist(unittest.TestCase):
    def test_every_documented_body_has_a_handler(self) -> None:
        routes = _routes()
        ghosts = [f"{m} {p}" for m, p, _s in _documented() if (m, p) not in routes]
        self.assertEqual([], ghosts, f"핸들러가 없는 요청 본문: {ghosts}")


class TestProbeActuallyWorks(unittest.TestCase):
    """훑기가 0개를 비교하며 통과하지 않는가."""

    def test_found_documented_bodies(self) -> None:
        self.assertGreaterEqual(len(_documented()), 8,
                                f"요청 본문을 {len(_documented())}개밖에 못 찾았다")

    def test_found_models_and_routes(self) -> None:
        self.assertGreater(len(_models()), 10)
        self.assertGreater(len(_routes()), 20)

    def test_required_detection_discriminates(self) -> None:
        """전부 「필수 아님」으로 보면 위 검사가 아무것도 안 지킨다."""
        models = _models()
        fail = models.get("FailBody", {})
        self.assertTrue(fail, "FailBody 를 못 읽었다")
        self.assertTrue(fail["node_id"][1], "alias 만 있는 필드를 선택으로 본다")
        self.assertFalse(fail["reason"][1], "기본값이 있는 필드를 필수로 본다")


if __name__ == "__main__":
    unittest.main()
