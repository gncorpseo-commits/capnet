#!/usr/bin/env bash
# paired A/B 비교 골격. Contest Must 아님.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
SCORE_A="${SCORE_A:-artifacts/score-n300-eurosat_scratch.json}"
SCORE_B="${SCORE_B:-artifacts/score-n300-eurosat_scratch_b.json}"
MAX_DEV="${MAX_DEVIATION:-0.05}"
MIN_N="${MIN_N:-300}"
a="$root/$SCORE_A"
b="$root/$SCORE_B"
[[ -f "$a" ]] || { echo "missing $a — run score_n300.sh first" >&2; exit 1; }
[[ -f "$b" ]] || { echo "missing $b — train B + WEIGHTS=eurosat_scratch_b.safetensors score_n300.sh" >&2; exit 1; }
set +e
python3 "$root/scripts/compare_ab.py" \
  --score-a "$a" --score-b "$b" \
  --max-deviation "$MAX_DEV" --min-n "$MIN_N"
rc=$?
set -e
if [[ "$rc" -eq 3 ]]; then
  echo "EXCEEDS_THRESHOLD (exit 3). Still not Contest Must."
fi
exit "$rc"
