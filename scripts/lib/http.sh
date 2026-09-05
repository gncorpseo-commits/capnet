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
