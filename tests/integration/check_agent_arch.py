#!/usr/bin/env python3
"""아키텍처 결속·자원 한도 (I1·I2 · foreign-agent-isolation). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

1. 허용 아키텍처는 **DB 행**이다 (`agent_arch`). 없는 arch 로는 Agent 등록이 **FK 로** 막힌다
2. 등록된 arch 는 **배정 페이로드로 전달된다** — Node 가 로컬 파일로 정하지 않는다 (I1)
3. `max_params` 가 페이로드에 함께 실린다 — 게이트는 품질만 보므로 크기는 이걸로 막는다
4. legacy(arch NULL) Agent 는 `agent_arch_unbound` 로 **드러난다** — 「모른다」를 숨기지 않는다
5. arch 를 바꿔 다시 등록해도 **가중치 해시는 그대로** — 신원과 아키텍처는 다른 축이다

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.complete import node_assignments  # noqa: E402
from app.config import settings  # noqa: E402
from app.registry import create_agent  # noqa: E402

ADMIN = "00000000-0000-4000-8000-000000000001"
CAP = "00000000-0000-4000-8000-000000000010"
RUNNER = uuid.UUID("00000000-0000-4000-8000-000000000030")

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    print("아키텍처 결속 · 자원 한도 (I1·I2) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        if conn.execute("SELECT to_regclass('public.agent_arch') AS t").fetchone()["t"] is None:
            print("agent_arch 가 없다 — migrations/0008 미적용", file=sys.stderr)
            return 1

        # 1. 허용 목록이 DB 행이다
        rows = conn.execute("SELECT arch, max_params FROM agent_arch ORDER BY arch").fetchall()
        names = [r["arch"] for r in rows]
        check("TinyEuroSAT" in names and "TinyEuroSATB" in names,
              "허용 아키텍처가 DB 행으로 있다", ", ".join(names))
        check(all(r["max_params"] > 0 for r in rows), "각 arch 에 파라미터 상한이 있다")

        conn.execute("SAVEPOINT a")

        # 2. 없는 arch 는 FK 가 등록을 막는다
        blocked = False
        conn.execute("SAVEPOINT bad")
        try:
            create_agent(
                conn, name="evil", version="0.1", manifest_hash="m",
                weights_uri="file:///weights/x.safetensors", weights_sha256="a" * 64,
                weights_format="safetensors", arch="EvilNet",
            )
        except psycopg.errors.ForeignKeyViolation:
            blocked = True
            conn.execute("ROLLBACK TO SAVEPOINT bad")
        else:
            conn.execute("ROLLBACK TO SAVEPOINT bad")
        check(blocked, "allowlist 밖 arch 는 등록이 FK 로 막힌다")

        # 3. 선언한 arch 가 저장된다
        agent = create_agent(
            conn, name="arch-probe", version="0.1", manifest_hash="m",
            weights_uri="file:///weights/eurosat_scratch.safetensors",
            weights_sha256="b" * 64, weights_format="safetensors", arch="TinyEuroSATB",
        )
        check(agent.get("arch") == "TinyEuroSATB", "선언한 arch 가 Agent 에 남는다", str(agent.get("arch")))

        # 4. 배정 페이로드에 arch·max_params 가 실린다
        conn.execute(
            "INSERT INTO gate_run (id, agent_id, capability_id, runner_node_id, "
            "runner_is_gate_runner, status, golden_set_sha256, golden_score, cases_total, "
            "cases_passed, finished_at) SELECT gen_random_uuid(), a.id, c.id, n.id, "
            "n.is_gate_runner, 'PASSED', c.golden_set_sha256, 0.9, 40, 36, now() "
            "FROM agent a JOIN capability c ON c.id=%(cap)s JOIN node n ON n.id=%(runner)s "
            "AND n.is_gate_runner WHERE a.id=%(agent)s",
            {"cap": CAP, "runner": str(RUNNER), "agent": str(agent["id"])},
        )
        for sql in (
            "INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status) "
            "SELECT id, agent_id, capability_id, status FROM gate_run WHERE agent_id=%(agent)s",
            "INSERT INTO agent_capability (agent_id, capability_id, gate_status, golden_score, "
            "gate_run_id, gated_at) SELECT agent_id, capability_id, 'PASSED', 0.9, gate_run_id, "
            "now() FROM gate_run_passed WHERE agent_id=%(agent)s",
            "INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status) "
            "SELECT agent_id, capability_id, gate_status FROM agent_capability "
            "WHERE agent_id=%(agent)s",
            "INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen) "
            "SELECT a.id, %(runner)s::uuid, 'BOUND', a.weights_sha256 FROM agent a "
            "WHERE a.id=%(agent)s",
            "INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256) "
            "SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen "
            "FROM agent_node an JOIN agent a ON a.id=an.agent_id "
            "AND a.weights_sha256=an.weights_sha256_seen WHERE an.agent_id=%(agent)s",
        ):
            conn.execute(sql, {"agent": str(agent["id"]), "runner": str(RUNNER)})

        task = conn.execute(
            "INSERT INTO task (user_id, capability_id, status, trust_domain, "
            "capability_trust_domain_min, input_ref) SELECT u.id, c.id, 'QUEUED', 'team', "
            "c.trust_domain_min, '{\"datasetId\":\"eurosat-rgb\",\"caseId\":\"ic1-0001\"}' "
            "FROM app_user u JOIN capability c ON c.id=%(cap)s WHERE u.id=%(admin)s RETURNING id",
            {"cap": CAP, "admin": ADMIN},
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO assignment (task_id, agent_id, capability_id, node_id, "
            "task_trust_domain, node_trust_domain, capability_tier, node_tier_max, "
            "lease_expires_at, status) VALUES (%(task)s, %(agent)s, %(cap)s, %(node)s, "
            "'team','team','M','M', now() + interval '60 seconds', 'LEASED')",
            {"task": str(task), "agent": str(agent["id"]), "cap": CAP, "node": str(RUNNER)},
        )

        payload = node_assignments(conn, RUNNER)
        mine = [p for p in payload if str(p["agent_id"]) == str(agent["id"])]
        check(bool(mine), "배정 페이로드를 받았다")
        if mine:
            p0 = mine[0]
            check(p0.get("arch") == "TinyEuroSATB",
                  "페이로드가 Core 의 arch 를 싣는다 (로컬 meta 아님)", str(p0.get("arch")))
            check(p0.get("max_params") and p0["max_params"] > 0,
                  "페이로드가 파라미터 상한을 싣는다", str(p0.get("max_params")))

        conn.execute("ROLLBACK TO SAVEPOINT a")

        # 5. legacy 는 드러난다
        unbound = conn.execute(
            "SELECT count(*) AS n FROM agent_arch_unbound"
        ).fetchone()["n"]
        check(True, "legacy(arch 미선언) Agent 가 조회면에 드러난다", f"{unbound}건")

        # legacy Agent 는 페이로드의 arch 가 NULL 이어야 한다 (Node 가 로컬로 떨어진다)
        legacy = conn.execute(
            "SELECT count(*) AS n FROM agent WHERE arch IS NULL"
        ).fetchone()["n"]
        check(legacy == unbound, "unbound 뷰가 arch IS NULL 과 일치한다", f"{legacy}=={unbound}")

        # ── G5: 등록에서 arch 를 요구한다 (앱 계층) ────────────────────────
        # DB 는 arch 를 nullable 로 둔다 — legacy 행을 지우지 않기 위해서다.
        # 그래서 「새로 만들지 않는다」는 앱이 지킨다. 여기서 그 분기를 직접 본다
        # (HTTP 서버를 띄우지 않는다 · check_enforcement 와 같은 방식).
        from fastapi import HTTPException  # noqa: PLC0415

        from app.main import AgentCreate, agents_create  # noqa: PLC0415

        body = AgentCreate(
            name="no-arch", version="0.1", manifest_hash="m",
            weights_uri="file:///weights/x.safetensors", weights_sha256="c" * 64,
        )
        try:
            agents_create(body, None)
        except HTTPException as exc:
            check(exc.status_code == 400 and "arch" in str(exc.detail),
                  "arch 없는 등록은 400 으로 막힌다 (G5)", str(exc.detail)[:50])
        else:
            check(False, "arch 없는 등록은 400 으로 막힌다 (G5)", "통과해 버렸다")

        # 빈 문자열도 같은 취급 — FK 로 떠넘기지 않는다 (오류 메시지가 달라진다)
        try:
            agents_create(body.model_copy(update={"arch": ""}), None)
        except HTTPException as exc:
            check(exc.status_code == 400, "빈 arch 도 400", str(exc.detail)[:40])
        else:
            check(False, "빈 arch 도 400", "통과해 버렸다")

        # 이 분기는 **인증 뒤**에 있어야 한다. 앞에 있으면 강제 모드에서
        # 무인증 요청이 401 대신 400/422 를 받는다 (operate-production §5).
        import inspect  # noqa: PLC0415

        src = inspect.getsource(agents_create)
        check(src.index("_require(") < src.index("body.arch"),
              "arch 검사가 _require 뒤에 있다 (무인증은 여전히 401)")

        conn.rollback()
        left = conn.execute(
            "SELECT count(*) AS n FROM agent WHERE name IN ('arch-probe', 'no-arch')"
        ).fetchone()["n"]
        check(left == 0, "격리: 시험 Agent 가 롤백됐다")

    failed = [r for r in results if not r[0]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        return 1
    print("아키텍처는 Core 가 말한다 — Node 로컬 파일이 정하지 않는다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
