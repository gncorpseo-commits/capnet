"""계약 출력 검증 — `structured` 까지 본다 (D-out).

## 왜 있는가

전에는 스칼라만 봤다. 그래서 `structured` 출력에서 **차원이 틀린 벡터 · 배열이 아닌 값 ·
구조가 없는 박스 목록이 전부 통과**했다(2026-08-15 실측). 카탈로그 52 중 **26개**가
`structured` 라, 그쪽 실행기를 얹기 전에 닫아야 했다.

여기서 고정하는 것은 둘이다.

1. **넓힌 것이 실제로 무는가** — 그 네 가지가 이제 떨어지는가
2. **`closed_set_labels` 판정이 그대로인가** — `image.classify`·`text.classify` 무회귀.
   촬영 경로가 이 위에 있다

## 한계

torch 없이 돈다 (`check_output_schema` 는 순수 함수다). 계약 게이트 전체는
`scripts/contract_bind.sh` 와 수용 게이트가 본다.
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402


def _purge() -> None:
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = list(sys.path)
        _purge()
        sys.path.insert(0, str(ROOT / "apps" / "node"))
        self.check = importlib.import_module("app.contract_check").check_output_schema

    def tearDown(self) -> None:
        sys.path[:] = self._saved
        _purge()

    def assertRejected(self, out, schema, contains: str = "") -> None:
        ok, why = self.check(out, schema)
        self.assertFalse(ok, f"통과했다: {out!r}")
        if contains:
            self.assertIn(contains, why)

    def assertAccepted(self, out, schema) -> None:
        ok, why = self.check(out, schema)
        self.assertTrue(ok, f"거절됐다: {why}")


VECTOR = {
    "required": ["vector"],
    "properties": {"vector": {
        "type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
    }},
}
BOXES = {
    "required": ["boxes"],
    "properties": {"boxes": {
        "type": "array",
        "items": {"type": "object", "required": ["x", "y", "w", "h"]},
    }},
}
# 실제 `image.classify@1` 계약의 모양. 이 판정이 바뀌면 촬영이 깨진다.
CLASSIFY = {
    "required": ["label"],
    "properties": {
        "label": {"type": "string", "enum": ["annual_crop", "forest"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "additionalProperties": False,
}


class TestStructuredNowChecked(Base):
    """실측으로 통과하던 넷이 이제 떨어진다."""

    def test_wrong_dimension_rejected(self) -> None:
        self.assertRejected({"vector": [0.1]}, VECTOR, "minItems")

    def test_too_many_items_rejected(self) -> None:
        self.assertRejected({"vector": [0.1, 0.2, 0.3, 0.4]}, VECTOR, "maxItems")

    def test_not_an_array_rejected(self) -> None:
        self.assertRejected({"vector": "not-a-vector"}, VECTOR, "array")

    def test_wrong_item_type_rejected(self) -> None:
        self.assertRejected({"vector": [0.1, "x", 0.3]}, VECTOR, "vector[1]")

    def test_malformed_object_items_rejected(self) -> None:
        self.assertRejected({"boxes": [{"x": "a"}]}, BOXES, "boxes[0]")

    def test_valid_structured_accepted(self) -> None:
        self.assertAccepted({"vector": [0.1, 0.2, 0.3]}, VECTOR)
        self.assertAccepted({"boxes": [{"x": 1, "y": 2, "w": 3, "h": 4}]}, BOXES)

    def test_error_says_where(self) -> None:
        """중첩은 「어디가」 없으면 제출자가 못 고친다."""
        ok, why = self.check({"boxes": [{"x": 1, "y": 2, "w": 3}]}, BOXES)
        self.assertFalse(ok)
        self.assertIn("boxes[0].h", why)


class TestClosedSetUnchanged(Base):
    """**무회귀** — 촬영 경로가 이 판정 위에 있다."""

    def test_valid_accepted(self) -> None:
        self.assertAccepted({"label": "forest", "confidence": 0.9}, CLASSIFY)

    def test_enum_violation_rejected(self) -> None:
        self.assertRejected({"label": "zzz"}, CLASSIFY, "enum")

    def test_range_violation_rejected(self) -> None:
        self.assertRejected({"label": "forest", "confidence": 1.5}, CLASSIFY, "maximum")

    def test_additional_field_rejected(self) -> None:
        self.assertRejected({"label": "forest", "x": 1}, CLASSIFY, "허용되지 않은 필드")

    def test_missing_required_rejected(self) -> None:
        self.assertRejected({}, CLASSIFY, "required 누락")

    def test_label_type_rejected(self) -> None:
        self.assertRejected({"label": 3}, CLASSIFY, "string")


class TestBooleanIsNotNumber(Base):
    """`bool` 은 파이썬에서 `int` 의 하위형이다 — 먼저 거르지 않으면 `True` 가 number 로 통과한다."""

    SCHEMA = {"properties": {"n": {"type": "number", "minimum": 0, "maximum": 1}}}

    def test_bool_rejected_as_number(self) -> None:
        self.assertRejected({"n": True}, self.SCHEMA, "number")

    def test_int_accepted_as_number(self) -> None:
        self.assertAccepted({"n": 1}, self.SCHEMA)


class TestUnknownVocabularyIsNotFaked(Base):
    """모르는 어휘를 **아는 척하지 않는다.**

    `pattern`·`format`·`oneOf` 는 지금 어느 계약도 쓰지 않는다. 반쯤 구현해 두면
    「검사했다」로 읽히므로, 통과시키되 **문서에 적어 둔다.**
    """

    def test_pattern_is_ignored_not_enforced(self) -> None:
        self.assertAccepted({"s": "zzz"}, {"properties": {"s": {"type": "string", "pattern": "^a"}}})

    def test_limits_are_documented(self) -> None:
        doc = (ROOT / "apps" / "node" / "app" / "contract_check.py").read_text(encoding="utf-8")
        self.assertIn("모르는 채로 통과시킨다", doc)


class TestNoNewDependency(Base):
    def test_jsonschema_not_imported(self) -> None:
        """새 의존성 0 — `jsonschema` 를 넣지 않는다 (THIRD-PARTY 한 줄이 따라붙는다)."""
        code = code_only(ROOT / "apps" / "node" / "app" / "contract_check.py")
        self.assertNotIn("jsonschema", code)


if __name__ == "__main__":
    unittest.main()
