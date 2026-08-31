"""`safety.pii` 실행기 — 규칙 기반 PII **참고** (Wave L).

**탐지가 아니라 참고다.** 선언한 패턴만 보고, 놓친 것이 없다고 말하지 않는다.
`quality_profile='none'` · 골든셋 없음. 규칙 전문과 그 한계는 `app.pii_rules`.
"""

from __future__ import annotations

import os
from typing import Any

from app.infer_text import read_text
from app.limits import MAX_PARAMS_DEFAULT
from app.pii_rules import find_pii
from app.preprocess import resolve_text_preprocess

# **자르지 않고 던진다** (`text.extract` 의 `MAX_FIELDS` 와 같은 규율). 잘라서 돌려주면
# 「전부 찾아봤다」가 거짓이 되고, **PII 능력에서 그 거짓말은 특히 나쁘다.**
# 계약이 정하는 것은 `max_chars` 다.
MAX_FINDINGS = int(os.environ.get("NODE_MAX_PII_FINDINGS", 2000))


def scan_pii(
    weights_path: str,
    text_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`{"patterns_checked": [...], "findings": [...]}` 를 돌려준다."""
    if arch and arch != "RuleTextPii":
        raise ValueError(f"unknown pii arch {arch!r}; known=['RuleTextPii']")

    # 게이트·증적 일관성 — 파일은 읽지만 추론에는 쓰지 않는다.
    from safetensors.torch import load_file

    from app.infer_text import TextResourceLimitExceeded
    from app.tiny_pii import RuleTextPii

    state = load_file(weights_path)
    model = RuleTextPii()
    model.load_state_dict(state, strict=True)
    params = sum(p.numel() for p in model.parameters())
    cap = max_params or MAX_PARAMS_DEFAULT
    if params > cap:
        raise TextResourceLimitExceeded(f"params {params} > max_params {cap}")

    encoding, form, max_chars = resolve_text_preprocess(preprocess)
    text = read_text(text_path, encoding=encoding, max_chars=max_chars, form=form)
    out = find_pii(text)
    if len(out["findings"]) > MAX_FINDINGS:
        raise TextResourceLimitExceeded(
            f"findings {len(out['findings'])} > max_findings {MAX_FINDINGS}"
        )
    return out
