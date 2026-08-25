from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class CapabilityInfo:
    """백엔드에 등록된 능력 한 줄 — LLM allowlist 항목."""

    code: str
    version: int
    name: str
    description: str = ""
    output_kind: str | None = None
    trust_domain_min: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.code}@{self.version}"


@dataclass
class RouteDecision:
    """라우팅 결과. 실행 성공과 무관하게 '능력을 골랐는지'가 1차 성공이다."""

    capability_code: str | None
    capability_version: int | None
    confidence: float
    reason: str
    raw_model: str = ""
    matched: CapabilityInfo | None = None
    rejected: bool = False  # allowlist 밖·파싱 실패 등

    @property
    def ok(self) -> bool:
        return (
            not self.rejected
            and self.capability_code is not None
            and self.capability_version is not None
            and self.matched is not None
        )


@dataclass
class ExecutionResult:
    ok: bool
    detail: dict[str, Any]
    message: str = ""


class CatalogSource(Protocol):
    def list_capabilities(self) -> list[CapabilityInfo]:
        ...


class ExecutionBackend(Protocol):
    """선택. 없으면 라우팅만 한다."""

    def execute(
        self,
        *,
        capability_code: str,
        capability_version: int,
        dataset_id: str | None = None,
        case_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        ...
