"""라우터 파싱·allowlist — Ollama 없이."""

from __future__ import annotations

import unittest

from capreq.adapters.base import CapabilityInfo
from capreq.adapters.static import StaticCatalog
from capreq.router import CapabilityRouter, _parse_decision


class FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content

    def chat(self, *, system: str, user: str) -> str:
        return self.content


class TestParse(unittest.TestCase):
    def test_plain_json(self) -> None:
        d = _parse_decision(
            '{"capability_code":"image.classify","capability_version":1,'
            '"confidence":0.9,"reason":"classify"}'
        )
        assert d is not None
        self.assertEqual(d["capability_code"], "image.classify")

    def test_fenced(self) -> None:
        d = _parse_decision(
            'here\n{"capability_code":null,"capability_version":null,'
            '"confidence":0.1,"reason":"no"}\n'
        )
        assert d is not None
        self.assertIsNone(d["capability_code"])


class TestAllowlist(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = StaticCatalog(
            [
                CapabilityInfo(
                    code="image.classify",
                    version=1,
                    name="IC",
                    description="image labels",
                )
            ]
        )

    def test_match(self) -> None:
        llm = FakeLLM(
            '{"capability_code":"image.classify","capability_version":1,'
            '"confidence":0.88,"reason":"user wants classification"}'
        )
        r = CapabilityRouter(catalog=self.catalog, llm=llm)  # type: ignore[arg-type]
        d = r.route("사진 분류해줘")
        self.assertTrue(d.ok)
        self.assertEqual(d.capability_code, "image.classify")

    def test_reject_unknown_code(self) -> None:
        llm = FakeLLM(
            '{"capability_code":"image.teleport","capability_version":1,'
            '"confidence":0.99,"reason":"hallucination"}'
        )
        r = CapabilityRouter(catalog=self.catalog, llm=llm)  # type: ignore[arg-type]
        d = r.route("순간이동")
        self.assertTrue(d.rejected)
        self.assertFalse(d.ok)


if __name__ == "__main__":
    unittest.main()
