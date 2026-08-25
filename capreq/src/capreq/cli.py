from __future__ import annotations

import argparse
import json
import sys

from capreq.adapters.capnet import CapNetAdapter
from capreq.adapters.static import NoExecute, StaticCatalog
from capreq.config import api_key, core_url, ollama_model, ollama_url
from capreq.ollama import OllamaClient
from capreq.router import CapabilityRouter


def _build_router(
    *,
    core: str | None,
    catalog_json: str | None,
    with_executor: bool,
) -> CapabilityRouter:
    llm = OllamaClient(base_url=ollama_url(), model=ollama_model())
    if catalog_json:
        catalog = StaticCatalog.from_json_file(catalog_json)
        executor = None if not with_executor else NoExecute()
        return CapabilityRouter(catalog=catalog, llm=llm, executor=executor)
    if not core:
        raise SystemExit("--core 또는 --catalog-json 이 필요하다")
    adapter = CapNetAdapter(core, api_key=api_key())
    return CapabilityRouter(
        catalog=adapter,
        llm=llm,
        executor=adapter if with_executor else None,
    )


def cmd_route(args: argparse.Namespace) -> int:
    router = _build_router(
        core=args.core,
        catalog_json=args.catalog_json,
        with_executor=args.execute,
    )
    decision, exe = router.route_and_maybe_execute(
        args.text,
        dataset_id=args.dataset,
        case_id=args.case,
        execute=args.execute,
    )
    out = {
        "ok": decision.ok,
        "capability_code": decision.capability_code,
        "capability_version": decision.capability_version,
        "confidence": decision.confidence,
        "reason": decision.reason,
        "rejected": decision.rejected,
        "model": ollama_model(),
    }
    if exe is not None:
        out["execution"] = {
            "ok": exe.ok,
            "message": exe.message,
            "detail_keys": list(exe.detail.keys()) if isinstance(exe.detail, dict) else [],
        }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if decision.ok else 2


def cmd_chat(args: argparse.Namespace) -> int:
    router = _build_router(
        core=args.core,
        catalog_json=args.catalog_json,
        with_executor=args.execute,
    )
    print(f"capreq chat · model={ollama_model()} · Ctrl+C 종료")
    if args.core:
        print(f"catalog: CapNet {args.core}")
    print("능력만 고른다. 실행은 --execute 일 때만.")
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line in ("/quit", "/exit"):
            return 0
        decision, exe = router.route_and_maybe_execute(
            line,
            dataset_id=args.dataset,
            case_id=args.case,
            execute=args.execute,
        )
        if decision.ok:
            print(
                f"capreq> {decision.capability_code}@{decision.capability_version} "
                f"(conf={decision.confidence:.2f}) — {decision.reason}"
            )
        else:
            print(f"capreq> (미매칭/거절) {decision.reason}")
        if exe is not None:
            print(f"exec> {'OK' if exe.ok else 'FAIL'} — {exe.message}")


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print("서버 의존성 없음: pip install -e \".[server]\"", file=sys.stderr)
        return 1
    from capreq.server import create_app

    app = create_app(
        core=args.core,
        catalog_json=args.catalog_json,
        execute_default=args.execute,
        dataset=args.dataset,
        case_id=args.case,
    )
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def cmd_gemma(args: argparse.Namespace) -> int:
    """Gemma 일반 대화 UI — CapNet 없이 대화만."""
    try:
        import uvicorn
    except ImportError:
        print("서버 의존성 없음: pip install -e \".[server]\"", file=sys.stderr)
        return 1
    from capreq.gemma_server import create_gemma_app, gemma_model

    model = args.model or gemma_model()
    print(f"Gemma 대화 UI · model={model}")
    print(f"브라우저 → http://{args.host}:{args.port}/")
    print("모델 없으면: ollama pull gemma2:2b")
    app = create_gemma_app(model=model)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="capreq", description="로컬 LLM → capability 라우터 / Gemma 대화")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--core", default=None, help="CapNet Core URL")
        sp.add_argument("--catalog-json", default=None, help="정적 카탈로그 JSON")
        sp.add_argument("--execute", action="store_true", help="백엔드 실행까지")
        sp.add_argument("--dataset", default="eurosat-rgb")
        sp.add_argument("--case", default="ic1-0001")

    pr = sub.add_parser("route", help="한 문장 라우팅")
    add_common(pr)
    pr.add_argument("text")
    pr.set_defaults(func=cmd_route)

    pc = sub.add_parser("chat", help="능력 라우팅 CLI")
    add_common(pc)
    pc.set_defaults(func=cmd_chat)

    ps = sub.add_parser("serve", help="능력 라우팅 웹 UI")
    add_common(ps)
    ps.add_argument("--host", default="127.0.0.1")
    ps.add_argument("--port", type=int, default=8090)
    ps.set_defaults(func=cmd_serve)

    pg = sub.add_parser("gemma", help="Gemma 일반 대화 웹 UI (테스트용)")
    pg.add_argument("--host", default="127.0.0.1")
    pg.add_argument("--port", type=int, default=8091)
    pg.add_argument("--model", default=None, help="기본 gemma2:2b")
    pg.set_defaults(func=cmd_gemma)

    args = p.parse_args(argv)
    if getattr(args, "cmd", None) != "gemma":
        if getattr(args, "core", None) is None and getattr(args, "catalog_json", None) is None:
            if hasattr(args, "core"):
                args.core = core_url()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
