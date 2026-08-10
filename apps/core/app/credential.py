"""Node 증서 발급·검증·폐기 (P2-4 · SD-002).

## 무엇을 하는가

Node 프로세스가 「자기가 어떤 `node.id` 인지」를 증명하게 한다.
지금까지 Node 경로는 `node_id` 를 **URL 에서 그대로** 받았다 — 아무나 사칭할 수 있었고,
실질 방어는 「팀 내부망 전제」뿐이었다 (SD-010).

## 절대규칙 4

증서는 **「너는 이 node.id 다」만** 말한다. `trust_domain`·`compute_tier_max`·`is_gate_runner` 는
증서에도 없고 이 모듈의 어떤 함수도 받지 않는다. 등급은 언제나 `node` 행에서 읽는다 (C1·C2).

## 시크릿

`cn_<8자 hex>.<43자 base64url>` 형태. 앞쪽이 prefix(조회·로그용), 뒤쪽이 시크릿이다.
평문은 발급 응답에서 **한 번만** 나가고 저장하지 않는다 — DB 에는 sha256 만 남는다 (C3).
토큰 엔트로피가 256비트이므로 느린 KDF 대신 sha256 을 쓴다 (`api_key` 와 같은 방식).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from typing import Any

import psycopg

PREFIX_BYTES = 4  # → hex 8자
SECRET_BYTES = 32  # 256비트
SCHEME = "CapNet-Node"


class CredentialError(Exception):
    """증서 검증 실패. 호출자가 401/403 으로 옮긴다."""


def _hash(secret: str) -> bytes:
    return hashlib.sha256(secret.encode("utf-8")).digest()


def new_token() -> tuple[str, str, str]:
    """(prefix, secret, 합친 토큰) — 합친 것만 사용자에게 보여 준다."""
    prefix = "cn_" + secrets.token_hex(PREFIX_BYTES)
    secret = secrets.token_urlsafe(SECRET_BYTES)
    return prefix, secret, f"{prefix}.{secret}"


def split_token(token: str) -> tuple[str, str]:
    """`cn_xxxxxxxx.secret` 을 쪼갠다. 형식이 틀리면 CredentialError."""
    token = (token or "").strip()
    if token.lower().startswith(SCHEME.lower() + " "):
        token = token[len(SCHEME) + 1 :].strip()
    prefix, sep, secret = token.partition(".")
    if not sep or not secret or not prefix.startswith("cn_"):
        raise CredentialError("토큰 형식이 아니다 (cn_xxxxxxxx.secret)")
    return prefix, secret


ISSUE_SQL = """
INSERT INTO node_credential (node_id, issued_by, key_prefix, secret_hash, label, expires_at)
SELECT n.id, u.id, %(prefix)s, %(hash)s, %(label)s, %(expires_at)s
  FROM node n JOIN app_user u ON u.id = %(issued_by)s
 WHERE n.id = %(node_id)s
RETURNING id, node_id, key_prefix, issued_at, expires_at, label
"""

VERIFY_SQL = """
SELECT nc.id, nc.node_id, nc.secret_hash, nc.revoked_at,
       (nc.expires_at IS NOT NULL AND nc.expires_at <= now()) AS is_expired
  FROM node_credential nc
 WHERE nc.key_prefix = %(prefix)s
"""

TOUCH_SQL = "UPDATE node_credential SET last_used_at = now() WHERE id = %(id)s"

REVOKE_SQL = """
UPDATE node_credential
   SET revoked_at = now(), revoked_reason = %(reason)s
 WHERE node_id = %(node_id)s AND revoked_at IS NULL
RETURNING id, node_id, key_prefix, revoked_at, revoked_reason
"""


def issue_credential(
    conn: psycopg.Connection,
    *,
    node_id: uuid.UUID,
    issued_by: uuid.UUID,
    label: str | None = None,
    expires_at: Any | None = None,
) -> dict[str, Any]:
    """증서를 발급한다. 반환값의 `secret` 은 **이때 한 번만** 존재한다.

    등급 인자를 받지 않는다 — 절대규칙 4. Node 당 활성 증서는 하나이므로,
    회전은 `revoke_credential()` 후 다시 부른다.
    """
    prefix, secret, token = new_token()
    try:
        row = conn.execute(
            ISSUE_SQL,
            {
                "node_id": str(node_id),
                "issued_by": str(issued_by),
                "prefix": prefix,
                "hash": _hash(secret),
                "label": label,
                "expires_at": expires_at,
            },
        ).fetchone()
    except psycopg.errors.UniqueViolation as exc:
        raise CredentialError(
            "이 Node 에는 이미 활성 증서가 있다 — 회전은 폐기 후 재발급이다"
        ) from exc
    if row is None:
        raise CredentialError("node 또는 발급자가 없다")

    out = dict(row)
    out["secret"] = token  # 저장하지 않는다. 응답에만 실린다.
    return out


def verify_credential(conn: psycopg.Connection, token: str) -> uuid.UUID:
    """토큰을 검증하고 **node_id 를 해석해서** 돌려준다.

    호출자가 URL 에서 받은 node_id 를 믿지 않고 이 반환값과 대조해야 한다.
    실패 사유를 세분화하지 않는다 — prefix 존재 여부가 새어 나가지 않게 한다.
    """
    prefix, secret = split_token(token)
    row = conn.execute(VERIFY_SQL, {"prefix": prefix}).fetchone()
    if row is None:
        raise CredentialError("증서가 유효하지 않다")

    # 해시 비교는 상수 시간으로 한다.
    if not hmac.compare_digest(bytes(row["secret_hash"]), _hash(secret)):
        raise CredentialError("증서가 유효하지 않다")
    if row["revoked_at"] is not None:
        raise CredentialError("폐기된 증서다")
    # 만료 판정은 DB 시계로 한다 — 앱 시계와 어긋나면 증서 수명이 두 개가 된다.
    if row["is_expired"]:
        raise CredentialError("만료된 증서다")

    conn.execute(TOUCH_SQL, {"id": str(row["id"])})
    return row["node_id"]


def revoke_credential(
    conn: psycopg.Connection, *, node_id: uuid.UUID, reason: str
) -> dict[str, Any] | None:
    """활성 증서를 폐기한다. 행은 남긴다 — 언제 무엇을 왜 끊었는지가 증적이다."""
    if not reason or not reason.strip():
        raise ValueError("reason is required")
    row = conn.execute(
        REVOKE_SQL, {"node_id": str(node_id), "reason": reason.strip()}
    ).fetchone()
    return dict(row) if row else None


def list_credential_status(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT node_id, node_name, trust_domain, provision_source, credential_id, "
        "key_prefix, issued_at, expires_at, last_used_at, credential_valid "
        "FROM node_credential_status ORDER BY node_name"
    ).fetchall()
    return [dict(r) for r in rows]
