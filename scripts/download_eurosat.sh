#!/usr/bin/env bash
set -euo pipefail
EXPECTED=b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90
URL=https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEST_DIR="$ROOT/data/eurosat"
DEST="$DEST_DIR/EuroSAT_RGB.zip"
mkdir -p "$DEST_DIR"
if [[ ! -f "$DEST" ]]; then
  curl -L --retry 3 -o "$DEST" "$URL"
fi
ACTUAL=$(sha256sum "$DEST" | awk '{print $1}')
echo "sha256 $ACTUAL"
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
  echo "archive_sha256 mismatch. expected $EXPECTED" >&2
  exit 1
fi
echo "EuroSAT RGB pin OK -> $DEST"
