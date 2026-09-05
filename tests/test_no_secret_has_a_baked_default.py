r"""Dockerfile·compose 에 **시크릿 기본값이 구워져 있지 않은가** (배치 B #79 · `#249` 잔여).

## 왜 있는가

`ENV POSTGRES_PASSWORD=capnet` 한 줄이 이미지에 들어가면 그 이미지를 받은 모두가
비밀번호를 안다. compose 의 `${X:-값}` 도 같다 — `.env` 를 안 쓰면 그 값으로 뜬다.

## 실측 (2026-09-06)

| 어디 | 시크릿 이름의 ENV/ARG·기본값 | 값 |
|---|---|---|
| `apps/core/Dockerfile` · `apps/node/Dockerfile` | `ENV`·`ARG` 7줄 중 시크릿 이름 | **0** ✅ |
| `compose.prod.yaml` | 시크릿 키 2개(`POSTGRES_PASSWORD`·`DATABASE_URL`) 전부 `${X:?…}` | 기본값 **0** ✅ |
| `compose.yaml` (데모) | `POSTGRES_PASSWORD`·`DATABASE_URL` 에 `:-capnet` | **2** — 프로드 오버레이가 둘 다 `:?` 로 덮는다 |
| `.env.example` | 시크릿 키 값 | 전부 **빈칸** ✅ |

데모 compose 의 `capnet` 은 **닫힌 기본값**이다 — `compose.prod.yaml` 이 `-f` 두 번째로 얹혀
같은 키를 `:?` 로 다시 선언한다. 여기서 고정하는 것은 그 **둘의 짝**이다: 데모에 기본값이
있는 시크릿 키는 프로드에서 반드시 `:?` 여야 한다.

## 재현

```bash
python3 -m unittest tests.test_no_secret_has_a_baked_default
```
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

DOCKERFILES = sorted(ROOT.glob("apps/*/Dockerfile"))
DEMO = ROOT / "compose.yaml"
PROD = ROOT / "compose.prod.yaml"
ENV_EXAMPLE = ROOT / ".env.example"

# 값이 새면 안 되는 이름. `DATABASE_URL` 은 안에 비밀번호가 들어간다.
SECRET_NAME = re.compile(r"PASSWORD|SECRET|TOKEN|CREDENTIAL(?!_FILE)|API_KEY(?!_FILE)|_KEY$|DATABASE_URL")
ENV_LINE = re.compile(r"^\s*([A-Z][A-Z0-9_]*):\s*(.*?)\s*$", re.M)
DOCKER_KV = re.compile(r"^(?:ENV|ARG)\s+([A-Z][A-Z0-9_]*)=?(.*)$", re.M)


def _is_secret(name: str) -> bool:
    """`REQUIRE_API_KEY=1` 은 **토글**이지 키가 아니다."""
    return bool(SECRET_NAME.search(name)) and not name.startswith("REQUIRE_")


def _env_keys(path: Path) -> dict[str, str]:
    """compose 의 `environment:` 블록 안 `KEY: 값` — 마지막 선언이 이긴다."""
    out: dict[str, str] = {}
    for m in ENV_LINE.finditer(hash_comment_free(path)):
        out[m.group(1)] = m.group(2)
    return out


class TestDockerfilesBakeNoSecret(unittest.TestCase):
    def test_no_secret_named_env_or_arg(self) -> None:
        seen, bad = 0, []
        for df in DOCKERFILES:
            for m in DOCKER_KV.finditer(hash_comment_free(df)):
                seen += 1
                if _is_secret(m.group(1)):
                    bad.append(f"{df.relative_to(ROOT)}: {m.group(0).strip()}")
        self.assertGreaterEqual(seen, 5, f"ENV/ARG 를 {seen}줄만 봤다")
        self.assertEqual([], bad, f"이미지에 구워진 시크릿: {bad}")


class TestProdHasNoDefault(unittest.TestCase):
    def test_every_secret_key_demands_dotenv(self) -> None:
        """`${X:?…}` 만 허용 — `:-` 도, 리터럴도 안 된다."""
        keys = {k: v for k, v in _env_keys(PROD).items() if _is_secret(k)}
        self.assertGreaterEqual(len(keys), 2, f"프로드의 시크릿 키를 {sorted(keys)} 만 봤다")
        for key, value in sorted(keys.items()):
            with self.subTest(key=key):
                self.assertRegex(value, rf"^\$\{{{key}:\?", f"{key} 에 기본값이 있다: {value}")

    def test_demo_defaults_are_all_overridden(self) -> None:
        """데모에 `:-` 기본값이 있는 시크릿 키는 프로드가 반드시 `:?` 로 덮는다."""
        demo = {k: v for k, v in _env_keys(DEMO).items() if _is_secret(k) and ":-" in v}
        self.assertTrue(demo, "데모 compose 에서 기본값 있는 시크릿 키를 하나도 못 찾았다")
        prod = _env_keys(PROD)
        for key, value in sorted(demo.items()):
            with self.subTest(key=key):
                self.assertRegex(value, r":-[^}]*capnet", f"데모 기본값이 capnet 이 아니다: {value}")
                self.assertIn(key, prod, f"프로드가 {key} 를 다시 선언하지 않는다 — 데모 기본값이 산다")
                self.assertIn(":?", prod[key])

    def test_prod_is_layered_second(self) -> None:
        body = hash_comment_free(ROOT / "scripts" / "prod_room.sh")
        self.assertIn('-f "$root/compose.yaml" -f "$root/compose.prod.yaml"', body,
                      "프로드 오버레이가 데모 뒤에 얹히지 않는다")


class TestEnvExampleIsBlank(unittest.TestCase):
    def test_secret_keys_have_no_value(self) -> None:
        lines = [l for l in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
                 if l and not l.startswith("#")]
        self.assertGreaterEqual(len(lines), 8, lines)
        bad = []
        for line in lines:
            key, _, value = line.partition("=")
            if _is_secret(key) and value and "<" not in value:
                bad.append(line)
        self.assertEqual([], bad, f".env.example 에 실제 값이 있다: {bad}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_two_dockerfiles_and_two_composes(self) -> None:
        self.assertEqual(2, len(DOCKERFILES), DOCKERFILES)
        self.assertGreaterEqual(len(_env_keys(DEMO)), 10)
        self.assertGreaterEqual(len(_env_keys(PROD)), 6)

    def test_secret_name_matches_the_expected_shapes(self) -> None:
        for name in ("POSTGRES_PASSWORD", "DATABASE_URL", "CAPNET_API_KEY", "NODE_CREDENTIAL"):
            self.assertTrue(_is_secret(name), name)
        for name in ("CAPNET_API_KEY_FILE", "NODE_CREDENTIAL_FILE", "REQUIRE_API_KEY",
                     "REQUIRE_NODE_CREDENTIAL", "POSTGRES_USER"):
            self.assertFalse(_is_secret(name), name)


if __name__ == "__main__":
    unittest.main()
