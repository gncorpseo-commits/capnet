"""Core 중개 입력 수집 (D22 · D8′). 바이트는 볼륨에, 메타는 DB 에.

## 원칙

**증적 = 해시·누가·어디로 · 바이트 = 휘발성 작업 저장소.**
바이트를 지워도 `task_input` 행은 남는다 — 그래야 나중에도 「어디로 갔는지」에 답한다.

## 왜 바이트를 DB 에 넣지 않나

「백업에서 입력 바이트는 빼고 증적 DB 는 넣는다」와 충돌한다. 볼륨을 분리해 두면
백업 정책도 분리된다 (`capnet_inputs` vs `capnet_pg`).

## 크기는 누가 재나

**DB 가 거절한다** — `task_input` 의 `capability_max_input_bytes` 스냅샷 + 복합 FK +
`CHECK (byte_size <= capability_max_input_bytes)` (0011). 여기서는 **읽는 도중에** 상한을
넘기면 끊는다. 다 받아 놓고 DB 에 물어보면 256MiB 를 메모리·디스크에 이미 올린 뒤다.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from typing import Any

import psycopg
from psycopg import errors as pg_errors

# 바이트가 사는 곳. compose 가 별도 볼륨을 여기에 붙인다.
INPUTS_DIR = Path(os.environ.get("CAPNET_INPUTS_DIR", "/inputs"))

# 스트리밍 청크. 작으면 syscall 이 늘고, 크면 상한 초과를 늦게 안다.
CHUNK = 1024 * 1024


class InputTooLarge(Exception):
    """계약 상한 초과. 호출자가 413 으로 옮긴다."""


class InputRejected(Exception):
    """계약 위반(MIME 등). 호출자가 400 으로 옮긴다."""


def blob_path(input_id: uuid.UUID | str) -> Path:
    """`<INPUTS_DIR>/<앞 2자>/<id>` — 한 디렉터리에 수만 개가 쌓이지 않게 한다."""
    s = str(input_id)
    return INPUTS_DIR / s[:2] / s


CAP_SQL = """
SELECT id, code, version, max_input_bytes, input_schema, quality_profile
  FROM capability
 WHERE code = %(code)s AND version = %(version)s
"""

INSERT_SQL = """
INSERT INTO task_input (
    id, capability_id, sha256, byte_size, media_type, uploaded_by,
    capability_max_input_bytes
)
SELECT %(id)s, c.id, %(sha256)s, %(byte_size)s, %(media_type)s, %(uploaded_by)s,
       c.max_input_bytes
  FROM capability c
 WHERE c.id = %(capability_id)s
RETURNING id, capability_id, sha256, byte_size, media_type, uploaded_by,
          capability_max_input_bytes, storage_state, created_at
"""


def allowed_media_types(input_schema: Any) -> list[str] | None:
    """계약이 선언한 MIME 목록. 없으면 None (검사하지 않는다).

    `input_schema.mediaTypes` 를 본다. 계약에 없는 것을 코드가 임의로 정하지 않는다 —
    「문서에만 있는 정책」을 만들지 않기 위해서다.
    """
    if not isinstance(input_schema, dict):
        return None
    kinds = input_schema.get("mediaTypes")
    if isinstance(kinds, list) and kinds:
        return [str(k) for k in kinds]
    return None


def assert_media_type(media_type: str, input_schema: Any) -> None:
    allowed = allowed_media_types(input_schema)
    if allowed is None:
        return
    if media_type not in allowed:
        raise InputRejected(
            f"media_type {media_type!r} 은 이 계약이 받지 않는다 (허용: {', '.join(allowed)})"
        )


def load_capability(
    conn: psycopg.Connection, *, code: str, version: int
) -> dict[str, Any] | None:
    row = conn.execute(CAP_SQL, {"code": code, "version": version}).fetchone()
    return dict(row) if row else None


def store_stream(chunks: Any, *, input_id: uuid.UUID, max_bytes: int) -> tuple[str, int]:
    """스트림을 파일로 받으면서 sha256·크기를 잰다. 상한을 넘기면 끊고 지운다.

    `max_bytes` 는 계약값이다. 여기서 통과해도 **DB 가 다시 판정한다** — 이 검사는
    「다 받아 놓고 거절」을 피하기 위한 것이고, 계약의 정본은 DB 제약이다.
    """
    path = blob_path(input_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    try:
        with open(path, "wb") as fh:
            for chunk in chunks:
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    raise InputTooLarge(
                        f"입력이 계약 상한을 넘었다 ({total} > {max_bytes} bytes)"
                    )
                digest.update(chunk)
                fh.write(chunk)
    except BaseException:
        purge_blob(input_id)
        raise
    if total == 0:
        purge_blob(input_id)
        raise InputRejected("빈 입력은 받지 않는다")
    return digest.hexdigest(), total


def record(
    conn: psycopg.Connection,
    *,
    input_id: uuid.UUID,
    capability_id: uuid.UUID,
    sha256: str,
    byte_size: int,
    media_type: str,
    uploaded_by: uuid.UUID | str,
) -> dict[str, Any]:
    """메타를 기록한다. 크기 계약은 DB 가 판정한다 (0011)."""
    try:
        row = conn.execute(
            INSERT_SQL,
            {
                "id": str(input_id),
                "capability_id": str(capability_id),
                "sha256": sha256,
                "byte_size": byte_size,
                "media_type": media_type,
                "uploaded_by": str(uploaded_by),
            },
        ).fetchone()
    except (pg_errors.CheckViolation, pg_errors.ForeignKeyViolation) as exc:
        name = getattr(exc.diag, "constraint_name", "") or ""
        if "within_contract" in name:
            raise InputTooLarge(f"DB 가 거절했다: {name}") from exc
        raise InputRejected(f"DB 가 거절했다: {name or exc}") from exc
    return dict(row)


def purge_blob(input_id: uuid.UUID | str) -> bool:
    """바이트만 지운다. 행은 남긴다 (증적)."""
    path = blob_path(input_id)
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


MARK_PURGED_SQL = """
UPDATE task_input
   SET storage_state = 'PURGED',
       bytes_purged_at = now()
 WHERE id = %(id)s
   AND storage_state = 'STORED'
RETURNING id, sha256, byte_size, bytes_purged_at
"""

DUE_SQL = """
SELECT task_input_id, reason, due_at, byte_size
  FROM task_input_purge_due
 WHERE due_at <= now()
 ORDER BY due_at
 LIMIT %(limit)s
"""

# 미완료 task 최대 수명 72h (Decision). 종결시켜야 바이트 TTL 이 시작된다.
# 절대규칙 2: task 는 스냅샷 테이블이 아니므로 UPDATE 로 종결한다.
TIMEOUT_STALE_SQL = """
UPDATE task
   SET status = 'TIMEOUT',
       finished_at = now(),
       updated_at = now()
 WHERE status IN ('CREATED', 'QUEUED')
   AND created_at + INTERVAL '72 hours' <= now()
RETURNING id
"""

GET_SQL = """
SELECT id, capability_id, sha256, byte_size, media_type, uploaded_by,
       storage_state, bytes_purged_at, created_at
  FROM task_input
 WHERE id = %(id)s
"""


def get(conn: psycopg.Connection, input_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(GET_SQL, {"id": str(input_id)}).fetchone()
    return dict(row) if row else None


def mark_purged(conn: psycopg.Connection, input_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(MARK_PURGED_SQL, {"id": str(input_id)}).fetchone()
    return dict(row) if row else None


def timeout_stale_tasks(conn: psycopg.Connection) -> int:
    """72h 넘게 미완료인 task 를 TIMEOUT 으로 종결한다."""
    return len(conn.execute(TIMEOUT_STALE_SQL).fetchall())


def purge_due(conn: psycopg.Connection, *, limit: int = 50) -> list[dict[str, Any]]:
    """삭제 예정 목록. 정책은 `task_input_purge_due` 뷰가 갖는다 (0011)."""
    return [dict(r) for r in conn.execute(DUE_SQL, {"limit": limit}).fetchall()]


NODE_MAY_READ_SQL = """
SELECT 1
  FROM assignment a
  JOIN task t ON t.id = a.task_id
 WHERE a.node_id = %(node_id)s
   AND t.input_id = %(input_id)s
   AND a.status = 'LEASED'
   AND a.lease_expires_at > now()
 LIMIT 1
"""


def node_may_read(
    conn: psycopg.Connection, *, node_id: uuid.UUID, input_id: uuid.UUID
) -> bool:
    """이 Node 가 이 입력을 받을 자격이 있는가.

    **살아 있는 lease 가 있어야 한다.** 증서만으로 아무 입력이나 내려주면, 등록된 기기
    전부가 남의 데이터를 읽을 수 있다 — 「승인 도메인 안으로만 간다」가 무너진다.
    """
    return (
        conn.execute(
            NODE_MAY_READ_SQL, {"node_id": str(node_id), "input_id": str(input_id)}
        ).fetchone()
        is not None
    )
