"""텍스트 추론 — `text.classify` 실행기 (단계 5).

`infer.py`(이미지)와 **같은 규약**을 지킨다.

- 가중치는 **Core 가 말한 `arch`** 로 세운다 (I1). 로컬 meta 로 정하지 않는다
- 전처리는 **계약이 선언한 값**으로 한다 (0014 · D3). 기본값으로 떨어지면
  「게이트가 승인한 것」과 「실행한 것」이 달라진다
- 파라미터 상한을 넘으면 실행하지 않는다 (D-maxp · `agent_arch.max_params`)

**품질을 주장하지 않는다.** `text.classify` 는 `quality_profile='none'` 이라
골든셋도 채점도 없다 — 이 파일은 계약을 만족하는 실행 경로일 뿐이다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.limits import MAX_PARAMS_DEFAULT
from app.preprocess import resolve_text_preprocess
from app.text_features import features, normalize


class TextResourceLimitExceeded(RuntimeError):
    """파라미터 상한 초과. 조용히 도는 것보다 터뜨리는 편이 낫다."""


def read_text(path: str, *, encoding: str, max_chars: int | None, form: str) -> str:
    """계약이 선언한 인코딩·정규화·길이로 읽는다.

    디코딩 실패를 **삼키지 않는다** — `errors='replace'` 로 넘기면 계약이 `utf-8` 이라고
    선언했는데 다른 인코딩이 들어와도 조용히 통과한다. MIME 대조(B1)와 같은 규율이다.
    """
    raw = Path(path).read_bytes()
    try:
        text = raw.decode(encoding)
    except (UnicodeDecodeError, LookupError) as exc:
        raise ValueError(f"입력이 계약 인코딩({encoding})이 아니다: {exc}") from exc
    return normalize(text, form=form, max_chars=max_chars)


def predict_text(
    weights_path: str,
    text_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> tuple[str, float]:
    """(label, confidence) 를 돌려준다. 라벨 집합은 `TEXT_LABELS` 가 정본이다."""
    import torch
    from safetensors.torch import load_file

    from app.tiny_text import TEXT_LABELS, TinyTextClassifier

    if arch and arch != "TinyTextClassifier":
        # 이 실행기는 이 arch 만 안다. 모르는 것을 아는 척하지 않는다.
        raise ValueError(f"unknown text arch {arch!r}; known=['TinyTextClassifier']")

    model = TinyTextClassifier()
    model.load_state_dict(load_file(weights_path))
    model.eval()

    params = sum(p.numel() for p in model.parameters())
    cap = max_params or MAX_PARAMS_DEFAULT
    if params > cap:
        raise TextResourceLimitExceeded(f"params {params} > max_params {cap}")

    encoding, form, max_chars = resolve_text_preprocess(preprocess)
    text = read_text(text_path, encoding=encoding, max_chars=max_chars, form=form)

    with torch.no_grad():
        logits = model(torch.tensor([features(text)], dtype=torch.float32))
        probs = torch.softmax(logits, dim=1)[0]
        idx = int(probs.argmax().item())
    return TEXT_LABELS[idx], float(probs[idx].item())
