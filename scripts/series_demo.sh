#!/usr/bin/env bash
# timeseries.forecast 종단 데모 (단계 6 ②) — 세 번째 모달리티 어휘(table)가 도는가
#
#   scripts/text_demo.sh
#
# 무엇을 보이나
#   1. arch 등록 (D-arch API)          — 허용 목록에 없으면 Agent 등록이 FK 로 막힌다
#   2. 능력 등록 (output_kind=structured · quality_profile=none)
#   3. 계약 샘플 부착 (Core 중개 · D8′) — 텍스트에는 로컬 골든셋 폴백이 없다
#   4. 계약 게이트 (team gate-runner)   — 벡터 **차원·원소 타입**을 대조 (D-out)
#   5. 작업 요청 → Core 배정 → 실행     — 사용자는 기기 주소를 모른다
#
# 무엇을 주장하지 않나
#   분류 성능. `timeseries.forecast` 는 `quality_profile='none'` 이라 골든셋도 채점도 없다.
#   이 스크립트는 **경로가 성립한다**만 보인다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
runner="${RUNNER_NODE_ID:-00000000-0000-4000-8000-000000000030}"
weights="series_scratch.safetensors"
arch="TinySeriesForecaster"

ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) arch 등록 (있으면 409 — 그대로 진행) =="
code=$(ccurl -s -o /dev/null -w '%{http_code}' -X POST "$core/v1/arches" \
  -H 'content-type: application/json' \
  -d "{\"arch\":\"$arch\",\"max_params\":500000,\"note\":\"timeseries.forecast 참조 모델 (단계 6 ②) · 24x4 = 100\"}")
echo "  HTTP $code"
[[ "$code" == "200" || "$code" == "409" ]] || { echo "arch 등록 실패" >&2; exit 1; }
if [[ "$code" == "409" ]]; then
  # D-arch 는 **갱신 경로가 없다** (상한을 사후에 바꾸면 이미 통과한 증서의 근거가 바뀐다).
  # 낮은 상한으로 먼저 등록돼 있으면 계약 게이트가 max_params 로 떨어진다 —
  # 그건 고장이 아니라 설계다. 빈 볼륨에서 돌리면 된다.
  cur=$(ccurl -sf "$core/v1/arches" | python3 -c "
import json,sys
for a in json.load(sys.stdin)['items']:
    if a['arch']=='$arch': print(a['max_params'])")
  echo "  이미 등록됨 (max_params=$cur) — 갱신하지 않는다 (D-arch)"
fi

echo "== 2) 능력 등록 (quality_profile=none · 골든셋 없음) =="
cap=$(ccurl -s -X POST "$core/v1/capabilities" -H 'content-type: application/json' -d '{
 "code":"timeseries.forecast","version":1,"name":"series forecast (scratch)",
 "description":"과거 24 → 앞으로 4 · 합성 데이터 scratch · 실제 시계열 성능 주장 없음",
 "input_schema":{"mediaTypes":["text/csv","application/json"],
   "preprocess":{"encoding":"utf-8","max_rows":10000,"window":24}},
 "output_schema":{"required":["forecast"],"properties":{
   "forecast":{"type":"array","items":{"type":"number"},"minItems":4,"maxItems":4}},
   "additionalProperties":false},
 "output_kind":"structured","compute_tier":"M","trust_domain_min":"team",
 "mvp_eligible":false,"quality_profile":"none"}')
capid=$(printf '%s' "$cap" | python3 -c '
import json,sys
d=json.load(sys.stdin)
print(d.get("id") or "")' 2>/dev/null || true)
if [[ -z "$capid" ]]; then
  capid=$(ccurl -sf "$core/v1/capabilities" | python3 -c '
import json,sys
d=json.load(sys.stdin); items=d["items"] if isinstance(d,dict) else d
print(next(c["id"] for c in items if c["code"]=="timeseries.forecast" and c["version"]==1))')
  echo "  이미 있음 → $capid"
else
  echo "  등록 → $capid"
fi

echo "== 3) 계약 샘플 부착 (Core 중개) =="
sample="$(mktemp -t capnet-text-XXXXXX.txt)"
python3 -c "
import math
print('\\n'.join('%.4f' % (0.2*t + 2*math.sin(t/5.0)) for t in range(40)))" > "$sample"
inp=$(ccurl -sf -X POST "$core/v1/inputs?capability=timeseries.forecast&version=1" \
  -H 'content-type: text/csv' --data-binary @"$sample")
inpid=$(printf '%s' "$inp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
ccurl -sf -X POST "$core/v1/capabilities/$capid/sample" -H 'content-type: application/json' \
  -d "{\"input_id\":\"$inpid\"}" >/dev/null
echo "  sample=$inpid"

echo "== 4) Agent 등록 =="
sha=$(docker compose --project-directory "$root" exec -T node-m-team \
  python -c "import hashlib;print(hashlib.sha256(open('/weights/$weights','rb').read()).hexdigest())" | tr -d '\r')
ver="0.1.0-text-$(date +%Y%m%d%H%M%S)"
agent=$(ccurl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' -d "{
 \"name\":\"series-scratch\",\"version\":\"$ver\",\"manifest_hash\":\"series\",
 \"weights_uri\":\"file:///weights/$weights\",\"weights_sha256\":\"$sha\",\"arch\":\"$arch\"}")
agentId=$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "  agent=$agentId arch=$arch"

echo "== 5) 계약 게이트 (team gate-runner 가 실행해서 판정) =="
CORE_URL="$core" bash "$root/scripts/contract_bind.sh" \
  --agent "$agentId" --capability timeseries.forecast@1 --weights "$weights"

echo "== 6) 능력만 요구한다 — 기기 주소 없음 =="
task_in="$(mktemp -t capnet-task-XXXXXX.txt)"
python3 -c "
import math
print('\\n'.join('%.4f' % (0.1*t + 1.5*math.cos(t/4.0)) for t in range(40)))" > "$task_in"
tin=$(ccurl -sf -X POST "$core/v1/inputs?capability=timeseries.forecast&version=1" \
  -H 'content-type: text/csv' --data-binary @"$task_in")
tid=$(printf '%s' "$tin" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
# datasetId 는 **참인 이름**을 적는다. inputId 가 있으므로 allowlist 는 건너뛴다
# (D8′ · Decision A) — 통제는 수집 문에 걸려 있고, 여기서 또 물으면 거짓말을 시킨다.
task=$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"text-demo\",\"caseId\":\"url-1\",\"capability_code\":\"timeseries.forecast\",\"capability_version\":1,\"inputId\":\"$tid\"}")
taskId=$(printf '%s' "$task" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
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
v = res.get("forecast") or []
if len(v) != 4:
    raise SystemExit("예측이 4개가 아니다: %d" % len(v))
if "label" in res:
    raise SystemExit("예측 결과에 label 이 들어 있다 — 증적이 거짓말한다")
print("series demo OK — 세 번째 모달리티(표/시계열)가 사슬을 완주했다")
print("forecast=", [round(x, 3) for x in v])
print("증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))
print("경계: 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))'
rm -f "$sample" "$task_in"
echo
echo "실제 시계열 성능을 주장하지 않는다 — 합성 데이터 학습이고 quality_profile='none' 이다."
