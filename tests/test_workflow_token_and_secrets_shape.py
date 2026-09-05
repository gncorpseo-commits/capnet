r"""워크플로가 **어떤 권한으로 무엇을 만지는가** — 시크릿 0 · 토큰 읽기 전용 (배치 B #95 · `#217` 옆).

## 왜 있는가

`test_ci_never_logs_secrets` 는 「찍히는가」를 본다. 여기는 **애초에 무엇이 있는가**다:
`secrets.*` 를 쓰는 자리, `pull_request_target`(포크 PR 에 쓰기 토큰을 주는 트리거), job 수준
`env` 에 든 값, `permissions:` 선언. 실측(2026-09-06):

| 무엇 | 값 |
|---|---|
| 워크플로 파일 | 1 (`ci.yml`) |
| `${{ secrets.* }}` · `GITHUB_TOKEN` 참조 | **0** — 이 CI 는 시크릿 없이 돈다 |
| `pull_request_target` · `schedule` | 없음 (`push` · `pull_request` · `workflow_dispatch`) |
| job `env` 의 값 | 일회용 서비스 컨테이너의 `capnet` 과 경로뿐 |
| `permissions:` 선언 | **없음** — 저장소 기본 `default_workflow_permissions` 가 `read` 라 실효 권한은 읽기 전용 (`gh api …/actions/permissions/workflow`, 2026-09-06) |

`permissions: contents: read` 를 **명시**하는 것은 `ci.yml` 이라 브리지에 올렸다 — 저장소 설정이 바뀌면
지금의 읽기 전용은 조용히 풀린다.

## 재현

```bash
python3 -m unittest tests.test_workflow_token_and_secrets_shape
gh api repos/gncorpseo-commits/capnet/actions/permissions/workflow   # default_workflow_permissions
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

WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))


class TestNoSecretIsEvenReferenced(unittest.TestCase):
    def test_zero_secret_or_token_references(self) -> None:
        self.assertEqual(1, len(WORKFLOWS), [p.name for p in WORKFLOWS])
        for p in WORKFLOWS:
            body = hash_comment_free(p)
            with self.subTest(file=p.name):
                self.assertNotRegex(body, r"secrets\.", f"{p.name} 이 시크릿을 참조한다 — 어디에 찍히는지부터 봐야 한다")
                self.assertNotIn("GITHUB_TOKEN", body)

    def test_no_fork_write_trigger(self) -> None:
        for p in WORKFLOWS:
            body = hash_comment_free(p)
            with self.subTest(file=p.name):
                self.assertNotIn("pull_request_target", body)
                triggers = set(re.findall(r"^  (\w+):", body[body.index("on:"):body.index("jobs:")], re.M))
                self.assertEqual({"push", "pull_request", "workflow_dispatch"}, triggers, triggers)

    def test_job_env_carries_only_throwaway_values(self) -> None:
        body = hash_comment_free(WORKFLOWS[0])
        values = re.findall(r"^\s{6}[A-Z_]+:\s*(.+)$", body, re.M)
        self.assertGreaterEqual(len(values), 3, values)
        for v in values:
            with self.subTest(value=v):
                self.assertRegex(v, r"capnet|\$\{\{ github\.workspace \}\}|^\d+$|^\"?[01]\"?$",
                                 f"env 값이 일회용·경로가 아니다: {v}")


class TestTokenScopeIsReadOnlyAndItIsWrittenDown(unittest.TestCase):
    def test_permissions_block_state_is_recorded(self) -> None:
        """선언이 생기면 이 표와 문서를 함께 고친다 — 없다는 사실도 기록이다."""
        body = hash_comment_free(WORKFLOWS[0])
        declared = re.search(r"^permissions:", body, re.M) is not None
        self.assertFalse(declared, "permissions 가 선언됐다 — 이 검사와 브리지 블록을 갱신하라")

    def test_bridge_carries_the_proposal(self) -> None:
        inbox = (ROOT / "docs" / "bridge" / "inbox-cursor.md").read_text(encoding="utf-8")
        found = re.search(r"permissions:\s*\n\s*contents: read", inbox) is not None
        self.assertTrue(found, "명시 선언 제안(permissions / contents: read)이 브리지에 없다")


if __name__ == "__main__":
    unittest.main()
