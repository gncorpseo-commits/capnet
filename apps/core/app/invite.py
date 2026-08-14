"""초대장 발행·소진·폐기 (G2 · 0016).

## 무엇을 하는가

관리 키가 **없는 사람**이 자기 기기를 함대에 넣을 수 있게 한다. 지금까지는 관리자가
`POST /v1/nodes` 를 직접 불러야 했다 — 「러닝크루가 자기 기기를 내놓는다」가 수작업이었다.

## 절대규칙 4 를 어떻게 지키나

**신청자는 등급을 고르지 않는다.** 관리자가 초대를 발행할 때 `trust_domain` 과
`compute_tier_max` 를 박아 넣고, 소진 요청은 이름·기기 종류만 준다. 등급은 언제나
초대장 행에서 읽는다 — 소진 요청 본문에 `trust_domain` 이 있어도 **쓰지 않는다.**

`team` 은 초대로 만들 수 없다 (`ck_invite_domain`). 그래서 초대로 들어온 기기는
`ck_gate_runner_team` 에 의해 **채점자가 될 수 없다** — 절대규칙 8 이 그대로 선다.

## 이 모듈의 위험한 점

소진 경로는 **관리 키 없이** 열려야 한다 (초대받은 사람에게는 키가 없다).
지금까지 쓰기는 전부 키 뒤에 있었으므로, 이것이 유일한 예외다. 그래서 완화를 겹친다:

- **만료** — 발행 시 반드시 박힌다 (`expires_at NOT NULL`, 기본 7일)
- **1회용** — `max_redemptions` 기본 1. 상한은 **DB CHECK** 가 막는다
- **폐기** — `revoked_at`
- **증적** — `audit_log` 에 `invite.redeemed` · `node_invite_redemption` 행

## 시크릿

`ci_<8자 hex>.<43자 base64url>`. 증서(`cn_`)와 같은 모양이고 평문은 발행 응답에서
**한 번만** 나간다. DB 에는 sha256 만 남는다.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from typing import Any

import psycopg

PREFIX_BYTES = 4
SECRET_BYTES = 32
SCHEME = "CapNet-Invite"
DEFAULT_TTL_DAYS = 7  # 사람이 들고 다닌다 — 증서보다 길다
DEFAULT_TIER = "M"


class InviteError(Exception):
    """초대 검증 실패. 호출자가 401/409 로 옮긴다."""


def _hash(secret: str) -> bytes:
    return hashlib.sha256(secret.encode("utf-8")).digest()


def new_token() -> tuple[str, str, str]:
    prefix = "ci_" + secrets.token_hex(PREFIX_BYTES)
    secret = secrets.token_urlsafe(SECRET_BYTES)
    return prefix, secret, f"{prefix}.{secret}"


def split_token(token: str) -> tuple[str, str]:
    """`ci_xxxxxxxx.secret` 을 쪼갠다. 형식이 틀리면 InviteError."""
    token = (token or "").strip()
    if token.lower().startswith(SCHEME.lower() + " "):
        token = token[len(SCHEME) + 1 :].strip()
    prefix, sep, secret = token.partition(".")
    if not sep or not secret or not prefix.startswith("ci_"):
        raise InviteError("토큰 형식이 아니다 (ci_xxxxxxxx.secret)")
    return prefix, secret


def looks_like_invite(authorization: str | None) -> bool:
    """초대 토큰처럼 생겼나. 다른 인증 방식과 섞이지 않게 호출자가 먼저 본다."""
    if not authorization:
        return False
    value = authorization.strip()
    if value.lower().startswith(SCHEME.lower() + " "):
        value = value[len(SCHEME) + 1 :].strip()
    return value.startswith("ci_")


ISSUE_SQL = """
INSERT INTO node_invite (
    issued_by, key_prefix, secret_hash, trust_domain, compute_tier_max,
    label, expires_at, max_redemptions, org_id)
SELECT u.id, %(prefix)s, %(hash)s, %(trust_domain)s, %(tier)s,
       %(label)s, coalesce(%(expires_at)s::timestamptz, now() + make_interval(days => %(ttl)s)),
       %(max_redemptions)s, %(org_id)s
  FROM app_user u
 WHERE u.id = %(issued_by)s
RETURNING id, key_prefix, trust_domain, compute_tier_max, label,
          expires_at, max_redemptions, redeemed_count, org_id, created_at
"""

VERIFY_SQL = """
SELECT i.id, i.secret_hash, i.trust_domain, i.compute_tier_max, i.issued_by, i.org_id,
       i.revoked_at, i.expires_at, i.max_redemptions, i.redeemed_count,
       s.state, s.usable
  FROM node_invite i
  JOIN node_invite_status s ON s.id = i.id
 WHERE i.key_prefix = %(prefix)s
"""

# 소진은 **조건부 UPDATE** 다. 앱이 세고 DB 가 막는다 —
# 두 요청이 같은 초대장을 동시에 써도 한쪽만 통과한다 (WHERE 절이 판정한다).
CLAIM_SQL = """
UPDATE node_invite
   SET redeemed_count = redeemed_count + 1
 WHERE id = %(id)s
   AND revoked_at IS NULL
   AND expires_at > now()
   AND redeemed_count < max_redemptions
RETURNING id, trust_domain, compute_tier_max, redeemed_count, max_redemptions
"""

LINK_SQL = """
INSERT INTO node_invite_redemption (invite_id, node_id)
VALUES (%(invite_id)s, %(node_id)s)
"""

AUDIT_SQL = """
INSERT INTO audit_log (actor_type, event, payload)
VALUES ('user', %(event)s, %(payload)s::jsonb)
"""

REVOKE_SQL = """
UPDATE node_invite
   SET revoked_at = now(), revoked_reason = %(reason)s
 WHERE id = %(invite_id)s AND revoked_at IS NULL
RETURNING id, key_prefix, revoked_at, revoked_reason
"""

LIST_SQL = "SELECT * FROM node_invite_status ORDER BY created_at DESC"


def issue_invite(
    conn: psycopg.Connection,
    *,
    issued_by: uuid.UUID,
    trust_domain: str,
    # 초대로 들어온 기기가 속할 조직 (D24). None = 팀 운영 공용 기기.
    org_id: uuid.UUID | str | None = None,
    compute_tier_max: str = DEFAULT_TIER,
    label: str | None = None,
    expires_at: Any | None = None,
    ttl_days: int = DEFAULT_TTL_DAYS,
    max_redemptions: int = 1,
) -> dict[str, Any]:
    """초대장을 발행한다. 반환값의 `secret` 은 **이때 한 번만** 존재한다.

    `trust_domain` 과 `org_id` 는 여기서 정해져 행에 박힌다 — 소진하는 쪽이 바꾸지 못한다.
    """
    prefix, secret, token = new_token()
    try:
        row = conn.execute(
            ISSUE_SQL,
            {
                "issued_by": str(issued_by),
                "prefix": prefix,
                "hash": _hash(secret),
                "trust_domain": trust_domain,
                "org_id": str(org_id) if org_id else None,
                "tier": compute_tier_max,
                "label": label,
                "expires_at": expires_at,
                "ttl": ttl_days,
                "max_redemptions": max_redemptions,
            },
        ).fetchone()
    except psycopg.errors.CheckViolation as exc:
        # `team` 초대는 여기서 걸린다 — 발행은 됐는데 소진이 안 되는 초대장을 만들지 않는다.
        raise InviteError(
            f"초대 거절 — {exc.diag.constraint_name} (team 등급은 초대로 만들 수 없다)"
        ) from exc
    except psycopg.errors.ForeignKeyViolation as exc:
        raise InviteError(f"알 수 없는 등급·티어 — {exc.diag.constraint_name}") from exc
    if row is None:
        raise InviteError("발행자가 없다")

    out = dict(row)
    out["secret"] = token  # 저장하지 않는다. 응답에만 실린다.
    return out


def verify_invite(conn: psycopg.Connection, token: str) -> dict[str, Any]:
    """초대 토큰을 검증하고 **초대장 행을 돌려준다** (등급은 이 행에서만 읽는다).

    「없는 초대」와 「틀린 시크릿」을 같은 문구로 답한다 — prefix 로 존재를 캐지 못하게.
    """
    prefix, secret = split_token(token)
    row = conn.execute(VERIFY_SQL, {"prefix": prefix}).fetchone()
    if row is None or not hmac.compare_digest(bytes(row["secret_hash"]), _hash(secret)):
        raise InviteError("초대가 유효하지 않다")
    if not row["usable"]:
        # 여기서는 상태를 말해 준다 — 이미 시크릿을 맞춘 사람이다.
        raise InviteError(f"초대를 쓸 수 없다 ({row['state']})")
    return dict(row)


def redeem_invite(
    conn: psycopg.Connection,
    *,
    invite: dict[str, Any],
    node_id: uuid.UUID,
    node_name: str,
) -> dict[str, Any]:
    """초대장을 소진하고 만들어진 Node 에 묶는다.

    호출자가 이미 `verify_invite` 로 검증했더라도 **여기서 다시 판정한다** —
    검증과 소진 사이에 폐기·만료·소진이 끼어들 수 있다. 판정은 `CLAIM_SQL` 의
    WHERE 절, 즉 DB 가 한다.
    """
    row = conn.execute(CLAIM_SQL, {"id": str(invite["id"])}).fetchone()
    if row is None:
        raise InviteError("초대를 쓸 수 없다 (그 사이 폐기·만료·소진됐다)")
    conn.execute(LINK_SQL, {"invite_id": str(invite["id"]), "node_id": str(node_id)})
    conn.execute(
        AUDIT_SQL,
        {
            "event": "invite.redeemed",
            "payload": json.dumps(
                {
                    "invite_id": str(invite["id"]),
                    "node_id": str(node_id),
                    "node_name": node_name,
                    "trust_domain": row["trust_domain"],
                    "compute_tier_max": row["compute_tier_max"],
                    "org_id": str(invite.get("org_id")) if invite.get("org_id") else None,
                    "redeemed_count": row["redeemed_count"],
                    "max_redemptions": row["max_redemptions"],
                }
            ),
        },
    )
    return dict(row)


def revoke_invite(
    conn: psycopg.Connection, *, invite_id: uuid.UUID, reason: str
) -> dict[str, Any] | None:
    row = conn.execute(
        REVOKE_SQL, {"invite_id": str(invite_id), "reason": reason}
    ).fetchone()
    return dict(row) if row else None


def list_invites(conn: psycopg.Connection) -> list[dict[str, Any]]:
    """초대장 상태 목록. 시크릿도 해시도 나가지 않는다 — prefix 만."""
    return [dict(r) for r in conn.execute(LIST_SQL).fetchall()]
