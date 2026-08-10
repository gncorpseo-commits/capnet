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
python3 -m unittest discover -s tests "${@}" || fail=1

echo
echo "== 골든셋 sha 정합 =="
python3 scripts/check_golden_sha.py || fail=1

echo
if [[ "$fail" -ne 0 ]]; then
  echo "실패 — 위 항목을 고친다." >&2
  exit 1
fi
echo "전부 통과."
