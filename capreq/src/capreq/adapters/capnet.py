from __future__ import annotations

import json
from typing import Any

import httpx

from capreq.adapters.base import CapabilityInfo, ExecutionResult


class CapNetAdapter:
    """CapNet Core HTTP 어댑터.

    - 카탈로그: GET /v1/capabilities
    - 실행: POST /v1/tasks (Agent 미지정) + 폴링
    """

    def __init__(
        self,
        core_url: str = "http://127.0.0.1:8000",
        *,
        api_key: str | None = None,
        timeout: float = 120.0,
        poll_seconds: float = 1.0,
        poll_max: int = 90,
    ) -> None:
        self.core_url = core_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.poll_seconds = poll_seconds
        self.poll_max = poll_max

    def _headers(self) -> dict[str, str]:
        h = {"accept": "application/json"}
        if self.api_key:
            h["authorization"] = f"Bearer {self.api_key}"
        return h

    def list_capabilities(self) -> list[CapabilityInfo]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(f"{self.core_url}/v1/capabilities", headers=self._headers())
            r.raise_for_status()
            items = r.json().get("items") or []
        out: list[CapabilityInfo] = []
        for it in items:
            out.append(
                CapabilityInfo(
                    code=str(it["code"]),
                    version=int(it["version"]),
                    name=str(it.get("name") or it["code"]),
                    description=str(it.get("description") or ""),
                    output_kind=it.get("output_kind"),
                    trust_domain_min=it.get("trust_domain_min"),
                    extra={
                        k: it[k]
                        for k in ("id", "compute_tier", "quality_profile", "mvp_eligible")
                        if k in it
                    },
                )
            )
        return out

    def execute(
        self,
        *,
        capability_code: str,
        capability_version: int,
        dataset_id: str | None = None,
        case_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        if not dataset_id or not case_id:
            return ExecutionResult(
                ok=False,
                detail={},
                message="CapNet 실행에는 dataset_id 와 case_id 가 필요하다 (allowlist).",
            )
        body: dict[str, Any] = {
            "datasetId": dataset_id,
            "caseId": case_id,
            "capability_code": capability_code,
            "capability_version": capability_version,
        }
        if extra:
            body.update(extra)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(
                    f"{self.core_url}/v1/tasks",
                    headers={**self._headers(), "content-type": "application/json"},
                    content=json.dumps(body),
                )
                if r.status_code >= 400:
                    return ExecutionResult(
                        ok=False,
                        detail={"status_code": r.status_code, "body": _safe_json(r)},
                        message=f"Task 생성 실패 HTTP {r.status_code}",
                    )
                task = r.json()
                task_id = task.get("id")
                if not task_id:
                    return ExecutionResult(
                        ok=False, detail=task, message="Task id 없음"
                    )
                got = None
                for _ in range(self.poll_max):
                    pr = client.get(
                        f"{self.core_url}/v1/tasks/{task_id}",
                        headers=self._headers(),
                    )
                    pr.raise_for_status()
                    got = pr.json()
                    if got.get("status") in ("COMPLETED", "FAILED"):
                        break
                    import time

                    time.sleep(self.poll_seconds)
        except httpx.HTTPError as exc:
            return ExecutionResult(
                ok=False, detail={}, message=f"Core 통신 실패: {exc}"
            )

        if not got:
            return ExecutionResult(ok=False, detail={}, message="폴링 결과 없음")
        if got.get("status") != "COMPLETED":
            return ExecutionResult(
                ok=False,
                detail=got,
                message=f"Task 미완료 status={got.get('status')}",
            )
        label = _extract_label(got)
        return ExecutionResult(
            ok=True,
            detail=got,
            message=f"COMPLETED label={label}" if label else "COMPLETED",
        )


def _safe_json(r: httpx.Response) -> Any:
    try:
        return r.json()
    except Exception:
        return r.text[:500]


def _extract_label(task: dict[str, Any]) -> str | None:
    ref = task.get("result_ref")
    if isinstance(ref, str):
        try:
            ref = json.loads(ref)
        except json.JSONDecodeError:
            return None
    if isinstance(ref, dict):
        lab = ref.get("label")
        return str(lab) if lab is not None else None
    return None

