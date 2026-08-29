"""CapNet 어댑터 — `httpx.MockTransport` 로 Core 없이.

여기서 보는 것은 세 가지다.
  1) D8′ · D22 — 첨부가 있으면 `inputId` 로, 없으면 dataset/case 로 Task 를 만든다
  2) 폴링이 **종결 상태 전부**에서 멈춘다 (TIMEOUT·CANCELED 포함)
  3) HTTP 오류가 예외가 아니라 `ExecutionResult(ok=False)` 로 내려온다
"""

from __future__ import annotations

import json
import unittest

import httpx

from capreq.adapters.capnet import CapNetAdapter, CapNetTaskError

TASK_ID = "11111111-1111-1111-1111-111111111111"


def _adapter(handler, **kw) -> CapNetAdapter:
    return CapNetAdapter(
        "http://core.test",
        transport=httpx.MockTransport(handler),
        poll_seconds=0.0,
        **kw,
    )


class TestCreateTask(unittest.TestCase):
    def test_input_id_body(self) -> None:
        seen: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(json.loads(request.content))
            return httpx.Response(200, json={"id": TASK_ID, "status": "QUEUED"})

        task = _adapter(handler).create_task(
            capability_code="text.ner", capability_version=1, input_id="in-1"
        )
        self.assertEqual(task["status"], "QUEUED")
        self.assertEqual(seen["inputId"], "in-1")
        self.assertEqual(seen["capability_code"], "text.ner")
        self.assertEqual(seen["datasetId"], "capreq-upload")

    def test_allowlist_body(self) -> None:
        seen: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(json.loads(request.content))
            return httpx.Response(200, json={"id": TASK_ID, "status": "QUEUED"})

        _adapter(handler).create_task(
            capability_code="image.classify",
            capability_version=1,
            dataset_id="eurosat-rgb",
            case_id="ic1-0001",
        )
        self.assertEqual(seen["caseId"], "ic1-0001")
        self.assertNotIn("inputId", seen)

    def test_no_input_basis_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError("입력 근거가 없으면 Core 를 부르지 않는다")

        with self.assertRaises(CapNetTaskError) as ctx:
            _adapter(handler).create_task(
                capability_code="text.ner", capability_version=1
            )
        self.assertEqual(ctx.exception.status_code, 0)

    def test_api_key_header(self) -> None:
        seen: list[str | None] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get("authorization"))
            return httpx.Response(200, json={"id": TASK_ID, "status": "QUEUED"})

        CapNetAdapter(
            "http://core.test", api_key="ck_x", transport=httpx.MockTransport(handler)
        ).create_task(capability_code="text.ner", capability_version=1, input_id="in-1")
        self.assertEqual(seen, ["CapNet-Key ck_x"])


class TestExecute(unittest.TestCase):
    def _poll_handler(self, statuses: list[str], result: dict | None = None):
        seq = list(statuses)

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST":
                return httpx.Response(200, json={"id": TASK_ID, "status": "QUEUED"})
            status = seq.pop(0) if seq else "COMPLETED"
            body: dict[str, object] = {"id": TASK_ID, "status": status}
            if status == "COMPLETED" and result is not None:
                body["result_ref"] = json.dumps(result)
            return httpx.Response(200, json=body)

        return handler

    def test_completed_carries_label(self) -> None:
        exe = _adapter(
            self._poll_handler(
                ["QUEUED", "RUNNING", "COMPLETED"],
                {"label": "email", "confidence": 0.9, "weights_sha256": "ab"},
            )
        ).execute(capability_code="text.classify", capability_version=1, input_id="in-1")
        self.assertTrue(exe.ok)
        self.assertIn("label=email", exe.message)
        self.assertEqual(exe.detail["status"], "COMPLETED")

    def test_polling_stops_on_timeout_status(self) -> None:
        # TIMEOUT 을 종결로 보지 않으면 poll_max 까지 헛돈다.
        exe = _adapter(self._poll_handler(["TIMEOUT"]), poll_max=3).execute(
            capability_code="text.ner", capability_version=1, input_id="in-1"
        )
        self.assertFalse(exe.ok)
        self.assertIn("TIMEOUT", exe.message)

    def test_create_error_is_result_not_exception(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"detail": "capability not found"})

        exe = _adapter(handler).execute(
            capability_code="text.ner", capability_version=1, input_id="in-1"
        )
        self.assertFalse(exe.ok)
        self.assertIn("HTTP 400", exe.message)
        self.assertEqual(exe.detail["status_code"], 400)

    def test_missing_input_basis_is_result(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError("호출되면 안 된다")

        exe = _adapter(handler).execute(
            capability_code="text.ner", capability_version=1
        )
        self.assertFalse(exe.ok)
        self.assertIn("input_id", exe.message)


class TestCatalog(unittest.TestCase):
    def test_list_capabilities(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "code": "text.ner",
                            "version": 1,
                            "name": "structural text ner",
                            "description": "spans",
                            "output_kind": "structured",
                        }
                    ]
                },
            )

        caps = _adapter(handler).list_capabilities()
        self.assertEqual(len(caps), 1)
        self.assertEqual(caps[0].key, "text.ner@1")


if __name__ == "__main__":
    unittest.main()
