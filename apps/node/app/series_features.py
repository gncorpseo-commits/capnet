"""시계열 입력 파싱 — **torch 없이** 돈다 (단계 6 ②).

## 왜 따로 있는가

학습(`apps/train/train_series_scratch.py`)과 추론(`app/infer_series.py`)이 **같은 함수**를
써야 한다. 두 벌이면 한쪽만 고쳐지고, 그 순간 「게이트가 승인한 것」과 「실행한 것」이
달라진다 — D3 가 전처리를 계약의 일부로 못박은 이유와 같다.

## 입력 형식

CSV 한 열(헤더 있어도 됨) 또는 JSON 숫자 배열. **둘 다 계약이 `mediaTypes` 로 선언한다.**
파싱 실패를 삼키지 않는다 — 계약이 `text/csv` 라고 했는데 다른 것이 오면 터진다.

## 정규화

마지막 `window` 개를 잘라 **평균 0 · 표준편차 1** 로 맞춘다. 되돌릴 수 있게
(mean, std)를 같이 돌려준다 — 예측을 원래 축척으로 되돌려야 하기 때문이다.
"""

from __future__ import annotations

import json
from pathlib import Path

# 모델이 보는 과거 길이. 계약(`input_schema.preprocess.window`)과 같아야 한다.
WINDOW = 24
# 내다보는 길이. 계약(`output_schema.properties.forecast.minItems/maxItems`)과 같아야 한다.
HORIZON = 4


def parse_series(path: str | Path, *, encoding: str, max_rows: int | None) -> list[float]:
    """CSV 한 열 또는 JSON 배열을 숫자 목록으로 읽는다."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode(encoding)
    except (UnicodeDecodeError, LookupError) as exc:
        raise ValueError(f"입력이 계약 인코딩({encoding})이 아니다: {exc}") from exc

    stripped = text.strip()
    values: list[float] = []
    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON 배열이 아니다: {exc}") from exc
        if not isinstance(data, list):
            raise ValueError("JSON 최상위가 배열이 아니다")
        for i, v in enumerate(data):
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ValueError(f"{i}번째 값이 숫자가 아니다: {v!r}")
            values.append(float(v))
    else:
        for i, line in enumerate(stripped.splitlines()):
            cell = line.split(",")[0].strip()
            if not cell:
                continue
            try:
                values.append(float(cell))
            except ValueError:
                if i == 0:
                    continue  # 헤더 한 줄은 넘어간다
                raise ValueError(f"{i + 1}행이 숫자가 아니다: {cell!r}") from None

    if max_rows is not None and len(values) > max_rows:
        raise ValueError(f"행이 {len(values)}개로 max_rows({max_rows})를 넘는다")
    return values


def window_features(values: list[float], *, window: int = WINDOW) -> tuple[list[float], float, float]:
    """마지막 `window` 개를 정규화해 돌려준다 → (특징, mean, std).

    표본이 모자라면 **던진다.** 0 으로 채워 넣으면 모델이 없는 과거를 본 것이 되고,
    그건 조용히 틀린 예측을 만든다.
    """
    if len(values) < window:
        raise ValueError(f"표본이 {len(values)}개로 window({window})보다 짧다")
    tail = values[-window:]
    mean = sum(tail) / window
    var = sum((v - mean) ** 2 for v in tail) / window
    std = var ** 0.5
    if std == 0:
        std = 1.0  # 상수 구간. 나눗셈만 피하고 값은 그대로 0 이 된다
    return [(v - mean) / std for v in tail], mean, std
