#!/usr/bin/env bash
# Core 를 부르는 공통 HTTP 래퍼. 각 운영 스크립트가 source 한다.
#
# 왜 있는가
#   REQUIRE_API_KEY=1 (제품 기본값) 이면 관리 API 쓰기 경로가 전부 401 이다.
#   스크립트마다 헤더를 손으로 붙이면 하나씩 빠뜨린다 — 한 곳에서 붙인다.
#
# 쓰는 법
#   CAPNET_API_KEY=ck_xxxxxxxx.yyy scripts/demo.sh
#   키가 없으면 헤더 없이 그대로 나간다 (강제가 꺼진 데모 경로가 안 깨진다).
#
# 시크릿 위생
#   키는 환경변수로만 받는다. 인자로 받으면 프로세스 목록(ps)에 남는다.
#   여기서 키를 echo 하지 않는다.

: "${CAPNET_API_KEY:=}"

# 키 파일 경로로도 받는다 — 환경변수보다 파일이 낫다 (docker inspect 에 안 뜬다).
if [ -z "$CAPNET_API_KEY" ] && [ -n "${CAPNET_API_KEY_FILE:-}" ] && [ -f "${CAPNET_API_KEY_FILE}" ]; then
  CAPNET_API_KEY="$(tr -d '[:space:]' < "${CAPNET_API_KEY_FILE}")"
fi

# curl 대용. 키가 있으면 관리 API 인증 헤더를 붙인다.
# 스킴은 apps/core/app/apikey.py 의 SCHEME 과 같아야 한다 (CapNet-Key).
#
# **헤더를 인자로 넘기지 않는다 (큐 #47).** 위 「시크릿 위생」이 인자를 금지해 놓고
# 정작 `curl -H "Authorization: … $KEY"` 로 넘기고 있었다 — 그건 curl 프로세스의 argv 라
# 같은 호스트의 아무나 `ps` 로 읽는다. 실측(2026-09-05):
#
#   curl -H Authorization: CapNet-Key ck_deadbeef.SECRETVALUE123 -s …   ← ps 에 그대로
#
# `-H @파일` 은 curl **7.55+** 가 지원한다. 파일은 0600 이고 호출이 끝나면 지운다.
# `|| rc=$?` 로 받는 이유: 호출자는 `set -e` 라, 그냥 두면 curl 실패 시 **지우기 전에**
# 셸이 죽어 시크릿 파일이 /tmp 에 남는다.
ccurl() {
  if [ -n "$CAPNET_API_KEY" ]; then
    local hdr rc=0
    hdr="$(mktemp -t capnet-hdr-XXXXXX)"
    chmod 600 "$hdr"
    printf 'Authorization: CapNet-Key %s\n' "$CAPNET_API_KEY" > "$hdr"
    curl -H "@$hdr" "$@" || rc=$?
    rm -f "$hdr"
    return $rc
  fi
  curl "$@"
}

# http_code 만 받는 판. `code()` 를 스크립트마다 다시 쓰지 않게 여기 둔다 (큐 #72).
# 키가 있으면 ccurl 이 헤더를 **0600 파일로** 넘긴다 — argv 에 안 남는다.
# **키 없이 눌러야 하는 프로브는 이걸 쓰면 안 된다.** 그건 각 스크립트의 맨 curl 이다.
ccode() {
  ccurl -s -o /dev/null -w '%{http_code}' -m 10 "$@"
}

# ── CORE_URL 이 가리키는 스택과 `docker compose` 가 고를 프로젝트가 같은가 (배치 R · R3)
#
# 왜 있는가
#   이 스크립트들은 주소는 CORE_URL 에서 받고, 가중치 해시·psql 은 `docker compose exec`
#   로 받는다. 그런데 compose 프로젝트는 CORE_URL 을 **따라가지 않는다** — 디렉터리
#   이름(또는 COMPOSE_PROJECT_NAME)에서 온다. 두 축이 따로 논다.
#
#   R3 실측(2026-09-06):
#
#     CORE_URL=http://127.0.0.1:18800 bash scripts/product_demo.sh   # 격리 방을 가리켰다
#     ...
#     == 4) Agent 등록 ==
#     service "node-m-team" is not running                            # 운영 프로젝트를 봤다
#
#   그때는 운영 스택이 꺼져 있어 「없다」로 끝났다. **켜져 있었으면 조용히 성공했을
#   것이다** — 격리 방에 등록할 Agent 의 가중치 해시를 다른 스택에서 읽어서. 배치 R 이
#   「운영 스택을 건드리지 마」라고 적은 바로 그 사고다.
#
# 무엇을 하나
#   CORE_URL 이 **루프백**이고 그 포트를 실제로 물고 있는 core 컨테이너가 있는데 그것이
#   지금 프로젝트의 것이 아니면 **멈춘다**. `docker compose port` 는 설정이 아니라
#   **런타임**을 본다 (CORE_PORT=18999 를 줘도 실제로 뜬 8000 을 답한다 — 실측).
#
# 무엇을 안 하나
#   스택이 안 떠 있으면 판단하지 않는다 (종전 「service … is not running」 그대로).
#   원격 Core 도 보지 않는다 — 거기엔 compose 가 없다.
#   끄려면 CAPNET_SKIP_COMPOSE_GUARD=1.
_capnet_compose_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

_capnet_assert_compose_matches_core() {
  [ -n "${CORE_URL:-}" ] || return 0
  [ -z "${CAPNET_SKIP_COMPOSE_GUARD:-}" ] || return 0
  case "${CORE_URL}" in
    http://127.0.0.1:*|http://localhost:*|http://0.0.0.0:*) ;;
    *) return 0 ;;
  esac
  command -v docker >/dev/null 2>&1 || return 0

  local want published
  want="${CORE_URL##*:}"; want="${want%%/*}"
  case "$want" in ''|*[!0-9]*) return 0 ;; esac

  published="$(docker compose --project-directory "$_capnet_compose_root" port core 8000 2>/dev/null | tail -1)"
  published="${published##*:}"
  case "$published" in ''|*[!0-9]*) return 0 ;; esac
  [ "$published" = "$want" ] && return 0

  echo "CORE_URL 과 compose 프로젝트가 다른 스택을 가리킨다." >&2
  echo "  CORE_URL      = ${CORE_URL}            (포트 ${want})" >&2
  echo "  compose 프로젝트 = ${COMPOSE_PROJECT_NAME:-<디렉터리 이름>} 의 core 는 ${published} 를 물고 있다" >&2
  echo "  이대로 두면 가중치 해시·psql 을 **다른 스택**에서 읽는다." >&2
  echo "  고치는 법: COMPOSE_PROJECT_NAME=<그 방 이름> 을 같이 준다 (clean_room=capnet-cleanroom · prod_room=capnet-prod)." >&2
  exit 1
}

_capnet_assert_compose_matches_core
