#!/usr/bin/env bash
# 골든셋 교체 후 재게이트 (SD-013).
#
# 무엇
#   `provenance_drift` 가 잡은 Agent — 구 골든셋에서 PASS 를 받고 지금도 라우팅되는 것들 —
#   을 **현재** 골든셋으로 다시 게이트한다. 새 gate_run 이 현재 sha 를 스냅샷하고,
#   `agent_capability.gate_run_id` 가 그 새 run 으로 옮겨간다 (gate.py UPSERT_AC_PASSED).
#
# 왜 proof_ab.sh 로는 안 되나
#   proof_ab.sh 는 실행할 때마다 **새 Agent 를 등록**한다. 기존 증서는 그대로 남는다.
#   재게이트는 기존 agent_id 를 그대로 쓰면서 게이트만 다시 도는 것이다.
#
# 사전 조건
#   docker compose up -d · Node 에 해당 Agent 의 weights_sha256 파일이 실제로 있을 것
#
#   scripts/regate.sh --dry-run   # 대상만 보여준다
#   scripts/regate.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
core="${CORE_URL:-http://127.0.0.1:8000}"
node="${NODE_URL:-http://127.0.0.1:8001}"
capId="${CAPABILITY_ID:-00000000-0000-4000-8000-000000000010}"
runnerId="${RUNNER_NODE_ID:-00000000-0000-4000-8000-000000000030}"
dry_run=false
[[ "${1:-}" == "--dry-run" ]] && dry_run=true

curl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }
nh="$(curl -sf "$node/health")" || { echo "Node 응답 없음: $node" >&2; exit 1; }

# 대상: 라우팅 가능한 증서 중, 근거 gate_run 의 sha 가 현재 capability sha 와 다른 것
targets="$(docker compose --project-directory "$root" exec -T postgres \
  psql -U capnet -d capnet -tAc "
SELECT a.id||'|'||a.name||'|'||a.weights_sha256
  FROM agent_capability ac
  JOIN agent_capability_passed acp
    ON acp.agent_id = ac.agent_id AND acp.capability_id = ac.capability_id
  JOIN agent a       ON a.id = ac.agent_id
  JOIN gate_run gr   ON gr.id = ac.gate_run_id
  JOIN capability c  ON c.id = ac.capability_id
 WHERE ac.capability_id = '$capId'
   AND gr.golden_set_sha256 IS DISTINCT FROM c.golden_set_sha256
 ORDER BY a.name, a.id")"

if [[ -z "${targets//[[:space:]]/}" ]]; then
  echo "재게이트 대상 없음 — 모든 증서가 현재 골든셋 기준이다."
  exit 0
fi

total="$(printf '%s\n' "$targets" | grep -c . || true)"
echo "재게이트 대상 $total 건 (현재 골든셋 기준이 아닌 증서)"

# weights_sha256 → Node 안의 파일 경로
weights_path_for() {
  printf '%s' "$nh" | python3 -c '
import json,sys
want=sys.argv[1]
h=json.load(sys.stdin)
for w in h.get("weights", []):
    if w["sha256"] == want and not w["placeholder"]:
        print(w["path"]); break
' "$1"
}

ok=0; failed=0; skipped=0
# 루프 입력은 fd 3 으로 읽는다. `docker compose exec -T` 가 stdin 을 먹어서
# 기본 fd 로 돌리면 첫 건만 처리하고 조용히 끝난다.
while IFS='|' read -r agentId name wsha <&3; do
  [[ -z "$agentId" ]] && continue
  wpath="$(weights_path_for "$wsha")"
  if [[ -z "$wpath" ]]; then
    echo "  건너뜀 $name ($(printf '%.12s' "$wsha")…) — Node 에 해당 가중치가 없다"
    skipped=$((skipped+1)); continue
  fi
  if $dry_run; then
    echo "  [dry-run] $name ← $(basename "$wpath")"
    continue
  fi

  # 1) 새 gate_run — capability 의 **현재** sha 를 스냅샷한다 (gate.py START_SQL)
  gr="$(curl -sf -X POST "$core/v1/internal/gate-runs" -H 'content-type: application/json' \
      -d "{\"agent_id\":\"$agentId\",\"capability_id\":\"$capId\",\"runner_node_id\":\"$runnerId\"}")"
  grId="$(printf '%s' "$gr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

  # 2) team gate-runner 에서 실채점 (절대규칙 8)
  set +e
  raw="$(docker compose --project-directory "$root" exec -T node-m-team \
    python -m app.score_gate --mode scratch --weights "$wpath" \
    --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02 2>/dev/null)"
  rc=$?
  set -e
  if [[ "$rc" -ne 0 && "$rc" -ne 2 ]]; then
    echo "  실패 $name — score_gate rc=$rc"
    failed=$((failed+1)); continue
  fi

  # 3) finish — golden_set_sha256 은 새 gate_run 스냅샷을 그대로 되돌려준다
  finish="$(printf '%s' "$raw" | python3 -c '
import json,sys
s=json.load(sys.stdin); gr=json.loads(sys.argv[1])
print(json.dumps({
  "status": s["status"], "dummy": False,
  "golden_score": s["golden_score"], "cases_total": s["cases_total"],
  "cases_passed": s["cases_passed"], "macro_f1": s["macro_f1"],
  "invalid_rate": s["invalid_rate"],
  "min_per_class_recall": s.get("min_per_class_recall"),
  "note": sys.argv[2],
  "golden_set_sha256": gr["golden_set_sha256"],
}))' "$gr" "regate after golden-set change (SD-013)")"
  curl -sf -X POST "$core/v1/internal/gate-runs/$grId/finish" \
    -H 'content-type: application/json' -d "$finish" >/dev/null

  status="$(printf '%s' "$raw" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  acc="$(printf '%s' "$raw" | python3 -c 'import json,sys; print("%.4f" % json.load(sys.stdin)["golden_score"])')"
  if [[ "$status" == "PASSED" ]]; then
    echo "  PASSED $name  acc=$acc"
    ok=$((ok+1))
  else
    # 주의: FAILED 는 기존 PASSED 증서를 **끌어내리지 못한다**
    # (gate.py UPSERT_AC_FAILED_SQL 의 WHERE gate_status <> 'PASSED').
    # 폐기는 사람이 정한다 — 절대규칙 8 · D15.
    echo "  FAILED $name  acc=$acc  ← 기존 PASSED 증서는 그대로 남는다. 폐기 결정 필요"
    failed=$((failed+1))
  fi
done 3<<< "$targets"

$dry_run && exit 0

echo
echo "재게이트 완료 — PASSED $ok · FAILED $failed · 건너뜀 $skipped"
echo "확인: SELECT * FROM provenance_drift_summary;"
