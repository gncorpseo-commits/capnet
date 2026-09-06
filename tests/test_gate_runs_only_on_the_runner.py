r"""게이트러너가 아닌 Node 에서 게이트를 돌릴 API·스크립트는 **0** (배치 C #103 · 절대규칙 8).

## 실측 (2026-09-06)

| 길 | 문 |
|---|---|
| Core `gate_run` INSERT | `INSERT … SELECT n.is_gate_runner` 스냅샷 + `CHECK (runner_is_gate_runner)` + `ck_gate_runner_team` (`test_absolute_rules_are_enforced` 가 본다) |
| 러너 자격이 생기는 곳 | `NodeCreate.is_gate_runner`(admin) 하나 — 소진(redeem)은 `is_gate_runner=False` 로 못박혀 있다 |
| Node 앱의 라우트 | `/health` · `/v1/execute` 둘뿐 — 게이트를 시작·채점하는 라우트 **없음** |
| 채점을 실제로 돌리는 스크립트(`score_gate`·`contract_check` exec) | 7곳 전부 `node-m-team` 또는 기본값이 `node-m-team` 인 `$runner_svc` |
| 계약 샘플 바이트 | `is_gate_runner(conn, node_id)` 뒤에만 |

`/finish` 는 developer 키가 부른다 — 어느 기기가 셈했는지는 Core 가 못 본다(설계상 team 러너 전제).
그래서 **스크립트가 어디서 exec 하는가**가 실질적 문이고, 여기서 그것을 센다.

## 재현

```bash
python3 -m unittest tests.test_gate_runs_only_on_the_runner
```
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

CORE_MAIN = ROOT / "apps" / "core" / "app" / "main.py"
NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"
SCRIPTS = ROOT / "scripts"
RUNNER = "node-m-team"


class TestTheNodeHasNoGateDoor(unittest.TestCase):
    def test_node_routes_are_exactly_two(self) -> None:
        routes = sorted(re.findall(r'@app\.(?:get|post|put|patch|delete)\("([^"]+)"', NODE_MAIN.read_text(encoding="utf-8")))
        self.assertEqual(["/health", "/v1/execute"], routes, routes)


class TestScoringHappensOnTheRunnerOnly(unittest.TestCase):
    def test_every_scoring_exec_targets_the_runner(self) -> None:
        sites, bad = [], []
        for p in sorted(SCRIPTS.glob("*.sh")):
            # `exec -T … \` 다음 줄에 `score_gate` 가 오는 스크립트가 둘이다 — 이어진 줄을 합쳐 본다.
            joined = re.sub(r"\\\n\s*", " ", hash_comment_free(p))
            for i, ln in enumerate(joined.splitlines(), 1):
                if not re.search(r"\b(score_gate|contract_check)\b", ln) or "exec" not in ln:
                    continue
                sites.append(f"{p.name}:{i}")
                m = re.search(r'exec\s+-T\s+("?\$\{?(\w+)\}?"?|[\w-]+)', ln)
                target = m.group(1) if m else ""
                if target == RUNNER:
                    continue
                if m and m.group(2):   # 변수면 기본값이 러너여야 한다
                    default = re.search(rf'^{m.group(2)}="\$\{{\w+:-([\w-]+)\}}"', hash_comment_free(p), re.M)
                    if default and default.group(1) == RUNNER:
                        continue
                bad.append(f"{p.name}:{i} → {target or '?'}")
        self.assertEqual(7, len(sites), sites)
        self.assertEqual([], bad, f"러너가 아닌 곳에서 채점한다: {bad}")


class TestRunnerStatusIsGrantedOnlyByAdmin(unittest.TestCase):
    def test_only_node_create_passes_the_flag_and_redeem_forces_false(self) -> None:
        src = CORE_MAIN.read_text(encoding="utf-8")
        passes = re.findall(r"is_gate_runner=(body\.is_gate_runner|False|True)", src)
        self.assertEqual(["body.is_gate_runner", "False"], passes, passes)
        h = src[src.index('@app.post("/v1/nodes")'):]
        h = h[:h.index("\n@app.")]
        self.assertIn('_require("admin", authorization)', h)
        self.assertIn("is_gate_runner=body.is_gate_runner", h)

    def test_schema_keeps_both_checks(self) -> None:
        schema = (ROOT / "docs" / "spec" / "schema.sql").read_text(encoding="utf-8")
        self.assertIn("CHECK (runner_is_gate_runner)", schema)
        self.assertIn("CONSTRAINT ck_gate_runner_team", schema)


if __name__ == "__main__":
    unittest.main()
