"""텍스트 임베딩 참조 구현 — scratch (단계 6 ①).

## 무엇을 하나

문자 n-gram 해시 가방(`text_features`)을 **선형 사영**해 고정 차원 벡터를 낸다.
`text.classify` 와 **같은 특징 추출**을 쓴다 — 두 벌을 만들지 않는다(D3 의 이유).

## 왜 이 능력이 먼저인가

**새 학습 데이터가 필요 없다.** 텍스트 특징·전처리가 이미 있고, 출력은 벡터라
라벨이 없다. 그리고 `structured` 의 **첫 사례**라, D-out(배열·중첩 검증)이 실제로
도는지가 이 능력 하나로 드러난다 — 임베딩 계약은 「차원이 맞는가·수치인가」가 전부다.

## 무엇을 주장하지 않는가

**의미적 유사도.** 이 사영은 scratch 로 학습된 것이 아니라 **고정 시드로 초기화**된
선형 변환이다. 같은 입력이 같은 벡터를 내고 다른 입력이 다른 벡터를 낸다는 것 —
그 이상은 말하지 않는다. `quality_profile='none'` 이라 골든셋도 채점도 없다.

「임베딩이니까 검색이 잘 된다」로 읽히지 않게 카탈로그에도 같은 문장을 적어 둔다.
"""

from __future__ import annotations

import torch.nn as nn

from app.text_features import HASH_DIM

# 출력 차원. 계약(`output_schema.properties.vector.minItems/maxItems`)과 같아야 한다 —
# 그 일치를 D-out 이 실제로 검사한다.
EMBED_DIM = 64


class TinyTextEmbedder(nn.Module):
    """해시 가방 → 선형 사영. 비선형이 없는 것이 의도다.

    보이려는 것은 **경로**이지 표현 학습이 아니다.
    """

    def __init__(self, dim: int = EMBED_DIM) -> None:
        super().__init__()
        self.projection = nn.Linear(HASH_DIM, dim, bias=False)

    def forward(self, x):  # noqa: ANN001, ANN201 - torch 텐서
        return self.projection(x)
