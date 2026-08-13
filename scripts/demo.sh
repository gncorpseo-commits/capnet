#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
# 관리 API 인증 헤더(CAPNET_API_KEY)를 한 곳에서 붙인다.
source "$root/scripts/lib/http.sh"
# 주소를 환경에서 받는다 — 격리 환경(clean_room.sh)에서 같은 스크립트를 그대로 돌리기 위해서다.
core="${CORE_URL:-http://127.0.0.1:8000}"
node="${NODE_URL:-http://127.0.0.1:8001}"
capId="00000000-0000-4000-8000-000000000010"
runnerId="00000000-0000-4000-8000-000000000030"

ccurl -sf "$core/health" >/dev/null
nh="$(ccurl -sf "$node/health")"
# sha 와 arch 를 **같은 증언**에서 뽑는다 — Node 가 들고 있는 파일과 그 학습 기록이다.
# arch 는 이제 등록 필수다 (G5): 없으면 Core 가 400 을 준다.
read -r sha arch <<< "$(printf '%s' "$nh" | python3 -c 'import json,sys
h=json.load(sys.stdin)
hits=[w for w in h.get("weights",[]) if "eurosat_scratch" in w["path"] and not w["placeholder"]]
assert hits, "scratch weights missing"
print(hits[0]["sha256"], hits[0].get("arch") or "")')"
[[ -n "$arch" ]] || { echo "Node 가 arch 를 모른다 — <weights>.meta.json 확인" >&2; exit 1; }

ver="0.1.0-scratch-$(date +%Y%m%d%H%M%S)"
agent="$(ccurl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' \
  -d "{\"name\":\"eurosat-scratch\",\"version\":\"$ver\",\"manifest_hash\":\"eurosat-scratch-tiny\",\"weights_uri\":\"file:///weights/eurosat_scratch.safetensors\",\"weights_sha256\":\"$sha\",\"arch\":\"$arch\"}")"
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

gr="$(ccurl -sf -X POST "$core/v1/internal/gate-runs" -H 'content-type: application/json' \
  -d "{\"agent_id\":\"$agentId\",\"capability_id\":\"$capId\",\"runner_node_id\":\"$runnerId\"}")"
grId="$(printf '%s' "$gr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

finish="$(printf '%s' "$raw" | python3 -c 'import json,sys
s=json.load(sys.stdin)
gr=json.loads(sys.argv[1])
print(json.dumps({
  "status": s["status"], "dummy": False,
  "golden_score": s["golden_score"], "cases_total": s["cases_total"],
  "cases_passed": s["cases_passed"], "macro_f1": s["macro_f1"],
  "invalid_rate": s["invalid_rate"], "min_per_class_recall": s.get("min_per_class_recall"), "note": "golden-set-v1 scratch TinyEuroSAT",
  "golden_set_sha256": gr["golden_set_sha256"],
}))' "$gr")"
fin="$(ccurl -sf -X POST "$core/v1/internal/gate-runs/$grId/finish" -H 'content-type: application/json' -d "$finish")"
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

ccurl -sf -X POST "$core/v1/agents/$agentId/bindings" -H 'content-type: application/json' \
  -d "{\"node_id\":\"$runnerId\",\"weights_sha256_seen\":\"$sha\"}" >/dev/null

task="$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"eurosat-rgb\",\"caseId\":\"ic1-0001\",\"requestedAgentId\":\"$agentId\"}")"
taskId="$(printf '%s' "$task" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

# 여기서부터는 Core 하고만 말한다.
# Core 워커가 배정하고, Node가 자기 몫을 가져가 실행하고, 결과가 Core로 돌아온다.
# 클라이언트는 Node 주소를 알 필요가 없다.
for _ in $(seq 1 60); do
  tr="$(ccurl -sf "$core/v1/tasks/$taskId")"
  st="$(printf '%s' "$tr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [[ "$st" == "COMPLETED" || "$st" == "FAILED" ]] && break
  sleep 1
done

printf '%s' "$tr" | python3 -c 'import json,sys
d=json.load(sys.stdin)
if d["status"] != "COMPLETED":
    raise SystemExit("task not completed: %s" % d["status"])
res=json.loads(d["result_ref"]) if isinstance(d["result_ref"],str) else (d["result_ref"] or {})
if res.get("dummy"):
    raise SystemExit("execute was dummy")
a=d["assignment"]
print("demo OK - real gate PASSED + scratch task COMPLETED (Core 중개)")
print("label=", res.get("label"))
print("증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))'
