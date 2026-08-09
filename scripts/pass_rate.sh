#!/usr/bin/env bash
# P1-3 통과율 측정 — 후보 Agent 모집단을 실게이트에 통과시켜 PASSED 비율을 낸다.
# 기획서 §7.2는 편차와 함께 "통과율 20–80%"를 판정 축으로 둔다.
#
# 모집단 규칙 (판정에 영향을 주므로 명시한다):
#   - 분모 = 정직하게 학습된 후보 가중치만. sanity floor(상수·난수·스키마 위반)는
#     설계상 반드시 실패하므로 분모에 넣지 않는다. floor는 scripts/sanity.sh가 별도로 본다.
#   - 후보는 Node가 실제로 들고 있는 safetensors여야 한다 (health가 증거).
#
# 사용: bash scripts/pass_rate.sh [weights1.safetensors weights2.safetensors ...]
#      인자가 없으면 Node health의 non-placeholder 가중치 전부를 후보로 본다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
core="http://127.0.0.1:8000"
node="http://127.0.0.1:8001"
capId="00000000-0000-4000-8000-000000000010"
runnerId="00000000-0000-4000-8000-000000000030"
stamp="$(date +%Y%m%d%H%M%S)"

curl -sf "$core/health" >/dev/null
nh="$(curl -sf "$node/health")"

if [[ $# -gt 0 ]]; then
  candidates=("$@")
else
  mapfile -t candidates < <(printf '%s' "$nh" | python3 -c '
import json,sys,os
h=json.load(sys.stdin)
for w in h.get("weights",[]):
    if not w["placeholder"]:
        print(os.path.basename(w["path"]))')
fi

if [[ ${#candidates[@]} -eq 0 ]]; then
  echo "후보 가중치가 없다. apps/node/weights/ 확인" >&2
  exit 1
fi

sha_of() {
  printf '%s' "$nh" | python3 -c '
import json,sys
want=sys.argv[1]
h=json.load(sys.stdin)
hits=[w for w in h.get("weights",[]) if w["path"].endswith(want) and not w["placeholder"]]
if not hits:
    raise SystemExit("weights missing on node: "+want)
print(hits[0]["sha256"])' "$1"
}

echo "== 통과율 실측 (team gate-runner · 골든=${GOLDEN:-데모 N=40}) =="
printf '%-34s %-8s %-8s %-8s %s\n' "candidate" "acc" "macro_f1" "invalid" "gate"
printf -- '---------------------------------------------------------------------------\n'

passed=0
total=0
rows=""

for wfile in "${candidates[@]}"; do
  sha="$(sha_of "$wfile")"
  label="cand-${wfile%.safetensors}-$stamp"

  set +e
  if [[ -n "${GOLDEN:-}" ]]; then
    # 지정 골든셋(예: 홀드아웃 n=300)으로 채점. 일회성 컨테이너에 마운트한다.
    #
    # 주의: GOLDEN 을 쓰면 뒤의 gate-run finish 는 API가 거부한다 —
    #   "cases_total 300 != golden_set_size 40"
    # capability 가 선언한 골든셋과 다른 셋의 점수를 게이트 기록으로 남길 수 없다.
    # 이건 버그가 아니라 계약이 작동하는 것이다. 사슬 밖 측정이 필요하면
    # scripts/score_n300.sh 를 GOLDEN 과 함께 쓰고 결과 JSON을 집계하라.
    raw="$(docker compose --project-directory "$root" run --rm --no-deps \
      -v "$GOLDEN:/golden-x:ro" -v "$root/apps/node/weights:/weights:ro" \
      node-m-team python -m app.score_gate --mode scratch --weights "/weights/$wfile" \
      --manifest /golden-x/manifest-image-classify-n300.json --cases /golden-x/cases \
      --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02)"
  else
    raw="$(docker compose --project-directory "$root" exec -T node-m-team \
      python -m app.score_gate --mode scratch --weights "/weights/$wfile" \
      --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02)"
  fi
  rc=$?
  set -e
  if [[ "$rc" -ne 0 && "$rc" -ne 2 ]]; then
    echo "score_gate failed rc=$rc ($wfile)" >&2
    exit 1
  fi

  # Agent 등록 → gate_run 시작 → finish. 결과가 FAILED여도 사슬에 기록한다.
  agent="$(curl -sf -X POST "$core/v1/agents" -H 'content-type: application/json' \
    -d "{\"name\":\"$label\",\"version\":\"0.1.0-$stamp\",\"manifest_hash\":\"$label-manifest\",\"weights_uri\":\"file:///weights/$wfile\",\"weights_sha256\":\"$sha\"}")"
  agentId="$(printf '%s' "$agent" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

  gr="$(curl -sf -X POST "$core/v1/internal/gate-runs" -H 'content-type: application/json' \
    -d "{\"agent_id\":\"$agentId\",\"capability_id\":\"$capId\",\"runner_node_id\":\"$runnerId\"}")"
  grId="$(printf '%s' "$gr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

  finish="$(printf '%s' "$raw" | python3 -c 'import json,sys
s=json.load(sys.stdin)
gr=json.loads(sys.argv[1])
print(json.dumps({
  "status": s["status"], "dummy": False,
  "golden_score": s["golden_score"], "cases_total": s["cases_total"],
  "cases_passed": s["cases_passed"], "macro_f1": s["macro_f1"],
  "invalid_rate": s["invalid_rate"], "min_per_class_recall": s.get("min_per_class_recall"), "note": sys.argv[2],
  "golden_set_sha256": gr["golden_set_sha256"],
}))' "$gr" "pass-rate $wfile")"
  curl -sf -X POST "$core/v1/internal/gate-runs/$grId/finish" \
    -H 'content-type: application/json' -d "$finish" >/dev/null

  line="$(printf '%s' "$raw" | python3 -c '
import json,sys
s=json.load(sys.stdin)
print("%-34s %-8.4f %-8.4f %-8.4f %s" % (sys.argv[1], s["golden_score"], s["macro_f1"], s["invalid_rate"], s["status"]))' "$wfile")"
  echo "$line"
  rows="$rows$line"$'\n'

  status="$(printf '%s' "$raw" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  total=$((total + 1))
  [[ "$status" == "PASSED" ]] && passed=$((passed + 1))
done

printf -- '---------------------------------------------------------------------------\n'
rate="$(python3 -c "print('%.1f' % (100.0 * $passed / $total))")"
echo "통과율 = $passed / $total = ${rate}%"

python3 - "$rate" <<'PY'
import sys
r = float(sys.argv[1])
if r > 80.0:
    print("판정 축: >80% — 골든셋이 너무 약하다 (§7.2). 계약 강화 후 재실험, 구현 확장 금지")
elif r < 20.0:
    print("판정 축: <20% — 골든셋이 너무 강하거나 모델군 부적합 (§7.2). 메트릭·티어 재설정")
else:
    print("판정 축: 20–80% 밴드 안 (§7.2 Go 조건 중 하나 충족)")
PY

cat <<'NOTE'

주의: 후보 수가 적으면 통과율의 해상도가 거칠다 (n=4면 25% 단위).
sanity floor는 분모에 없다 — scripts/sanity.sh로 따로 본다.
NOTE
