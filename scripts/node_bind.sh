#!/usr/bin/env bash
# Agent 를 게이트에 통과시키고 Node 에 바인딩한다 (온보딩 2단계)
#
#   scripts/node_bind.sh --node <uuid> --weights eurosat_scratch.safetensors
#   scripts/node_bind.sh --node <uuid> --weights eurosat_scratch_b.safetensors --name my-agent
#   scripts/node_bind.sh --node <uuid> --weights w.safetensors --arch TinyEuroSATB   # meta 가 없을 때
#
# 왜 필요한가
#   Node 를 등록하고 증서를 줘도 **일이 가지 않는다.** 배정에는 사슬이 다 서야 한다:
#     Agent 등록 → 실게이트 PASSED → 증서(agent_capability_passed) → Node 바인딩(agent_node_ready)
#   이 스크립트가 그 사슬을 세운다.
#
# 절대규칙 8
#   게이트는 **team gate-runner 에서만** 돈다. 대상 Node 가 무엇이든 채점은 러너가 한다.
#   대상 Node 는 「그 가중치를 들고 있다」는 바인딩만 받는다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
# 관리 API 인증 헤더(CAPNET_API_KEY)를 한 곳에서 붙인다.
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
runner="${RUNNER_NODE_ID:-00000000-0000-4000-8000-000000000030}"
runner_svc="${RUNNER_SERVICE:-node-m-team}"
cap="${CAPABILITY_ID:-00000000-0000-4000-8000-000000000010}"

node=""; weights=""; name=""; arch=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --node)     node="$2"; shift 2 ;;
    --weights)  weights="$2"; shift 2 ;;
    --name)     name="$2"; shift 2 ;;
    --arch)     arch="$2"; shift 2 ;;
    --capability-id) cap="$2"; shift 2 ;;
    *) echo "모르는 인자: $1" >&2; exit 1 ;;
  esac
done
[[ -n "$node" && -n "$weights" ]] || {
  echo "사용: scripts/node_bind.sh --node <uuid> --weights <file.safetensors> [--name N] [--arch A]" >&2; exit 1; }
name="${name:-agent-${weights%.safetensors}}"
stamp="$(date +%Y%m%d%H%M%S)"

curl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) 러너가 들고 있는 가중치 해시 확인 =="
sha=$(docker compose --project-directory "$root" exec -T "$runner_svc" \
  python -c "
import hashlib,sys
h=hashlib.sha256()
with open('/weights/$weights','rb') as f:
    for b in iter(lambda: f.read(1<<20), b''): h.update(b)
print(h.hexdigest())" 2>/dev/null) || {
  echo "러너에 /weights/$weights 가 없다" >&2; exit 1; }
echo "  $weights → ${sha:0:16}…"

# arch 는 등록 필수다 (G5). 근거는 학습 기록(`<weights>.meta.json`) — 추측이 아니다.
# --arch 로 덮어쓸 수 있다 (meta 가 없는 가중치).
if [[ -z "${arch:-}" ]]; then
  arch=$(docker compose --project-directory "$root" exec -T "$runner_svc" \
    python -c "from app.infer import _arch_for_weights; print(_arch_for_weights('/weights/$weights'))" 2>/dev/null | tr -d '\r')
fi
[[ -n "$arch" ]] || { echo "arch 를 정할 수 없다 — --arch 로 준다" >&2; exit 1; }
echo "  arch=$arch"

echo "== 2) Agent 등록 =="
agent=$(ccurl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' \
  -d "{\"name\":\"$name\",\"version\":\"0.1.0-$stamp\",\"manifest_hash\":\"$name-manifest\",\"weights_uri\":\"file:///weights/$weights\",\"weights_sha256\":\"$sha\",\"arch\":\"$arch\"}")
agent_id=$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "  agent=$agent_id"

echo "== 3) 실게이트 (team gate-runner · 절대규칙 8) =="
set +e
raw=$(docker compose --project-directory "$root" exec -T "$runner_svc" \
  python -m app.score_gate --mode scratch --weights "/weights/$weights" \
  --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02 2>/dev/null)
rc=$?
set -e
[[ "$rc" -eq 0 || "$rc" -eq 2 ]] || { echo "채점 실패 rc=$rc" >&2; exit 1; }
status=$(printf '%s' "$raw" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
printf '%s' "$raw" | python3 -c 'import json,sys; s=json.load(sys.stdin); print("  status=%s acc=%.4f f1=%.4f" % (s["status"],s["golden_score"],s["macro_f1"]))'

gr=$(ccurl -sf -X POST "$core/v1/internal/gate-runs" -H 'content-type: application/json' \
  -d "{\"agent_id\":\"$agent_id\",\"capability_id\":\"$cap\",\"runner_node_id\":\"$runner\"}")
gr_id=$(printf '%s' "$gr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
finish=$(printf '%s' "$raw" | python3 -c '
import json,sys
s=json.load(sys.stdin); gr=json.loads(sys.argv[1])
print(json.dumps({"status":s["status"],"dummy":False,"golden_score":s["golden_score"],
 "cases_total":s["cases_total"],"cases_passed":s["cases_passed"],"macro_f1":s["macro_f1"],
 "invalid_rate":s["invalid_rate"],"min_per_class_recall":s.get("min_per_class_recall"),
 "note":sys.argv[2],"golden_set_sha256":gr["golden_set_sha256"]}))' "$gr" "node_bind $name")
ccurl -sf -X POST "$core/v1/internal/gate-runs/$gr_id/finish" \
  -H 'content-type: application/json' -d "$finish" >/dev/null

if [[ "$status" != "PASSED" ]]; then
  echo "  게이트 미통과 — 바인딩하지 않는다 (미통과 Agent 에는 배정이 안 간다)" >&2
  exit 2
fi

echo "== 4) Node 바인딩 =="
ccurl -sf -X POST "$core/v1/agents/$agent_id/bindings" -H 'content-type: application/json' \
  -d "{\"node_id\":\"$node\",\"weights_sha256_seen\":\"$sha\"}" >/dev/null
echo "  $agent_id → node $node"

echo
echo "== 확인 =="
echo "  scripts/call.sh ic1-0001        # Agent 지정 없이 능력만으로 호출"
echo "  curl -s $core/v1/nodes-liveness"   # 조회 경로라 키 없이 된다
