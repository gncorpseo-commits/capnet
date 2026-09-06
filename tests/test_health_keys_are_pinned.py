r"""`/health` 두 곳이 **어떤 칸을 내보내는지** 못박는다 (배치 C #111 · `#111` 계열 재전수).

## 왜 있는가

`test_node_routes_are_pinned` 는 증서 **값**이 안 나가는지를 본다. 칸이 하나 늘어나면 — `core_url`,
`credential_file`, `os.environ` 덤프 — 그 검사는 조용하다. `/health` 는 무인증이라 칸 하나가 곧 공개다.
실측(2026-09-06):

| 어디 | 칸 |
|---|---|
| Node `GET /health` | `ok` · `node_id` · `credential_present` · `weights_path` · `weights_sha256` · `weights[]`(`path`·`sha256`·`placeholder`·`arch`) |
| Core `GET /health` | `ok` · `postgres` · `capability`(id·code·version) |
| 환경변수 이름·`os.environ`·`CORE_URL`·`*_FILE` 이 반환식에 | **0** |

`weights_path`·`path` 는 컨테이너 안 경로다 — 가중치 sha 와 함께 증적(D15)의 일부라 남긴다. 새 칸은 이 표에
이유와 함께 넣어야 한다.

## 재현

```bash
python3 -m unittest tests.test_health_keys_are_pinned
```
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE_MAIN = ROOT / "apps" / "node" / "app" / "main.py"
CORE_MAIN = ROOT / "apps" / "core" / "app" / "main.py"

NODE_HEALTH_KEYS = {"ok", "node_id", "credential_present", "weights_path", "weights_sha256", "weights"}
NODE_WEIGHT_ENTRY_KEYS = {"path", "sha256", "placeholder", "arch"}
CORE_HEALTH_KEYS = {"ok", "postgres", "capability"}


def _health(path: Path) -> ast.FunctionDef:
    for fn in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(fn, ast.FunctionDef) and any(
            isinstance(d, ast.Call) and d.args and getattr(d.args[0], "value", None) == "/health" for d in fn.decorator_list
        ):
            return fn
    raise AssertionError(f"{path.name} 에 /health 가 없다")


def _returned_keys(fn: ast.FunctionDef) -> set[str]:
    for n in ast.walk(fn):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
            return {k.value for k in n.value.keys if isinstance(k, ast.Constant)}
    raise AssertionError("dict 를 돌려주지 않는다")


class TestNodeHealth(unittest.TestCase):
    def test_top_level_keys(self) -> None:
        self.assertEqual(NODE_HEALTH_KEYS, _returned_keys(_health(NODE_MAIN)))

    def test_weight_entry_keys(self) -> None:
        fn = _health(NODE_MAIN)
        keys = set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "sha256" for k in n.keys):
                keys |= {k.value for k in n.keys if isinstance(k, ast.Constant)}
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Subscript):
                t = n.targets[0]
                if isinstance(t.value, ast.Name) and t.value.id == "entry" and isinstance(t.slice, ast.Constant):
                    keys.add(t.slice.value)
        self.assertEqual(NODE_WEIGHT_ENTRY_KEYS, keys)

    def test_no_environment_or_url_or_file_path_variable_is_returned(self) -> None:
        fn = _health(NODE_MAIN)
        bad = []
        for n in ast.walk(fn):
            if isinstance(n, ast.Name) and (n.id in ("CORE_URL",) or n.id.endswith("_FILE") or n.id == "environ"):
                bad.append(n.id)
            if isinstance(n, ast.Attribute) and n.attr == "environ":
                bad.append("os.environ")
        self.assertEqual([], bad, f"health 가 내부 설정을 내보낸다: {bad}")


class TestCoreHealth(unittest.TestCase):
    def test_keys(self) -> None:
        self.assertEqual(CORE_HEALTH_KEYS, _returned_keys(_health(CORE_MAIN)))

    def test_capability_row_is_three_columns(self) -> None:
        src = ast.get_source_segment(CORE_MAIN.read_text(encoding="utf-8"), _health(CORE_MAIN)) or ""
        self.assertIn("SELECT id, code, version FROM capability", src)


if __name__ == "__main__":
    unittest.main()
