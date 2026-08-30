#!/usr/bin/env python3
"""`PATCH /v1/capabilities/{id}` — 설명만 바뀌고 계약은 안 바뀐다. **DB 가 필요하다.**

파일명이 `test_` 로 시작하지 않는 것은 의도다 — `unittest discover` 가 집어가면
DB 없는 단위 테스트 실행이 깨진다.

## 무엇을 고정하나

등록(`POST`)은 `(code, version)` UNIQUE 로 한 번뿐이라, 저장소에서 `description` 을 고쳐도
**이미 등록된 스택에는 영원히 안 들어갔다.** 라우터는 DB 의 설명을 읽으므로 오래 돌아간
스택은 저장소와 다른 문구로 라우팅한다 (실측: 홀드아웃 10점 차 · 브리지
`routing-measured-not-fixed`). Decision (b) 가 그 하나를 여는 길로 PATCH 를 골랐다.

여기서 보는 것은 **연 것이 그 하나뿐인가**다.

1. `description` 이 실제로 바뀐다
2. **계약 칸은 하나도 안 바뀐다** — PATCH 전후 스냅샷을 통째로 비교한다. ← 핵심
3. 계약 칸을 보내면 **400** (모델이 막는다 · 화이트리스트를 손으로 세지 않는다)
4. 없는 id 는 **404**
5. `code`·`version` 도 못 바꾼다 (같은 400 경로지만 따로 못 박는다)

전부 SAVEPOINT 로 돌리고 ROLLBACK 한다 — 앱 계층(FastAPI)은 DB 트랜잭션을 공유하지
못하므로 여기서는 **모델 검증**과 **SQL 갱신**을 각각 그 계층에서 본다.

환경: DATABASE_URL · PYTHONPATH=apps/core
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "core"))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.capability import update_capability_description  # noqa: E402
from app.config import settings  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


CAP_INSERT = """
INSERT INTO capability (code, version, name, description, input_schema, output_schema,
                        output_kind, compute_tier, trust_domain_min,
                        golden_set_ref, golden_set_sha256, golden_set_size, golden_metrics,
                        quality_profile, max_input_bytes, max_attempts)
VALUES (%(code)s, 1, 'probe', %(desc)s, '{"a": 1}'::jsonb, '{"b": 2}'::jsonb,
        'structured', 'M', 'team', '(none)', %(zero)s, 1, '{}'::jsonb, 'none', 4096, 3)
RETURNING id
"""

# PATCH 가 건드리면 안 되는 칸. 하나라도 움직이면 스냅샷이 거짓말이 된다.
CONTRACT_COLUMNS = (
    "code", "version", "name", "input_schema", "output_schema", "output_kind",
    "compute_tier", "trust_domain_min", "mvp_eligible", "quality_profile",
    "max_input_bytes", "max_attempts",
    "golden_set_ref", "golden_set_sha256", "golden_set_size", "golden_metrics",
)


def snapshot(conn: psycopg.Connection, cap_id) -> dict:
    cols = ", ".join(CONTRACT_COLUMNS)
    row = conn.execute(
        f"SELECT {cols} FROM capability WHERE id = %s", (str(cap_id),)
    ).fetchone()
    return dict(row)


def run_db_checks(conn: psycopg.Connection) -> None:
    conn.execute("SAVEPOINT probe")
    cap_id = conn.execute(
        CAP_INSERT,
        {"code": f"probe.patch.{uuid.uuid4().hex[:8]}", "desc": "옛 설명", "zero": "0" * 64},
    ).fetchone()["id"]

    before = snapshot(conn, cap_id)

    row = update_capability_description(conn, cap_id, description="새 설명")
    check(row is not None and row["description"] == "새 설명",
          "description 이 실제로 바뀐다", str(row and row["description"]))

    after = snapshot(conn, cap_id)
    moved = [c for c in CONTRACT_COLUMNS if before[c] != after[c]]
    check(moved == [], "계약 칸은 하나도 안 바뀐다", f"움직인 칸: {moved}" if moved else "16칸 동일")

    missing = update_capability_description(conn, uuid.uuid4(), description="x")
    check(missing is None, "없는 id 는 None (라우트가 404 로 옮긴다)")

    # description 을 비우는 것도 허용한다 — 계약이 NOT NULL 이 아니다.
    row = update_capability_description(conn, cap_id, description=None)
    check(row is not None and row["description"] is None, "None 으로도 비울 수 있다")

    conn.execute("ROLLBACK TO SAVEPOINT probe")


def run_model_checks() -> None:
    """허용 밖 필드는 **모델이** 막는다 — 라우트에 화이트리스트를 손으로 적지 않는다."""
    try:
        from app.main import CapabilityDescriptionPatch
    except Exception as exc:  # fastapi 가 없으면 이 검사만 건너뛴다
        check(False, "app.main 임포트", f"{exc}")
        return

    ok = CapabilityDescriptionPatch(description="예")
    check(ok.description == "예", "description 만 있으면 통과한다")

    forbidden = [
        "input_schema", "output_schema", "output_kind", "compute_tier",
        "trust_domain_min", "quality_profile", "golden_set_ref", "golden_set_sha256",
        "golden_set_size", "golden_metrics", "max_input_bytes", "max_attempts",
        "mvp_eligible", "code", "version", "name", "id",
    ]
    rejected = []
    for field in forbidden:
        try:
            CapabilityDescriptionPatch(description="예", **{field: 1})
        except Exception:
            rejected.append(field)
    check(sorted(rejected) == sorted(forbidden),
          "계약 칸 17종은 전부 거절된다 (400)",
          f"통과해 버린 칸: {sorted(set(forbidden) - set(rejected))}")


def main() -> int:
    print("== PATCH /v1/capabilities/{id} — 설명만 연다 ==")
    run_model_checks()
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        run_db_checks(conn)

    failed = [n for ok, n, _ in results if not ok]
    print(f"\n===== 결과: 통과 {len(results) - len(failed)} · 실패 {len(failed)} =====")
    if failed:
        for name in failed:
            print(f"  FAIL {name}")
        return 1
    print("설명만 열렸다 — 계약은 그대로다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
