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
            # Core apikey.py SCHEME 과 같아야 한다.
            h["authorization"] = f"CapNet-Key {self.api_key}"
        return h

    def upload_input(
        self,
        *,
        capability_code: str,
        capability_version: int,
        data: bytes,
        media_type: str,
    ) -> str:
        """Core 중개 입력 수집(D22). inputId 를 돌려준다."""
        url = (
            f"{self.core_url}/v1/inputs"
            f"?capability={capability_code}&version={capability_version}"
        )
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(
                url,
                headers={**self._headers(), "content-type": media_type},
                content=data,
            )
            if r.status_code >= 400:
                raise CapNetUploadError(
                    r.status_code,
                    _safe_json(r),
                )
            row = r.json()
            input_id = row.get("id")
            if not input_id:
                raise CapNetUploadError(r.status_code, row)
            return str(input_id)

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
        input_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        if input_id:
            # D8′ · Decision A — Core 가 받은 바이트면 allowlist 를 건너뛴다.
            body: dict[str, Any] = {
                "datasetId": dataset_id or "capreq-upload",
                "caseId": case_id or "upload-1",
                "capability_code": capability_code,
                "capability_version": capability_version,
                "inputId": input_id,
            }
        elif not dataset_id or not case_id:
            return ExecutionResult(
                ok=False,
                detail={},
                message=(
                    "CapNet 실행에는 input_id 또는 "
                    "dataset_id+case_id(allowlist) 가 필요하다."
                ),
            )
        else:
            body = {
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
        task_id = got.get("id")
        msg = "COMPLETED"
        if label:
            msg = f"COMPLETED label={label}"
        if task_id:
            msg = f"{msg} task={task_id}"
        return ExecutionResult(
            ok=True,
            detail=got,
            message=msg,
        )


class CapNetUploadError(Exception):
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"input upload HTTP {status_code}")


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

