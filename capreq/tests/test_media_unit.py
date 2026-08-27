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


if __name__ == "__main__":
    unittest.main()
