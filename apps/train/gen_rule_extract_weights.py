#!/usr/bin/env python3
"""`rule_extract.safetensors` 생성 — 버퍼 한 칸 (RuleTextExtract · 파라미터 0).

`gen_rule_ner_weights.py` 와 같은 모양이다. 학습이 없다 — 규칙 실행기의
가중치 파일은 게이트(지문·`max_params`)가 성립하도록 두는 자리표시자다.
"""

from __future__ import annotations

from pathlib import Path

from safetensors.torch import save_file

from app.tiny_extract import RuleTextExtract

ROOT = Path(__file__).resolve().parents[1]  # apps/
OUT = ROOT / "node" / "weights" / "rule_extract.safetensors"


def main() -> None:
    model = RuleTextExtract()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    save_file(model.state_dict(), OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
