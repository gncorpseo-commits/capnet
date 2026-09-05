r"""`arch` 이름이 **네 곳에서 같은가** (G2 · `tiny_*.py` 형제 전수).

## 왜 있는가

G2 는 「같은 디렉터리의 형제 파일 전수」다. `apps/node/app/tiny_*.py` 는 **아홉**인데
검사가 이름을 부르는 것은 **셋**뿐이었다.

훑어 보니 **클래스 이름은 정본이 아니었다.** `tiny_cnn.py` 의 `ARCH_REGISTRY` 가 정본이고,
같은 구조를 다른 이름으로 등록하는 것이 **의도**다:

```text
"TinyTableTyper": _text_classifier(),   # 표 열 타입 추론은 text.classify 와 같은 모델
```

**「클래스가 없으면 결함」이라고 셌으면 `table_demo.sh` 를 거짓 결함으로 적을 뻔했다** —
`#218`(`$node_id` 를 세어 「우회 일곱」)·`#245`(`datasetId` 두 종류)와 같은 함정이다.

## 진짜 공백 — **데모가 등록하는 이름은 아무도 안 본다**

| 곳 | 무엇 | 대조하던 검사 |
|---|---|---|
| `tiny_cnn.py` `ARCH_REGISTRY` | 빌더 **11** | `test_contract_checks_by_arch` |
| `tiny_cnn.py` `ARCH_MODALITY` | 모달리티 **11** | 같음 |
| `gate.py` `REFERENCE_ARCHS` | 실행 가능 목록 **11** | 같음 |
| **`scripts/*_demo.sh` 의 `arch="…"`** | **9** | **없었다** |

데모의 `arch` 에 오타가 나면 **그 데모를 돌릴 때만** 드러난다. 그런데 그 데모들은
`#254` 기준 **아무도 안 돌린다** — 오타가 무기한 산다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| `ARCH_REGISTRY` = `ARCH_MODALITY` = `REFERENCE_ARCHS` | **11** · 셋 다 같다 ✅ |
| 데모가 등록하는 arch | **9** — 전부 그 11 안 ✅ |
| `tiny_*.py` 형제 | **9** — 전부 레지스트리가 부른다 ✅ |
| 이름이 어긋난 곳 | **0** |

## 무엇을 안 보나

- **클래스 이름과 arch 이름이 같은가.** 같을 필요가 없다 — 위가 그 이유다
- 모델이 **무엇을 내는가.** 그건 `test_output_schema` · 모달리티 검사들이 본다
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = ROOT / "apps" / "node" / "app"
TINY = NODE / "tiny_cnn.py"
GATE = ROOT / "apps" / "core" / "app" / "gate.py"
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import code_only  # noqa: E402

DEMO_ARCH = re.compile(r'^arch="([A-Za-z0-9]+)"', re.M)


def _dict_keys(path: Path, name: str) -> set[str]:
    """모듈 자리의 `NAME: … = {…}` 에서 문자열 키만."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
        if target == name and isinstance(node.value, ast.Dict):
            return {k.value for k in node.value.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    raise AssertionError(f"{path.name} 에서 {name} 을 못 찾았다")


def _reference_archs() -> set[str]:
    src = GATE.read_text(encoding="utf-8")
    block = src[src.index("REFERENCE_ARCHS"):]
    block = block[:block.index("})") + 2]
    return set(re.findall(r'"([A-Za-z0-9]+)"', block))


def _demo_archs() -> dict[str, str]:
    out = {}
    for path in sorted(SCRIPTS.glob("*.sh")):
        m = DEMO_ARCH.search(path.read_text(encoding="utf-8"))
        if m:
            out[path.name] = m.group(1)
    return out


class TestTheThreeCanonicalListsAgree(unittest.TestCase):
    def test_registry_and_modality_have_the_same_keys(self) -> None:
        reg, mod = _dict_keys(TINY, "ARCH_REGISTRY"), _dict_keys(TINY, "ARCH_MODALITY")
        self.assertTrue(reg, "ARCH_REGISTRY 가 비었다")
        self.assertEqual(reg, mod,
                         f"빌더와 모달리티가 갈린다: {sorted(reg ^ mod)}")

    def test_gate_allowlist_matches(self) -> None:
        reg, ref = _dict_keys(TINY, "ARCH_REGISTRY"), _reference_archs()
        self.assertTrue(ref, "REFERENCE_ARCHS 를 못 읽었다")
        self.assertEqual(reg, ref,
                         f"실행 가능 목록이 빌더와 갈린다: {sorted(reg ^ ref)}")


class TestDemosRegisterKnownArchs(unittest.TestCase):
    """**여기가 새로 막는 것이다.** 오타는 그 데모를 돌릴 때만 드러나는데, 아무도 안 돌린다."""

    def test_every_demo_arch_is_known(self) -> None:
        demos = _demo_archs()
        self.assertTrue(demos, "데모의 arch 를 하나도 못 찾았다")
        known = _dict_keys(TINY, "ARCH_REGISTRY")
        bad = sorted(f"{f}: {a}" for f, a in demos.items() if a not in known)
        self.assertEqual([], bad, f"레지스트리에 없는 arch 를 등록한다: {bad}")

    def test_enough_demos_declare_one(self) -> None:
        self.assertGreaterEqual(len(_demo_archs()), 9, sorted(_demo_archs()))


class TestEverySiblingIsReachable(unittest.TestCase):
    """`tiny_*.py` 를 새로 놓고 **레지스트리에 안 넣으면** 아무도 못 쓴다."""

    def test_every_tiny_module_is_imported_by_the_registry(self) -> None:
        siblings = sorted(p for p in NODE.glob("tiny_*.py") if p.name != "tiny_cnn.py")
        self.assertGreaterEqual(len(siblings), 8, [p.name for p in siblings])
        body = code_only(TINY)
        missing = [p.name for p in siblings if f"app.{p.stem}" not in body
                   and f"from app.{p.stem}" not in body and p.stem not in body]
        self.assertEqual([], missing, f"레지스트리가 안 부르는 형제: {missing}")

    def test_the_registry_names_a_capability_for_each(self) -> None:
        mod = _dict_keys(TINY, "ARCH_MODALITY")
        self.assertGreaterEqual(len(mod), 11, sorted(mod))


class TestProbeActuallyScans(unittest.TestCase):
    def test_counts_are_what_we_measured(self) -> None:
        self.assertEqual(11, len(_dict_keys(TINY, "ARCH_REGISTRY")))
        self.assertEqual(11, len(_reference_archs()))

    def test_the_demo_reader_discriminates(self) -> None:
        """아무 문자열이나 잡으면 위 검사가 공허하다."""
        self.assertEqual("TinyTableTyper", DEMO_ARCH.search('arch="TinyTableTyper"\n').group(1))
        self.assertIsNone(DEMO_ARCH.search('  arch="Indented"\n'))
        self.assertIsNone(DEMO_ARCH.search('# arch="주석"\n'))


if __name__ == "__main__":
    unittest.main()
