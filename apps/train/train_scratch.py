"""EuroSAT RGB scratch 학습 → safetensors. 사전학습 가중치 사용 금지."""

from __future__ import annotations

import hashlib
import io
import json
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
from app.tiny_cnn import LABELS, TinyEuroSAT  # noqa: E402

ZIP_PATH = Path("/data/EuroSAT_RGB.zip")
OUT_PATH = Path("/out/eurosat_scratch.safetensors")
META_PATH = Path("/out/eurosat_scratch.meta.json")

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
    torch.manual_seed(20260806)
    random.seed(20260806)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = list_images(zf)
    random.shuffle(names)
    # scratch 전수. 사전학습 없음. 게이트 미달이면 FAILED가 정답.
    ds = ZipEuroSAT(ZIP_PATH, names, augment=True)
    loader = DataLoader(ds, batch_size=64, shuffle=True, num_workers=0)
    model = TinyEuroSAT()
    start_epoch = 0
    if OUT_PATH.is_file():
        from safetensors.torch import load_file

        model.load_state_dict(load_file(str(OUT_PATH)))
        if META_PATH.is_file():
            start_epoch = int(json.loads(META_PATH.read_text(encoding="utf-8")).get("epochs", 0))
        print(f"resume from existing safetensors epoch={start_epoch}", flush=True)
    opt = torch.optim.Adam(model.parameters(), lr=5e-4)
    loss_fn = nn.CrossEntropyLoss()
    model.train()
    extra = 20
    total_epochs = start_epoch + extra
    last_loss = 0.0
    lr = 3e-4 if start_epoch else 1e-3
    opt = torch.optim.Adam(model.parameters(), lr=lr)
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
        "arch": "TinyEuroSAT",
        "pretrained": False,
        "dataset": "eurosat-rgb",
        "input_hw": [32, 32],
        "train_images": len(names),
        "epochs": total_epochs,
        "seed": 20260806,
        "final_train_loss": last_loss,
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2), flush=True)


if __name__ == "__main__":
    main()
