"""전처리 선언 해석 — **torch 없이** 돈다.

`infer.py` 에 있던 것을 옮겼다. 이유는 하나다: 계약 게이트의 **선언 검사 경로**(C2)가
torch 없는 Node(`s-public` — `apps/node/Dockerfile` 이 조건부로만 설치한다)에서도
돌아야 하는데, `infer.py` 는 모듈 최상단에서 `import torch` 를 한다.

그래서 「선언을 읽는 일」과 「그 선언으로 추론하는 일」을 나눴다.
읽는 쪽은 순수 함수라 의존성이 필요 없다. `infer.py` 는 여기서 가져다 쓴다.

전처리 어휘 자체(모달리티별 키)는 `docs/spec/capability-catalog.md` §4 가 정본이다.
"""

from __future__ import annotations

from typing import Any

# 계약이 전처리를 선언하기 전의 값 (D3 · 32×32 RGB). `image.classify` 의 선언값과 같다 —
# 0014 가 계약에 적어 넣은 것이 바로 이 값이라, 골든 경로의 픽셀 처리는 바뀌지 않는다.
DEFAULT_PREPROCESS: dict[str, Any] = {"resize": [32, 32], "colorspace": "RGB"}


def resolve_preprocess(declared: dict[str, Any] | None) -> tuple[tuple[int, int], str]:
    """계약 선언을 (resize, colorspace) 로 푼다. 없으면 종전 기본값."""
    spec = declared or DEFAULT_PREPROCESS
    size = spec.get("resize") or DEFAULT_PREPROCESS["resize"]
    if not (isinstance(size, (list, tuple)) and len(size) == 2):
        raise ValueError(f"preprocess.resize 형식이 아니다: {size!r}")
    w, h = int(size[0]), int(size[1])
    if w < 1 or h < 1:
        raise ValueError(f"preprocess.resize 가 양수가 아니다: {size!r}")
    space = str(spec.get("colorspace") or DEFAULT_PREPROCESS["colorspace"])
    return (w, h), space
