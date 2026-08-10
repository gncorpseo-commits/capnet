"""Agent / Node 등록·바인딩. 등급은 Core가 부여한다. Node 자기주장은 받지 않는다."""

from __future__ import annotations

import re
import json
import uuid
from typing import Any

import psycopg
from psycopg import errors as pg_errors

from app.const import SEED_ADMIN_ID, SHA256_HEX

_PT_RE = re.compile(r"\.(pt|pth)(\b|$)", re.IGNORECASE)


def assert_safetensors(weights_format: str, weights_uri: str) -> None:
    if weights_format != "safetensors":
        raise ValueError("weights_format must be safetensors")
    if _PT_RE.search(weights_uri):
        raise ValueError(".pt/.pth weights are rejected")


def assert_sha256(value: str) -> None:
    if not re.fullmatch(SHA256_HEX, value):
        raise ValueError("weights_sha256 must be 64 lowercase hex chars")


def list_agents(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, owner_id, name, version, status, manifest_hash, "
        "weights_format, weights_uri, weights_sha256, arch, created_at "
        "FROM agent ORDER BY created_at"
    ).fetchall()
    return [dict(r) for r in rows]


def get_agent(conn: psycopg.Connection, agent_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, owner_id, name, version, status, manifest_hash, "
        "weights_format, weights_uri, weights_sha256, arch, created_at "
        "FROM agent WHERE id = %s",
        (str(agent_id),),
    ).fetchone()
    return dict(row) if row else None


def create_agent(
    conn: psycopg.Connection,
    *,
    name: str,
    version: str,
    manifest_hash: str,
    weights_uri: str,
    weights_sha256: str,
    weights_format: str,
    arch: str | None = None,
) -> dict[str, Any]:
    assert_safetensors(weights_format, weights_uri)
    assert_sha256(weights_sha256)
    row = conn.execute(
        """
        INSERT INTO agent (
            owner_id, name, version, status,
            manifest_hash, weights_format, weights_uri, weights_sha256, arch
        )
        SELECT %(owner_id)s, %(name)s, %(version)s, 'ACTIVE',
               %(manifest_hash)s, 'safetensors', %(weights_uri)s, %(weights_sha256)s,
               %(arch)s
          FROM app_user u
         WHERE u.id = %(owner_id)s
        RETURNING id, owner_id, name, version, status, manifest_hash,
                  weights_format, weights_uri, weights_sha256, arch, created_at
        """,
        {
            "owner_id": SEED_ADMIN_ID,
            "name": name,
            "version": version,
            "manifest_hash": manifest_hash,
            "weights_uri": weights_uri,
            "weights_sha256": weights_sha256,
            "arch": arch,
        },
    ).fetchone()
    if row is None:
        raise RuntimeError("seed admin missing")
    return dict(row)


def list_nodes(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, owner_id, name, device_type, gpu, provision_source, "
        "trust_domain, compute_tier_max, is_gate_runner, created_at "
        "FROM node ORDER BY created_at"
    ).fetchall()
    return [dict(r) for r in rows]


def get_node(conn: psycopg.Connection, node_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, owner_id, name, device_type, gpu, provision_source, "
        "trust_domain, compute_tier_max, is_gate_runner, created_at "
        "FROM node WHERE id = %s",
        (str(node_id),),
    ).fetchone()
    return dict(row) if row else None


def create_node(
    conn: psycopg.Connection,
    *,
    name: str,
    device_type: str,
    trust_domain: str,
    compute_tier_max: str,
    is_gate_runner: bool,
    gpu: str | None,
    provision_source: str | None,
) -> dict[str, Any]:
    # Core가 부여. 요청 본문은 관리자 API이지 Node 런타임의 자기주장이 아니다.
    source = provision_source
    if source is None:
        source = "public" if trust_domain == "public" else "team"
    if is_gate_runner and source != "team":
        raise ValueError("gate-runner must be provision_source=team")
    try:
        row = conn.execute(
            """
            INSERT INTO node (
                owner_id, name, device_type, gpu, provision_source,
                trust_domain, compute_tier_max, is_gate_runner
            )
            SELECT %(owner_id)s, %(name)s, %(device_type)s, %(gpu)s, %(provision_source)s,
                   %(trust_domain)s, %(compute_tier_max)s, %(is_gate_runner)s
              FROM app_user u
             WHERE u.id = %(owner_id)s
            RETURNING id, owner_id, name, device_type, gpu, provision_source,
                      trust_domain, compute_tier_max, is_gate_runner, created_at
            """,
            {
                "owner_id": SEED_ADMIN_ID,
                "name": name,
                "device_type": device_type,
                "gpu": gpu,
                "provision_source": source,
                "trust_domain": trust_domain,
                "compute_tier_max": compute_tier_max,
                "is_gate_runner": is_gate_runner,
            },
        ).fetchone()
    except (pg_errors.CheckViolation, pg_errors.ForeignKeyViolation) as exc:
        raise ValueError(f"node insert rejected by DB: {exc.diag.constraint_name}") from exc
    if row is None:
        raise RuntimeError("seed admin missing")
    return dict(row)


def bind_agent_node(
    conn: psycopg.Connection,
    *,
    agent_id: uuid.UUID,
    node_id: uuid.UUID,
    weights_sha256_seen: str,
) -> dict[str, Any]:
    assert_sha256(weights_sha256_seen)
    try:
        bound = conn.execute(
            """
            INSERT INTO agent_node (agent_id, node_id, bind_status, weights_sha256_seen)
            SELECT a.id, n.id, 'BOUND', %(seen)s
              FROM agent a
              JOIN node n ON n.id = %(node_id)s
             WHERE a.id = %(agent_id)s
            ON CONFLICT (agent_id, node_id) DO UPDATE
               SET bind_status = 'BOUND',
                   weights_sha256_seen = EXCLUDED.weights_sha256_seen
            RETURNING agent_id, node_id, bind_status, weights_sha256_seen
            """,
            {
                "agent_id": str(agent_id),
                "node_id": str(node_id),
                "seen": weights_sha256_seen,
            },
        ).fetchone()
    except (pg_errors.ForeignKeyViolation, pg_errors.UniqueViolation, pg_errors.CheckViolation) as exc:
        name = exc.diag.constraint_name if exc.diag else None
        raise ValueError(f"bind rejected: {name or exc}") from exc
    if bound is None:
        raise ValueError("agent or node not found")

    ready = conn.execute(
        """
        INSERT INTO agent_node_ready (agent_id, node_id, bind_status, weights_sha256)
        SELECT an.agent_id, an.node_id, an.bind_status, an.weights_sha256_seen
          FROM agent_node an
          JOIN agent a ON a.id = an.agent_id AND a.weights_sha256 = an.weights_sha256_seen
         WHERE an.agent_id = %(agent_id)s
           AND an.node_id = %(node_id)s
           AND an.bind_status = 'BOUND'
        ON CONFLICT (agent_id, node_id) DO NOTHING
        RETURNING agent_id, node_id, bind_status, weights_sha256
        """,
        {"agent_id": str(agent_id), "node_id": str(node_id)},
    ).fetchone()

    out = dict(bound)
    out["ready"] = ready is not None or _is_ready(conn, agent_id, node_id)
    return out


def _is_ready(conn: psycopg.Connection, agent_id: uuid.UUID, node_id: uuid.UUID) -> bool:
    row = conn.execute(
        "SELECT 1 FROM agent_node_ready WHERE agent_id = %s AND node_id = %s",
        (str(agent_id), str(node_id)),
    ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Node 생존·가용 상태 (node_session / node_liveness)
#
# 스키마에는 처음부터 있었으나 코드가 쓰지 않고 있었다.
# 배정이 UUID 순서로만 골라서, 죽은 기기나 이미 바쁜 기기에도 일이 갔다.
# ---------------------------------------------------------------------------

UPSERT_SESSION_SQL = """
WITH live AS (
    SELECT id FROM node_session
     WHERE node_id = %(node_id)s AND closed_at IS NULL
     ORDER BY last_heartbeat DESC
     LIMIT 1
), updated AS (
    UPDATE node_session s
       SET last_heartbeat = now(), availability = %(availability)s, metrics = %(metrics)s::jsonb
      FROM live
     WHERE s.id = live.id
    RETURNING s.id
), inserted AS (
    INSERT INTO node_session (node_id, availability, metrics)
    SELECT %(node_id)s, %(availability)s, %(metrics)s::jsonb
     WHERE NOT EXISTS (SELECT 1 FROM live)
    RETURNING id
)
SELECT id FROM updated UNION ALL SELECT id FROM inserted
"""


def heartbeat(
    conn: psycopg.Connection,
    *,
    node_id: uuid.UUID,
    availability: str,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Node가 살아 있음을 알린다. 세션이 없으면 열고, 있으면 갱신한다."""
    if availability not in ("AVAILABLE", "BUSY", "DRAINING", "OFFLINE"):
        raise ValueError(f"bad availability: {availability}")
    row = conn.execute(
        UPSERT_SESSION_SQL,
        {
            "node_id": str(node_id),
            "availability": availability,
            "metrics": json.dumps(metrics or {}),
        },
    ).fetchone()
    return {"session_id": str(row["id"]), "availability": availability}


def liveness(conn: psycopg.Connection) -> list[dict[str, Any]]:
    """node_liveness 뷰 + 진행 중 배정 수."""
    rows = conn.execute(
        """
        SELECT l.node_id, n.name, l.availability, l.last_heartbeat, l.is_fresh,
               (SELECT count(*) FROM assignment a
                 WHERE a.node_id = l.node_id AND a.status = 'LEASED'
                   AND a.lease_expires_at > now()) AS active
          FROM node_liveness l JOIN node n ON n.id = l.node_id
         ORDER BY n.name
        """
    ).fetchall()
    return [dict(r) for r in rows]
