#!/usr/bin/env bash
# 통합 검사 러너 — **검사마다 깨끗한 DB** (구조적 격리)
#
#   scripts/run_integration.sh                    # 전부
#   scripts/run_integration.sh check_revocation   # 하나만
#
# ## 무엇이 문제였나
#
# 통합 검사 5개가 **DB 하나를 공유**했다. 넷은 SAVEPOINT + ROLLBACK 으로 스스로 격리하지만,
# `check_revocation` 은 **커밋해야 한다** — 배정·폐기·복권은 각각 다른 트랜잭션이고,
# 그 경계를 넘나드는 것이 바로 그 검사가 보는 계약이다.
#
# 그래서 그 검사가 남긴 상태가 뒤 검사를 오염시켰다. 지금까지의 대응은
# 「뒤 검사의 SETUP 을 멱등하게」·「앞 검사가 뒷정리」였는데, 그건 **쌍마다 붙이는 반창고**다.
# 검사가 늘면 조합이 늘고, 순서 가정이 코드 어디에도 적히지 않은 채 남는다.
#
# ## 구조적 해법 — 템플릿 데이터베이스
#
# 완전히 마이그레이션된 **템플릿 DB** 를 한 번 만들고, 검사마다
# `CREATE DATABASE ... TEMPLATE` 로 복제해 준다. PostgreSQL 에서 이건 파일 복사라 빠르다.
#
#   - 순서 의존이 **사라진다** (공유 상태가 없다)
#   - 커밋하는 검사가 마음껏 커밋해도 된다
#   - 멱등 SETUP·뒷정리 같은 반창고가 필요 없다
#
# DROP 하지 않는다 — postgres 서버 자체가 일회용이다 (CI 서비스 컨테이너 · 로컬 일회용 컨테이너).
# 서버가 사라질 때 검사 DB 도 같이 사라진다.
#
# 환경: PGHOST · PGPORT · PGUSER · PGPASSWORD (libpq 표준) · PYTHONPATH=apps/core
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"

export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGUSER="${PGUSER:-capnet}"
export PGPASSWORD="${PGPASSWORD:-capnet}"
export PYTHONPATH="${PYTHONPATH:-$root/apps/core}"

TEMPLATE="${CAPNET_TEMPLATE_DB:-capnet_tpl}"
ADMIN_DB="${CAPNET_ADMIN_DB:-postgres}"

url_for() { echo "postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/$1"; }

# 실행마다 고유한 토큰. `$$` 는 컨테이너 안에서 늘 1 이라 재실행하면 이름이 충돌한다.
run_id="$(date +%s)$(( RANDOM % 10000 ))"

checks=("$@")
if [[ ${#checks[@]} -eq 0 ]]; then
  # 이름 순으로 고정한다 — 순서가 결과를 바꾸지 않지만, 출력은 재현되는 편이 낫다.
  while IFS= read -r f; do checks+=("$(basename "$f" .py)"); done \
    < <(find "$root/tests/integration" -name 'check_*.py' | sort)
fi

echo "통합 검사 — 검사마다 깨끗한 DB (템플릿 복제)"
echo "  서버 ${PGHOST}:${PGPORT} · 검사 ${#checks[@]}개"

# --- 1) 템플릿 준비 -----------------------------------------------------------
# 이미 있으면 다시 만들지 않는다 (같은 서버에서 여러 번 부를 수 있게).
exists=$(psql -d "$ADMIN_DB" -tAc "SELECT 1 FROM pg_database WHERE datname='$TEMPLATE'" | tr -d '[:space:]')
if [[ "$exists" != "1" ]]; then
  echo
  echo "== 템플릿 준비 ($TEMPLATE) =="
  psql -d "$ADMIN_DB" -qc "CREATE DATABASE $TEMPLATE" >/dev/null
  psql -d "$TEMPLATE" -v ON_ERROR_STOP=1 -q -f "$root/docs/spec/schema.sql" >/dev/null
  psql -d "$TEMPLATE" -v ON_ERROR_STOP=1 -q -f "$root/apps/core/sql/seed.sql" >/dev/null
  DATABASE_URL="$(url_for "$TEMPLATE")" python3 -m app.migrate up | sed 's/^/  /'
else
  echo "  템플릿 재사용: $TEMPLATE"
fi

# --- 2) 검사마다 복제해서 실행 -------------------------------------------------
pass=0; fail=0; idx=0; failed_names=()
for name in "${checks[@]}"; do
  idx=$((idx+1))
  script="$root/tests/integration/$name.py"
  [[ -f "$script" ]] || { echo "  없는 검사: $name" >&2; fail=$((fail+1)); failed_names+=("$name"); continue; }

  # 이름 + 실행 토큰 + 순번. 같은 검사를 한 번에 두 번 돌려도 겹치지 않는다.
  db="chk_$(echo "$name" | tr -cd '[:alnum:]_' | cut -c1-28)_${run_id}_${idx}"
  # 템플릿에 연결이 남아 있으면 CREATE DATABASE 가 거부된다. 위 단계들은 전부 종료했다.
  psql -d "$ADMIN_DB" -qc "CREATE DATABASE $db TEMPLATE $TEMPLATE" >/dev/null

  printf '\n== %s ==\n' "$name"
  if DATABASE_URL="$(url_for "$db")" python3 "$script"; then
    pass=$((pass+1))
  else
    fail=$((fail+1)); failed_names+=("$name")
  fi
done

printf '\n===== 통합 검사: 통과 %d · 실패 %d =====\n' "$pass" "$fail"
if [[ "$fail" -gt 0 ]]; then
  printf '실패: %s\n' "${failed_names[*]}"
  exit 1
fi
echo "검사끼리 상태를 공유하지 않는다 — 순서를 바꿔도 같은 결과다."
