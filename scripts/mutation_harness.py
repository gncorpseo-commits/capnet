#!/usr/bin/env python3
"""핀 검사가 **정말 무는가** — 등록된 변이를 심고, 검사가 우는지 보고, 되돌린다 (큐 #135).

배치 A–C 의 「핀」PR 은 뮤테이션을 **세션 안에서만** 돌렸다. 저장소에는 「울었다」는 문장만 남고 다시 돌릴 길이 없었다.
이 도구는 그 변이를 등록부(`MUTATIONS`)에 적어 두고 언제든 다시 돌린다. `tests/test_mutation_harness_registry.py` 가
등록부가 낡지 않게(파일·찾을 문자열·검사 모듈이 실재) 본다. 검사 자체는 아니라 `run_tests` 에 넣지 않는다 — 파일을 고쳤다 되돌리기 때문.

    python3 scripts/mutation_harness.py --list
    python3 scripts/mutation_harness.py            # 전부 (깨끗한 트리에서)
    python3 scripts/mutation_harness.py --only claim-autocommit

각 항목: 파일 · 찾을 문자열 → 바꿀 문자열(또는 `append`) · 울어야 하는 검사 모듈. 하나라도 안 울면 exit 1.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# id · 파일 · find · replace(None 이면 append) · 우는 검사 · 무엇을 흉내내나
MUTATIONS: list[dict[str, str | None]] = [
    {"id": "claim-autocommit", "file": "apps/core/app/db.py", "find": '"autocommit": False', "replace": '"autocommit": True',
     "test": "tests.test_claim_cannot_double", "why": "lock 이 INSERT 전에 풀린다 (#101)"},
    {"id": "gate-finish-any-state", "file": "apps/core/app/gate.py", "find": "   AND status = 'RUNNING'\n", "replace": "",
     "test": "tests.test_gate_state_moves_only_through_select", "why": "finish 가 이전 상태를 안 본다 (#88)"},
    {"id": "tier-hand-rank", "file": "apps/core/app/claim.py", "find": None, "replace": '\nRANK = {"S": 1, "M": 2, "L": 3}\n',
     "test": "tests.test_absolute_rules_are_enforced", "why": "손 순위표로 행렬 우회 (#107)"},
    {"id": "insert-select-literal", "file": "apps/core/app/claim.py", "find": None,
     "replace": '\nX_SQL = """INSERT INTO assignment (task_id) SELECT %(t)s"""\n',
     "test": "tests.test_absolute_rules_are_enforced", "why": "FROM 없는 SELECT (#108)"},
    {"id": "grade-update-node", "file": "apps/core/app/claim.py", "find": None,
     "replace": '\nDEMOTE_SQL = """UPDATE node SET trust_domain = %(d)s WHERE id = %(id)s"""\n',
     "test": "tests.test_grades_are_never_rewritten_by_the_app", "why": "앱이 등급을 덮어쓴다 (#102)"},
    {"id": "health-leaks-core-url", "file": "apps/node/app/main.py", "find": '        "node_id": NODE_ID,\n',
     "replace": '        "node_id": NODE_ID,\n        "core_url": CORE_URL,\n',
     "test": "tests.test_health_keys_are_pinned", "why": "/health 에 내부 설정 칸 (#111)"},
    {"id": "public-get-added", "file": "apps/core/app/main.py", "find": None,
     "replace": '\n@app.get("/v1/leak")\ndef leak() -> dict[str, Any]:\n    return {}\n',
     "test": "tests.test_public_get_set_agrees_everywhere", "why": "무인증 GET 이 늘었다 (#109)"},
    {"id": "gitignore-artifacts", "file": ".gitignore", "find": "artifacts/\n", "replace": "",
     "test": "tests.test_artifacts_never_reach_the_zip", "why": "채점 산출물이 추적된다 (#122)"},
    {"id": "sh-shebang", "file": "scripts/lib/tally.sh", "find": "#!/usr/bin/env bash", "replace": "#!/bin/sh",
     "test": "tests.test_scripts_set_errexit", "why": "pipefail 없는 셸 (#131)"},
    {"id": "ps1-no-stop", "file": "scripts/sanity.ps1", "find": '$ErrorActionPreference = "Stop"\n', "replace": "",
     "test": "tests.test_ps1_stop_on_first_error", "why": "PowerShell 이 실패 뒤로 흐른다 (#132)"},
    {"id": "demo-no-verdict", "file": "scripts/series_demo.sh", "find": 'if d["status"] != "COMPLETED":', "replace": "if False:",
     "test": "tests.test_demos_fail_red", "why": "데모가 실패해도 초록 (#126)"},
    {"id": "role-unknown-minimum-opens", "file": "apps/core/app/apikey.py", "find": "need = ROLE_RANK.get(minimum, 99)",
     "replace": "need = ROLE_RANK.get(minimum, 0)", "test": "tests.test_role_rank_fails_closed", "why": "오타 난 최소역할이 열린다 (#110)"},
]


def _apply(m: dict[str, str | None]) -> bytes:
    p = ROOT / str(m["file"])
    original = p.read_bytes()
    text = original.decode("utf-8")
    if m["find"] is None:
        text = text + str(m["replace"])
    else:
        if str(m["find"]) not in text:
            raise RuntimeError(f"{m['id']}: 찾을 문자열이 없다 — 등록부가 낡았다")
        text = text.replace(str(m["find"]), str(m["replace"]), 1)
    p.write_bytes(text.encode("utf-8"))
    return original


def _cries(test: str) -> bool:
    proc = subprocess.run([sys.executable, "-m", "unittest", "-q", test], cwd=ROOT, capture_output=True, text=True, timeout=600)
    return proc.returncode != 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    items = [m for m in MUTATIONS if a.only in (None, m["id"])]
    if a.list or not items:
        for m in MUTATIONS:
            print(f"{m['id']:28s} {m['file']:36s} → {m['test']}  ({m['why']})")
        return 0 if MUTATIONS else 1
    silent = []
    for m in items:
        p = ROOT / str(m["file"])
        original = _apply(m)
        try:
            cried = _cries(str(m["test"]))
        finally:
            p.write_bytes(original)
        print(f"{'운다  ' if cried else '조용함'} {m['id']}")
        if not cried:
            silent.append(str(m["id"]))
    print(f"{len(items) - len(silent)}/{len(items)} 운다" + (f" · 조용한 것: {silent}" if silent else ""))
    return 1 if silent else 0


if __name__ == "__main__":
    raise SystemExit(main())
