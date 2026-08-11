#!/usr/bin/env python3
"""부하·지연 실측 (측정 없이 주장 없음).

    python3 scripts/load_probe.py --tasks 30
    python3 scripts/load_probe.py --tasks 60 --concurrency 12 --json out.json

## 왜 있는가

이 시스템의 성능은 **한 번도 측정된 적이 없다.** 처리량도, 배정 지연도, 동시 부하에서
무엇이 먼저 막히는지도 모른다. 그런데 「기기를 묶어 일을 시킨다」가 제품의 주장이다.

이 프로브는 숫자를 만든다. 좋게 보이려는 게 아니라 **한계를 드러내려는** 것이다.

## 무엇을 재나

| 지표 | 뜻 |
|------|-----|
| submit → assigned | Task 를 넣고 **배정**될 때까지 (Core 워커 몫) |
| assigned → completed | 배정 후 **실행**까지 (Node 폴링 + 추론 몫) |
| end-to-end | 제출부터 완료까지 |
| throughput | 완료/초 |

두 구간을 나누는 게 핵심이다 — 느리면 **어디가** 느린지 알아야 한다.

## 읽는 법

Core 워커는 한 번에 **한 건**씩 배정하고, 배정할 게 없으면 `CORE_WORKER_INTERVAL_S` 만큼 쉰다.
Node 는 `NODE_POLL_INTERVAL_S` 주기로 자기 몫을 가져간다.
그래서 이 둘이 **구조적 상한**이다 — 측정값이 그 상한에 붙어 있으면 병목은 코드가 아니라 주기다.

읽기 전용이 아니다 — Task 를 실제로 만든다. **일회용 스택에서 돌린다.**
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request

CORE = os.environ.get("CORE_URL", "http://127.0.0.1:8000").rstrip("/")
API_KEY = os.environ.get("CAPNET_API_KEY")


def _req(path: str, body: dict | None = None, method: str = "GET") -> dict:
    url = f"{CORE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"content-type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"CapNet-Key {API_KEY}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


class Result:
    __slots__ = ("case", "submitted", "assigned", "completed", "error", "dummy", "node")

    def __init__(self, case: str) -> None:
        self.case = case
        self.submitted = self.assigned = self.completed = None
        self.error: str | None = None
        self.dummy = False
        self.node: str | None = None


def run_one(case_id: str, cap_code: str, cap_ver: int, timeout_s: float) -> Result:
    r = Result(case_id)
    t0 = time.perf_counter()
    try:
        task = _req(
            "/v1/tasks",
            {
                "datasetId": "eurosat-rgb",
                "caseId": case_id,
                "capability_code": cap_code,
                "capability_version": cap_ver,
            },
            "POST",
        )
    except Exception as exc:  # 제출 자체가 막히면 그것도 결과다
        r.error = f"submit: {exc}"
        return r
    r.submitted = t0
    task_id = task["id"]

    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        try:
            t = _req(f"/v1/tasks/{task_id}")
        except Exception as exc:
            r.error = f"poll: {exc}"
            return r
        if r.assigned is None and t.get("assignment"):
            r.assigned = time.perf_counter()
            r.node = str(t["assignment"].get("node_id"))
        if t["status"] in ("COMPLETED", "FAILED"):
            r.completed = time.perf_counter()
            if t["status"] == "FAILED":
                r.error = "task FAILED"
            else:
                res = t.get("result_ref")
                res = json.loads(res) if isinstance(res, str) else (res or {})
                r.dummy = bool(res.get("dummy"))
            return r
        time.sleep(0.15)
    r.error = f"timeout after {timeout_s}s"
    return r


def pct(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    k = min(len(s) - 1, int(round((len(s) - 1) * p)))
    return s[k]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=int, default=30)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--capability", default="image.classify")
    ap.add_argument("--version", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--json", help="결과를 JSON 으로 저장")
    args = ap.parse_args()

    try:
        _req("/health")
    except Exception as exc:
        print(f"Core 응답 없음: {CORE} ({exc})", file=sys.stderr)
        return 1

    cases = [f"ic1-{(i % 40) + 1:04d}" for i in range(args.tasks)]
    results: list[Result] = []
    lock = threading.Lock()
    idx = threading.Semaphore(args.concurrency)

    def worker(case: str) -> None:
        with idx:
            r = run_one(case, args.capability, args.version, args.timeout)
        with lock:
            results.append(r)

    print(f"부하 프로브 — {CORE}")
    print(f"  task {args.tasks}건 · 동시 {args.concurrency} · {args.capability}@{args.version}")
    if not API_KEY:
        print("  (API 키 없음 — 강제 모드면 401 이 난다)")

    wall0 = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(c,)) for c in cases]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall = time.perf_counter() - wall0

    ok = [r for r in results if r.error is None]
    bad = [r for r in results if r.error is not None]
    dummies = [r for r in ok if r.dummy]

    to_assign = [r.assigned - r.submitted for r in ok if r.assigned and r.submitted]
    to_exec = [r.completed - r.assigned for r in ok if r.completed and r.assigned]
    e2e = [r.completed - r.submitted for r in ok if r.completed and r.submitted]

    def line(name: str, xs: list[float]) -> None:
        if not xs:
            print(f"  {name:<22} (없음)")
            return
        print(f"  {name:<22} p50={statistics.median(xs):6.2f}s  "
              f"p95={pct(xs, 0.95):6.2f}s  max={max(xs):6.2f}s")

    print()
    print("== 결과 ==")
    print(f"  완료 {len(ok)}/{len(results)} · 실패 {len(bad)} · dummy {len(dummies)}")
    print(f"  벽시계 {wall:.1f}s · 처리량 {len(ok) / wall:.2f} 건/초")
    print()
    line("제출→배정", to_assign)
    line("배정→완료", to_exec)
    line("제출→완료(e2e)", e2e)

    nodes: dict[str, int] = {}
    for r in ok:
        if r.node:
            nodes[r.node] = nodes.get(r.node, 0) + 1
    if nodes:
        print()
        print("  기기별 배정:")
        for n, c in sorted(nodes.items(), key=lambda kv: -kv[1]):
            print(f"    {n[:8]}… {c}건")

    if bad:
        print()
        print("  실패 사유:")
        seen: dict[str, int] = {}
        for r in bad:
            key = (r.error or "")[:70]
            seen[key] = seen.get(key, 0) + 1
        for k, c in sorted(seen.items(), key=lambda kv: -kv[1]):
            print(f"    {c:3d}× {k}")

    if dummies:
        print()
        print(f"  !! dummy {len(dummies)}건 — 실제 추론이 아니다")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "core": CORE,
                    "tasks": args.tasks,
                    "concurrency": args.concurrency,
                    "wall_s": wall,
                    "completed": len(ok),
                    "failed": len(bad),
                    "dummy": len(dummies),
                    "throughput_per_s": (len(ok) / wall) if wall else 0,
                    "to_assign_p50": statistics.median(to_assign) if to_assign else None,
                    "to_assign_p95": pct(to_assign, 0.95) if to_assign else None,
                    "to_exec_p50": statistics.median(to_exec) if to_exec else None,
                    "e2e_p50": statistics.median(e2e) if e2e else None,
                    "e2e_p95": pct(e2e, 0.95) if e2e else None,
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )
        print(f"\n  JSON: {args.json}")

    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
