#!/usr/bin/env bash
# text.classify 참조 모델 scratch 학습 (단계 5)
#
#   scripts/train_text_scratch.sh
#
# 학습 데이터를 **생성한다** — 외부 말뭉치가 없으므로 다운로드 단계도 없다.
# 그래서 이미지 쪽(`train_scratch.sh`)과 달리 data/ 마운트가 필요 없다.
#
# torchvision·pillow 도 필요 없다 (텍스트다). torch + safetensors 만 설치한다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
OUT_NAME="${OUT_NAME:-text_struct_scratch.safetensors}"
docker run --rm \
  -v "$root/apps/node/weights:/out" \
  -v "$root/apps/train:/train:ro" \
  -v "$root/apps/node:/nodepkg:ro" \
  -e PYTHONPATH=/nodepkg \
  -e "HOST_UID=$(id -u)" -e "HOST_GID=$(id -g)" \
  python:3.11-slim \
  bash -lc "pip install -q torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -q safetensors numpy \
    && python /train/train_text_scratch.py --out /out/$OUT_NAME \
    && chown \$HOST_UID:\$HOST_GID /out/$OUT_NAME /out/${OUT_NAME%.safetensors}.meta.json \
    && chmod 644 /out/$OUT_NAME /out/${OUT_NAME%.safetensors}.meta.json"
