#!/usr/bin/env bash
# safety.pii 종단 데모 (Wave L) — 규칙 PII **참고**가 structured 로 완주하는가
#
#   scripts/pii_demo.sh
#
# 무엇을 보이나
#   1. arch 등록 — RuleTextPii (파라미터 0 · rule_pii.safetensors)
#   2. 능력 등록 (output_kind=structured · quality_profile=none) + 설명 동기화(PATCH)
#   3. 계약 샘플 부착 (Core 중개 · D8′)
#   4. 계약 게이트 (team gate-runner)
#   5. 작업 요청 → Core 배정 → 실행
#
# 무엇을 주장하지 않나
#   **탐지가 아니라 참고다.** 선언한 패턴만 본다 — 놓친 것이 없다고 말하지 않는다.
#   `_like` 는 꼴이 같다는 뜻이지 실제 번호라는 뜻이 아니다. 마스킹 도구도,
#   개인정보 보호 준수 보증도 아니다. 결과의 span 은 **가려서** 낸다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
weights="rule_pii.safetensors"
arch="RuleTextPii"

ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) arch 등록 (있으면 409 — 그대로 진행) =="
code=$(ccurl -s -o /dev/null -w '%{http_code}' -X POST "$core/v1/arches" \
  -H 'content-type: application/json' \
  -d "{\"arch\":\"$arch\",\"max_params\":1000,\"note\":\"safety.pii 규칙 기반 · 가중치 0 (Wave L)\"}")
echo "  HTTP $code"
[[ "$code" == "200" || "$code" == "409" ]] || { echo "arch 등록 실패" >&2; exit 1; }

echo "== 2) 능력 등록 (quality_profile=none · 골든셋 없음) =="
# 저장소의 능력 정의. 아래 「이미 있음」 분기에서 description 동기화에 다시 쓴다.
cap_body='{
 "code":"safety.pii","version":1,"name":"pii pattern hint",
 "description":"평문에서 미리 선언한 패턴(email·주민번호 꼴·카드번호 꼴·전화번호 꼴·IP·UUID)의 자리를 찾아 **가려서** 알려 준다. 탐지가 아니라 참고다 — 놓친 것이 없다고 말하지 않고, 찾아본 목록을 patterns_checked 로 함께 낸다. 「_like」는 꼴이 같다는 뜻이지 실제 번호라는 뜻이 아니다. 원문을 고쳐 주는 마스킹 도구가 아니고 개인정보 보호 준수를 보증하지 않는다. 타입 span 일반은 text.ner, 「키: 값」 필드는 text.extract 다. 품질 주장 없음",
 "input_schema":{"mediaTypes":["text/plain"],
   "preprocess":{"encoding":"utf-8","normalize":"NFC","max_chars":8000}},
 "output_schema":{"required":["patterns_checked","findings"],"properties":{
   "patterns_checked":{"type":"array","items":{"type":"string"}},
   "findings":{"type":"array","items":{"type":"object",
     "required":["label","start","end","text"],
     "properties":{
       "label":{"type":"string","enum":["email","krrn_like","card_like","phone_kr_like","ipv6","ipv4","uuid"]},
       "start":{"type":"integer","minimum":0},
       "end":{"type":"integer","minimum":0},
       "text":{"type":"string"}},
     "additionalProperties":false}}},
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
print(next(c["id"] for c in items if c["code"]=="safety.pii" and c["version"]==1))')
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
sample="$(mktemp -t capnet-pii-XXXXXX.txt)"
printf '문의 ops@example.dev 로 주세요\n서버 10.0.0.1 · 요청 7f3a9c21-1b2c-4d3e-8f90-aabbccddeeff\n' > "$sample"
inp=$(ccurl -sf -X POST "$core/v1/inputs?capability=safety.pii&version=1" \
  -H 'content-type: text/plain' --data-binary @"$sample")
inpid=$(printf '%s' "$inp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
ccurl -sf -X POST "$core/v1/capabilities/$capid/sample" -H 'content-type: application/json' \
  -d "{\"input_id\":\"$inpid\"}" >/dev/null
echo "  sample=$inpid"

echo "== 4) Agent 등록 =="
sha=$(docker compose --project-directory "$root" exec -T node-m-team \
  python -c "import hashlib;print(hashlib.sha256(open('/weights/$weights','rb').read()).hexdigest())" | tr -d '\r')
ver="0.1.0-pii-$(date +%Y%m%d%H%M%S)"
agent=$(ccurl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' -d "{
 \"name\":\"rule-text-pii\",\"version\":\"$ver\",\"manifest_hash\":\"rule-pii\",
 \"weights_uri\":\"file:///weights/$weights\",\"weights_sha256\":\"$sha\",\"arch\":\"$arch\"}")
agentId=$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "  agent=$agentId arch=$arch"
# rule_ner · rule_extract · rule_rank 와 sha 가 같다 — 넷 다 파라미터 0 · 버퍼 한 칸이라
# 바이트가 같다. 구별하는 것은 arch 이고, 증적에는 arch·sha 가 사실대로 남는다.

echo "== 5) 계약 게이트 (team gate-runner 가 실행해서 판정) =="
CORE_URL="$core" bash "$root/scripts/contract_bind.sh" \
  --agent "$agentId" --capability safety.pii@1 --weights "$weights"

echo "== 6) 능력만 요청 — 기기 주소 없음 =="
task_in="$(mktemp -t capnet-pii-task-XXXXXX.txt)"
printf '담당 ops@example.dev · 연락 010-1234-5678\n주민 900101-1234567 · 카드 4111 1111 1111 1111\n가짜카드 1234 5678 9012 3456 · 날짜꼴아님 991301-1234567\n' > "$task_in"
tin=$(ccurl -sf -X POST "$core/v1/inputs?capability=safety.pii&version=1" \
  -H 'content-type: text/plain' --data-binary @"$task_in")
tid=$(printf '%s' "$tin" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
task=$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"text-demo\",\"caseId\":\"url-1\",\"capability_code\":\"safety.pii\",\"capability_version\":1,\"inputId\":\"$tid\"}")
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
checked = res.get("patterns_checked") or []
findings = res.get("findings") or []
if not checked:
    raise SystemExit("patterns_checked 가 비어 있다 — 결과가 자기 한계를 안 들고 있다")
if not findings:
    raise SystemExit("findings 가 비어 있다")
if "label" in res or "vector" in res or "entities" in res:
    raise SystemExit("pii 결과에 다른 능력의 칸이 들어 있다 — 증적이 거짓말한다")
for f in findings:
    if "@example.dev" in f["text"] or "1234567" in f["text"] or "4111" in f["text"]:
        raise SystemExit("원문이 가려지지 않았다: %r" % f["text"])
labels = [f["label"] for f in findings]
if "krrn_like" not in labels or "card_like" not in labels:
    raise SystemExit("주민/카드 꼴이 안 잡혔다: %r" % labels)
if labels.count("card_like") != 1:
    raise SystemExit("Luhn 을 못 지나는 것이 카드로 잡혔다: %r" % labels)
if labels.count("krrn_like") != 1:
    raise SystemExit("날짜꼴이 아닌 것이 주민번호로 잡혔다: %r" % labels)
print("pii demo OK — safety.pii 가 structured 로 완주했다")
print("찾아본 패턴:", ", ".join(checked))
for f in findings:
    print("  %-14s %-24s @ %d-%d" % (f["label"], f["text"], f["start"], f["end"]))
a=d["assignment"]
print("증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))
print("경계: 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))'
rm -f "$sample" "$task_in"
echo
echo "탐지가 아니라 참고다 — 선언한 패턴만 보고, 놓친 것이 없다고 말하지 않는다."
