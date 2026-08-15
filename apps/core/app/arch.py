"""허용 아키텍처 등록 (D-arch).

## 무엇이 문제였나

`agent.arch` 는 `agent_arch` 를 FK 로 참조한다(`0008` · I1). 즉 **허용 목록이 DB 행**이고,
없는 arch 로는 Agent 등록이 막힌다 — 그건 설계대로다.

그런데 **그 행을 넣는 경로가 없었다.** 능력 카탈로그를 52 로 넓히면서 실측으로 드러났다:
비참조 arch 로 Agent 를 등록하려 하자 `unknown arch 'TinyTextCNN'` 400 이 났고,
운영자가 DB 에 직접 INSERT 하는 것 말고는 방법이 없었다. 그건 제품 경로가 아니다.

## 무엇을 하지 않는가

- **UPDATE·DELETE 를 만들지 않는다.** `max_params` 는 계약 게이트의 상한이다. 사후에 올리면
  **이미 통과한 증서의 근거가 바뀐다** — 증적이 「그때 무엇을 기준으로 통과했는가」를 답하지
  못하게 된다(D15). 상한을 바꿔야 하면 **새 arch 이름**으로 등록한다.
- **와일드카드·일괄 등록이 없다.** 관리자가 이름을 하나씩 명시한다. allowlist 가
  「사실상 전부 허용」이 되는 순간 `0008` 이 막으려던 것이 되살아난다.
- **덮어쓰지 않는다.** 이미 있는 이름이면 409 다. `ON CONFLICT DO NOTHING` 으로 조용히
  넘기면, 다른 `max_params` 로 다시 등록한 운영자가 **성공했다고 믿고 옛 값을 쓰게 된다.**
"""

from __future__ import annotations

import re
from typing import Any

import psycopg
from psycopg import errors as pg_errors

# arch 이름. 영문으로 시작하고 영숫자·`_`·`.`·`-` 만. 64자 이하.
# 좁게 잡는 이유: 이 값은 Node 의 `ARCH_REGISTRY` 조회 키이자 증적에 남는 식별자다.
# 공백·따옴표·제어문자가 섞이면 로그와 증적이 읽기 어려워진다.
ARCH_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")


def list_arches(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT arch, max_params, note, added_at FROM agent_arch ORDER BY arch"
    ).fetchall()
    return [dict(r) for r in rows]


def create_arch(
    conn: psycopg.Connection,
    *,
    arch: str,
    max_params: int,
    note: str | None = None,
) -> dict[str, Any]:
    """허용 아키텍처 한 개를 **추가**한다. 추가만 — 갱신·삭제 없음.

    `max_params` 는 계약 게이트가 쓰는 상한이다(참조 구현은 로드 후 파라미터 수를,
    비참조는 가중치 지문의 shape 합계를 이 값과 비교한다).
    """
    if not ARCH_NAME.match(arch or ""):
        raise ValueError(
            "arch 이름은 영문으로 시작하고 영숫자·_·.·- 만 쓸 수 있다 (64자 이하)"
        )
    # 상한은 DB CHECK(max_params > 0)가 갖는다. 여기서 다시 적으면 두 곳이 어긋난다 —
    # 0 이하만 먼저 걸러 **어느 제약인지** 말해 준다.
    if max_params < 1:
        raise ValueError("max_params must be > 0 (agent_arch_max_params_check)")

    # 중복은 **INSERT 전에** 본다. UniqueViolation 이 나면 트랜잭션이 죽어서
    # 「지금 값이 얼마인지」를 되물을 수 없기 때문이다 — 그러면 운영자에게
    # 「이미 있다」까지만 말하고 무엇과 부딪혔는지는 못 말한다.
    existing = conn.execute(
        "SELECT max_params FROM agent_arch WHERE arch = %s", (arch,)
    ).fetchone()
    if existing is not None:
        raise ValueError(
            f"arch {arch!r} already exists (max_params={existing['max_params']}). "
            "상한을 바꾸려면 새 이름으로 등록한다 — 갱신하면 이미 발급된 증서의 근거가 바뀐다"
        )

    try:
        row = conn.execute(
            """
            INSERT INTO agent_arch (arch, max_params, note)
            VALUES (%(arch)s, %(max_params)s, %(note)s)
            RETURNING arch, max_params, note, added_at
            """,
            {"arch": arch, "max_params": max_params, "note": note},
        ).fetchone()
    except pg_errors.UniqueViolation as exc:
        # 위 조회와 INSERT 사이에 다른 요청이 먼저 넣은 경우. 여기서는 되묻지 않는다
        # (트랜잭션이 이미 죽었다) — 판정은 DB 가 했고 우리는 그대로 전한다.
        raise ValueError(f"arch {arch!r} already exists") from exc
    return dict(row)
