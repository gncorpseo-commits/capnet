"""이미지 임베딩 참조 구현 — **기존 가중치를 그대로 쓴다** (단계 6 ③).

## 무엇을 하나

`TinyEuroSAT` 의 **합성곱 트렁크만** 세워 128차원 벡터를 낸다.
분류기 머리(`head`)는 쓰지 않는다.

## 왜 새 가중치를 만들지 않았나

`eurosat_scratch.safetensors` 가 이미 저장소에 있다. 임베딩은 그 파일의 **앞부분**이므로
새로 학습할 것도, 새로 커밋할 것도 없다 — G-data 등급의 「기존 자산 재사용」이 실제로
무엇인지 보이는 사례다. 패키지도 커지지 않는다.

## `strict=False` 를 쓰지 않는다

머리 텐서를 버려야 하니 손쉬운 길은 `load_state_dict(..., strict=False)` 인데,
그러면 **트렁크 키가 하나 빠져 있어도 조용히 통과한다.** 랜덤 초기화된 층으로
추론하면서 벡터는 그럴듯하게 나온다 — 터지지 않고 틀리는 종류다.

그래서 키를 **명시적으로 걸러 내고, 기대한 키가 전부 있는지 확인한 뒤** strict 로 넣는다.

## 무엇을 주장하지 않는가

**의미적 유사도.** 이 트렁크는 10개 라벨 분류로 학습됐고, 그 표현이 다른 목적에
좋다는 근거는 없다. `image.embed` 는 `quality_profile='none'` 이라 골든셋도 채점도 없다.
"""

from __future__ import annotations

import torch
from torch import nn

# 트렁크 출력 차원. 계약(`output_schema.properties.vector.minItems/maxItems`)과 같아야 한다.
EMBED_DIM = 128

# 이 접두어를 가진 텐서만 쓴다. 나머지(`head.*`)는 분류기이며 임베딩에 필요 없다.
TRUNK_PREFIX = "features."


class TinyEuroSATEmbed(nn.Module):
    """`TinyEuroSAT` 의 트렁크. 층 구성이 **정확히 같아야** 키가 맞는다."""

    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.flatten(self.features(x), 1)


def load_trunk(model: TinyEuroSATEmbed, state: dict[str, torch.Tensor]) -> None:
    """분류기 텐서를 걸러 내고 트렁크만 넣는다. **빠진 키가 있으면 던진다.**"""
    wanted = set(model.state_dict().keys())
    trunk = {k: v for k, v in state.items() if k.startswith(TRUNK_PREFIX)}
    missing = wanted - set(trunk)
    if missing:
        raise ValueError(
            f"트렁크 텐서가 빠졌다: {sorted(missing)} — 이 가중치는 이 arch 가 아니다"
        )
    # strict=True. 여기까지 왔으면 키가 정확히 맞는다.
    model.load_state_dict({k: trunk[k] for k in wanted})
