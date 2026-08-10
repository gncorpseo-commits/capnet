#!/usr/bin/env bash
# legacy Agent 의 arch 를 백필한다 (I1 의 남은 구멍)
#
#   scripts/backfill_agent_arch.sh --dry-run
#   scripts/backfill_agent_arch.sh
#
# 왜 필요한가
#   `migrations/0008` 은 arch 를 계약에 묶었지만, 그 이전에 등록된 Agent 는 `arch IS NULL` 이다.
#   실 DB 에서 45건(라우팅 가능 35건)이었다. 그것들의 실행 arch 는 여전히
#   **Node 로컬 파일**이 정한다 — I1 이 닫으려던 바로 그 구멍이다.
#
# 근거를 어디서 얻나 (중요)
#   Core 는 가중치 파일을 보지 않는다. 그래서 **추측으로 채우지 않는다.**
#   가중치를 실제로 들고 있는 Node 에게 물어본다:
#
#     GET /health → weights[] = { path, sha256, arch }
#
#   `arch` 는 학습 시 `train_scratch.py` 가 남긴 `<weights>.meta.json` 의 값이다.
#   즉 **학습 기록**이다. Node 의 증언이지 Core 의 독립 판정이 아니다 —
#   이 스크립트는 그 사실을 알고 쓰는 도구다.
#
#   `weights_sha256` 이 일치하는 Agent 만 채운다. 해시가 같으면 같은 파일이므로,
#   「어느 파일인지」는 추측이 아니다. 추측이 섞이는 지점은 「그 파일의 arch 가 무엇인가」뿐이고,
#   그건 학습 기록이 답한다.
#
# 무엇을 하지 않는가
#   - 이미 arch 가 있는 Agent 를 덮어쓰지 않는다
#   - Node 가 들고 있지 않은 가중치의 Agent 는 **그대로 둔다** (조회면에 남는다)
#   - allowlist(`agent_arch`) 밖 arch 로는 채우지 않는다 — FK 가 막지만 미리 거른다
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
core="${CORE_URL:-http://127.0.0.1:8000}"
node="${NODE_URL:-http://127.0.0.1:8001}"
dry=false
[[ "${1:-}" == "--dry-run" ]] && dry=true

curl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }
nh="$(curl -sf "$node/health")" || { echo "Node 응답 없음: $node" >&2; exit 1; }

# `docker compose exec -T` 는 stdin 을 먹는다. 여기서는 -c/-tAc 만 쓰므로 /dev/null 로 막는다.
# 이걸 안 하면 while 루프가 첫 줄만 처리하고 조용히 끝난다 (regate.sh 에서 이미 한 번 당했다).
psql() { docker compose --project-directory "$root" exec -T postgres psql -U capnet -d capnet "$@" </dev/null; }

echo "== 1) Node 가 들고 있는 가중치 (증언) =="
map="$(printf '%s' "$nh" | python3 -c '
import json, sys
h = json.load(sys.stdin)
for w in h.get("weights", []):
    if w.get("placeholder") or not w.get("arch"):
        continue
    print("%s\t%s\t%s" % (w["sha256"], w["arch"], w["path"].split("/")[-1]))')"
[[ -n "$map" ]] || { echo "Node 가 arch 를 아는 가중치가 없다" >&2; exit 1; }
printf '%s\n' "$map" | awk -F'\t' '{printf "  %s  %-14s %s\n", substr($1,1,12), $2, $3}'

echo
echo "== 2) 백필 대상 =="
psql -tAc "SELECT count(*)||'건 (라우팅 가능 '||count(*) FILTER (WHERE routable)||'건)' FROM agent_arch_unbound" \
  | sed 's/^/  arch 미선언: /'

allowed="$(psql -tAc "SELECT string_agg(arch, ',') FROM agent_arch" | tr -d '[:space:]')"
echo "  허용 arch: $allowed"

total=0; skipped=0
# 루프 입력은 fd 3 으로 읽는다 — 안쪽에서 docker 를 부르므로 기본 fd 를 쓰면 첫 줄만 돈다.
while IFS=$'\t' read -r sha arch file <&3; do
  [[ -z "$sha" ]] && continue
  if [[ ",$allowed," != *",$arch,"* ]]; then
    echo "  건너뜀 $file — '$arch' 는 agent_arch 에 없다"
    skipped=$((skipped+1)); continue
  fi
  n="$(psql -tAc "SELECT count(*) FROM agent WHERE weights_sha256='$sha' AND arch IS NULL" | tr -d '[:space:]')"
  [[ "$n" == "0" ]] && continue
  echo "  $file → $arch : $n 건"
  total=$((total+n))
  if ! $dry; then
    psql -qc "UPDATE agent SET arch='$arch' WHERE weights_sha256='$sha' AND arch IS NULL" >/dev/null
  fi
done 3<<< "$map"

echo
if $dry; then
  echo "[dry-run] $total 건이 채워질 예정 — 아무것도 쓰지 않았다 (건너뜀 $skipped)"
  exit 0
fi
echo "채움: $total 건 (건너뜀 $skipped)"

echo
echo "== 3) 남은 구멍 =="
psql -c "SELECT name, version, routable FROM agent_arch_unbound ORDER BY name LIMIT 20"
psql -tAc "SELECT '남은 미선언: '||count(*)||'건 (라우팅 가능 '||count(*) FILTER (WHERE routable)||'건)' FROM agent_arch_unbound"
echo
echo "남은 것은 Node 가 그 가중치를 들고 있지 않은 Agent 다 — 추측으로 채우지 않는다."
