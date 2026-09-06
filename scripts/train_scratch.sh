#!/usr/bin/env bash
# Agent A 기본 · B: ARCH=TinyEuroSATB OUT_NAME=eurosat_scratch_b.safetensors ./train_scratch.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
zip="$root/data/eurosat/EuroSAT_RGB.zip"
if [[ ! -f "$zip" ]]; then
  echo "EuroSAT zip missing. Run scripts/download_eurosat.sh first." >&2
  exit 1
fi
ARCH="${ARCH:-TinyEuroSAT}"
OUT_NAME="${OUT_NAME:-eurosat_scratch.safetensors}"
EXTRA_EPOCHS="${EXTRA_EPOCHS:-20}"
# 최종 G2: 학습 컨테이너의 핀은 런타임과 같은 정본에서 읽는다 — Dockerfile ARG(torch) · apps/node/requirements.txt(나머지).
torch_ver="$(sed -n 's/^ARG TORCH_VERSION=//p' "$root/apps/node/Dockerfile")"
tv_ver="$(sed -n 's/^ARG TORCHVISION_VERSION=//p' "$root/apps/node/Dockerfile")"
sf_ver="$(sed -n 's/^safetensors==//p' "$root/apps/node/requirements.txt")"
np_ver="$(sed -n 's/^numpy==//p' "$root/apps/node/requirements.txt")"
pl_ver="$(sed -n 's/^pillow==//p' "$root/apps/node/requirements.txt")"
[ -n "$torch_ver" ] && [ -n "$tv_ver" ] && [ -n "$sf_ver" ] && [ -n "$np_ver" ] && [ -n "$pl_ver" ] || { echo "런타임 핀을 못 읽었다 (Dockerfile ARG / requirements.txt)" >&2; exit 1; }
docker run --rm \
  -v "$root/data/eurosat:/data:ro" \
  -v "$root/apps/node/weights:/out" \
  -v "$root/apps/train:/train:ro" \
  -v "$root/apps/node:/nodepkg:ro" \
  -e PYTHONPATH=/nodepkg \
  -e "ARCH=$ARCH" \
  -e "OUT_NAME=$OUT_NAME" \
  -e "EXTRA_EPOCHS=$EXTRA_EPOCHS" \
  python:3.11-slim \
  bash -lc "pip install -q \"torch==$torch_ver\" \"torchvision==$tv_ver\" --index-url https://download.pytorch.org/whl/cpu && pip install -q \"safetensors==$sf_ver\" \"pillow==$pl_ver\" && python /train/train_scratch.py"
