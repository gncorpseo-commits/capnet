#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
zip="$root/data/eurosat/EuroSAT_RGB.zip"
out="$root/data/golden-n300"
if [[ ! -f "$zip" ]]; then
  echo "EuroSAT zip missing. Run scripts/download_eurosat.sh first." >&2
  exit 1
fi
mkdir -p "$out"
docker run --rm \
  -v "$root/data/eurosat:/data:ro" \
  -v "$out:/out" \
  -v "$root/scripts:/scripts:ro" \
  python:3.11-slim \
  python /scripts/extract_golden.py --n 300 --zip /data/EuroSAT_RGB.zip --out /out --cases-prefix ic1f
echo "n=300 written under data/golden-n300 (gitignored)."
