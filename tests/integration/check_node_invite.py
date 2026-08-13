#!/usr/bin/env python3
"""초대 경로 (G2 · 0016). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

초대는 **관리 키 없이 쓰기가 일어나는 유일한 경로**다. 그래서 여기서 보는 것은
「동작하나」가 아니라 **「무엇이 못 일어나나」**다.

1. 등급은 **초대장이** 정한다 — 소진 요청 본문이 바꾸지 못한다 (절대규칙 4)
2. `team` 초대는 **발행 자체가** 거절된다 (`ck_invite_domain`)
3. 초대로 들어온 기기는 **채점자가 될 수 없다** (`ck_gate_runner_team`)
4. 1회용이 실제로 1회다 — 두 번째 소진은 거절되고 `redeemed_count` 는 상한을 못 넘는다
5. 만료·폐기된 초대는 안 통한다
6. 틀린 시크릿은 **prefix 가 맞아도** 안 통한다 (존재를 캐지 못한다)
7. 소진은 **DB 가 판정한다** — CLAIM 을 직접 두 번 불러도 상한을 못 넘는다
8. 증적이 남는다 — `audit_log` · `node_invite_redemption`
9. 시크릿은 목록·조회면에 **나오지 않는다**

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.config import settings  # noqa: E402
from app.invite import (  # noqa: E402
    CLAIM_SQL,
    InviteError,
    issue_invite,
    list_invites,
    looks_like_invite,
    redeem_invite,
    revoke_invite,
    verify_invite,
)
from app.registry import create_node  # noqa: E402

ADMIN = uuid.UUID("00000000-0000-4000-8000-000000000001")

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def redeem(conn: psycopg.Connection, token: str, name: str) -> dict:
    """`POST /v1/nodes/redeem` 이 하는 일과 같은 순서."""
    invite = verify_invite(conn, token)
    node = create_node(
        conn,
        name=name,
        device_type="PC_GPU",
        trust_domain=invite["trust_domain"],     # 초대장 값
        compute_tier_max=invite["compute_tier_max"],
        is_gate_runner=False,
        gpu=None,
        provision_source="invited",
    )
    redeem_invite(conn, invite=invite, node_id=node["id"], node_name=name)
    return node


def main() -> int:
    print("초대 경로 (G2) — 전부 롤백된다\n")
    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False) as conn:
        if conn.execute("SELECT to_regclass('public.node_invite') AS t").fetchone()["t"] is None:
            print("node_invite 가 없다 — migrations/0016 미적용", file=sys.stderr)
            return 1
        conn.execute("SAVEPOINT s")

        # ── 1. team 초대는 발행 자체가 거절된다 ────────────────────────────
        conn.execute("SAVEPOINT bad")
        try:
            issue_invite(conn, issued_by=ADMIN, trust_domain="team")
        except InviteError as exc:
            check("ck_invite_domain" in str(exc), "team 초대는 발행이 거절된다", str(exc)[:52])
        else:
            check(False, "team 초대는 발행이 거절된다", "발행돼 버렸다")
        conn.execute("ROLLBACK TO SAVEPOINT bad")

        # ── 2. 발행 — 등급이 초대장에 박힌다 ───────────────────────────────
        inv = issue_invite(
            conn, issued_by=ADMIN, trust_domain="tenant", compute_tier_max="M",
            label="러닝크루", ttl_days=7,
        )
        check(inv["trust_domain"] == "tenant" and inv["compute_tier_max"] == "M",
              "발행 시 등급이 초대장에 박힌다", f"{inv['trust_domain']}/{inv['compute_tier_max']}")
        check(inv["max_redemptions"] == 1, "기본은 1회용", str(inv["max_redemptions"]))
        days = (inv["expires_at"] - inv["created_at"]).days
        check(days == 7, "기본 TTL 7일", f"{days}일")
        check(looks_like_invite(inv["secret"]) and inv["secret"].startswith("ci_"),
              "토큰 모양이 ci_ 다", inv["secret"][:11] + "…")

        # ── 3. 틀린 시크릿 — prefix 가 맞아도 안 통한다 ────────────────────
        prefix = inv["key_prefix"]
        try:
            verify_invite(conn, f"{prefix}.wrong-secret-wrong-secret")
        except InviteError as exc:
            check("유효하지 않다" in str(exc), "틀린 시크릿은 거절 (존재를 캐지 못한다)", str(exc))
        else:
            check(False, "틀린 시크릿은 거절", "통과해 버렸다")

        # ── 4. 소진 — 등급은 초대장이 정한다 ───────────────────────────────
        node = redeem(conn, inv["secret"], "crew-laptop-1")
        check(node["trust_domain"] == "tenant" and node["provision_source"] == "invited",
              "소진하면 초대장 등급으로 Node 가 생긴다",
              f"{node['trust_domain']}/{node['provision_source']}")
        check(node["is_gate_runner"] is False, "초대로 들어온 기기는 게이트러너가 아니다")

        # 요청이 등급을 주장해도 소용없다 — redeem() 은 초대장 값만 쓴다.
        # 그 「주장」을 흉내 내 직접 team 으로 만들어 보면 DB 가 막는다.
        conn.execute("SAVEPOINT claim")
        try:
            create_node(
                conn, name="liar", device_type="PC_GPU", trust_domain="team",
                compute_tier_max="M", is_gate_runner=False, gpu=None,
                provision_source="invited",
            )
        except ValueError as exc:
            check("ck_trust_provision_align" in str(exc),
                  "invited 는 team 등급이 될 수 없다 (DB 가 막는다)", str(exc)[:52])
        else:
            check(False, "invited 는 team 등급이 될 수 없다", "만들어져 버렸다")
        conn.execute("ROLLBACK TO SAVEPOINT claim")

        # 초대로 들어온 기기를 게이트러너로 만들려 하면 DB 가 막는다
        conn.execute("SAVEPOINT runner")
        try:
            conn.execute(
                "UPDATE node SET is_gate_runner = true WHERE id = %s", (str(node["id"]),)
            )
        except psycopg.errors.CheckViolation as exc:
            check("ck_gate_runner_team" in str(exc.diag.constraint_name or ""),
                  "초대 기기는 채점자가 될 수 없다 (절대규칙 8 유지)",
                  str(exc.diag.constraint_name))
        else:
            check(False, "초대 기기는 채점자가 될 수 없다", "승격돼 버렸다")
        conn.execute("ROLLBACK TO SAVEPOINT runner")

        # ── 5. 1회용이 실제로 1회다 ───────────────────────────────────────
        try:
            redeem(conn, inv["secret"], "crew-laptop-2")
        except InviteError as exc:
            check("REDEEMED" in str(exc) or "쓸 수 없다" in str(exc),
                  "두 번째 소진은 거절된다", str(exc)[:46])
        else:
            check(False, "두 번째 소진은 거절된다", "두 대가 만들어졌다")

        row = conn.execute(
            "SELECT redeemed_count, max_redemptions, state FROM node_invite_status "
            "WHERE id = %s", (str(inv["id"]),)
        ).fetchone()
        check(row["redeemed_count"] == 1 and row["state"] == "REDEEMED",
              "소진 계수가 상한에서 멈춘다", f"{row['redeemed_count']}/{row['max_redemptions']} {row['state']}")

        # 앱을 건너뛰고 DB 를 직접 두들겨도 상한을 못 넘는다 — 판정은 WHERE 절이 한다
        again = conn.execute(CLAIM_SQL, {"id": str(inv["id"])}).fetchone()
        check(again is None, "CLAIM 을 직접 불러도 상한을 못 넘는다 (DB 가 판정)")

        # ── 6. 증적 ───────────────────────────────────────────────────────
        aud = conn.execute(
            "SELECT payload FROM audit_log WHERE event = 'invite.redeemed' "
            "ORDER BY at DESC LIMIT 1"
        ).fetchone()
        payload = aud["payload"] if aud else {}
        if isinstance(payload, str):
            payload = json.loads(payload)
        check(aud is not None and str(payload.get("node_id")) == str(node["id"]),
              "소진이 audit_log 에 남는다", str(payload.get("trust_domain")))
        link = conn.execute(
            "SELECT invite_id FROM node_invite_redemption WHERE node_id = %s",
            (str(node["id"]),),
        ).fetchone()
        check(link is not None and str(link["invite_id"]) == str(inv["id"]),
              "「이 기기가 어느 초대로 들어왔나」에 답한다")

        # ── 7. 만료·폐기 ──────────────────────────────────────────────────
        exp = issue_invite(conn, issued_by=ADMIN, trust_domain="public", ttl_days=1)
        conn.execute(
            "UPDATE node_invite SET expires_at = now() - interval '1 second' WHERE id = %s",
            (str(exp["id"]),),
        )
        try:
            verify_invite(conn, exp["secret"])
        except InviteError as exc:
            check("EXPIRED" in str(exc), "만료된 초대는 안 통한다", str(exc)[:40])
        else:
            check(False, "만료된 초대는 안 통한다", "통과해 버렸다")

        rev = issue_invite(conn, issued_by=ADMIN, trust_domain="public")
        revoke_invite(conn, invite_id=rev["id"], reason="test")
        try:
            verify_invite(conn, rev["secret"])
        except InviteError as exc:
            check("REVOKED" in str(exc), "폐기된 초대는 안 통한다", str(exc)[:40])
        else:
            check(False, "폐기된 초대는 안 통한다", "통과해 버렸다")

        # ── 8. 시크릿이 조회면에 없다 ─────────────────────────────────────
        items = list_invites(conn)
        blob = json.dumps(items, default=str)
        secrets_seen = [i["secret"] for i in (inv, exp, rev) if i["secret"] in blob]
        check(not secrets_seen and "secret_hash" not in blob,
              "목록에 시크릿도 해시도 없다", f"{len(items)}건 · prefix 만")
        check(any(i["key_prefix"] == inv["key_prefix"] for i in items),
              "prefix 는 보인다 — 어느 초대인지는 답한다")

        conn.execute("ROLLBACK TO SAVEPOINT s")
        conn.rollback()
        left = conn.execute(
            "SELECT count(*) AS n FROM node WHERE name LIKE 'crew-laptop%'"
        ).fetchone()["n"]
        check(left == 0, "격리: 시험 Node 가 롤백됐다")

    ok = sum(1 for r in results if r[0])
    print(f"\n{ok}/{len(results)} 통과")
    if ok != len(results):
        return 1
    print("등급은 초대장이 정한다 — 소진하는 쪽이 주장하지 못한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
