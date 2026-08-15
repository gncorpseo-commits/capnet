"""작업 접수 — `inputId` 가 있으면 datasetId allowlist 를 건너뛴다 (D8′ · Decision A).

## 왜 있는가

allowlist 는 **비통제 수집**을 막으려고 있다(D8′). 그런데 `POST /v1/tasks` 에서
**무조건** 돌아서, 이미지 밖 모든 작업이 막혔다 — 텍스트 작업에는 맞는 `datasetId` 가 없고,
통과시키려면 `eurosat-rgb` 를 적어야 했다. 그러면 **증적에 없던 데이터셋이 남는다.**

「내 데이터가 어디로 갔는지 답한다」가 제품 주장인데, 그 답을 거짓으로 만드는 관문이었다.

## 여기서 고정하는 것

1. **`inputId` 가 있을 때만** 건너뛴다 — 없으면 종전대로 막는다
2. **건너뛰기가 무검증이 아니다** — 입력 존재·상태 확인은 그대로 (그 앞을 지나갈 수 없다)
3. **바이트를 받는 문은 안 건드렸다** — `POST /v1/inputs` 의 계약·해시·크기·MIME 대조 유지

## 판정 방식과 그 한계

라우트 소스를 본다. 실제 HTTP 판정(400/200/404)은 `scripts/text_demo.sh` 와
격리 스택 실측이 했다 — 2026-08-16 결과를 문서에 적어 뒀다.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

MAIN = ROOT / "apps" / "core" / "app" / "main.py"


class TestIntakeGuard(unittest.TestCase):
    def setUp(self) -> None:
        code = code_only(MAIN)
        i = code.index('@app.post("/v1/tasks")')
        rest = code[i + 20:]
        j = rest.find("\n@app.")
        self.body = code[i:i + 20 + (j if j != -1 else len(rest))]

    def test_allowlist_is_conditional_on_input_id(self) -> None:
        """`assert_dataset_id` 가 `body.input_id is None` 아래에 있어야 한다."""
        self.assertIn("if body.input_id is None:", self.body)
        guard = self.body.index("if body.input_id is None:")
        call = self.body.index("assert_dataset_id(")
        self.assertLess(guard, call, "allowlist 검사가 조건 밖에 있다")

    def test_allowlist_still_present(self) -> None:
        """건너뛰기를 넣으면서 검사를 **지우지 않았다.** 지우면 비통제 수집이 열린다."""
        self.assertIn("assert_dataset_id(", self.body)

    def test_input_is_still_verified(self) -> None:
        """건너뛴 것은 allowlist 뿐 — 입력 존재·상태는 그대로 본다."""
        self.assertIn("input not found", self.body)
        self.assertIn("storage_state", self.body)

    def test_upload_gate_untouched(self) -> None:
        """바이트를 받는 문은 안 건드렸다 — 계약 MIME 대조가 살아 있어야 한다 (B1)."""
        code = code_only(MAIN)
        i = code.index('@app.post("/v1/inputs")')
        rest = code[i + 20:]
        j = rest.find("\n@app.")
        upload = code[i:i + 20 + (j if j != -1 else len(rest))]
        self.assertNotIn("assert_dataset_id", upload)
        self.assertIn("capability", upload)


class TestPolicyIsDocumented(unittest.TestCase):
    def test_reason_is_written_down(self) -> None:
        """**왜** 건너뛰는지가 코드 옆에 있어야 한다.

        「allowlist 를 껐다」로만 남으면 다음 사람이 D8′ 를 약화한 것으로 읽는다.
        """
        src = MAIN.read_text(encoding="utf-8")
        self.assertIn("비통제 수집", src)
        self.assertIn("거짓말을 시킨다", src)

    def test_catalog_records_the_change(self) -> None:
        cat = (ROOT / "docs" / "spec" / "capability-catalog.md").read_text(encoding="utf-8")
        self.assertIn("Decision A", cat)


if __name__ == "__main__":
    unittest.main()
