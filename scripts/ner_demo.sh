#!/usr/bin/env bash
# text.ner 종단 데모 (PR-B) — 규칙 기반 span 이 structured 로 완주하는가
#
#   scripts/ner_demo.sh
#
# 무엇을 보이나
#   1. arch 등록 — RuleTextNer (가중치 0 · rule_ner.safetensors)
#   2. 능력 등록 (output_kind=structured · quality_profile=none)
#   3. 계약 샘플 부착 (Core 중개 · D8′)
#   4. 계약 게이트 (team gate-runner)
#   5. 작업 요청 → Core 배정 → 실행
#
# 무엇을 주장하지 않나
#   일반 NER 성능. 사람·조직명은 다루지 않는다 — 구조 종류(email·url·…) span 만.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
runner="${RUNNER_NODE_ID:-00000000-0000-4000-8000-000000000030}"
weights="rule_ner.safetensors"
arch="RuleTextNer"

ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) arch 등록 (있으면 409 — 그대로 진행) =="
code=$(ccurl -s -o /dev/null -w '%{http_code}' -X POST "$core/v1/arches" \
  -H 'content-type: application/json' \
  -d "{\"arch\":\"$arch\",\"max_params\":1000,\"note\":\"text.ner 규칙 기반 · 가중치 0 (PR-B)\"}")
echo "  HTTP $code"
[[ "$code" == "200" || "$code" == "409" ]] || { echo "arch 등록 실패" >&2; exit 1; }

echo "== 2) 능력 등록 (quality_profile=none · 골든셋 없음) =="
cap=$(ccurl -s -X POST "$core/v1/capabilities" -H 'content-type: application/json' -d '{
 "code":"text.ner","version":1,"name":"structural text ner",
 "description":"자유 문장 어디에 있든 email·url·ipv4·uuid·iso_date 를 위치(start·end)와 함께 찾는다. 이름표(키)가 없어도 된다. 규칙 기반 · 일반 NER 주장 없음",
 "input_schema":{"mediaTypes":["text/plain"],
   "preprocess":{"encoding":"utf-8","normalize":"NFC","max_chars":8000}},
 "output_schema":{"required":["entities"],"properties":{
   "entities":{"type":"array","items":{"type":"object",
     "required":["label","start","end","text"],
     "properties":{
       "label":{"type":"string","enum":["email","url","ipv4","uuid","iso_date"]},
       "start":{"type":"integer","minimum":0},
       "end":{"type":"integer","minimum":0},
       "text":{"type":"string"}},
     "additionalProperties":false}}},
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
print(next(c["id"] for c in items if c["code"]=="text.ner" and c["version"]==1))')
  echo "  이미 있음 → $capid"
else
  echo "  등록 → $capid"
fi

echo "== 3) 계약 샘플 부착 (Core 중개) =="
sample="$(mktemp -t capnet-ner-XXXXXX.txt)"
printf 'Contact ops@example.dev or https://example.com on 2026-08-27 host 10.0.0.1 id 7f3a9c21-1b2c-4d3e-8f90-aabbccddeeff' > "$sample"
inp=$(ccurl -sf -X POST "$core/v1/inputs?capability=text.ner&version=1" \
  -H 'content-type: text/plain' --data-binary @"$sample")
inpid=$(printf '%s' "$inp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
ccurl -sf -X POST "$core/v1/capabilities/$capid/sample" -H 'content-type: application/json' \
  -d "{\"input_id\":\"$inpid\"}" >/dev/null
echo "  sample=$inpid"

echo "== 4) Agent 등록 =="
sha=$(docker compose --project-directory "$root" exec -T node-m-team \
  python -c "import hashlib;print(hashlib.sha256(open('/weights/$weights','rb').read()).hexdigest())" | tr -d '\r')
ver="0.1.0-ner-$(date +%Y%m%d%H%M%S)"
agent=$(ccurl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' -d "{
 \"name\":\"rule-text-ner\",\"version\":\"$ver\",\"manifest_hash\":\"rule-ner\",
 \"weights_uri\":\"file:///weights/$weights\",\"weights_sha256\":\"$sha\",\"arch\":\"$arch\"}")
agentId=$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "  agent=$agentId arch=$arch"

echo "== 5) 계약 게이트 (team gate-runner 가 실행해서 판정) =="
CORE_URL="$core" bash "$root/scripts/contract_bind.sh" \
  --agent "$agentId" --capability text.ner@1 --weights "$weights"

echo "== 6) 능력만 요청 — 기기 주소 없음 =="
task_in="$(mktemp -t capnet-ner-task-XXXXXX.txt)"
printf 'ops@example.dev seen at 192.168.0.5 on 2026-01-02' > "$task_in"
tin=$(ccurl -sf -X POST "$core/v1/inputs?capability=text.ner&version=1" \
  -H 'content-type: text/plain' --data-binary @"$task_in")
tid=$(printf '%s' "$tin" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
task=$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"text-demo\",\"caseId\":\"url-1\",\"capability_code\":\"text.ner\",\"capability_version\":1,\"inputId\":\"$tid\"}")
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
ents = res.get("entities") or []
if not ents:
    raise SystemExit("entities 가 비어 있다")
if "label" in res or "vector" in res:
    raise SystemExit("NER 결과에 label/vector 가 들어 있다 — 증적이 거짓말한다")
labels = sorted({e["label"] for e in ents})
print("ner demo OK — text.ner 가 structured span 으로 완주했다")
print("entities=", len(ents), "종류=", labels)
for e in ents:
    print(" ", e["label"], e["text"], "@", e["start"], "-", e["end"])
a=d["assignment"]
print("증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))
print("경계: 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))'
rm -f "$sample" "$task_in"
echo
echo "일반 NER·사람 이름을 주장하지 않는다 — quality_profile='none' · 규칙 span 만."
