#!/usr/bin/env bash
# SD-007 마이그레이션 러너 래퍼.
# 기존 볼륨을 `docker compose down -v` 없이 다음 세대로 올린다.
#
#   scripts/migrate.sh status      # 적용 상태 (기본값)
#   scripts/migrate.sh verify      # 체크섬·금지 패턴만 검사 (쓰기 없음)
#   scripts/migrate.sh up --dry-run
#   scripts/migrate.sh up
#
# postgres 만 떠 있으면 된다. core 이미지를 일회용으로 빌려 쓴다 (score_n300.sh 와 같은 패턴).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cmd="${1:-status}"
shift || true

docker compose --project-directory "$root" run --rm --no-deps \
  core python -m app.migrate "$cmd" "$@"
