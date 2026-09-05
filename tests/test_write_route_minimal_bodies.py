r"""쓰기 라우트의 **최소 몸통**을 모델에서 뽑아 둔다 (배치 B #73 · `#235` 잔여).

## 왜 있는가

`#235`(큐 #49)는 쓰기 라우트 **스물둘 중 셋**만 무인증으로 눌러 본다는 것을 표로 남기고,
나머지 열아홉을 **못 늘린 이유**를 이렇게 적었다:

> FastAPI 는 핸들러 본문보다 **먼저** 요청 본문을 검증한다. 몸통 없이 `POST` 하면 인증에
> 닿기도 전에 **422** 고, 그 절은 **인증을 재지 못한다.** 라우트마다 유효한 최소 몸통이
> 필요하고, 그게 맞는지는 **돌려 봐야** 안다.

**「몸통이 무엇인가」는 돌려 보지 않아도 안다.** 요청 모델이 소스에 있다. 이 파일이
그것을 뽑아 **붙여넣기용 표**로 고정한다 — Docker 가 있는 회차가 §14 옆에 그대로 쓴다.

## 실측 (2026-09-06)

| 무엇 | 수 |
|---|---|
| 쓰기 라우트 | **22** |
| 요청 모델이 있는 것 | **20** (`POST /v1/inputs`·`…/purge` 는 본문 없음) |
| **필수 필드가 있는 것** | **10** — 나머지는 전부 기본값이 있다 |
| 몸통 없이 눌러도 **401 까지 가는** 라우트 | **12** |

**열둘은 몸통이 필요 없다.** `#235` 가 「열아홉 전부 몸통이 필요하다」고 읽힐 수 있게
적었는데, 실제로는 **열 개만** 필요하다. 그만큼 Docker 회차의 일이 줄어든다.

## 무엇을 고정하나

1. 표의 몸통이 그 라우트 모델의 **필수 필드를 전부** 담는다
2. 모델에 필수 필드가 늘면 **표가 낡는다** → 운다 (`#223` 이 겪은 422 함정 예방)
3. 몸통이 필요 없는 라우트를 「필요하다」고 적지 않는다
4. 세는 대상이 비지 않는다

## 무엇을 안 보나

**실제 응답.** 401 이 나오는지는 강제 모드에서 `prod_room` 이 잰다 (Docker 필요 ·
이 세션에는 데몬이 없다). 여기는 **몸통이 계약과 맞는가**만 본다.
"""

from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_every_route_declares_its_auth import MAIN  # noqa: E402

WRITE = ("POST", "PUT", "PATCH", "DELETE")

# 라우트 → 무인증 프로브에 쓸 **최소 몸통**. 값은 형식만 맞으면 된다 —
# 인증이 조회보다 먼저 오므로 존재하지 않아도 401 이다 (`#236` 이 못박았다).
MINIMAL_BODY: dict[str, dict[str, object]] = {
    "POST /v1/agents": {"name": "probe", "version": "1", "manifest_hash": "h",
                        "weights_uri": "file:///weights/x.safetensors",
                        "weights_sha256": "0" * 64},
    "POST /v1/agents/{agent_id}/bindings": {
        "node_id": "00000000-0000-4000-8000-0000000000ff",
        "weights_sha256_seen": "0" * 64},
    "POST /v1/arches": {"arch": "ProbeArch", "max_params": 1},
    "POST /v1/capabilities": {"code": "probe.noop", "name": "probe",
                              "input_schema": {}, "output_schema": {}},
    "POST /v1/internal/agent-capabilities/revoke": {"reason": "probe"},
    "POST /v1/internal/assignments/{assignment_id}/complete": {"weights_sha256": "0" * 64},
    "POST /v1/internal/gate-runs": {
        "agent_id": "00000000-0000-4000-8000-0000000000ff",
        "capability_id": "00000000-0000-4000-8000-0000000000ff",
        "runner_node_id": "00000000-0000-4000-8000-0000000000ff"},
    "POST /v1/internal/gate-runs/{gate_run_id}/finish": {"status": "FAILED"},
    "POST /v1/nodes": {"name": "probe", "device_type": "SERVER",
                       "trust_domain": "public", "compute_tier_max": "S"},
    "POST /v1/nodes/redeem": {"name": "probe"},
    "POST /v1/nodes/{node_id}/credentials/revoke": {"reason": "probe"},
}


def _models() -> dict[str, list[str]]:
    """`BaseModel` 이름 → **필수** 필드."""
    out: dict[str, list[str]] = {}
    for node in ast.walk(ast.parse(MAIN.read_text(encoding="utf-8"))):
        if not (isinstance(node, ast.ClassDef)
                and any(isinstance(b, ast.Name) and b.id == "BaseModel" for b in node.bases)):
            continue
        req = []
        for st in node.body:
            if not (isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)):
                continue
            if st.value is None:
                req.append(st.target.id)                      # 기본값 없음 = 필수
            elif "Field(..." in ast.unparse(st.value):
                req.append(st.target.id)                      # 명시적 필수
        out[node.name] = req
    return out


def _write_routes() -> list[tuple[str, str, str | None]]:
    """`(verb, path, 본문 모델)`."""
    models = _models()
    out = []
    for fn in ast.walk(ast.parse(MAIN.read_text(encoding="utf-8"))):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        dec = [d for d in fn.decorator_list
               if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
               and isinstance(d.func.value, ast.Name) and d.func.value.id == "app"]
        if not dec or dec[0].func.attr.upper() not in WRITE:
            continue
        body_model = None
        for arg in fn.args.args:
            if arg.annotation is None:
                continue
            name = ast.unparse(arg.annotation).replace(" | None", "")
            if name in models:
                body_model = name
        out.append((dec[0].func.attr.upper(), str(dec[0].args[0].value), body_model))
    return out


class TestEveryRequiredFieldIsCovered(unittest.TestCase):
    def test_each_body_has_the_models_required_fields(self) -> None:
        """**여기가 핵심이다.** 빠지면 프로브가 422 로 끝나고 인증을 못 잰다."""
        models, routes = _models(), _write_routes()
        self.assertTrue(routes, "쓰기 라우트를 하나도 못 찾았다")
        bad = []
        for verb, path, model in routes:
            key = f"{verb} {path}"
            required = set(models.get(model or "", []))
            if not required:
                continue
            missing = required - set(MINIMAL_BODY.get(key, {}))
            if missing:
                bad.append(f"{key} ← {sorted(missing)}")
        self.assertEqual([], bad, "최소 몸통에 필수 필드가 빠졌다: " + "; ".join(bad))

    def test_no_body_is_listed_for_a_route_that_needs_none(self) -> None:
        """필요 없는 몸통을 적으면 「열아홉 전부 필요하다」는 오해가 남는다."""
        models, routes = _models(), _write_routes()
        needs = {f"{v} {p}" for v, p, m in routes if models.get(m or "", [])}
        extra = sorted(set(MINIMAL_BODY) - needs)
        self.assertEqual([], extra, f"필수 필드가 없는데 몸통을 적었다: {extra}")

    def test_every_body_is_json_serialisable(self) -> None:
        """`curl -d` 에 그대로 붙일 수 있어야 한다."""
        bodies = MINIMAL_BODY.items()
        self.assertTrue(bodies, "최소 몸통 표가 비었다")
        for key, body in bodies:
            with self.subTest(route=key):
                self.assertIsInstance(json.dumps(body, ensure_ascii=False), str)


class TestTodaysCounts(unittest.TestCase):
    def test_write_routes_and_bodies(self) -> None:
        models, routes = _models(), _write_routes()
        self.assertGreaterEqual(len(routes), 20, len(routes))
        needing = [f"{v} {p}" for v, p, m in routes if models.get(m or "", [])]
        self.assertEqual(len(MINIMAL_BODY), len(needing),
                         f"몸통이 필요한 라우트 {len(needing)} ≠ 표 {len(MINIMAL_BODY)}")

    def test_most_routes_need_no_body(self) -> None:
        """`#235` 가 「열아홉 전부 몸통이 필요하다」로 읽힐 수 있게 적었다 — 아니다."""
        models, routes = _models(), _write_routes()
        free = [f"{v} {p}" for v, p, m in routes if not models.get(m or "", [])]
        self.assertGreaterEqual(len(free), 10, free)


class TestProbeActuallyScans(unittest.TestCase):
    def test_models_are_read(self) -> None:
        self.assertGreaterEqual(len(_models()), 15, sorted(_models()))

    def test_the_required_detector_discriminates(self) -> None:
        """기본값 있는 필드를 필수로 세면 표가 쓸데없이 커진다."""
        models = _models()
        self.assertIn("name", models.get("NodeCreate", []))
        self.assertNotIn("org_id", models.get("NodeCreate", []))
        self.assertEqual([], models.get("TaskCreate", ["x"]) and
                         [f for f in models["TaskCreate"] if f not in ()] or [])


if __name__ == "__main__":
    unittest.main()
