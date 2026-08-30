#!/usr/bin/env bash
# text.extract 종단 데모 (Wave C) — 규칙 필드 추출이 structured 로 완주하는가
#
#   scripts/text_extract_demo.sh
#
# 무엇을 보이나
#   1. arch 등록 — RuleTextExtract (파라미터 0 · rule_extract.safetensors)
#   2. 능력 등록 (output_kind=structured · quality_profile=none)
#   3. 계약 샘플 부착 (Core 중개 · D8′)
#   4. 계약 게이트 (team gate-runner)
#   5. 작업 요청 → Core 배정 → 실행
#
# 무엇을 주장하지 않나
#   자연어 이해. 문장에서 사실을 뽑지 못한다 — 한 줄에 「이름: 값」으로
#   이름표가 붙어 있는 것만 가져온다. 값의 뜻도 타입도 판정하지 않는다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
weights="rule_extract.safetensors"
arch="RuleTextExtract"

ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) arch 등록 (있으면 409 — 그대로 진행) =="
code=$(ccurl -s -o /dev/null -w '%{http_code}' -X POST "$core/v1/arches" \
  -H 'content-type: application/json' \
  -d "{\"arch\":\"$arch\",\"max_params\":1000,\"note\":\"text.extract 규칙 기반 · 가중치 0 (Wave C)\"}")
echo "  HTTP $code"
[[ "$code" == "200" || "$code" == "409" ]] || { echo "arch 등록 실패" >&2; exit 1; }

echo "== 2) 능력 등록 (quality_profile=none · 골든셋 없음) =="
cap=$(ccurl -s -X POST "$core/v1/capabilities" -H 'content-type: application/json' -d '{
 "code":"text.extract","version":1,"name":"structural field extract",
 "description":"줄이 「키: 값」 꼴로 이름표를 달고 있을 때만 그 이름표와 값을 뽑는다. 자유 문장 속 이메일·IP·날짜 같은 타입 span 은 여기가 아니라 text.ner 이다. 자연어 이해 주장 없음",
 "input_schema":{"mediaTypes":["text/plain"],
   "preprocess":{"encoding":"utf-8","normalize":"NFC","max_chars":8000}},
 "output_schema":{"required":["fields"],"properties":{
   "fields":{"type":"array","items":{"type":"object",
     "required":["key","value","line","start","end"],
     "properties":{
       "key":{"type":"string","minLength":1,"maxLength":64},
       "value":{"type":"string","minLength":1},
       "line":{"type":"integer","minimum":0},
       "start":{"type":"integer","minimum":0},
       "end":{"type":"integer","minimum":0}},
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
print(next(c["id"] for c in items if c["code"]=="text.extract" and c["version"]==1))')
  echo "  이미 있음 → $capid"
else
  echo "  등록 → $capid"
fi

echo "== 3) 계약 샘플 부착 (Core 중개) =="
sample="$(mktemp -t capnet-extract-XXXXXX.txt)"
printf 'Title: Q3 incident report\n- Owner: ops@example.dev\nHost = 10.0.0.1\nOpened: 2026-08-27\n12:30\nNote: 값에 : 콜론이 있어도 값이다\n' > "$sample"
inp=$(ccurl -sf -X POST "$core/v1/inputs?capability=text.extract&version=1" \
  -H 'content-type: text/plain' --data-binary @"$sample")
inpid=$(printf '%s' "$inp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
ccurl -sf -X POST "$core/v1/capabilities/$capid/sample" -H 'content-type: application/json' \
  -d "{\"input_id\":\"$inpid\"}" >/dev/null
echo "  sample=$inpid"

echo "== 4) Agent 등록 =="
sha=$(docker compose --project-directory "$root" exec -T node-m-team \
  python -c "import hashlib;print(hashlib.sha256(open('/weights/$weights','rb').read()).hexdigest())" | tr -d '\r')
ver="0.1.0-extract-$(date +%Y%m%d%H%M%S)"
agent=$(ccurl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' -d "{
 \"name\":\"rule-text-extract\",\"version\":\"$ver\",\"manifest_hash\":\"rule-extract\",
 \"weights_uri\":\"file:///weights/$weights\",\"weights_sha256\":\"$sha\",\"arch\":\"$arch\"}")
agentId=$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "  agent=$agentId arch=$arch"
# rule_ner.safetensors 와 sha 가 같다 — 둘 다 파라미터 0 · 버퍼 한 칸이라 바이트가 같다.
# 구별하는 것은 arch 이고, 증적에는 arch·sha 가 사실대로 남는다.

echo "== 5) 계약 게이트 (team gate-runner 가 실행해서 판정) =="
CORE_URL="$core" bash "$root/scripts/contract_bind.sh" \
  --agent "$agentId" --capability text.extract@1 --weights "$weights"

echo "== 6) 능력만 요청 — 기기 주소 없음 =="
task_in="$(mktemp -t capnet-extract-task-XXXXXX.txt)"
printf 'Ticket: INC-4021\nSeverity = high\nAssignee: ops@example.dev\nnot a field line\n' > "$task_in"
tin=$(ccurl -sf -X POST "$core/v1/inputs?capability=text.extract&version=1" \
  -H 'content-type: text/plain' --data-binary @"$task_in")
tid=$(printf '%s' "$tin" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
task=$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"text-demo\",\"caseId\":\"url-1\",\"capability_code\":\"text.extract\",\"capability_version\":1,\"inputId\":\"$tid\"}")
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
fields = res.get("fields") or []
if not fields:
    raise SystemExit("fields 가 비어 있다")
if "label" in res or "vector" in res or "entities" in res:
    raise SystemExit("extract 결과에 label/vector/entities 가 들어 있다 — 증적이 거짓말한다")
keys = [f["key"] for f in fields]
if "not a field line" in keys:
    raise SystemExit("이름표가 없는 줄을 필드로 읽었다")
print("extract demo OK — text.extract 가 structured 필드로 완주했다")
print("fields=", len(fields), "keys=", keys)
for f in fields:
    print(" ", f["key"], "=", f["value"], "@ line", f["line"], f["start"], "-", f["end"])
a=d["assignment"]
print("증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))
print("경계: 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))'
rm -f "$sample" "$task_in"
echo
echo "자연어 이해를 주장하지 않는다 — quality_profile='none' · 줄 규칙만."
