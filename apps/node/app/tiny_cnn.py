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


ARCH_REGISTRY: dict[str, type[nn.Module]] = {
    "TinyEuroSAT": TinyEuroSAT,
    "TinyEuroSATB": TinyEuroSATB,
}


def build_model(arch: str = "TinyEuroSAT") -> nn.Module:
    try:
        return ARCH_REGISTRY[arch]()
    except KeyError as exc:
        raise ValueError(f"unknown arch {arch!r}; known={list(ARCH_REGISTRY)}") from exc
