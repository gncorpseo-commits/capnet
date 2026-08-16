#!/usr/bin/env bash
# 제출 zip 을 **미리** 검증한다 (G9 · S2)
#
#   scripts/check_release.sh                 # HEAD 로 (태그 없이도 된다)
#   scripts/check_release.sh v0.1.0-contest  # 태그로
#
# ## 왜 있는가
#
# 포털 패킹은 8/25–26 이고, 그날 처음 돌려 보면 늦다. 여기서 막는 것은 셋이다.
#
#   1. **용량 초과** — 상한 50MB (U2). 가중치를 늘릴 때마다 커진다
#   2. **필수 파일 누락** — 심사위원이 재현하지 못한다
#   3. **넣지 말아야 할 것** — `.git` · `.env` · 실험 가중치
#
# 실제로 `git archive` 를 돌려 **압축본을 열어 본다.** 「명령이 있다」가 아니라
# 「그 명령의 결과가 조건을 만족한다」를 본다.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
ref="${1:-HEAD}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

zip="$tmp/capnet-${ref}.zip"
echo "== 제출 패키지 검증 (ref=$ref) =="
git -C "$root" archive --format=zip --prefix=capnet/ "$ref" -o "$zip"

fail=0
check() { if [[ "$1" == "0" ]]; then echo "  OK   $2"; else echo "  FAIL $2  $3"; fail=1; fi }

LIMIT_MB=50
mb=$(python3 -c "import os;print(f'{os.path.getsize(\"$zip\")/1048576:.1f}')")
python3 -c "import sys; sys.exit(0 if float('$mb') <= $LIMIT_MB and float('$mb') > 0 else 1)"
check $? "크기 ${mb} MB ≤ ${LIMIT_MB} MB" ""

python3 - "$zip" <<'PY'
import sys, zipfile
names = zipfile.ZipFile(sys.argv[1]).namelist()
inner = {n[len("capnet/"):] for n in names if n.startswith("capnet/")}

must = [
    "README.md", "LICENSE", "NOTICE", "THIRD-PARTY-LICENSES.md", "sbom.json",
    "compose.yaml", "compose.prod.yaml", "docs/spec/schema.sql",
    "scripts/demo.sh", "scripts/sanity.sh", "scripts/demo_violations.sh",
    # 없으면 심사위원이 재현할 수 없다 (S4-1).
    "apps/node/weights/eurosat_scratch.safetensors",
    "apps/node/weights/eurosat_scratch_b.safetensors",
    "apps/node/weights/text_struct_scratch.safetensors",
    "apps/node/weights/text_embed_scratch.safetensors",
    "apps/node/weights/series_scratch.safetensors",
    "apps/node/weights/placeholder.safetensors",
]
missing = [m for m in must if m not in inner]
print(f"  {'OK  ' if not missing else 'FAIL'} 필수 파일 {len(must)}종", end="")
print("" if not missing else f"  없음: {', '.join(missing[:3])}")

# 넣지 말아야 할 것. 실험 가중치는 이름으로 거른다 (`.gitignore` 가 막지만 확인한다).
bad = [
    n for n in inner
    if n.startswith(".git/") or n.endswith(".env") or n == ".env"
    or ("weights/" in n and n.endswith(".safetensors") and n.split("/")[-1] not in {
        "eurosat_scratch.safetensors", "eurosat_scratch_b.safetensors",
        "text_struct_scratch.safetensors", "text_embed_scratch.safetensors",
        "series_scratch.safetensors", "placeholder.safetensors",
    })
]
print(f"  {'OK  ' if not bad else 'FAIL'} 금지 산출물 없음", end="")
print("" if not bad else f"  있음: {', '.join(bad[:3])}")
print(f"  파일 {len(inner)}개 · 최상위 prefix capnet/ {'OK' if all(n.startswith('capnet/') for n in names) else 'FAIL'}")
sys.exit(1 if (missing or bad) else 0)
PY
check $? "압축본 내용" ""

echo
if [[ "$fail" -ne 0 ]]; then
  echo "실패 — 위 항목을 고친다. 8/25 에 처음 보면 늦다." >&2
  exit 1
fi
echo "제출 패키지 조건 충족. 남은 것은 태그·Release·포털 업로드 (사람이 한다)."
