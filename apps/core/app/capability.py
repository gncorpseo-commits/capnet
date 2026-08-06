"""Capability 등록·조회. 스키마 제약을 우회하지 않는다."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

import psycopg
from psycopg import errors as pg_errors

from app.const import SHA256_HEX

_OUTPUT_KINDS = frozenset({"closed_set_labels", "structured", "freeform"})
_TIERS = frozenset({"L", "M", "S"})
_DOMAINS = frozenset({"team", "tenant", "public"})


def assert_capability_sha256(value: str) -> None:
    if not re.fullmatch(SHA256_HEX, value):
        raise ValueError("golden_set_sha256 must be 64 lowercase hex chars")


def list_capabilities(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, code, version, name, description, output_kind, compute_tier, "
        "trust_domain_min, mvp_eligible, golden_set_ref, golden_set_sha256, "
        "golden_set_size, created_at "
        "FROM capability ORDER BY code, version"
    ).fetchall()
    return [dict(r) for r in rows]


def get_capability(conn: psycopg.Connection, capability_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, code, version, name, description, input_schema, output_schema, "
        "output_kind, compute_tier, trust_domain_min, mvp_eligible, "
        "golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics, created_at "
        "FROM capability WHERE id = %s",
        (str(capability_id),),
    ).fetchone()
    return dict(row) if row else None


def create_capability(
    conn: psycopg.Connection,
    *,
    code: str,
    version: int,
    name: str,
    description: str | None,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any],
    output_kind: str,
    compute_tier: str,
    trust_domain_min: str,
    mvp_eligible: bool,
    golden_set_ref: str,
    golden_set_sha256: str,
    golden_set_size: int,
    golden_metrics: dict[str, Any],
) -> dict[str, Any]:
    if not code.strip():
        raise ValueError("code required")
    if version < 1:
        raise ValueError("version must be >= 1")
    if output_kind not in _OUTPUT_KINDS:
        raise ValueError(f"output_kind must be one of {sorted(_OUTPUT_KINDS)}")
    if compute_tier not in _TIERS:
        raise ValueError("compute_tier must be L, M, or S")
    if trust_domain_min not in _DOMAINS:
        raise ValueError("trust_domain_min must be team, tenant, or public")
    if golden_set_size < 1:
        raise ValueError("golden_set_size must be > 0")
    assert_capability_sha256(golden_set_sha256)
    # ck_capability_mvp_scoreable: mvp면 closed_set_labels만
    if mvp_eligible and output_kind != "closed_set_labels":
        raise ValueError("mvp_eligible requires output_kind=closed_set_labels")

    try:
        row = conn.execute(
            """
            INSERT INTO capability (
                code, version, name, description,
                input_schema, output_schema, output_kind,
                compute_tier, trust_domain_min, mvp_eligible,
                golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics
            )
            VALUES (
                %(code)s, %(version)s, %(name)s, %(description)s,
                %(input_schema)s::jsonb, %(output_schema)s::jsonb, %(output_kind)s,
                %(compute_tier)s, %(trust_domain_min)s, %(mvp_eligible)s,
                %(golden_set_ref)s, %(golden_set_sha256)s, %(golden_set_size)s,
                %(golden_metrics)s::jsonb
            )
            RETURNING id, code, version, name, description, input_schema, output_schema,
                      output_kind, compute_tier, trust_domain_min, mvp_eligible,
                      golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics,
                      created_at
            """,
            {
                "code": code.strip(),
                "version": version,
                "name": name,
                "description": description,
                "input_schema": json.dumps(input_schema),
                "output_schema": json.dumps(output_schema),
                "output_kind": output_kind,
                "compute_tier": compute_tier,
                "trust_domain_min": trust_domain_min,
                "mvp_eligible": mvp_eligible,
                "golden_set_ref": golden_set_ref,
                "golden_set_sha256": golden_set_sha256,
                "golden_set_size": golden_set_size,
                "golden_metrics": json.dumps(golden_metrics),
            },
        ).fetchone()
    except pg_errors.UniqueViolation as exc:
        raise ValueError("capability (code, version) already exists") from exc
    except pg_errors.CheckViolation as exc:
        raise ValueError(f"capability check rejected: {exc}") from exc
    except pg_errors.ForeignKeyViolation as exc:
        raise ValueError(f"capability FK rejected: {exc}") from exc
    return dict(row)
