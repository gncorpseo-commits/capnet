#!/usr/bin/env bash
# 제품 데모 — 「능력만 말하고, 파일을 붙이면, 승인 Node 에서 실행되고, 증적이 조회된다」
#
#   scripts/product_demo.sh
#
# 이 한 파일이 제품 주장 전체를 순서대로 보인다. 각 단계는 **Core 의 공개 API 만** 부른다 —
# DB 를 직접 보지 않는다. 심사·동료가 같은 명령으로 같은 것을 볼 수 있어야 하기 때문이다.
#
#   1) 살아 있나          GET /health
#   2) 무엇을 할 수 있나  GET /v1/capabilities
#   3) 능력이 준비됐나    없으면 scripts/ner_demo.sh 로 등록·게이트까지 한다
#   4) 능력만 말한다      POST /v1/inputs → POST /v1/tasks  (기기 주소 없음 · D22 · D8′)
#   5) 증적이 조회된다    GET /v1/tasks/{id}  (결과 + 어느 기기·어느 Agent·어느 경계)
#   6) 얼마나 돌았나      GET /v1/ops/work-units  (D26 · 정본은 Core 관측)
#
# 무엇을 주장하지 않나
#   품질. 여기 쓰는 text.ner 은 quality_profile='none' 이다 — 규칙 span 만 낸다.
#   이 스크립트가 보이는 것은 **경로와 증적**이지 정확도가 아니다.
#
# 환경
#   CORE_URL          기본 http://127.0.0.1:8000
#   CAPNET_API_KEY    강제 모드일 때 필요 (scripts/lib/http.sh 가 붙인다)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"

say() { printf '\n== %s ==\n' "$1"; }
die() { printf '\n실패: %s\n' "$1" >&2; exit 1; }

# ── 1) 살아 있나 ──────────────────────────────────────────────────────────
say "1) Core 가 살아 있나"
health="$(ccurl -sf -m 10 "$core/health")" || die "Core 응답 없음: $core (compose up 했는가)"
printf '%s' "$health" | python3 -c '
import json,sys
d=json.load(sys.stdin)
if not d.get("ok"): raise SystemExit("health ok=false")
print("  Core OK · postgres=%s" % d.get("postgres"))'

# ── 2) 무엇을 할 수 있나 ──────────────────────────────────────────────────
say "2) 무엇을 할 수 있나 (카탈로그)"
caps="$(ccurl -sf "$core/v1/capabilities")" || die "카탈로그 조회 실패"
printf '%s' "$caps" | python3 -c '
import json,sys
d=json.load(sys.stdin)
items=d["items"] if isinstance(d,dict) else d
print("  등록된 능력 %d 종" % len(items))
for c in sorted(items, key=lambda c:(c["code"], c["version"])):
    print("   %-22s v%-2s %-18s quality=%s" % (
        c["code"], c["version"], c.get("output_kind") or "-", c.get("quality_profile") or "-"))'

# ── 3) 능력이 준비됐나 ────────────────────────────────────────────────────
# 없으면 등록·계약 게이트까지 한 번에 한다. 데모가 「먼저 저걸 돌리세요」로 끝나지 않게.
say "3) text.ner 이 라우팅 가능한가"
ready="$(printf '%s' "$caps" | python3 -c '
import json,sys
d=json.load(sys.stdin)
items=d["items"] if isinstance(d,dict) else d
print("yes" if any(c["code"]=="text.ner" and c["version"]==1 for c in items) else "no")')"
if [ "$ready" != "yes" ]; then
  echo "  아직 없다 — scripts/ner_demo.sh 로 등록·게이트까지 돈다 (한 번만)"
  CORE_URL="$core" bash "$root/scripts/ner_demo.sh" >/dev/null 2>&1 \
    || die "ner_demo.sh 실패 — 그 스크립트를 직접 돌려 원인을 본다"
  echo "  준비 완료"
else
  echo "  이미 등록돼 있다"
fi

# ── 4) 능력만 말한다 ──────────────────────────────────────────────────────
say "4) 능력만 말한다 — 기기 주소는 어디에도 없다"
sample="$(mktemp -t capnet-product-XXXXXX.txt)"
trap 'rm -f "$sample"' EXIT
printf 'Contact ops@example.dev from 10.0.0.1 on 2026-08-29\n' > "$sample"
echo "  입력: $(cat "$sample")"

inp="$(ccurl -sf -X POST "$core/v1/inputs?capability=text.ner&version=1" \
  -H 'content-type: text/plain' --data-binary @"$sample")" \
  || die "입력 수집 실패 — Core 중개 경로(D22)"
inpid="$(printf '%s' "$inp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
printf '%s' "$inp" | python3 -c '
import json,sys
d=json.load(sys.stdin)
print("  Core 가 받아 적었다 — sha256=%s… %s bytes · %s" % (
    (d.get("sha256") or "")[:16], d.get("byte_size"), d.get("media_type")))'

task="$(ccurl -sf -X POST "$core/v1/tasks" -H 'content-type: application/json' \
  -d "{\"datasetId\":\"text-demo\",\"caseId\":\"product-1\",\"capability_code\":\"text.ner\",\"capability_version\":1,\"inputId\":\"$inpid\"}")" \
  || die "작업 생성 실패"
taskId="$(printf '%s' "$task" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
echo "  요청: capability=text.ner@1 · inputId=$inpid"
echo "  task=$taskId  (어느 기기로 갈지는 Core 가 정한다)"

# ── 5) 증적이 조회된다 ────────────────────────────────────────────────────
say "5) 증적이 조회된다"
tr=""
for _ in $(seq 1 60); do
  tr="$(ccurl -sf "$core/v1/tasks/$taskId")" || die "작업 조회 실패"
  st="$(printf '%s' "$tr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$st" = "COMPLETED" ] || [ "$st" = "FAILED" ] && break
  sleep 1
done
printf '%s' "$tr" | python3 -c '
import json,sys
d=json.load(sys.stdin)
if d["status"] != "COMPLETED":
    raise SystemExit("작업이 완주하지 않았다: %s" % d["status"])
res = d["result_ref"]
res = json.loads(res) if isinstance(res,str) else (res or {})
if res.get("dummy"):
    raise SystemExit("placeholder 로 돌았다 — 실행 증적이 아니다")
ents = res.get("entities") or []
if not ents:
    raise SystemExit("entities 가 비어 있다")
print("  결과 — 찾은 span %d 건" % len(ents))
for e in ents:
    print("    %-9s %-24s @ %s-%s" % (e["label"], e["text"], e["start"], e["end"]))
a = d["assignment"]
print("  어디서 돌았나 — node=%s" % a["node_id"])
print("                 agent=%s" % a["agent_id"])
print("  경계          — 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))
print("  이 네 값은 앱이 계산한 것이 아니라 DB 가 복합 FK 로 판정한 스냅샷이다.")'

# ── 6) 얼마나 돌았나 ──────────────────────────────────────────────────────
say "6) 얼마나 돌았나 (운영 조회 · D26)"
wu="$(ccurl -sf "$core/v1/ops/work-units?days=7")" || die "work-units 조회 실패 (developer 이상 필요)"
printf '%s' "$wu" | python3 -c '
import json,sys
d=json.load(sys.stdin)
t=d["totals"]
print("  최근 %d일 · 종결 배정 %d건 (성공 %d · 실패 %d)"
      % (d["window_days"], t["assignments"], t["succeeded"], t["failed"]))
print("  Core 관측 (정본) 합 %s ms · 평균 %s ms" % (t["core_observed_ms_sum"], t["core_observed_ms_avg"]))
print("  Node 자기신고(힌트) 합 %s ms · 평균 %s ms" % (t["node_hint_ms_sum"], t["node_hint_ms_avg"]))
print("  vram_mb_peak · energy_wh — 미계측 (계측된 건 %d · %d)"
      % (t["vram_measured"], t["energy_measured"]))
for r in d["by_capability"]:
    print("   %-22s %d건 · 관측 평균 %s ms" % (r["code"], r["assignments"], r["core_observed_ms_avg"]))
for w in d["warnings"]:
    print("  경고: %s" % w)'

say "요약"
echo "능력만 말했고, 파일은 Core 가 받아 적었고, 승인된 Node 에서 돌았고, 증적이 조회됐다."
echo "품질은 주장하지 않는다 — text.ner 은 quality_profile='none' 이다."
