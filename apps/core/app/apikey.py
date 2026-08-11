"""관리 API 인증 — 사용자 API 키 (SD-010 나머지 절반).

## 무엇을 막는가

이 모듈 이전에는 관리 API 에 인증이 **없었다.** 실측으로 익명 요청이
`team` · `L등급` · **게이트러너** Node 를 등록하고 증서까지 받았다.

게이트러너가 되면 자기 Agent 를 자기가 채점해 통과시킬 수 있다 —
FK 사슬·증적·Node 증서가 전부 그 위에 쌓은 심층 방어인데 **정문이 열려 있었다.**

## 두 가지 신원이 공존한다

| 스킴 | 누구 | 어디에 |
|------|------|--------|
| `CapNet-Node <token>` | **기기** | Node 가 부르는 경로 (P2-4) |
| `CapNet-Key <token>` | **사람/도구** | 관리·등록·게이트 기록 경로 (여기) |

섞지 않는다. Node 증서로 Node 를 등록할 수 없고, API 키로 heartbeat 를 보낼 수 없다.

## 역할

`app_user.role` 이 `user < developer < admin` 이다 (스키마 v4.4 의 CHECK).
새 테이블을 만들지 않았다 — **스키마가 이미 예견해 뒀고 코드가 쓰지 않았을 뿐이다.**

## 시크릿

`ck_<8자 hex>.<43자 base64url>`. 평문은 발급 때 한 번만 나가고 DB 에는 sha256 만 남는다.
`node_credential` 과 같은 규약이다.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from typing import Any

import psycopg

PREFIX_BYTES = 4
SECRET_BYTES = 32
SCHEME = "CapNet-Key"

# 높을수록 강한 권한. 비교는 이 표로만 한다 — 문자열 정렬은 의미가 없다.
ROLE_RANK: dict[str, int] = {"user": 1, "developer": 2, "admin": 3}


class ApiKeyError(Exception):
    """키 검증 실패. 호출자가 401 로 옮긴다."""


class Forbidden(Exception):
    """키는 유효하나 역할이 모자란다. 호출자가 403 으로 옮긴다."""


def _hash(secret: str) -> bytes:
    return hashlib.sha256(secret.encode("utf-8")).digest()


def new_token() -> tuple[str, str, str]:
    prefix = "ck_" + secrets.token_hex(PREFIX_BYTES)
    secret = secrets.token_urlsafe(SECRET_BYTES)
    return prefix, secret, f"{prefix}.{secret}"


def split_token(token: str) -> tuple[str, str]:
    token = (token or "").strip()
    if token.lower().startswith(SCHEME.lower() + " "):
        token = token[len(SCHEME) + 1 :].strip()
    prefix, sep, secret = token.partition(".")
    if not sep or not secret or not prefix.startswith("ck_"):
        raise ApiKeyError("토큰 형식이 아니다 (ck_xxxxxxxx.secret)")
    return prefix, secret


def looks_like_api_key(authorization: str | None) -> bool:
    """이 Authorization 이 API 키 스킴인가. Node 증서와 구분하는 데 쓴다."""
    if not authorization:
        return False
    a = authorization.strip()
    return a.lower().startswith(SCHEME.lower() + " ") or a.startswith("ck_")


ISSUE_SQL = """
INSERT INTO api_key (user_id, key_prefix, key_hash, label)
SELECT u.id, %(prefix)s, %(hash)s, %(label)s
  FROM app_user u WHERE u.id = %(user_id)s
RETURNING id, user_id, key_prefix, label, created_at
"""

VERIFY_SQL = """
SELECT k.id, k.user_id, k.key_hash, k.revoked_at, u.role, u.name
  FROM api_key k JOIN app_user u ON u.id = k.user_id
 WHERE k.key_prefix = %(prefix)s
"""

TOUCH_SQL = "UPDATE api_key SET last_used_at = now() WHERE id = %(id)s"

REVOKE_SQL = """
UPDATE api_key SET revoked_at = now()
 WHERE key_prefix = %(prefix)s AND revoked_at IS NULL
RETURNING id, user_id, key_prefix, revoked_at
"""

ENSURE_USER_SQL = """
INSERT INTO app_user (name, role) VALUES (%(name)s, %(role)s)
RETURNING id, name, role
"""


def ensure_user(conn: psycopg.Connection, *, name: str, role: str) -> dict[str, Any]:
    if role not in ROLE_RANK:
        raise ValueError(f"unknown role {role!r}; known={sorted(ROLE_RANK)}")
    row = conn.execute(ENSURE_USER_SQL, {"name": name, "role": role}).fetchone()
    return dict(row)


def issue_key(
    conn: psycopg.Connection, *, user_id: uuid.UUID, label: str | None = None
) -> dict[str, Any]:
    """키를 발급한다. 반환값의 `secret` 은 **이때 한 번만** 존재한다."""
    prefix, secret, token = new_token()
    row = conn.execute(
        ISSUE_SQL,
        {"user_id": str(user_id), "prefix": prefix, "hash": _hash(secret), "label": label},
    ).fetchone()
    if row is None:
        raise ApiKeyError("app_user 가 없다")
    out = dict(row)
    out["secret"] = token
    return out


def verify_key(conn: psycopg.Connection, token: str) -> dict[str, Any]:
    """키를 검증하고 `{user_id, role, name}` 을 돌려준다.

    실패 사유를 세분화하지 않는다 — prefix 존재 여부가 새어 나가지 않게 한다.
    """
    prefix, secret = split_token(token)
    row = conn.execute(VERIFY_SQL, {"prefix": prefix}).fetchone()
    if row is None:
        raise ApiKeyError("키가 유효하지 않다")
    if not hmac.compare_digest(bytes(row["key_hash"]), _hash(secret)):
        raise ApiKeyError("키가 유효하지 않다")
    if row["revoked_at"] is not None:
        raise ApiKeyError("폐기된 키다")
    conn.execute(TOUCH_SQL, {"id": str(row["id"])})
    return {"user_id": row["user_id"], "role": row["role"], "name": row["name"]}


def assert_role(actor: dict[str, Any], minimum: str) -> None:
    """역할이 모자라면 Forbidden. 문자열 비교가 아니라 순위표로 판정한다."""
    have = ROLE_RANK.get(str(actor.get("role")), 0)
    need = ROLE_RANK.get(minimum, 99)
    if have < need:
        raise Forbidden(f"'{minimum}' 이상이 필요하다 (현재 '{actor.get('role')}')")


def revoke_key(conn: psycopg.Connection, *, key_prefix: str) -> dict[str, Any] | None:
    row = conn.execute(REVOKE_SQL, {"prefix": key_prefix}).fetchone()
    return dict(row) if row else None


def list_key_status(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT api_key_id, user_id, user_name, role, key_prefix, label, "
        "created_at, last_used_at, active FROM api_key_status ORDER BY created_at"
    ).fetchall()
    return [dict(r) for r in rows]
