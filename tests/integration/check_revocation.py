#!/usr/bin/env python3
"""폐기 경로 통합 시험 (SD-014). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다. CI 의 migrate job 이 마이그레이션을 올린 뒤 경로로 직접 부른다.

여기서 고정하는 계약:
  1. 근거 없는 폐기는 **거부**된다 (현재 골든셋에서 FAILED 인 gate_run 이 있어야)
  2. 폐기해도 **행은 남는다** — assignment 가 FK 로 참조하므로 삭제는 불가능하다 (D15)
  3. 폐기하면 claim 이 **배정하지 않는다**
  4. 다시 통과하면 **복권**된다 (폐기는 형벌이 아니다)
  5. `agent.status='DISABLED'` 도 라우팅을 막는다 (이전엔 claim 이 무시했다)

환경: DATABASE_URL · PYTHONPATH=apps/core · REQUIRE_LIVE_NODE=0
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))
os.environ.setdefault("REQUIRE_LIVE_NODE", "0")

from app.claim import claim_next  # noqa: E402
from app.db import get_conn  # noqa: E402
from app.gate import (  # noqa: E402
    RevokeRefused,
    finish_gate_run,
    revoke_capability,
    start_gate_run,
)

CAP = uuid.UUID("00000000-0000-4000-8000-000000000010")
AGENT = uuid.UUID("00000000-0000-4000-8000-000000000020")
RUNNER = uuid.UUID("00000000-0000-4000-8000-000000000030")
ADMIN = "00000000-0000-4000-8000-000000000001"

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(name)


def new_task(conn, case_id: str) -> uuid.UUID:
    row = conn.execute(
        """
        INSERT INTO task (user_id, capability_id, status, trust_domain,
                          capability_trust_domain_min, input_ref)
        SELECT u.id, c.id, 'QUEUED', 'team', c.trust_domain_min, %s
          FROM app_user u JOIN capability c ON c.id = %s
         WHERE u.id = %s
        RETURNING id
        """,
        ('{"datasetId":"eurosat-rgb","caseId":"%s"}' % case_id, str(CAP), ADMIN),
    ).fetchone()
    return row["id"]


def pass_gate(conn, note: str) -> None:
    gr = start_gate_run(conn, agent_id=AGENT, capability_id=CAP, runner_node_id=RUNNER)
    finish_gate_run(
        conn,
        gate_run_id=gr["id"],
        status="PASSED",
        golden_score=0.90,
        cases_total=40,
        cases_passed=36,
        dummy=False,
        note=note,
        macro_f1=0.90,
        invalid_rate=0.0,
        min_per_class_recall=0.5,
        golden_set_sha256=gr["golden_set_sha256"],
    )


def fail_gate(conn) -> None:
    """현재 골든셋에서 떨어진 gate_run — 폐기 근거를 만든다."""
    conn.execute(
        """
        INSERT INTO gate_run (agent_id, capability_id, runner_node_id, runner_is_gate_runner,
                              status, golden_set_sha256, golden_score, cases_total,
                              cases_passed, finished_at)
        SELECT a.id, c.id, n.id, n.is_gate_runner, 'FAILED', c.golden_set_sha256,
               0.10, 40, 4, now()
          FROM agent a JOIN capability c ON c.id = %s
          JOIN node n ON n.id = %s AND n.is_gate_runner
         WHERE a.id = %s
        """,
        (str(CAP), str(RUNNER), str(AGENT)),
    )


def live_certs(conn) -> int:
    return conn.execute(
        "SELECT count(*) AS n FROM agent_capability_passed WHERE revoked_at IS NULL"
    ).fetchone()["n"]


def all_certs(conn) -> int:
    return conn.execute(
        "SELECT count(*) AS n FROM agent_capability_passed"
    ).fetchone()["n"]


def main() -> int:
    print("폐기 경로 통합 시험 (SD-014)")

    # 증서를 스스로 만든다. seed 는 더 이상 라우팅 증서를 발급하지 않는다 (SD-015).
    with get_conn() as conn:
        pass_gate(conn, "시험 준비 — 증서 발급")
    with get_conn() as conn:
        check("준비: 게이트 통과로 증서가 생긴다", live_certs(conn) == 1)

    # 대조군 — 정상 경로가 막히지 않았는지 먼저 본다.
    with get_conn() as conn:
        tid = new_task(conn, "ic1-0001")
    with get_conn() as conn:
        check("대조군: 살아있는 증서로 배정된다", claim_next(conn, task_id=tid) is not None)

    # 1. 근거 없는 폐기는 거부
    with get_conn() as conn:
        probe = conn.execute(
            """
            INSERT INTO agent (owner_id, name, version, manifest_hash,
                               weights_format, weights_uri, weights_sha256)
            VALUES (%s, 'revoke-probe', '0.1', 'm', 'safetensors', 'file:///w', %s)
            RETURNING id
            """,
            (ADMIN, "f" * 64),
        ).fetchone()["id"]
    refused = False
    try:
        with get_conn() as conn:
            revoke_capability(conn, agent_id=probe, capability_id=CAP, reason="근거 없음")
    except RevokeRefused:
        refused = True
    check("근거 없는 폐기는 거부된다", refused)

    # 2·3. 근거를 만든 뒤 폐기 → 행은 남고 라우팅은 끊긴다
    with get_conn() as conn:
        fail_gate(conn)
    with get_conn() as conn:
        before_rows = all_certs(conn)
        revoke_capability(conn, agent_id=AGENT, capability_id=CAP, reason="홀드아웃 미달")
    with get_conn() as conn:
        check("폐기해도 행은 남는다 (assignment FK)", all_certs(conn) == before_rows,
              f"{before_rows} → {all_certs(conn)}")
        check("폐기하면 live 증서가 0", live_certs(conn) == 0)
    with get_conn() as conn:
        tid = new_task(conn, "ic1-0002")
    with get_conn() as conn:
        check("폐기 후 claim 이 배정하지 않는다", claim_next(conn, task_id=tid) is None)

    # 폐기 이력이 조회되는가
    with get_conn() as conn:
        row = conn.execute(
            "SELECT revoked_reason, revoked_gate_run_id FROM revoked_capability LIMIT 1"
        ).fetchone()
        check("revoked_capability 뷰에 근거가 남는다",
              bool(row) and row["revoked_gate_run_id"] is not None)
        n = conn.execute(
            "SELECT count(*) AS n FROM audit_log WHERE event = 'capability_revoked'"
        ).fetchone()["n"]
        check("audit_log 에 폐기가 기록된다", n >= 1)

    # 4. 복권
    with get_conn() as conn:
        pass_gate(conn, "복권")
    with get_conn() as conn:
        check("다시 통과하면 복권된다", live_certs(conn) == 1)
    with get_conn() as conn:
        tid = new_task(conn, "ic1-0003")
    with get_conn() as conn:
        check("복권 후 claim 이 다시 배정한다", claim_next(conn, task_id=tid) is not None)

    # 5. agent.status
    with get_conn() as conn:
        conn.execute("UPDATE agent SET status='DISABLED' WHERE id=%s", (str(AGENT),))
    with get_conn() as conn:
        tid = new_task(conn, "ic1-0004")
    with get_conn() as conn:
        check("DISABLED agent 는 배정되지 않는다", claim_next(conn, task_id=tid) is None)
    with get_conn() as conn:
        conn.execute("UPDATE agent SET status='ACTIVE' WHERE id=%s", (str(AGENT),))

    # 뒷정리를 하지 않는다. 이 검사는 **커밋해야** 하고(트랜잭션 경계가 계약의 일부다),
    # 그 뒤처리를 여기서 떠안으면 「다음에 무엇이 오는지」를 이 파일이 알아야 한다.
    # 격리는 scripts/run_integration.sh 가 검사마다 DB 를 복제해서 준다.

    print()
    if failures:
        print(f"실패 {len(failures)}건: {', '.join(failures)}")
        return 1
    print("폐기 경로 전부 통과.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
