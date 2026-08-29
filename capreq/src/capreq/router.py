from __future__ import annotations

import json
import os
import re
from typing import Any

from capreq.adapters.base import (
    CatalogSource,
    CapabilityInfo,
    ExecutionBackend,
    ExecutionResult,
    RouteDecision,
)
from capreq.ollama import OllamaClient

_JSON_BLOB = re.compile(r"\{[\s\S]*\}")


def _system_prompt(caps: list[CapabilityInfo]) -> str:
    lines = [
        "You are a capability router for an execution platform.",
        "Pick EXACTLY ONE capability from the ALLOWLIST below that best matches the user request.",
        "If none fit, set capability_code to null.",
        "Reply with JSON only, no markdown:",
        '{"capability_code": string|null, "capability_version": number|null,',
        ' "confidence": number, "reason": string}',
        "Rules:",
        "- capability_code MUST be copied exactly from the allowlist (or null).",
        "- capability_version MUST match the allowlist entry for that code.",
        "- confidence is 0..1.",
        "- Do not invent codes. Do not execute anything.",
        # 아래 세 줄은 성능 주장이 아니라 카탈로그의 사실을 옮긴 것이다.
        "- The request may be written in Korean; the allowlist is in English.",
        "- The part of a code before '.' is the input modality"
        " (image / text / table / timeseries). If an attachment is mentioned,"
        " prefer a code whose modality matches that file.",
        "- Match on the asked-for OUTPUT too: labels, spans/entities, a vector,"
        " a parsed table, or a forecast.",
        "",
        "ALLOWLIST:",
    ]
    for c in caps:
        desc = (c.description or "").replace("\n", " ").strip()
        if len(desc) > 180:
            desc = desc[:177] + "..."
        lines.append(
            f"- code={c.code} version={c.version} name={c.name!r} "
            f"kind={c.output_kind or '-'} desc={desc!r}"
        )
    return "\n".join(lines)


class CapabilityRouter:
    def __init__(
        self,
        catalog: CatalogSource,
        llm: OllamaClient | None = None,
        *,
        executor: ExecutionBackend | None = None,
        min_confidence: float | None = None,
    ) -> None:
        self.catalog = catalog
        self.llm = llm or OllamaClient()
        self.executor = executor
        self.min_confidence = (
            min_confidence
            if min_confidence is not None
            else float(os.environ.get("CAPREQ_MIN_CONFIDENCE", "0.45"))
        )

    def route(self, user_text: str) -> RouteDecision:
        caps = self.catalog.list_capabilities()
        if not caps:
            return RouteDecision(
                capability_code=None,
                capability_version=None,
                confidence=0.0,
                reason="등록된 능력이 없다",
                rejected=True,
            )
        raw = self.llm.chat(system=_system_prompt(caps), user=user_text.strip())
        parsed = _parse_decision(raw)
        if parsed is None:
            return RouteDecision(
                capability_code=None,
                capability_version=None,
                confidence=0.0,
                reason="모델 JSON 파싱 실패",
                raw_model=raw,
                rejected=True,
            )
        code = parsed.get("capability_code")
        ver = parsed.get("capability_version")
        conf = float(parsed.get("confidence") or 0.0)
        reason = str(parsed.get("reason") or "")
        if code is None or code == "null" or code == "":
            return RouteDecision(
                capability_code=None,
                capability_version=None,
                confidence=conf,
                reason=reason or "매칭되는 능력 없음",
                raw_model=raw,
            )
        code = str(code)
        try:
            ver_i = int(ver) if ver is not None else None
        except (TypeError, ValueError):
            ver_i = None
        matched = _find(caps, code, ver_i)
        if matched is None:
            # 버전만 빠진 경우 같은 code 최신(목록 순서상 첫) 시도
            matched = _find(caps, code, None)
        if matched is None:
            return RouteDecision(
                capability_code=code,
                capability_version=ver_i,
                confidence=conf,
                reason=f"allowlist에 없음: {code}@{ver_i} — {reason}",
                raw_model=raw,
                rejected=True,
            )
        if conf < self.min_confidence:
            return RouteDecision(
                capability_code=matched.code,
                capability_version=matched.version,
                confidence=conf,
                reason=f"confidence {conf:.2f} < {self.min_confidence} — {reason}",
                raw_model=raw,
                matched=matched,
                rejected=True,
            )
        return RouteDecision(
            capability_code=matched.code,
            capability_version=matched.version,
            confidence=conf,
            reason=reason,
            raw_model=raw,
            matched=matched,
        )

    def route_and_maybe_execute(
        self,
        user_text: str,
        *,
        dataset_id: str | None = None,
        case_id: str | None = None,
        input_id: str | None = None,
        execute: bool = False,
        extra: dict[str, Any] | None = None,
    ) -> tuple[RouteDecision, ExecutionResult | None]:
        decision = self.route(user_text)
        if not execute:
            return decision, None
        if not decision.ok or decision.capability_code is None:
            return decision, ExecutionResult(
                ok=False,
                detail={},
                message="라우팅 실패 — 실행하지 않음",
            )
        if self.executor is None:
            return decision, ExecutionResult(
                ok=False,
                detail={},
                message="ExecutionBackend 미연결",
            )
        result = self.executor.execute(
            capability_code=decision.capability_code,
            capability_version=int(decision.capability_version or 1),
            dataset_id=dataset_id,
            case_id=case_id,
            input_id=input_id,
            extra=extra,
        )
        return decision, result


def _find(
    caps: list[CapabilityInfo], code: str, version: int | None
) -> CapabilityInfo | None:
    for c in caps:
        if c.code != code:
            continue
        if version is None or c.version == version:
            return c
    return None


def _parse_decision(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_BLOB.search(text)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
