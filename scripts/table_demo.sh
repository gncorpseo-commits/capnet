#!/usr/bin/env bash
# table.extract 종단 데모 (단계 6 ④) — 여러 칸을 내는 출력이 계약과 대조되는가
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
#   분류 성능. `table.extract` 는 `quality_profile='none'` 이라 골든셋도 채점도 없다.
#   이 스크립트는 **경로가 성립한다**만 보인다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
runner="${RUNNER_NODE_ID:-00000000-0000-4000-8000-000000000030}"
weights="text_struct_scratch.safetensors"
arch="TinyTableTyper"

ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) arch 등록 (있으면 409 — 그대로 진행) =="
code=$(ccurl -s -o /dev/null -w '%{http_code}' -X POST "$core/v1/arches" \
  -H 'content-type: application/json' \
  -d "{\"arch\":\"$arch\",\"max_params\":500000,\"note\":\"table.extract — text.classify 가중치 재사용 (단계 6 ④)\"}")
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
# 저장소의 능력 정의. 아래 「이미 있음」 분기에서 description 동기화에 다시 쓴다.
cap_body='{
 "code":"table.extract","version":1,"name":"structural table extract",
 "description":"평문 표 → 열 타입 추론 · text.classify 가중치 재사용 · 표 이해도 주장 없음",
 "input_schema":{"mediaTypes":["text/plain"],
   "preprocess":{"encoding":"utf-8","max_rows":1000,"max_cols":64}},
 "output_schema":{"required":["columns","rows","header_detected"],"properties":{
   "columns":{"type":"array","items":{"type":"object","required":["index","type","support"]}},
   "rows":{"type":"array","items":{"type":"array","items":{"type":"string"}}},
   "header_detected":{"type":"boolean"}},
   "additionalProperties":false},
 "output_kind":"structured","compute_tier":"M","trust_domain_min":"team",
 "mvp_eligible":false,"quality_profile":"none"}'
cap=$(ccurl -s -X POST "$core/v1/capabilities" -H 'content-type: application/json' -d "$cap_body")
capid=$(printf '%s' "$cap" | python3 -c '
import json,sys
d=json.load(sys.stdin)
print(d.get("id") or "")' 2>/dev/null || true)
if [[ -z "$capid" ]]; then
  capid=$(ccurl -sf "$core/v1/capabilities" | python3 -c '
import json,sys
d=json.load(sys.stdin); items=d["items"] if isinstance(d,dict) else d
print(next(c["id"] for c in items if c["code"]=="table.extract" and c["version"]==1))')
  echo "  이미 있음 → $capid"
  # 등록은 (code, version) UNIQUE 로 한 번뿐이라, 저장소에서 description 을 고쳐도
  # 이미 등록된 스택에는 안 들어간다. 라우터는 DB 의 설명을 읽으므로 오래 돌아간 스택은
  # 저장소와 다른 문구로 라우팅한다 (실측 · 크기는 `scripts/route_bench.py` 로 잰다). 여기서 맞춘다.
  # **문구를 여기서 만들지 않는다** — 정본은 위 cap_body 이고 DB 를 거기에 맞출 뿐이다.
  want=$(printf '%s' "$cap_body" | python3 -c 'import json,sys; print(json.load(sys.stdin)["description"])')
  have=$(ccurl -sf "$core/v1/capabilities/$capid" | python3 -c '
import json,sys; print(json.load(sys.stdin).get("description") or "")')
  if [[ "$want" != "$have" ]]; then
    ccurl -sf -X PATCH "$core/v1/capabilities/$capid" -H 'content-type: application/json' \
      -d "$(printf '%s' "$want" | python3 -c '
import json,sys; print(json.dumps({"description": sys.stdin.read().rstrip(chr(10))}, ensure_ascii=False))')" \
      >/dev/null
    echo "  설명 동기화 — DB 가 저장소보다 낡아 있었다 (PATCH)"
  fi
else
  echo "  등록 → $capid"
fi

echo "== 3) 계약 샘플 부착 (Core 중개) =="
sample="$(mktemp -t capnet-text-XXXXXX.txt)"
printf 'name,contact,seen\nalpha,ops@example.dev,2026-01-02\nbravo,dev@example.io,2026-03-04\ncharlie,qa@example.org,2026-05-06\n' > "$sample"
inp=$(ccurl -sf -X POST "$core/v1/inputs?capability=table.extract&version=1" \
  -H 'content-type: text/plain' --data-binary @"$sample")
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
  --agent "$agentId" --capability table.extract@1 --weights "$weights"

echo "== 6) 능력만 요구한다 — 기기 주소 없음 =="
task_in="$(mktemp -t capnet-task-XXXXXX.txt)"
printf '| host | id |\n|------|----|\n| 10.0.0.1 | 7f3a9c21-1b2c-4d3e-8f90-aabbccddeeff |\n| 10.0.0.2 | 91a2b3c4-5d6e-4f70-8123-445566778899 |\n' > "$task_in"
tin=$(ccurl -sf -X POST "$core/v1/inputs?capability=table.extract&version=1" \
  -H 'content-type: text/plain' --data-binary @"$task_in")
tid=$(printf '%s' "$tin" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
# datasetId 는 **참인 이름**을 적는다. inputId 가 있으므로 allowlist 는 건너뛴다
# (D8′ · Decision A) — 통제는 수집 문에 걸려 있고, 여기서 또 물으면 거짓말을 시킨다.
task=$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"text-demo\",\"caseId\":\"url-1\",\"capability_code\":\"table.extract\",\"capability_version\":1,\"inputId\":\"$tid\"}")
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
cols = res.get("columns") or []
rows = res.get("rows") or []
if not cols or not rows:
    raise SystemExit("columns/rows 가 비어 있다")
if "label" in res or "vector" in res:
    raise SystemExit("표 추출 결과에 label/vector 가 들어 있다 — 증적이 거짓말한다")
print("table demo OK — 여러 칸을 내는 능력이 사슬을 완주했다")
print("columns=", [(c["index"], c["type"], c["support"]) for c in cols])
print("rows  =", len(rows), "행 · header_detected =", res.get("header_detected"))
print("증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))
print("경계: 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))'
rm -f "$sample" "$task_in"
echo
echo "표 이해도를 주장하지 않는다 — 머리글 판별은 느슨한 규칙이고 quality_profile='none' 이다."
