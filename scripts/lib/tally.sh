#!/usr/bin/env bash
# 검사 집계의 **판정 한 줄**. `clean_room.sh` · `prod_room.sh` 가 함께 쓴다.
#
# ## 왜 나눠 뒀나
#
# 두 스크립트 다 이렇게 끝났다:
#
#   printf '===== 결과: 통과 %d · 실패 %d =====\n' "$pass" "$fail"
#   [ "$fail" -eq 0 ] || exit 1
#   echo "…에서 전부 재현된다."
#
# **한 건도 안 돌린 상태가 초록이었다.** `pass=0 · fail=0` 이면 `fail -eq 0` 이 참이라
# 「전부 재현된다」를 찍고 `exit 0` 한다. 이 회차가 고쳐 온 것과 같은 모양이다 —
# **0건을 「됐다」로 뭉뚱그린다** (#180 누출 검사 · #181 통합 러너).
#
# 그 판정을 한 곳에 두면 **검사할 수 있다.** 두 스크립트는 Docker 가 있어야 끝까지
# 돌지만, 이 함수는 그냥 돈다 → `tests/test_room_tally.py` 가 실제로 부른다.
#
# ## 쓰는 법
#
#   source "$root/scripts/lib/tally.sh"
#   tally_verdict "$pass" "$fail" "깨끗한 환경에서 전부 재현된다." || exit 1
#
# 종료 코드: 0 = 한 건 이상 돌았고 실패 0 · 1 = 실패가 있거나 **한 건도 안 돌았다**

tally_verdict() {
  local pass="$1" fail="$2" ok_line="$3"
  printf '===== 결과: 통과 %d · 실패 %d =====\n' "$pass" "$fail"
  if [ $((pass + fail)) -eq 0 ]; then
    echo "검사를 한 건도 안 돌렸다 — 0건은 통과가 아니다." >&2
    echo "스크립트가 중간에 빠져나갔는지 본다 (Docker · compose · 포트)." >&2
    return 1
  fi
  [ "$fail" -eq 0 ] || return 1
  echo "$ok_line"
}
