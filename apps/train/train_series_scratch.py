#!/usr/bin/env python3
"""`timeseries.forecast` 참조 모델 scratch 학습 (단계 6 ②).

학습 데이터를 **생성한다** — 추세 + 계절성 + 잡음. 외부 데이터가 0 이다.
홀드아웃은 **다른 시드**로 만들고, 그 오차는 `.meta.json` 에만 남긴다.
`quality_profile='none'` 이라 제품 문구로 쓰지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import torch
from safetensors.torch import save_file

from app.series_features import HORIZON, WINDOW, window_features
from app.tiny_series import TinySeriesForecaster


def make_dataset(n: int, seed: int) -> tuple[list[list[float]], list[list[float]]]:
    """(특징, 정답) 쌍 n 개. 각 표본은 서로 다른 추세·주기·위상을 갖는다."""
    rng = random.Random(seed)
    xs: list[list[float]] = []
    ys: list[list[float]] = []
    for _ in range(n):
        slope = rng.uniform(-0.5, 0.5)
        amp = rng.uniform(0.5, 3.0)
        period = rng.uniform(4.0, 16.0)
        phase = rng.uniform(0.0, math.tau)
        noise = rng.uniform(0.0, 0.2)
        total = WINDOW + HORIZON
        series = [
            slope * t + amp * math.sin(phase + math.tau * t / period)
            + rng.gauss(0.0, noise)
            for t in range(total)
        ]
        feat, mean, std = window_features(series[:WINDOW], window=WINDOW)
        xs.append(feat)
        # 정답도 **같은 축척**으로 둔다 — 예측을 되돌릴 때 mean/std 를 그대로 쓴다.
        ys.append([(v - mean) / std for v in series[WINDOW:]])
    return xs, ys


def main() -> int:
    ap = argparse.ArgumentParser(prog="train_series_scratch")
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=4000)
    ap.add_argument("--holdout", type=int, default=800)
    ap.add_argument("--epochs", type=int, default=400)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20260816)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    xtr, ytr = make_dataset(args.samples, args.seed)
    xho, yho = make_dataset(args.holdout, args.seed + 1)
    xtr_t = torch.tensor(xtr, dtype=torch.float32)
    ytr_t = torch.tensor(ytr, dtype=torch.float32)
    xho_t = torch.tensor(xho, dtype=torch.float32)
    yho_t = torch.tensor(yho, dtype=torch.float32)

    model = TinySeriesForecaster()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    lossf = torch.nn.MSELoss()
    final = 0.0
    for _ in range(args.epochs):
        opt.zero_grad()
        loss = lossf(model(xtr_t), ytr_t)
        loss.backward()
        opt.step()
        final = float(loss.item())

    with torch.no_grad():
        ho_mse = float(lossf(model(xho_t), yho_t).item())
        # 「마지막 값을 그대로 반복」 기준선. 이보다 나쁘면 모델이 배운 게 없다는 뜻이다.
        naive = float(lossf(xho_t[:, -1:].repeat(1, HORIZON), yho_t).item())

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_file({k: v.contiguous() for k, v in model.state_dict().items()}, str(out))
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    meta = {
        "weights": out.name,
        "weights_sha256": sha,
        "arch": "TinySeriesForecaster",
        "pretrained": False,
        "dataset": "synthetic-series (규칙 생성: 추세+계절성+잡음 · 외부 데이터 없음)",
        "window": WINDOW,
        "horizon": HORIZON,
        "train_samples": args.samples,
        "holdout_samples": args.holdout,
        "epochs": args.epochs,
        "seed": args.seed,
        "final_train_mse": final,
        "holdout_mse": ho_mse,
        "holdout_mse_naive_baseline": naive,
        "note": (
            "timeseries.forecast 는 quality_profile='none' 이다 — 이 오차는 기록일 뿐 "
            "제품의 품질 보장이 아니다. 합성 데이터로 학습했고 실제 시계열 성능을 주장하지 않는다."
        ),
    }
    out.with_suffix("").with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"saved {out} sha256={sha[:16]}… holdout_mse={ho_mse:.4f} naive={naive:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
