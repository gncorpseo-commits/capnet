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
# 케이스 디렉터리 검증. 심볼릭 링크는 컨테이너 마운트를 넘어가지 못하므로 실체를 요구한다.
if [[ -L "$golden/cases" ]]; then
  echo "cases 가 심볼릭 링크다: $golden/cases — 컨테이너 안에서 해석되지 않는다. 실제 파일로 두라." >&2
  exit 1
fi
n_cases="$(find "$golden/cases" -maxdepth 1 -name '*.jpg' 2>/dev/null | wc -l)"
n_manifest="$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1],encoding="utf-8"))["cases"]))' "$manifest")"
if [[ "$n_cases" -eq 0 ]]; then
  echo "케이스 이미지가 0건이다: $golden/cases" >&2
  exit 1
fi
if [[ "$n_cases" -ne "$n_manifest" ]]; then
  echo "케이스 수 불일치: 파일 $n_cases vs manifest $n_manifest ($golden)" >&2
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
