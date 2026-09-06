r"""등급·스냅샷을 **앱이 덮어쓰는 경로는 0** (배치 C #102 · 절대규칙 4).

## 왜 있는가

`trust_domain`·`compute_tier_max` 는 Core 가 부여한다. 그 값이 앱 UPDATE 로 움직이면 「할당 중 강등 불가」
(FK 스냅샷)도, 「Node 는 자기 등급을 주장 못 한다」도 뒷문이 생긴다. 실측(2026-09-06):

| 무엇 | 값 |
|---|---|
| 등급·스냅샷 여섯 컬럼(`trust_domain`·`compute_tier_max`·`task_trust_domain`·`node_trust_domain`·`capability_tier`·`node_tier_max`)을 `SET` 하는 UPDATE | **0** |
| `UPDATE node` | **0** — 등급은 등록 뒤 앱으로 못 바꾼다 |
| 등급 이름을 본문으로 받는 모델 | **3** — `TaskCreate.trust_domain`(요청자 도메인 · DB FK 가 판정, D23) · `InviteCreate`·`NodeCreate`(admin). `CapabilityCreate` 의 `compute_tier`·`trust_domain_min` 은 계약값이지 Node 등급이 아니다 |
| Node 앱이 페이로드에 싣는 등급 낱말 | **0** |

## 재현

```bash
python3 -m unittest tests.test_grades_are_never_rewritten_by_the_app
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "apps" / "core" / "app"
NODE = ROOT / "apps" / "node" / "app"
GRADE = ("trust_domain", "compute_tier_max", "task_trust_domain", "node_trust_domain", "capability_tier", "node_tier_max")
# 등급 이름을 본문으로 받아도 되는 모델과 그 이유
GRADE_BODY_MODELS = {
    "TaskCreate": "요청자의 신뢰 도메인 — 앱이 아니라 task 의 복합 FK 가 판정한다 (D23)",
    "InviteCreate": "초대장에 등급이 박힌다 — admin 만 발행 (G2)",
    "NodeCreate": "admin 직접 등록",
}


def _sql_strings() -> list[str]:
    out = []
    for p in sorted(CORE.glob("*.py")):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and "UPDATE" in node.value.upper():
                out.append(node.value)
    return out


class TestNoUpdateTouchesAGrade(unittest.TestCase):
    def test_no_set_of_a_grade_column(self) -> None:
        sqls = _sql_strings()
        self.assertGreaterEqual(len(sqls), 10, len(sqls))
        bad = []
        for s in sqls:
            m = re.search(r"\bSET\b(.*?)(?:\bWHERE\b|\bRETURNING\b|$)", s, re.S | re.I)
            if not m:
                continue
            for col in GRADE:
                if re.search(rf"\b{col}\s*=", m.group(1)):
                    bad.append(f"{col}: {s.strip()[:60]}")
        self.assertEqual([], bad, f"앱이 등급·스냅샷을 덮어쓴다: {bad}")

    def test_no_update_node_at_all(self) -> None:
        hits = [s.strip()[:60] for s in _sql_strings() if re.search(r"\bUPDATE\s+node\b", s, re.I)]
        self.assertEqual([], hits, f"UPDATE node 가 생겼다 — 등급 뒷문인지 봐야 한다: {hits}")


class TestOnlyAdminOrTheDbTakesAGradeFromABody(unittest.TestCase):
    def test_models_carrying_grade_fields_are_the_known_four(self) -> None:
        src = (CORE / "main.py").read_text(encoding="utf-8")
        carrying = {}
        for node in ast.parse(src).body:
            if isinstance(node, ast.ClassDef):
                fields = {st.target.id for st in node.body if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)}
                hit = sorted(fields & set(GRADE))
                if hit:
                    carrying[node.name] = hit
        self.assertEqual(set(GRADE_BODY_MODELS), set(carrying), carrying)

    def test_the_admin_three_are_required_admin(self) -> None:
        src = (CORE / "main.py").read_text(encoding="utf-8")
        for model in ("InviteCreate", "NodeCreate"):
            with self.subTest(model=model):
                m = re.search(rf"def \w+\([^)]*body: {model}\b.*?\n(.*?)(?=\n@app\.)", src, re.S)
                self.assertIsNotNone(m, f"{model} 을 받는 핸들러를 못 찾았다")
                assert m is not None
                self.assertIn('_require("admin", authorization)', m.group(1), f"{model} 핸들러가 admin 을 요구하지 않는다")


class TestTheNodeNeverSpeaksOfItsGrade(unittest.TestCase):
    def test_no_grade_word_in_node_app(self) -> None:
        files = sorted(NODE.glob("*.py"))
        self.assertTrue(files)
        for p in files:
            with self.subTest(file=p.name):
                self.assertNotRegex(p.read_text(encoding="utf-8"), r"trust_domain|compute_tier|is_gate_runner")


if __name__ == "__main__":
    unittest.main()
