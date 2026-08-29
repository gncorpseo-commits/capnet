"""MIME allowlist — Ollama 없이."""

from __future__ import annotations

import unittest

from capreq.media import check_media_for_capability, modality_of_capability


class TestMedia(unittest.TestCase):
    def test_image_classify_jpeg(self) -> None:
        self.assertIsNone(
            check_media_for_capability("image.classify", "image/jpeg")
        )

    def test_image_reject_text(self) -> None:
        err = check_media_for_capability("image.classify", "text/plain")
        assert err is not None
        self.assertIn("image.classify", err)

    def test_modality(self) -> None:
        self.assertEqual(modality_of_capability("text.embed"), "text")

    def test_image_classify_rejects_png(self) -> None:
        # 계약이 JPEG 만 선언했다 (0012). 모달리티 기본값으로 통과시키면
        # Core 가 400 을 주는 것을 여기서 못 걸러 낸다.
        err = check_media_for_capability("image.classify", "image/png")
        assert err is not None
        self.assertIn("image/jpeg", err)

    def test_timeseries_forecast_csv(self) -> None:
        # `timeseries` 접두는 모달리티 표에 없었다 — 업로드가 통째로 막혀 있었다.
        self.assertIsNone(
            check_media_for_capability("timeseries.forecast", "text/csv")
        )

    def test_table_extract_plain_text(self) -> None:
        self.assertIsNone(check_media_for_capability("table.extract", "text/plain"))

    def test_unknown_capability_has_no_rule(self) -> None:
        err = check_media_for_capability("sound.dance", "audio/wav")
        assert err is not None
        self.assertIn("규칙이 없다", err)


if __name__ == "__main__":
    unittest.main()
