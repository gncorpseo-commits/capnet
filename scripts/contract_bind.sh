#!/usr/bin/env bash
# 계약 게이트 — 러너가 실제로 검증하고 그 결과로 마감한다 (B2)
#
#   scripts/contract_bind.sh --agent <uuid> --capability <code@version> --weights <file>
#
# 무엇을 하는가
#   1. 계약 게이트런을 시작한다 (Core 가 kind=contract 와 샘플을 스냅샷한다)
#   2. **게이트러너가** 계약 샘플을 받아 arch·max_params·input_schema·output_schema 를
#      실행해서 판정한다 (`python -m app.contract_check`)
#   3. 그 결과로 gate-run 을 마감한다 — 하나라도 실패면 FAILED (golden 과 같은 규약)
#   4. 통과하면 Node 에 바인딩한다
#
# 왜 러너인가
#   절대규칙 8. Core 가 스스로 판정을 만들면 「실행과 판정의 분리」가 무너진다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
# 관리 API 인증 헤더(CAPNET_API_KEY)를 한 곳에서 붙인다.
source "$root/scripts/lib/http.sh"

core="${CORE_URL:-http://127.0.0.1:8000}"
runner="${RUNNER_NODE_ID:-00000000-0000-4000-8000-000000000030}"
agent=""; capref=""; weights=""; target_node=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent) agent="$2"; shift 2 ;;
    --capability) capref="$2"; shift 2 ;;
    --weights) weights="$2"; shift 2 ;;
    --node) target_node="$2"; shift 2 ;;
    *) echo "모르는 인자: $1" >&2; exit 1 ;;
  esac
done
[[ -n "$agent" && -n "$capref" && -n "$weights" ]] || {
  echo "사용: contract_bind.sh --agent <uuid> --capability <code@version> --weights <file> [--node <uuid>]" >&2
  exit 1; }
code="${capref%@*}"; ver="${capref#*@}"; [[ "$ver" == "$capref" ]] && ver=1

ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) 계약 조회 =="
cap=$(ccurl -sf "$core/v1/capabilities" | python3 -c "
import json,sys
for c in json.load(sys.stdin)['items']:
    if c['code']=='$code' and c['version']==$ver: print(json.dumps(c)); break
else: raise SystemExit('capability 없음: $capref')")
cap_id=$(printf '%s' "$cap" | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
prof=$(printf '%s' "$cap" | python3 -c 'import json,sys;print(json.load(sys.stdin)["quality_profile"])')
echo "  $capref → ${cap_id:0:8}… profile=$prof"
[[ "$prof" == "none" ]] || { echo "  golden 능력이다 — scripts/node_bind.sh 를 쓴다" >&2; exit 1; }
ccurl -sf "$core/v1/capabilities/$cap_id" > /tmp/capnet_contract.json

echo "== 2) 게이트런 시작 (샘플 스냅샷은 DB 가 강제한다) =="
gr=$(ccurl -sf -X POST "$core/v1/internal/gate-runs" -H 'content-type: application/json' \
      -d "{\"agent_id\":\"$agent\",\"capability_id\":\"$cap_id\",\"runner_node_id\":\"$runner\"}") || {
  echo "  시작 거절 — 이 능력에 계약 샘플이 없다면 먼저 붙인다:" >&2
  echo "    POST $core/v1/capabilities/$cap_id/sample  {\"inputId\": \"...\"}" >&2
  exit 1; }
gr_id=$(printf '%s' "$gr" | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
kind=$(printf '%s' "$gr" | python3 -c 'import json,sys;print(json.load(sys.stdin)["kind"])')
echo "  gate_run=${gr_id:0:8}… kind=$kind"

echo "== 3) 러너가 검증한다 =="
# arch·max_params 는 **Core 가 말한다** (I1). 러너 로컬 meta 로 정하지 않는다.
ag=$(ccurl -sf "$core/v1/agents/$agent")
arch=$(printf '%s' "$ag" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("arch") or "")')
maxp=$(printf '%s' "$ag" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("max_params") or "")')
echo "  Core 가 말한 arch=${arch:-（없음）} max_params=${maxp:-（없음）}"
dc(){ docker compose --project-directory "$root" "$@"; }
dc cp /tmp/capnet_contract.json node-m-team:/tmp/contract.json
dc exec -T node-m-team python -c "
import os,urllib.request,sys
node_id=os.environ.get('NODE_ID')
cred=None
p=os.environ.get('NODE_CREDENTIAL_FILE')
if p and os.path.isfile(p): cred=open(p).read().strip()
cred=cred or os.environ.get('NODE_CREDENTIAL')
h={'Authorization':'CapNet-Node '+cred} if cred else {}
u=os.environ['CORE_URL']+'/v1/internal/capabilities/$cap_id/sample?node_id='+node_id
open('/tmp/sample.bin','wb').write(urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=60).read())
print('  샘플 수신 완료')"

set +e
raw=$(dc exec -T node-m-team python -m app.contract_check \
        --weights "/weights/$weights" ${arch:+--arch "$arch"} ${maxp:+--max-params "$maxp"} \
        --contract /tmp/contract.json --sample /tmp/sample.bin)
rc=$?
set -e
echo "$raw" | python3 -c '
import json, sys
d = json.loads(sys.stdin.read())
notes = d.get("_notes", {})
for k, v in d.items():
    if k.startswith("_"):
        continue
    print("  " + ("OK  " if v else "FAIL") + " " + k + " — " + str(notes.get(k, "")))'

echo "== 4) 그 결과로 마감한다 =="
status=$([ "$rc" -eq 0 ] && echo PASSED || echo FAILED)
body=$(printf '%s' "$raw" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
checks={k:v for k,v in d.items() if not k.startswith('_')}
print(json.dumps({'status':'$status','contract_checks':checks,
                  'note':'contract_check by gate-runner: '+json.dumps(d['_notes'],ensure_ascii=False)[:400]}))")
ccurl -sf -X POST "$core/v1/internal/gate-runs/$gr_id/finish" \
  -H 'content-type: application/json' -d "$body" >/dev/null
echo "  gate_run $status"
[[ "$status" == "PASSED" ]] || { echo "계약 검증 실패 — 바인딩하지 않는다"; exit 2; }

echo "== 5) Node 바인딩 =="
node="${target_node:-$runner}"
sha=$(dc exec -T node-m-team python -c "
import hashlib,sys;print(hashlib.sha256(open('/weights/$weights','rb').read()).hexdigest())" | tr -d '\r')
ccurl -sf -X POST "$core/v1/agents/$agent/bindings" -H 'content-type: application/json' \
  -d "{\"node_id\":\"$node\",\"weights_sha256_seen\":\"$sha\"}" >/dev/null
echo "  바인딩 완료 — 이제 배정이 간다"
