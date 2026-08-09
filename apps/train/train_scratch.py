"""EuroSAT RGB scratch 학습 → safetensors. 사전학습 가중치 사용 금지."""

from __future__ import annotations

import hashlib
import io
import json
import os
import random
import sys
import zipfile
from pathlib import Path

import torch
from PIL import Image
from safetensors.torch import save_file
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms.functional import to_tensor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "node"))
from app.tiny_cnn import LABELS, build_model  # noqa: E402

ZIP_PATH = Path("/data/EuroSAT_RGB.zip")
# ARCH=TinyEuroSAT | TinyEuroSATB · OUT_NAME으로 출력 파일 구분
ARCH = os.environ.get("ARCH", "TinyEuroSAT")
OUT_NAME = os.environ.get("OUT_NAME", "eurosat_scratch.safetensors")
OUT_PATH = Path("/out") / OUT_NAME
META_PATH = Path("/out") / (Path(OUT_NAME).stem + ".meta.json")

FOLDER_TO_LABEL = {
    "AnnualCrop": "annual_crop",
    "Forest": "forest",
    "HerbaceousVegetation": "herbaceous_vegetation",
    "Highway": "highway",
    "Industrial": "industrial",
    "Pasture": "pasture",
    "PermanentCrop": "permanent_crop",
    "Residential": "residential",
    "River": "river",
    "SeaLake": "sea_lake",
}
LABEL_INDEX = {name: i for i, name in enumerate(LABELS)}


class ZipEuroSAT(Dataset):
    def __init__(self, zip_path: Path, names: list[str], augment: bool = False) -> None:
        self.zf = zipfile.ZipFile(zip_path)
        self.names = names
        self.augment = augment

    def __len__(self) -> int:
        return len(self.names)

    def __getitem__(self, idx: int):
        name = self.names[idx]
        folder = name.replace("\\", "/").split("/")[1]
        label = LABEL_INDEX[FOLDER_TO_LABEL[folder]]
        with self.zf.open(name) as fh:
            img = Image.open(io.BytesIO(fh.read())).convert("RGB").resize((32, 32))
        if self.augment and random.random() < 0.5:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        return to_tensor(img), label


# 홀드아웃 분할 (H1) — 골든셋이 학습셋 안에 있으면 게이트는 능력이 아니라 암기를 잰다.
# scripts/extract_golden.py 의 동일 함수와 **규칙이 같아야 한다.** 한쪽만 고치면 누출이 되살아난다.
HOLDOUT_MOD = 5  # 1/5 ≈ 20%


def is_holdout(name: str) -> bool:
    """zip 엔트리명 해시로 결정적 분할. 시드·순서와 무관하게 항상 같은 결과."""
    return int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16) % HOLDOUT_MOD == 0


def list_images(zf: zipfile.ZipFile) -> list[str]:
    names = []
    for name in zf.namelist():
        if not name.lower().endswith(".jpg"):
            continue
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 3 and parts[1] in FOLDER_TO_LABEL:
            names.append(name)
    names.sort()
    return names


def main() -> None:
    seed = int(os.environ.get("SEED", "20260806"))
    torch.manual_seed(seed)
    random.seed(seed)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        all_names = list_images(zf)
    # HOLDOUT=0 이면 구버전 동작(전수 학습). 기본은 홀드아웃 제외.
    use_holdout = os.environ.get("HOLDOUT", "1") != "0"
    if use_holdout:
        names = [n for n in all_names if not is_holdout(n)]
    else:
        names = list(all_names)
    held = len(all_names) - len(names)
    print(
        f"split holdout={'on' if use_holdout else 'OFF'} "
        f"train={len(names)} held_out={held} total={len(all_names)}",
        flush=True,
    )
    if use_holdout and held == 0:
        raise SystemExit("홀드아웃이 0건이다. 분할 규칙을 확인하라.")
    random.shuffle(names)
    # 사전학습 없음. 게이트 미달이면 FAILED가 정답.
    ds = ZipEuroSAT(ZIP_PATH, names, augment=True)
    loader = DataLoader(ds, batch_size=64, shuffle=True, num_workers=0)
    model = build_model(ARCH)
    start_epoch = 0
    if OUT_PATH.is_file():
        from safetensors.torch import load_file

        model.load_state_dict(load_file(str(OUT_PATH)))
        if META_PATH.is_file():
            start_epoch = int(json.loads(META_PATH.read_text(encoding="utf-8")).get("epochs", 0))
        print(f"resume arch={ARCH} from existing safetensors epoch={start_epoch}", flush=True)
    loss_fn = nn.CrossEntropyLoss()
    model.train()
    extra = int(os.environ.get("EXTRA_EPOCHS", "20"))
    total_epochs = start_epoch + extra
    last_loss = 0.0
    lr = 3e-4 if start_epoch else 1e-3
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    print(f"train arch={ARCH} out={OUT_PATH.name} epochs={extra}", flush=True)
    for epoch in range(extra):
        total = 0.0
        correct = 0
        seen = 0
        for xb, yb in loader:
            opt.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            opt.step()
            total += float(loss.item()) * len(yb)
            correct += int((logits.argmax(1) == yb).sum().item())
            seen += len(yb)
        last_loss = total / max(seen, 1)
        print(
            f"epoch {start_epoch + epoch + 1}/{total_epochs} loss={last_loss:.4f} acc={correct / max(seen, 1):.4f} n={seen}",
            flush=True,
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    state = {k: v.detach().cpu().contiguous() for k, v in model.state_dict().items()}
    save_file(state, str(OUT_PATH))
    digest = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
    meta = {
        "weights": OUT_PATH.name,
        "weights_sha256": digest,
        "arch": ARCH,
        "pretrained": False,
        "dataset": "eurosat-rgb",
        "split": {
            "holdout": use_holdout,
            "rule": f"sha1(zip_entry_name)[:8] % {HOLDOUT_MOD} == 0 -> holdout",
            "train_count": len(names),
            "held_out_count": held,
        },
        "input_hw": [32, 32],
        "train_images": len(names),
        "epochs": total_epochs,
        "seed": seed,
        "final_train_loss": last_loss,
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2), flush=True)


if __name__ == "__main__":
    main()
