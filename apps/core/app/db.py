"""DB 커넥션 — 풀링 (SD-017).

## 왜 풀인가

`get_conn()` 이 매 호출마다 `psycopg.connect()` 를 했다. 실측(2026-08-11):

| 구간 | p50 |
|------|-----|
| 커넥션 수립 | **10.8ms** |
| `claim_next` (실제 일) | **0.7ms** |
| DB 여는 API 요청 | 14~15ms |
| DB 없는 API 요청 | 3.3ms |

**실제 일보다 커넥션이 15배 비쌌다.** API 요청 1건, 워커 루프 1회가 각각 새로 열었다.
부하 실측에서 처리량이 5.4건/초에 평평하고 지연만 늘었다 — 포화.

## 무엇을 지켰나

- **호출부 시그니처가 그대로다.** `with get_conn() as conn:` 는 그대로 동작한다.
  커밋/롤백 규약도 같다 — 성공하면 커밋, 예외면 롤백
- **풀이 없어도 돈다.** `psycopg_pool` 이 없거나 열지 못하면 예전 방식(직접 연결)으로 떨어진다.
  마이그레이션 CLI 처럼 한 번 쓰고 끝나는 경로는 풀이 필요 없다
- 크기는 환경으로 (`DB_POOL_MIN` · `DB_POOL_MAX`). 기본은 작게 — Core 는 워커 1개 + API 몇 개다

## 주의

풀은 **프로세스 안에서만** 공유된다. uvicorn 워커를 여러 개 띄우면 프로세스마다 풀이 생긴다.
`DB_POOL_MAX × 프로세스 수` 가 postgres 의 `max_connections` 를 넘지 않게 한다.
"""

from __future__ import annotations

import atexit
import logging
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import settings

logger = logging.getLogger(__name__)

POOL_MIN = int(os.environ.get("DB_POOL_MIN", "1"))
POOL_MAX = int(os.environ.get("DB_POOL_MAX", "8"))
POOL_TIMEOUT_S = float(os.environ.get("DB_POOL_TIMEOUT_S", "10"))
POOL_ENABLED = os.environ.get("DB_POOL", "1") != "0"

_pool = None
_pool_lock = threading.Lock()
_pool_failed = False


def _get_pool():
    """풀을 게으르게 연다. 못 열면 None 을 돌려주고 다시 시도하지 않는다."""
    global _pool, _pool_failed
    if not POOL_ENABLED or _pool_failed:
        return None
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is not None:
            return _pool
        try:
            from psycopg_pool import ConnectionPool

            pool = ConnectionPool(
                conninfo=settings.database_url,
                min_size=POOL_MIN,
                max_size=POOL_MAX,
                timeout=POOL_TIMEOUT_S,
                kwargs={"row_factory": dict_row, "autocommit": False},
                open=False,
                name="capnet-core",
            )
            pool.open(wait=True, timeout=POOL_TIMEOUT_S)
            atexit.register(_close_pool)
            _pool = pool
            logger.info("db pool opened (min=%d max=%d)", POOL_MIN, POOL_MAX)
        except Exception:
            # 풀을 못 열어도 서비스는 돈다 — 예전 방식으로 떨어진다.
            _pool_failed = True
            logger.warning("db pool unavailable; falling back to direct connect", exc_info=True)
            return None
    return _pool


def _close_pool() -> None:
    global _pool
    if _pool is not None:
        try:
            _pool.close()
        finally:
            _pool = None


@contextmanager
def _direct() -> Iterator[psycopg.Connection]:
    """풀 없이 직접 연결 — 예전 방식. 폴백이자 일회성 도구용."""
    conn = psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    """커밋/롤백 규약은 예전과 같다 — 성공하면 커밋, 예외면 롤백.

    풀에서 빌려 쓰고 돌려준다. 풀이 없으면 직접 연결한다.
    """
    pool = _get_pool()
    if pool is None:
        with _direct() as conn:
            yield conn
        return

    # psycopg_pool 의 connection() 도 성공 시 commit · 예외 시 rollback 한다.
    # 규약이 같아서 호출부를 바꾸지 않아도 된다.
    with pool.connection() as conn:
        yield conn


def pool_stats() -> dict[str, object]:
    """운영 조회용. 풀이 없으면 그 사실을 알린다."""
    pool = _get_pool()
    if pool is None:
        return {"enabled": False, "reason": "disabled" if not POOL_ENABLED else "unavailable"}
    s = pool.get_stats()
    return {
        "enabled": True,
        "min": POOL_MIN,
        "max": POOL_MAX,
        "size": s.get("pool_size"),
        "available": s.get("pool_available"),
        "waiting": s.get("requests_waiting"),
        "requests": s.get("requests_num"),
    }
