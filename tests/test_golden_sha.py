"""골든셋 sha 정합 테스트 (SD-013 회귀 방지).

리포에 **실제로 커밋된** 파일을 본다 (골든 픽스처). 픽스처를 따로 두지 않는 이유는,
막으려는 사고가 정확히 「커밋된 선언부가 서로 어긋나는 것」이기 때문이다.

2026-08-10 사고: 매니페스트만 홀드아웃으로 교체되고 선언부 4곳이 따라오지 않아
capability 가 리포에 없는 골든셋을 가리켰다. 사슬이 self-consistent 라 데모는 통과했다.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_golden_sha as g  # noqa: E402


class TestCanonicalSha(unittest.TestCase):
    def test_matches_extract_golden_method(self):
        """extract_golden.py:175-177 과 같은 정본화여야 한다.

        정본화가 바뀌면 sha 가 통째로 달라진다 — 여기서 잡는다.
        """
        import hashlib
        data = json.loads(g.MANIFEST.read_text(encoding="utf-8"))
        text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        self.assertEqual(
            g.canonical_sha256(g.MANIFEST),
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )

    def test_manifest_file_is_already_canonical(self):
        """커밋된 파일 자체가 정본형이어야 한다. 아니면 재계산값과 파일이 다르다."""
        data = json.loads(g.MANIFEST.read_text(encoding="utf-8"))
        text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        self.assertEqual(
            text.encode("utf-8"),
            g.MANIFEST.read_bytes(),
            "매니페스트가 정본형이 아니다 — extract_golden.py 로 다시 뽑아야 한다",
        )


class TestDeclarationsAgree(unittest.TestCase):
    """선언부 4곳이 모두 매니페스트 재계산값과 같아야 한다."""

    @classmethod
    def setUpClass(cls):
        cls.truth = g.canonical_sha256(g.MANIFEST)

    def test_spec_md(self):
        self.assertEqual(g.declared_in_spec_md(g.SPEC_MD), self.truth)

    def test_machine_pin(self):
        self.assertEqual(g.declared_in_machine_pin(g.MACHINE_PIN), self.truth)

    def test_seed_sql(self):
        self.assertEqual(g.declared_in_seed(g.SEED_SQL), self.truth)

    def test_report_draft_prefix(self):
        declared = g.declared_in_report(g.REPORT_DRAFT)
        self.assertIsNotNone(declared, "보고서 초안에서 sha 인용을 찾지 못했다")
        self.assertTrue(
            self.truth.startswith(declared),
            f"보고서 인용 {declared}… 이 정본 {self.truth[:12]}… 과 다르다",
        )


class TestParsersFailLoudly(unittest.TestCase):
    """파서가 못 찾으면 None 이어야 한다.

    문서 형식이 바뀌었는데 조용히 통과하면 검사기가 껍데기가 된다.
    """

    def _tmp(self, name: str, body: str) -> Path:
        import tempfile
        p = Path(tempfile.mkdtemp()) / name
        p.write_text(body, encoding="utf-8")
        return p

    def test_spec_md_without_declaration(self):
        self.assertIsNone(g.declared_in_spec_md(self._tmp("a.md", "# 아무것도 없다\n")))

    def test_machine_pin_without_golden_demo(self):
        self.assertIsNone(g.declared_in_machine_pin(self._tmp("a.json", '{"x": 1}')))

    def test_seed_without_manifest_ref(self):
        self.assertIsNone(g.declared_in_seed(self._tmp("a.sql", "INSERT INTO x VALUES (1);")))

    def test_report_without_row(self):
        self.assertIsNone(g.declared_in_report(self._tmp("a.md", "| 항목 | 값 |\n")))


class TestCaseFiles(unittest.TestCase):
    """매니페스트가 적은 케이스 sha 와 실제 파일이 같아야 한다."""

    def test_all_cases_match(self):
        problems = g.check_cases(g.MANIFEST, g.CASES_DIR)
        self.assertEqual(problems, [], "케이스 파일이 매니페스트와 어긋난다")

    def test_case_count_matches_declared_n(self):
        data = json.loads(g.MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(len(data["cases"]), data["selection"]["n"])

    def test_split_is_holdout(self):
        """데모 골든셋은 홀드아웃이어야 한다 (SD-008 해소 상태 유지)."""
        data = json.loads(g.MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["selection"]["split"], "holdout")

    def test_selection_is_not_model_based(self):
        """모델 기반 선택이면 게이트가 게이밍된다."""
        data = json.loads(g.MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(data["selection"]["model_based"])


class TestEndToEnd(unittest.TestCase):
    def test_checker_passes_on_repo(self):
        """검사기 본체가 리포 상태에서 통과해야 한다."""
        import contextlib
        import io
        buf = io.StringIO()
        argv = sys.argv
        sys.argv = ["check_golden_sha.py"]
        try:
            with contextlib.redirect_stdout(buf):
                rc = g.main()
        finally:
            sys.argv = argv
        self.assertEqual(rc, 0, f"검사기가 실패했다:\n{buf.getvalue()}")


if __name__ == "__main__":
    unittest.main()
