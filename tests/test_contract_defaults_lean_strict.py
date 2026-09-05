r"""계약 필드의 **기본값이 느슨한 쪽으로 기울어 있지 않은가** (배치 B #91 · `#189` 계열).

## 왜 있는가

등록 본문에서 칸을 빼먹으면 기본값이 들어간다. 그 기본값이 「검사 없음」·「누구나」·「무제한」
쪽이면, 빼먹은 등록이 **가장 열린 능력**이 된다. `#189` 는 계약이 깨졌을 때 검사가 꺼지지 않게
했다 — 여기는 계약을 **안 썼을 때** 무엇이 되는가다.

## 실측 (2026-09-06)

| 칸 | 기본값 | 어느 쪽 |
|---|---|---|
| `CapabilityCreate.quality_profile` | `"golden"` | 게이트를 **붙인다** (골든셋 4칸 없으면 등록 실패) |
| `CapabilityCreate.trust_domain_min` | `"team"` | 가장 좁은 도메인 |
| `CapabilityCreate.mvp_eligible` | `False` | — |
| `CapabilityCreate.output_kind` | `"closed_set_labels"` | 채점 가능한 유일한 종류 |
| `max_input_bytes` 를 안 보내면 | `coalesce(…, 33554432)` = 32 MiB | 상한 256 MiB 의 1/8 · 마이그레이션 DEFAULT 와 같다 |
| `max_attempts` 를 안 보내면 | `coalesce(…, 5)` | 유한 |
| `AgentCreate.weights_format` | `"safetensors"` | 절대규칙 5 |
| `AgentCreate.arch` | `None` 이지만 핸들러가 **거부** (G5·I1) | 선택처럼 보여도 필수 |
| `NodeCreate.is_gate_runner` | `False` | 러너 자격은 기본이 아니다 |
| 능력을 **등록**하는 데모 9개 | 전부 `quality_profile` 을 **명시** (`none`) | 기본값에 기대지 않는다 |

## 재현

```bash
python3 -m unittest tests.test_contract_defaults_lean_strict
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"
CAPABILITY = ROOT / "apps" / "core" / "app" / "capability.py"
MIGRATION_0011 = ROOT / "migrations" / "0011_task_input.sql"

EXPECTED = {
    ("CapabilityCreate", "quality_profile"): "golden",
    ("CapabilityCreate", "trust_domain_min"): "team",
    ("CapabilityCreate", "mvp_eligible"): False,
    ("CapabilityCreate", "output_kind"): "closed_set_labels",
    ("AgentCreate", "weights_format"): "safetensors",
    ("AgentCreate", "arch"): None,
    ("NodeCreate", "is_gate_runner"): False,
}


def _defaults() -> dict[tuple[str, str], object]:
    out: dict[tuple[str, str], object] = {}
    for node in ast.parse(MAIN.read_text(encoding="utf-8")).body:
        if not isinstance(node, ast.ClassDef):
            continue
        for st in node.body:
            if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name) and st.value is not None:
                if isinstance(st.value, ast.Constant):
                    out[(node.name, st.target.id)] = st.value.value
    return out


class TestModelDefaults(unittest.TestCase):
    def test_every_expected_default(self) -> None:
        got = _defaults()
        self.assertTrue(EXPECTED)
        for key, want in EXPECTED.items():
            with self.subTest(field=key):
                self.assertIn(key, got, f"{key} 가 기본값 없는 필수 칸이 됐다 — 표를 고쳐라")
                self.assertEqual(want, got[key], f"{key} 기본값이 {got[key]!r} 로 바뀌었다")

    def test_arch_is_required_by_the_handler(self) -> None:
        src = MAIN.read_text(encoding="utf-8")
        h = src[src.index('@app.post("/v1/agents")'):]
        h = h[:h.index("\n@app.")]
        self.assertRegex(h, r"if not body\.arch:\s*\n\s*raise HTTPException", "arch 없이 등록이 된다")


class TestSqlFallbacksAreBounded(unittest.TestCase):
    def test_coalesce_matches_the_migration_default(self) -> None:
        cap = CAPABILITY.read_text(encoding="utf-8")
        m = re.search(r"coalesce\(%\(max_input_bytes\)s::bigint,\s*(\d+)\)", cap)
        self.assertIsNotNone(m, "max_input_bytes 의 coalesce 를 못 찾았다")
        assert m is not None
        mig = MIGRATION_0011.read_text(encoding="utf-8")
        d = re.search(r"max_input_bytes BIGINT NOT NULL DEFAULT (\d+)", mig)
        cap_max = re.search(r"max_input_bytes <= (\d+)", mig)
        assert d is not None and cap_max is not None
        self.assertEqual(d.group(1), m.group(1), "코드의 기본값과 DDL DEFAULT 가 다르다")
        self.assertLessEqual(int(m.group(1)) * 8, int(cap_max.group(1)), "기본값이 상한에 붙어 있다")

    def test_attempts_fallback_is_finite_and_small(self) -> None:
        m = re.search(r"coalesce\(%\(max_attempts\)s::int,\s*(\d+)\)", CAPABILITY.read_text(encoding="utf-8"))
        self.assertIsNotNone(m)
        assert m is not None
        self.assertLessEqual(int(m.group(1)), 10, m.group(1))


class TestDemoTemplatesDoNotLeanOnTheDefault(unittest.TestCase):
    def test_every_registering_demo_names_its_profile(self) -> None:
        # **등록**하는 데모만 — `product`·`capreq` 는 카탈로그를 조회만 한다.
        demos = [p for p in sorted((ROOT / "scripts").glob("*_demo.sh"))
                 if re.search(r"POST[^|\n]*/v1/capabilities[\"' ]", p.read_text(encoding="utf-8"))]
        self.assertEqual(9, len(demos), [p.name for p in demos])
        for p in demos:
            with self.subTest(demo=p.name):
                self.assertIn('"quality_profile":"none"', p.read_text(encoding="utf-8"),
                              f"{p.name} 이 quality_profile 을 기본값에 맡긴다")


if __name__ == "__main__":
    unittest.main()
