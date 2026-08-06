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
{
  grep -v '^\s*#' "$root/apps/core/requirements.txt" || true
  grep -v '^\s*#' "$root/apps/node/requirements.txt" || true
  echo torch
  echo torchvision
} | sed '/^\s*$/d' | awk '!seen[$0]++' > "$req"
"$py" -m cyclonedx_py requirements "$req" -o "$raw" --of JSON
"$py" "$root/scripts/enrich_sbom.py" "$raw" "$out"
echo "OK $out"
