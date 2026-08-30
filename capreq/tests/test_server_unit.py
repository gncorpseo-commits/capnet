"""capreq 웹 서버 경로 — Core·Ollama 없이 (FastAPI TestClient).

## 왜 있는가

**첨부 분기가 한 번도 실행된 적이 없었다.** `request.form()` 은 starlette 의
`UploadFile` 을 돌려주는데 코드가 `fastapi.UploadFile`(그 *하위* 클래스)로
`isinstance` 를 했다 — 항상 False 라 파일이 조용히 버려지고, 요청은 allowlist 데모
경로로 떨어져 **영원히 QUEUED 인 작업**을 만들었다. 2026-08-30 종단 실측에서 잡았다.

서버 경로에 검사가 하나도 없어서 그때까지 아무도 몰랐다. 그래서 여기서 고정한다 —
**파일이 실제로 Core 로 올라가는가**와 **못 돌 요청을 미리 거절하는가**.
"""

from __future__ import annotations

import json
import unittest
from typing import Any

from fastapi.testclient import TestClient

import capreq.server as server
from capreq.adapters.base import CapabilityInfo, ExecutionResult

TASK_ID = "11111111-1111-1111-1111-111111111111"
INPUT_ID = "22222222-2222-2222-2222-222222222222"


class FakeLLM:
    """고정 라우팅. 실제 모델을 부르지 않는다."""

    def __init__(self, code: str = "text.ner", version: int = 1, **_: Any) -> None:
        self.code, self.version = code, version

    def chat(self, *, system: str, user: str) -> str:
        FakeLLM.last_user = user  # 프롬프트에 첨부 힌트가 붙었는지 보려고 남긴다
        return json.dumps({
            "capability_code": self.code, "capability_version": self.version,
            "confidence": 0.95, "reason": "fake",
        })


class FakeCore:
    """Core 대역. 무엇이 불렸는지만 기록한다."""

    def __init__(self, *_: Any, **__: Any) -> None:
        self.uploads: list[dict[str, Any]] = []
        self.tasks: list[dict[str, Any]] = []

    def list_capabilities(self) -> list[CapabilityInfo]:
        return [
            CapabilityInfo(code="text.ner", version=1, name="ner", output_kind="structured"),
            CapabilityInfo(code="image.classify", version=1, name="ic",
                           output_kind="closed_set_labels"),
        ]

    def upload_input(self, *, capability_code, capability_version, data, media_type):
        self.uploads.append({"code": capability_code, "bytes": data, "mime": media_type})
        return INPUT_ID

    def create_task(self, **kw: Any) -> dict[str, Any]:
        self.tasks.append(kw)
        return {"id": TASK_ID, "status": "QUEUED"}

    def execute(self, **kw: Any) -> ExecutionResult:
        self.tasks.append(kw)
        return ExecutionResult(ok=True, detail={"id": TASK_ID, "status": "COMPLETED",
                                                "result_ref": json.dumps({"entities": []})},
                              message="COMPLETED")

    def get_task(self, task_id: str) -> dict[str, Any]:
        return {"id": task_id, "status": "COMPLETED",
                "result_ref": json.dumps({"entities": [], "dummy": False})}


class ServerCase(unittest.TestCase):
    route_to = ("text.ner", 1)

    def setUp(self) -> None:
        self._llm, self._core = server.OllamaClient, server.CapNetAdapter
        code, ver = self.route_to
        server.OllamaClient = lambda **kw: FakeLLM(code, ver)  # type: ignore[assignment]
        self.core = FakeCore()
        server.CapNetAdapter = lambda *a, **kw: self.core  # type: ignore[assignment]
        self.client = TestClient(server.create_app(core="http://core.test", catalog_json=None))

    def tearDown(self) -> None:
        server.OllamaClient, server.CapNetAdapter = self._llm, self._core


class TestAttachment(ServerCase):
    def test_multipart_file_reaches_core(self) -> None:
        """이 검사가 없어서 첨부가 통째로 버려지는 것을 못 잡았다."""
        r = self.client.post(
            "/api/chat",
            data={"message": "이메일 찾아줘", "execute": "true", "wait": "false"},
            files={"file": ("in.txt", b"ops@example.dev", "text/plain")},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(len(self.core.uploads), 1, "파일이 Core 로 올라가지 않았다")
        self.assertEqual(self.core.uploads[0]["bytes"], b"ops@example.dev")
        self.assertEqual(body["input_id"], INPUT_ID, "응답에 inputId 가 없다")
        self.assertEqual(self.core.tasks[0]["input_id"], INPUT_ID,
                         "작업이 inputId 없이 만들어졌다 — 영원히 QUEUED 가 된다")

    def test_prompt_carries_the_attachment_hint(self) -> None:
        """첨부를 라우터에게 알려야 모달리티가 맞는 능력이 뽑힌다."""
        self.client.post(
            "/api/chat",
            data={"message": "찾아줘", "execute": "false"},
            files={"file": ("in.txt", b"x", "text/plain")},
        )
        self.assertIn("[첨부:", FakeLLM.last_user)

    def test_mime_is_checked_before_upload(self) -> None:
        r = self.client.post(
            "/api/chat",
            data={"message": "분류해줘", "execute": "true"},
            files={"file": ("a.png", b"\x89PNG", "image/png")},
        )
        body = r.json()
        self.assertEqual(self.core.uploads, [], "계약 밖 MIME 을 올려 보냈다")
        self.assertFalse(body["execution_ok"])
        self.assertIn("text.ner", body["execution_message"])


class TestNoDoomedTask(ServerCase):
    def test_text_capability_without_file_is_refused(self) -> None:
        """이미지 밖 모달리티에는 로컬 골든 폴백이 없다 (D8′).

        보내면 Node 가 400 을 내고 작업은 재시도 끝에 FAILED 가 된다 — 실측했다.
        만들지 않는 편이 낫다.
        """
        r = self.client.post("/api/chat", json={"message": "찾아줘", "execute": True})
        body = r.json()
        self.assertEqual(self.core.tasks, [], "못 돌 작업을 만들었다")
        self.assertFalse(body["execution_ok"])
        self.assertIn("첨부", body["execution_message"])


class TestImageStillUsesAllowlist(ServerCase):
    route_to = ("image.classify", 1)

    def test_image_without_file_keeps_the_demo_path(self) -> None:
        """데모 경로(caseId)는 이미지에만 남는다 — 그건 깨지 않는다."""
        r = self.client.post("/api/chat", json={"message": "분류해줘", "execute": True})
        self.assertEqual(r.json()["execution_ok"], True)
        self.assertEqual(self.core.tasks[0]["dataset_id"], "eurosat-rgb")


class TestTaskPolling(ServerCase):
    def test_task_state_summarises(self) -> None:
        st = self.client.get(f"/api/tasks/{TASK_ID}").json()
        self.assertTrue(st["ok"])
        self.assertEqual(st["status"], "COMPLETED")
        self.assertTrue(st["done"])


if __name__ == "__main__":
    unittest.main()
