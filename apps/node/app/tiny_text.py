"""텍스트 분류 참조 구현 — scratch (단계 5).

## 무엇을 분류하나

짧은 문자열의 **구조 종류**다. `email` · `url` · `ipv4` · `uuid` · `iso_date` · `plain`.

## 왜 이 과제인가

**외부 말뭉치를 쓰지 않아도 되기 때문이다.** 학습 데이터를 규칙으로 **생성**할 수 있으므로
라이선스가 붙지 않는다 — 절대규칙 6(사전학습 금지)과 대회 2차 라이선스 검증에
새로 얹을 것이 없다. 감정 분석·주제 분류였다면 남의 말뭉치가 필요했다.

그리고 쓸모없는 과제도 아니다. 「이 필드가 이메일인가 IP 인가」는 문서 라우팅·PII 선별의
앞단에서 실제로 쓰인다.

## 무엇을 주장하지 않는가

`text.classify` 는 카탈로그에서 **`quality_profile='none'`** 이다. 골든셋도 채점도 없다 —
**품질을 주장하지 않는다.** 이 모델이 있는 이유는 「텍스트 모달리티가 계약 게이트와
실행 경로를 통과한다」를 보이기 위해서지, 분류 성능을 파는 것이 아니다.
성능 수치를 제품 문구에 쓰지 않는다.

## 구조

해시된 문자 n-gram 가방(`text_features`) → `Linear`. 그것뿐이다.
4096 × 6 + 6 = **24,582 파라미터**. CPU 에서 몇 초면 scratch 로 학습된다.
"""

from __future__ import annotations

import torch.nn as nn

from app.text_features import HASH_DIM

# 닫힌 라벨 집합. 계약(`output_schema.properties.label.enum`)과 **같은 순서**여야 한다 —
# 인덱스가 라벨로 되돌아가는 경로가 여기 하나뿐이다.
TEXT_LABELS = ("email", "url", "ipv4", "uuid", "iso_date", "plain")


class TinyTextClassifier(nn.Module):
    """해시 가방 → 선형 분류기. 은닉층이 없는 것이 의도다.

    더 큰 모델을 쓰면 「무엇이 계약을 통과시켰는가」가 흐려진다. 여기서 보이려는 것은
    **경로**이지 모델이 아니다.
    """

    def __init__(self, num_labels: int = len(TEXT_LABELS)) -> None:
        super().__init__()
        self.classifier = nn.Linear(HASH_DIM, num_labels)

    def forward(self, x):  # noqa: ANN001, ANN201 - torch 텐서
        return self.classifier(x)
