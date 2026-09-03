"""버전 문자열이 **여러 곳에서 갈리지 않는가** (큐 #23).

## 왜 있는가

#201 이 Core 에서 같은 사고를 잡았다 — `openapi.yaml` 은 `0.3.0`, `FastAPI(version=)` 은
`0.2.0`. **같은 서비스가 두 버전을 말하고 있었다.** 그 검사는 Core 두 자리를 못박았다.

전수했다 (2026-09-03). 나머지는 **`capreq` 네 자리**였다:

| 어디 | 값 |
|---|---|
| `capreq/pyproject.toml` | `0.1.0` |
| `capreq/src/capreq/__init__.py` `__version__` | `0.1.0` |
| `server.py` `FastAPI(version=…)` | `0.1.0` (리터럴) |
| `gemma_server.py` `FastAPI(version=…)` | `0.1.0` (리터럴) |

**오늘은 넷 다 같다.** 그런데 맞추는 것이 없다 — 하나만 올리면 조용히 갈린다.
Core 가 실제로 그렇게 갈렸다.

## 무엇을 고쳤나

두 서버의 **리터럴을 없앴다.** 이제 `capreq.__version__` 하나에서 온다.
남은 자리는 둘(`pyproject.toml` · `__init__.py`)이고, 이 검사가 **같은지 본다.**

`pyproject.toml` 은 빌드가 읽고 `__version__` 은 코드가 읽는다 — 둘을 합칠 수는 없어서
(이 환경에는 `tomllib` 로 읽을 빌드 백엔드 설정만 있고 동적 버전 배관이 없다)
**한쪽이 움직이면 걸리게** 한다.

## 무엇을 고정하지 **않나**

**버전 값 자체.** `0.1.0` 을 박으면 올릴 때마다 검사가 일을 시킨다.
보는 것은 **서로 같은가** 하나다.

Node(`apps/node/app/main.py`)의 `0.2.0` 은 대조 상대가 없다 — 스펙 파일이 없어서
갈릴 자리가 없다. 짝이 생기면 그때 여기 넣는다.
"""

from __future__ import annotations

import ast
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "capreq" / "pyproject.toml"
INIT = ROOT / "capreq" / "src" / "capreq" / "__init__.py"
SERVERS = (
    ROOT / "capreq" / "src" / "capreq" / "server.py",
    ROOT / "capreq" / "src" / "capreq" / "gemma_server.py",
)

_SEMVER = re.compile(r"^\d+\.\d+\.\d+")


def _pyproject_version() -> str | None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    v = (data.get("project") or {}).get("version")
    return str(v) if v else None


def _dunder_version() -> str | None:
    tree = ast.parse(INIT.read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == "__version__"
                and isinstance(n.value, ast.Constant)):
            return str(n.value.value)
    return None


def _fastapi_version_args(path: Path) -> list[ast.expr]:
    """그 파일의 `FastAPI(...)` 호출에 넘긴 `version=` 값들."""
    out: list[ast.expr] = []
    for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "FastAPI"):
            continue
        for kw in n.keywords:
            if kw.arg == "version":
                out.append(kw.value)
    return out


class TestOneSourceOfVersion(unittest.TestCase):
    def test_pyproject_and_dunder_agree(self) -> None:
        py, dunder = _pyproject_version(), _dunder_version()
        self.assertIsNotNone(py, "pyproject.toml 의 project.version 을 못 읽었다")
        self.assertIsNotNone(dunder, "__version__ 을 못 읽었다")
        self.assertEqual(py, dunder,
                         "capreq/pyproject.toml 과 __version__ 이 다르다")

    def test_versions_look_like_versions(self) -> None:
        """파서가 엉뚱한 것을 집어 `None == None` 으로 통과하는 것을 막는다."""
        for name, value in (("pyproject", _pyproject_version()),
                            ("__version__", _dunder_version())):
            with self.subTest(name=name):
                self.assertIsNotNone(value)
                assert value is not None
                self.assertRegex(value, _SEMVER, f"{name} 이 버전처럼 안 생겼다: {value!r}")


class TestServersDoNotHardcode(unittest.TestCase):
    """**여기가 #201 이 잡은 사고와 같은 자리다.**"""

    def test_no_literal_version_in_servers(self) -> None:
        bad = []
        for path in SERVERS:
            for value in _fastapi_version_args(path):
                if isinstance(value, ast.Constant):
                    bad.append(f"{path.name}: version={value.value!r}")
        self.assertEqual(
            [], bad,
            "FastAPI(version=…) 에 리터럴을 박았다 — `capreq.__version__` 에서 받는다: "
            f"{bad}",
        )

    def test_servers_use_the_package_version(self) -> None:
        for path in SERVERS:
            with self.subTest(server=path.name):
                args = _fastapi_version_args(path)
                self.assertTrue(args, f"{path.name} 에 FastAPI(version=…) 가 없다")
                self.assertTrue(
                    all(isinstance(a, ast.Name) and a.id == "__version__" for a in args),
                    f"{path.name} 이 __version__ 을 안 쓴다",
                )

    def test_servers_import_it(self) -> None:
        """이름만 맞고 임포트가 없으면 실행할 때 죽는다."""
        for path in SERVERS:
            with self.subTest(server=path.name):
                self.assertIn("from capreq import __version__",
                              path.read_text(encoding="utf-8"),
                              f"{path.name} 이 __version__ 을 임포트하지 않는다")


class TestProbeActuallyWorks(unittest.TestCase):
    def test_found_the_fastapi_calls(self) -> None:
        """`FastAPI(` 모양이 바뀌면 위 검사가 **0개를 훑으며** 통과한다."""
        total = sum(len(_fastapi_version_args(p)) for p in SERVERS)
        self.assertGreaterEqual(total, 2, f"FastAPI(version=…) 를 {total}개밖에 못 찾았다")


if __name__ == "__main__":
    unittest.main()
