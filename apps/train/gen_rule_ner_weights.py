#!/usr/bin/env python3
"""`rule_ner.safetensors` 생성 — 빈 state dict (RuleTextNer · 파라미터 0)."""

from __future__ import annotations

from pathlib import Path

from safetensors.torch import save_file

from app.tiny_ner import RuleTextNer

ROOT = Path(__file__).resolve().parents[1]  # apps/
OUT = ROOT / "node" / "weights" / "rule_ner.safetensors"


def main() -> None:
    model = RuleTextNer()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    save_file(model.state_dict(), OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
