"""입력 계약의 **거절 경로를 돌려서** 본다 (D8′ · 절대규칙 7).

## 왜 있는가

큐 #33 — 「고쳤다고 주석에 적혀 있는데 못박은 검사가 없는 자리」를 전수하다 걸렸다.

`apps/core/app/inputs.py` 는 **Core 중개 수집의 문지기**다. 이 파일의 주석 둘이
과거 버그를 적고 있다:

    inputs.py:75   처음에는 「선언이 없으면 검사하지 않는다」였다. 계약이 안 정한 것을
                   코드가 정하지 …
    inputs.py:111  처음에는 청크를 메모리에 모은 뒤 파일로 썼다. 상한이 256MiB 라
                   최악의 경우 그만큼 상주했다 …

**둘 다 돌려 보는 검사가 없었다** (2026-09-03 실측):

```text
grep -rl "assert_media_type\|allowed_media_types\|InputTooLarge" tests/  → 없음
```

`test_docs_can_claims` 가 `"if allowed is None:" in inputs` 를 보지만 그건 **텍스트**다.
소스를 그대로 두고 동작만 바꾸면 통과한다. 이 파일은 **의존성이 가볍다**(hashlib·os·
uuid·pathlib) — `psycopg` 는 타입 주석과 `except` 절에만 쓰인다. **돌릴 수 있는데
안 돌리고 있었다.**

## 무엇을 고정하나

1. **형식을 선언하지 않은 계약은 업로드를 받지 않는다** — 「안 정했으니 다 받는다」가 아니다
2. 목록 밖 MIME 은 거절하고, **허용 목록을 말해 준다**
3. `store_stream` 이 **받는 즉시 쓴다** — 소비 도중 파일이 자라는 것으로 본다
4. 상한을 넘기면 **그 자리에서 끊고**(스트림을 끝까지 안 읽는다) **바이트를 지운다**
5. 빈 입력·중간 예외에도 **바이트가 남지 않는다**

3번이 이 검사의 값이다. 「거절된다」만 보면 **다 받아 놓고 마지막에 거절하는 구현**도
통과한다 — 그게 바로 주석이 적은 옛 버그다.

## 스텁 위생 (#186 교훈)

`psycopg` 스텁을 `sys.modules` 에 **남기면** 진짜로 psycopg 가 필요한 다른 검사들이
그것을 집어 깨진다 (실제로 `run_tests` 의 skip 이 7 → 2 로 줄고 5건이 에러였다).
**넣은 것만 되돌린다.** 아래 `TestStubHygiene` 가 그것을 확인한다.
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import shutil
import sys
import tempfile
import types
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps" / "core" / "app" / "inputs.py"

_TMP = tempfile.mkdtemp(prefix="capnet-inputs-probe-")


def _load_inputs():
    """`inputs.py` 를 파일 경로로 불러온다 — 스텁은 **넣은 것만** 되돌린다."""
    added = "psycopg" not in sys.modules
    if added:
        stub = types.ModuleType("psycopg")
        errs = types.ModuleType("psycopg.errors")
        # `except` 절에서만 쓰인다 — 임포트 시점에 존재하기만 하면 된다.
        for name in ("CheckViolation", "ForeignKeyViolation", "UniqueViolation"):
            setattr(errs, name, type(name, (Exception,), {}))
        stub.errors = errs
        sys.modules["psycopg"] = stub
        sys.modules["psycopg.errors"] = errs
    prev = os.environ.get("CAPNET_INPUTS_DIR")
    os.environ["CAPNET_INPUTS_DIR"] = _TMP
    try:
        spec = importlib.util.spec_from_file_location("_capnet_inputs_probe", SOURCE)
        assert spec and spec.loader, SOURCE
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        if prev is None:
            os.environ.pop("CAPNET_INPUTS_DIR", None)
        else:
            os.environ["CAPNET_INPUTS_DIR"] = prev
        if added:
            sys.modules.pop("psycopg", None)
            sys.modules.pop("psycopg.errors", None)


inputs = _load_inputs()


def tearDownModule() -> None:
    shutil.rmtree(_TMP, ignore_errors=True)


async def _agen(chunks, *, watch=None, seen=None):
    for c in chunks:
        if watch is not None:
            seen.append(watch())
        yield c


def _run(coro):
    return asyncio.run(coro)


class TestMediaTypeContract(unittest.TestCase):
    """「과목이 받겠다고 한 것만」 — user-guide §5.1 이 적은 그 규칙."""

    def test_undeclared_contract_refuses_everything(self) -> None:
        """**여기가 옛 버그다.** 「선언이 없으면 검사하지 않는다」가 아니다."""
        for schema in (None, {}, {"type": "object"}, {"mediaTypes": []}):
            with self.subTest(schema=schema):
                with self.assertRaises(inputs.InputRejected):
                    inputs.assert_media_type("text/plain", schema)

    def test_declared_type_passes(self) -> None:
        inputs.assert_media_type("text/plain", {"mediaTypes": ["text/plain"]})

    def test_other_type_is_refused(self) -> None:
        with self.assertRaises(inputs.InputRejected):
            inputs.assert_media_type("image/png", {"mediaTypes": ["text/plain"]})

    def test_message_names_the_allowed_list(self) -> None:
        """무엇을 보내야 하는지 안 알려 주면 붙이는 쪽이 추측한다."""
        with self.assertRaises(inputs.InputRejected) as ctx:
            inputs.assert_media_type("image/png", {"mediaTypes": ["text/plain", "text/csv"]})
        self.assertIn("text/plain", str(ctx.exception))
        self.assertIn("text/csv", str(ctx.exception))


class TestStoreStreamWritesAsItGoes(unittest.TestCase):
    def setUp(self) -> None:
        self.iid = uuid.uuid4()
        self.path = inputs.blob_path(self.iid)

    def tearDown(self) -> None:
        inputs.purge_blob(self.iid)

    def test_hash_and_size_are_correct(self) -> None:
        import hashlib
        chunks = [b"abc", b"defg", b"h"]
        sha, total = _run(inputs.store_stream(_agen(chunks), input_id=self.iid, max_bytes=100))
        self.assertEqual(hashlib.sha256(b"".join(chunks)).hexdigest(), sha)
        self.assertEqual(8, total)
        self.assertEqual(b"".join(chunks), self.path.read_bytes())

    def test_file_grows_while_the_stream_is_still_being_read(self) -> None:
        """**이 검사가 옛 버그를 못박는다.**

        메모리에 다 모은 뒤 쓰는 구현이면 소비 도중 파일 크기가 **0 으로 머문다.**
        「거절된다」만 보는 검사로는 그 구현도 통과한다.

        ### 처음 판이 잰 것은 **파이썬 파일 버퍼**였다 (적어 둔다)

        8바이트 청크로 재니 `[0, 0, 0, 0, 0]` 이 나왔다. 구현은 **이미 흘려 쓰고 있었는데**
        `open(path, "wb")` 의 기본 버퍼(수 KB)가 `close()` 전까지 디스크에 안 내보낸 것이다.
        **검사가 구현이 아니라 버퍼를 재고 있었다** — 그대로 뒀으면 「고쳐야 할 결함」을
        하나 지어낼 뻔했다.

        실제 청크는 `inputs.CHUNK` = **1MiB** 다. 버퍼보다 큰 청크로 재야 이 검사가
        보려는 것(**받는 즉시 내보낸다**)을 본다.
        """
        seen: list[int] = []

        def size_now() -> int:
            try:
                return self.path.stat().st_size
            except FileNotFoundError:
                return -1

        # 파일 버퍼보다 확실히 큰 청크 — 아니면 버퍼를 재게 된다 (위 주석).
        size = max(inputs.CHUNK // 8, 1 << 16)
        chunks = [b"x" * size for _ in range(5)]
        _run(inputs.store_stream(
            _agen(chunks, watch=size_now, seen=seen), input_id=self.iid,
            max_bytes=size * len(chunks) + 1))
        self.assertEqual(5, len(seen), f"스트림을 다 안 읽었다: {seen}")
        self.assertGreater(
            max(seen), 0,
            f"소비 도중 파일이 자라지 않았다 — 메모리에 모으고 있다: {seen}",
        )
        self.assertEqual(sorted(seen), seen, f"크기가 단조 증가하지 않는다: {seen}")

    def test_over_limit_stops_early_and_leaves_nothing(self) -> None:
        """상한을 넘기면 **그 자리에서 끊는다** — 끝까지 읽고 나서가 아니다."""
        seen: list[int] = []
        chunks = [b"y" * 10 for _ in range(10)]

        with self.assertRaises(inputs.InputTooLarge):
            _run(inputs.store_stream(
                _agen(chunks, watch=lambda: 0, seen=seen), input_id=self.iid, max_bytes=25))
        self.assertLess(len(seen), len(chunks), f"상한을 넘고도 끝까지 읽었다: {len(seen)}")
        self.assertFalse(self.path.exists(), "거절했는데 바이트가 남았다")

    def test_empty_input_is_refused_and_leaves_nothing(self) -> None:
        with self.assertRaises(inputs.InputRejected):
            _run(inputs.store_stream(_agen([b"", b""]), input_id=self.iid, max_bytes=100))
        self.assertFalse(self.path.exists(), "빈 입력인데 바이트가 남았다")

    def test_mid_stream_error_leaves_nothing(self) -> None:
        """중간에 끊긴 업로드가 디스크에 반쯤 남으면 그건 유령 증적이다."""
        class Boom(Exception):
            pass

        async def broken():
            yield b"z" * 16
            raise Boom("연결 끊김")

        with self.assertRaises(Boom):
            _run(inputs.store_stream(broken(), input_id=self.iid, max_bytes=1000))
        self.assertFalse(self.path.exists(), "끊긴 업로드가 남았다")


class TestStubHygiene(unittest.TestCase):
    """#186 이 실제로 저지른 사고 — 내 스텁이 **다른 검사를 껐다.**"""

    def test_psycopg_stub_is_not_left_behind(self) -> None:
        mod = sys.modules.get("psycopg")
        if mod is None:
            return
        self.assertNotEqual(
            "_capnet_inputs_probe_stub", getattr(mod, "__capnet_stub__", ""),
            "psycopg 스텁을 sys.modules 에 남겼다",
        )
        self.assertTrue(
            hasattr(mod, "connect") or getattr(mod, "__file__", None),
            "sys.modules['psycopg'] 가 빈 스텁이다 — 다른 검사가 이걸 집는다",
        )

    def test_probe_module_actually_loaded(self) -> None:
        """로더가 조용히 실패하면 위 검사들이 **아무것도 안 본다.**"""
        for name in ("assert_media_type", "store_stream", "blob_path",
                     "purge_blob", "InputRejected", "InputTooLarge"):
            with self.subTest(name=name):
                self.assertTrue(hasattr(inputs, name), f"{name} 을 못 불러왔다")


if __name__ == "__main__":
    unittest.main()
