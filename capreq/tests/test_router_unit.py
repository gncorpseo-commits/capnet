"""라우터 파싱·allowlist — Ollama 없이."""

from __future__ import annotations

import unittest

# 의존성이 없으면 **오류가 아니라 건너뜀**이다 (큐 #60 · `testing.md` §4.6).
# 예전에는 import 가 그대로 터져 로컬 실행이 `FAILED (errors=3)` 였고, 그게
# 「코드가 깨졌다」처럼 보였다. CI 의 capreq 잡은 핀을 깔므로 그대로 돈다.
try:
    from capreq.adapters.base import CapabilityInfo
    from capreq.adapters.static import StaticCatalog
    from capreq.router import CapabilityRouter, _parse_decision
except ModuleNotFoundError:  # noqa: F401
    raise unittest.SkipTest("httpx 없음 — capreq 런타임 핀이 깔린 환경에서만 돈다")


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

    def test_version_fallback_is_said_out_loud(self) -> None:
        """없는 버전은 같은 code 의 등록 버전으로 가되, reason 이 그 사실을 말한다 (큐 #92)."""
        llm = FakeLLM(
            '{"capability_code":"image.classify","capability_version":7,'
            '"confidence":0.9,"reason":"classify"}'
        )
        r = CapabilityRouter(catalog=self.catalog, llm=llm)  # type: ignore[arg-type]
        d = r.route("사진 분류해줘")
        self.assertTrue(d.ok)
        self.assertEqual(d.capability_version, 1)
        self.assertIn("@7", d.reason)
        self.assertIn("@1", d.reason)

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
