#!/usr/bin/env python3
"""강제 모드 불변식 (S1 · 안전 사슬 G1). **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇이 문제였나

`check_api_key`(23) · `check_node_credential`(17) 은 **DB 계층**을 본다 — 키 해시·역할·
증서 검증 자체. 그런데 「**강제를 켜면 실제로 401 이 나오는가**」는 `prod_room.sh`(수동) 에만
있었다. **안전이 핵심 기능인데 그 회귀를 CI 가 잡지 못했다** (`docs/design/safety-chain.md` G1).

## 무엇을 고정하나

앱의 **강제 분기** — `_actor` · `_require` · `_authenticated_node` · `_assert_node_matches`.
HTTP 서버를 띄우지 않는다. 그 함수들이 `HTTPException(401/403)` 을 던지는지를 직접 본다
(새 의존성 0 — `httpx`/`TestClient` 를 끌어오지 않는다).

강제 플래그는 **모듈 상수**라 임포트 시점에 굳는다. 그래서 환경변수를 바꾸고
`importlib.reload` 로 두 모드를 모두 확인한다 — 그게 실제 배포 모양이기도 하다
(`compose.prod.yaml` 이 환경으로 뒤집는다).

### 켜짐 (`REQUIRE_*=1` · 제품)

1. 키 없음 → **401** · 형식이 아닌 값 → **401** · 없는 키 → **401**
2. 역할이 모자라면 → **403** (`user` 키로 `admin` 요구)
3. 증서 없음 → **401** · 다른 Node 증서 → **403** (사칭)

### 꺼짐 (`REQUIRE_*=0` · 데모)

4. 키 없음 → 통과(레거시 경로). **그러나 잘못된 키는 여전히 401** —
   「강제가 꺼져 있으니 아무 키나 통과」하는 구간을 만들지 않는다
5. 역할 검사는 **켜짐/꺼짐과 무관하게** 돈다 — 키가 오면 항상 역할까지 본다
6. 증서가 오면 항상 검증한다 — 다른 Node 증서는 꺼짐에서도 **403**

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import importlib
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.apikey import ensure_user, issue_key  # noqa: E402
from app.config import settings  # noqa: E402
from app.const import SEED_ADMIN_ID  # noqa: E402
from app.credential import issue_credential  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def status_of(fn, *args) -> int | str:
    """호출 결과를 상태코드로 옮긴다. 통과하면 'pass'."""
    try:
        fn(*args)
    except HTTPException as exc:
        return exc.status_code
    except Exception as exc:  # 예상 못 한 실패는 그대로 드러낸다
        return f"{type(exc).__name__}: {exc}"
    return "pass"


def load_main(*, api_key: bool, node_cred: bool):
    """강제 플래그를 환경에 심고 app.main 을 다시 읽는다.

    상수가 임포트 시점에 굳으므로 reload 가 아니면 한 모드밖에 못 본다.
    """
    os.environ["REQUIRE_API_KEY"] = "1" if api_key else "0"
    os.environ["REQUIRE_NODE_CREDENTIAL"] = "1" if node_cred else "0"
    # 워커는 startup 이벤트에서만 뜬다 — 임포트만으로는 돌지 않는다.
    import app.main as m

    return importlib.reload(m)


def main() -> int:
    print("강제 모드 불변식 (S1) — 앱의 강제 분기를 본다\n")

    with psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=True) as conn:
        admin = ensure_user(conn, name="enf-admin", role="admin")
        plain = ensure_user(conn, name="enf-user", role="user")
        admin_key = issue_key(conn, user_id=admin["id"], label="enf")["secret"]
        user_key = issue_key(conn, user_id=plain["id"], label="enf")["secret"]

        nodes = conn.execute(
            "SELECT id FROM node ORDER BY created_at LIMIT 2"
        ).fetchall()
        if len(nodes) < 2:
            print("Node 가 2개 미만이다 — 시드 확인", file=sys.stderr)
            return 1
        node_a, node_b = uuid.UUID(str(nodes[0]["id"])), uuid.UUID(str(nodes[1]["id"]))
        cred_a = issue_credential(
            conn, node_id=node_a, issued_by=uuid.UUID(SEED_ADMIN_ID), label="enf"
        )["secret"]

    bad_key = "ck_deadbeef." + "A" * 43

    # ── 켜짐 ────────────────────────────────────────────────────────────
    m = load_main(api_key=True, node_cred=True)
    print("  [REQUIRE_API_KEY=1 · REQUIRE_NODE_CREDENTIAL=1]")
    check(m.REQUIRE_API_KEY and m.REQUIRE_NODE_CREDENTIAL, "강제 플래그가 켜졌다")

    check(status_of(m._actor, None) == 401, "키 없음 → 401")
    check(status_of(m._actor, "not-a-key") == 401, "형식이 아닌 값 → 401")
    check(status_of(m._actor, bad_key) == 401, "없는 키 → 401")
    check(status_of(m._actor, f"CapNet-Key {admin_key}") == "pass", "admin 키 → 통과")

    check(status_of(m._require, "admin", None) == 401, "무인증 admin 요구 → 401")
    check(status_of(m._require, "admin", user_key) == 403,
          "역할 부족(user→admin) → 403")
    check(status_of(m._require, "admin", admin_key) == "pass", "admin 키로 admin 요구 → 통과")
    check(status_of(m._require, "user", user_key) == "pass", "user 키로 user 요구 → 통과")

    check(status_of(m._authenticated_node, None) == 401, "증서 없음 → 401")
    check(status_of(m._authenticated_node, f"CapNet-Node {bad_key}") == 401,
          "가짜 증서 → 401")
    check(status_of(m._assert_node_matches, node_b, f"CapNet-Node {cred_a}") == 403,
          "다른 Node 증서로 사칭 → 403")
    check(status_of(m._assert_node_matches, node_a, f"CapNet-Node {cred_a}") == "pass",
          "자기 증서 → 통과")

    # ── 초대 소진: 관리 키 없이 열리는 유일한 쓰기 (G2 · 0016) ───────────
    #
    # 이 경로가 «키 없이 열린다»는 것 자체가 이 기능의 위험이다. 그래서 두 가지를 같이 본다:
    #   ① 초대 토큰 없이는 못 들어온다 (열려 있다 ≠ 아무나 쓴다)
    #   ② 막는 주체가 «API 키 강제»가 아니다 — 키를 요구하면 초대받은 사람이 못 쓴다
    body = m.NodeRedeem(name="probe")
    check(status_of(m.node_redeem, body, None) == 401,
          "초대 토큰 없이 소진 → 401 (강제 모드에서도 열린 경로다)")
    detail = ""
    try:
        m.node_redeem(body, None)
    except Exception as exc:  # noqa: BLE001 — HTTPException.detail 만 본다
        detail = str(getattr(exc, "detail", ""))
    check("초대 토큰" in detail and "api key" not in detail.lower(),
          "막는 주체가 API 키 강제가 아니다 (초대 토큰을 요구한다)", detail[:44])
    check(status_of(m.node_redeem, body, f"CapNet-Invite ci_deadbeef.{'A' * 43}") == 401,
          "없는 초대 토큰 → 401")

    # ── 꺼짐 ────────────────────────────────────────────────────────────
    m = load_main(api_key=False, node_cred=False)
    print("\n  [REQUIRE_API_KEY=0 · REQUIRE_NODE_CREDENTIAL=0 — 데모 경로]")
    check(not m.REQUIRE_API_KEY and not m.REQUIRE_NODE_CREDENTIAL, "강제 플래그가 꺼졌다")

    check(status_of(m._actor, None) == "pass", "키 없음 → 통과 (레거시 경로)")
    check(status_of(m._authenticated_node, None) == "pass", "증서 없음 → 통과")

    # 여기가 요점이다 — 꺼져 있어도 «잘못된» 자격은 통과시키지 않는다.
    check(status_of(m._actor, bad_key) == 401, "꺼져 있어도 없는 키는 401")
    check(status_of(m._require, "admin", user_key) == 403,
          "꺼져 있어도 역할은 본다 (user→admin 403)")
    check(status_of(m._authenticated_node, f"CapNet-Node {bad_key}") == 401,
          "꺼져 있어도 가짜 증서는 401")
    check(status_of(m._assert_node_matches, node_b, f"CapNet-Node {cred_a}") == 403,
          "꺼져 있어도 사칭은 403")

    # 원래대로 되돌린다 — 뒤에 오는 검사가 이 프로세스를 쓰지는 않지만, 환경을 남기지 않는다.
    os.environ.pop("REQUIRE_API_KEY", None)
    os.environ.pop("REQUIRE_NODE_CREDENTIAL", None)

    failed = [r for r in results if not r[0]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        return 1
    print("강제는 플래그로 켜지지만, 잘못된 자격은 꺼져 있어도 통과하지 않는다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
