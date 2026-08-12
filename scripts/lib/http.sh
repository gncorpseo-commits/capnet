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
ccurl() {
  if [ -n "$CAPNET_API_KEY" ]; then
    curl -H "Authorization: CapNet-Key ${CAPNET_API_KEY}" "$@"
  else
    curl "$@"
  fi
}
