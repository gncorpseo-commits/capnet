#!/usr/bin/env python3
"""`rule_rank.safetensors` 생성 — 버퍼 한 칸 (RuleTextRank · 파라미터 0).

`gen_rule_extract_weights.py` 와 같은 모양이다. 학습이 없다 — 규칙 실행기의
가중치 파일은 게이트(지문·`max_params`)가 성립하도록 두는 자리표시자다.
"""

from __future__ import annotations

from pathlib import Path

from safetensors.torch import save_file

from app.tiny_rank import RuleTextRank

ROOT = Path(__file__).resolve().parents[1]  # apps/
OUT = ROOT / "node" / "weights" / "rule_rank.safetensors"


def main() -> None:
    model = RuleTextRank()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    save_file(model.state_dict(), OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
