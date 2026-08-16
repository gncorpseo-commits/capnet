"""이미지 임베딩 실행기 (단계 6 ③).

`infer.py`(분류)와 **같은 전처리 어휘**를 쓴다 — 계약이 선언한 `resize`·`colorspace` 를
적용한다. 다른 것은 출력이다: 라벨이 아니라 128차원 벡터.

**이미지 모달리티가 `structured` 를 내는 첫 사례다.** 그동안 이미지는 closed_set 뿐이었다.
"""

from __future__ import annotations

from typing import Any

from app.limits import MAX_PARAMS_DEFAULT


def embed_image(
    weights_path: str,
    image_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> list[float]:
    import torch
    from safetensors.torch import load_file

    from app.infer import load_image_tensor
    from app.tiny_image_embed import TinyEuroSATEmbed, load_trunk

    if arch and arch != "TinyEuroSATEmbed":
        raise ValueError(f"unknown image-embed arch {arch!r}; known=['TinyEuroSATEmbed']")

    model = TinyEuroSATEmbed()
    load_trunk(model, load_file(weights_path))
    model.eval()

    params = sum(p.numel() for p in model.parameters())
    cap = max_params or MAX_PARAMS_DEFAULT
    if params > cap:
        from app.infer_text import TextResourceLimitExceeded

        raise TextResourceLimitExceeded(f"params {params} > max_params {cap}")

    tensor = load_image_tensor(image_path, preprocess=preprocess)
    with torch.no_grad():
        vec = model(tensor)[0]
    return [float(x) for x in vec]
