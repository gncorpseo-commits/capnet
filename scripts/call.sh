#!/usr/bin/env bash
# 능력 호출 — 제품 경로 (product-distribution §4)
#
#   scripts/call.sh ic1-0001
#   scripts/call.sh ic1-0007 --capability image.classify --version 1
#   scripts/call.sh ic1-0003 --agent <uuid>      # 증명 모드 (UC-7) — 보통은 쓰지 않는다
#
# 무엇이 다른가
#   `demo.sh` 는 Agent 를 만들고 **지정해서** 부른다 (증명용).
#   이 스크립트는 **Capability 만 말한다** — 「모델 이름이 아니라 능력으로 요청한다」가
#   제품의 주장이고(product-distribution §4), 그 경로가 실제로 도는지 여기서 본다.
#
#   사용자는 어느 기기가 실행할지, 어떤 Agent 가 붙을지 모른다. Core 가 정한다.
set -euo pipefail
# 관리 API 인증 헤더(CAPNET_API_KEY)를 한 곳에서 붙인다.
source "$(cd "$(dirname "$0")" && pwd)/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"

case_id="${1:-}"; shift || true
capability="image.classify"; version="1"; dataset="eurosat-rgb"; agent=""; timeout_s=90

[[ -n "$case_id" ]] || { echo "사용: scripts/call.sh <caseId> [--capability C] [--version N] [--agent UUID]" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --capability) capability="$2"; shift 2 ;;
    --version)    version="$2"; shift 2 ;;
    --dataset)    dataset="$2"; shift 2 ;;
    --agent)      agent="$2"; shift 2 ;;
    --timeout)    timeout_s="$2"; shift 2 ;;
    *) echo "모르는 인자: $1" >&2; exit 1 ;;
  esac
done

curl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

body="{\"datasetId\":\"$dataset\",\"caseId\":\"$case_id\",\"capability_code\":\"$capability\",\"capability_version\":$version"
[[ -n "$agent" ]] && body="$body,\"requestedAgentId\":\"$agent\""
body="$body}"

echo "요청: $capability@$version · case=$case_id" >&2
[[ -n "$agent" ]] && echo "  (증명 모드 — Agent 지정)" >&2

task=$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' -d "$body") || {
  echo "요청 거절 — allowlist·계약·신뢰 도메인을 본다" >&2; exit 1; }
task_id=$(printf '%s' "$task" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')

deadline=$(( $(date +%s) + timeout_s ))
while :; do
  tr=$(ccurl -sf "$core/v1/tasks/$task_id")
  st=$(printf '%s' "$tr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
  [[ "$st" == "COMPLETED" || "$st" == "FAILED" ]] && break
  [[ $(date +%s) -ge $deadline ]] && { echo "시간 초과 — status=$st (task=$task_id)" >&2; exit 1; }
  sleep 1
done

printf '%s' "$tr" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if d["status"] != "COMPLETED":
    print("실패 status=%s" % d["status"], file=sys.stderr); raise SystemExit(1)
res = json.loads(d["result_ref"]) if isinstance(d["result_ref"], str) else (d["result_ref"] or {})
a = d.get("assignment") or {}
print("label      = %s" % res.get("label"))
conf = res.get("confidence")
if conf is not None:
    print("confidence = %.4f" % conf)
# 증적 — 누가·무엇으로·어디서 실행했는지. 제품이 보장하는 것 (product-distribution §2)
print("증적       node=%s agent=%s" % (a.get("node_id"), a.get("agent_id")))
print("           weights_sha256=%s" % (res.get("weights_sha256") or "")[:16])
if res.get("dummy"):
    print("!! dummy=true — 실제 추론이 아니다. placeholder 가중치로 실행됐다", file=sys.stderr)
    raise SystemExit(2)
'
