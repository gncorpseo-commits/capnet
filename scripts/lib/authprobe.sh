#!/usr/bin/env bash
# 강제 모드 인증 프로브의 **판정 한 줄**. `prod_room.sh` 가 쓴다.
#
# ## 왜 나눠 뒀나
#
# `prod_room.sh` 는 Docker 가 있어야 돌지만 **이 함수는 그냥 돈다** —
# `tests/test_prod_room_auth_probe.py` 가 실제로 부른다 (`lib/tally.sh` 와 같은 이유).
#
# ## 왜 판정을 따로 두나 — `000` 때문이다
#
# `prod_room.sh` 의 `code()` 는 이렇게 생겼다:
#
#   code(){ curl -s -o /dev/null -w '%{http_code}' -m 10 "$@"; }
#
# **Core 가 죽어 있으면 `000` 을 낸다.** 인증 프로브는 `= 401` 을 보므로 `000` 이
# 실패로 떨어져 안전하다. 그런데 **공개 프로브**는 「401 이 아니면 통과」다 —
# 그대로 쓰면 **Core 가 안 떠 있을 때 「공개 GET 정상」으로 초록**이 된다.
#
# 이 회차들이 고쳐 온 것과 같은 모양이다 (0건·0행·공허 `any` 를 통과로 세기).
# 그래서 **응답이 아닌 것은 먼저 실패**로 못박는다.
#
# ## 쓰는 법
#
#   source "$root/scripts/lib/authprobe.sh"
#   probe_verdict public "$c"   # 공개여야 하는 자리 — 401/403 이면 실패
#   probe_verdict authed "$c"   # 인증이 필요한 자리 — 401 이 아니면 실패
#
# 종료 코드: 0 = 기대대로 · 1 = 어긋남 또는 **응답 자체가 없음**

probe_verdict() {
  local kind="$1" code="$2"
  # 세 자리 숫자가 아니거나 000 이면 **응답을 못 받은 것**이다. 통과로 세지 않는다.
  case "$code" in
    ''|*[!0-9]*) echo "    응답 코드가 숫자가 아니다: '${code}'" >&2; return 1 ;;
  esac
  [ "${#code}" -eq 3 ] || { echo "    응답 코드가 세 자리가 아니다: '${code}'" >&2; return 1; }
  [ "$code" != "000" ] || { echo "    응답 없음 (000) — Core 가 떠 있는지 본다" >&2; return 1; }

  case "$kind" in
    public)
      # 공개인데 잠겼다 = 제품 입구(capreq)가 키 없이 카탈로그를 못 읽는다.
      if [ "$code" = "401" ] || [ "$code" = "403" ]; then
        echo "    공개여야 하는데 $code" >&2; return 1
      fi
      return 0 ;;
    authed)
      [ "$code" = "401" ] || { echo "    인증이 필요한데 $code" >&2; return 1; }
      return 0 ;;
    *)
      echo "    알 수 없는 종류: '$kind'" >&2; return 1 ;;
  esac
}
