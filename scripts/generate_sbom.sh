#!/usr/bin/env bash
# CapNet CycloneDX SBOM 생성기 (호스트 Python 3.11+)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/sbom.json"
py="${PYTHON:-python3}"
command -v "$py" >/dev/null || { echo "need python3"; exit 1; }
# 의존성 원본이 **있는지 먼저 본다 (큐 #55).** 아래 grep 이 `|| true` 였을 때는
# 파일이 사라져도 조용히 넘어가 SBOM 이 **그 의존성 없이** 만들어지고 exit 0 이었다.
# 대회 2차 라이선스 검증에 내는 산출물이라, 빠진 채 초록인 것이 가장 나쁘다.
for f in "$root/apps/core/requirements.txt" "$root/apps/node/requirements.txt"; do
  [ -r "$f" ] || { echo "의존성 파일을 못 읽는다: $f" >&2; exit 1; }
done
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
  # `|| true` 가 아니다 — grep 의 1(고른 줄 없음)만 봐주고 2(읽기 실패)는 죽는다.
  grep -v '^\s*#' "$root/apps/core/requirements.txt" || [ "$?" -eq 1 ]
  grep -v '^\s*#' "$root/apps/node/requirements.txt" || [ "$?" -eq 1 ]
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
