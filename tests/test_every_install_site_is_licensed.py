r"""**설치가 일어나는 자리 전부**가 THIRD-PARTY-LICENSES 에 있는가 (배치 B #85 · `#11` 잔여).

## 왜 있는가

`check_submission.check_deps_declared` 는 `requirements.txt` 둘과 `capreq/pyproject.toml` 을 본다.
그런데 패키지가 깔리는 자리는 그 셋만이 아니다 — `apps/node/Dockerfile` 은 `torch`·`torchvision` 을
**직접** `pip install` 하고, `ci.yml` 은 두 잡에서 일곱 개를 리터럴로 깐다. 그 자리에 새 이름이
들어와도 아무도 표를 확인하지 않았다. 베이스 이미지도 같다 — 표에 `postgres:16` 은 있고
`python:3.11-slim` 은 **없었다** (같은 종류의 것인데 하나만 적혀 있었다).

## 실측 (2026-09-06)

| 자리 | 이름 수 | 표 누락 |
|---|---|---|
| `apps/core/requirements.txt` · `apps/node/requirements.txt` | 5 · 5 | 0 |
| `capreq/pyproject.toml` (deps + extras) | 4 | 0 |
| `apps/node/Dockerfile` `pip install` 리터럴 | 2 | 0 |
| `ci.yml` `pip install` 리터럴 | 7 (고유 6) | 0 |
| 베이스 이미지 `FROM`·`image:` | 2 | **1 → 0** (`python:3.11-slim` 한 줄 추가) |
| 같은 이름의 `==` 핀이 자리마다 다른 것 | — | 0 |

## 재현

```bash
python3 -m unittest tests.test_every_install_site_is_licensed
```
"""

from __future__ import annotations

import re
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

TABLE = ROOT / "THIRD-PARTY-LICENSES.md"
REQUIREMENTS = (ROOT / "apps" / "core" / "requirements.txt", ROOT / "apps" / "node" / "requirements.txt")
PYPROJECT = ROOT / "capreq" / "pyproject.toml"
DOCKERFILES = sorted(ROOT.glob("apps/*/Dockerfile"))
CI = ROOT / ".github" / "workflows" / "ci.yml"
COMPOSES = (ROOT / "compose.yaml", ROOT / "compose.prod.yaml")

# 표는 사람이 읽는 이름을 쓴다 — 패키지 이름이 그대로 안 나오는 것만 여기서 잇는다.
DISPLAY = {"pillow": "pillow", "uvicorn": "uvicorn", "psycopg": "psycopg"}


def _name(spec: str) -> str:
    return re.split(r"[\[=<>!~;\s]", spec.strip().strip('"\''))[0].lower()


def _version(spec: str) -> str | None:
    m = re.search(r"==([\w.+]+)", spec)
    return m.group(1) if m else None


def _pip_literals(text: str) -> list[str]:
    """`pip install a "b==1" \\` 줄이 이어지는 것까지 — `-r`·`--index-url` 같은 옵션은 뺀다."""
    out: list[str] = []
    joined = re.sub(r"\\\n", " ", text)
    # `\s+` 는 줄바꿈을 넘어 다음 줄까지 삼킨다 — 같은 줄 안에서만 잇는다.
    for m in re.finditer(r"pip install((?:[ \t]+(?:\"[^\"]+\"|'[^']+'|[^\s;&|]+))+)", joined):
        toks = re.findall(r"\"[^\"]+\"|'[^']+'|\S+", m.group(1))
        skip_next = False
        for t in toks:
            if skip_next:
                skip_next = False
                continue
            if t in ("-r", "--index-url", "--extra-index-url"):
                skip_next = True
                continue
            if t.startswith("-"):
                continue
            out.append(t.strip("\"'"))
    return out


def sites() -> dict[str, list[str]]:
    got: dict[str, list[str]] = {}
    for p in REQUIREMENTS:
        got[str(p.relative_to(ROOT))] = [l for l in p.read_text(encoding="utf-8").splitlines()
                                          if l.strip() and not l.startswith("#")]
    with PYPROJECT.open("rb") as fh:
        proj = tomllib.load(fh)["project"]
    specs = list(proj.get("dependencies", []))
    for extra in proj.get("optional-dependencies", {}).values():
        specs.extend(extra)
    got["capreq/pyproject.toml"] = specs
    for df in DOCKERFILES:
        got[str(df.relative_to(ROOT))] = _pip_literals(hash_comment_free(df))
    got[".github/workflows/ci.yml"] = _pip_literals(hash_comment_free(CI))
    return got


def base_images() -> list[str]:
    out = []
    for df in DOCKERFILES:
        out += re.findall(r"^FROM\s+(\S+)", hash_comment_free(df), re.M)
    for c in COMPOSES:
        out += re.findall(r"^\s*image:\s*(\S+)", hash_comment_free(c), re.M)
    return sorted(set(out))


class TestEveryInstallSiteIsInTheTable(unittest.TestCase):
    def test_no_installed_name_is_missing(self) -> None:
        table = TABLE.read_text(encoding="utf-8").lower()
        got = sites()
        self.assertGreaterEqual(len(got), 5, sorted(got))
        names = {_name(s) for specs in got.values() for s in specs}
        self.assertGreaterEqual(len(names), 8, sorted(names))
        # Dockerfile 의 `${TORCH_VERSION}` 은 이름이 아니다 — `torch==${…}` 에서 이름만 남는다.
        missing = sorted(n for n in names if n and DISPLAY.get(n, n) not in table)
        self.assertEqual([], missing, f"THIRD-PARTY-LICENSES 에 없는 설치 이름: {missing}")

    def test_dockerfile_and_ci_are_actually_read(self) -> None:
        got = sites()
        self.assertIn("torch", [_name(s) for s in got["apps/node/Dockerfile"]])
        self.assertGreaterEqual(len(got[".github/workflows/ci.yml"]), 6, got[".github/workflows/ci.yml"])

    def test_pins_agree_across_sites(self) -> None:
        pins: dict[str, dict[str, str]] = {}
        for site, specs in sites().items():
            for s in specs:
                v = _version(s)
                if v and "${" not in v:
                    pins.setdefault(_name(s), {})[site] = v
        self.assertTrue(pins, "== 핀을 하나도 못 찾았다")
        drift = [f"{n}: {vs}" for n, vs in sorted(pins.items()) if len(set(vs.values())) > 1]
        self.assertEqual([], drift, f"같은 이름인데 자리마다 핀이 다르다: {drift}")

    def test_base_images_are_in_the_table(self) -> None:
        table = TABLE.read_text(encoding="utf-8")
        imgs = base_images()
        self.assertGreaterEqual(len(imgs), 2, imgs)
        missing = [i for i in imgs if f"`{i}`" not in table]
        self.assertEqual([], missing, f"표에 없는 베이스 이미지: {missing}")


class TestProbeActuallyParses(unittest.TestCase):
    def test_pip_literal_parser(self) -> None:
        text = 'RUN pip install --no-cache-dir -r /app/req.txt \\\n && pip install "a==1.0" b \\\n   --index-url https://x ; fi\n'
        self.assertEqual(["a==1.0", "b"], _pip_literals(text))

    def test_todays_shape(self) -> None:
        got = sites()
        self.assertEqual({"apps/core/requirements.txt": 5, "apps/node/requirements.txt": 5, "capreq/pyproject.toml": 4,
                          "apps/core/Dockerfile": 0, "apps/node/Dockerfile": 2, ".github/workflows/ci.yml": 7},
                         {k: len(v) for k, v in got.items()})
        self.assertEqual(["postgres:16", "python:3.11-slim"], base_images())


if __name__ == "__main__":
    unittest.main()
