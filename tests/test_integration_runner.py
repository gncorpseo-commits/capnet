"""통합 검사 러너가 **아무것도 조용히 빠뜨리지 않는가**.

## 왜 있는가

`scripts/run_integration.sh` 는 `tests/integration/check_*.py` 를 **glob 으로** 집어간다:

    < <(find "$root/tests/integration" -name 'check_*.py' | sort)

`docs/guide/testing.md` §4.5 가 그것을 이렇게 약속한다 —
「이름 순으로 **전부** 집어간다. 파일을 놓기만 하면 CI 가 돈다 (**등록부가 따로 없다**)」.

**약속의 대가는 이름이다.** 패턴을 벗어난 이름으로 파일을 놓으면 **아무 말 없이 안 돈다.**
검사를 짜 놓고 돌지 않는 것은 검사가 없는 것보다 나쁘다 — 있다고 믿게 되기 때문이다.

이번 회차에 고친 다섯 결함이 전부 같은 모양이었다: **못 한 것이 안 한 것처럼 보인다.**
여기는 아직 그런 일이 없다(15개 전부 패턴에 맞는다). **나기 전에 막는다.**

## 무엇을 보나

1. `tests/integration/` 의 파이썬 파일이 **전부** 러너의 패턴에 맞는가
2. 러너가 **glob 을 쓰는가** — 하드코딩 목록으로 바뀌면 §4.5 가 거짓이 된다

## 무엇을 안 보나

**개수를 못박지 않는다.** 통합 검사는 능력·강제 경로를 더할 때마다 는다 —
`test_doc_counts` 가 같은 이유로 그 개수를 문서에 못박지 못하게 한다.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "tests" / "integration"
RUNNER = ROOT / "scripts" / "run_integration.sh"

# 러너가 쓰는 패턴. 여기와 스크립트가 갈라지면 아래 검사가 걸린다.
PATTERN = "check_*.py"


class TestNothingIsSilentlySkipped(unittest.TestCase):
    def test_every_python_file_matches_the_runner_pattern(self) -> None:
        """패턴 밖 이름은 **아무 말 없이 안 돈다.**"""
        picked = {p.name for p in INTEGRATION.glob(PATTERN)}
        present = {
            p.name
            for p in INTEGRATION.glob("*.py")
            if p.name != "__init__.py"
        }
        skipped = sorted(present - picked)
        self.assertEqual(
            skipped,
            [],
            "러너가 안 집어가는 파일이 있다 — 이름을 `check_…py` 로 바꾸거나, "
            f"의도라면 여기 근거와 함께 적는다: {skipped}",
        )

    def test_runner_uses_a_glob_not_a_list(self) -> None:
        """하드코딩 목록으로 바뀌면 `testing.md` §4.5 의 「등록부가 없다」가 거짓이 된다."""
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("check_*.py", text, "러너가 패턴으로 안 집는다")
        self.assertIn("find", text, "glob 대신 목록을 쓰는 것으로 보인다")

    def test_probe_actually_finds_things(self) -> None:
        """0개를 비교하며 통과하는 상태를 막는다. **개수는 못박지 않는다.**"""
        self.assertGreater(len(list(INTEGRATION.glob(PATTERN))), 5)


class TestZeroChecksIsNotPass(unittest.TestCase):
    """**하나도 못 찾으면 실패해야 한다.**

    위 검사들은 「패턴을 벗어난 파일 하나」를 막는다. 그런데 **전부가 안 잡히는 경우**는
    따로였다 — 루프가 안 돌고 끝에서 「통과 0 · 실패 0」이 찍힌 뒤 `exit 0` 이었다.

    CI 의 `integration` 잡이 이 스크립트를 그대로 부른다. glob 이 한 번 빗나가면
    **통합 검사 0개로 초록**이 된다. `find` 는 디렉터리가 없어도 프로세스 치환 안이라
    `set -e` 에 안 걸리므로, 스크립트 스스로 세는 수밖에 없다.

    postgres 없이 돈다 — 가드가 `psql` 보다 먼저다. 그것 자체가 이 검사의 요구사항이다.
    """

    def _run_in_fake_root(self, files: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "scripts").mkdir()
            (root / "tests" / "integration").mkdir(parents=True)
            for name in files:
                (root / "tests" / "integration" / name).write_text("", encoding="utf-8")
            dst = root / "scripts" / RUNNER.name
            dst.write_text(RUNNER.read_text(encoding="utf-8"), encoding="utf-8")
            dst.chmod(0o755)
            return subprocess.run(
                ["bash", str(dst)],
                capture_output=True,
                text=True,
                timeout=60,
                # psql 까지 가면 안 된다. 가더라도 진짜 DB 를 건드리지 않게 막아 둔다.
                env={**os.environ, "PGHOST": "127.0.0.1", "PGPORT": "1"},
            )

    def test_empty_integration_dir_fails(self) -> None:
        r = self._run_in_fake_root([])
        self.assertNotEqual(r.returncode, 0, f"0건인데 통과했다:\n{r.stdout}\n{r.returncode}")
        self.assertIn("하나도 못 찾았다", r.stderr + r.stdout)

    def test_only_off_pattern_files_fails(self) -> None:
        """`check_` 로 시작하지 않는 이름만 있으면 = 0건이다."""
        r = self._run_in_fake_root(["revocation_check.py", "helpers.py"])
        self.assertNotEqual(r.returncode, 0, f"패턴 밖 파일만 있는데 통과했다:\n{r.stdout}")
        self.assertIn("하나도 못 찾았다", r.stderr + r.stdout)

    def test_guard_runs_before_psql(self) -> None:
        """가드가 DB 준비보다 뒤면 「postgres 가 없어서」로 실패가 뭉개진다."""
        r = self._run_in_fake_root([])
        blob = r.stderr + r.stdout
        self.assertNotIn("psql", blob, f"psql 까지 갔다 — 가드가 늦다:\n{blob}")


if __name__ == "__main__":
    unittest.main()
