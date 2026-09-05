#!/usr/bin/env bash
# 깨끗한 환경 재현 — 빈 볼륨에서 전체 배터리를 돌린다 (촬영 준비 ①)
#
#   scripts/clean_room.sh          # 격리 프로젝트로 전체 검증 후 정리
#   scripts/clean_room.sh --keep   # 끝나고 스택을 남긴다 (수동 확인용)
#
# 왜 있는가
#   촬영은 **새 clone·빈 볼륨**에서 한다. 그런데 그 검증은 스키마 세대 4 때 한 번 했고
#   그 뒤로 세대가 8까지 올랐고 CLAIM_SQL·seed 도 바뀌었다. 그 검증은 낡았다.
#
#   이 스크립트는 **운영 스택을 건드리지 않고** 별도 compose 프로젝트·별도 포트·빈 볼륨에서
#   촬영이 의존하는 것들을 전부 돌린다. 그래서 언제든 다시 확인할 수 있다.
#
# 무엇을 건드리지 않는가
#   운영 프로젝트(ai-agent-store)의 컨테이너·볼륨. 포트도 겹치지 않게 띄운다.
#
# 무엇을 돌리지 않는가 (큐 #46)
#   데모 스크립트 13 중 여기서 도는 것은 demo.sh · demo_violations.sh **둘**이다.
#   카탈로그 「구현됨」 10종 중 빈 볼륨에서 종단으로 도는 능력은 image.classify **하나**.
#   나머지는 tests/test_clean_room_covers_demos.py 의 OUTSIDE_CLEAN_ROOM 이 이유와 함께 센다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
# 판정 한 줄은 prod_room 과 공유한다 — 0건을 통과로 세지 않게.
source "$root/scripts/lib/tally.sh"
proj="${CLEAN_ROOM_PROJECT:-capnet-cleanroom}"
core_port="${CLEAN_ROOM_CORE_PORT:-18800}"
node_port="${CLEAN_ROOM_NODE_PORT:-18801}"
keep=false
[[ "${1:-}" == "--keep" ]] && keep=true

export CORE_URL="http://127.0.0.1:${core_port}"
export NODE_URL="http://127.0.0.1:${node_port}"
export COMPOSE_PROJECT_NAME="$proj"

override="$(mktemp -t capnet-cleanroom-XXXXXX.yaml)"
cat > "$override" <<EOF
services:
  postgres:
    ports: !override []
  core:
    ports: !override ["${core_port}:8000"]
  node-m-team:
    ports: !override ["${node_port}:8001"]
  node-s-team:
    ports: !override []
  node-s-public:
    ports: !override []
EOF

dc() { docker compose -p "$proj" --project-directory "$root" -f "$root/compose.yaml" -f "$override" "$@"; }

cleanup() {
  if $keep; then
    echo
    echo "스택을 남긴다 (--keep). 정리하려면:"
    echo "  docker compose -p $proj --project-directory $root -f $root/compose.yaml -f $override down -v"
  else
    echo
    echo "== 정리 =="
    dc down -v >/dev/null 2>&1 || true
    rm -f "$override"
  fi
}
trap cleanup EXIT

pass=0; fail=0
step() {  # step "이름" 명령...
  local name="$1"; shift
  printf '\n== %s ==\n' "$name"
  if "$@"; then pass=$((pass+1)); echo "  ✅ $name"
  else fail=$((fail+1)); echo "  ❌ $name"; fi
}

echo "깨끗한 환경 재현 — 프로젝트=$proj · Core=$CORE_URL"
echo "운영 스택(ai-agent-store)은 건드리지 않는다."

echo
echo "== 빈 볼륨에서 기동 =="
dc down -v >/dev/null 2>&1 || true
dc up -d --build postgres core node-m-team 2>&1 | tail -3
for i in $(seq 1 90); do curl -sf -m 3 "$CORE_URL/health" >/dev/null 2>&1 && break; sleep 2; done
curl -sf -m 5 "$CORE_URL/health" >/dev/null || { echo "Core 가 뜨지 않았다"; exit 1; }
for i in $(seq 1 60); do curl -sf -m 3 "$NODE_URL/health" >/dev/null 2>&1 && break; sleep 2; done
echo "  기동 완료"

# 마이그레이션 — 새 볼륨에서도 0001..N 이 전부 적용돼야 한다
step "마이그레이션 적용" bash -c '
  docker compose -p "$COMPOSE_PROJECT_NAME" --project-directory "'"$root"'" -f "'"$root"'/compose.yaml" -f "'"$override"'" \
    run --rm --no-deps core python -m app.migrate up 2>&1 | tail -3'

step "마이그레이션 verify" bash -c '
  docker compose -p "$COMPOSE_PROJECT_NAME" --project-directory "'"$root"'" -f "'"$root"'/compose.yaml" -f "'"$override"'" \
    run --rm --no-deps core python -m app.migrate verify 2>&1 | tail -1'

step "증적 드리프트 0 (새 볼륨)" bash -c '
  n=$(docker compose -p "$COMPOSE_PROJECT_NAME" --project-directory "'"$root"'" -f "'"$root"'/compose.yaml" -f "'"$override"'" \
      exec -T postgres psql -U capnet -d capnet -tAc "SELECT count(*) FROM provenance_drift WHERE still_routable")
  echo "  라우팅 드리프트: $n"; [ "$(echo $n | tr -d "[:space:]")" = "0" ]'

step "골든셋 sha 정합" python3 "$root/scripts/check_golden_sha.py"
step "M25 위반 시연" bash "$root/scripts/demo_violations.sh"
step "sanity floor 3종" bash "$root/scripts/sanity.sh"
step "demo (실게이트 + 사슬)" bash "$root/scripts/demo.sh"

# 능력 호출 — Agent 지정 없는 제품 경로. demo 가 Agent 를 하나 세워 둔 뒤라야 의미가 있다.
step "능력 호출 (Agent 미지정)" bash "$root/scripts/call.sh" ic1-0002

# Node 온보딩 — 등록 + 증서
step "Node 온보딩" bash -c '
  out=$(CAPNET_SECRETS_DIR=$(mktemp -d) bash "'"$root"'/scripts/node_onboard.sh" --name cleanroom-1 --domain tenant --tier M 2>&1)
  echo "$out" | tail -4
  echo "$out" | grep -q "NODE_CREDENTIAL_FILE"'

printf '\n'
# 「전부」가 무엇의 전부인지 밝힌다 — 능력 종단은 image.classify 하나다 (큐 #46).
# 나머지 아홉 종의 데모는 여기서 안 돈다: tests/test_clean_room_covers_demos.py
tally_verdict "$pass" "$fail" "깨끗한 환경에서 위 단계가 전부 재현된다 (능력 종단은 image.classify 하나)." || exit 1
