#!/usr/bin/env python3
"""조직 경계 (D24 · 0017). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

`trust_domain` 은 **민감도 등급**이지 **어느 조직**이 아니다. tenant 가 둘이면 둘 다
`'tenant'` 라 `domain_compatible` 이 구별하지 못했고, **조직 A 의 작업이 조직 B 의 기기에
배정됐다.** 조회 문제가 아니라 **실행 문제**였다.

1. **A 의 작업은 B 의 기기로 안 간다** — `claim` 이 고르지 않는다
2. **DB 가 마지막 방어선이다** — 앱을 건너뛰고 배정을 직접 넣어도 `ck_assignment_org` 가 거절
3. **공용 기기(`org_id IS NULL`)는 모든 조직을 받는다** — 팀 운영 기기 (D24-1)
4. 같은 조직 기기로는 정상 배정된다 (가용성이 안 깨진다)
5. **스냅샷이 진짜 행과 같아야 한다** — 복합 FK 가 거짓 스냅샷을 거절
6. **조회 격리** — 남의 조직 작업은 404, 함대 목록은 자기 조직 + 공용만
7. **초대가 조직을 정한다** — 소진 요청은 조직을 주장하지 못한다 (D24-2)

`claim`·조회는 커밋된 데이터를 봐야 하므로 **커밋하고 끝에서 지운다**
(`check_task_ownership` 과 같은 사정).

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import importlib
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))
os.environ.setdefault("REQUIRE_LIVE_NODE", "0")

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.apikey import ensure_user, issue_key  # noqa: E402
from app.claim import claim_next  # noqa: E402
from app.config import settings  # noqa: E402
from app.invite import issue_invite, redeem_invite, verify_invite  # noqa: E402
from app.registry import create_node  # noqa: E402

ADMIN = "00000000-0000-4000-8000-000000000001"
CAP_TENANT = "00000000-0000-4000-8000-000000000011"  # image.classify@2 · min=tenant
AGENT = "00000000-0000-4000-8000-000000000020"
RUNNER = "00000000-0000-4000-8000-000000000030"

results: list[tuple[bool, str, str]] = []
made: dict[str, list[str]] = {"node": [], "task": [], "org": [], "user": [], "invite": []}


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def gate_agent(conn: psycopg.Connection) -> None:
    """seed Agent 를 tenant 능력에 통과시킨다 (조직과 무관 — Agent 는 공용 카탈로그)."""
    gr = conn.execute(
        "INSERT INTO gate_run (agent_id, capability_id, runner_node_id, runner_is_gate_runner,"
        " status, golden_set_sha256, golden_score, cases_total, cases_passed, finished_at)"
        " SELECT a.id, c.id, n.id, n.is_gate_runner, 'PASSED', c.golden_set_sha256, 0.9, 40, 36, now()"
        " FROM agent a JOIN capability c ON c.id=%s JOIN node n ON n.id=%s AND n.is_gate_runner"
        " WHERE a.id=%s RETURNING id",
        (CAP_TENANT, RUNNER, AGENT),
    ).fetchone()["id"]
    for sql in (
        "INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status)"
        " SELECT id, agent_id, capability_id, status FROM gate_run WHERE id=%(gr)s",
        "INSERT INTO agent_capability (agent_id, capability_id, gate_status, golden_score,"
        " gate_run_id, gated_at) SELECT agent_id, capability_id, 'PASSED', 0.9, gate_run_id, now()"
        " FROM gate_run_passed WHERE gate_run_id=%(gr)s"
        " ON CONFLICT (agent_id, capability_id) DO UPDATE SET gate_status='PASSED'",
        "INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status)"
        " SELECT agent_id, capability_id, gate_status FROM agent_capability WHERE gate_run_id=%(gr)s"
        " ON CONFLICT (agent_id, capability_id) DO UPDATE SET revoked_at=NULL",
    ):
        conn.execute(sql, {"gr": str(gr)})


def bind(conn: psycopg.Connection, node_id) -> None:
    conn.execute(
        "INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen)"
        " SELECT a.id, %(n)s::uuid, 'BOUND', a.weights_sha256 FROM agent a WHERE a.id=%(a)s"
        " ON CONFLICT (agent_id, node_id) DO NOTHING",
        {"n": str(node_id), "a": AGENT},
    )
    conn.execute(
        "INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256)"
        " SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen FROM agent_node an"
        " JOIN agent a ON a.id=an.agent_id AND a.weights_sha256=an.weights_sha256_seen"
        " WHERE an.node_id=%(n)s::uuid ON CONFLICT (agent_id, node_id) DO NOTHING",
        {"n": str(node_id)},
    )


def make_task(conn: psycopg.Connection, *, user_id, org_id) -> uuid.UUID:
    tid = conn.execute(
        "INSERT INTO task (user_id, capability_id, status, trust_domain,"
        " capability_trust_domain_min, input_ref, org_id)"
        " SELECT %s, c.id, 'QUEUED', 'tenant', c.trust_domain_min, '{\"caseId\":\"ic1-0001\"}', %s"
        " FROM capability c WHERE c.id=%s RETURNING id",
        (str(user_id), str(org_id) if org_id else None, CAP_TENANT),
    ).fetchone()["id"]
    made["task"].append(str(tid))
    return tid


def main() -> int:
    print("조직 경계 (D24) — 커밋하고 끝에서 지운다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        if conn.execute("SELECT to_regclass('public.org') AS t").fetchone()["t"] is None:
            print("org 가 없다 — migrations/0017 미적용", file=sys.stderr)
            return 1

        try:
            # ── 조직 둘 + 각 조직의 tenant 기기 ─────────────────────────
            orgs = {}
            for code in ("probe-a", "probe-b"):
                orgs[code] = conn.execute(
                    "INSERT INTO org (code, name) VALUES (%s, %s) RETURNING id", (code, code)
                ).fetchone()["id"]
                made["org"].append(str(orgs[code]))

            ua = ensure_user(conn, name="org-a-user", role="developer")
            conn.execute("UPDATE app_user SET org_id=%s WHERE id=%s", (orgs["probe-a"], ua["id"]))
            ub = ensure_user(conn, name="org-b-user", role="developer")
            conn.execute("UPDATE app_user SET org_id=%s WHERE id=%s", (orgs["probe-b"], ub["id"]))
            made["user"] += [str(ua["id"]), str(ub["id"])]
            key_a = issue_key(conn, user_id=ua["id"], label="a")["secret"]
            key_b = issue_key(conn, user_id=ub["id"], label="b")["secret"]

            nodes = {}
            for code, org in (("a", orgs["probe-a"]), ("b", orgs["probe-b"]), ("shared", None)):
                n = create_node(
                    conn, name=f"probe-node-{code}", device_type="PC_GPU",
                    trust_domain="tenant", compute_tier_max="M", is_gate_runner=False,
                    gpu=None, provision_source="invited", org_id=org, owner_id=ADMIN,
                )
                nodes[code] = n
                made["node"].append(str(n["id"]))
            check(nodes["a"]["org_id"] is not None and nodes["shared"]["org_id"] is None,
                  "기기에 조직이 붙는다 (None = 공용)",
                  f"a={str(nodes['a']['org_id'])[:8]} shared=None")

            gate_agent(conn)
            for n in nodes.values():
                bind(conn, n["id"])
            conn.commit()

            # ── 1. A 의 작업은 B 의 기기로 안 간다 ──────────────────────
            t = make_task(conn, user_id=ua["id"], org_id=orgs["probe-a"])
            conn.commit()
            check(claim_next(conn, task_id=t, node_id=nodes["b"]["id"]) is None,
                  "조직 A 의 작업은 조직 B 의 기기로 배정되지 않는다")

            # ── 2. DB 가 마지막 방어선 — 앱을 건너뛰어도 거절 ───────────
            refused = ""
            try:
                conn.execute(
                    "INSERT INTO assignment (task_id, agent_id, capability_id, node_id,"
                    " task_trust_domain, node_trust_domain, capability_tier, node_tier_max,"
                    " task_org_id, node_org_id, lease_expires_at, status)"
                    " SELECT t.id, %(a)s, t.capability_id, n.id, t.trust_domain, n.trust_domain,"
                    " 'M', n.compute_tier_max, t.org_id, n.org_id, now() + interval '60 seconds', 'LEASED'"
                    " FROM task t, node n WHERE t.id=%(t)s AND n.id=%(n)s",
                    {"t": str(t), "n": str(nodes["b"]["id"]), "a": AGENT},
                )
            except psycopg.errors.CheckViolation as exc:
                refused = exc.diag.constraint_name or ""
                conn.rollback()
            check(refused == "ck_assignment_org",
                  "앱을 건너뛰어도 DB 가 거절한다", refused or "거절 안 됨")

            # ── 3·4. 공용 기기는 받는다 · 같은 조직도 받는다 ────────────
            t2 = make_task(conn, user_id=ua["id"], org_id=orgs["probe-a"])
            conn.commit()
            got = claim_next(conn, task_id=t2, node_id=nodes["shared"]["id"])
            check(got is not None, "공용 기기(org NULL)는 모든 조직의 작업을 받는다")
            t3 = make_task(conn, user_id=ua["id"], org_id=orgs["probe-a"])
            conn.commit()
            got3 = claim_next(conn, task_id=t3, node_id=nodes["a"]["id"])
            check(got3 is not None, "같은 조직 기기로는 정상 배정된다 (가용성이 안 깨진다)")
            check(got3 and str(got3["task_org_id"]) == str(got3["node_org_id"]),
                  "배정에 조직 스냅샷이 실린다",
                  str(got3["task_org_id"])[:8] if got3 else "")
            conn.commit()

            # ── 5. 거짓 스냅샷은 복합 FK 가 거절 ────────────────────────
            t4 = make_task(conn, user_id=ua["id"], org_id=orgs["probe-a"])
            conn.commit()
            fk = ""
            try:
                conn.execute(
                    "INSERT INTO assignment (task_id, agent_id, capability_id, node_id,"
                    " task_trust_domain, node_trust_domain, capability_tier, node_tier_max,"
                    " task_org_id, node_org_id, lease_expires_at, status)"
                    " SELECT t.id, %(a)s, t.capability_id, n.id, t.trust_domain, n.trust_domain,"
                    " 'M', n.compute_tier_max, %(fake)s, %(fake)s, now() + interval '60 seconds', 'LEASED'"
                    " FROM task t, node n WHERE t.id=%(t)s AND n.id=%(n)s",
                    {"t": str(t4), "n": str(nodes["b"]["id"]), "a": AGENT,
                     "fake": str(orgs["probe-b"])},
                )
            except psycopg.errors.ForeignKeyViolation as exc:
                fk = exc.diag.constraint_name or ""
                conn.rollback()
            check(fk == "assignment_task_org_fkey",
                  "거짓 조직 스냅샷은 복합 FK 가 거절한다", fk or "거절 안 됨")

            # ── 6. 조회 격리 ────────────────────────────────────────────
            os.environ["REQUIRE_API_KEY"] = "1"
            import app.main as m  # noqa: PLC0415

            m = importlib.reload(m)
            from fastapi import HTTPException  # noqa: PLC0415

            code = "pass"
            try:
                m.get_task(t, f"CapNet-Key {key_b}")
            except HTTPException as exc:
                code = exc.status_code
            check(code == 404, "남의 조직 작업은 404", str(code))
            got = m.get_task(t, f"CapNet-Key {key_a}")
            check(str(got["id"]) == str(t), "자기 조직 작업은 보인다")

            names = {n["name"] for n in m.nodes_list(f"CapNet-Key {key_a}")["items"]}
            check("probe-node-a" in names and "probe-node-shared" in names
                  and "probe-node-b" not in names,
                  "함대 목록은 자기 조직 + 공용만",
                  f"{sorted(x for x in names if x.startswith('probe-'))}")

            # ── 7. 초대가 조직을 정한다 ─────────────────────────────────
            inv = issue_invite(conn, issued_by=uuid.UUID(ADMIN), trust_domain="tenant",
                               org_id=orgs["probe-b"], label="org-probe")
            made["invite"].append(str(inv["id"]))
            conn.commit()
            iv = verify_invite(conn, inv["secret"])
            check(str(iv["org_id"]) == str(orgs["probe-b"]), "초대장에 조직이 박힌다")
            n = create_node(conn, name="probe-node-invited", device_type="PC_GPU",
                            trust_domain=iv["trust_domain"], compute_tier_max=iv["compute_tier_max"],
                            is_gate_runner=False, gpu=None, provision_source="invited",
                            org_id=iv["org_id"], owner_id=iv["issued_by"])
            made["node"].append(str(n["id"]))
            redeem_invite(conn, invite=iv, node_id=n["id"], node_name="probe-node-invited")
            check(str(n["org_id"]) == str(orgs["probe-b"]),
                  "소진하면 초대장의 조직으로 기기가 생긴다 (요청이 주장하지 못한다)")
            check(str(n["owner_id"]) == str(ADMIN),
                  "소유자가 실제로 기록된다 (시드 하드코딩 제거)", str(n["owner_id"])[:8])
            conn.commit()
        finally:
            os.environ.pop("REQUIRE_API_KEY", None)
            conn.rollback()
            # 지우는 순서가 있다 — task.current_assignment_id 가 assignment 를 가리킨다.
            conn.execute(
                "UPDATE task SET current_assignment_id = NULL WHERE id = ANY(%s)",
                (made["task"],),
            )
            conn.execute("DELETE FROM assignment WHERE task_id = ANY(%s)", (made["task"],))
            conn.execute("DELETE FROM audit_log WHERE task_id = ANY(%s)", (made["task"],))
            conn.execute("DELETE FROM task WHERE id = ANY(%s)", (made["task"],))
            conn.execute(
                "DELETE FROM node_invite_redemption WHERE node_id = ANY(%s)", (made["node"],)
            )
            conn.execute("DELETE FROM agent_node_ready WHERE node_id = ANY(%s)", (made["node"],))
            conn.execute("DELETE FROM agent_node WHERE node_id = ANY(%s)", (made["node"],))
            conn.execute("DELETE FROM node_session WHERE node_id = ANY(%s)", (made["node"],))
            conn.execute("DELETE FROM node WHERE id = ANY(%s)", (made["node"],))
            conn.execute("DELETE FROM node_invite WHERE id = ANY(%s)", (made["invite"],))
            conn.commit()
            left = conn.execute(
                "SELECT count(*) AS n FROM node WHERE name LIKE 'probe-node-%'"
            ).fetchone()["n"]
            check(left == 0, "격리: 시험 행이 지워졌다", f"{left}건 남음")

    ok = sum(1 for r in results if r[0])
    print(f"\n{ok}/{len(results)} 통과")
    if ok != len(results):
        return 1
    print("등급은 민감도, 조직은 소속 — 두 축을 섞지 않는다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
