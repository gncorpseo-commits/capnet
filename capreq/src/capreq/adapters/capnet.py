from __future__ import annotations

import json
import time
from typing import Any

import httpx

from capreq.adapters.base import CapabilityInfo, ExecutionResult
from capreq.results import extract_label

# task.status 종결값 (schema.sql). TIMEOUT·CANCELED 도 폴링을 멈춰야 한다.
TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "TIMEOUT", "CANCELED"})


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
        transport: Any | None = None,
    ) -> None:
        self.core_url = core_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.poll_seconds = poll_seconds
        self.poll_max = poll_max
        # 테스트 이음매 — `httpx.MockTransport` 를 꽂아 Core 없이 검증한다.
        self.transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout, transport=self.transport)

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
        with self._client() as client:
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
        with self._client() as client:
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

    def _task_body(
        self,
        *,
        capability_code: str,
        capability_version: int,
        dataset_id: str | None,
        case_id: str | None,
        input_id: str | None,
        extra: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Task 본문. 입력 근거가 없으면 None (호출자가 거절 메시지를 만든다)."""
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
            return None
        else:
            body = {
                "datasetId": dataset_id,
                "caseId": case_id,
                "capability_code": capability_code,
                "capability_version": capability_version,
            }
        if extra:
            body.update(extra)
        return body

    def create_task(
        self,
        *,
        capability_code: str,
        capability_version: int,
        dataset_id: str | None = None,
        case_id: str | None = None,
        input_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Task 를 만들고 **기다리지 않는다.** 상태는 `get_task` 로 따로 본다."""
        body = self._task_body(
            capability_code=capability_code,
            capability_version=capability_version,
            dataset_id=dataset_id,
            case_id=case_id,
            input_id=input_id,
            extra=extra,
        )
        if body is None:
            raise CapNetTaskError(
                0,
                "CapNet 실행에는 input_id 또는 dataset_id+case_id(allowlist) 가 필요하다.",
            )
        with self._client() as client:
            r = client.post(
                f"{self.core_url}/v1/tasks",
                headers={**self._headers(), "content-type": "application/json"},
                content=json.dumps(body),
            )
            if r.status_code >= 400:
                raise CapNetTaskError(r.status_code, _safe_json(r))
            task = r.json()
        if not task.get("id"):
            raise CapNetTaskError(r.status_code, task)
        return task

    def get_task(
        self, task_id: str, *, client: httpx.Client | None = None
    ) -> dict[str, Any]:
        """`client` 를 주면 그 연결을 재사용한다 — 폴링이 90번 새로 연결하지 않게."""
        if client is not None:
            return self._get_task(client, task_id)
        with self._client() as own:
            return self._get_task(own, task_id)

    def _get_task(self, client: httpx.Client, task_id: str) -> dict[str, Any]:
        r = client.get(f"{self.core_url}/v1/tasks/{task_id}", headers=self._headers())
        if r.status_code >= 400:
            raise CapNetTaskError(r.status_code, _safe_json(r))
        return r.json()

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
        """Task 를 만들고 종결 상태까지 폴링한다."""
        try:
            task = self.create_task(
                capability_code=capability_code,
                capability_version=capability_version,
                dataset_id=dataset_id,
                case_id=case_id,
                input_id=input_id,
                extra=extra,
            )
        except CapNetTaskError as exc:
            if exc.status_code == 0:
                return ExecutionResult(ok=False, detail={}, message=str(exc.body))
            return ExecutionResult(
                ok=False,
                detail={"status_code": exc.status_code, "body": exc.body},
                message=f"Task 생성 실패 HTTP {exc.status_code}",
            )
        except httpx.HTTPError as exc:
            return ExecutionResult(ok=False, detail={}, message=f"Core 통신 실패: {exc}")

        task_id = str(task["id"])
        got: dict[str, Any] = task
        try:
            # 연결 하나로 끝까지 본다. 매 회 새로 열면 poll_max 만큼 TCP 를 낭비한다.
            with self._client() as client:
                for _ in range(self.poll_max):
                    got = self.get_task(task_id, client=client)
                    if got.get("status") in TERMINAL_STATUSES:
                        break
                    time.sleep(self.poll_seconds)
        except CapNetTaskError as exc:
            return ExecutionResult(
                ok=False,
                detail={"status_code": exc.status_code, "body": exc.body},
                message=f"Task 조회 실패 HTTP {exc.status_code}",
            )
        except httpx.HTTPError as exc:
            return ExecutionResult(ok=False, detail=got, message=f"Core 통신 실패: {exc}")

        if got.get("status") != "COMPLETED":
            return ExecutionResult(
                ok=False,
                detail=got,
                message=f"Task 미완료 status={got.get('status')}",
            )
        label = extract_label(got)
        msg = "COMPLETED"
        if label:
            msg = f"COMPLETED label={label}"
        return ExecutionResult(ok=True, detail=got, message=f"{msg} task={task_id}")


class CapNetTaskError(Exception):
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"task HTTP {status_code}")


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
