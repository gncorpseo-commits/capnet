r"""`scripts/lib/*.sh` 의 **판정 함수에 단위 검사가 있는가** (큐 #47 · `#44`·`#205` 옆).

## 실측 (2026-09-05)

| 함수 | 파일 | 단위 검사 |
|---|---|---|
| `tally_verdict` | `lib/tally.sh` | ✅ `test_room_tally.py` — 실제로 `source` 해서 부른다 |
| `probe_verdict` | `lib/authprobe.sh` | ✅ `test_prod_room_auth_probe.py` — 같음 |
| **`ccurl`** | `lib/http.sh` | **없었다** |

셋 중 **하나만 검사 밖**이었다. 그리고 그 하나에서 결함이 나왔다.

## 결함 — 주석이 금지한 것을 코드가 하고 있었다

`lib/http.sh` 의 「시크릿 위생」은 이렇게 적혀 있다:

> 키는 환경변수로만 받는다. **인자로 받으면 프로세스 목록(ps)에 남는다.**

그래 놓고 헤더를 **curl 의 인자로** 넘기고 있었다. `-H` 의 값도 argv 다.
실측 (`ccurl` 을 띄워 놓고 `pgrep -a curl`):

```text
curl -H Authorization: CapNet-Key ck_deadbeef.SECRETVALUE123 -s --max-time 4 http://…
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^ 같은 호스트의 아무나 읽는다
```

`ps` 는 **다른 사용자에게도 보인다** (`hidepid` 를 켜지 않은 기본 리눅스). 데모·촬영은
공용 워크스테이션에서 돈다. 「환경변수로만 받는다」의 목적이 여기서 무너져 있었다.

### 고친 방법 — `-H @파일`

curl **7.55+** 는 헤더를 파일에서 읽는다. 파일은 `0600` 이고 호출이 끝나면 지운다.

```text
curl -H @/tmp/capnet-hdr-JdOf7v -s --max-time 4 http://…     ← 키가 안 보인다
```

`|| rc=$?` 로 받는 이유가 있다. 호출자는 전부 `set -e` 다 — 그냥 두면 curl 이 실패할 때
**지우기 전에** 셸이 죽어 **시크릿 파일이 `/tmp` 에 남는다.** 고치면서 만들 뻔한 두 번째
결함이라 검사로 못박는다.

## 어떻게 검사하나 — 가짜 `curl`

Docker 도 살아 있는 Core 도 필요 없다. `PATH` 앞에 **argv 를 받아 적는 `curl`** 을 놓고
`ccurl` 을 부른다. 그 함수가 실제로 무엇을 넘기는지 그대로 보인다.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "scripts" / "lib"
HTTP = LIB / "http.sh"

KEY = "ck_deadbeef.SUPERSECRETVALUE"

# 가짜 curl — argv 를 적고, `-H @파일` 이면 그 내용과 권한도 적는다.
STUB = r"""#!/usr/bin/env bash
out="$STUB_OUT"
printf '%s\n' "$@" > "$out.argv"
prev=""
for a in "$@"; do
  if [ "$prev" = "-H" ] && [ "${a#@}" != "$a" ]; then
    f="${a#@}"
    cat "$f" > "$out.header"
    stat -c '%a' "$f" > "$out.mode"
    printf '%s\n' "$f" > "$out.path"
  fi
  prev="$a"
done
exit "${STUB_RC:-0}"
"""


def run_ccurl(env: dict[str, str], args: str = "-s http://example") -> dict[str, object]:
    """가짜 curl 로 `ccurl` 을 한 번 부르고 관측값을 돌려준다."""
    with tempfile.TemporaryDirectory() as tmp:
        stub_dir = Path(tmp) / "bin"
        stub_dir.mkdir()
        stub = stub_dir / "curl"
        stub.write_text(STUB, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        out = Path(tmp) / "obs"

        full = dict(os.environ)
        full.pop("CAPNET_API_KEY", None)
        full.pop("CAPNET_API_KEY_FILE", None)
        full.update(env)
        full["STUB_OUT"] = str(out)
        full["PATH"] = f"{stub_dir}:{full['PATH']}"

        proc = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", f'source "{HTTP}"; ccurl {args}'],
            capture_output=True, text=True, env=full, timeout=60,
        )
        read = lambda suffix: (  # noqa: E731
            Path(f"{out}.{suffix}").read_text(encoding="utf-8")
            if Path(f"{out}.{suffix}").is_file() else None
        )
        return {
            "rc": proc.returncode,
            "argv": (read("argv") or "").splitlines(),
            "header": read("header"),
            "mode": (read("mode") or "").strip(),
            "path": (read("path") or "").strip(),
            "stderr": proc.stderr,
        }


class TestTheKeyNeverReachesArgv(unittest.TestCase):
    """**여기가 핵심이다.** `-H` 의 값도 argv 라 `ps` 에 그대로 뜬다."""

    def test_key_is_not_in_the_arguments(self) -> None:
        got = run_ccurl({"CAPNET_API_KEY": KEY})
        self.assertTrue(got["argv"], f"가짜 curl 이 안 불렸다: {got['stderr']}")
        for arg in got["argv"]:
            self.assertNotIn(KEY, arg, f"키가 argv 에 있다: {got['argv']}")

    def test_the_header_still_arrives(self) -> None:
        """새지 않게 하려다 **인증을 안 붙이면** 강제 모드가 전부 401 이 된다."""
        got = run_ccurl({"CAPNET_API_KEY": KEY})
        self.assertEqual(f"Authorization: CapNet-Key {KEY}\n", got["header"])
        self.assertIn("-H", got["argv"])

    def test_header_file_is_not_world_readable(self) -> None:
        got = run_ccurl({"CAPNET_API_KEY": KEY})
        self.assertEqual("600", got["mode"], "헤더 파일이 0600 이 아니다")

    def test_header_file_is_removed_after_success(self) -> None:
        got = run_ccurl({"CAPNET_API_KEY": KEY})
        self.assertTrue(got["path"], "헤더 파일 경로를 못 봤다")
        self.assertFalse(Path(str(got["path"])).exists(), "성공 뒤에도 시크릿 파일이 남는다")

    def test_header_file_is_removed_after_failure(self) -> None:
        """호출자는 `set -e` 다 — 그냥 두면 **지우기 전에** 셸이 죽는다."""
        got = run_ccurl({"CAPNET_API_KEY": KEY, "STUB_RC": "7"})
        self.assertEqual(7, got["rc"], "curl 의 종료 코드를 안 넘긴다")
        self.assertTrue(got["path"], "헤더 파일 경로를 못 봤다")
        self.assertFalse(Path(str(got["path"])).exists(), "실패 뒤 시크릿 파일이 남는다")


class TestKeyResolution(unittest.TestCase):
    def test_without_a_key_no_header_is_added(self) -> None:
        """강제가 꺼진 데모 경로를 깨지 않는다."""
        got = run_ccurl({})
        self.assertIsNone(got["header"])
        self.assertNotIn("-H", got["argv"])
        self.assertIn("-s", got["argv"])

    def test_key_file_is_read_and_trimmed(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".key", delete=False) as fh:
            fh.write(f"  {KEY}\n")
            path = fh.name
        try:
            got = run_ccurl({"CAPNET_API_KEY_FILE": path})
            self.assertEqual(f"Authorization: CapNet-Key {KEY}\n", got["header"])
        finally:
            os.unlink(path)

    def test_env_wins_over_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".key", delete=False) as fh:
            fh.write("ck_fromfile.AAA\n")
            path = fh.name
        try:
            got = run_ccurl({"CAPNET_API_KEY": KEY, "CAPNET_API_KEY_FILE": path})
            self.assertEqual(f"Authorization: CapNet-Key {KEY}\n", got["header"])
        finally:
            os.unlink(path)


class TestEveryLibFunctionHasAUnitCheck(unittest.TestCase):
    """셋 중 하나만 검사 밖이었다 — 다시 그렇게 되지 않게 센다."""

    FUNCTIONS = {
        "tally_verdict": "test_room_tally.py",
        "probe_verdict": "test_prod_room_auth_probe.py",
        "ccurl": "test_lib_http_never_leaks_the_key.py",
    }

    def test_every_function_is_named_by_a_test(self) -> None:
        tests = ROOT / "tests"
        for func, owner in self.FUNCTIONS.items():
            with self.subTest(function=func):
                path = tests / owner
                self.assertTrue(path.is_file(), f"{owner} 가 없다")
                self.assertIn(func, path.read_text(encoding="utf-8"))

    def test_no_lib_function_is_unclaimed(self) -> None:
        """새 판정 함수가 검사 없이 생기면 운다."""
        import re
        found = set()
        for path in sorted(LIB.glob("*.sh")):
            found |= set(re.findall(r"^([a-z_][a-z0-9_]*)\(\)", path.read_text(encoding="utf-8"), re.M))
        self.assertTrue(found, "lib 함수를 하나도 못 찾았다")
        self.assertEqual(set(self.FUNCTIONS), found,
                         f"검사 주인이 없는 lib 함수: {sorted(found - set(self.FUNCTIONS))}")


if __name__ == "__main__":
    unittest.main()
