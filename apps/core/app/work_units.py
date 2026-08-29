"""작업량 조회면 — `GET /v1/ops/work-units` (P2-2 · PR-C · Decision D1–D3).

## 무엇을 재나

로드맵 P2-2 는 「`duration_ms`·`vram_mb_peak` 계측」인데 **컬럼은 이미 있었다.**
남아 있던 것은 「무엇을 정본으로 볼 것인가」였고, 그것이 Decision 으로 정해졌다.

| 값 | 뜻 | 지위 |
|---|---|---|
| `core_observed_ms` | `assignment.finished_at − created_at` | **정본** (D1-a) |
| `node_hint_ms` | `assignment.duration_ms` — Node 가 잰 **추론 구간만** | 힌트 (D1-a) |
| `vram_mb_peak` · `energy_wh` | — | **미계측** (D2-a) |

**왜 Core 관측이 정본인가.** 절대규칙 4 는 「Node 는 자기 등급을 주장할 수 없다」다.
등급이 그렇다면 **자기 일의 양**도 같은 질문을 받는다. Node 자기신고는 전송·대기·큐를
빼고 재므로, 그 값으로 원가를 세우면 실제보다 싸게 잡힌다 (실측 평균 차 789 ms).

**왜 힌트를 지우지 않나.** 둘은 틀린 값이 아니라 **재는 대상이 다르다.** 관측에서
자기신고를 빼면 「일 밖에서 쓴 시간」이 나온다 — 그건 지우면 못 얻는 값이다.

**왜 `vram_mb_peak` 을 RSS 로 채우지 않나.** 우리 Node 는 CPU 휠이다. 주기억 사용량을
그 칸에 넣으면 **칸 이름이 거짓말이 된다.** 못 잰 것은 못 쟀다고 적는다.

## 규율

- **읽기 전용 · DDL 0 · 새 컬럼 0.** 관측 시간은 저장하지 않는다 — 파생값이다.
- **시크릿 없음.** id·이름·개수·밀리초만 나간다.
- 종결된 배정만 센다 (`finished_at IS NOT NULL`). 도는 중인 것을 평균에 넣으면
  「지금 느리다」와 「방금 시작했다」가 섞인다.
"""

from __future__ import annotations

from typing import Any

import psycopg

# 기본 창. 「최근 7일」은 Decision D3 이 정한 정책 숫자다.
DEFAULT_WINDOW_DAYS = 7
# 상한. 더 긴 창은 조회면이 아니라 원장이 할 일이다.
MAX_WINDOW_DAYS = 90

# 종결된 배정 한 건 = work unit 한 건.
# `EXTRACT(EPOCH …)` 는 numeric 이라 ms 로 올린 뒤 정수로 내린다.
_WINDOW = """
    SELECT a.id,
           a.status,
           a.capability_id,
           a.node_id,
           a.duration_ms                                                  AS node_hint_ms,
           round(EXTRACT(EPOCH FROM (a.finished_at - a.created_at)) * 1000)::bigint
                                                                          AS core_observed_ms,
           a.vram_mb_peak,
           a.energy_wh
      FROM assignment a
     WHERE a.finished_at IS NOT NULL
       AND a.finished_at >= now() - make_interval(days => %(days)s)
"""

# 합계·평균은 **SQL 이 낸다.** 앱이 행을 끌어와 더하면 창이 커질수록 응답이 무거워진다.
_AGG = """
    count(*)                                             AS assignments,
    count(*) FILTER (WHERE status = 'SUCCEEDED')         AS succeeded,
    count(*) FILTER (WHERE status = 'FAILED')            AS failed,
    coalesce(sum(core_observed_ms), 0)::bigint           AS core_observed_ms_sum,
    round(avg(core_observed_ms))::bigint                 AS core_observed_ms_avg,
    max(core_observed_ms)::bigint                        AS core_observed_ms_max,
    coalesce(sum(node_hint_ms), 0)::bigint               AS node_hint_ms_sum,
    round(avg(node_hint_ms))::bigint                     AS node_hint_ms_avg,
    count(*) FILTER (WHERE node_hint_ms IS NULL)         AS node_hint_missing,
    count(*) FILTER (WHERE vram_mb_peak IS NOT NULL)     AS vram_measured,
    count(*) FILTER (WHERE energy_wh IS NOT NULL)        AS energy_measured
"""

TOTALS_SQL = f"""
WITH w AS ({_WINDOW})
SELECT {_AGG},
       -- 관측은 자기신고를 **포함하는** 구간이다. 뒤집히면 시계·보고가 어긋난 것이다.
       count(*) FILTER (
           WHERE node_hint_ms IS NOT NULL AND node_hint_ms > core_observed_ms
       )                                                 AS hint_exceeds_observed,
       min(core_observed_ms)::bigint                     AS core_observed_ms_min
  FROM w
"""

BY_CAPABILITY_SQL = f"""
WITH w AS ({_WINDOW})
SELECT c.code, c.version, {_AGG}
  FROM w
  JOIN capability c ON c.id = w.capability_id
 GROUP BY c.code, c.version
 ORDER BY assignments DESC, c.code, c.version
"""

BY_NODE_SQL = f"""
WITH w AS ({_WINDOW})
SELECT n.id AS node_id, n.name, n.trust_domain, n.compute_tier_max, {_AGG}
  FROM w
  JOIN node n ON n.id = w.node_id
 GROUP BY n.id, n.name, n.trust_domain, n.compute_tier_max
 ORDER BY assignments DESC, n.name
"""

# 응답에 뜻을 같이 실어 보낸다. 숫자만 주면 읽는 쪽이 `duration_ms` 를
# 「그 일에 든 시간」으로 오해한다 — 그게 이 PR 이 고치려는 것이다.
MEASURE = {
    "canonical": "core_observed_ms",
    "core_observed_ms": (
        "Core 관측 — assignment.finished_at − created_at. **정본** (D1). "
        "전송·대기·큐를 포함한 왕복 전체다. 저장하지 않는 파생값이다."
    ),
    "node_hint_ms": (
        "Node 자기신고 — assignment.duration_ms. Node 가 잰 **추론 구간만**이라 "
        "관측보다 작다. 검증할 수 없으므로 힌트로만 쓴다 (D1)."
    ),
    "vram_mb_peak": "미계측 — 우리 Node 는 CPU 휠이다. RSS 로 대체하지 않는다 (D2).",
    "energy_wh": "미계측 — 재는 장치가 없다 (D2).",
}


def _clean(row: dict[str, Any]) -> dict[str, Any]:
    """UUID 는 문자열로, `avg` 의 None 은 0 으로."""
    out: dict[str, Any] = {}
    for key, val in row.items():
        if key.endswith("_id") and val is not None:
            out[key] = str(val)
        elif key.endswith(("_sum", "_avg", "_max", "_min")) and val is None:
            # 창에 행이 없으면 avg·max 는 NULL 이다. 0 으로 내려 보내면
            # 「0ms 였다」로 읽힌다 — 건수가 0 인 것은 assignments 가 말한다.
            out[key] = None
        else:
            out[key] = val
    return out


def work_units(
    conn: psycopg.Connection, *, days: int = DEFAULT_WINDOW_DAYS
) -> dict[str, Any]:
    """최근 `days` 일의 작업량. 쓰기 없음."""
    if not 1 <= days <= MAX_WINDOW_DAYS:
        raise ValueError(f"days 는 1..{MAX_WINDOW_DAYS} 여야 한다 (받음 {days})")

    params = {"days": days}
    totals = _clean(dict(conn.execute(TOTALS_SQL, params).fetchone()))
    by_capability = [
        _clean(dict(r)) for r in conn.execute(BY_CAPABILITY_SQL, params).fetchall()
    ]
    by_node = [_clean(dict(r)) for r in conn.execute(BY_NODE_SQL, params).fetchall()]

    warnings: list[str] = []
    if totals["assignments"] == 0:
        warnings.append(f"최근 {days}일에 종결된 배정이 없다")
    if totals["hint_exceeds_observed"]:
        warnings.append(
            f"Node 자기신고가 Core 관측보다 큰 배정 {totals['hint_exceeds_observed']}건 "
            "— 시계나 보고가 어긋났다 (관측은 자기신고를 포함하는 구간이다)"
        )
    if totals["assignments"] and totals["node_hint_missing"] == totals["assignments"]:
        warnings.append("Node 자기신고가 하나도 없다 — Node 가 duration_ms 를 보내는지 확인")

    return {
        "ok": not warnings,
        "window_days": days,
        "measure": MEASURE,
        "totals": totals,
        "by_capability": by_capability,
        "by_node": by_node,
        "warnings": warnings,
    }
