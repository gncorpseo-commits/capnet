"""안전 자세 조회면 (S2 · safety-chain G3).

「**누가 내 데이터를 돌릴 수 있나**」를 한 면에서 답한다.

지금까지 이 질문에 답하려면 조회면 넷을 이어 붙여야 했다 —
`/v1/nodes`(등급) · `/v1/nodes-credentials`(증서) · `/v1/nodes-liveness`(생사) ·
`/v1/ops/status`(합계). 기기 하나에 대해 「왜 실행 가능한가」가 한 곳에 없었다 (G3).

## 규율

- **읽기 전용.** INSERT/UPDATE 없음. 새 테이블·뷰 없음 (DDL 0).
- **시크릿 없음.** 증서는 `key_prefix`·만료·마지막 사용만 — 해시도 토큰도 나가지 않는다.
- **라우팅 가능 판정은 `claim` 과 같은 조인으로 센다.** 조회면이 실제 배정과 갈라지면
  「안전하다고 보여주는데 실제로는 다르다」가 된다. 그게 이 조회면의 유일한 실패 방식이다.
  아래 `_ROUTABLE_PAIRS` 는 `claim.CLAIM_SQL` 의 후보 조건에서 **task 쪽만 뺀 것**이다.
"""

from __future__ import annotations

from typing import Any

import psycopg

# claim.CLAIM_SQL 의 후보 조건과 같아야 한다 (task 쪽 조건만 제외):
#   증서 유효(revoked_at IS NULL) · Agent ACTIVE · agent_node_ready · 티어 호환.
# 여기서 세는 것은 「이 기기에서 지금 돌 수 있는 (Agent, 능력) 쌍」이다.
_ROUTABLE_PAIRS = """
    SELECT count(*)
      FROM agent_capability_passed acp
      JOIN agent ag             ON ag.id = acp.agent_id AND ag.status = 'ACTIVE'
      JOIN agent_node_ready anr ON anr.agent_id = acp.agent_id AND anr.node_id = n.id
      JOIN capability c         ON c.id = acp.capability_id
      JOIN tier_compatible tc   ON tc.capability_tier = c.compute_tier
                               AND tc.node_tier_max = n.compute_tier_max
     WHERE acp.revoked_at IS NULL
"""

SAFETY_SQL = f"""
SELECT
    n.id                        AS node_id,
    n.name,
    n.device_type,
    n.trust_domain,
    n.provision_source,
    n.compute_tier_max,
    n.is_gate_runner,
    n.created_at,

    -- 증서 (0007). 시크릿·해시는 뽑지 않는다.
    coalesce(cred.credential_valid, false) AS credential_valid,
    cred.key_prefix,
    cred.issued_at              AS credential_issued_at,
    cred.expires_at             AS credential_expires_at,
    cred.last_used_at           AS credential_last_used_at,

    -- 생사
    live.availability,
    live.last_heartbeat,
    coalesce(live.is_fresh, false) AS is_fresh,

    -- 이 기기가 받을 수 있는 요청의 신뢰 도메인 (domain_compatible = 정책 행렬).
    -- team(3) 기기는 public·tenant·team 을 받고, public(1) 기기는 public 만 받는다.
    (SELECT array_agg(dc.task_domain ORDER BY dc.task_privacy_rank DESC)
       FROM domain_compatible dc
      WHERE dc.node_domain = n.trust_domain)     AS accepts_task_domains,

    -- 지금 이 기기로 배정될 수 있는 (Agent, 능력) 쌍
    ({_ROUTABLE_PAIRS})                          AS routable_pairs,

    (SELECT count(*) FROM agent_node_ready anr
      WHERE anr.node_id = n.id)                  AS agents_ready,

    (SELECT count(*) FROM assignment a
      WHERE a.node_id = n.id AND a.status = 'LEASED'
        AND a.lease_expires_at > now())          AS leases_live,

    -- 위험 축 둘 — 기기 단위로 센다 (합계는 /v1/ops/status 가 준다).
    -- arch 미선언 Agent 가 이 기기에서 돌 수 있나 (G5 · 0008)
    (SELECT count(*)
       FROM agent_arch_unbound au
       JOIN agent_node_ready anr ON anr.agent_id = au.agent_id AND anr.node_id = n.id
      WHERE au.routable)                         AS arch_unbound_routable,

    -- 구 골든셋 증서로 이 기기에서 돌 수 있나 (SD-013 · 0002/0004)
    (SELECT count(DISTINCT pd.agent_id)
       FROM provenance_drift pd
       JOIN agent_node_ready anr ON anr.agent_id = pd.agent_id AND anr.node_id = n.id
      WHERE pd.still_routable)                   AS drift_routable

FROM node n
-- node_credential_status 는 유효 증서가 여럿이면 행이 늘어난다. 하나로 좁힌다.
LEFT JOIN LATERAL (
    SELECT * FROM node_credential_status s
     WHERE s.node_id = n.id
     ORDER BY s.credential_valid DESC, s.issued_at DESC NULLS LAST
     LIMIT 1
) cred ON TRUE
LEFT JOIN node_liveness live ON live.node_id = n.id
ORDER BY n.trust_domain, n.name
"""


def _node_risks(row: dict[str, Any], *, require_credential: bool) -> list[str]:
    """기기 하나의 위험 표시. 숫자만 주면 보는 사람마다 기준이 달라진다."""
    risks: list[str] = []

    if not row["credential_valid"]:
        if require_credential:
            # 강제가 켜져 있으면 안전하지만 **일을 못 한다** — 위험이 아니라 가용성 문제다.
            risks.append("증서 없음 — 강제가 켜져 있어 이 기기는 배정을 가져갈 수 없다")
        else:
            risks.append("증서 없음 — 강제를 켜면 이 기기는 잠긴다 (지금은 사칭을 막지 못한다)")

    if not row["is_fresh"]:
        risks.append("heartbeat 끊김 — 살아 있지 않다")
    elif row["availability"] in ("DRAINING", "OFFLINE"):
        risks.append(f"배정을 받지 않는 상태다 ({row['availability']})")

    if row["arch_unbound_routable"]:
        risks.append(
            f"arch 미선언 Agent 가 이 기기로 라우팅 가능 {row['arch_unbound_routable']}건"
        )
    if row["drift_routable"]:
        risks.append(f"구 골든셋 증서로 라우팅 가능 {row['drift_routable']}건 (재게이트 대상)")

    # 등급과 조달 경로가 어긋난 조합은 DB CHECK 가 막는다(ck_trust_provision_align).
    # 여기서는 「막히지는 않지만 봐야 하는」 조합만 표시한다.
    if row["trust_domain"] == "team" and row["provision_source"] != "team":
        risks.append("team 등급인데 조달 경로가 team 이 아니다")

    return risks


def safety_posture(
    conn: psycopg.Connection,
    *,
    require_api_key: bool,
    require_credential: bool,
) -> dict[str, Any]:
    """함대의 안전 자세를 한 번에 준다. 쓰기 없음."""
    rows = [dict(r) for r in conn.execute(SAFETY_SQL).fetchall()]

    nodes: list[dict[str, Any]] = []
    for row in rows:
        row["accepts_task_domains"] = row["accepts_task_domains"] or []
        row["risks"] = _node_risks(row, require_credential=require_credential)
        row["ok"] = not row["risks"]
        nodes.append(row)

    # 「내 team 요청을 돌릴 수 있는 기기가 몇 대인가」 — 질문 그대로의 답.
    # 실제로 배정되려면 라우팅 가능한 (Agent, 능력) 쌍도 있어야 하므로 둘 다 센다.
    by_domain: dict[str, dict[str, int]] = {}
    for domain in ("team", "tenant", "public"):
        eligible = [n for n in nodes if domain in n["accepts_task_domains"]]
        by_domain[domain] = {
            "nodes_eligible": len(eligible),
            "nodes_live": sum(1 for n in eligible if n["is_fresh"]),
            "nodes_routable": sum(1 for n in eligible if n["routable_pairs"] > 0),
            "nodes_without_credential": sum(1 for n in eligible if not n["credential_valid"]),
        }

    totals = {
        "nodes": len(nodes),
        "nodes_live": sum(1 for n in nodes if n["is_fresh"]),
        "nodes_without_credential": sum(1 for n in nodes if not n["credential_valid"]),
        "nodes_with_risk": sum(1 for n in nodes if n["risks"]),
        "routable_pairs": sum(n["routable_pairs"] for n in nodes),
    }

    warnings: list[str] = []
    if not require_credential and totals["nodes_without_credential"]:
        warnings.append(
            f"증서 없는 기기 {totals['nodes_without_credential']}대가 배정을 가져갈 수 있다 "
            "— REQUIRE_NODE_CREDENTIAL 이 꺼져 있다"
        )
    if not require_api_key:
        warnings.append("관리 API 강제가 꺼져 있다 — 등록·바인딩이 열려 있다 (SD-010)")
    if totals["nodes"] and totals["nodes_live"] == 0:
        warnings.append("살아 있는 기기가 없다")
    if totals["routable_pairs"] == 0:
        warnings.append("라우팅 가능한 (Agent, 능력) 쌍이 없다 — 게이트·바인딩 확인")

    return {
        # ok = 위험 표시가 하나도 없다. 강제가 꺼져 있으면 여기서 false 다 —
        # 데모 기본값에서 ok=true 가 나오면 이 조회면은 거짓말을 하는 것이다.
        "ok": not warnings and totals["nodes_with_risk"] == 0,
        "enforcement": {
            "api_key": require_api_key,
            "node_credential": require_credential,
        },
        "totals": totals,
        "by_task_domain": by_domain,
        "warnings": warnings,
        "nodes": nodes,
    }
