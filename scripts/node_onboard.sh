#!/usr/bin/env bash
# Node 온보딩 — 등록 → 증서 발급 → 주입 방법 안내 (P2-4 · v제품-1 운영화)
#
#   scripts/node_onboard.sh --name gpu-01 --tier M --domain team --source team
#   scripts/node_onboard.sh --name tenant-a1 --domain tenant --source invited
#
# 무엇을 하는가
#   1. Core 에 Node 를 등록한다 (등급은 **Core 가** 부여한다 — 절대규칙 4)
#   2. 그 Node 의 증서를 발급받는다 (평문 시크릿은 이때 한 번만 나온다)
#   3. 시크릿을 파일로 떨군다 (0600) — 프로세스 목록·docker inspect 에 노출되지 않게
#   4. Node 런타임에 넣을 환경변수를 출력한다
#
# 무엇을 하지 않는가
#   - Agent 바인딩 (가중치가 Node 에 있어야 한다 → scripts/node_bind.sh)
#   - 시크릿을 커밋하거나 로그에 남기는 일. 출력 파일은 .gitignore 대상 경로에 쓴다
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
# 관리 API 인증 헤더(CAPNET_API_KEY)를 한 곳에서 붙인다.
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"

name=""; device="PC_GPU"; tier="M"; domain="team"; source=""; runner="false"
outdir="${CAPNET_SECRETS_DIR:-$root/data/node-secrets}"

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)     name="$2"; shift 2 ;;
    --device)   device="$2"; shift 2 ;;
    --tier)     tier="$2"; shift 2 ;;
    --domain)   domain="$2"; shift 2 ;;
    --source)   source="$2"; shift 2 ;;
    --gate-runner) runner="true"; shift ;;
    --out)      outdir="$2"; shift 2 ;;
    -h|--help)  usage 0 ;;
    *) echo "모르는 인자: $1" >&2; usage 1 ;;
  esac
done

[[ -n "$name" ]] || { echo "--name 이 필요하다" >&2; usage 1; }

# provision_source 기본값은 도메인에서 유도한다.
# ck_trust_provision_align: team→team · tenant→team|invited · public→아무거나
if [[ -z "$source" ]]; then
  case "$domain" in
    team)   source="team" ;;
    tenant) source="invited" ;;
    public) source="public" ;;
  esac
fi

curl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }

echo "== 1) Node 등록 =="
body=$(printf '{"name":"%s","device_type":"%s","trust_domain":"%s","compute_tier_max":"%s","provision_source":"%s","is_gate_runner":%s}' \
  "$name" "$device" "$domain" "$tier" "$source" "$runner")
resp=$(ccurl -sf -X POST "$core/v1/nodes" -H 'content-type: application/json' -d "$body") || {
  echo "등록 실패 — 등급 조합이 제약에 맞는지 본다 (ck_trust_provision_align)" >&2; exit 1; }
node_id=$(printf '%s' "$resp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
printf '%s' "$resp" | python3 -c '
import json,sys
d=json.load(sys.stdin)
print("  id=%s" % d["id"])
print("  %s · %s · tier=%s · source=%s · gate_runner=%s"
      % (d["name"], d["trust_domain"], d["compute_tier_max"], d["provision_source"], d["is_gate_runner"]))'

echo "== 2) 증서 발급 =="
cred=$(ccurl -sf -X POST "$core/v1/nodes/$node_id/credentials" \
  -H 'content-type: application/json' -d "{\"label\":\"$name onboarding\"}") || {
  echo "발급 실패 — 이미 활성 증서가 있으면 먼저 폐기한다:" >&2
  echo "  curl -X POST $core/v1/nodes/$node_id/credentials/revoke -H 'content-type: application/json' -H \"Authorization: CapNet-Key \$CAPNET_API_KEY\" -d '{\"reason\":\"회전\"}'" >&2
  exit 1; }

mkdir -p "$outdir"; chmod 700 "$outdir"
secret_file="$outdir/$name.credential"
printf '%s' "$cred" | python3 -c 'import json,sys; sys.stdout.write(json.load(sys.stdin)["secret"])' > "$secret_file"
chmod 600 "$secret_file"
printf '%s' "$cred" | python3 -c '
import json,sys
d=json.load(sys.stdin)
print("  prefix=%s (시크릿은 파일에만 — 화면에 찍지 않는다)" % d["key_prefix"])'

echo
echo "== 3) Node 런타임에 주입 =="
cat <<EOF
  NODE_ID=$node_id
  NODE_CREDENTIAL_FILE=$secret_file
  CORE_URL=$core

  compose 예:
    environment:
      NODE_ID: "$node_id"
      NODE_CREDENTIAL_FILE: /run/secrets/node.credential
    volumes:
      - $secret_file:/run/secrets/node.credential:ro
EOF

echo
echo "== 다음 =="
echo "  가중치를 Node 에 두고 Agent 를 바인딩한다 → scripts/node_bind.sh"
echo "  증서 상태 확인 → curl -s -H \"Authorization: CapNet-Key \$CAPNET_API_KEY\" $core/v1/nodes-credentials"
echo
echo "  시크릿 파일: $secret_file (0600). **커밋하지 않는다.**"
echo "  회전: revoke 후 이 스크립트의 2단계를 다시 돈다."
