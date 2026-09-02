"""시크릿이 **로그·화면으로 나가지 않는가.**

## 왜 있는가

`CLAUDE.md` 보안절이 **「시크릿을 로그·커밋 메시지·출력에 노출하지 않는다」** 고 적는다.
그 규칙을 보는 것은 `scripts/check_submission.py` 의 `check_secrets` **하나**인데,
그건 **패키징 대상 파일에 시크릿 값이 박혀 있는가**를 본다.

**런타임에 흘러 나가는 쪽은 아무도 안 봤다** — `logger.info(...)` 나 `echo` 에
키·증서가 실리면 그 값은 컨테이너 로그·CI 출력·터미널 기록에 남는다.

**전수했다 (2026-09-02). 새는 곳은 없다.** 이 검사는 **다음에 새지 않게** 하는 것이다.

## 무엇을 고정하나

1. 파이썬의 로그·출력 호출이 **시크릿 이름의 값**을 인자로 싣지 않는다.
   예외는 아래 `ALLOWED_PY` — **왜 괜찮은지**를 적어야 한다
2. 셸의 `echo`·`printf` 가 **화면으로** 시크릿 변수를 마스킹 없이 내보내지 않는다

## 도구를 못 믿은 이야기 (적어 둔다)

처음 훑었을 때 **0건**이 나왔다. 그런데 `apps/core/app/apikey_cli.py` 는 발급한 키를
**분명히 찍는다.** 스캐너가 `out["secret"]` 같은 **첨자 문자열**을 안 보고 있었다 —
`ast.Name` 과 `ast.Attribute` 만 모았다.

고치니 그 둘이 나왔다. **0 을 「없다」로 읽지 않았다** — 이번 회차가 계속 고쳐 온 것과
같은 자리다.

셸 쪽도 처음엔 **3건**이 나왔는데 전부 오탐이었다 (파이프로 **파일**에 쓰는 것 둘 ·
`$secret_file` 이라는 **경로** 하나). 규칙을 좁혔다 — 넓게 잡아 설명·정상 코드가
걸리면 **검사를 넓히지 말고 패턴을 좁힌다** (`measured-claims.md` §6 · `_srcguard` 사고).

## 무엇을 안 보나

**값이 실제로 시크릿인지는 모른다** — 이름으로 본다. `check_secrets` 가 값 쪽을
따로 본다. 여기는 **경로**(logging·stdout)를 본다.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_TREES = (ROOT / "apps", ROOT / "capreq" / "src", ROOT / "scripts")
SKIP_PARTS = {"__pycache__", "node_modules"}

SINKS = frozenset({
    "print", "info", "warning", "error", "debug", "exception", "critical", "log",
})
# **낱말이 모자라면 검사가 눈이 먼다.** 실제로 그랬다 — `node_onboard.sh` 의
# `$cred` 를 처음 목록이 못 잡아 뮤테이션이 안 물렸다. 짧은 형태도 넣는다.
SECRET_WORDS = ("secret", "credential", "cred", "key", "apikey", "token",
                "password", "authorization")
# 이름에 시크릿 낱말이 들어가지만 **값은 시크릿이 아닌** 것들 (경로·존재 여부·접두).
NOT_SECRET = ("_file", "_path", "_dir", "_prefix", "prefix", "present", "_name")

# 예외 — **왜 괜찮은가**를 적는다. 못 적으면 예외가 아니다.
ALLOWED_PY: dict[tuple[str, str], str] = {
    ("apps/core/app/apikey_cli.py", "print"): (
        "키 **발급** CLI 다. 해시만 저장하므로 이때 한 번 보여 주지 않으면 "
        "운영자가 키를 가질 방법이 없다 — 코드가 그렇게 적고 있다 "
        "(「이번 한 번만 보인다 — 저장은 해시만 된다」)"
    ),
}


def _is_secret_name(name: str) -> bool:
    low = name.lower()
    if any(n in low for n in NOT_SECRET):
        return False
    return any(w in low for w in SECRET_WORDS)


def _py_files():
    for tree in PY_TREES:
        for p in sorted(tree.rglob("*.py")):
            if not any(s in p.parts for s in SKIP_PARTS):
                yield p


def python_hits() -> list[tuple[str, int, str, list[str]]]:
    """`(파일, 줄, 싱크, 실린 시크릿 이름들)`."""
    out = []
    for p in _py_files():
        try:
            mod = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(mod):
            if not isinstance(node, ast.Call):
                continue
            sink = (
                node.func.id if isinstance(node.func, ast.Name)
                else node.func.attr if isinstance(node.func, ast.Attribute)
                else None
            )
            if sink not in SINKS:
                continue
            names: set[str] = set()
            for arg in node.args:
                for sub in ast.walk(arg):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
                    elif isinstance(sub, ast.Attribute):
                        names.add(sub.attr)
                    elif (
                        isinstance(sub, ast.Subscript)
                        and isinstance(sub.slice, ast.Constant)
                        and isinstance(sub.slice.value, str)
                    ):
                        # `out["secret"]` — 첫 판에 이걸 놓쳐 0건이 나왔다.
                        names.add(sub.slice.value)
            bad = sorted(n for n in names if _is_secret_name(n))
            if bad:
                out.append((str(p.relative_to(ROOT)), node.lineno, sink, bad))
    return out


# 셸 예외 — **왜 화면이 아닌가**를 적는다.
ALLOWED_SH: dict[tuple[str, str], str] = {
    ("scripts/run_integration.sh", "PGPASSWORD"): (
        "`url_for()` 는 **함수의 반환값**을 `echo` 로 내보내는 셸 관용구다 — "
        "호출자가 전부 `$(url_for …)` 로 받아 `DATABASE_URL` 에 넣는다. 화면으로 "
        "가지 않는다. 값도 CI·로컬 일회용 postgres 의 것이다 (`capnet`)"
    ),
}

_EXPANSION = re.compile(r'(?<!\\)\$\{?([A-Za-z_][A-Za-z0-9_]*)([^}"]*)\}?')
_MASKS = ("%%", "##", "%", "#", ":0:", ":-")


def shell_hits() -> list[tuple[str, int, str, str]]:
    """`echo`·`printf` 가 **화면으로** 시크릿을 내보내는 자리.

    파이프·리다이렉트가 있는 줄은 뺀다 — 화면이 아니라 파일·다음 프로그램으로 간다.
    """
    out = []
    for p in sorted((ROOT / "scripts").glob("*.sh")):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            st = line.strip()
            # **줄 첫머리만 보면 안 된다.** `if [ -n "$key" ]; then echo …` 처럼
            # 복합문 안의 echo 를 놓친다 — 실제로 그래서 뮤테이션이 안 물렸다.
            if not re.search(r"\b(echo|printf)\b", st):
                continue
            if "|" in st or ">" in st:
                continue
            # **`echo` 뒤쪽만 본다.** `if [ -n "$key" ]; then echo "…${key%%.*}…"` 의
            # 앞쪽 조건절까지 보면 마스킹한 출력을 오탐한다 (실제로 그랬다).
            m0 = re.search(r"\b(echo|printf)\b", st)
            tail = st[m0.end():] if m0 else st
            for m in _EXPANSION.finditer(tail):
                var, rest = m.group(1), m.group(2) or ""
                if not _is_secret_name(var):
                    continue
                if any(k in rest for k in _MASKS):
                    continue
                if (str(p.relative_to(ROOT)), var) in ALLOWED_SH:
                    continue
                out.append((str(p.relative_to(ROOT)), i, var, st[:110]))
    return out


class TestPythonDoesNotLogSecrets(unittest.TestCase):
    def test_no_unapproved_secret_in_a_sink(self) -> None:
        """**여기가 핵심이다.** 로그로 나간 값은 컨테이너 로그·CI 기록에 남는다."""
        bad = [
            f"{f}:{ln} {sink}({', '.join(names)})"
            for f, ln, sink, names in python_hits()
            if (f, sink) not in ALLOWED_PY
        ]
        self.assertEqual(
            bad, [],
            "시크릿이 로그·출력으로 나간다 — 마스킹하거나 `ALLOWED_PY` 에 "
            f"근거와 함께 적는다: {bad}",
        )

    def test_allowed_entries_are_real(self) -> None:
        """유령 예외가 남으면 다음 사람이 「여기는 원래 찍는 자리」로 넘어간다."""
        real = {(f, sink) for f, _ln, sink, _n in python_hits()}
        ghosts = sorted(f"{f} {sink}" for (f, sink) in ALLOWED_PY if (f, sink) not in real)
        self.assertEqual(ghosts, [], f"`ALLOWED_PY` 에만 있는 예외: {ghosts}")

    def test_allowed_entries_carry_a_reason(self) -> None:
        thin = sorted(f"{f} {s}" for (f, s), why in ALLOWED_PY.items() if len(why.strip()) < 20)
        self.assertEqual(thin, [], f"근거가 너무 짧다: {thin}")


class TestShellDoesNotEchoSecrets(unittest.TestCase):
    def test_no_secret_reaches_the_screen(self) -> None:
        bad = [f"{f}:{ln} ${var}  {src}" for f, ln, var, src in shell_hits()]
        self.assertEqual(bad, [], f"셸이 시크릿을 화면으로 내보낸다: {bad}")

    def test_shell_allowlist_is_real_and_reasoned(self) -> None:
        """유령 예외가 남으면 다음 사람이 「원래 찍는 자리」로 넘어간다."""
        for (path, var), why in ALLOWED_SH.items():
            with self.subTest(entry=f"{path} ${var}"):
                f = ROOT / path
                self.assertTrue(f.is_file(), f"{path} 가 없다")
                self.assertIn(f"${{{var}}}", f.read_text(encoding="utf-8"),
                              f"{path} 에 ${var} 확장이 없다 — 유령 예외다")
                self.assertGreater(len(why.strip()), 20, "근거가 너무 짧다")


class TestProbeActuallyWorks(unittest.TestCase):
    """**0 을 「없다」로 읽지 않는다** — 첫 판에 그렇게 틀렸다."""

    def test_scanner_sees_the_known_issuance_print(self) -> None:
        """`apikey_cli` 의 발급 출력을 못 보면 스캐너가 눈이 먼 것이다."""
        found = {(f, sink) for f, _ln, sink, _n in python_hits()}
        self.assertIn(
            ("apps/core/app/apikey_cli.py", "print"), found,
            "스캐너가 발급 CLI 의 키 출력을 못 본다 — 첨자(`out[\"secret\"]`)를 놓쳤을 때 그랬다",
        )

    def test_scanner_reads_many_files(self) -> None:
        self.assertGreater(len(list(_py_files())), 30)
        self.assertGreater(len(list((ROOT / "scripts").glob("*.sh"))), 20)

    def test_name_filter_keeps_paths_out(self) -> None:
        """`$secret_file` 은 **경로**다 — 오탐으로 잡으면 검사를 못 쓴다."""
        self.assertFalse(_is_secret_name("secret_file"))
        self.assertFalse(_is_secret_name("key_prefix"))
        self.assertFalse(_is_secret_name("credential_present"))
        self.assertTrue(_is_secret_name("secret"))
        self.assertTrue(_is_secret_name("CAPNET_API_KEY"))
        self.assertTrue(_is_secret_name("node_credential"))


if __name__ == "__main__":
    unittest.main()
