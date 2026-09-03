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
# 판정 한 줄은 clean_room 과 공유한다 — 0건을 통과로 세지 않게.
source "$root/scripts/lib/tally.sh"
# 인증 프로브 판정 — 000(응답 없음)을 통과로 세지 않는다. §13·§14 가 쓴다.
source "$root/scripts/lib/authprobe.sh"
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
# 여기서 먼저 빌드한다. `dc run` 은 --build 를 안 받으므로, 이걸 빼면 **마이그레이션이
# 옛 이미지에서** 돈다 — migrations/ 는 이미지에 COPY 되기 때문이다. §4 의 --build 는
# 런타임만 덮으므로, 새 마이그레이션이 적용되지 않은 DB 위에 새 코드가 뜬다.
# (G2 검사를 추가하다 실제로 걸렸다 — 0016 이 안 올라가 초대 발행이 500 이었다.)
dc build core >/dev/null 2>&1
dc run --rm --no-deps core python -m app.migrate up 2>&1 | tail -2
chk "migrate up 성공" dc run --rm --no-deps core python -m app.migrate verify

echo
echo "== 4) core 기동 (강제 모드) =="
# --build 가 없으면 **옛 이미지로 통과할 수 있다.** 이 게이트는 지금 소스가 제품
# 프로파일에서 도는지를 보는 것이지, 예전에 빌드해 둔 것이 도는지가 아니다.
# (S2 검사를 추가하다 실제로 걸렸다 — 새 엔드포인트가 404 였다.)
dc up -d --build core >/dev/null 2>&1
for i in $(seq 1 60); do curl -sf -m 3 "$CORE_URL/health" >/dev/null 2>&1 && break; sleep 2; done
chk "health 는 인증 없이 200" test "$(code $CORE_URL/health)" = "200"
# enforcement 표시는 §8-3 으로 옮겼다 — 조회면도 키를 요구하므로(read-auth)
# 키를 발급하기 전인 여기서는 401 이 정상이다.

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
echo "== 8-1) 안전 자세 조회면도 강제 아래에 있다 (S2) =="
# 「누가 내 데이터를 돌릴 수 있나」를 익명이 볼 수 있으면, 증서 없는 기기 목록이
# 그대로 공격 지도가 된다. 조회면이라고 예외를 두지 않는다.
c=$(code "$CORE_URL/v1/ops/safety")
echo "    GET /v1/ops/safety (키 없음) → HTTP $c"
chk "무인증 안전 조회면 401" test "$c" = "401"
enf=$(curl -s -m 10 "$CORE_URL/v1/ops/safety" -H "Authorization: CapNet-Key $key" \
      | python3 -c 'import json,sys; d=json.load(sys.stdin); e=d["enforcement"]; print(e["api_key"], e["node_credential"])' 2>/dev/null)
echo "    admin 키로 조회 → enforcement: $enf"
chk "강제 켜짐이 조회면에 그대로 보인다" test "$enf" = "True True"

echo
echo "== 8-2) 초대 소진은 관리 키 없이 된다 (G2) =="
# 이 경로만 키 없이 열린다 — 초대받은 사람에게는 관리 키가 없기 때문이다.
# 열려 있다는 것과 아무나 쓴다는 것은 다르다. 둘 다 여기서 본다.
inv=$(curl -s -m 10 -X POST "$CORE_URL/v1/nodes/invites" -H 'content-type: application/json' \
      -H "Authorization: CapNet-Key $key" -d '{"trust_domain":"tenant","label":"prod-room"}')
itok=$(printf '%s' "$inv" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("secret",""))' 2>/dev/null)
chk "초대 발행 (admin 키)" test -n "$itok"
c=$(code -X POST "$CORE_URL/v1/nodes/redeem" -H 'content-type: application/json' -d '{"name":"crew-1"}')
echo "    POST /v1/nodes/redeem (토큰 없음) → HTTP $c"
chk "초대 토큰 없는 소진 401" test "$c" = "401"
red=$(curl -s -m 10 -X POST "$CORE_URL/v1/nodes/redeem" -H 'content-type: application/json' \
      -H "Authorization: CapNet-Invite $itok" -d '{"name":"crew-1","device_type":"PC_GPU"}')
got=$(printf '%s' "$red" | python3 -c '
import json,sys
d=json.load(sys.stdin); n=d.get("node",{})
print("%s/%s/%s/%s" % (n.get("trust_domain"), n.get("provision_source"),
                       n.get("is_gate_runner"), bool(d.get("credential",{}).get("secret"))))' 2>/dev/null)
echo "    관리 키 없이 소진 → $got (도메인/조달/게이트러너/증서)"
chk "키 없이 소진되고 등급은 초대장이 정한다" test "$got" = "tenant/invited/False/True"
c=$(code -X POST "$CORE_URL/v1/nodes/redeem" -H 'content-type: application/json' \
      -H "Authorization: CapNet-Invite $itok" -d '{"name":"crew-2"}')
echo "    같은 초대 두 번째 → HTTP $c"
chk "1회용 초대는 두 번 안 된다" test "$c" = "401"

echo
echo "== 8-3) 조회면도 강제 아래에 있다 · 남의 작업은 안 보인다 (read-auth) =="
# 쓰기만 잠그면 「증적이 남고 조회된다」가 「누구나 조회된다」가 된다.
c=$(code "$CORE_URL/v1/ops/status");        echo "    GET /v1/ops/status (키 없음) → HTTP $c"
chk "무인증 운영 조회면 401" test "$c" = "401"
c=$(code "$CORE_URL/v1/nodes-credentials"); echo "    GET /v1/nodes-credentials (키 없음) → HTTP $c"
chk "무인증 증서 조회면 401" test "$c" = "401"
echo -n "    enforcement: "; curl -s -m 10 "$CORE_URL/v1/ops/status" \
  -H "Authorization: CapNet-Key $key" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["enforcement"], "ok=",d["ok"])' 2>/dev/null \
  || echo "(조회 실패)"

# 소유권 — 다른 사용자의 키로는 남의 작업이 **404** 다 (403 이면 존재를 흘린다).
other=$(dc run --rm --no-deps core python -m app.apikey_cli issue --role user --label other 2>&1 \
        | grep -oE 'ck_[0-9a-f]{8}\.[A-Za-z0-9_-]+' | head -1)
chk "다른 사용자 키 발급" test -n "$other"
tid=$(curl -s -m 10 -X POST "$CORE_URL/v1/tasks" -H 'content-type: application/json' \
      -H "Authorization: CapNet-Key $key" \
      -d '{"datasetId":"eurosat-rgb","caseId":"ic1-0001"}' \
      | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))' 2>/dev/null)
chk "작업 생성 (admin 키)" test -n "$tid"
c=$(code "$CORE_URL/v1/tasks/$tid" -H "Authorization: CapNet-Key $key")
echo "    소유자(admin) 조회 → HTTP $c"
chk "소유자는 자기 작업을 본다" test "$c" = "200"
c=$(code "$CORE_URL/v1/tasks/$tid" -H "Authorization: CapNet-Key $other")
echo "    다른 사용자 조회 → HTTP $c"
chk "남의 작업은 404 (403 아님)" test "$c" = "404"
c=$(code "$CORE_URL/v1/tasks/$tid")
echo "    무인증 조회 → HTTP $c"
chk "무인증 작업 조회 401" test "$c" = "401"

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
dc --profile demo up -d --build node-m-team >/dev/null 2>&1
for i in $(seq 1 60); do curl -sf -m 3 "$NODE_URL/health" >/dev/null 2>&1 && break; sleep 2; done
chk "Node health 200" test "$(code $NODE_URL/health)" = "200"
sleep 5
hb=$(curl -s -m 10 "$CORE_URL/v1/nodes-liveness" -H "Authorization: CapNet-Key $key" | python3 -c '
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

# 경로 파라미터에 넣는 더미. **존재하지 않아도 된다** — 인증이 조회보다 먼저 오므로
# 무인증이면 401 이어야 한다. 404 가 나오면 그건 인증 전에 DB 를 본 것이다.
dummy=00000000-0000-4000-8000-0000000000ff
capid=00000000-0000-4000-8000-000000000010

echo
echo "== 13) 공개 GET 전수 — 강제 모드에서도 열려 있어야 한다 =="
# 제품 입구(capreq)는 **키 없이** 카탈로그를 읽어 라우팅한다. 그 전제가 강제 모드에서
# 깨지면 입구가 통째로 죽는다. 지금까지 여기서 눌러 본 공개 GET 은 /health 하나였다.
# 목록은 tests/test_prod_room_auth_probe.py 가 소스와 대조한다 — 빠뜨리면 검사가 잡는다.
for path in \
  "/" \
  "/health" \
  "/openapi.yaml" \
  "/v1/capabilities" \
  "/v1/capabilities/$capid" \
  "/v1/datasets" ; do
  c=$(code "$CORE_URL$path")
  echo "    GET $path (키 없음) → HTTP $c"
  chk "공개 GET $path" probe_verdict public "$c"
done

echo
echo "== 14) 인증 GET 전수 — 무인증이면 전부 401 =="
# ast 검사(test_every_route_declares_its_auth)는 「인증 헬퍼를 불렀는가」만 본다.
# **강제 모드에서 실제로 401 이 나오는가**는 여기서만 잰다. 지금까지 넷뿐이었다.
for path in \
  "/v1/agents" \
  "/v1/agents/$dummy" \
  "/v1/api-keys" \
  "/v1/arches" \
  "/v1/inputs/$dummy" \
  "/v1/internal/capabilities/$capid/sample" \
  "/v1/internal/gate-runs/$dummy" \
  "/v1/internal/inputs/$dummy/bytes" \
  "/v1/internal/nodes/$dummy/assignments" \
  "/v1/nodes" \
  "/v1/nodes-credentials" \
  "/v1/nodes-liveness" \
  "/v1/nodes/invites" \
  "/v1/nodes/$dummy" \
  "/v1/ops/safety" \
  "/v1/ops/status" \
  "/v1/ops/work-units" \
  "/v1/tasks/$dummy" ; do
  c=$(code "$CORE_URL$path")
  echo "    GET $path (키 없음) → HTTP $c"
  chk "무인증 GET $path 401" probe_verdict authed "$c"
done

echo
tally_verdict "$pass" "$fail" "제품 프로파일에서 전부 재현된다." || exit 1
