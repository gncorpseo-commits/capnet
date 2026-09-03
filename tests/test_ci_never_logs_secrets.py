r"""CI 워크플로가 **시크릿을 로그로 흘리지 않는가** (큐 #31).

## 왜 있는가

[#196](https://github.com/gncorpseo-commits/capnet/pull/196)이 「시크릿이 런타임 출력으로
나가는가」를 전수해 못박았다. 그 검사가 보는 범위는 **`*.py` 와 `scripts/*.sh`** 다:

```text
for p in sorted(tree.rglob("*.py")): ...
for p in sorted((ROOT / "scripts").glob("*.sh")): ...
```

**`.github/workflows/*.yml` 은 범위 밖이었다.**

그런데 Actions 로그는 **가장 나쁜 자리**다 — 공개 저장소에서 누구나 읽고,
지워도 캐시·포크·알림에 남는다. `echo "${{ secrets.X }}"` 한 줄이면 끝난다.

## 실측 (2026-09-03) — **오늘 새는 곳은 없다**

| 무엇 | 수 |
|---|---|
| 워크플로 파일 | **1** (`ci.yml`) |
| `${{ secrets.* }}` 사용 | **0** |
| 시크릿 낱말을 출력하는 `echo`/`printf` | **0** |
| `set -x` (명령 전체를 로그에 흘린다) | **0** |

`POSTGRES_PASSWORD: capnet` 은 **일회용 서비스 컨테이너**의 값이고 `echo` 되지 않는다.

## 무엇을 고정하나

1. 출력 명령(`echo`·`printf`·`cat`)의 인자에 **시크릿 낱말**이 없다
2. `${{ secrets.* }}` 을 **출력하지 않는다**
3. `set -x` 가 없다 — 켜면 그 블록의 **모든 명령**이 값과 함께 로그로 간다

## 무엇을 고정하지 **않나**

- `${{ secrets.* }}` 사용 **자체**. 배포·토큰이 필요해질 수 있다. 막는 것은 **출력**이다
- 워크플로 안의 리터럴 값. 일회용 테스트 DB 비밀번호가 그렇고, 그건
  `check_submission.check_secrets` 의 몫이다 — **겹쳐 두면 어느 검사가 지키는지 흐려진다**
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# 값이 시크릿인 이름들. `#196` 의 낱말 목록과 같은 계열이다.
#
# **낱말 경계를 붙이지 않는다.** 처음에는 `\b(?:…|api[_-]?key)\b` 였는데
# 이 저장소가 실제로 쓰는 `CAPNET_API_KEY` 를 **못 잡았다** — `_` 가 단어 문자라
# `_API` 앞에 경계가 없다. #196 이 「낱말 목록에 `cred` 가 없어 `$cred` 를 못 잡았다」로
# 겪은 것과 같은 함정이다. 아래 `test_detector_discriminates` 가 그걸 잡았다.
SECRET_WORD = re.compile(
    r"(?i)(?:secret|password|passwd|token|credential|cred\b|api[_-]?key|apikey|private[_-]?key)"
)
# 값이 아니라 **유무·접두**를 말하는 이름은 시크릿이 아니다 (#196 이 겪은 오탐).
NOT_SECRET = re.compile(r"(?i)(key_prefix|credential_present|secret_file|_path\b|_dir\b)")

OUTPUT = re.compile(r"\b(?:echo|printf|cat)\b([^\n|>]*)")
EXPRESSION = re.compile(r"\$\{\{\s*secrets\.[A-Za-z0-9_]+\s*\}\}")


def _workflows() -> list[Path]:
    if not WORKFLOWS.is_dir():
        return []
    return sorted(p for p in WORKFLOWS.iterdir() if p.suffix in (".yml", ".yaml"))


def _lines(path: Path) -> list[tuple[int, str]]:
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        out.append((i, line))
    return out


class TestNoSecretReachesTheLog(unittest.TestCase):
    def test_output_commands_do_not_name_a_secret(self) -> None:
        """**`echo` 뒤쪽만** 본다 — 앞쪽 조건절까지 보면 마스킹한 출력을 오탐한다 (#196 교훈)."""
        bad: list[str] = []
        for path in _workflows():
            for lineno, line in _lines(path):
                for m in OUTPUT.finditer(line):
                    arg = m.group(1)
                    if SECRET_WORD.search(arg) and not NOT_SECRET.search(arg):
                        bad.append(f"{path.name}:{lineno} {line.strip()[:80]}")
        self.assertEqual([], bad, "CI 가 시크릿을 로그로 찍는다: " + "; ".join(bad))

    def test_secrets_expression_is_never_printed(self) -> None:
        bad: list[str] = []
        for path in _workflows():
            for lineno, line in _lines(path):
                if EXPRESSION.search(line) and OUTPUT.search(line):
                    bad.append(f"{path.name}:{lineno}")
        self.assertEqual([], bad, f"`${{{{ secrets.* }}}}` 를 출력한다: {bad}")

    def test_no_shell_tracing(self) -> None:
        """`set -x` 는 **그 블록의 모든 명령**을 값과 함께 로그로 보낸다."""
        bad: list[str] = []
        for path in _workflows():
            for lineno, line in _lines(path):
                if re.search(r"\bset\s+-[a-z]*x", line):
                    bad.append(f"{path.name}:{lineno} {line.strip()[:60]}")
        self.assertEqual([], bad, f"셸 추적이 켜져 있다: {bad}")


class TestProbeActuallyScans(unittest.TestCase):
    """범위가 비면 위 검사 **전부**가 공허하게 통과한다."""

    def test_workflows_exist(self) -> None:
        self.assertTrue(_workflows(), ".github/workflows 를 못 찾았다")

    def test_lines_are_read(self) -> None:
        total = sum(len(_lines(p)) for p in _workflows())
        self.assertGreater(total, 50, f"워크플로에서 {total}줄밖에 못 읽었다")

    def test_detector_discriminates(self) -> None:
        """낱말 탐지가 **아무것도 안 잡거나 전부 잡으면** 위 검사가 헛돈다."""
        self.assertTrue(SECRET_WORD.search('echo "$CAPNET_API_KEY"'))
        self.assertTrue(SECRET_WORD.search("echo ${{ secrets.FOO }} token"))
        self.assertFalse(SECRET_WORD.search('echo "적용할 것 없음"'))
        # 유무·접두를 말하는 이름은 시크릿이 아니다.
        self.assertTrue(NOT_SECRET.search('echo "$key_prefix"'))

    def test_output_pattern_finds_real_commands(self) -> None:
        self.assertTrue(OUTPUT.search('          echo "빈 DB 인데 up 이 성공했다"'))
        self.assertIsNone(OUTPUT.search("          python3 -m app.migrate up"))


if __name__ == "__main__":
    unittest.main()
