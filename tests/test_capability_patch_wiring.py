"""`PATCH /v1/capabilities/{id}` 배선 — DB 없이 소스로 본다.

동작(설명이 실제로 바뀐다 · 계약이 안 바뀐다)은 `tests/integration/check_capability_patch.py`
가 살아 있는 DB 로 본다. 여기서 고정하는 것은 **열어 준 구멍이 하나로 유지되는가**다.

## 왜 이 검사가 있나

Decision (b) 는 「드리프트를 고치되 **계약은 못 고치게**」였다. 그 경계는 코드 세 줄로
지켜진다 — `UPDATE … SET description` 하나 · 모델의 `extra: forbid` · 라우트의 `admin`.
셋 중 하나가 느슨해지면 **계약 스냅샷의 원본이 움직인다**(`task_input` 복합 FK ·
`gate_run` · `assignment`). 그래서 세 줄을 여기서 못 박는다.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

CAPABILITY = ROOT / "apps" / "core" / "app" / "capability.py"
MAIN = ROOT / "apps" / "core" / "app" / "main.py"
SPEC = ROOT / "docs" / "spec" / "openapi.yaml"
SPEC_COPY = ROOT / "apps" / "core" / "openapi.yaml"
SCHEMA = ROOT / "docs" / "spec" / "schema.sql"


def registering_demos() -> list[Path]:
    """**능력을 등록하는** 스크립트를 목록에서 세지 않고 찾아낸다.

    Wave I 는 셋, Wave K 가 나머지 다섯을 고쳤다. 그때 목록을 손으로 적어 뒀다면
    아홉 번째 데모에서 또 갈라진다 — 이 저장소가 이번 달에 세 번 겪은 그 모양이다.
    「`POST /v1/capabilities` 를 하는 스크립트」가 정본이고 여기는 그걸 읽는다.

    `demo.sh` 는 여기 안 걸린다 — `image.classify` 는 **seed** 가 넣기 때문에 등록하지
    않는다. 예외를 적어 둔 게 아니라 **대상이 아닌 것**이다.
    """
    return sorted(
        p for p in (ROOT / "scripts").glob("*.sh")
        if 'v1/capabilities" -H' in p.read_text(encoding="utf-8")
    )

# PATCH 가 절대 건드리면 안 되는 칸.
CONTRACT_FIELDS = (
    "input_schema", "output_schema", "output_kind", "compute_tier", "trust_domain_min",
    "quality_profile", "golden_set_ref", "golden_set_sha256", "golden_set_size",
    "golden_metrics", "max_input_bytes", "max_attempts", "mvp_eligible", "code", "version",
)


class TestUpdateTouchesOnlyDescription(unittest.TestCase):
    def setUp(self) -> None:
        self.code = code_only(CAPABILITY)

    def test_function_exists(self) -> None:
        self.assertIn("def update_capability_description(", self.code)

    def test_the_update_sets_description_and_nothing_else(self) -> None:
        """`SET` 절에 칸이 하나뿐이어야 한다 — 늘어나면 계약이 열린다."""
        m = re.search(r"UPDATE capability\s+SET (.+?)\s+WHERE", self.code, re.S)
        self.assertIsNotNone(m, "UPDATE capability … SET … WHERE 를 못 찾았다")
        set_clause = m.group(1)
        self.assertNotIn(",", set_clause, f"SET 절에 칸이 둘 이상이다: {set_clause!r}")
        self.assertIn("description", set_clause)

    def test_no_contract_field_is_assigned(self) -> None:
        m = re.search(r"UPDATE capability\s+SET (.+?)\s+WHERE", self.code, re.S)
        for field in CONTRACT_FIELDS:
            self.assertNotIn(field, m.group(1), f"{field} 가 SET 절에 있다")

    def test_only_one_update_statement_in_the_module(self) -> None:
        """등록 모듈에 UPDATE 가 늘어나면 이 검사부터 다시 본다."""
        self.assertEqual(self.code.count("UPDATE capability"), 1)


class TestRouteWiring(unittest.TestCase):
    def setUp(self) -> None:
        self.code = code_only(MAIN)

    def test_patch_route_exists(self) -> None:
        self.assertIn('@app.patch("/v1/capabilities/{capability_id}")', self.code)

    def test_route_requires_admin(self) -> None:
        """등록(`POST`)과 같은 문턱이다 — 라우팅용 메타라도 아무나 못 바꾼다."""
        i = self.code.index('@app.patch("/v1/capabilities/{capability_id}")')
        body = self.code[i : i + 1200]
        self.assertIn('_require("admin"', body)

    def test_route_returns_404_for_missing_id(self) -> None:
        i = self.code.index('@app.patch("/v1/capabilities/{capability_id}")')
        self.assertIn("404", self.code[i : i + 1200])

    def test_model_forbids_extra_fields(self) -> None:
        """화이트리스트를 손으로 세지 않는다 — 계약 칸이 늘어도 빠뜨리지 않게."""
        i = self.code.index("class CapabilityDescriptionPatch(BaseModel):")
        body = self.code[i : i + 500]
        self.assertIn('"extra": "forbid"', body)

    def test_model_declares_only_description(self) -> None:
        i = self.code.index("class CapabilityDescriptionPatch(BaseModel):")
        body = self.code[i : self.code.index("model_config", i)]
        fields = re.findall(r"^\s{4}(\w+)\s*:", body, re.M)
        self.assertEqual(fields, ["description"], f"모델 필드가 늘었다: {fields}")


class TestNoSchemaChange(unittest.TestCase):
    def test_no_migration_was_added_for_this(self) -> None:
        """Decision (b) 는 **DDL 0** 이다."""
        self.assertNotIn("ALTER TABLE capability", SCHEMA.read_text(encoding="utf-8"))


class TestDocumented(unittest.TestCase):
    def test_openapi_both_copies_document_patch(self) -> None:
        for path in (SPEC, SPEC_COPY):
            text = path.read_text(encoding="utf-8")
            i = text.index("  /v1/capabilities/{capability_id}:")
            block = text[i : text.index("  /v1/agents:", i)]
            self.assertIn("patch:", block, f"{path.name} 에 patch 가 없다")
            self.assertIn("additionalProperties: false", block)


class TestDemosSyncDescription(unittest.TestCase):
    """데모가 **저장소 문구를 DB 에 맞춘다.** 문구를 데모에서 새로 짓지 않는다."""

    def setUp(self) -> None:
        self.demos = registering_demos()

    def test_the_probe_finds_the_demos(self) -> None:
        """검사가 0개를 돌며 통과하는 상태를 막는다."""
        self.assertGreaterEqual(len(self.demos), 8, [p.name for p in self.demos])

    def test_seeded_capability_demo_is_not_in_scope(self) -> None:
        """`demo.sh` 는 등록하지 않는다 — `image.classify` 는 seed 가 넣는다."""
        self.assertNotIn("demo.sh", [p.name for p in self.demos])

    def test_every_registering_demo_patches_when_it_already_exists(self) -> None:
        for path in self.demos:
            text = path.read_text(encoding="utf-8")
            self.assertIn("cap_body=", text, f"{path.name}: 정본 변수가 없다")
            self.assertIn("-X PATCH", text, f"{path.name}: PATCH 단계가 없다")
            self.assertIn("이미 있음", text, f"{path.name}: 기존 id 분기가 사라졌다")

    def test_description_comes_from_the_post_body(self) -> None:
        """PATCH 로 보내는 값의 출처가 `cap_body` 여야 한다 — 두 벌을 만들지 않는다."""
        for path in self.demos:
            text = path.read_text(encoding="utf-8")
            self.assertIn('"$cap_body"', text, f"{path.name}")
            self.assertRegex(text, r'want=\$\(printf .%s. "\$cap_body"', f"{path.name}")

    def test_demo_still_posts_first(self) -> None:
        """PATCH 는 **폴백**이다 — 새 스택에서는 POST 한 번으로 끝나야 한다."""
        for path in self.demos:
            text = path.read_text(encoding="utf-8")
            self.assertLess(text.index("-X POST"), text.index("-X PATCH"), f"{path.name}")

    def test_patch_body_carries_only_description(self) -> None:
        """계약 칸이 PATCH 본문에 섞이면 Core 가 400 이지만, 데모가 그걸 시도조차 않게 한다."""
        for path in self.demos:
            text = path.read_text(encoding="utf-8")
            i = text.index("-X PATCH")
            body = text[i : i + 400]
            self.assertIn('{"description"', body, f"{path.name}")
            for field in ("input_schema", "output_schema", "compute_tier", "quality_profile"):
                self.assertNotIn(field, body, f"{path.name}: PATCH 본문에 {field}")


if __name__ == "__main__":
    unittest.main()
