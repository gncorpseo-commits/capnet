#!/usr/bin/env bash
# text.classify 종단 데모 (단계 5) — 이미지가 아닌 모달리티가 사슬을 타는가
#
#   scripts/text_demo.sh
#
# 무엇을 보이나
#   1. arch 등록 (D-arch API)          — 허용 목록에 없으면 Agent 등록이 FK 로 막힌다
#   2. 능력 등록 (quality_profile=none) — 골든셋 없음. **품질을 주장하지 않는다**
#   3. 계약 샘플 부착 (Core 중개 · D8′) — 텍스트에는 로컬 골든셋 폴백이 없다
#   4. 계약 게이트 (team gate-runner)   — 텍스트 전처리 선언을 **적용해** 실추론
#   5. 작업 요청 → Core 배정 → 실행     — 사용자는 기기 주소를 모른다
#
# 무엇을 주장하지 않나
#   분류 성능. `text.classify` 는 `quality_profile='none'` 이라 골든셋도 채점도 없다.
#   이 스크립트는 **경로가 성립한다**만 보인다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
runner="${RUNNER_NODE_ID:-00000000-0000-4000-8000-000000000030}"
weights="text_struct_scratch.safetensors"
arch="TinyTextClassifier"

ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) arch 등록 (있으면 409 — 그대로 진행) =="
code=$(ccurl -s -o /dev/null -w '%{http_code}' -X POST "$core/v1/arches" \
  -H 'content-type: application/json' \
  -d "{\"arch\":\"$arch\",\"max_params\":100000,\"note\":\"text.classify 참조 구현 (단계 5)\"}")
echo "  HTTP $code"
[[ "$code" == "200" || "$code" == "409" ]] || { echo "arch 등록 실패" >&2; exit 1; }

echo "== 2) 능력 등록 (quality_profile=none · 골든셋 없음) =="
# 저장소의 능력 정의. 아래 「이미 있음」 분기에서 description 동기화에 다시 쓴다.
cap_body='{
 "code":"text.classify","version":1,"name":"structural text classify",
 "description":"closed-set 6 labels · 규칙 생성 학습 · 품질 주장 없음",
 "input_schema":{"mediaTypes":["text/plain"],
   "preprocess":{"encoding":"utf-8","normalize":"NFC","max_chars":8000}},
 "output_schema":{"required":["label"],"properties":{
   "label":{"type":"string","enum":["email","url","ipv4","uuid","iso_date","plain"]},
   "confidence":{"type":"number","minimum":0,"maximum":1}},
   "additionalProperties":false},
 "output_kind":"closed_set_labels","compute_tier":"M","trust_domain_min":"team",
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
print(next(c["id"] for c in items if c["code"]=="text.classify" and c["version"]==1))')
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
printf 'ops-alerts+prod@example.dev' > "$sample"
inp=$(ccurl -sf -X POST "$core/v1/inputs?capability=text.classify&version=1" \
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
 \"name\":\"text-struct-scratch\",\"version\":\"$ver\",\"manifest_hash\":\"text-struct\",
 \"weights_uri\":\"file:///weights/$weights\",\"weights_sha256\":\"$sha\",\"arch\":\"$arch\"}")
agentId=$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "  agent=$agentId arch=$arch"

echo "== 5) 계약 게이트 (team gate-runner 가 실행해서 판정) =="
CORE_URL="$core" bash "$root/scripts/contract_bind.sh" \
  --agent "$agentId" --capability text.classify@1 --weights "$weights"

echo "== 6) 능력만 요구한다 — 기기 주소 없음 =="
task_in="$(mktemp -t capnet-task-XXXXXX.txt)"
printf 'https://capnet.example.org/docs/spec' > "$task_in"
tin=$(ccurl -sf -X POST "$core/v1/inputs?capability=text.classify&version=1" \
  -H 'content-type: text/plain' --data-binary @"$task_in")
tid=$(printf '%s' "$tin" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
# datasetId 는 **참인 이름**을 적는다. inputId 가 있으므로 allowlist 는 건너뛴다
# (D8′ · Decision A) — 통제는 수집 문에 걸려 있고, 여기서 또 물으면 거짓말을 시킨다.
task=$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"text-demo\",\"caseId\":\"url-1\",\"capability_code\":\"text.classify\",\"capability_version\":1,\"inputId\":\"$tid\"}")
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
print("text demo OK — 텍스트가 계약 게이트와 실행 경로를 완주했다")
print("label=", res.get("label"), " confidence=", res.get("confidence"))
print("증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))
print("경계: 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))'
rm -f "$sample" "$task_in"
echo
echo "품질은 주장하지 않는다 — quality_profile='none' 이라 골든셋도 채점도 없다."
