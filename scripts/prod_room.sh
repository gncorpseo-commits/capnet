#!/usr/bin/env bash
# 제품 수용 게이트 — 강제 모드(compose.prod.yaml)를 빈 볼륨에서 e2e 로 증명한다.
#
#   scripts/prod_room.sh
#
# clean_room.sh 가 데모 경로의 게이트라면 이것은 제품 경로의 게이트다.
# 운영 스택·데모 스택을 건드리지 않는다 (별도 프로젝트 capnet-prod · 포트 18830/18831).
# 부트스트랩 순서는 docs/guide/operate-production.md.
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
proj=capnet-prod
core_port=18830
node_port=18831

export CORE_URL="http://127.0.0.1:${core_port}"
export NODE_URL="http://127.0.0.1:${node_port}"
export COMPOSE_PROJECT_NAME="$proj"
export POSTGRES_USER=capnet POSTGRES_DB=capnet
export POSTGRES_PASSWORD='Pr0d-Test-$ecret'
export DATABASE_URL="postgresql://capnet:Pr0d-Test-%24ecret@postgres:5432/capnet"

ov="$(mktemp -t capnet-prod-XXXXXX.yaml)"
cat > "$ov" <<EOF
services:
  core:
    ports: !override ["${core_port}:8000"]
  node-m-team:
    ports: !override ["${node_port}:8001"]
  node-s-team:
    ports: !override []
  node-s-public:
    ports: !override []
EOF

dc(){ docker compose -p "$proj" --project-directory "$root" \
        -f "$root/compose.yaml" -f "$root/compose.prod.yaml" -f "$ov" "$@"; }

pass=0; fail=0
chk(){ local n="$1"; shift; if "$@"; then pass=$((pass+1)); echo "  ✅ $n"; else fail=$((fail+1)); echo "  ❌ $n"; fi; }
code(){ curl -s -o /dev/null -w '%{http_code}' -m 10 "$@"; }

cleanup(){ echo; echo "== 정리 =="; dc --profile demo down -v >/dev/null 2>&1; rm -f "$ov"
           rm -f "$root/data/node-secrets/node-m-team.credential"; }
trap cleanup EXIT

secrets="$root/data/node-secrets"; mkdir -p "$secrets"
rm -f "$secrets/node-m-team.credential"

echo "== 1) postgres 기동 (호스트 포트 비공개여야 한다) =="
dc --profile demo down -v >/dev/null 2>&1
dc up -d --build postgres >/dev/null 2>&1
for i in $(seq 1 60); do dc exec -T postgres pg_isready -U capnet -d capnet >/dev/null 2>&1 && break; sleep 2; done
pub=$(dc ps --format '{{.Service}} {{.Publishers}}' | grep '^postgres' | grep -c '5432/tcp ->' )
chk "postgres 호스트 미노출" test "$pub" = "0"

echo
echo "== 2) 자동 마이그레이션이 꺼져 있다 =="
dc up migrate 2>&1 | grep -q "건너뜀" && echo "  migrate 서비스: 건너뜀"
chk "CAPNET_AUTO_MIGRATE=0 이면 적용 안 함" bash -c '
  n=$('"$(declare -f dc >/dev/null; echo)"' docker compose -p '"$proj"' --project-directory '"$root"' \
      -f '"$root"'/compose.yaml -f '"$root"'/compose.prod.yaml -f '"$ov"' \
      exec -T postgres psql -U capnet -d capnet -tAc "SELECT coalesce(to_regclass('"'"'schema_migration'"'"')::text,'"'"'없음'"'"')")
  echo "    schema_migration: $n"; [ "$(echo $n|tr -d "[:space:]")" = "없음" ]'

echo
echo "== 3) 운영자가 직접 마이그레이션 =="
dc run --rm --no-deps core python -m app.migrate up 2>&1 | tail -2
chk "migrate up 성공" dc run --rm --no-deps core python -m app.migrate verify

echo
echo "== 4) core 기동 (강제 모드) =="
dc up -d core >/dev/null 2>&1
for i in $(seq 1 60); do curl -sf -m 3 "$CORE_URL/health" >/dev/null 2>&1 && break; sleep 2; done
chk "health 는 인증 없이 200" test "$(code $CORE_URL/health)" = "200"
echo -n "    enforcement: "; curl -s -m 10 "$CORE_URL/v1/ops/status" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["enforcement"], "ok=",d["ok"])' 2>/dev/null || echo "(조회 실패)"

echo
echo "== 5) 무인증 쓰기는 막힌다 =="
c=$(code -X POST "$CORE_URL/v1/nodes" -H 'content-type: application/json' \
      -d '{"name":"intruder","device_type":"SERVER","trust_domain":"public","compute_tier_max":"S","provision_source":"public"}')
echo "    POST /v1/nodes (키 없음) → HTTP $c"
chk "무인증 Node 등록 401" test "$c" = "401"
c=$(code -X POST "$CORE_URL/v1/agents" -H 'content-type: application/json' -d '{"name":"x","version":"1","manifest_hash":"h","weights_uri":"file:///weights/x.safetensors","weights_sha256":"0000000000000000000000000000000000000000000000000000000000000000"}')
echo "    POST /v1/agents (키 없음) → HTTP $c"
chk "무인증 Agent 등록 401" test "$c" = "401"

echo
echo "== 6) 잘못된 키도 막힌다 =="
c=$(code -X POST "$CORE_URL/v1/nodes" -H 'content-type: application/json' \
      -H 'Authorization: CapNet-Key ck_deadbeef.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' \
      -d '{"name":"intruder2","device_type":"SERVER","trust_domain":"public","compute_tier_max":"S","provision_source":"public"}')
echo "    POST /v1/nodes (가짜 키) → HTTP $c"
chk "가짜 키 401" test "$c" = "401"

echo
echo "== 7) admin 키 부트스트랩 (CLI — 유일한 첫 키 경로) =="
key=$(dc run --rm --no-deps core python -m app.apikey_cli issue --role admin --label bootstrap 2>&1 | grep -oE 'ck_[0-9a-f]{8}\.[A-Za-z0-9_-]+' | head -1)
if [ -n "$key" ]; then echo "    발급됨: ${key%%.*}.****"; else echo "    발급 실패"; fi
chk "admin 키 발급" test -n "$key"
export CAPNET_API_KEY="$key"

echo
echo "== 8) 키가 있으면 통과한다 =="
c=$(code -X POST "$CORE_URL/v1/nodes" -H 'content-type: application/json' \
      -H "Authorization: CapNet-Key $key" \
      -d '{"name":"prod-probe","device_type":"SERVER","trust_domain":"team","compute_tier_max":"M","provision_source":"team"}')
echo "    POST /v1/nodes (admin 키) → HTTP $c"
chk "admin 키로 Node 등록" bash -c "[ '$c' = '200' ] || [ '$c' = '201' ]"

echo
echo "== 9) seed 게이트러너 증서 발급 → 파일 주입 =="
runner=00000000-0000-4000-8000-000000000030
cred=$(curl -s -m 10 -X POST "$CORE_URL/v1/nodes/$runner/credentials" \
        -H 'content-type: application/json' -H "Authorization: CapNet-Key $key" \
        -d '{"label":"prod-e2e"}' | python3 -c 'import json,sys; print(json.load(sys.stdin).get("secret",""))' 2>/dev/null)
if [ -n "$cred" ]; then printf '%s' "$cred" > "$secrets/node-m-team.credential"; chmod 600 "$secrets/node-m-team.credential"; fi
chk "증서 발급·파일 기록" test -s "$secrets/node-m-team.credential"

echo
echo "== 10) 증서 없는 Node 는 401 (사칭 차단) =="
c=$(code "$CORE_URL/v1/internal/nodes/$runner/assignments")
echo "    GET assignments (증서 없음) → HTTP $c"
chk "증서 없는 Node 401" test "$c" = "401"

echo
echo "== 11) Node 기동 (증서 파일 마운트) =="
dc --profile demo up -d node-m-team >/dev/null 2>&1
for i in $(seq 1 60); do curl -sf -m 3 "$NODE_URL/health" >/dev/null 2>&1 && break; sleep 2; done
chk "Node health 200" test "$(code $NODE_URL/health)" = "200"
sleep 5
hb=$(curl -s -m 10 "$CORE_URL/v1/nodes-liveness" | python3 -c '
import json,sys
d=json.load(sys.stdin)
for n in d["nodes"]:
    if n["node_id"]=="00000000-0000-4000-8000-000000000030":
        print("fresh" if n.get("is_fresh") else "stale"); break
else: print("없음")' 2>/dev/null)
echo "    게이트러너 하트비트: $hb"
chk "증서로 하트비트 통과" test "$hb" = "fresh"

echo
echo "== 12) 강제 모드에서 demo.sh 완주 =="
CAPNET_API_KEY="$key" bash "$root/scripts/demo.sh" > "${TMPDIR:-/tmp}/prod_demo.log" 2>&1
rc=$?
tail -4 "${TMPDIR:-/tmp}/prod_demo.log"
echo "    rc=$rc"
chk "demo.sh 강제 모드 통과" test "$rc" = "0"

echo
printf '===== 결과: 통과 %d · 실패 %d =====\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
echo "제품 프로파일에서 전부 재현된다."
