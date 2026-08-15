"""시계열 예측 참조 구현 — scratch (단계 6 ②).

## 무엇을 하나

정규화된 과거 `WINDOW` 개 → 앞으로 `HORIZON` 개. **선형 자기회귀**다.

## 왜 이 능력인가

**세 번째 모달리티 어휘**(`table`)를 처음 시험한다. 텍스트·이미지가 아닌 입력이
같은 계약 형판(선언 → 러너가 적용 → 실추론 → 출력 대조)으로 도는지가 여기서 드러난다.

학습 데이터는 **규칙으로 생성**한다(추세 + 계절성 + 잡음). 외부 데이터가 0 이라
절대규칙 6 과 2차 라이선스 검증에 얹을 것이 없다 — `text.classify` 와 같은 기준이다.

## 무엇을 주장하지 않는가

**실제 시계열에서의 예측 정확도.** 합성 데이터로 학습했고 `quality_profile='none'` 이라
골든셋도 채점도 없다. 이 모델이 있는 이유는 **경로**를 보이기 위해서다.
"""

from __future__ import annotations

import torch.nn as nn

from app.series_features import HORIZON, WINDOW


class TinySeriesForecaster(nn.Module):
    """`Linear(WINDOW, HORIZON)`. 은닉층이 없는 것이 의도다."""

    def __init__(self, window: int = WINDOW, horizon: int = HORIZON) -> None:
        super().__init__()
        self.head = nn.Linear(window, horizon)

    def forward(self, x):  # noqa: ANN001, ANN201 - torch 텐서
        return self.head(x)
