#!/usr/bin/env bash
# text.embed 참조 사영 생성 (단계 6 ①) — 라벨 학습 없음, 고정 시드 초기화
#
#   scripts/train_text_embed.sh
#
# 학습 데이터를 **생성한다** — 외부 말뭉치가 없으므로 다운로드 단계도 없다.
# 그래서 이미지 쪽(`train_scratch.sh`)과 달리 data/ 마운트가 필요 없다.
#
# torchvision·pillow 도 필요 없다 (텍스트다). torch + safetensors 만 설치한다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
OUT_NAME="${OUT_NAME:-text_embed_scratch.safetensors}"
# 최종 G2: 학습 컨테이너의 핀은 런타임과 같은 정본에서 읽는다 — Dockerfile ARG(torch) · apps/node/requirements.txt(나머지).
torch_ver="$(sed -n 's/^ARG TORCH_VERSION=//p' "$root/apps/node/Dockerfile")"
tv_ver="$(sed -n 's/^ARG TORCHVISION_VERSION=//p' "$root/apps/node/Dockerfile")"
sf_ver="$(sed -n 's/^safetensors==//p' "$root/apps/node/requirements.txt")"
np_ver="$(sed -n 's/^numpy==//p' "$root/apps/node/requirements.txt")"
pl_ver="$(sed -n 's/^pillow==//p' "$root/apps/node/requirements.txt")"
[ -n "$torch_ver" ] && [ -n "$tv_ver" ] && [ -n "$sf_ver" ] && [ -n "$np_ver" ] && [ -n "$pl_ver" ] || { echo "런타임 핀을 못 읽었다 (Dockerfile ARG / requirements.txt)" >&2; exit 1; }
docker run --rm \
  -v "$root/apps/node/weights:/out" \
  -v "$root/apps/train:/train:ro" \
  -v "$root/apps/node:/nodepkg:ro" \
  -e PYTHONPATH=/nodepkg \
  -e "HOST_UID=$(id -u)" -e "HOST_GID=$(id -g)" \
  python:3.11-slim \
  bash -lc "pip install -q \"torch==$torch_ver\" --index-url https://download.pytorch.org/whl/cpu \
    && pip install -q \"safetensors==$sf_ver\" \"numpy==$np_ver\" \
    && python /train/train_text_embed.py --out /out/$OUT_NAME \
    && chown \$HOST_UID:\$HOST_GID /out/$OUT_NAME /out/${OUT_NAME%.safetensors}.meta.json \
    && chmod 644 /out/$OUT_NAME /out/${OUT_NAME%.safetensors}.meta.json"
