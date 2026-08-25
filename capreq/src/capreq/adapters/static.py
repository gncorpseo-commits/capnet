from __future__ import annotations

"""파일/정적 카탈로그 — Core 없이 라우팅만 시험할 때."""

import json
from pathlib import Path

from capreq.adapters.base import CapabilityInfo, ExecutionResult


class StaticCatalog:
    def __init__(self, items: list[CapabilityInfo]) -> None:
        self._items = list(items)

    @classmethod
    def from_json_file(cls, path: str | Path) -> StaticCatalog:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        items = [
            CapabilityInfo(
                code=str(it["code"]),
                version=int(it.get("version", 1)),
                name=str(it.get("name") or it["code"]),
                description=str(it.get("description") or ""),
                output_kind=it.get("output_kind"),
            )
            for it in data
        ]
        return cls(items)

    def list_capabilities(self) -> list[CapabilityInfo]:
        return list(self._items)


class NoExecute:
    """실행 백엔드 없음 — 연결 해제 상태."""

    def execute(self, **kwargs) -> ExecutionResult:  # type: ignore[no-untyped-def]
        return ExecutionResult(
            ok=False,
            detail=dict(kwargs),
            message="ExecutionBackend 미연결 — 라우팅만 수행됨",
        )
