r"""가중치를 읽는 **모든 자리**가 safetensors 인가 — `scripts/` 까지 (배치 C #104 · 절대규칙 5).

## 왜 있는가

`test_absolute_rules_are_enforced` 는 `apps`·`capreq/src` 에서 pickle 계열 호출이 **없음**을 본다.
여기서는 반대로 **있는 것**을 센다 — 가중치를 실제로 여는 호출 전부를 나열하고, 하나하나가
`safetensors` 인지 본다. 그러면 새 실행기가 `torch.load` 를 들고 와도 개수와 종류에서 걸린다.
`scripts/*.py` 는 기존 검사 범위 밖이라 여기서 같이 본다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| 가중치 로더 호출 (`load_file`·`safe_open`) | **14** — 전부 `safetensors` 에서 import |
| `torch.load`·`pickle.load`·`joblib.load`·`np.load(allow_pickle=True)`·`torch.hub` | **0** (`apps`·`scripts`·`capreq/src`) |
| `.pt`/`.pth` 경로 리터럴 | **0** |

## 재현

```bash
python3 -m unittest tests.test_every_weight_loader_is_safetensors
```
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREES = (ROOT / "apps", ROOT / "scripts", ROOT / "capreq" / "src")
LOADERS = {"load_file", "safe_open"}
FORBIDDEN = re.compile(r"torch\.load\(|pickle\.load|joblib\.load|torch\.hub|allow_pickle\s*=\s*True")


def _py() -> list[Path]:
    out = []
    for t in TREES:
        out.extend(p for p in sorted(t.rglob("*.py")) if "__pycache__" not in p.parts)
    return out


def _loader_sites() -> list[tuple[str, str]]:
    """(파일:줄, 어디서 import 했나) — `load_file`·`safe_open` 호출마다."""
    out = []
    for p in _py():
        tree = ast.parse(p.read_text(encoding="utf-8"))
        origin = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for a in node.names:
                    if a.name in LOADERS:
                        origin[a.asname or a.name] = node.module or ""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in LOADERS:
                out.append((f"{p.relative_to(ROOT)}:{node.lineno}", origin.get(node.func.id, "?")))
    return out


class TestEveryLoaderIsSafetensors(unittest.TestCase):
    def test_all_sites_import_from_safetensors(self) -> None:
        sites = _loader_sites()
        self.assertEqual(14, len(sites), [s for s, _ in sites])
        bad = [s for s, o in sites if not o.startswith("safetensors")]
        self.assertEqual([], bad, f"safetensors 가 아닌 로더: {bad}")

    def test_no_pickle_shaped_loader_anywhere(self) -> None:
        files = _py()
        self.assertGreaterEqual(len(files), 40, len(files))
        bad = []
        for p in files:
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and FORBIDDEN.search(ast.unparse(node)):
                    bad.append(f"{p.relative_to(ROOT)}:{node.lineno}")
        self.assertEqual([], bad, f"pickle 계열 로더: {bad}")

    def test_no_pt_or_pth_literal(self) -> None:
        bad = []
        for p in _py():
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and re.search(r"\.pth?$", node.value):
                    bad.append(f"{p.relative_to(ROOT)}:{node.lineno} {node.value!r}")
        self.assertEqual([], bad, bad)


if __name__ == "__main__":
    unittest.main()
