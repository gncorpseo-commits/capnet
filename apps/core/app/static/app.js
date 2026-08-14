// CapNet 최소 UI 공용 — 관리 키 보관과 호출 래퍼.
//
// ## 키는 브라우저에만 산다
//
// `sessionStorage` 에 둔다. 서버로 보내는 것은 **요청 헤더뿐**이고, Core 는 저장하지 않는다.
// `localStorage` 가 아니라 `sessionStorage` 인 것은 의도다 — **탭을 닫으면 사라진다.**
// 공용 PC 에서 화면만 보고 일어서도 키가 남지 않는다. 새로고침에는 살아남는다.
//
// URL 에 키를 넣지 않는다. 쿼리스트링은 서버 접근 로그·브라우저 기록·Referer 로 샌다.
//
// ## 소진 경로는 키를 쓰지 않는다
//
// 초대받은 사람에게는 관리 키가 없다. `apiNoKey()` 는 어떤 경우에도 키를 붙이지 않는다 —
// 실수로 `api()` 를 쓰면 없는 키를 붙이려다 조용히 다른 동작이 된다.

const KEY_NAME = "capnet.apiKey";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function getKey() {
  try { return sessionStorage.getItem(KEY_NAME) || ""; } catch { return ""; }
}
function setKey(v) {
  try { v ? sessionStorage.setItem(KEY_NAME, v) : sessionStorage.removeItem(KEY_NAME); } catch { /* 저장 불가 브라우저 */ }
}
function keyPrefix(v) {
  const k = v || getKey();
  return k ? k.split(".")[0] : "";
}

async function _send(path, opts, headers) {
  const r = await fetch(path, { ...(opts || {}), headers: { ...headers, ...((opts || {}).headers || {}) } });
  const text = await r.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = { detail: text }; }
  if (!r.ok) {
    const detail = typeof body?.detail === "string" ? body.detail : JSON.stringify(body?.detail ?? body);
    const err = new Error(detail);
    err.status = r.status;
    throw err;
  }
  return body;
}

// 관리 API. 키가 있으면 붙인다. 강제가 꺼진 데모에서는 키 없이도 돈다.
async function api(path, opts) {
  const k = getKey();
  return _send(path, opts, k ? { Authorization: "CapNet-Key " + k } : {});
}

// 초대 소진 전용. **절대 관리 키를 붙이지 않는다.**
async function apiInvite(path, opts, token) {
  return _send(path, opts, token ? { Authorization: "CapNet-Invite " + token } : {});
}

// 키 없이 부르는 공개 조회 (능력 카탈로그 등).
async function apiNoKey(path, opts) {
  return _send(path, opts, {});
}

// 화면 위쪽에 키 입력줄을 붙인다. 강제 모드에서 UI 를 쓰려면 이게 필요하다.
function mountKeyBar(el) {
  const node = typeof el === "string" ? $(el) : el;
  if (!node) return;
  node.innerHTML = `
    <div class="note keybar">
      <label for="k-input">관리 API 키</label>
      <input id="k-input" type="password" autocomplete="off" spellcheck="false"
             placeholder="ck_xxxxxxxx.yyy — 강제 모드에서 필요">
      <button id="k-save" type="button">저장</button>
      <button id="k-clear" type="button" class="secondary">지우기</button>
      <span id="k-state" class="muted"></span>
    </div>`;
  const state = $("k-state");
  const paint = () => {
    const p = keyPrefix();
    state.textContent = p ? `이 탭에 보관 중 · ${p}` : "키 없음 — 강제 모드면 401 이 난다";
  };
  $("k-save").onclick = () => { setKey($("k-input").value.trim()); $("k-input").value = ""; paint(); };
  $("k-clear").onclick = () => { setKey(""); paint(); };
  paint();
}
