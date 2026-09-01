"""라이선스 고지 검사가 **capreq 까지 보는가**.

## 왜 있는가

`CLAUDE.md` 저장소 규칙:

> 의존성을 추가하는 커밋에서 `THIRD-PARTY-LICENSES.md` 에 한 줄을 같이 넣는다.
> **예외 없음.**

그런데 그것을 강제하는 `check_submission.check_deps_declared` 는
**`apps/core`·`apps/node` 의 `requirements.txt` 만** 봤다. `capreq` 는 저장소에 함께
배포되는 모듈이고 자기 의존성을 `pyproject.toml` 로 선언한다
(`httpx` · extra 로 `fastapi`·`uvicorn`·`python-multipart`).

**구멍이 실재했다 (2026-09-02 실측).** 고치기 전 코드에 미고지 의존성을 하나 넣고
돌렸더니 **28/28 통과**했다. 지금은 잡는다.

지금까지 안 터진 이유는 그 넷이 **Core 와 겹쳐** 이미 고지돼 있었기 때문이다 —
**우연이지 방어가 아니었다.** 대회 2차 심사가 라이선스를 본다 (절대규칙 6 참조).

## 무엇을 보나

1. 검사가 **`capreq/pyproject.toml` 을 읽는가**
2. `[build-system] requires` 를 의존성으로 세지 않는가 (빌드 도구는 배포물이 아니다)
3. **0개를 훑으며 통과하지 않는가** — 경로가 바뀌면 조용해지는 것이 원래 실패 방식이었다

## 무엇을 안 보나

**개수를 못박지 않는다.** 의존성은 늘 수 있다. 여기서 보는 것은 **범위**다.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_submission.py"
PYPROJECT = ROOT / "capreq" / "pyproject.toml"
LICENSES = ROOT / "THIRD-PARTY-LICENSES.md"


class TestCheckCoversCapreq(unittest.TestCase):
    def setUp(self) -> None:
        # **주석·docstring 을 비우고 본다.** 안 그러면 「설명에 적어 뒀으니 통과」가 된다 —
        # 이 저장소에서 다섯 번 난 사고이고, 이 검사를 짜면서 **여섯 번째로** 겪었다:
        # 처음엔 원문을 훑어서 뮤테이션 셋이 전부 안 물렸다 (docstring 이 낱말을 갖고 있었다).
        self.text = code_only(CHECK)

    def test_reads_capreq_pyproject(self) -> None:
        self.assertIn('"capreq/pyproject.toml"', self.text, "capreq 의존성을 안 본다")

    def test_uses_a_parser_not_a_regex(self) -> None:
        """정규식으로 짰다가 `packages.find` 의 `where = ["src"]` 까지 의존성으로 집었다."""
        self.assertIn("import tomllib", self.text, "toml 을 정규식으로 훑으면 또 헛짚는다")
        self.assertNotIn("as tomllib", self.text, "이름만 tomllib 인 다른 파서를 쓴다")

    def test_ignores_build_system(self) -> None:
        """`setuptools`·`wheel` 은 빌드 도구다 — 배포물에 안 들어간다."""
        self.assertIn("build-system", CHECK.read_text(encoding="utf-8"),
                      "빌드 의존성을 왜 빼는지 근거가 없다")
        self.assertNotIn("requires", self.text.split("def check_deps_declared")[0][-400:])

    def test_refuses_to_pass_on_zero(self) -> None:
        """경로가 바뀌면 **조용히** 0건을 훑으며 통과한다 — 그게 원래 실패 방식이다."""
        # **그 함수의 몸통만** 본다 — 뒤에 나오는 다른 함수에도 `seen > 0` 이 있어서,
        # 통째로 훑으면 이 검사가 헛돈다 (뮤테이션으로 잡았다).
        after = self.text.split("def check_deps_declared", 1)[1]
        body = after.split("\ndef ", 1)[0]
        self.assertRegex(body, r"seen\s*>\s*\d+", "0건 통과를 막는 하한이 없다")


class TestDeclaredDepsAreActuallyCovered(unittest.TestCase):
    """문서가 실제로 덮고 있는가 — 검사기와 별개로 여기서도 본다."""

    def test_capreq_runtime_deps_are_declared(self) -> None:
        import tomllib

        with PYPROJECT.open("rb") as fh:
            doc = tomllib.load(fh)
        project = doc.get("project") or {}
        specs = list(project.get("dependencies") or [])
        for extra in (project.get("optional-dependencies") or {}).values():
            specs.extend(extra)
        self.assertGreater(len(specs), 2, "capreq 의존성을 하나도 못 읽었다")

        declared = LICENSES.read_text(encoding="utf-8").lower()
        missing = sorted(
            {re.split(r"[\[=<>!~;\s]", s)[0].strip().lower() for s in specs} - {""}
            - {n for n in re.findall(r"[a-z0-9_.\-]+", declared)}
        )
        self.assertEqual(missing, [], f"고지되지 않은 capreq 의존성: {missing}")


if __name__ == "__main__":
    unittest.main()
