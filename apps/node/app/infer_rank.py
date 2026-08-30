"""`text.rank` 실행기 — 규칙 기반 어휘 겹침 순위 (Wave G).

**품질을 주장하지 않는다.** `quality_profile='none'` · 골든셋 없음.
이 파일은 계약을 만족하는 실행 경로일 뿐이다. 규칙 전문은 `app.rank_rules`.
"""

from __future__ import annotations

import os
from typing import Any

from app.infer_text import read_text
from app.limits import MAX_PARAMS_DEFAULT
from app.preprocess import resolve_text_preprocess
from app.rank_rules import rank_lines

# **자르지 않고 던진다** (`text.extract` 의 `MAX_FIELDS` 와 같은 규율). 잘라서 돌려주면
# 「전부 줄 세웠다」가 거짓이 되고, 쓰는 쪽은 뒤가 잘린 줄 모른다.
# 이것은 계약 항목이 아니라 **러너 자원 한도**다 — 계약이 정하는 것은 `max_chars` 다.
MAX_CANDIDATES = int(os.environ.get("NODE_MAX_CANDIDATES", 2000))


def rank_text(
    weights_path: str,
    text_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`{"query": ..., "ranking": [...]}` 를 돌려준다."""
    if arch and arch != "RuleTextRank":
        raise ValueError(f"unknown rank arch {arch!r}; known=['RuleTextRank']")

    # 게이트·증적 일관성 — 파일은 읽지만 추론에는 쓰지 않는다.
    from safetensors.torch import load_file

    from app.infer_text import TextResourceLimitExceeded
    from app.tiny_rank import RuleTextRank

    state = load_file(weights_path)
    model = RuleTextRank()
    model.load_state_dict(state, strict=True)
    params = sum(p.numel() for p in model.parameters())
    cap = max_params or MAX_PARAMS_DEFAULT
    if params > cap:
        raise TextResourceLimitExceeded(f"params {params} > max_params {cap}")

    encoding, form, max_chars = resolve_text_preprocess(preprocess)
    text = read_text(text_path, encoding=encoding, max_chars=max_chars, form=form)
    out = rank_lines(text)
    if len(out["ranking"]) > MAX_CANDIDATES:
        raise TextResourceLimitExceeded(
            f"candidates {len(out['ranking'])} > max_candidates {MAX_CANDIDATES}"
        )
    return out
