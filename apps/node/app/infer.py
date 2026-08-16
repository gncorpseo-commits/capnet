"""32×32 RGB → closed-set 라벨. safetensors + scratch 백본만 (사전학습 없음).

## 자원 한도 (I2 · foreign-agent-isolation §3)

남의 Agent 를 받으면 「팀 Node 신뢰」 전제가 사라진다 (기획서 §5.3).
여기서 세 가지를 막는다.

- **디코드 폭탄** — 작은 파일이 거대 비트맵으로 펴지는 것. PIL 의 전역 상한 + 자체 검사
- **CPU 독점** — torch thread 수를 묶는다. 한 건이 Node 전체를 먹지 않게
- **거대 모델** — 파라미터 수 상한. 게이트는 품질만 보므로 크기는 여기서 막는다

compose 의 `mem_limit` 은 **컨테이너 전체** 한도라, 한 건의 악성 추론이 같은 Node 의
다른 lease 까지 죽인다. 그래서 건별 한도가 따로 필요하다.
"""

from __future__ import annotations

import json
import os
from typing import Any
from pathlib import Path

import torch
from PIL import Image
from safetensors.torch import load_file
from torchvision.transforms.functional import to_tensor

from app.tiny_cnn import LABELS, build_model

# --- 자원 한도 -------------------------------------------------------------
MAX_INPUT_PIXELS = int(os.environ.get("NODE_MAX_INPUT_PIXELS", 8_000_000))
# torch 없이 읽혀야 해서 `app.limits` 로 옮겼다 (D-maxp). 이름만 다시 내보낸다.
from app.limits import MAX_PARAMS_DEFAULT  # noqa: E402,F401
TORCH_THREADS = int(os.environ.get("NODE_TORCH_THREADS", 1))

# 디코드 폭탄 방어 — PIL 전역 상한. 초과하면 PIL 이 예외를 던진다.
Image.MAX_IMAGE_PIXELS = MAX_INPUT_PIXELS
torch.set_num_threads(max(1, TORCH_THREADS))


class ResourceLimitExceeded(Exception):
    """한도를 넘었다. 실행하지 않는다 — 터뜨리는 편이 조용히 도는 것보다 낫다."""


_model = None
_loaded_path: str | None = None
_loaded_arch: str | None = None
_loaded_params: int = 0


def _arch_for_weights(weights_path: str) -> str:
    # eurosat_scratch.safetensors → eurosat_scratch.meta.json
    meta = Path(weights_path).parent / (Path(weights_path).stem + ".meta.json")
    if meta.is_file():
        data = json.loads(meta.read_text(encoding="utf-8"))
        return str(data.get("arch", "TinyEuroSAT"))
    return "TinyEuroSAT"


# 전처리 선언 해석은 `app.preprocess` 로 옮겼다 — **torch 없이** 돌아야 하기 때문이다
# (계약 게이트의 선언 검사 경로 · C2). 여기서는 이름만 다시 내보낸다.
from app.preprocess import DEFAULT_PREPROCESS, resolve_preprocess  # noqa: E402,F401


def load_image_tensor(image_path: str, *, preprocess: dict[str, Any] | None = None):
    """계약이 선언한 전처리로 이미지를 텐서 하나로 만든다.

    **분류와 임베딩이 같은 함수를 쓴다** (단계 6 ③). 두 벌이면 한쪽만 고쳐지고,
    그 순간 「게이트가 승인한 전처리」와 「실행한 전처리」가 갈라진다 (D3).

    픽셀 상한도 여기 있다 — 임베딩 경로만 상한이 없으면 그쪽으로 큰 이미지가 들어온다.
    """
    img = Image.open(image_path)
    w, h = img.size
    if w * h > MAX_INPUT_PIXELS:
        raise ResourceLimitExceeded(f"입력 {w}x{h} 픽셀 > 상한 {MAX_INPUT_PIXELS}")
    size, space = resolve_preprocess(preprocess)
    return to_tensor(img.convert(space).resize(size)).unsqueeze(0)


def predict_image(
    weights_path: str,
    image_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> tuple[str, float]:
    """추론 1건.

    `arch` 가 주어지면 **그것만** 쓴다 — Core 가 말한 값이다. 주어지지 않으면
    로컬 meta 로 떨어진다 (legacy · arch 미선언 Agent).

    `preprocess` 가 주어지면 **계약이 선언한 값**으로 전처리한다 (0014 · B2).
    주어지지 않으면 종전 기본값 — 골든 경로는 이 길로 그대로 돈다.
    """
    global _model, _loaded_path, _loaded_arch, _loaded_params
    resolved = arch or _arch_for_weights(weights_path)
    if _model is None or _loaded_path != weights_path or _loaded_arch != resolved:
        model = build_model(resolved)  # allowlist 밖이면 여기서 ValueError
        state = load_file(weights_path)
        model.load_state_dict(state)
        model.eval()
        _model = model
        _loaded_path = weights_path
        _loaded_arch = resolved
        _loaded_params = sum(p.numel() for p in model.parameters())

    # 한도는 **매 호출** 본다. 로드할 때만 보면 모델이 캐시된 뒤 상한을 낮춰도 계속 돈다 —
    # Core 가 max_params 를 조인 순간부터 막혀야 한다.
    cap = max_params or MAX_PARAMS_DEFAULT
    if _loaded_params > cap:
        raise ResourceLimitExceeded(
            f"파라미터 {_loaded_params} > 상한 {cap} (arch={resolved})"
        )
    xb = load_image_tensor(image_path, preprocess=preprocess)
    with torch.no_grad():
        logits = _model(xb)
        prob = torch.softmax(logits, dim=1)[0]
        idx = int(prob.argmax().item())
        return LABELS[idx], float(prob[idx].item())


def case_path(cases_dir: str, case_id: str) -> Path:
    return Path(cases_dir) / f"{case_id}.jpg"
