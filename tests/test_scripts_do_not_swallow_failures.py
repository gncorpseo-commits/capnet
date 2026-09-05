r"""`scripts/*.sh` 가 **실패를 조용히 삼키는 자리** (큐 #55 · `#205` 교훈).

## 왜 있는가

`#205` 가 남긴 교훈은 「**응답 없음(`000`)을 통과로 세지 마라**」였다. 같은 질문을
셸 쪽 전체에 물었다 — `|| true` · `|| :` 는 **직전 명령의 실패를 지운다.**

## 실측 (2026-09-05)

| 무엇 | 수 |
|---|---|
| `scripts/**/*.sh` 의 `\|\| true` · `\|\| :` | **18** |
| 그중 **실제 결함** | **1** — `generate_sbom.sh` |
| 근거가 서는 자리 | **17** (아래 표) |
| `%{http_code}` 를 받는 자리 | **10** |
| 그중 `000` 이 새는 곳 | **0** — 전부 **허용 목록 비교**(`== "200" \|\| == "409"`) |

### 결함 — SBOM 이 의존성 없이 조용히 만들어졌다

```bash
grep -v '^\s*#' "$root/apps/core/requirements.txt" || true   # ← 파일이 없어도 넘어간다
```

`grep` 은 파일이 없으면 **2** 로 죽는다. `|| true` 가 그걸 지웠다. 실측:

```text
$ bash -c 'set -euo pipefail; { grep -v "^#" /nonexistent/requirements.txt || true; }; echo rc=$?'
grep: /nonexistent/requirements.txt: No such file or directory
rc=0                                       ← 그리고 SBOM 은 core 의존성 없이 만들어진다
```

`capreq` 쪽은 `[ -n "$capreq_reqs" ] || exit 1` 로 막혀 있었는데 **`requirements.txt`
둘만 안 막혀 있었다.** 대회 2차 라이선스 검증에 내는 산출물이라, **빠진 채 초록**인 것이
가장 나쁘다.

고친 방법 둘:

1. 파일 존재를 **먼저** 본다 (`pip install` 전이라 빨리 죽는다)
2. `|| true` → `|| [ "$?" -eq 1 ]` — grep 의 **1**(고른 줄 없음)만 봐주고 **2**(읽기 실패)는 죽는다

### 나머지 열일곱 — 근거가 선다

`shift`(인자 없음) · 뒷정리(`down -v`·`kill`·`tail`) · `grep -c .`(0건) ·
데모의 `id` 추출(바로 뒤 `ccurl -sf` 가 다시 확인한다). 아래 `ALLOWED_SWALLOW` 가
**파일별 개수**로 못박는다 — 늘리려면 근거와 함께 고쳐야 한다.

## 무엇을 안 보나

- `2>/dev/null` 자체. 오류 **메시지**를 숨기는 것과 **종료 코드**를 지우는 것은 다르다
- 실행 결과. 여기는 소스만 본다 (`generate_sbom.sh` 의 가드는 아래에서 **실제로 돌려 본다**)
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SBOM = SCRIPTS / "generate_sbom.sh"

SWALLOW = re.compile(r"\|\|\s*(?:true|:)(?:\s|$|\))")

# 실패를 지워도 되는 자리와 **개수**. 늘리려면 근거와 함께 이 표를 고친다 (큐 #55).
ALLOWED_SWALLOW = {
    "call.sh": (1, "`shift` — 인자가 없을 때 정상"),
    "migrate.sh": (1, "같음"),
    "capreq_demo.sh": (2, "뒷정리 — 이미 죽은 프로세스 `kill` · 로그 `tail`"),
    "clean_room.sh": (2, "뒷정리 — 없는 스택 `down -v`"),
    "regate.sh": (1, "`grep -c .` — 0건이 정상이고 그 수를 쓴다"),
    "embed_demo.sh": (1, "id 추출 — 비면 바로 뒤 `ccurl -sf` 가 다시 확인한다"),
    "image_embed_demo.sh": (1, "같음"),
    "ner_demo.sh": (1, "같음"),
    "pii_demo.sh": (1, "같음"),
    "series_demo.sh": (1, "같음"),
    "table_demo.sh": (1, "같음"),
    "text_demo.sh": (1, "같음"),
    "text_extract_demo.sh": (1, "같음"),
    "text_rank_demo.sh": (1, "같음"),
}


def _swallows() -> dict[str, int]:
    out: dict[str, int] = {}
    for path in sorted(list(SCRIPTS.glob("*.sh")) + list((SCRIPTS / "lib").glob("*.sh"))):
        n = sum(1 for line in path.read_text(encoding="utf-8").splitlines()
                if not line.strip().startswith("#") and SWALLOW.search(line))
        if n:
            out[path.name] = n
    return out


class TestNoNewSilentSwallowing(unittest.TestCase):
    def test_every_swallow_is_accounted_for(self) -> None:
        """새 `|| true` 는 표를 거친다 — `#205` 가 준 교훈이 여기 있다."""
        got = _swallows()
        self.assertTrue(got, "`|| true` 를 하나도 못 찾았다 — 탐지기가 죽었다")
        new = sorted(f"{name}({n})" for name, n in got.items() if name not in ALLOWED_SWALLOW)
        self.assertEqual([], new, f"근거 없는 실패 삼킴: {new}")

    def test_counts_did_not_grow(self) -> None:
        got = _swallows()
        grown = sorted(f"{name}: {ALLOWED_SWALLOW[name][0]} → {n}"
                       for name, n in got.items()
                       if name in ALLOWED_SWALLOW and n > ALLOWED_SWALLOW[name][0])
        self.assertEqual([], grown, f"삼키는 자리가 늘었다: {grown}")

    def test_the_table_has_no_ghosts(self) -> None:
        got = _swallows()
        ghosts = sorted(n for n in ALLOWED_SWALLOW if n not in got)
        self.assertEqual([], ghosts, f"사라진 자리가 표에 남아 있다: {ghosts}")

    def test_the_sbom_generator_is_not_in_the_table(self) -> None:
        """고친 자리가 표로 되돌아가면 결함이 **허가**가 된다."""
        self.assertNotIn("generate_sbom.sh", ALLOWED_SWALLOW)
        self.assertNotIn("generate_sbom.sh", _swallows())


class TestSbomRefusesToRunWithoutItsInputs(unittest.TestCase):
    """**실제로 돌려 본다.** 정적 검사만으로는 가드가 도는지 모른다."""

    def _stub_tree(self, drop: str | None) -> Path:
        tmp = Path(tempfile.mkdtemp())
        (tmp / "scripts").mkdir()
        shutil.copy(SBOM, tmp / "scripts" / SBOM.name)
        for rel, text in (
            ("apps/core/requirements.txt", "fastapi==0.116.1\n"),
            ("apps/node/requirements.txt", "uvicorn==0.30.0\n"),
        ):
            if rel == drop:
                continue
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return tmp

    def test_missing_core_requirements_fails_loudly(self) -> None:
        tmp = self._stub_tree("apps/core/requirements.txt")
        try:
            proc = subprocess.run(["bash", str(tmp / "scripts" / SBOM.name)],
                                  capture_output=True, text=True, timeout=120)
            self.assertNotEqual(0, proc.returncode, "의존성 파일이 없는데 통과했다")
            self.assertIn("의존성 파일을 못 읽는다", proc.stderr)
            self.assertIn("apps/core/requirements.txt", proc.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_node_requirements_fails_loudly(self) -> None:
        tmp = self._stub_tree("apps/node/requirements.txt")
        try:
            proc = subprocess.run(["bash", str(tmp / "scripts" / SBOM.name)],
                                  capture_output=True, text=True, timeout=120)
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("apps/node/requirements.txt", proc.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_guard_runs_before_anything_slow(self) -> None:
        """`pip install` 뒤에 두면 없는 파일 하나 때문에 몇십 초를 기다린다."""
        body = SBOM.read_text(encoding="utf-8")
        self.assertLess(body.index("의존성 파일을 못 읽는다"),
                        body.index("pip install"),
                        "가드가 pip install 뒤에 있다")

    def test_grep_only_forgives_no_match(self) -> None:
        """`|| true` 로 되돌아가면 파일이 없어도 조용히 넘어간다."""
        body = SBOM.read_text(encoding="utf-8")
        self.assertIn('|| [ "$?" -eq 1 ]', body)
        self.assertNotIn("requirements.txt\" || true", body)


class TestHttpCodesAreNeverAllowedByDefault(unittest.TestCase):
    """`000` 을 통과로 세지 않는다 — 비교가 **허용 목록**이어야 한다 (`#205`)."""

    def test_every_http_code_check_is_an_allowlist(self) -> None:
        bad = []
        for path in sorted(SCRIPTS.glob("*.sh")):
            lines = path.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if "%{http_code}" not in line:
                    continue
                # 함수 **정의**(`code(){ … }`)는 판정 자리가 아니다 — 부르는 쪽이 가른다.
                if re.match(r"^\s*[a-z_]+\s*\(\)", line):
                    body = "\n".join(lines)
                    if "probe_verdict" in body or re.search(r'(?:==|=)\s*"?\d{3}"?', body):
                        continue
                    bad.append(f"{path.name}:{i + 1} (정의만 있고 어디서도 안 가른다)")
                    continue
                window = "\n".join(lines[i:i + 10])
                if re.search(r'(?:==|=)\s*"?\d{3}"?', window) or "probe_verdict" in window:
                    continue
                bad.append(f"{path.name}:{i + 1}")
        self.assertEqual([], bad, f"http_code 를 받고 값을 안 가른다: {bad}")

    def test_enough_http_code_sites_are_seen(self) -> None:
        n = sum(1 for p in SCRIPTS.glob("*.sh")
                for line in p.read_text(encoding="utf-8").splitlines()
                if "%{http_code}" in line)
        self.assertGreaterEqual(n, 8, f"{n}곳만 봤다")


if __name__ == "__main__":
    unittest.main()
