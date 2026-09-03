"""`openapi.yaml` 이 실제 라우트와 어긋나지 않는지 본다.

## 왜 있는가

드리프트가 **조용히** 쌓였다. `/v1/ops/*` · `/v1/inputs/*` · 증서 계열 15개가 코드에는 있고
문서에는 없었다 — 여러 세대에 걸쳐서다. 문서만 보고 붙이는 쪽에는 그 경로들이 **없는 것**이다.

한 번 맞추는 것으로는 다시 벌어진다. 그래서 검사로 남긴다.

## 무엇을 지키나

1. `include_in_schema=False` 가 아닌 모든 라우트는 `openapi.yaml` 에 있다 — **메서드까지**
2. `openapi.yaml` 의 모든 항목은 실제 라우트다 (지운 API 가 문서에 남지 않는다) — **메서드까지**
3. 두 사본(`apps/core/` · `docs/spec/`)이 같다

**경로만 보던 때의 구멍 (2026-09-01).** 처음에는 **경로**만 봤다. 그래서 이미 문서에 있는
경로에 **메서드를 하나 더 붙이면 아무것도 걸리지 않았다** — Wave I 가
`PATCH /v1/capabilities/{id}` 를 더했을 때 이 검사는 조용했고, 문서에는 **손으로** 넣었다.
다음에 그러면 빠진다. 지금은 `(메서드, 경로)` 쌍으로 본다.

## 왜 파싱을 손으로 하나

`unittest discover` 는 **의존성 없이** 돈다 (CI 단위 잡은 아무것도 설치하지 않는다).
`app.main` 을 임포트하면 fastapi 가 필요하고, YAML 로 읽으면 pyyaml 이 필요하다.
그래서 소스와 문서를 **텍스트로** 본다 — 이 검사가 지키려는 것에는 그걸로 충분하다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"
SPEC = ROOT / "apps" / "core" / "openapi.yaml"
SPEC_COPY = ROOT / "docs" / "spec" / "openapi.yaml"

# @app.get("/v1/x") · @app.post("/v1/x", include_in_schema=False)
ROUTE_RE = re.compile(r'^@app\.(get|post|put|patch|delete)\(\s*"([^"]+)"([^)]*)\)', re.M)
# 최상위 paths 항목 — 두 칸 들여쓴 "/..." 줄
PATH_RE = re.compile(r'^  (/\S*?):\s*$', re.M)


# 경로 블록 안의 메서드 — 네 칸 들여쓴 `get:` 같은 줄
METHOD_RE = re.compile(r"^    (get|post|put|patch|delete):\s*$", re.M)


# openapi.yaml 머리말 — `info:` 블록의 두 칸 들여쓴 항목.
_INFO_RE = re.compile(r"^info:\n((?:  \S.*\n|  .*\n)*?)^\S", re.M)


def _spec_info(key: str) -> str | None:
    """`info.<key>` 를 텍스트로 뽑는다 (pyyaml 없이 — 단위 잡은 의존성 0)."""
    m = re.search(rf"^info:\n(?:.*\n)*?^  {re.escape(key)}:\s*(\S.*?)\s*$",
                  SPEC.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip('"\'') if m else None


def _app_kwarg(key: str) -> str | None:
    """`app = FastAPI(...)` 의 키워드 인자. 주석 줄은 건너뛴다.

    **범위를 괄호 균형으로 닫는다.** 처음에는 `^app = FastAPI\\((.*?)^\\)` 로 잡았는데,
    호출을 한 줄로 접으면 그 정규식이 **파일 뒤쪽의 다른 `)`** 까지 훑었다 — 그래도
    답이 맞아 통과했다. 우연히 맞는 파서는 다음번에 조용히 틀린다.
    """
    src = MAIN.read_text(encoding="utf-8")
    start = src.find("app = FastAPI(")
    if start < 0:
        return None
    i = start + len("app = FastAPI(")
    depth = 1
    while i < len(src) and depth:
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
        i += 1
    if depth:
        return None
    body = "\n".join(
        ln for ln in src[start:i].splitlines() if not ln.strip().startswith("#")
    )
    kw = re.search(rf'\b{re.escape(key)}\s*=\s*"([^"]*)"', body)
    return kw.group(1) if kw else None


def routes() -> list[tuple[str, bool]]:
    """(경로, 문서화 대상인가) 목록."""
    src = MAIN.read_text(encoding="utf-8")
    return [
        (path, "include_in_schema=False" not in rest)
        for _method, path, rest in ROUTE_RE.findall(src)
    ]


def route_ops() -> list[tuple[str, str, bool]]:
    """(메서드, 경로, 문서화 대상인가) 목록. **경로만 보면 메서드 추가가 새어 나간다.**"""
    src = MAIN.read_text(encoding="utf-8")
    return [
        (method, path, "include_in_schema=False" not in rest)
        for method, path, rest in ROUTE_RE.findall(src)
    ]


def spec_paths() -> set[str]:
    return set(PATH_RE.findall(SPEC.read_text(encoding="utf-8")))


def spec_ops() -> set[tuple[str, str]]:
    """openapi 가 문서화한 `(메서드, 경로)` 쌍."""
    text = SPEC.read_text(encoding="utf-8")
    parts = re.split(r"^  (/\S*?):\s*$", text, flags=re.M)
    ops: set[tuple[str, str]] = set()
    for i in range(1, len(parts), 2):
        path, body = parts[i], parts[i + 1]
        ops.update((method, path) for method in METHOD_RE.findall(body))
    return ops


class OpenApiDrift(unittest.TestCase):
    def test_every_public_route_is_documented(self) -> None:
        documented = spec_paths()
        missing = sorted({p for p, public in routes() if public} - documented)
        self.assertEqual(
            missing, [], f"openapi.yaml 에 없는 라우트 {len(missing)}개: {missing}"
        )

    def test_every_public_operation_is_documented(self) -> None:
        """**메서드까지** 본다 — 이미 있는 경로에 `PATCH` 를 붙여도 걸린다."""
        documented = spec_ops()
        missing = sorted(
            (m, p) for m, p, public in route_ops() if public and (m, p) not in documented
        )
        self.assertEqual(
            missing, [], f"openapi.yaml 에 없는 (메서드, 경로) {len(missing)}개: {missing}"
        )

    def test_no_phantom_operations(self) -> None:
        """문서에만 있는 메서드 — 지운 동작이 남으면 붙이는 쪽이 헛짚는다.

        `include_in_schema=False` 인 라우트도 **실재하므로** 여기서는 센다
        (`/openapi.yaml` 이 그 예다 — 스펙을 내려 주는 자기 자신이라 자동 스키마에서는
        빼지만 손으로 쓴 문서에는 적어 둔다).
        """
        real = {(m, p) for m, p, _ in route_ops()}
        phantom = sorted(spec_ops() - real)
        self.assertEqual(
            phantom, [], f"라우트가 없는 openapi 항목 {len(phantom)}개: {phantom}"
        )

    def test_no_phantom_paths(self) -> None:
        """문서에만 있는 경로 — 지운 API 가 남아 있으면 붙이는 쪽이 헛짚는다."""
        declared = {p for p, _ in routes()}
        phantom = sorted(spec_paths() - declared)
        self.assertEqual(
            phantom, [], f"라우트가 없는 openapi 경로 {len(phantom)}개: {phantom}"
        )

    def test_two_copies_match(self) -> None:
        self.assertEqual(
            SPEC.read_text(encoding="utf-8"),
            SPEC_COPY.read_text(encoding="utf-8"),
            "apps/core/openapi.yaml 과 docs/spec/openapi.yaml 이 다르다",
        )

    def test_version_agrees_with_the_app(self) -> None:
        """정적 스펙과 **실행 중인 앱**이 같은 버전을 말하는가.

        갈려 있었다 (2026-09-03 실측): `openapi.yaml` 은 `0.3.0`, `FastAPI(...)` 는
        `0.2.0`. 같은 Core 인데 `GET /openapi.yaml` 과 `GET /openapi.json` 이 서로
        다른 버전을 준다 — 붙이는 쪽은 어느 쪽을 믿어야 할지 알 수 없다.

        경로·메서드는 이미 못박혀 있었지만 **머리말(`info`)은 아무도 안 봤다.**
        """
        self.assertEqual(_spec_info("version"), _app_kwarg("version"),
                         "openapi.yaml info.version 과 FastAPI(version=) 가 다르다")

    def test_title_agrees_with_the_app(self) -> None:
        """제목이 갈리면 스펙 두 개가 **다른 서비스**로 읽힌다."""
        self.assertEqual(_spec_info("title"), _app_kwarg("title"),
                         "openapi.yaml info.title 과 FastAPI(title=) 가 다르다")

    def test_info_parser_actually_finds_things(self) -> None:
        """머리말을 못 읽으면 위 둘이 `None == None` 으로 조용히 통과한다."""
        for key in ("title", "version"):
            self.assertIsNotNone(_spec_info(key), f"openapi.yaml info.{key} 를 못 읽었다")
            self.assertIsNotNone(_app_kwarg(key), f"FastAPI({key}=) 를 못 읽었다")

    def test_parser_actually_finds_things(self) -> None:
        """검사가 0개를 비교하며 통과하는 상태를 막는다."""
        self.assertGreater(len(routes()), 20)
        self.assertGreater(len(spec_paths()), 20)
        self.assertGreater(len(route_ops()), 20)
        self.assertGreater(len(spec_ops()), 20)


if __name__ == "__main__":
    unittest.main()
