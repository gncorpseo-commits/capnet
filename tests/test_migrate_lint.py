"""마이그레이션 정적 검사 테스트 (SD-007).

DB 없이 돈다. 표준 라이브러리 unittest 만 쓴다 — 이 리포에는 pytest 가 없다.

여기서 지키는 것은 **절대규칙이 도구로 강제되는가**이다.
검사기가 조용히 약해지면 마이그레이션 경로로 제약이 빠져나갈 수 있다.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "core"))

from app.migrate_lint import (  # noqa: E402
    ALLOW_MARKER,
    MigrationError,
    lint,
    load_migrations,
    strip_sql_comments,
)


class TestForbiddenPatterns(unittest.TestCase):
    """절대규칙 1 — 제약을 약화하는 SQL 은 적용 전에 막힌다."""

    def assert_blocked(self, sql: str, expect: str) -> None:
        problems = lint(sql)
        self.assertTrue(problems, f"막았어야 한다: {sql!r}")
        self.assertTrue(
            any(expect in p for p in problems),
            f"{expect!r} 가 사유에 없다: {problems}",
        )

    def test_drop_constraint(self):
        self.assert_blocked("ALTER TABLE node DROP CONSTRAINT ck_gate_runner_team;", "제약 삭제")

    def test_drop_table(self):
        self.assert_blocked("DROP TABLE assignment;", "테이블 삭제")

    def test_drop_column(self):
        self.assert_blocked("ALTER TABLE agent DROP COLUMN weights_sha256;", "컬럼 삭제")

    def test_not_valid(self):
        self.assert_blocked(
            "ALTER TABLE task ADD CONSTRAINT c CHECK (x > 0) NOT VALID;", "NOT VALID"
        )

    def test_drop_not_null(self):
        self.assert_blocked("ALTER TABLE agent ALTER COLUMN name DROP NOT NULL;", "NOT NULL 해제")

    def test_disable_trigger(self):
        self.assert_blocked("ALTER TABLE gate_run DISABLE TRIGGER ALL;", "절대규칙 1")

    def test_deferred_constraints(self):
        self.assert_blocked("SET CONSTRAINTS ALL DEFERRED;", "제약 지연")

    def test_case_insensitive(self):
        """소문자로 써도 막힌다."""
        self.assert_blocked("alter table node drop constraint ck_x;", "제약 삭제")

    def test_split_across_lines(self):
        """줄바꿈으로 쪼개도 막힌다 — 공백 정규화가 하는 일."""
        self.assert_blocked("ALTER TABLE node\n  DROP\n  CONSTRAINT ck_x;", "제약 삭제")


class TestSnapshotTables(unittest.TestCase):
    """절대규칙 2 — assignment · gate_run 은 INSERT … SELECT 만."""

    def test_assignment_values_blocked(self):
        problems = lint("INSERT INTO assignment (id, task_id) VALUES ('a', 'b');")
        self.assertTrue(any("assignment" in p and "절대규칙 2" in p for p in problems))

    def test_gate_run_values_blocked(self):
        problems = lint("INSERT INTO gate_run (id, status) VALUES ('a', 'PASSED');")
        self.assertTrue(any("gate_run" in p and "절대규칙 2" in p for p in problems))

    def test_insert_select_allowed(self):
        """정상 경로는 통과해야 한다 — 오탐이면 러너를 아무도 안 쓴다."""
        sql = (
            "INSERT INTO gate_run (id, agent_id, status, golden_set_sha256)\n"
            "SELECT gen_random_uuid(), a.id, 'RUNNING', c.golden_set_sha256\n"
            "  FROM agent a JOIN capability c ON true;"
        )
        self.assertEqual(lint(sql), [])

    def test_other_table_values_allowed(self):
        """스냅샷 테이블이 아니면 VALUES 를 막지 않는다."""
        self.assertEqual(lint("INSERT INTO app_user (id, name) VALUES ('x','y');"), [])


class TestTransactionControl(unittest.TestCase):
    """파일이 스스로 트랜잭션을 열면 러너의 원자성이 깨진다."""

    def test_begin_blocked(self):
        self.assertTrue(any("BEGIN" in p for p in lint("BEGIN;\nSELECT 1;")))

    def test_commit_blocked(self):
        self.assertTrue(any("COMMIT" in p for p in lint("SELECT 1;\nCOMMIT;")))

    def test_rollback_blocked(self):
        self.assertTrue(any("ROLLBACK" in p for p in lint("ROLLBACK;")))

    def test_begin_inside_do_block_allowed(self):
        """PL/pgSQL 의 BEGIN 은 트랜잭션 제어가 아니다 — 줄 맨 앞 `BEGIN;` 만 잡는다."""
        sql = "DO $$\nBEGIN\n    RAISE NOTICE 'hi';\nEND $$;"
        self.assertEqual(lint(sql), [])


class TestAllowMarker(unittest.TestCase):
    """면허가 아니라 리뷰에서 눈에 띄라고 있는 표식."""

    def test_marker_permits_constraint_change(self):
        sql = f"{ALLOW_MARKER}\n-- 근거: …\nALTER TABLE node DROP CONSTRAINT ck_x;"
        self.assertEqual(lint(sql), [])

    def test_marker_does_not_permit_snapshot_insert(self):
        """표식은 절대규칙 1 에만 쓰인다. 절대규칙 2 는 여전히 막힌다."""
        sql = f"{ALLOW_MARKER}\nINSERT INTO assignment (id) VALUES ('a');"
        self.assertTrue(any("절대규칙 2" in p for p in lint(sql)))

    def test_marker_does_not_permit_own_transaction(self):
        sql = f"{ALLOW_MARKER}\nBEGIN;\nSELECT 1;"
        self.assertTrue(any("BEGIN" in p for p in lint(sql)))


class TestCommentHandling(unittest.TestCase):
    """주석 안의 금지어로 오탐하면 안 된다 — 마이그레이션은 주석에 경위를 적는다."""

    def test_line_comment_not_flagged(self):
        self.assertEqual(lint("-- 예전에는 DROP CONSTRAINT 를 했다\nSELECT 1;"), [])

    def test_block_comment_not_flagged(self):
        self.assertEqual(lint("/* DROP TABLE assignment; */\nSELECT 1;"), [])

    def test_strip_keeps_line_structure(self):
        """줄 단위 검사(TXN)를 위해 줄 수가 유지돼야 한다."""
        stripped = strip_sql_comments("-- a\n-- b\nBEGIN;")
        self.assertEqual(len(stripped.splitlines()), 3)

    def test_real_sql_after_comment_still_flagged(self):
        self.assertTrue(lint("-- 설명\nALTER TABLE node DROP CONSTRAINT ck_x;"))


class TestLoadMigrations(unittest.TestCase):
    """계보 무결성 — 파일명·번호."""

    def _dir(self, names: dict[str, str]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        for name, body in names.items():
            (tmp / name).write_text(body, encoding="utf-8")
        return tmp

    def test_loads_in_order(self):
        d = self._dir({
            "0001_baseline.sql": "SELECT 1;",
            "0002_second.sql": "SELECT 2;",
            "0003_third.sql": "SELECT 3;",
        })
        got = load_migrations(d)
        self.assertEqual([m.version for m in got], [1, 2, 3])
        self.assertEqual([m.name for m in got], ["baseline", "second", "third"])

    def test_checksum_is_sha256_of_file(self):
        import hashlib
        body = "SELECT 1;\n"
        d = self._dir({"0001_baseline.sql": body})
        expected = hashlib.sha256(body.encode()).hexdigest()
        self.assertEqual(load_migrations(d)[0].checksum, expected)

    def test_bad_filename_rejected(self):
        d = self._dir({"0001_baseline.sql": "SELECT 1;", "2-Bad Name.sql": "SELECT 1;"})
        with self.assertRaises(MigrationError) as cm:
            load_migrations(d)
        self.assertIn("파일명 규칙", str(cm.exception))

    def test_version_gap_rejected(self):
        d = self._dir({"0001_baseline.sql": "SELECT 1;", "0003_third.sql": "SELECT 3;"})
        with self.assertRaises(MigrationError) as cm:
            load_migrations(d)
        self.assertIn("구멍", str(cm.exception))

    def test_missing_baseline_rejected(self):
        d = self._dir({"0002_second.sql": "SELECT 2;"})
        with self.assertRaises(MigrationError) as cm:
            load_migrations(d)
        self.assertIn("0001", str(cm.exception))

    def test_missing_directory_rejected(self):
        with self.assertRaises(MigrationError):
            load_migrations(Path("/nonexistent/capnet-migrations"))

    def test_empty_directory_is_ok(self):
        """빈 디렉터리는 오류가 아니다 — 아직 아무것도 없는 상태."""
        self.assertEqual(load_migrations(self._dir({})), [])


class TestRepoMigrations(unittest.TestCase):
    """리포에 실제로 커밋된 마이그레이션이 규칙을 지키는가 (골든 픽스처)."""

    def test_repo_migrations_load(self):
        got = load_migrations(ROOT / "migrations")
        self.assertGreaterEqual(len(got), 1)
        self.assertEqual(got[0].name, "baseline")

    def test_repo_migrations_lint_clean(self):
        for m in load_migrations(ROOT / "migrations"):
            with self.subTest(migration=m.path.name):
                self.assertEqual(lint(m.sql), [], f"{m.path.name} 이 정적 검사를 어긴다")


if __name__ == "__main__":
    unittest.main()
