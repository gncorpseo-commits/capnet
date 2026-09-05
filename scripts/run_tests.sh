#!/usr/bin/env bash
# 전체 검증 — DB 없이 도는 것만. 통합 검증은 scripts/migrate.sh 와 CI 가 한다.
#
# pytest 를 쓰지 않는다. 이 리포에는 pip 가 없는 개발 환경이 있고,
# 표준 라이브러리 unittest 로 충분하다 (새 의존성 0).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

fail=0

echo "== 단위 테스트 =="
# 출력을 잡아 두는 이유는 **건너뛴 건수**를 맨 아래 배너에 다시 올리기 위해서다.
# `OK (skipped=7)` 은 초록으로 지나가고, 그래서 실제로 6건이 조용히 빠진 적이 있다
# (2026-09-01 · `node` 가 사라졌고 아무도 그 숫자를 안 읽었다). 임시 파일은 쓰지 않는다.
unit_out="$(python3 -m unittest discover -s tests "${@}" 2>&1)" || fail=1
printf '%s\n' "$unit_out"
# `OK (skipped=7)` · `FAILED (failures=1, skipped=7)` 둘 다에서 뽑는다.
skipped="$(printf '%s' "$unit_out" | sed -n 's/.*skipped=\([0-9][0-9]*\).*/\1/p' | tail -1)"
: "${skipped:=0}"

echo
echo "== 골든셋 sha 정합 =="
python3 scripts/check_golden_sha.py || fail=1

echo
echo "== 제출 zip 검증 (G9) =="
# 포털 패킹은 8/25–26 이다. 그날 처음 돌려 보면 늦다 — 매번 같이 본다.
bash "$root/scripts/check_release.sh" || fail=1

echo
echo "== 출품 패키지 기계 점검 =="
# 작업 중에도 돌 수 있게 워킹트리 검사는 뺀다. 패키징 직전에는 --skip-tree 없이 돌린다.
python3 scripts/check_submission.py --skip-tree || fail=1

echo
# **skip 은 통과가 아니다.** 배너까지 끌고 올라오지 않으면 아무도 안 읽는다.
#
# **실패한 회차에도 찍는다 (큐 #58).** 예전에는 이 블록이 `전부 통과.` 아래에만 있어서,
# `FAILED (failures=1, skipped=7)` 에서 숫자를 뽑아 놓고 **한 번도 안 보여 줬다** —
# 위 sed 가 두 모양을 다 잡는 이유가 사라져 있었다. 고칠 게 있는 회차일수록
# 「무엇이 안 돌았는가」가 필요하다.
if [[ "$skipped" -gt 0 ]]; then
  echo "  ${skipped}건은 **건너뛰었다** — 그 환경에 없는 것이 있다는 뜻이다."
  echo "  사유 목록: tests/test_skip_reasons.py 의 ALLOWED · 전부 돌리는 법: docs/guide/testing.md §2·§4.6"
fi
if [[ "$fail" -ne 0 ]]; then
  echo "실패 — 위 항목을 고친다." >&2
  exit 1
fi
echo "전부 통과."
