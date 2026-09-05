r"""GC 가 **지우지 않은 바이트를 「지웠다」고 세지 않는가** (배치 B #90 · `#187` 계열).

## 왜 있는가

`#187` 은 관리자 `POST /v1/inputs/{id}/purge` 가 안 지웠으면서 `purged_now: True` 라 하던 것을
고쳤다. 같은 일을 하는 자리가 하나 더 있다 — 배경 GC `_gc_once`. 실측(2026-09-06):

```python
purge_blob(input_id)              # 결과를 버린다 (True=지금 지움 · False=이미 없음)
if mark_purged(conn, input_id):
    freed += int(item["byte_size"] or 0)      # 파일이 이미 없었어도 더한다
```

`freed_bytes` 는 「이번 GC 가 회수한 바이트」로 로그에 찍힌다. 파일이 먼저 사라진 입력
(관리자 purge 와 경쟁 · 디스크 정리) 도 그 크기를 더하니, 회수량이 **실제보다 크게** 보고됐다.
행 상태를 PURGED 로 맞추는 것은 옳다 — 거짓말은 **숫자**였다.

## 고친 뒤

`removed = purge_blob(...)` 를 잡고, `freed` 는 `removed` 일 때만 더하며, 로그에
`file_removed=` 를 같이 찍는다.

## 재현

```bash
python3 -m unittest tests.test_gc_does_not_count_bytes_it_did_not_free
```
"""

from __future__ import annotations

import ast
import os
import re
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"


def _gc_once_src() -> str:
    src = MAIN.read_text(encoding="utf-8")
    i = src.index("def _gc_once(")
    return src[i:src.index("\ndef ", i + 1)]


class TestFreedIsGuardedByTheRealRemoval(unittest.TestCase):
    def test_purge_blob_result_is_captured(self) -> None:
        body = _gc_once_src()
        self.assertRegex(body, r"removed\s*=\s*purge_blob\(input_id\)", "purge_blob 의 결과를 버린다")
        self.assertNotRegex(body, r"^\s*purge_blob\(input_id\)", "결과 없이 부르는 purge_blob 이 남아 있다")

    def test_freed_is_added_only_when_removed(self) -> None:
        """`freed += …` 는 `if removed:` 안에 있어야 한다 — AST 로 본다."""
        fn = next(n for n in ast.walk(ast.parse(MAIN.read_text(encoding="utf-8")))
                  if isinstance(n, ast.FunctionDef) and n.name == "_gc_once")
        guarded = False
        for node in ast.walk(fn):
            if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "removed":
                if any(isinstance(x, ast.AugAssign) and isinstance(x.target, ast.Name) and x.target.id == "freed"
                       for x in ast.walk(node)):
                    guarded = True
        self.assertTrue(guarded, "freed += 가 `if removed:` 밖에 있다")
        unguarded = [x.lineno for x in ast.walk(fn)
                     if isinstance(x, ast.AugAssign) and isinstance(x.target, ast.Name) and x.target.id == "freed"]
        self.assertEqual(1, len(unguarded), f"freed 를 더하는 자리가 하나가 아니다: {unguarded}")

    def test_log_line_says_whether_the_file_was_there(self) -> None:
        self.assertIn("file_removed=%s", _gc_once_src())


class TestPurgeBlobTellsTheTruth(unittest.TestCase):
    """정적 검사의 전제 — `purge_blob` 이 정말 True/False 를 가른다."""

    def test_missing_file_is_false_and_present_file_is_true(self) -> None:
        # `app.inputs` 는 psycopg 를 끌어온다 — 함수 소스만 잘라 실행한다.
        src = (ROOT / "apps" / "core" / "app" / "inputs.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "purge_blob")
        with tempfile.TemporaryDirectory() as td:
            ns: dict = {"blob_path": lambda iid: Path(td) / f"{iid}.bin", "uuid": uuid, "Path": Path}
            exec(ast.get_source_segment(src, fn) or "", ns)  # noqa: S102 — 저장소의 함수 그대로
            purge_blob = ns["purge_blob"]
            iid = uuid.uuid4()
            self.assertFalse(purge_blob(iid), "없는 파일을 지웠다고 한다")
            (Path(td) / f"{iid}.bin").write_bytes(b"x")
            self.assertTrue(purge_blob(iid))
            self.assertFalse(os.path.exists(Path(td) / f"{iid}.bin"))


class TestProbeActuallyReads(unittest.TestCase):
    def test_gc_once_is_found_and_small(self) -> None:
        body = _gc_once_src()
        self.assertIn("purge_due(", body)
        self.assertLess(len(body.splitlines()), 60)


if __name__ == "__main__":
    unittest.main()
