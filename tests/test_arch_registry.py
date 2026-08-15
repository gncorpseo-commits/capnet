"""허용 아키텍처 등록 API 의 규율을 고정한다 (D-arch).

## 왜 있는가

`agent.arch` 는 `agent_arch` 를 FK 로 참조한다(`0008` · I1) — **허용 목록이 DB 행**이고,
없는 arch 로는 Agent 등록이 막힌다. 그런데 그 행을 넣는 경로가 없어서 운영자가 DB 에
직접 INSERT 해야 했다. 이 API 가 그 구멍을 메운다.

**메우면서 새 구멍을 내지 않는 것**이 여기서 볼 것이다.

1. **admin 전용** — 아무나 arch 를 늘리면 allowlist 가 「사실상 전부 허용」이 된다
2. **추가만** — `max_params` 는 계약 게이트의 상한이라 사후에 바꾸면
   **이미 통과한 증서의 근거가 바뀐다**(D15). UPDATE·DELETE 경로를 만들지 않는다
3. **덮어쓰지 않는다** — 중복은 409. 조용히 넘기면 다른 상한으로 다시 등록한 운영자가
   성공했다고 믿고 옛 값을 쓴다
4. **이름을 좁게** — 이 값은 `ARCH_REGISTRY` 조회 키이자 증적 식별자다

## 판정 방식과 그 한계

라우트·역할·문구는 **소스 텍스트**로 본다. 실제 HTTP 동작(401/403/409)은
`prod_room.sh` 와 통합 검사의 몫이다 — 이 리포의 단위 잡은 의존성 0 으로 돈다.
`psycopg` 가 있으면 이름 검증 함수는 직접 호출해 확인한다.
"""

from __future__ import annotations

import importlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _srcguard import code_only as _code_only  # noqa: E402
MAIN = ROOT / "apps" / "core" / "app" / "main.py"
ARCH = ROOT / "apps" / "core" / "app" / "arch.py"

try:
    import psycopg  # noqa: F401
    _HAS_PSYCOPG = True
except ModuleNotFoundError:
    _HAS_PSYCOPG = False


class TestEndpointDiscipline(unittest.TestCase):
    def setUp(self) -> None:
        self.main = MAIN.read_text(encoding="utf-8")
        self.main_code = _code_only(MAIN)

    def _endpoint(self, decorator: str) -> str:
        """그 엔드포인트 **하나만** 잘라 낸다 — 다음 `@app.` 앞까지.

        고정 길이로 자르면 창이 **다음 핸들러까지 넘친다.** 실제로 그래서
        `_require("admin")` 을 `developer` 로 바꾸는 변이를 놓쳤다 — 바로 뒤
        `capabilities_create` 의 `_require("admin")` 이 창 안에 들어와 통과시켰다.
        """
        i = self.main_code.index(decorator)
        rest = self.main_code[i + len(decorator):]
        j = rest.find("\n@app.")
        return self.main_code[i:i + len(decorator) + (j if j != -1 else len(rest))]

    def test_post_requires_admin(self) -> None:
        body = self._endpoint('@app.post("/v1/arches")')
        self.assertIn('_require("admin"', body,
                      "arch 등록이 admin 을 요구하지 않는다 — allowlist 가 무의미해진다")

    def test_get_is_not_public(self) -> None:
        """조회도 열지 않는다 — 어떤 모델 구조를 받는가는 운영 정보다."""
        body = self._endpoint('@app.get("/v1/arches")')
        self.assertIn("_require(", body, "arch 목록이 공개돼 있다")

    def test_no_update_or_delete_route(self) -> None:
        """**갱신·삭제 경로를 만들지 않는다** (D15).

        `max_params` 를 사후에 올리면 이미 통과한 증서의 근거가 바뀐다.
        """
        for verb in ("put", "patch", "delete"):
            self.assertNotIn(
                f'@app.{verb}("/v1/arches', self.main_code,
                f"/v1/arches 에 {verb.upper()} 경로가 생겼다 — 상한을 사후에 바꾸면 증적이 깨진다",
            )

    def test_documented_in_both_openapi_copies(self) -> None:
        """`test_openapi_drift` 는 경로만 본다 — 두 사본이 같은지도 여기서 본다."""
        a = (ROOT / "apps" / "core" / "openapi.yaml").read_text(encoding="utf-8")
        b = (ROOT / "docs" / "spec" / "openapi.yaml").read_text(encoding="utf-8")
        self.assertIn("/v1/arches:", a)
        self.assertEqual(a, b, "openapi.yaml 두 사본이 다르다")


class TestArchModuleDiscipline(unittest.TestCase):
    def test_no_update_or_delete_sql(self) -> None:
        code = _code_only(ARCH).upper()
        self.assertNotIn("UPDATE AGENT_ARCH", code)
        self.assertNotIn("DELETE FROM AGENT_ARCH", code)
        # 조용한 무시도 금지 — 중복은 알려야 한다.
        self.assertNotIn("ON CONFLICT", code)

    @unittest.skipUnless(_HAS_PSYCOPG, "psycopg 없음 — 의존성 있는 환경에서만 돈다")
    def test_name_pattern_rejects_junk(self) -> None:
        sys.path.insert(0, str(ROOT / "apps" / "core"))
        for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
            del sys.modules[name]
        create_arch = importlib.import_module("app.arch").create_arch

        for bad in ("", " ", "1Tiny", "Tiny Model", "Tiny;DROP", "T" * 65, "티니"):
            with self.assertRaises(ValueError, msg=f"{bad!r} 가 통과했다"):
                create_arch(None, arch=bad, max_params=100)  # type: ignore[arg-type]

    @unittest.skipUnless(_HAS_PSYCOPG, "psycopg 없음 — 의존성 있는 환경에서만 돈다")
    def test_max_params_must_be_positive(self) -> None:
        sys.path.insert(0, str(ROOT / "apps" / "core"))
        for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
            del sys.modules[name]
        create_arch = importlib.import_module("app.arch").create_arch

        for bad in (0, -1):
            with self.assertRaises(ValueError):
                create_arch(None, arch="TinyOK", max_params=bad)  # type: ignore[arg-type]

    def test_name_pattern_shape(self) -> None:
        """psycopg 없이도 정규식 자체는 본다 — 패턴이 느슨해지는 것을 잡는다."""
        src = ARCH.read_text(encoding="utf-8")
        m = re.search(r'ARCH_NAME = re\.compile\(r"([^"]+)"\)', src)
        self.assertIsNotNone(m, "ARCH_NAME 패턴을 못 찾았다")
        assert m is not None
        pat = re.compile(m.group(1))
        self.assertTrue(pat.match("TinyEuroSAT"))
        self.assertTrue(pat.match("tiny-text.cnn_2"))
        for bad in ("", "1Tiny", "Tiny Model", "Tiny;DROP", "T" * 65):
            self.assertFalse(pat.match(bad), f"{bad!r} 가 통과한다")


if __name__ == "__main__":
    unittest.main()
