#!/usr/bin/env bash
# text.rank 종단 데모 (Wave G) — 규칙 순위가 structured 로 완주하는가
#
#   scripts/text_rank_demo.sh
#
# 무엇을 보이나
#   1. arch 등록 — RuleTextRank (파라미터 0 · rule_rank.safetensors)
#   2. 능력 등록 (output_kind=structured · quality_profile=none)
#   3. 계약 샘플 부착 (Core 중개 · D8′)
#   4. 계약 게이트 (team gate-runner)
#   5. 작업 요청 → Core 배정 → 실행
#
# 무엇을 주장하지 않나
#   뜻을 안다는 것. 어휘가 겹치는 정도만 센다 — 「자동차」와 「차량」은 안 겹친다.
#   의미 유사도는 text.embed, 학습된 관련도는 retrieve.* 몫이다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
weights="rule_rank.safetensors"
arch="RuleTextRank"

ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) arch 등록 (있으면 409 — 그대로 진행) =="
code=$(ccurl -s -o /dev/null -w '%{http_code}' -X POST "$core/v1/arches" \
  -H 'content-type: application/json' \
  -d "{\"arch\":\"$arch\",\"max_params\":1000,\"note\":\"text.rank 규칙 기반 · 가중치 0 (Wave G)\"}")
echo "  HTTP $code"
[[ "$code" == "200" || "$code" == "409" ]] || { echo "arch 등록 실패" >&2; exit 1; }

echo "== 2) 능력 등록 (quality_profile=none · 골든셋 없음) =="
cap=$(ccurl -s -X POST "$core/v1/capabilities" -H 'content-type: application/json' -d '{
 "code":"text.rank","version":1,"name":"lexical overlap rank",
 "description":"첫 줄을 질의로 보고 나머지 줄들을 질의와 겹치는 낱말 수(자카드)로 줄 세운다. 뜻은 모른다 — 「자동차」와 「차량」은 안 겹친다. 의미 유사도는 text.embed, 학습된 관련도는 retrieve.dense/retrieve.rerank 다. 타입 span 은 text.ner, 「키: 값」 필드는 text.extract 다. 품질 주장 없음",
 "input_schema":{"mediaTypes":["text/plain"],
   "preprocess":{"encoding":"utf-8","normalize":"NFC","max_chars":8000}},
 "output_schema":{"required":["query","ranking"],"properties":{
   "query":{"type":"string"},
   "ranking":{"type":"array","items":{"type":"object",
     "required":["rank","line","text","score","overlap"],
     "properties":{
       "rank":{"type":"integer","minimum":1},
       "line":{"type":"integer","minimum":0},
       "text":{"type":"string","minLength":1},
       "score":{"type":"number","minimum":0,"maximum":1},
       "overlap":{"type":"array","items":{"type":"string"}}},
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
print(next(c["id"] for c in items if c["code"]=="text.rank" and c["version"]==1))')
  echo "  이미 있음 → $capid"
else
  echo "  등록 → $capid"
fi

echo "== 3) 계약 샘플 부착 (Core 중개) =="
sample="$(mktemp -t capnet-rank-XXXXXX.txt)"
printf 'ipv4 주소 로그\n\n로그에 ipv4 주소가 여러 개 있다\n오늘 점심 메뉴는 김치찌개\nipv4 주소 목록\n' > "$sample"
inp=$(ccurl -sf -X POST "$core/v1/inputs?capability=text.rank&version=1" \
  -H 'content-type: text/plain' --data-binary @"$sample")
inpid=$(printf '%s' "$inp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
ccurl -sf -X POST "$core/v1/capabilities/$capid/sample" -H 'content-type: application/json' \
  -d "{\"input_id\":\"$inpid\"}" >/dev/null
echo "  sample=$inpid"

echo "== 4) Agent 등록 =="
sha=$(docker compose --project-directory "$root" exec -T node-m-team \
  python -c "import hashlib;print(hashlib.sha256(open('/weights/$weights','rb').read()).hexdigest())" | tr -d '\r')
ver="0.1.0-rank-$(date +%Y%m%d%H%M%S)"
agent=$(ccurl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' -d "{
 \"name\":\"rule-text-rank\",\"version\":\"$ver\",\"manifest_hash\":\"rule-rank\",
 \"weights_uri\":\"file:///weights/$weights\",\"weights_sha256\":\"$sha\",\"arch\":\"$arch\"}")
agentId=$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "  agent=$agentId arch=$arch"
# rule_ner.safetensors · rule_extract.safetensors 와 sha 가 같다 — 셋 다 파라미터 0 ·
# 버퍼 한 칸이라 바이트가 같다. 구별하는 것은 arch 이고, 증적에는 arch·sha 가 사실대로 남는다.

echo "== 5) 계약 게이트 (team gate-runner 가 실행해서 판정) =="
CORE_URL="$core" bash "$root/scripts/contract_bind.sh" \
  --agent "$agentId" --capability text.rank@1 --weights "$weights"

echo "== 6) 능력만 요청 — 기기 주소 없음 =="
task_in="$(mktemp -t capnet-rank-task-XXXXXX.txt)"
printf '느린 쿼리 인덱스\n무관한 줄 하나\n느린 쿼리를 인덱스로 고쳤다\n인덱스 없이 느린 쿼리\n' > "$task_in"
tin=$(ccurl -sf -X POST "$core/v1/inputs?capability=text.rank&version=1" \
  -H 'content-type: text/plain' --data-binary @"$task_in")
tid=$(printf '%s' "$tin" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
task=$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"text-demo\",\"caseId\":\"url-1\",\"capability_code\":\"text.rank\",\"capability_version\":1,\"inputId\":\"$tid\"}")
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
ranking = res.get("ranking") or []
if not ranking:
    raise SystemExit("ranking 이 비어 있다")
if "label" in res or "vector" in res or "entities" in res or "fields" in res:
    raise SystemExit("rank 결과에 다른 능력의 칸이 들어 있다 — 증적이 거짓말한다")
if res.get("query") != "느린 쿼리 인덱스":
    raise SystemExit("첫 줄이 질의로 잡히지 않았다: %r" % res.get("query"))
if [r["rank"] for r in ranking] != list(range(1, len(ranking) + 1)):
    raise SystemExit("rank 가 1부터 이어지지 않는다")
scores = [r["score"] for r in ranking]
if scores != sorted(scores, reverse=True):
    raise SystemExit("점수 내림차순이 아니다")
if ranking[0]["text"] == "무관한 줄 하나":
    raise SystemExit("겹치는 낱말이 없는 줄이 1위가 됐다")
print("rank demo OK — text.rank 가 structured 순위로 완주했다")
print("query=", res["query"], "· 후보", len(ranking), "줄")
for r in ranking:
    print("  %d. score=%.4f line=%d overlap=%s | %s"
          % (r["rank"], r["score"], r["line"], ",".join(r["overlap"]) or "-", r["text"]))
a=d["assignment"]
print("증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))
print("경계: 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))'
rm -f "$sample" "$task_in"
echo
echo "뜻을 안다고 주장하지 않는다 — quality_profile='none' · 어휘 겹침만 센다."
