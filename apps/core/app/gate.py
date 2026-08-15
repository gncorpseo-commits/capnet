"""게이트 사슬 — INSERT … SELECT 만. 추론은 Node/score_gate, 여기선 기록·검증만."""

from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg
from psycopg import errors as pg_errors

START_SQL = """
INSERT INTO gate_run (
    agent_id, capability_id, runner_node_id, runner_is_gate_runner,
    status, golden_set_sha256, kind, capability_quality_profile, sample_input_id,
    capability_preprocess
)
SELECT a.id, c.id, n.id, n.is_gate_runner,
       'RUNNING', c.golden_set_sha256,
       -- 종류는 **능력이 정한다.** 앱이 고르면 golden 능력에 계약 게이트런을 붙일 수 있다
       -- (DB 가 복합 FK 로 거절하지만, 애초에 고를 일이 아니다 · D20).
       CASE WHEN c.quality_profile = 'none' THEN 'contract' ELSE 'golden' END,
       c.quality_profile,
       -- 계약 게이트런은 무엇으로 검증했는지를 남긴다. 샘플이 없으면
       -- ck_gate_run_contract_needs_sample 이 INSERT 를 거절한다 (0013).
       CASE WHEN c.quality_profile = 'none' THEN c.sample_input_id ELSE NULL END,
       -- 전처리 선언 스냅샷. 없으면 ck_gate_run_contract_needs_preprocess 가 거절한다 (0014).
       CASE WHEN c.quality_profile = 'none'
            THEN c.input_schema -> 'preprocess' ELSE NULL END
  FROM agent a
  JOIN capability c ON c.id = %(capability_id)s
  JOIN node n ON n.id = %(runner_node_id)s AND n.is_gate_runner = true
 WHERE a.id = %(agent_id)s
RETURNING id, agent_id, capability_id, runner_node_id, runner_is_gate_runner,
          status, golden_set_sha256, kind, capability_quality_profile,
          sample_input_id, capability_preprocess, created_at
"""

# 계약 게이트런이 통과하려면 러너가 **실행해서** 확인해야 하는 항목 (D20 · B2).
# 「무엇을 근거로 이 Agent 가 이 능력에 붙었는가」가 증적에 남는다.
#
# `preprocess` 가 돌아왔다 (0014) — 계약이 `input_schema.preprocess` 로 값을 선언하게 되면서
# 러너가 **그 값을 적용해** 확인할 수 있게 됐다. 0013 에서 뺐던 이유(검증 없는 불린)가 사라졌다.
CONTRACT_CHECKS_COMMON = (
    "input_schema", "output_schema", "preprocess", "weights_fingerprint",
    # D-maxp: 비참조에도 파라미터 상한을 요구한다. 지문이 shape 만으로 셀 수 있으므로
    # torch 없이도 판정 가능하다 — 「실행해야만 셀 수 있는 값」이 아니었다.
    # 이게 빠져 있는 동안 비참조 모델에는 **상한이 없었다.**
    "max_params",
)

# 참조 구현(우리가 빌더를 가진 arch)일 때만 추가로 요구하는 것.
# **실행해서** 판정할 수 있는 유일한 경우이므로 여기서는 원칙을 낮추지 않는다.
CONTRACT_CHECKS_REFERENCE = ("arch",)

# Core 가 아는 「참조 구현」 arch 이름. 이것은 정책이 아니라 **코드 사실**이다 —
# 「우리 러너에 빌더가 있는가」이므로 DB 행(`agent_arch`)이 아니라 상수로 둔다.
# `agent_arch` 는 **등록 허용 목록**이고(FK 로 막는다), 이쪽은 **실행 가능 목록**이다.
# 둘이 어긋나면 `test_contract_checks_by_arch` 가 잡는다.
REFERENCE_ARCHS = frozenset({"TinyEuroSAT", "TinyEuroSATB"})

# 하위 호환 별칭 — 참조 구현일 때의 전체 집합. 기존 문서·스크립트가 이 이름을 쓴다.
CONTRACT_CHECKS = CONTRACT_CHECKS_COMMON + CONTRACT_CHECKS_REFERENCE


def required_contract_checks(arch: str | None) -> tuple[str, ...]:
    """이 Agent 의 계약 게이트런이 만족해야 하는 검사 집합 (Decision 2-C · C2).

    **왜 갈라지는가.** B2 의 원칙은 「계약을 말로 받지 않는다 — 러너가 실행해서 판정한다」였다.
    그 원칙은 **우리 코드가 그 모달리티를 실행할 수 있을 때만** 성립한다.
    `text.generate` 를 실행하려면 제출자 코드가 필요하고, 그건 절대규칙 5 와 정면으로 닿는다.

    그래서 참조 구현이 있으면 **종전 그대로 6종 전부**(무회귀), 없으면 **공통 4종**만 요구한다.
    공통 4종은 실행이 아니라 **선언 정합과 파일 구조**를 본다 — 그 한계는 문서에 적는다
    (`docs/spec/capability-catalog.md` §5).

    `arch` 가 NULL 인 legacy Agent 도 공통 4종으로 떨어진다. 그쪽은 애초에 Core 가
    arch 를 모르므로 참조 구현이라고 말할 근거가 없다.
    """
    if arch in REFERENCE_ARCHS:
        return CONTRACT_CHECKS_COMMON + CONTRACT_CHECKS_REFERENCE
    return CONTRACT_CHECKS_COMMON

FINISH_SQL = """
UPDATE gate_run
   SET status = %(status)s,
       golden_score = %(golden_score)s,
       cases_total = %(cases_total)s,
       cases_passed = %(cases_passed)s,
       result_summary = %(result_summary)s::jsonb,
       finished_at = now()
 WHERE id = %(gate_run_id)s
   AND status = 'RUNNING'
RETURNING id, agent_id, capability_id, runner_node_id, status,
          golden_score, cases_total, cases_passed, result_summary, finished_at,
          kind, capability_quality_profile, sample_input_id, capability_preprocess
"""

MINT_PASSED_SQL = """
INSERT INTO gate_run_passed (gate_run_id, agent_id, capability_id, status)
SELECT gr.id, gr.agent_id, gr.capability_id, gr.status
  FROM gate_run gr
 WHERE gr.id = %(gate_run_id)s
   AND gr.status = 'PASSED'
ON CONFLICT (gate_run_id) DO NOTHING
"""

UPSERT_AC_PASSED_SQL = """
INSERT INTO agent_capability (
    agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at
)
SELECT grp.agent_id, grp.capability_id, 'PASSED', %(golden_score)s, grp.gate_run_id, now()
  FROM gate_run_passed grp
 WHERE grp.gate_run_id = %(gate_run_id)s
ON CONFLICT (agent_id, capability_id) DO UPDATE
   SET gate_status = 'PASSED',
       golden_score = EXCLUDED.golden_score,
       gate_run_id = EXCLUDED.gate_run_id,
       gated_at = EXCLUDED.gated_at
"""

MINT_ACP_SQL = """
INSERT INTO agent_capability_passed (agent_id, capability_id, gate_status)
SELECT ac.agent_id, ac.capability_id, ac.gate_status
  FROM agent_capability ac
  JOIN gate_run_passed grp ON grp.agent_id = ac.agent_id
                          AND grp.capability_id = ac.capability_id
 WHERE grp.gate_run_id = %(gate_run_id)s
   AND ac.gate_status = 'PASSED'
-- 폐기됐던 증서가 다시 통과하면 복권한다. DO NOTHING 이면 영원히 폐기 상태로 남는다.
-- 폐기는 형벌이 아니라 「지금 기준으로 못 미친다」는 표시다 (SD-014).
ON CONFLICT (agent_id, capability_id) DO UPDATE
   SET revoked_at = NULL,
       revoked_reason = NULL,
       revoked_gate_run_id = NULL
 WHERE agent_capability_passed.revoked_at IS NOT NULL
"""

# 폐기 근거 — **현재** 골든셋에서 떨어진 FAILED gate_run 이 있어야 한다.
# 옛 골든셋에서의 실패로는 폐기하지 않는다. 근거 없는 폐기를 막는 것이 요점이다.
REVOKE_EVIDENCE_SQL = """
SELECT gr.id, gr.golden_score, gr.golden_set_sha256, gr.finished_at
  FROM gate_run gr
  JOIN capability c ON c.id = gr.capability_id
 WHERE gr.agent_id = %(agent_id)s
   AND gr.capability_id = %(capability_id)s
   AND gr.status = 'FAILED'
   AND gr.golden_set_sha256 = c.golden_set_sha256
 ORDER BY gr.finished_at DESC NULLS LAST
 LIMIT 1
"""

# 행을 지우지 않는다 — assignment 가 FK 로 참조한다 (D15). 라우팅만 끊는다.
REVOKE_SQL = """
UPDATE agent_capability_passed
   SET revoked_at = now(),
       revoked_reason = %(reason)s,
       revoked_gate_run_id = %(gate_run_id)s
 WHERE agent_id = %(agent_id)s
   AND capability_id = %(capability_id)s
   AND revoked_at IS NULL
RETURNING agent_id, capability_id, revoked_at, revoked_reason, revoked_gate_run_id
"""

REVOKE_AUDIT_SQL = """
INSERT INTO audit_log (task_id, actor_type, event, payload)
VALUES (NULL, 'core', 'capability_revoked', %(payload)s::jsonb)
"""

UPSERT_AC_FAILED_SQL = """
INSERT INTO agent_capability (
    agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at
)
SELECT gr.agent_id, gr.capability_id, 'FAILED', %(golden_score)s, NULL, now()
  FROM gate_run gr
 WHERE gr.id = %(gate_run_id)s
   AND gr.status = 'FAILED'
ON CONFLICT (agent_id, capability_id) DO UPDATE
   SET gate_status = 'FAILED',
       golden_score = EXCLUDED.golden_score,
       gate_run_id = NULL,
       gated_at = EXCLUDED.gated_at
 WHERE agent_capability.gate_status <> 'PASSED'
"""


def start_gate_run(
    conn: psycopg.Connection,
    *,
    agent_id: uuid.UUID,
    capability_id: uuid.UUID,
    runner_node_id: uuid.UUID,
) -> dict[str, Any] | None:
    try:
        row = conn.execute(
            START_SQL,
            {
                "agent_id": str(agent_id),
                "capability_id": str(capability_id),
                "runner_node_id": str(runner_node_id),
            },
        ).fetchone()
    except pg_errors.ForeignKeyViolation:
        return None
    except pg_errors.CheckViolation as exc:
        # 대표적으로 ck_gate_run_contract_needs_sample — ungated 능력에 계약 샘플이 없다.
        name = getattr(exc.diag, "constraint_name", "") or ""
        if "needs_preprocess" in name:
            raise ValueError(
                "계약 게이트런을 시작할 수 없다: 이 능력이 전처리를 선언하지 않았다 "
                f"(input_schema.preprocess) — {name}"
            ) from exc
        raise ValueError(
            "계약 게이트런을 시작할 수 없다: 이 능력에 검증 샘플이 없다 "
            f"(POST /v1/capabilities/{{id}}/sample) — {name}"
        ) from exc
    return dict(row) if row else None


def _load_cap_metrics(conn: psycopg.Connection, gate_run_id: uuid.UUID) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT c.golden_metrics, c.golden_set_size, c.golden_set_sha256 AS capability_sha256,
               gr.golden_set_sha256 AS gate_run_sha256,
               gr.kind,
               -- 계약 게이트런의 필수 검사 집합이 arch 로 갈린다 (Decision 2-C · C2).
               a.arch AS agent_arch
          FROM gate_run gr
          JOIN capability c ON c.id = gr.capability_id
          JOIN agent a ON a.id = gr.agent_id
         WHERE gr.id = %s
        """,
        (str(gate_run_id),),
    ).fetchone()
    if row is None:
        raise ValueError("gate-run not found")
    return dict(row)


def assert_golden_set_sha256(
    *,
    dummy: bool,
    provided: str | None,
    expected: str,
) -> None:
    """S3: 채점에 쓴 골든셋 해시가 gate_run 스냅샷과 다르면 거부."""
    if provided is None:
        if not dummy:
            raise ValueError(
                "real gate requires golden_set_sha256 matching the gate_run snapshot"
            )
        return
    if provided != expected:
        raise ValueError(
            f"golden_set_sha256 mismatch: provided={provided} expected={expected}"
        )


def assert_real_finish(
    *,
    status: str,
    dummy: bool,
    golden_score: float | None,
    cases_total: int | None,
    cases_passed: int | None,
    macro_f1: float | None,
    invalid_rate: float | None,
    min_per_class_recall: float | None,
    cap: dict[str, Any],
) -> None:
    """dummy=false PASSED는 골든 지표를 충족해야 한다. dummy plumbing과 섞지 않는다."""
    if dummy:
        return
    if cases_total is None or cases_passed is None or golden_score is None:
        raise ValueError("real gate requires golden_score, cases_total, cases_passed")
    if cases_total != cap["golden_set_size"]:
        raise ValueError(
            f"cases_total {cases_total} != golden_set_size {cap['golden_set_size']}"
        )
    expected_acc = cases_passed / cases_total if cases_total else 0.0
    if abs(expected_acc - float(golden_score)) > 1e-6:
        raise ValueError("golden_score must equal cases_passed / cases_total")
    if status != "PASSED":
        return
    if macro_f1 is None or invalid_rate is None:
        raise ValueError("real PASSED requires macro_f1 and invalid_rate")
    metrics = cap["golden_metrics"]
    if isinstance(metrics, str):
        metrics = json.loads(metrics)
    min_acc = float(metrics["min_accuracy"])
    min_f1 = float(metrics["min_macro_f1"])
    max_inv = float(metrics["max_invalid_rate"])
    if golden_score < min_acc or macro_f1 < min_f1 or invalid_rate > max_inv:
        raise ValueError(
            "real PASSED rejected: "
            f"acc={golden_score:.4f} f1={macro_f1:.4f} inv={invalid_rate:.4f} "
            f"need acc>={min_acc} f1>={min_f1} inv<={max_inv}"
        )
    # 계약이 선언했으면 증명 없이 PASSED 를 받지 않는다.
    # 이게 없으면 클래스를 통째로 버린 모델도 통과한다 (m=8 -> acc 0.80 / f1 0.711).
    min_recall_req = metrics.get("min_per_class_recall")
    if min_recall_req is not None:
        if min_per_class_recall is None:
            raise ValueError(
                "real PASSED requires min_per_class_recall "
                f"(capability declares >= {min_recall_req})"
            )
        if float(min_per_class_recall) < float(min_recall_req):
            raise ValueError(
                "real PASSED rejected: "
                f"min_per_class_recall={float(min_per_class_recall):.4f} "
                f"< {float(min_recall_req)}"
            )


def assert_contract_finish(
    *,
    status: str,
    golden_score: float | None,
    cases_total: int | None,
    cases_passed: int | None,
    contract_checks: dict[str, Any] | None,
    arch: str | None = None,
) -> None:
    """계약 게이트런은 **채점하지 않는다.** 대신 러너가 무엇을 확인했는지를 요구한다.

    골든 통계는 애초에 오면 안 된다 — `ck_gate_run_contract_no_golden_stats` 가 DB 에서도
    막지만, 여기서 먼저 거절해야 「점수를 보냈는데 조용히 사라졌다」가 안 된다.

    요구 집합은 `arch` 가 참조 구현인지에 따라 갈린다 (`required_contract_checks`).
    러너가 **더** 보내는 것은 막지 않는다 — 증적이 늘어나는 것은 손해가 아니다.
    """
    given = [
        n for n, v in (
            ("golden_score", golden_score),
            ("cases_total", cases_total),
            ("cases_passed", cases_passed),
        ) if v is not None
    ]
    if given:
        raise ValueError(
            f"contract gate takes no golden stats (got {', '.join(given)})"
        )
    if status != "PASSED":
        return
    required = required_contract_checks(arch)
    if not contract_checks:
        raise ValueError(
            "contract PASSED requires contract_checks "
            f"({', '.join(required)})"
        )
    missing = [k for k in required if k not in contract_checks]
    if missing:
        raise ValueError(f"contract_checks missing: {', '.join(missing)}")
    failed = [k for k in required if contract_checks[k] is not True]
    if failed:
        raise ValueError(f"contract check not satisfied: {', '.join(failed)}")


def finish_gate_run(
    conn: psycopg.Connection,
    *,
    gate_run_id: uuid.UUID,
    status: str,
    golden_score: float | None,
    cases_total: int | None,
    cases_passed: int | None,
    dummy: bool,
    note: str | None,
    macro_f1: float | None = None,
    invalid_rate: float | None = None,
    min_per_class_recall: float | None = None,
    golden_set_sha256: str | None = None,
    contract_checks: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if status not in ("PASSED", "FAILED", "ERROR"):
        raise ValueError("status must be PASSED, FAILED, or ERROR")

    cap = _load_cap_metrics(conn, gate_run_id)
    expected_sha = str(cap["gate_run_sha256"])
    is_contract = cap["kind"] == "contract"

    if is_contract:
        # 계약 게이트런에는 골든셋이 없다. sha 는 센티널이고 대조할 것이 없다.
        assert_contract_finish(
            status=status,
            golden_score=golden_score,
            cases_total=cases_total,
            cases_passed=cases_passed,
            contract_checks=contract_checks,
            arch=cap.get("agent_arch"),
        )
    else:
        if contract_checks is not None:
            raise ValueError("golden gate takes no contract_checks")
        assert_golden_set_sha256(
            dummy=dummy, provided=golden_set_sha256, expected=expected_sha
        )
        assert_real_finish(
            status=status,
            dummy=dummy,
            golden_score=golden_score,
            cases_total=cases_total,
            cases_passed=cases_passed,
            macro_f1=macro_f1,
            invalid_rate=invalid_rate,
            min_per_class_recall=min_per_class_recall,
            cap=cap,
        )

    summary: dict[str, Any]
    if is_contract:
        summary = {
            "dummy": dummy,
            "scored_by": "contract-v1",
            "contract_checks": contract_checks or {},
        }
    else:
        summary = {
            "dummy": dummy,
            "scored_by": "plumbing-only" if dummy else "golden-set-v1",
            "golden_set_sha256": expected_sha,
        }
        if golden_set_sha256 is not None:
            summary["golden_set_sha256_provided"] = golden_set_sha256
        if macro_f1 is not None:
            summary["macro_f1"] = macro_f1
        if invalid_rate is not None:
            summary["invalid_rate"] = invalid_rate
    if note:
        summary["note"] = note

    row = conn.execute(
        FINISH_SQL,
        {
            "gate_run_id": str(gate_run_id),
            "status": status,
            "golden_score": golden_score,
            "cases_total": cases_total,
            "cases_passed": cases_passed,
            "result_summary": json.dumps(summary),
        },
    ).fetchone()
    if row is None:
        return None

    params = {"gate_run_id": str(gate_run_id), "golden_score": golden_score}
    if status == "PASSED":
        conn.execute(MINT_PASSED_SQL, params)
        conn.execute(UPSERT_AC_PASSED_SQL, params)
        conn.execute(MINT_ACP_SQL, params)
    elif status == "FAILED":
        conn.execute(UPSERT_AC_FAILED_SQL, params)

    out = dict(row)
    out["chain_minted"] = status == "PASSED"
    return out


class RevokeRefused(Exception):
    """폐기 근거가 없다. 현재 골든셋에서 떨어진 gate_run 이 있어야 한다."""


def revoke_capability(
    conn: psycopg.Connection,
    *,
    agent_id: uuid.UUID,
    capability_id: uuid.UUID,
    reason: str,
) -> dict[str, Any] | None:
    """능력 증서를 폐기한다 — 행은 남기고 라우팅만 끊는다.

    삭제하지 않는 이유: `assignment` 가 `agent_capability_passed` 를 FK 로 참조한다.
    한 번이라도 실행된 Agent 의 증서는 지울 수 없다. 실행을 인가한 증서를 지우면
    그 실행의 증적이 끊긴다 (D15).

    근거 없이는 폐기하지 않는다 — **현재** 골든셋에서 FAILED 인 gate_run 이 있어야 한다.
    되돌리려면 다시 게이트를 통과시킨다 (MINT_ACP_SQL 이 복권한다).
    """
    if not reason or not reason.strip():
        raise ValueError("reason is required")

    evidence = conn.execute(
        REVOKE_EVIDENCE_SQL,
        {"agent_id": str(agent_id), "capability_id": str(capability_id)},
    ).fetchone()
    if evidence is None:
        raise RevokeRefused(
            "현재 골든셋에서 FAILED 인 gate_run 이 없다 — 근거 없는 폐기는 하지 않는다"
        )

    row = conn.execute(
        REVOKE_SQL,
        {
            "agent_id": str(agent_id),
            "capability_id": str(capability_id),
            "reason": reason.strip(),
            "gate_run_id": str(evidence["id"]),
        },
    ).fetchone()
    if row is None:
        return None  # 증서가 없거나 이미 폐기됨

    out = dict(row)
    out["evidence_gate_run_id"] = evidence["id"]
    out["evidence_score"] = evidence["golden_score"]
    try:
        conn.execute(
            REVOKE_AUDIT_SQL,
            {
                "payload": json.dumps(
                    {
                        "agent_id": str(agent_id),
                        "capability_id": str(capability_id),
                        "reason": reason.strip(),
                        "evidence_gate_run_id": str(evidence["id"]),
                    }
                )
            },
        )
    except pg_errors.Error:
        # 증적 보조 기록 실패가 폐기 자체를 뒤집지 않는다 (complete.py 와 같은 규약).
        pass
    return out


def get_gate_run(conn: psycopg.Connection, gate_run_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, agent_id, capability_id, runner_node_id, runner_is_gate_runner, "
        "status, golden_set_sha256, golden_score, cases_total, cases_passed, "
        "kind, capability_quality_profile, sample_input_id, capability_preprocess, "
        "result_summary, created_at, finished_at "
        "FROM gate_run WHERE id = %s",
        (str(gate_run_id),),
    ).fetchone()
    return dict(row) if row else None


def list_agent_capabilities(conn: psycopg.Connection, agent_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT agent_id, capability_id, gate_status, golden_score, gate_run_id, gated_at "
        "FROM agent_capability WHERE agent_id = %s",
        (str(agent_id),),
    ).fetchall()
    return [dict(r) for r in rows]
