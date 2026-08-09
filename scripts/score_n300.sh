#!/usr/bin/env bash
# n=300 골든셋 채점. A/B Must 아님.
# WEIGHTS=eurosat_scratch_b.safetensors OUT_NAME=score-n300-b.json ./score_n300.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
golden="${GOLDEN:-$root/data/golden-n300}"   # 예: GOLDEN=$PWD/data/golden-n300-holdout
manifest="$golden/manifest-image-classify-n300.json"
WEIGHTS="${WEIGHTS:-eurosat_scratch.safetensors}"
stem="${WEIGHTS%.safetensors}"
OUT_NAME="${OUT_NAME:-score-n300-${stem}-$(basename "$golden").json}"
weights_host="$root/apps/node/weights/$WEIGHTS"

if [[ ! -f "$manifest" ]]; then
  echo "n=300 missing. Run scripts/extract_golden_n300.sh first." >&2
  exit 1
fi
if [[ ! -f "$weights_host" ]]; then
  echo "weights missing: $weights_host" >&2
  exit 1
fi

mkdir -p "$root/artifacts"
out_path="$root/artifacts/$OUT_NAME"

set +e
raw="$(docker compose --project-directory "$root" run --rm --no-deps \
  -v "$golden:/golden-n300:ro" \
  -v "$root/apps/node/weights:/weights:ro" \
  -v "$root/apps/node/app:/app/app:ro" \
  node-m-team \
  python -m app.score_gate \
    --mode scratch \
    --weights "/weights/$WEIGHTS" \
    --manifest /golden-n300/manifest-image-classify-n300.json \
    --cases /golden-n300/cases \
    --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02)"
rc=$?
set -e
if [[ "$rc" -ne 0 && "$rc" -ne 2 ]]; then
  echo "score_gate n300 rc=$rc" >&2
  exit "$rc"
fi
printf '%s\n' "$raw" > "$out_path"
python3 -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); print(f\"n300 status={d['status']} acc={d['golden_score']:.4f} f1={d['macro_f1']:.4f} n={d['cases_total']} → {sys.argv[1]}\")" "$out_path"
echo "A/B Must remains open. Compare: scripts/compare_ab.sh"
