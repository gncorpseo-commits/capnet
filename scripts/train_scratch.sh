#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
zip="$root/data/eurosat/EuroSAT_RGB.zip"
if [[ ! -f "$zip" ]]; then
  echo "EuroSAT zip missing. Run scripts/download_eurosat.sh first." >&2
  exit 1
fi
docker run --rm \
  -v "$root/data/eurosat:/data:ro" \
  -v "$root/apps/node/weights:/out" \
  -v "$root/apps/train:/train:ro" \
  -v "$root/apps/node:/nodepkg:ro" \
  -e PYTHONPATH=/nodepkg \
  python:3.11-slim \
  bash -lc 'pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu && pip install -q safetensors pillow && python /train/train_scratch.py'
