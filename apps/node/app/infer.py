"""32×32 RGB → closed-set 라벨. safetensors + TinyEuroSAT scratch만."""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image
from safetensors.torch import load_file
from torchvision.transforms.functional import to_tensor

from app.tiny_cnn import LABELS, TinyEuroSAT

_model: TinyEuroSAT | None = None
_loaded_path: str | None = None


def predict_image(weights_path: str, image_path: str) -> tuple[str, float]:
    global _model, _loaded_path
    if _model is None or _loaded_path != weights_path:
        model = TinyEuroSAT()
        state = load_file(weights_path)
        model.load_state_dict(state)
        model.eval()
        _model = model
        _loaded_path = weights_path
    img = Image.open(image_path).convert("RGB").resize((32, 32))
    xb = to_tensor(img).unsqueeze(0)
    with torch.no_grad():
        logits = _model(xb)
        prob = torch.softmax(logits, dim=1)[0]
        idx = int(prob.argmax().item())
        return LABELS[idx], float(prob[idx].item())


def case_path(cases_dir: str, case_id: str) -> Path:
    return Path(cases_dir) / f"{case_id}.jpg"
