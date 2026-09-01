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
# capreq 도 저장소와 함께 배포된다. **자기 의존성을 pyproject.toml 로 선언**하므로
# requirements.txt 만 모으면 빠진다 — 실제로 `httpx`·`python-multipart` 가 SBOM 에
# 없었다 (2026-09-02 실측). `[build-system] requires` 는 빼고 런타임·extra 만 모은다.
capreq_reqs="$("$py" - "$root/capreq/pyproject.toml" <<'PYDEPS'
import sys, tomllib

with open(sys.argv[1], "rb") as fh:
    doc = tomllib.load(fh)
project = doc.get("project") or {}
specs = list(project.get("dependencies") or [])
for extra in (project.get("optional-dependencies") or {}).values():
    specs.extend(extra)
for spec in specs:
    print(spec)
PYDEPS
)"
[ -n "$capreq_reqs" ] || { echo "capreq/pyproject.toml 에서 의존성을 못 읽었다" >&2; exit 1; }

{
  grep -v '^\s*#' "$root/apps/core/requirements.txt" || true
  grep -v '^\s*#' "$root/apps/node/requirements.txt" || true
  printf '%s\n' "$capreq_reqs"
  echo "torch==$torch_ver"
  echo "torchvision==$torchvision_ver"
} | sed '/^\s*$/d' | awk '
  # **이름으로** 중복을 없앤다. 줄 단위로 하면 `fastapi==0.116.1`(core 핀)과
  # `fastapi>=0.110`(capreq 범위)이 서로 다른 줄이라 **둘 다 남아 SBOM 에 같은
  # 구성요소가 두 번** 들어갔다 (2026-09-02 실측). 먼저 나온 것을 남긴다 —
  # requirements.txt 의 **핀이 실제 배포본**이고 앞에 온다.
  # `[` 를 문자 클래스에 넣으면 awk 가 `[=` 를 동치 클래스로 읽어 터진다. 따로 자른다.
  { name = $0; sub(/[=<>!~;].*$/, "", name); sub(/\[.*$/, "", name); gsub(/[ \t]+/, "", name) }
  !seen[name]++
' > "$req"
"$py" -m cyclonedx_py requirements "$req" -o "$raw" --of JSON
"$py" "$root/scripts/enrich_sbom.py" "$raw" "$out"
echo "OK $out"
