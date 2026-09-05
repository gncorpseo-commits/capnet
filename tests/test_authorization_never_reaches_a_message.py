r"""Authorization 값이 **예외 문구·응답·헤더 조립 밖으로** 나가지 않는다 (배치 B #81 · `#218` 잔여).

## 왜 있는가

`test_secrets_never_reach_output` 은 **로그·출력 호출**의 인자를 본다. 그런데 키가 새는
길은 하나 더 있다 — **예외 문구**다. `raise ApiKeyError(f"bad {authorization}")` 는 로그
호출이 아니지만, 그 예외를 `print(f"… {exc}")` 가 받으면 값이 그대로 찍힌다. Node 는
실제로 `{exc}` 를 다섯 곳에서 찍는다.

## 실측 (2026-09-06)

| 무엇 | 값 |
|---|---|
| `raise` 247 · `HTTPException(` 84 중 시크릿 이름의 값을 문구에 싣는 것 | **0** |
| Core 의 `return` 이 `authorization` 을 싣는 곳 | **2** — 둘 다 `verify_key`·`verify_credential` 의 **인자**다 |
| Node 의 `NODE_CREDENTIAL` 이 문자열로 합쳐지는 곳 | **1** — `headers["Authorization"]` 한 줄 |
| Core 가 헤더 값을 응답으로 돌려주는 곳 | **0** |

`apps/node/app/preprocess.py` 의 `f"preprocess.{key} …"` 는 **설정 필드 이름**이지 키가 아니다 —
아래 `EXEMPT` 한 건.

## 재현

```bash
python3 -m unittest tests.test_authorization_never_reaches_a_message
```
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "apps" / "core" / "app"
NODE = ROOT / "apps" / "node" / "app"

SECRET_WORDS = ("secret", "credential", "cred", "key", "apikey", "token", "password", "authorization")
NOT_SECRET = ("_file", "_path", "_dir", "_prefix", "prefix", "present", "_name", "_id", "keys")

# **이름은 시크릿 낱말이지만 값은 아닌** 자리 — 왜 괜찮은지 적는다.
EXEMPT: dict[tuple[str, str], str] = {
    ("apps/node/app/preprocess.py", "key"): "preprocess 설정의 필드 이름(resize·crop…)을 도는 루프 변수",
}


def _is_secret(name: str) -> bool:
    n = name.lower()
    return any(w in n for w in SECRET_WORDS) and not any(x in n for x in NOT_SECRET)


def _py() -> list[Path]:
    return sorted(list(CORE.glob("*.py")) + list(NODE.glob("*.py")))


def _secret_refs(sub: ast.AST, skip: ast.AST | None = None) -> list[str]:
    out = []
    for n in ast.walk(sub):
        if n is skip:
            continue
        if isinstance(n, ast.Name) and _is_secret(n.id):
            out.append(n.id)
        elif isinstance(n, ast.Attribute) and _is_secret(n.attr):
            out.append(n.attr)
    return out


def _messages() -> tuple[int, int, list[str]]:
    """(`raise` 수, `HTTPException(` 수, 시크릿 값을 문구에 실은 자리)."""
    raises = https = 0
    bad = []
    for p in _py():
        rel = str(p.relative_to(ROOT))
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Raise) and node.exc is not None:
                raises += 1
                sub = node.exc
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "HTTPException":
                https += 1
                sub = node
            else:
                continue
            # 예외 **클래스 이름**(`ApiKeyError`)은 값이 아니다 — 호출 대상은 뺀다.
            callee = sub.func if isinstance(sub, ast.Call) else None
            refs = [r for r in _secret_refs(sub, skip=callee) if (rel, r) not in EXEMPT]
            if refs:
                bad.append(f"{rel}:{node.lineno} {refs}")
    return raises, https, bad


class TestExceptionMessagesCarryNoSecret(unittest.TestCase):
    def test_no_raise_or_http_detail_names_a_secret_value(self) -> None:
        raises, https, bad = _messages()
        self.assertGreaterEqual(raises, 200, raises)
        self.assertGreaterEqual(https, 60, https)
        self.assertEqual([], bad, f"예외 문구에 시크릿 값이 실린다: {bad}")

    def test_exemptions_are_real(self) -> None:
        for (rel, name), why in EXEMPT.items():
            with self.subTest(site=rel):
                self.assertTrue(why.strip(), "이유가 비었다")
                body = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn(f"{{{name}}}", body, f"{rel} 에 {{{name}}} 이 더는 없다 — 예외를 지워라")


class TestCoreNeverEchoesTheHeader(unittest.TestCase):
    def test_authorization_is_returned_only_into_a_verifier(self) -> None:
        """`return verify_key(conn, authorization)` 은 넘기는 것이지 돌려주는 것이 아니다."""
        seen, bad = [], []
        for p in CORE.glob("*.py"):
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if not (isinstance(node, ast.Return) and node.value is not None):
                    continue
                if not any(isinstance(x, ast.Name) and x.id == "authorization" for x in ast.walk(node.value)):
                    continue
                v = node.value
                callee = v.func.id if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) else None
                seen.append(callee)
                if callee not in ("verify_key", "verify_credential"):
                    bad.append(f"{p.name}:{node.lineno}")
        self.assertEqual(["verify_credential", "verify_key"], sorted(s for s in seen if s), seen)
        self.assertEqual([], bad, f"authorization 을 응답으로 돌려준다: {bad}")


class TestNodeCredentialIsOnlyEverAHeader(unittest.TestCase):
    def test_the_credential_is_joined_into_one_string_only(self) -> None:
        tree = ast.parse((NODE / "main.py").read_text(encoding="utf-8"))
        joins = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.JoinedStr, ast.BinOp, ast.Call)) and any(
                isinstance(x, ast.Name) and x.id == "NODE_CREDENTIAL" for x in ast.walk(node)
            ):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bool":
                    continue  # `credential_present: bool(NODE_CREDENTIAL)` — 값이 아니라 유무
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    continue  # `os.environ.get(...)` 은 읽는 쪽
                joins.append((type(node).__name__, node.lineno))
        self.assertEqual(1, len(joins), f"NODE_CREDENTIAL 이 문자열로 합쳐지는 곳이 하나가 아니다: {joins}")
        line = (NODE / "main.py").read_text(encoding="utf-8").splitlines()[joins[0][1] - 1]
        self.assertIn('headers["Authorization"] = f"CapNet-Node {NODE_CREDENTIAL}"', line)


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_modules_are_read(self) -> None:
        self.assertGreaterEqual(len(_py()), 25, len(_py()))

    def test_detector_finds_a_planted_leak(self) -> None:
        tree = ast.parse('raise ApiKeyError(f"bad {authorization}")')
        raise_ = tree.body[0]
        assert isinstance(raise_, ast.Raise) and raise_.exc is not None
        refs = _secret_refs(raise_.exc, skip=raise_.exc.func)  # type: ignore[attr-defined]
        self.assertEqual(["authorization"], refs)


if __name__ == "__main__":
    unittest.main()
