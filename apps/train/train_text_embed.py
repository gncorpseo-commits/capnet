#!/usr/bin/env python3
"""`text.embed` 참조 사영 생성 (단계 6 ①).

    python -m app.train_text_embed --out /weights/text_embed_scratch.safetensors

## 「학습」이 아니라 **고정 초기화**다

이 사영은 라벨로 학습하지 않는다. 고정 시드로 초기화한 선형 변환을 저장할 뿐이다.
**그 사실을 이름과 meta 에 적는다** — 「학습된 임베딩」으로 읽히면 안 된다.

그래도 재현 가능해야 한다: 같은 시드면 같은 가중치, 같은 입력이면 같은 벡터.
그것이 이 능력이 계약에 대해 약속하는 전부다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
from safetensors.torch import save_file

from app.text_features import features
from app.tiny_embed import EMBED_DIM, TinyTextEmbedder


def main() -> int:
    ap = argparse.ArgumentParser(prog="train_text_embed")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20260816)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    model = TinyTextEmbedder()
    model.eval()

    # 재현성 확인 — 같은 입력이 같은 벡터를 내는가, 다른 입력은 다른가.
    with torch.no_grad():
        a = model(torch.tensor([features("hello@example.com")], dtype=torch.float32))[0]
        b = model(torch.tensor([features("hello@example.com")], dtype=torch.float32))[0]
        c = model(torch.tensor([features("192.168.0.1")], dtype=torch.float32))[0]
    same = bool(torch.allclose(a, b))
    differs = not bool(torch.allclose(a, c))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_file({k: v.contiguous() for k, v in model.state_dict().items()}, str(out))
    sha = hashlib.sha256(out.read_bytes()).hexdigest()

    meta = {
        "weights": out.name,
        "weights_sha256": sha,
        "arch": "TinyTextEmbedder",
        "pretrained": False,
        "dataset": "없음 — 라벨 학습을 하지 않는다 (고정 시드 초기화 사영)",
        "embed_dim": EMBED_DIM,
        "seed": args.seed,
        "deterministic_same_input": same,
        "differs_on_different_input": differs,
        "note": (
            "이것은 학습된 임베딩이 아니다. 고정 시드 선형 사영이며 의미적 유사도를 "
            "주장하지 않는다. text.embed 는 quality_profile='none' 이라 골든셋도 채점도 없다."
        ),
    }
    out.with_suffix("").with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"saved {out} sha256={sha[:16]}… dim={EMBED_DIM} same={same} differs={differs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
