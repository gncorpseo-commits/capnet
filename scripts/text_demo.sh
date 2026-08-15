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
cap=$(ccurl -s -X POST "$core/v1/capabilities" -H 'content-type: application/json' -d '{
 "code":"text.classify","version":1,"name":"structural text classify",
 "description":"closed-set 6 labels · 규칙 생성 학습 · 품질 주장 없음",
 "input_schema":{"mediaTypes":["text/plain"],
   "preprocess":{"encoding":"utf-8","normalize":"NFC","max_chars":8000}},
 "output_schema":{"required":["label"],"properties":{
   "label":{"type":"string","enum":["email","url","ipv4","uuid","iso_date","plain"]},
   "confidence":{"type":"number","minimum":0,"maximum":1}},
   "additionalProperties":false},
 "output_kind":"closed_set_labels","compute_tier":"M","trust_domain_min":"team",
 "mvp_eligible":false,"quality_profile":"none"}')
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

cat <<'NOTE'

== 6) 작업 실행은 여기서 막힌다 (보고) ==

  POST /v1/tasks 는 datasetId 를 **무조건** allowlist 와 대조한다
  (`apps/core/app/allowlist.py` · `ALLOWED_DATASET_IDS = {"eurosat-rgb"}`).

    {"detail":"datasetId not allowlisted: text-demo"}   HTTP 400

  텍스트 작업에는 맞는 datasetId 가 없다. `eurosat-rgb` 를 적으면 통과하지만
  **증적에 거짓 데이터셋이 남는다** — 그래서 그렇게 하지 않았다.

  D8′ 는 allowlist 를 「데모·카탈로그 **보조** 경로」로 남긴다고 했는데, 코드에서는
  아직 **필수**다. Core 중개 입력(inputId)이 있으면 바이트는 이미 계약에 묶여 있고
  (복합 FK) 해시·크기·MIME 도 검증됐으므로, 그 경우 datasetId 대조는 뜻이 없다.

  **정책이라 임의로 바꾸지 않았다.** Decision 이 필요하다 — docs/bridge/inbox-cursor.md

  여기까지: arch 등록 → 능력 등록 → 계약 샘플 → **계약 게이트 PASSED(실추론)** → 바인딩.
  즉 「텍스트 모달리티가 계약 사슬을 탄다」는 성립하고, 남은 것은 작업 접수 한 칸이다.

NOTE
echo "품질은 주장하지 않는다 — quality_profile='none' 이라 골든셋도 채점도 없다."
