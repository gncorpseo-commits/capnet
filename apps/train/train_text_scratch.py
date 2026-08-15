#!/usr/bin/env python3
"""`text.classify` 참조 모델 scratch 학습 (단계 5).

    python -m app.train_text_scratch --out /weights/text_struct_scratch.safetensors

## 학습 데이터를 **생성**한다

외부 말뭉치를 쓰지 않는다. 이메일·URL·IPv4·UUID·ISO 날짜·평문을 **규칙으로 만든다.**
그래서 라이선스가 붙지 않고(절대규칙 6 · 대회 2차 라이선스 검증), 같은 시드면 누구나
같은 데이터를 재현한다.

`random.Random(seed)` 하나만 쓴다 — 전역 `random` 을 건드리면 호출자의 난수열이 바뀐다.

## 홀드아웃을 나눈다

`--holdout` 비율만큼 **생성기를 나눠** 학습에 쓰지 않은 표본으로 정확도를 잰다.
그 값은 `.meta.json` 에만 남기고 **제품 문구로 쓰지 않는다** — `text.classify` 는
`quality_profile='none'` 이라 품질을 주장하지 않는다 (SD-008 의 교훈: 학습셋으로 잰 값을
성능으로 말하지 않는다).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import string
from pathlib import Path

import torch
from safetensors.torch import save_file

from app.text_features import features
from app.tiny_text import TEXT_LABELS, TinyTextClassifier

WORDS = (
    "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima "
    "mike november oscar papa quebec romeo sierra tango uniform victor whiskey"
).split()
TLDS = ("com", "net", "org", "io", "dev", "kr")
SCHEMES = ("http", "https")


def _word(rng: random.Random) -> str:
    return rng.choice(WORDS)


def _make(rng: random.Random, label: str) -> str:
    """라벨 하나에 해당하는 문자열을 만든다. 규칙만 쓴다 — 외부 데이터 없음."""
    if label == "email":
        return f"{_word(rng)}{rng.randint(1, 99)}@{_word(rng)}.{rng.choice(TLDS)}"
    if label == "url":
        path = "/".join(_word(rng) for _ in range(rng.randint(0, 3)))
        return f"{rng.choice(SCHEMES)}://{_word(rng)}.{rng.choice(TLDS)}/{path}"
    if label == "ipv4":
        return ".".join(str(rng.randint(0, 255)) for _ in range(4))
    if label == "uuid":
        hexd = "".join(rng.choice(string.hexdigits.lower()[:16]) for _ in range(32))
        return f"{hexd[:8]}-{hexd[8:12]}-{hexd[12:16]}-{hexd[16:20]}-{hexd[20:]}"
    if label == "iso_date":
        return f"{rng.randint(1970, 2099):04d}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
    if label == "plain":
        return " ".join(_word(rng) for _ in range(rng.randint(2, 8)))
    raise ValueError(f"unknown label: {label}")


def make_dataset(n: int, seed: int) -> list[tuple[str, int]]:
    """라벨이 고르게 섞인 표본 n 개. 클래스 불균형을 만들지 않는다."""
    rng = random.Random(seed)
    rows: list[tuple[str, int]] = []
    for i in range(n):
        idx = i % len(TEXT_LABELS)
        rows.append((_make(rng, TEXT_LABELS[idx]), idx))
    rng.shuffle(rows)
    return rows


def _tensors(rows: list[tuple[str, int]]) -> tuple[torch.Tensor, torch.Tensor]:
    xs = torch.tensor([features(t) for t, _ in rows], dtype=torch.float32)
    ys = torch.tensor([y for _, y in rows], dtype=torch.long)
    return xs, ys


def main() -> int:
    ap = argparse.ArgumentParser(prog="train_text_scratch")
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=6000)
    ap.add_argument("--holdout", type=int, default=1200)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--lr", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=20260815)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    # 홀드아웃은 **다른 시드**로 만든다. 같은 시드로 잘라 쓰면 생성 순서가 겹칠 수 있다.
    train_rows = make_dataset(args.samples, args.seed)
    hold_rows = make_dataset(args.holdout, args.seed + 1)

    xtr, ytr = _tensors(train_rows)
    xho, yho = _tensors(hold_rows)

    model = TinyTextClassifier()
    opt = torch.optim.SGD(model.parameters(), lr=args.lr)
    lossf = torch.nn.CrossEntropyLoss()

    final_loss = 0.0
    for _ in range(args.epochs):
        opt.zero_grad()
        loss = lossf(model(xtr), ytr)
        loss.backward()
        opt.step()
        final_loss = float(loss.item())

    with torch.no_grad():
        acc = float((model(xho).argmax(1) == yho).float().mean().item())

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_file({k: v.contiguous() for k, v in model.state_dict().items()}, str(out))
    sha = hashlib.sha256(out.read_bytes()).hexdigest()

    meta = {
        "weights": out.name,
        "weights_sha256": sha,
        "arch": "TinyTextClassifier",
        "pretrained": False,
        "dataset": "synthetic-structural (규칙 생성 · 외부 말뭉치 없음)",
        "labels": list(TEXT_LABELS),
        "train_samples": args.samples,
        "holdout_samples": args.holdout,
        "epochs": args.epochs,
        "seed": args.seed,
        "final_train_loss": final_loss,
        "holdout_accuracy": acc,
        "note": (
            "text.classify 는 quality_profile='none' 이다 — 이 정확도는 기록일 뿐 "
            "제품의 품질 보장이 아니다. 골든셋도 채점 게이트도 없다."
        ),
    }
    out.with_suffix("").with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"saved {out} sha256={sha[:16]}… holdout_acc={acc:.4f} loss={final_loss:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
