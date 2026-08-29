"""규칙 기반 필드 추출 — 가중치 파일은 증적용 자리표시자뿐이다.

추론은 `extract_patterns` 의 줄 규칙으로 한다. `RuleTextExtract` 는 safetensors·지문·
`max_params` 게이트가 성립하도록 **파라미터 0 인 torch 모듈**이다 — 「모델 없이도 됨」(step6 §3).
`RuleTextNer` 와 같은 모양이고, 같은 이유로 버퍼 한 칸을 둔다.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class RuleTextExtract(nn.Module):
    """학습 가능 파라미터 0.

    **버퍼 한 칸을 둔다.** state dict 가 완전히 비면 `weights_fingerprint` 가
    「텐서가 하나도 없다」로 실패한다 — 그 검사는 빈 파일·잘린 파일을 잡는 것이라
    약화시키지 않는다. 버퍼는 `parameters()` 에 들어가지 않으므로 `max_params`
    검사에서 파라미터 수는 여전히 **0** 이다 (PR-B 에서 한 번 걸리고 배운 것).
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_buffer("rule_marker", torch.zeros(1, dtype=torch.float32))
