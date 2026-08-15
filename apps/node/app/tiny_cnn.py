"""EuroSAT scratch용 소형 CNN. 사전학습 가중치 없음."""

from __future__ import annotations

import torch
from torch import nn

LABELS = (
    "annual_crop",
    "forest",
    "herbaceous_vegetation",
    "highway",
    "industrial",
    "pasture",
    "permanent_crop",
    "residential",
    "river",
    "sea_lake",
)


class TinyEuroSAT(nn.Module):
    """Agent A 데모 백본. 사전학습 없음."""

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
        self.head = nn.Linear(128, len(LABELS))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = torch.flatten(x, 1)
        return self.head(x)


class TinyEuroSATB(nn.Module):
    """Agent B용 다른 소형 scratch 백본 (채널·BN 상이). 사전학습 없음."""

    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )
        self.head = nn.Linear(64, len(LABELS))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = torch.flatten(x, 1)
        return self.head(x)


def _text_classifier() -> type[nn.Module]:
    # 지연 import — 이미지 경로만 쓰는 곳에서 텍스트 모듈을 끌고 오지 않는다.
    from app.tiny_text import TinyTextClassifier

    return TinyTextClassifier


def _text_embedder() -> type[nn.Module]:
    from app.tiny_embed import TinyTextEmbedder

    return TinyTextEmbedder


def _series_forecaster() -> type[nn.Module]:
    from app.tiny_series import TinySeriesForecaster

    return TinySeriesForecaster


ARCH_REGISTRY: dict[str, type[nn.Module]] = {
    "TinyEuroSAT": TinyEuroSAT,
    "TinyEuroSATB": TinyEuroSATB,
    "TinyTextClassifier": _text_classifier(),
    "TinyTextEmbedder": _text_embedder(),
    "TinySeriesForecaster": _series_forecaster(),
}

# arch → 모달리티. **실행기 디스패치의 정본이다** (단계 5).
#
# 전처리 어휘로도 짐작할 수 있지만(`is_text_preprocess`), 그건 계약만 있고 arch 를
# 모를 때의 차선책이다. arch 는 Core 가 말한 값이고 게이트가 그 값으로 승인했으므로,
# 「승인한 것과 실행한 것이 같다」를 지키려면 여기서 갈라야 한다 (I1).
ARCH_MODALITY: dict[str, str] = {
    "TinyEuroSAT": "image",
    "TinyEuroSATB": "image",
    "TinyTextClassifier": "text",
    # 임베딩도 텍스트를 읽는다. 다른 것은 **출력**이다 — 라벨이 아니라 벡터.
    "TinyTextEmbedder": "text_embed",
    # 세 번째 모달리티 어휘 — 표/시계열 (단계 6 ②).
    "TinySeriesForecaster": "series",
}


def build_model(arch: str = "TinyEuroSAT") -> nn.Module:
    try:
        return ARCH_REGISTRY[arch]()
    except KeyError as exc:
        raise ValueError(f"unknown arch {arch!r}; known={list(ARCH_REGISTRY)}") from exc
