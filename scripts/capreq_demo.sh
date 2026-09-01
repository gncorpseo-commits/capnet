#!/usr/bin/env bash
# capreq 종단 데모 — **제품 입구**가 실제로 이어지는가
#
#   scripts/capreq_demo.sh
#
# ## 왜 있는가
#
# 다른 `*_demo.sh` 는 전부 **Core 를 직접** 부른다. 그런데 사람이 실제로 쓰는 입구는
# `capreq` 다 — 브라우저에서 문장을 쓰고 파일을 붙인다. 그 경로에는 종단 검사가 없었다.
#
# 없어서 무슨 일이 났나: **첨부가 한 번도 동작하지 않았다** (`7936a0f`). 단위 검사도
# `chat_flow_probe.js` 도 통과하고 있었다 — `fetch` 를 스텁으로 막아 놓기 때문이다.
# 손으로 종단을 재고서야 잡혔다. 그 실측을 스크립트로 남긴다.
#
# ## 무엇을 보이나
#
#   1. capreq 가 **Core 의 살아 있는 카탈로그**를 읽는가 (`/api/capabilities`)
#   2. 문장 + 첨부 → 라우팅 → **Core 중개 업로드**(`input_id`) → 작업 → 완주
#   3. 증적이 조회되는가 (assignment · node · 신뢰도메인·티어 경계)
#   4. **빈 첨부가 거절되는가** — 0 바이트를 「첨부 없음」으로 보면 이미지 능력이
#      데모 데이터셋으로 흘러가 **남의 결과를 내 결과처럼** 돌려준다 (2026-09-02 회귀)
#   5. 첨부 **없는** 경로도 도는가
#
# ## 무엇을 주장하지 않나
#
#   **라우팅 정확도를 주장하지 않는다.** 이 스크립트는 **경로가 이어지는지**만 본다.
#   어떤 능력이 뽑히는지는 로컬 LLM 이 정하고 매번 같지 않다. 정확도는
#   `scripts/route_bench.py` 가 홀드아웃으로 따로 잰다.
#
# ## 종료 코드 — 배선과 라우팅을 **구분한다**
#
#   0  경로가 이어졌다
#   1  **배선이 끊겼다** — 서비스 없음 · 업로드 누락 · 증적 없음. 고칠 버그다
#   2  **라우팅이 빗나갔다** — 배선은 멀쩡한데 뽑힌 능력이 첨부를 못 다룬다.
#      LLM 이 매번 같지 않아 이것을 실패로 세면 검사가 흔들린다. **따로 센다.**
#
# 환경: CORE_URL · CAPREQ_URL · CAPREQ_PORT · CAPNET_API_KEY(강제 모드)
#       Ollama 와 살아 있는 스택이 필요하다 — CI 에 넣지 않는다 (route_bench 와 같은 부류).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
source "$root/scripts/lib/http.sh"
core="${CORE_URL:-http://127.0.0.1:8000}"
port="${CAPREQ_PORT:-8099}"
capreq="${CAPREQ_URL:-http://127.0.0.1:$port}"
ollama="${CAPREQ_OLLAMA_URL:-http://127.0.0.1:11434}"

started=""
tmp="$(mktemp -d)"
cleanup() {
  [ -n "$started" ] && kill "$started" 2>/dev/null || true
  rm -rf "$tmp"
}
trap cleanup EXIT

echo "== 0) 준비물 =="
ccurl -sf "$core/health" >/dev/null || { echo "Core 응답 없음: $core" >&2; exit 1; }
echo "  OK   Core        $core"
curl -sf -m 5 "$ollama/api/tags" >/dev/null || { echo "Ollama 응답 없음: $ollama" >&2; exit 1; }
echo "  OK   Ollama      $ollama"

if ! curl -sf -m 5 -o /dev/null "$capreq/"; then
  # 안 떠 있으면 우리가 띄운다. 띄운 것만 우리가 내린다.
  echo "  ..   capreq 가 없다 — 띄운다 (port $port)"
  ( cd "$root" && PYTHONPATH=capreq/src python3 -m capreq serve --port "$port" >"$tmp/capreq.log" 2>&1 & echo $! > "$tmp/pid" )
  started="$(cat "$tmp/pid")"
  for _ in $(seq 1 30); do
    curl -sf -m 2 -o /dev/null "$capreq/" && break
    sleep 1
  done
  curl -sf -m 5 -o /dev/null "$capreq/" || {
    echo "capreq 가 안 뜬다 — 의존성을 확인한다 (pip install \"./capreq[server]\")" >&2
    tail -5 "$tmp/capreq.log" >&2 || true
    exit 1
  }
fi
echo "  OK   capreq      $capreq"

echo
echo "== 1) capreq 가 Core 의 살아 있는 카탈로그를 읽는가 =="
curl -sf -m 20 "$capreq/api/capabilities" > "$tmp/caps.json" || {
  echo "카탈로그를 못 읽는다 — capreq→Core 배선이 끊겼다" >&2; exit 1; }
ccurl -sf "$core/v1/capabilities" > "$tmp/core_caps.json"
python3 - "$tmp/caps.json" "$tmp/core_caps.json" <<'PY'
import json, sys
seen = {(c["code"], c["version"]) for c in json.load(open(sys.argv[1]))["items"]}
live = {(c["code"], c["version"]) for c in json.load(open(sys.argv[2]))["items"]}
if not seen:
    raise SystemExit("capreq 가 능력을 하나도 못 봤다")
missing = sorted(live - seen)
if missing:
    raise SystemExit(f"Core 에 있는데 capreq 가 못 보는 것 {len(missing)}개: {missing[:5]}")
print(f"  OK   {len(seen)}종 · Core 와 같다 (정적 사본이 아니다)")
PY

echo
echo "== 2) 문장 + 첨부 → 라우팅 → Core 중개 업로드 → 완주 =="
printf '문의: ops@example.dev 로 연락 주세요. 서버는 10.0.0.7 입니다.\n' > "$tmp/in.txt"
echo "  ..   로컬 LLM 이 답할 때까지 기다린다 (CPU 에서는 분 단위다)"
curl -sf -m 600 -X POST "$capreq/api/chat" \
  -F 'message=이 글에서 이메일이랑 IP 주소를 찾아줘' \
  -F 'execute=true' -F 'wait=true' \
  -F "file=@$tmp/in.txt;type=text/plain" > "$tmp/chat.json" || {
    echo "/api/chat 이 실패했다 — 배선" >&2; exit 1; }

route_miss=0
python3 - "$tmp/chat.json" "$tmp/caps.json" <<'PY' || route_miss=$?
import json, sys
d = json.load(open(sys.argv[1]))
caps = {(c["code"], c["version"]) for c in json.load(open(sys.argv[2]))["items"]}

if not d.get("ok"):
    raise SystemExit("라우터가 답을 못 냈다 — 배선")
code, ver = d.get("capability_code"), d.get("capability_version")
if (code, ver) not in caps:
    raise SystemExit(f"카탈로그에 없는 능력을 골랐다: {code}@{ver}")
print(f"  OK   라우팅      {code}@{ver} (confidence={d.get('confidence')})")

# **D8′ 의 핵심.** 파일이 Core 를 거쳤다는 증거다. 없으면 자유 업로드거나 버려진 것이다.
if not d.get("input_id"):
    raise SystemExit("input_id 가 없다 — 첨부가 Core 를 거치지 않았다 (7936a0f 가 그 버그였다)")
print(f"  OK   Core 중개   input_id={d['input_id']}")

if not d.get("task_id"):
    raise SystemExit("task_id 가 없다 — 작업이 안 만들어졌다")
status = d.get("task_status")
if status != "COMPLETED":
    # 배선은 이어졌다. 뽑힌 능력이 이 첨부를 못 다뤘을 뿐이다.
    print(f"  MISS 라우팅    {code}@{ver} 로 갔고 상태가 {status} 다: {d.get('execution_message')}")
    raise SystemExit(2)
res = d.get("result") or {}
if not isinstance(res, dict) or not res:
    raise SystemExit("완주했는데 결과가 비어 있다")
print(f"  OK   완주        task={d['task_id']} · 결과 칸 {sorted(res)}")
PY
[ "$route_miss" = "1" ] && exit 1

echo
echo "== 3) 증적 조회 (Core 가 기록한 것) =="
taskId=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["task_id"])' "$tmp/chat.json")
ccurl -sf "$core/v1/tasks/$taskId" > "$tmp/task.json" || {
  echo "작업 증적을 못 읽는다 — 배선" >&2; exit 1; }
python3 - "$tmp/task.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
a = d.get("assignment")
if not a:
    raise SystemExit("assignment 가 없다 — 어디서 돌았는지 답할 수 없다")
print("  증적: assignment=%s node=%s agent=%s status=%s" % (a["id"], a["node_id"], a["agent_id"], a["status"]))
print("  경계: 신뢰도메인 task=%s -> node=%s · 티어 capability=%s <= node_max=%s"
      % (a["task_trust_domain"], a["node_trust_domain"], a["capability_tier"], a["node_tier_max"]))
PY

echo
echo "== 4) 빈 첨부는 거절되는가 (회귀) =="
# **이 자리가 비어 있어서 결함이 살아 있었다 (2026-09-02).** 0 바이트 파일을 붙이면
# `file_bytes` 가 `b""` 라 「첨부 없음」과 같아졌고, 이미지 능력은 allowlist 데모
# 데이터셋으로 흘러가 **남의 결과를 사용자 파일의 결과처럼** 돌려줬다.
# 단위 검사는 가짜 Core 를 쓴다 — 살아 있는 스택에서도 막히는지는 여기서만 본다.
: > "$tmp/empty.txt"
curl -sf -m 600 -X POST "$capreq/api/chat" \
  -F 'message=위성 사진 종류를 판별해줘' \
  -F 'execute=true' -F 'wait=true' \
  -F "file=@$tmp/empty.txt;type=image/png" > "$tmp/empty.json" || {
    echo "/api/chat 이 실패했다 — 배선" >&2; exit 1; }
python3 - "$tmp/empty.json" <<'EMPTYCASE'
import json, sys
d = json.load(open(sys.argv[1]))
if d.get("ok"):
    raise SystemExit(f"빈 첨부가 통과했다: {d.get('capability_code')} · {d.get('execution_message')}")
if d.get("task_id") or d.get("input_id"):
    raise SystemExit("빈 첨부로 작업이 만들어졌다 — 데모 데이터가 대신 돌았을 수 있다")
if "비어" not in (d.get("reason") or ""):
    raise SystemExit(f"거절 이유가 빈 파일을 가리키지 않는다: {d.get('reason')!r}")
print(f"  OK   거절        {d['reason']}")
EMPTYCASE

echo
echo "== 5) 첨부 없는 경로 =="
curl -sf -m 600 -X POST "$capreq/api/chat" \
  -F 'message=위성 사진 종류를 판별해줘' -F 'execute=false' > "$tmp/noatt.json" || {
    echo "첨부 없는 /api/chat 이 실패했다 — 배선" >&2; exit 1; }
python3 - "$tmp/noatt.json" "$tmp/caps.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
caps = {(c["code"], c["version"]) for c in json.load(open(sys.argv[2]))["items"]}
if d.get("ok") and (d.get("capability_code"), d.get("capability_version")) in caps:
    print(f"  OK   라우팅만  {d['capability_code']}@{d['capability_version']} · 실행 안 함")
elif d.get("rejected") or not d.get("ok"):
    # 미매칭도 정상 화면이다 — 없는 능력을 지어내지 않는 것이 맞는 동작이다.
    print("  OK   미매칭    능력을 지어내지 않았다")
else:
    raise SystemExit(f"카탈로그 밖 능력을 골랐다: {d.get('capability_code')}")
PY

echo
if [ "$route_miss" = "2" ]; then
  echo "배선은 이어졌다. 다만 이번 라우팅이 빗나갔다 (exit 2) — 정확도는 route_bench 가 잰다."
  exit 2
fi
echo "제품 입구가 이어졌다 — 문장과 파일이 Core 를 거쳐 승인된 Node 에서 돌고 증적이 남았다."
echo "라우팅 정확도는 주장하지 않는다. 이 스크립트는 경로만 본다."
