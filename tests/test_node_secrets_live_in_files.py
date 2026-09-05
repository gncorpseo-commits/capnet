r"""Node 증서가 **파일에만 사는가** (큐 #56 · `#196` 재전수).

## 왜 있는가

`compose.prod.yaml` 이 스스로 적는다:

> 증서는 **파일로** 넣는다: 환경변수로 주면 `docker inspect` 에 평문이 뜬다.

`#47`(`ccurl` 이 키를 argv 로 넘기던 자리)이 보여 준 것처럼, **주석이 금지한 것을 코드가
하고 있는지는 세어 봐야 안다.** 증서 쪽을 다시 훑었다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| 증서를 **파일로** 넣는 compose 서비스 | **3** (`node-m-team`·`node-s-team`·`node-s-public`) |
| 증서 **값**을 환경변수로 주는 서비스 | **0** ✅ |
| `node_onboard.sh` 가 화면에 찍는 것 | `key_prefix` 만 — 시크릿은 파일에만 ✅ |
| 시크릿 디렉터리·파일 권한 | `0700` · `0600` ✅ |
| `.gitignore` 가 막는 것 | `data/node-secrets/` · `*.credential` ✅ |
| Node 가 읽는 순서 | **파일 먼저**, 없으면 환경변수 ✅ |

`NODE_CREDENTIAL`(값) 환경변수는 **읽는 쪽에만** 남아 있다 — 아무 compose 도 그걸 채우지
않으므로 실제로는 죽은 길이다. **읽을 수 있다는 것과 그렇게 준다는 것은 다르다.**

## 무엇을 안 보나

**발급을 실제로 돌리지 않는다** — 살아 있는 Core 가 필요하다. 여기는 스크립트가 그 값을
어디에 두고 무엇을 찍는지, 그리고 compose 가 어떻게 주는지 **소스에서** 본다.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONBOARD = ROOT / "scripts" / "node_onboard.sh"
BIND = ROOT / "scripts" / "node_bind.sh"
NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"
GITIGNORE = ROOT / ".gitignore"
COMPOSES = (ROOT / "compose.yaml", ROOT / "compose.prod.yaml")

# `NODE_CREDENTIAL: <값>` 처럼 **값을 주는** 자리. `_FILE` 은 경로라 괜찮다.
ENV_VALUE = re.compile(r"^\s*NODE_CREDENTIAL\s*:", re.M)


class TestComposeGivesAPathNotAValue(unittest.TestCase):
    def test_no_compose_sets_the_credential_value(self) -> None:
        """**여기가 핵심이다.** 값을 주면 `docker inspect` 에 평문이 뜬다."""
        bad = []
        for path in COMPOSES:
            if path.is_file() and ENV_VALUE.search(path.read_text(encoding="utf-8")):
                bad.append(path.name)
        self.assertEqual([], bad, f"compose 가 증서 값을 환경변수로 준다: {bad}")

    def test_prod_gives_the_file_path_to_every_node(self) -> None:
        body = (ROOT / "compose.prod.yaml").read_text(encoding="utf-8")
        self.assertEqual(3, body.count("NODE_CREDENTIAL_FILE:"),
                         "제품 오버레이가 Node 셋 전부에 증서 파일을 안 준다")

    def test_the_reason_stays_written(self) -> None:
        reason = "환경변수로 주면 docker inspect 에 평문이 뜬다"
        self.assertTrue(reason in (ROOT / "compose.prod.yaml").read_text(encoding="utf-8"),
                        f"compose.prod.yaml 에서 이유가 사라졌다: «{reason}»")


class TestOnboardKeepsTheSecretOffTheScreen(unittest.TestCase):
    def test_it_prints_only_the_prefix(self) -> None:
        body = ONBOARD.read_text(encoding="utf-8")
        self.assertIn('d["key_prefix"]', body, "prefix 대신 무엇을 찍는지 확인하라")
        self.assertIn("시크릿은 파일에만", body)

    def test_it_writes_the_secret_to_a_file(self) -> None:
        body = ONBOARD.read_text(encoding="utf-8")
        self.assertRegex(body, r'\["secret"\][^\n]*>\s*"\$secret_file"',
                         "시크릿을 파일로 안 쓴다")

    def test_permissions_are_tight(self) -> None:
        body = ONBOARD.read_text(encoding="utf-8")
        self.assertIn('chmod 700 "$outdir"', body, "시크릿 디렉터리가 0700 이 아니다")
        self.assertIn('chmod 600 "$secret_file"', body, "시크릿 파일이 0600 이 아니다")

    def test_the_snippet_hands_over_a_path(self) -> None:
        """안내 문구가 값을 붙여 넣게 하면 사람이 그대로 한다."""
        body = ONBOARD.read_text(encoding="utf-8")
        self.assertIn("NODE_CREDENTIAL_FILE=$secret_file", body)
        self.assertNotIn("NODE_CREDENTIAL=$cred", body)


class TestBindTouchesNoSecret(unittest.TestCase):
    def test_node_bind_has_no_credential_of_its_own(self) -> None:
        """`node_bind.sh` 는 게이트·바인딩만 한다 — 증서를 다루면 자리가 하나 는다."""
        body = BIND.read_text(encoding="utf-8")
        self.assertNotIn("secret", body.lower().replace("secrets_dir", ""))
        self.assertIn("scripts/lib/http.sh", body, "관리 키는 공통 래퍼로만 붙인다")


class TestNodeReadsTheFileFirst(unittest.TestCase):
    def test_file_beats_env(self) -> None:
        body = NODE_MAIN.read_text(encoding="utf-8")
        file_at = body.index("NODE_CREDENTIAL_FILE and os.path.isfile")
        env_at = body.index('os.environ.get("NODE_CREDENTIAL")')
        self.assertLess(file_at, env_at, "Node 가 환경변수를 먼저 본다")


class TestGitignoreBlocksThem(unittest.TestCase):
    def test_both_patterns_are_ignored(self) -> None:
        body = GITIGNORE.read_text(encoding="utf-8")
        for pattern in ("data/node-secrets/", "*.credential"):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, body)

    def test_no_credential_file_is_tracked(self) -> None:
        """무시해도 **이미 들어간 것**이 있으면 소용없다.

        **파일이 있는 것 자체는 정상이다** — 온보딩을 한 번 돌리면 생기고, 위 두 패턴이
        그것을 커밋에서 막는다. 여기서 보는 것은 「git 이 추적하는가」다.
        """
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(0, out.returncode, out.stderr)
        tracked = [f for f in out.stdout.split("\0")
                   if f.endswith(".credential") or f.startswith("data/node-secrets/")]
        self.assertEqual([], tracked, f"증서 파일이 git 에 들어가 있다: {tracked}")


if __name__ == "__main__":
    unittest.main()
