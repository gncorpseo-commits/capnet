#!/usr/bin/env bash
# UC-7 증명 모드 교차 실행 — Agent A·B를 각각 실게이트로 통과시킨 뒤,
# 동일 caseId를 requestedAgentId로 교차 할당해 게이트 사슬 위에서 비교한다.
#
# 사슬 밖 오프라인 비교(scripts/compare_ab)와 다르다. 여기는 전부 DB를 거친다:
#   gate_run(dummy=false) → gate_run_passed → agent_capability_passed
#   → agent_node_ready → assignment(INSERT … SELECT) → 결과
#
# 사전 조건: docker compose up -d · apps/node/weights/ 에 A·B safetensors
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
core="http://127.0.0.1:8000"
node="http://127.0.0.1:8001"
capId="00000000-0000-4000-8000-000000000010"
runnerId="00000000-0000-4000-8000-000000000030"
caseId="${CASE_ID:-ic1-0001}"
stamp="$(date +%Y%m%d%H%M%S)"

jq_py() { python3 -c "$1"; }

curl -sf "$core/health" >/dev/null
nh="$(curl -sf "$node/health")"

# 가중치 파일명 → sha256 (Node가 실제로 들고 있는 것만 인정)
sha_of() {
  printf '%s' "$nh" | python3 -c '
import json,sys
want=sys.argv[1]
h=json.load(sys.stdin)
hits=[w for w in h.get("weights",[]) if w["path"].endswith(want) and not w["placeholder"]]
if not hits:
    raise SystemExit("weights missing on node: "+want)
print(hits[0]["sha256"])' "$1"
}

# 이름·가중치로 Agent를 등록하고 실게이트를 통과시킨다. stdout = agentId
gate_agent() {
  local label="$1" wfile="$2" sha="$3"
  local agent agentId raw rc status gr grId finish fin

  agent="$(curl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' \
    -d "{\"name\":\"$label\",\"version\":\"0.1.0-$stamp\",\"manifest_hash\":\"$label-manifest\",\"weights_uri\":\"file:///weights/$wfile\",\"weights_sha256\":\"$sha\"}")"
  agentId="$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

  set +e
  raw="$(docker compose --project-directory "$root" exec -T node-m-team \
    python -m app.score_gate --mode scratch --weights "/weights/$wfile" \
    --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02)"
  rc=$?
  set -e
  if [[ "$rc" -ne 0 && "$rc" -ne 2 ]]; then
    echo "score_gate failed rc=$rc ($label)" >&2
    return 1
  fi
  status="$(printf '%s' "$raw" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  printf '%s' "$raw" | python3 -c 'import json,sys
s=json.load(sys.stdin)
print("  %-22s status=%s acc=%.4f f1=%.4f" % (sys.argv[1], s["status"], s["golden_score"], s["macro_f1"]), file=sys.stderr)' "$label"

  gr="$(curl -sf -X POST "$core/v1/internal/gate-runs" -H 'content-type: application/json' \
    -d "{\"agent_id\":\"$agentId\",\"capability_id\":\"$capId\",\"runner_node_id\":\"$runnerId\"}")"
  grId="$(printf '%s' "$gr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

  finish="$(printf '%s' "$raw" | python3 -c 'import json,sys
s=json.load(sys.stdin)
gr=json.loads(sys.argv[1])
print(json.dumps({
  "status": s["status"], "dummy": False,
  "golden_score": s["golden_score"], "cases_total": s["cases_total"],
  "cases_passed": s["cases_passed"], "macro_f1": s["macro_f1"],
  "invalid_rate": s["invalid_rate"], "note": sys.argv[2],
  "golden_set_sha256": gr["golden_set_sha256"],
}))' "$gr" "golden-set-v1 scratch $label")"
  curl -sf -X POST "$core/v1/internal/gate-runs/$grId/finish" \
    -H 'content-type: application/json' -d "$finish" >/dev/null

  if [[ "$status" != "PASSED" ]]; then
    echo "  $label: 실게이트 FAILED — 교차 실행 대상에서 제외 (정직)" >&2
    return 2
  fi

  curl -sf -X POST "$core/v1/agents/$agentId/bindings" -H 'content-type: application/json' \
    -d "{\"node_id\":\"$runnerId\",\"weights_sha256_seen\":\"$sha\"}" >/dev/null

  printf '%s' "$agentId"
}

# 지정 Agent로 동일 case를 실행하고 label을 돌려준다.
# Core 하고만 말한다 — 배정은 Core 워커가, 실행은 Node가 자기 몫을 가져가서 한다.
run_case() {
  local agentId="$1" task taskId tr st
  task="$(curl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
    -d "{\"datasetId\":\"eurosat-rgb\",\"caseId\":\"$caseId\",\"requestedAgentId\":\"$agentId\"}")"
  taskId="$(printf '%s' "$task" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

  for _ in $(seq 1 60); do
    tr="$(curl -sf "$core/v1/tasks/$taskId")"
    st="$(printf '%s' "$tr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
    [[ "$st" == "COMPLETED" || "$st" == "FAILED" ]] && break
    sleep 1
  done

  printf '%s' "$tr" | python3 -c '
import json,sys
d=json.load(sys.stdin)
if d["status"] != "COMPLETED":
    raise SystemExit("task not completed: %s" % d["status"])
a=d["assignment"]
if str(a["agent_id"]) != sys.argv[1]:
    raise SystemExit("requestedAgentId 무시됨: 요청=%s 할당=%s" % (sys.argv[1], a["agent_id"]))
res=json.loads(d["result_ref"]) if isinstance(d["result_ref"],str) else (d["result_ref"] or {})
if res.get("dummy"):
    raise SystemExit("execute was dummy")
print(res.get("label"))' "$agentId"
}

shaA="$(sha_of eurosat_scratch.safetensors)"
shaB="$(sha_of eurosat_scratch_b.safetensors)"
if [[ "$shaA" == "$shaB" ]]; then
  echo "A와 B의 weights_sha256이 같다 — 교체 비교가 무의미하다" >&2
  exit 1
fi

echo "== 실게이트 (team gate-runner) =="
agentA="$(gate_agent proof-agent-a eurosat_scratch.safetensors "$shaA")"
agentB="$(gate_agent proof-agent-b eurosat_scratch_b.safetensors "$shaB")"

echo "== 교차 할당 (동일 case=$caseId) =="
labelA="$(run_case "$agentA")"
labelB="$(run_case "$agentB")"
echo "  A($agentA) → $labelA"
echo "  B($agentB) → $labelB"

if [[ "$labelA" == "$labelB" ]]; then
  echo "AGREE — 사슬 위에서 Agent를 교체해도 같은 라벨"
else
  echo "DISAGREE — 같은 계약을 통과했으나 라벨이 다름 (case 1건은 판정 근거가 아니다)"
fi

cat <<'NOTE'

주의: 이 스크립트는 case 1건의 교차 실행이다. §7.1-4(편차 < 0.05)의
통계 판정은 n>=300 골든셋에서 별도로 한다. 여기서 증명되는 것은
"게이트를 통과한 두 Agent가 사슬 위에서 교체 가능하다"는 배관 사실이다.
NOTE
