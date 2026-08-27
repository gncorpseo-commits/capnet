"""`text.ner` 실행기 — 규칙 기반 span 추출 (PR-B).

**품질을 주장하지 않는다.** `quality_profile='none'` · 골든셋 없음.
이 파일은 계약을 만족하는 실행 경로일 뿐이다.
"""

from __future__ import annotations

from typing import Any

from app.infer_text import read_text
from app.limits import MAX_PARAMS_DEFAULT
from app.ner_patterns import find_entities
from app.preprocess import resolve_text_preprocess


def extract_ner(
    weights_path: str,
    text_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`{"entities": [...]}` 를 돌려준다."""
    if arch and arch != "RuleTextNer":
        raise ValueError(f"unknown ner arch {arch!r}; known=['RuleTextNer']")

    # 게이트·증적 일관성 — 파일은 읽지만 추론에는 쓰지 않는다.
    from safetensors.torch import load_file

    from app.infer_text import TextResourceLimitExceeded
    from app.tiny_ner import RuleTextNer

    state = load_file(weights_path)
    model = RuleTextNer()
    model.load_state_dict(state, strict=True)
    params = sum(p.numel() for p in model.parameters())
    cap = max_params or MAX_PARAMS_DEFAULT
    if params > cap:
        raise TextResourceLimitExceeded(f"params {params} > max_params {cap}")

    encoding, form, max_chars = resolve_text_preprocess(preprocess)
    text = read_text(text_path, encoding=encoding, max_chars=max_chars, form=form)
    return {"entities": find_entities(text)}
