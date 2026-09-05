r"""**설정을 주석으로 옮겨도 통과하는 검사**를 막는다 (G1 · `_srcguard` 확장).

## 왜 있는가

`tests/_srcguard.py` 는 이 저장소가 **네 번** 겪은 사고에서 나왔다 — 「X 를 쓰지 않는다」를
텍스트로 검사할 때 **그렇게 적어 둔 설명이 검사에 걸린** 자리들이다. 그 헬퍼는
**파이썬**의 `#` 주석과 docstring 을 걷는다.

**거울상이 남아 있었다.** 「설정이 **있다**」를 텍스트로 확인할 때, 그 설정을 **주석으로
옮기면** 검사가 그대로 통과한다. 파이썬이 아니라 **YAML** 이라 `code_only` 가 못 닿았다.

## 실측 (2026-09-05) — 이번 회차에 내가 쓴 검사 둘이 걸렸다

| 심은 것 | 그 전 | 결과 |
|---|---|---|
| `# restart: "no"` 로 주석 처리 | `test_migrate_does_not_restart` **통과** | migrate 가 실패한 세대를 **무한 재시작** |
| `# NODE_CREDENTIAL_FILE: …` 하나 주석 | `…file_path_to_every_node` **통과** | 그 Node 가 강제 모드에서 **증서 없이** 돈다 |

둘 다 `#252`·`#251` 에서 **내가** 쓴 검사다. 뮤테이션을 「값을 바꾼다」로만 심었고
**「주석으로 옮긴다」는 안 심었다.**

## 무엇을 더했나

`_srcguard.hash_comment_free(path)` — YAML·셸의 `#` 주석을 비운다. 줄 번호는 유지하고,
**따옴표 안의 `#` 는 안 지운다** (`a: "x#y"` 는 값이다).

## 규칙 — 언제 걷고 언제 안 걷나

| 무엇을 보나 | 어떻게 |
|---|---|
| 설정이 **있다** (`restart: "no"` · `NODE_CREDENTIAL_FILE:`) | **걷고** 본다 |
| **이유**가 적혀 있다 (initdb 함정 주석 · 시크릿 위생) | **원문**을 본다 — 주석이 본체다 |

**설명을 지워야 통과하는 검사를 만들지 않는다** (`_srcguard` 머리말). 반대로,
**주석만 있어도 통과하는 검사도 만들지 않는다.**
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import code_only, hash_comment_free  # noqa: E402

# 설정의 **존재**를 보는 검사 — 주석을 걷고 봐야 한다.
MUST_STRIP = {
    "test_migrate_stops_on_failure.py": "compose 의 restart·depends_on 조건",
    "test_node_secrets_live_in_files.py": "compose 의 증서 파일 경로",
}


class TestTheHelperStripsWhatItShould(unittest.TestCase):
    def test_a_commented_setting_disappears(self) -> None:
        probe = ROOT / "tests" / "__hash_probe.yaml"
        probe.write_text('a: 1\n# b: 2\n  # c: 3\nd: 4\n', encoding="utf-8")
        try:
            got = hash_comment_free(probe)
            self.assertIn("a: 1", got)
            self.assertIn("d: 4", got)
            self.assertNotIn("b: 2", got)
            self.assertNotIn("c: 3", got)
        finally:
            probe.unlink()

    def test_a_hash_inside_quotes_survives(self) -> None:
        """`a: "x#y"` 는 값이다 — 지우면 멀쩡한 설정이 사라진다."""
        probe = ROOT / "tests" / "__hash_probe2.yaml"
        probe.write_text('a: "x#y"   # 진짜 주석\nb: \'p#q\'\n', encoding="utf-8")
        try:
            got = hash_comment_free(probe)
            self.assertIn('a: "x#y"', got)
            self.assertIn("b: 'p#q'", got)
            self.assertNotIn("진짜 주석", got)
        finally:
            probe.unlink()

    def test_line_numbers_are_kept(self) -> None:
        """줄이 밀리면 오류 메시지가 엉뚱한 곳을 가리킨다."""
        probe = ROOT / "tests" / "__hash_probe3.yaml"
        probe.write_text("a: 1\n# only a comment\nb: 2\n", encoding="utf-8")
        try:
            lines = hash_comment_free(probe).splitlines()
            self.assertEqual(3, len(lines))
            self.assertEqual("", lines[1])
        finally:
            probe.unlink()


class TestTheRealFilesStillReadCorrectly(unittest.TestCase):
    def test_compose_settings_survive_the_strip(self) -> None:
        got = hash_comment_free(ROOT / "compose.yaml")
        for setting in ('restart: "no"', "condition: service_completed_successfully",
                        "pg_isready", "ports:"):
            with self.subTest(setting=setting):
                self.assertIn(setting, got, f"주석을 걷었더니 설정이 사라졌다: {setting}")

    def test_prod_overlay_settings_survive(self) -> None:
        got = hash_comment_free(ROOT / "compose.prod.yaml")
        self.assertEqual(3, got.count("NODE_CREDENTIAL_FILE:"))
        self.assertIn("ports: !override []", got)

    def test_comments_are_actually_gone(self) -> None:
        raw = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        before = sum(1 for l in raw.splitlines() if l.strip().startswith("#"))
        after = sum(1 for l in hash_comment_free(ROOT / "compose.yaml").splitlines()
                    if l.strip().startswith("#"))
        self.assertGreater(before, 5, "기준 파일에 주석이 거의 없다 — 검사가 공허하다")
        self.assertEqual(0, after)


class TestTheChecksThatMustStripDoStrip(unittest.TestCase):
    """이 둘은 **설정의 존재**를 본다 — 걷지 않으면 주석으로 옮겨도 통과한다."""

    def test_they_import_the_helper(self) -> None:
        must = MUST_STRIP.items()
        self.assertTrue(must, "걷어야 하는 검사 목록이 비었다")
        for name, what in must:
            with self.subTest(check=name, sees=what):
                body = code_only(ROOT / "tests" / name)
                self.assertIn("hash_comment_free", body,
                              f"{name} 이 주석을 안 걷는다 — {what} 을 주석으로 옮겨도 통과한다")

    def test_the_helper_is_exported(self) -> None:
        self.assertTrue(callable(hash_comment_free))
        self.assertTrue(callable(code_only), "파이썬 쪽 헬퍼가 사라졌다")


if __name__ == "__main__":
    unittest.main()
