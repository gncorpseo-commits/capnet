#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
echo "sanity floor: constant / random / invalid must FAILED"
for mode in constant random invalid; do
  set +e
  raw="$(docker compose --project-directory "$root" exec -T node-m-team python -m app.score_gate --mode "$mode" --weights /weights/eurosat_scratch.safetensors --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02)"
  rc=$?
  set -e
  if [[ "$rc" -ne 0 && "$rc" -ne 2 ]]; then
    echo "score_gate $mode failed rc=$rc" >&2
    exit 1
  fi
  status="$(python -c 'import json,sys; print(json.load(sys.stdin)["status"])' <<<"$raw")"
  printf '%s' "$raw" | python -c 'import json,sys; s=json.load(sys.stdin); print("  %s: status=%s acc=%.4f" % (s["mode"], s["status"], s["golden_score"]))'
  if [[ "$status" != "FAILED" ]]; then
    echo "sanity $mode must FAILED" >&2
    exit 1
  fi
done
echo "sanity OK (floors FAILED). A/B Must는 미결·미구현."
