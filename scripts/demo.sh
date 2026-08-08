#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
core="http://127.0.0.1:8000"
node="http://127.0.0.1:8001"
capId="00000000-0000-4000-8000-000000000010"
runnerId="00000000-0000-4000-8000-000000000030"

curl -sf "$core/health" >/dev/null
nh="$(curl -sf "$node/health")"
sha="$(printf '%s' "$nh" | python3 -c 'import json,sys
h=json.load(sys.stdin)
hits=[w for w in h.get("weights",[]) if "eurosat_scratch" in w["path"] and not w["placeholder"]]
assert hits, "scratch weights missing"
print(hits[0]["sha256"])')"

ver="0.1.0-scratch-$(date +%Y%m%d%H%M%S)"
agent="$(curl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' \
  -d "{\"name\":\"eurosat-scratch\",\"version\":\"$ver\",\"manifest_hash\":\"eurosat-scratch-tiny\",\"weights_uri\":\"file:///weights/eurosat_scratch.safetensors\",\"weights_sha256\":\"$sha\"}")"
agentId="$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

set +e
raw="$(docker compose --project-directory "$root" exec -T node-m-team python -m app.score_gate --mode scratch --weights /weights/eurosat_scratch.safetensors --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02)"
rc=$?
set -e
if [[ "$rc" -ne 0 && "$rc" -ne 2 ]]; then
  echo "score_gate failed rc=$rc" >&2
  exit 1
fi
printf '%s\n' "$raw" | python3 -c 'import json,sys; s=json.load(sys.stdin); print("score status=%s acc=%.4f f1=%.4f" % (s["status"], s["golden_score"], s["macro_f1"]))'
status="$(printf '%s' "$raw" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"

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
  "invalid_rate": s["invalid_rate"], "note": "golden-set-v1 scratch TinyEuroSAT",
  "golden_set_sha256": gr["golden_set_sha256"],
}))' "$gr")"
fin="$(curl -sf -X POST "$core/v1/internal/gate-runs/$grId/finish" -H 'content-type: application/json' -d "$finish")"
printf '%s' "$fin" | python3 -c 'import json,sys
fin=json.load(sys.stdin)
summary=fin.get("result_summary") or {}
if isinstance(summary,str):
    summary=json.loads(summary)
if summary.get("dummy"):
    raise SystemExit("finish marked dummy")'

if [[ "$status" != "PASSED" ]]; then
  echo "REAL GATE FAILED (honest). Task not started."
  exit 2
fi

curl -sf -X POST "$core/v1/agents/$agentId/bindings" -H 'content-type: application/json' \
  -d "{\"node_id\":\"$runnerId\",\"weights_sha256_seen\":\"$sha\"}" >/dev/null

task="$(curl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"eurosat-rgb\",\"caseId\":\"ic1-0001\",\"requestedAgentId\":\"$agentId\"}")"
taskId="$(printf '%s' "$task" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
claim="$(curl -sf -X POST "$core/v1/internal/claim" -H 'content-type: application/json' \
  -d "{\"task_id\":\"$taskId\"}")"
execBody="$(printf '%s' "$claim" | python3 -c 'import json,sys
c=json.load(sys.stdin)
print(json.dumps({"id":c["id"],"weights_sha256":c["weights_sha256"],"input_ref":c["input_ref"]}))')"
out="$(curl -sf -X POST "$node/v1/execute" -H 'content-type: application/json' -d "$execBody")"
printf '%s' "$out" | python3 -c 'import json,sys
e=json.load(sys.stdin)
if e.get("dummy"):
    raise SystemExit("execute was dummy")
print("demo OK — real gate PASSED + scratch task COMPLETED")
print("label=", e.get("label"))'
