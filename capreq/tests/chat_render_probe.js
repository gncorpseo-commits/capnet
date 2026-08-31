// `chat.html` 의 렌더러를 **실제로 실행해** 만들어진 DOM 을 본다.
//
// ## 왜 있는가
//
// #107 · #112 · #118 · #128 — 네 번 연속으로 「브라우저 렌더링은 못 봤다」고 적었다.
// 이 저장소에서 **가장 오래 미확인**으로 남은 자리이고, 거기서 결함이 **두 번** 나왔다:
// #118 은 새 결과 칸이 원시 JSON 으로 새고 있었고, #128 은 자른 사실 고지가 빠질 뻔했다.
//
// 옆 파일 `test_chat_html_unit.py` 는 **문자열 검사**라 「반쯤 지운 렌더러」를 통과시킨다 —
// 그 한계를 그 파일이 스스로 적어 뒀다. 여기는 **실행**이라 그 구멍을 막는다.
//
// ## 왜 Playwright 를 쓰지 않나
//
// `chat.html` 이 실제로 쓰는 브라우저 API 가 적다 (실측):
//
//     document.* 12 · fetch 4 · addEventListener 3 · FormData 1 · setTimeout 1
//     window.*    0 · localStorage 0
//
// 그래서 아래 **최소 스텁**이면 `<script>` 를 통째로 실행할 수 있다. **npm 패키지 0.**
//
// ## 무엇을 여전히 못 보나
//
// 실제 브라우저의 **CSS·레이아웃**과 **사용자 상호작용**(드래그앤드롭·폼 제출).
// 그래서 이 파일이 통과해도 **「브라우저에서 봤다」고 쓰지 않는다** —
// **「렌더러를 실행해 DOM 을 봤다」**가 맞는 말이다.

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
    children: [],
    style: {},
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); },
      remove(c) { this._s.delete(c); },
      contains(c) { return this._s.has(c); },
    },
    appendChild(c) { this.children.push(c); return c; },
    // `renderSummary` 가 **이 값으로** 최종 append 를 결정한다. 스텁에 없으면
    // undefined → falsy → 아무것도 안 그려진다 (처음 돌렸을 때 24종이 그렇게 실패했다).
    get childElementCount() { return this.children.length; },
    addEventListener() {},
    set textContent(v) { this._text = String(v); this.children = []; },
    get textContent() {
      // 브라우저처럼 자손 텍스트를 이어 붙인다 — 단언이 트리 전체를 볼 수 있게.
      return this._text + this.children.map((c) => c.textContent).join("");
    },
  };
}

const byId = {};
for (const id of ["log", "meta", "file", "attachName", "clearFile", "dropzone", "f", "q", "ex"]) {
  byId[id] = makeNode("div");
}
byId.file.files = [];
byId.file.value = "";

global.document = {
  createElement: makeNode,
  getElementById: (id) => byId[id] || makeNode("div"),
};

// 최상위에서 `refreshMeta()` 가 한 번 호출된다. 네트워크를 타지 않게 막는다.
global.fetch = () => Promise.resolve({ json: () => Promise.resolve({}) });
global.FormData = function FormData() { this.append = () => {}; };

// ------------------------------------------------------- chat.html 실행

const HTML = path.join(__dirname, "..", "src", "capreq", "static", "chat.html");
const html = fs.readFileSync(HTML, "utf8");
const script = html.split("<script>")[1].split("</script>")[0];

// `renderSummary` 등은 함수 선언이라 이 스코프에 뜬다.
const load = new Function(script + "\nreturn { renderSummary, renderRouting, renderExec, statusBadge };");
const ui = load();

// ------------------------------------------------------------- 단언 도구

let failed = 0;
let passed = 0;

function check(ok, name, detail) {
  if (ok) { passed += 1; console.log("  OK   " + name); }
  else { failed += 1; console.log("  FAIL " + name + (detail ? " — " + detail : "")); }
}

function render(summary) {
  const box = makeNode("div");
  ui.renderSummary(box, summary);
  return box;
}

function textOf(box) { return box.textContent; }

function countTags(node, tag, acc) {
  acc = acc || { n: 0 };
  if (node.tagName === tag) acc.n += 1;
  node.children.forEach((c) => countTags(c, tag, acc));
  return acc.n;
}

// ------------------------------------------------- 능력 10종의 결과 모양
//
// 서버 `summarize_result` 가 내는 **요약 모양**을 그대로 적는다.
// (요약기 자체는 `test_results_unit.py` 가 본다 — 여기는 그 결과를 화면이 그리는가다.)

const SHAPES = {
  "image.classify / text.classify": { label: "annual_crop", confidence: 0.9836 },
  "text.ner": { entities: [{ label: "email", start: 8, end: 23, text: "ops@example.dev" }] },
  "text.extract": {
    fields: { items: [{ key: "Ticket", value: "INC-4021", line: 0 }], count: 1, truncated: false },
  },
  "text.rank": {
    ranking: {
      items: [{ rank: 1, line: 3, text: "인덱스 없이 느린 쿼리", score: 0.75, overlap: ["느린", "쿼리"] }],
      count: 1, truncated: false, query: "느린 쿼리 인덱스",
    },
  },
  "safety.pii": {
    pii: {
      items: [{ label: "email", start: 3, end: 18, text: "o**@e******.dev" }],
      count: 1, truncated: false, patterns_checked: ["card_like", "email"],
    },
  },
  "text.embed / image.embed / timeseries.forecast": {
    vector: { name: "vector", dim: 64, head: [0.1, 0.2], truncated: true },
  },
  "table.extract": {
    table: {
      columns: [{ index: 0, type: "int", support: 3 }], rows: [["1"]],
      row_count: 1, truncated: false, header_detected: true,
    },
  },
};

console.log("== 능력이 내는 결과 모양마다 실제로 그려지는가 ==");
for (const [name, summary] of Object.entries(SHAPES)) {
  const box = render(summary);
  check(box.children.length > 0, name + " — 무언가 그려진다");
}

console.log("\n== 그린 내용이 맞는가 ==");

{
  const t = textOf(render(SHAPES["text.ner"]));
  check(t.includes("엔티티 1건") && t.includes("ops@example.dev"), "text.ner — 엔티티 표에 값이 들어간다");
}
{
  const box = render(SHAPES["text.extract"]);
  check(countTags(box, "TABLE") === 1, "text.extract — 표를 만든다", "table 수=" + countTags(box, "TABLE"));
  check(textOf(box).includes("INC-4021"), "text.extract — 값이 그려진다");
}
{
  const t = textOf(render(SHAPES["text.rank"]));
  check(t.includes("느린 쿼리 인덱스"), "text.rank — 질의를 보여 준다");
  check(t.includes("0.7500"), "text.rank — score 를 4자리로 그린다");
  check(t.includes("뜻을 비교한 것이 아닙니다"), "text.rank — 점수를 관련도로 팔지 않는다");
}
{
  const t = textOf(render(SHAPES["table.extract"]));
  check(t.includes("헤더 감지"), "table.extract — 헤더 감지를 적는다");
}
{
  const t = textOf(render(SHAPES["text.embed / image.embed / timeseries.forecast"]));
  check(t.includes("dim=64"), "vector — 차원을 적는다");
  check(t.includes("…"), "vector — 자른 사실을 `…` 로 알린다");
}

console.log("\n== safety.pii — 빈 결과가 「깨끗하다」로 읽히면 안 된다 ==");
{
  const t = textOf(render(SHAPES["safety.pii"]));
  check(t.includes("찾아본 패턴"), "찾아본 패턴 목록을 먼저 그린다");
  check(t.includes("목록에 없는 것은 찾지 않았습니다"), "목록 밖은 「찾지 않았다」고 적는다");
  check(t.includes("o**@e******.dev"), "가려진 값을 그대로 그린다");
  check(!t.includes("ops@example.dev"), "화면이 가림을 되돌리지 않는다");
  check(t.includes("탐지가 아니라 참고"), "탐지가 아니라는 것을 화면이 말한다");
}
{
  const empty = { pii: { items: [], count: 0, truncated: false, patterns_checked: ["email"] } };
  const t = textOf(render(empty));
  check(t.includes("「없다」가 아니라"), "**빈 결과에도** 「없다가 아니다」를 적는다");
  check(t.includes("찾아본 패턴"), "빈 결과에도 찾아본 목록이 남는다");
}

console.log("\n== 자른 사실은 잘렸을 때만 말한다 ==");
{
  const cut = { fields: { items: [{ key: "k", value: "v", line: 0 }], count: 30, truncated: true } };
  check(textOf(render(cut)).includes("만 표시"), "truncated=true 면 고지가 붙는다");
  const whole = { fields: { items: [{ key: "k", value: "v", line: 0 }], count: 1, truncated: false } };
  check(!textOf(render(whole)).includes("만 표시"), "truncated=false 면 고지가 없다");
}

console.log("\n== 없는 칸은 그리지 않는다 ==");
{
  const box = render({});
  check(box.children.length === 0, "빈 요약은 아무것도 그리지 않는다", "children=" + box.children.length);
  const t = textOf(render({ label: "x" }));
  check(!t.includes("엔티티") && !t.includes("순위"), "라벨만 있으면 라벨만 그린다");
}
{
  // 계약이 모르는 칸은 **삼키지 않고** 「그 밖의 출력」으로 남아야 한다.
  const t = textOf(render({ other: { segments: [1, 2] } }));
  check(t.includes("그 밖의 출력"), "모르는 칸은 폴백으로 보인다");
}

console.log("\n== 라우팅·실행 줄 ==");
{
  const box = makeNode("div");
  ui.renderRouting(box, { ok: true, capability_code: "safety.pii", capability_version: 1, confidence: 0.93 });
  check(textOf(box).includes("safety.pii@1"), "능력 코드를 그린다");
  const miss = makeNode("div");
  ui.renderRouting(miss, { ok: false, reason: "확신 부족" });
  check(textOf(miss).includes("(미매칭)"), "못 고르면 「미매칭」이라고 적는다");
}
{
  const box = makeNode("div");
  ui.renderExec(box, "COMPLETED", "t-1", null, { node_id: "n-1", capability_tier: "M" });
  const t = textOf(box);
  check(t.includes("COMPLETED") && t.includes("node=n-1") && t.includes("tier=M"),
        "실행 줄에 상태와 배정 증적이 들어간다");
}

console.log("\n===== 결과: 통과 " + passed + " · 실패 " + failed + " =====");
if (failed) {
  console.log("렌더러가 서버 요약과 어긋났다.");
  process.exit(1);
}
console.log("렌더러를 실행해 DOM 을 봤다 — 브라우저에서 본 것은 아니다 (CSS·상호작용 제외).");
