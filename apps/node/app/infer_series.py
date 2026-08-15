"""시계열 예측 실행기 (단계 6 ②).

다른 모달리티와 **같은 규약**이다 — arch·전처리·상한을 Core 가 말한 값으로 쓴다.
다른 점은 출력이 **수치 배열**이라, 계약 검증이 `enum` 이 아니라 길이·원소 타입을 본다(D-out).

예측은 정규화 축척에서 나오므로 **원래 축척으로 되돌려** 내보낸다 — 그러지 않으면
사용자가 받는 숫자가 입력과 다른 단위가 된다.
"""

from __future__ import annotations

from typing import Any

from app.limits import MAX_PARAMS_DEFAULT
from app.preprocess import resolve_table_preprocess
from app.series_features import parse_series, window_features


def forecast_series(
    weights_path: str,
    series_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> list[float]:
    """앞으로 `HORIZON` 개를 **원래 축척으로** 돌려준다."""
    import torch
    from safetensors.torch import load_file

    from app.tiny_series import TinySeriesForecaster

    if arch and arch != "TinySeriesForecaster":
        raise ValueError(f"unknown series arch {arch!r}; known=['TinySeriesForecaster']")

    encoding, max_rows, window = resolve_table_preprocess(preprocess)

    model = TinySeriesForecaster(window=window)
    model.load_state_dict(load_file(weights_path))
    model.eval()

    params = sum(p.numel() for p in model.parameters())
    cap = max_params or MAX_PARAMS_DEFAULT
    if params > cap:
        from app.infer_text import TextResourceLimitExceeded

        raise TextResourceLimitExceeded(f"params {params} > max_params {cap}")

    values = parse_series(series_path, encoding=encoding, max_rows=max_rows)
    feat, mean, std = window_features(values, window=window)
    with torch.no_grad():
        out = model(torch.tensor([feat], dtype=torch.float32))[0]
    # 정규화를 되돌린다. 이걸 빼면 숫자가 입력과 다른 단위로 나간다.
    return [float(x) * std + mean for x in out]
