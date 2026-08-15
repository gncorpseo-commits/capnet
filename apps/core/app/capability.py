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
_PROFILES = frozenset({"golden", "none"})

# 「골든셋 없음」의 고정 표현 (0010 · D20). `golden_set_*` 의 NOT NULL 을 해제하지 않고
# 규약으로 표현한다 — 값은 `ck_capability_profile_sentinel` 이 강제한다.
#
# **호출자가 이 값을 손으로 넣지 않는다.** 넣게 두면 규약이 새고, 언젠가 진짜 골든셋 자리에
# 센티널이 들어간다. quality_profile='none' 이면 Core 가 채운다.
SENTINEL_GOLDEN = {
    "golden_set_ref": "(none)",
    "golden_set_sha256": "0" * 64,
    "golden_set_size": 1,
    "golden_metrics": {},
}


def assert_capability_sha256(value: str) -> None:
    if not re.fullmatch(SHA256_HEX, value):
        raise ValueError("golden_set_sha256 must be 64 lowercase hex chars")


def list_capabilities(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, code, version, name, description, output_kind, compute_tier, "
        "trust_domain_min, mvp_eligible, quality_profile, max_input_bytes, max_attempts, "
        "golden_set_ref, golden_set_sha256, "
        "golden_set_size, created_at "
        "FROM capability ORDER BY code, version"
    ).fetchall()
    return [dict(r) for r in rows]


def get_capability(conn: psycopg.Connection, capability_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, code, version, name, description, input_schema, output_schema, "
        "output_kind, compute_tier, trust_domain_min, mvp_eligible, quality_profile, "
        "max_input_bytes, max_attempts, "
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
    golden_set_ref: str | None = None,
    golden_set_sha256: str | None = None,
    golden_set_size: int | None = None,
    golden_metrics: dict[str, Any] | None = None,
    quality_profile: str = "golden",
    max_input_bytes: int | None = None,
    max_attempts: int | None = None,
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
    if quality_profile not in _PROFILES:
        raise ValueError(f"quality_profile must be one of {sorted(_PROFILES)}")
    # 입력 크기 계약 (0011 · D22). 값을 안 주면 DB 기본값(32MiB)이 들어간다.
    # 절대 상한은 DB CHECK 가 갖는다 — 여기서 다시 적으면 두 곳이 어긋난다.
    if max_input_bytes is not None and max_input_bytes < 1:
        raise ValueError("max_input_bytes must be > 0")
    # 배정 시도 상한 (0015). 절대 상한은 DB CHECK 가 갖는다 — 여기 다시 적으면 어긋난다.
    if max_attempts is not None and max_attempts < 1:
        raise ValueError("max_attempts must be > 0")

    if quality_profile == "none":
        # 골든셋 관련 값은 **받지 않는다.** 보내왔다면 호출자가 뭔가 오해한 것이다 —
        # 조용히 덮어쓰면 「골든셋을 줬는데 무시됐다」가 된다.
        given = [
            n for n, v in (
                ("golden_set_ref", golden_set_ref),
                ("golden_set_sha256", golden_set_sha256),
                ("golden_set_size", golden_set_size),
                ("golden_metrics", golden_metrics),
            ) if v is not None
        ]
        if given:
            raise ValueError(
                "quality_profile='none' takes no golden set fields "
                f"(got {', '.join(given)}) — Core fills the sentinel"
            )
        golden_set_ref = SENTINEL_GOLDEN["golden_set_ref"]
        golden_set_sha256 = SENTINEL_GOLDEN["golden_set_sha256"]
        golden_set_size = SENTINEL_GOLDEN["golden_set_size"]
        golden_metrics = SENTINEL_GOLDEN["golden_metrics"]
        # 채점이 없는 능력은 MVP 통계 대상이 아니다.
        if mvp_eligible:
            raise ValueError("quality_profile='none' cannot be mvp_eligible")
    else:
        # ck_capability_golden_scoreable (0018): 골든은 **채점 가능한 출력**에만.
        #
        # freeform 은 정답 집합을 정의할 수 없다 — 요약문이 「맞다/틀리다」로 갈리지 않으므로
        # 골든셋 정의서 §6 의 채점 규칙(결정적·부분점수 없음·퍼지 매칭 금지)이 성립하지 않는다.
        # 잴 수 없는 것에 점수를 붙이고 그 점수로 품질 보장을 파는 경로를 여기서 끊는다.
        #
        # DB 도 같은 것을 막지만 여기서 먼저 거절해 **어느 제약인지** 말해 준다.
        # structured 는 막지 않는다 — 채점기가 아직 없을 뿐 원리적으로는 잴 수 있다.
        if output_kind == "freeform":
            raise ValueError(
                "quality_profile='golden' requires a scoreable output_kind "
                "(freeform has no answer set) — ck_capability_golden_scoreable"
            )
        missing = [
            n for n, v in (
                ("golden_set_ref", golden_set_ref),
                ("golden_set_sha256", golden_set_sha256),
                ("golden_set_size", golden_set_size),
                ("golden_metrics", golden_metrics),
            ) if v is None
        ]
        if missing:
            raise ValueError(
                f"quality_profile='golden' requires {', '.join(missing)}"
            )
        if golden_set_ref == SENTINEL_GOLDEN["golden_set_ref"] or (
            golden_set_sha256 == SENTINEL_GOLDEN["golden_set_sha256"]
        ):
            raise ValueError(
                "sentinel golden set values are reserved for quality_profile='none'"
            )

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
                golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics,
                quality_profile, max_input_bytes, max_attempts
            )
            VALUES (
                %(code)s, %(version)s, %(name)s, %(description)s,
                %(input_schema)s::jsonb, %(output_schema)s::jsonb, %(output_kind)s,
                %(compute_tier)s, %(trust_domain_min)s, %(mvp_eligible)s,
                %(golden_set_ref)s, %(golden_set_sha256)s, %(golden_set_size)s,
                %(golden_metrics)s::jsonb, %(quality_profile)s,
                coalesce(%(max_input_bytes)s::bigint, 33554432),
                coalesce(%(max_attempts)s::int, 5)
            )
            RETURNING id, code, version, name, description, input_schema, output_schema,
                      output_kind, compute_tier, trust_domain_min, mvp_eligible,
                      golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics,
                      quality_profile, max_input_bytes, max_attempts, created_at
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
                "quality_profile": quality_profile,
                "max_input_bytes": max_input_bytes,
                "max_attempts": max_attempts,
            },
        ).fetchone()
    except pg_errors.UniqueViolation as exc:
        raise ValueError("capability (code, version) already exists") from exc
    except pg_errors.CheckViolation as exc:
        raise ValueError(f"capability check rejected: {exc}") from exc
    except pg_errors.ForeignKeyViolation as exc:
        raise ValueError(f"capability FK rejected: {exc}") from exc
    return dict(row)
