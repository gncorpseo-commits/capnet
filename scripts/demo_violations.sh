#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
docker compose -f "$ROOT/compose.yaml" exec -T postgres \
  psql -U capnet -d capnet -v ON_ERROR_STOP=1 < "$ROOT/scripts/demo_violations.sql"
echo "demo_violations finished (expect 6 REJECTED notices)"
