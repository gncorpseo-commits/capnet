#!/usr/bin/env bash
# CapNet CycloneDX SBOM 생성기 (호스트 Python 3.11+)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/sbom.json"
py="${PYTHON:-python3}"
command -v "$py" >/dev/null || { echo "need python3"; exit 1; }
"$py" -m pip install -q cyclonedx-bom
req="$(mktemp)"
raw="$(mktemp)"
trap 'rm -f "$req" "$raw"' EXIT
# torch 버전은 Dockerfile 의 ARG 가 정본이다 — 여기에 다시 적으면 둘이 어긋난다.
torch_ver="$(sed -n 's/^ARG TORCH_VERSION=//p' "$root/apps/node/Dockerfile")"
torchvision_ver="$(sed -n 's/^ARG TORCHVISION_VERSION=//p' "$root/apps/node/Dockerfile")"
[ -n "$torch_ver" ] && [ -n "$torchvision_ver" ] || {
  echo "apps/node/Dockerfile 에서 torch 핀을 읽지 못했다" >&2; exit 1; }
{
  grep -v '^\s*#' "$root/apps/core/requirements.txt" || true
  grep -v '^\s*#' "$root/apps/node/requirements.txt" || true
  echo "torch==$torch_ver"
  echo "torchvision==$torchvision_ver"
} | sed '/^\s*$/d' | awk '!seen[$0]++' > "$req"
"$py" -m cyclonedx_py requirements "$req" -o "$raw" --of JSON
"$py" "$root/scripts/enrich_sbom.py" "$raw" "$out"
echo "OK $out"
