"""텍스트 임베딩 실행기 (단계 6 ①).

`infer_text.py` 와 같은 규약이다 — arch·전처리·상한을 **Core 가 말한 값**으로 쓴다.
다른 점은 출력이 라벨이 아니라 **벡터**라는 것뿐이고, 그래서 계약 검증도
`enum` 이 아니라 **차원과 원소 타입**을 본다 (D-out).
"""

from __future__ import annotations

from typing import Any

from app.limits import MAX_PARAMS_DEFAULT
from app.preprocess import resolve_text_preprocess
from app.text_features import features


def embed_text(
    weights_path: str,
    text_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> list[float]:
    """고정 차원 벡터를 돌려준다. 의미적 유사도는 주장하지 않는다."""
    import torch
    from safetensors.torch import load_file

    from app.infer_text import read_text
    from app.tiny_embed import TinyTextEmbedder

    if arch and arch != "TinyTextEmbedder":
        raise ValueError(f"unknown embed arch {arch!r}; known=['TinyTextEmbedder']")

    model = TinyTextEmbedder()
    model.load_state_dict(load_file(weights_path))
    model.eval()

    params = sum(p.numel() for p in model.parameters())
    cap = max_params or MAX_PARAMS_DEFAULT
    if params > cap:
        from app.infer_text import TextResourceLimitExceeded

        raise TextResourceLimitExceeded(f"params {params} > max_params {cap}")

    encoding, form, max_chars = resolve_text_preprocess(preprocess)
    text = read_text(text_path, encoding=encoding, max_chars=max_chars, form=form)
    with torch.no_grad():
        vec = model(torch.tensor([features(text)], dtype=torch.float32))[0]
    # float 로 내린다 — JSON 으로 나가야 하고, 계약이 `type: number` 를 요구한다.
    return [float(x) for x in vec]
