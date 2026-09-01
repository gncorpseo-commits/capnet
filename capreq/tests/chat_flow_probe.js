// `chat.html` 의 **흐름**을 실행해 본다 — 폼 제출 → 라우팅 → 폴링 → 결과.
//
// ## 왜 있는가
//
// `chat_render_probe.js` 는 **렌더러 하나**를 호출한다. 여기는 **사용자가 보내기를 누른
// 뒤 벌어지는 전부**를 돌린다 — `onsubmit` → `fetch("/api/chat")` → `renderRouting` →
// `pollTask` → `renderSummary`.
//
// 그 경로에 검사가 없어서 생긴 일이 이미 있다. **#112 — 첨부가 제품 1호부터 한 번도
// 서버에 닿지 않았다.** 그때 고친 것은 서버 쪽(`isinstance`)이었고, **클라이언트가 파일을
// 실제로 `FormData` 에 담는지는 아무도 확인한 적이 없다.** 여기서 처음 본다.
//
// ## 무엇을 스텁하나
//
// `document` · `fetch` · `FormData` · `setTimeout`. **npm 패키지 0.**
// `setTimeout` 은 **즉시 실행**으로 바꾼다 — 폴링이 1초씩 자면 검사가 2분 걸린다.
//
// ## 여전히 못 보는 것
//
// 실제 브라우저의 **CSS·레이아웃**, 진짜 파일 선택기·드래그앤드롭의 **OS 상호작용**.
// 여기서 보는 것은 **「그 이벤트가 왔을 때 코드가 무엇을 하는가」**다.

"use strict";

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------- 최소 DOM

function makeNode(tag) {
  return {
    tagName: String(tag).toUpperCase(),
    className: "",
    _text: "",
    hidden: false,
    checked: false,
    value: "",
    children: [],
    style: {},
    scrollTop: 0,
    scrollHeight: 0,
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); },
      remove(c) { this._s.delete(c); },
      contains(c) { return this._s.has(c); },
    },
    appendChild(c) { this.children.push(c); return c; },
    get childElementCount() { return this.children.length; },
    addEventListener() {},
    set textContent(v) { this._text = String(v); this.children = []; },
    get textContent() {
      return this._text + this.children.map((c) => c.textContent).join("");
    },
  };
}

const byId = {};
for (const id of ["log", "meta", "file", "attachName", "clearFile", "dropzone", "f", "msg", "ex"]) {
  byId[id] = makeNode("div");
}
byId.file.files = [];
byId.ex.checked = true;

global.document = {
  createElement: makeNode,
  getElementById: (id) => byId[id] || makeNode("div"),
};

// 폴링이 실제로 자면 검사가 2분 걸린다. 즉시 깨운다.
global.setTimeout = (fn) => { fn(); return 0; };

global.FormData = function FormData() {
  this._parts = [];
  this.append = (k, v) => this._parts.push([k, v]);
  this.get = (k) => (this._parts.find((p) => p[0] === k) || [])[1];
  this.keys = () => this._parts.map((p) => p[0]);
};

// ------------------------------------------------------- 프로그램 가능한 fetch

let routes = {};      // URL 접두 → 응답을 만드는 함수
const calls = [];     // 무엇을 어떻게 불렀는지 기록

function reply(body, ok) {
  return Promise.resolve({ ok: ok !== false, statusText: "OK", json: () => Promise.resolve(body) });
}

global.fetch = (url, init) => {
  calls.push({ url: String(url), init: init || null });
  for (const prefix of Object.keys(routes)) {
    if (String(url).startsWith(prefix)) return routes[prefix](String(url), init);
  }
  return reply({});
};

// ------------------------------------------------------- chat.html 실행

const HTML = path.join(__dirname, "..", "src", "capreq", "static", "chat.html");
const script = fs.readFileSync(HTML, "utf8").split("<script>")[1].split("</script>")[0];
// `setFile` 은 첨부 상태를 만드는 유일한 길이라 같이 꺼낸다.
new Function(script + "\nglobalThis.__setFile = setFile;\nglobalThis.__resetCaps = () => { knownCaps = null; };")();
const knownCapsReset = () => globalThis.__resetCaps();

const onsubmit = byId.f.onsubmit;

// ------------------------------------------------------------- 단언 도구

let failed = 0;
let passed = 0;

function check(ok, name, detail) {
  if (ok) { passed += 1; console.log("  OK   " + name); }
  else { failed += 1; console.log("  FAIL " + name + (detail ? " — " + detail : "")); }
}

async function submit({ message, file, execute }) {
  byId.log.children = [];
  calls.length = 0;
  byId.msg.value = message === undefined ? "안녕" : message;
  byId.ex.checked = execute !== false;
  globalThis.__setFile(file || null);
  await onsubmit({ preventDefault() {} });
  // 마지막 말풍선 = 봇 응답
  return byId.log.children[byId.log.children.length - 1];
}

function chatPost(body, ok) { routes["/api/chat"] = () => reply(body, ok); }

function taskStates(states) {
  let i = 0;
  routes["/api/tasks/"] = () => reply(states[Math.min(i++, states.length - 1)]);
}

const DONE_OK = {
  ok: true, done: true, status: "COMPLETED",
  assignment: { node_id: "n-1", agent_id: "a-1", node_trust_domain: "team", capability_tier: "M" },
  result: { label: "annual_crop", confidence: 0.98 },
};

// ------------------------------------------------------------------ 검사

async function main() {
  console.log("== 보내기 → 라우팅 → 폴링 → 결과 ==");
  {
    chatPost({ ok: true, capability_code: "image.classify", capability_version: 1,
               confidence: 0.93, task_id: "t-1", task_status: "QUEUED" });
    taskStates([{ ok: true, done: false, status: "RUNNING" }, DONE_OK]);
    const bubble = await submit({ message: "이 사진 분류해줘" });
    const t = bubble.textContent;
    check(t.includes("image.classify@1"), "라우팅 결과를 그린다");
    check(t.includes("COMPLETED"), "폴링이 종결 상태까지 간다");
    check(t.includes("annual_crop"), "결과 요약을 그린다");
    check(t.includes("node=n-1") && t.includes("tier=M"), "배정 증적을 그린다");
    check(bubble.className.includes("ok"), "성공이면 말풍선이 ok", bubble.className);
    const posted = calls.filter((c) => c.url === "/api/chat");
    check(posted.length === 1, "/api/chat 을 한 번만 부른다", "횟수=" + posted.length);
  }

  console.log("\n== 첨부 — #112 가 서버에서 고친 것의 클라이언트 짝 ==");
  {
    chatPost({ ok: true, capability_code: "text.ner", capability_version: 1,
               confidence: 1.0, task_id: "t-2", task_status: "QUEUED" });
    taskStates([DONE_OK]);
    const file = { name: "log.txt", type: "text/plain" };
    await submit({ message: "이메일 찾아줘", file });
    const post = calls.find((c) => c.url === "/api/chat");
    check(post && post.init && post.init.body instanceof global.FormData,
          "첨부가 있으면 FormData 로 보낸다");
    const fd = post.init.body;
    check(fd.get("file") === file, "**파일이 실제로 실린다** (#112 의 클라이언트 짝)");
    check(fd.get("wait") === "false", "브라우저는 wait=false 로 보내고 폴링한다");
    check(fd.get("message") === "이메일 찾아줘", "메시지도 같이 실린다");
    check(!(post.init.headers && post.init.headers["content-type"]),
          "FormData 에 content-type 을 손으로 붙이지 않는다 (boundary 가 깨진다)");
  }
  {
    // 첨부 + 실행 성공이면 첨부가 비워져야 한다 — 같은 파일이 두 번 가지 않게.
    chatPost({ ok: true, capability_code: "text.ner", capability_version: 1,
               confidence: 1.0, task_id: "t-3", task_status: "QUEUED" });
    taskStates([DONE_OK]);
    await submit({ message: "다시", file: { name: "a.txt", type: "text/plain" } });
    check(byId.attachName.textContent === "첨부 없음", "성공 뒤 첨부가 비워진다",
          byId.attachName.textContent);
  }

  console.log("\n== 첨부가 없으면 JSON 으로 보낸다 ==");
  {
    chatPost({ ok: true, capability_code: "text.rank", capability_version: 1,
               confidence: 0.8, task_id: "t-4", task_status: "QUEUED" });
    taskStates([DONE_OK]);
    await submit({ message: "줄 세워줘" });
    const post = calls.find((c) => c.url === "/api/chat");
    check(post.init.headers["content-type"] === "application/json", "JSON 헤더를 붙인다");
    const body = JSON.parse(post.init.body);
    check(body.wait === false, "wait=false");
    check(body.execute === true, "실행 체크 상태를 보낸다");
  }

  console.log("\n== 실패를 성공처럼 그리지 않는다 ==");
  {
    chatPost({ ok: true, capability_code: "text.ner", capability_version: 1, confidence: 0.9,
               task_id: "t-5", task_status: "FAILED", execution_ok: false,
               execution_message: "Node 가 거절했다", result: null });
    const bubble = await submit({ message: "실패" });
    check(bubble.textContent.includes("FAILED"), "FAILED 를 그린다");
    check(bubble.textContent.includes("Node 가 거절했다"), "실패 사유를 그린다");
    check(bubble.className.includes("bad"), "말풍선이 bad", bubble.className);
  }
  {
    chatPost({ detail: "capability 없음" }, false);   // HTTP 4xx
    const bubble = await submit({ message: "없는 능력" });
    check(bubble.textContent.startsWith("(오류)"), "HTTP 오류를 오류로 적는다", bubble.textContent);
    check(bubble.textContent.includes("capability 없음"), "detail 을 그대로 보여 준다");
    check(bubble.className.includes("bad"), "말풍선이 bad");
  }
  {
    chatPost({ ok: true, capability_code: "text.ner", capability_version: 1, confidence: 0.9,
               task_id: "t-6", task_status: "QUEUED" });
    routes["/api/tasks/"] = () => reply({ ok: false, error: "Task 조회 실패 HTTP 404" });
    const bubble = await submit({ message: "조회 실패" });
    check(bubble.textContent.includes("Task 조회 실패"), "상태 조회 실패를 그대로 적는다");
    check(bubble.className.includes("bad"), "말풍선이 bad");
  }

  console.log("\n== 보낼 것이 없으면 보내지 않는다 ==");
  {
    byId.log.children = [];
    calls.length = 0;
    byId.msg.value = "";
    globalThis.__setFile(null);
    await onsubmit({ preventDefault() {} });
    check(calls.length === 0, "빈 입력이면 요청을 만들지 않는다", "호출=" + calls.length);
    check(byId.log.children.length === 0, "말풍선도 만들지 않는다");
  }

  console.log("\n== 미매칭 — 막다른 골목에 두지 않는다 ==");
  {
    routes["/api/capabilities"] = () => reply({ items: [
      { code: "text.ner", version: 1, name: "structural text ner", description: "타입 span 을 찾는다" },
      { code: "safety.pii", version: 1, name: "pii pattern hint", description: "선언한 패턴의 자리를 가려서 알려 준다" },
    ] });
    chatPost({ ok: false, reason: "확신 부족", capability_code: null, capability_version: null,
               confidence: 0.1 });
    const bubble = await submit({ message: "?????" });
    const t = bubble.textContent;
    check(t.includes("(미매칭)"), "미매칭을 적는다");
    check(t.includes("확신 부족"), "이유를 적는다");
    check(!t.includes("COMPLETED"), "task 가 없으면 실행 줄을 그리지 않는다");
    check(t.includes("지금 할 수 있는 일 2가지"), "**할 수 있는 것을 보여 준다**");
    check(t.includes("text.ner@1") && t.includes("safety.pii@1"), "능력 목록이 실제로 그려진다");
    check(calls.some((c) => c.url === "/api/capabilities"), "카탈로그를 서버에서 받는다");
  }
  {
    // 두 번째 미매칭에서 또 받아 오지 않는다 (한 번 받아 두고 쓴다).
    calls.length = 0;
    chatPost({ ok: false, reason: "또 모름", capability_code: null, capability_version: null });
    await submit({ message: "?????" });
    check(!calls.some((c) => c.url === "/api/capabilities"), "두 번째부터는 다시 안 받는다");
  }
  {
    // 매칭됐을 때는 목록을 들이밀지 않는다 — 방해가 된다.
    chatPost({ ok: true, capability_code: "text.ner", capability_version: 1,
               confidence: 0.9, task_id: "t-7", task_status: "QUEUED" });
    taskStates([DONE_OK]);
    const bubble = await submit({ message: "이메일 찾아줘" });
    check(!bubble.textContent.includes("지금 할 수 있는 일"), "매칭되면 목록을 안 보여 준다");
  }
  {
    // 카탈로그를 못 받아도 화면이 무너지지 않는다 — 그리고 **못 받았다고 말한다.**
    knownCapsReset();
    routes["/api/capabilities"] = () => Promise.reject(new Error("Core 없음"));
    chatPost({ ok: false, reason: "확신 부족", capability_code: null, capability_version: null });
    const bubble = await submit({ message: "?????" });
    check(bubble.textContent.includes("(미매칭)"), "카탈로그를 못 받아도 미매칭은 그린다");
    check(!bubble.textContent.includes("지금 할 수 있는 일"), "0가지라고 말하지 않는다");
    check(bubble.textContent.includes("불러오지 못했"),
          "**못 받았다고 말한다** — 아무것도 안 그리면 「할 수 있는 일이 없다」로 읽힌다");
  }
  {
    // **실패를 캐시하지 않는다.** `[]` 는 JS 에서 truthy 라, 예전에는 한 번 실패하면
    // 새로 고칠 때까지 영영 다시 안 받았다.
    calls.length = 0;
    routes["/api/capabilities"] = () => reply({ items: [
      { code: "text.ner", version: 1, name: "structural text ner", description: "타입 span" },
    ] });
    chatPost({ ok: false, reason: "또 모름", capability_code: null, capability_version: null });
    const bubble = await submit({ message: "?????" });
    check(calls.some((c) => c.url === "/api/capabilities"), "**실패한 뒤에는 다시 받아 본다**");
    check(bubble.textContent.includes("지금 할 수 있는 일 1가지"), "복구되면 그때는 그린다");
  }

  console.log("\n===== 결과: 통과 " + passed + " · 실패 " + failed + " =====");
  if (failed) {
    console.log("클라이언트 흐름이 어긋났다.");
    process.exit(1);
  }
  console.log("흐름을 실행해 봤다 — 실제 브라우저·파일 선택기는 아니다 (CSS·OS 상호작용 제외).");
}

main().catch((e) => { console.error(e); process.exit(1); });
