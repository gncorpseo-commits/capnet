"""`CLAUDE.md` 절대 규칙을 **기계가 전수한다** (큐 14–19).

## 왜 있는가

절대 규칙 여덟은 「이것을 어기면 프로젝트의 핵심 주장이 무너진다」고 적혀 있다.
그런데 지키는 것은 **사람의 기억**이었다. 전수해 보니 **오늘 새는 곳은 없었다** —
그리고 그것이 이 검사를 만드는 이유다. 7회차 #192–#196 과 같은 자리다.

실측 (2026-09-03):

| 규칙 | 무엇 | 오늘 |
|---|---|---|
| 5 | pickle · `.pt` · `.pth` 로드 | **0건** — 로드는 전부 `safetensors` |
| 2 | `assignment` · `gate_run` INSERT | **5자리 전부** `INSERT … SELECT` |
| 4 | Node 가 자기 등급을 주장 | **0건** — 소진은 초대장, 등록은 admin |
| 8 | 게이트가 제출자 Node 에서 | **0건** — 앱 가드 + `ck_gate_runner_team` + `INSERT … SELECT` |
| 7 | 자유 업로드 · 서명 URL · `fileToken` | **0건** — 금지 문구 주석에만 있다 |
| 3 | `compute_tier` 앱 문자열 비교 | **0건** |

## 무엇을 고정하나

규칙마다 **어긋난 커밋이 들어오면 실패**한다. 목록을 박지 않고 `ast` 로 훑는다.

## 왜 `ast` 인가 — 주석이 오탐을 만든다

`main.py:433` 은 「금지되는 것은 …**서명 URL·fileToken**이다」라고 **적는다.**
`grep` 으로 보면 그 문장이 위반으로 잡힌다. 규칙을 **적어 둔 것**과 **쓴 것**은 다르다.
그래서 문자열·호출은 `ast` 로 보고, 주석과 docstring 은 세지 않는다.

## 무엇을 고정하지 **않나**

규칙 1(schema 제약 약화)·6(사전학습 가중치)은 여기서 안 본다 —
`test_migrate_lint`·`test_license_coverage`·`check_submission` 이 이미 본다.
겹쳐 두면 어느 검사가 진짜로 지키는지 흐려진다.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_ROOTS = (ROOT / "apps", ROOT / "capreq" / "src")
SCHEMA = ROOT / "docs" / "spec" / "schema.sql"
CORE_MAIN = ROOT / "apps" / "core" / "app" / "main.py"
REGISTRY = ROOT / "apps" / "core" / "app" / "registry.py"


def _py_files() -> list[Path]:
    out: list[Path] = []
    for r in CODE_ROOTS:
        out.extend(sorted(p for p in r.rglob("*.py") if "__pycache__" not in p.parts))
    return out


def _parsed() -> list[tuple[Path, ast.Module]]:
    return [(p, ast.parse(p.read_text(encoding="utf-8"))) for p in _py_files()]


def _docstring_ids(tree: ast.Module) -> set[int]:
    """docstring 은 **적어 둔 것**이지 쓴 것이 아니다."""
    out: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = n.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                out.add(id(body[0].value))
    return out


def _live_strings(tree: ast.Module):
    ds = _docstring_ids(tree)
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in ds:
            yield n


class TestRule5NoPickleWeights(unittest.TestCase):
    """**절대규칙 5** — 가중치는 `safetensors` 만. pickle 은 로드 자체가 임의 코드 실행이다."""

    BANNED = frozenset({
        ("torch", "load"), ("pickle", "load"), ("pickle", "loads"),
        ("joblib", "load"), ("dill", "load"), ("dill", "loads"),
    })

    def test_no_pickle_loader_is_called(self) -> None:
        hits = []
        for path, tree in _parsed():
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and isinstance(n.func.value, ast.Name)
                        and (n.func.value.id, n.func.attr) in self.BANNED):
                    hits.append(f"{path.relative_to(ROOT)}:{n.lineno} "
                                f"{n.func.value.id}.{n.func.attr}")
        self.assertEqual([], hits, f"pickle 계열 로더를 부른다: {hits}")

    def test_numpy_load_never_allows_pickle(self) -> None:
        hits = []
        for path, tree in _parsed():
            for n in ast.walk(tree):
                if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "load"):
                    continue
                for kw in n.keywords:
                    if kw.arg == "allow_pickle" and not (
                            isinstance(kw.value, ast.Constant) and kw.value.value is False):
                        hits.append(f"{path.relative_to(ROOT)}:{n.lineno}")
        self.assertEqual([], hits, f"allow_pickle 을 켠다: {hits}")

    def test_no_pt_or_pth_path_in_live_code(self) -> None:
        """경로 문자열이 살아 있으면 다음 사람이 그걸 로더에 넣는다."""
        hits = []
        for path, tree in _parsed():
            for n in _live_strings(tree):
                if n.value.endswith((".pt", ".pth")):
                    hits.append(f"{path.relative_to(ROOT)}:{n.lineno} {n.value!r}")
        self.assertEqual([], hits, f"`.pt`/`.pth` 경로가 코드에 있다: {hits}")

    def test_the_probe_sees_the_real_loader(self) -> None:
        """`safetensors` 로 읽는 자리가 **있어야** 이 검사가 대상을 훑고 있는 것이다."""
        src = "\n".join(p.read_text(encoding="utf-8") for p in _py_files())
        self.assertIn("safetensors", src, "가중치 로더를 하나도 못 찾았다 — 훑는 범위가 틀렸다")


class TestRule2InsertSelectOnly(unittest.TestCase):
    """**절대규칙 2** — `assignment`·`gate_run` 은 `INSERT … SELECT` 만. 앱이 스냅샷을 계산하지 않는다."""

    TARGET = re.compile(r"INSERT\s+INTO\s+(assignment|gate_run)\b", re.I)
    SQL_FILES = ("apps/core/app/*.py", "apps/core/sql/*.sql", "apps/node/app/*.py")

    def _blocks(self) -> list[tuple[str, int, str]]:
        out: list[tuple[str, int, str]] = []
        for pat in self.SQL_FILES:
            for p in sorted(ROOT.glob(pat)):
                lines = p.read_text(encoding="utf-8").splitlines()
                for i, line in enumerate(lines):
                    if self.TARGET.search(line):
                        out.append((str(p.relative_to(ROOT)), i + 1,
                                    "\n".join(lines[i:i + 25])))
        return out

    def test_every_insert_is_a_select(self) -> None:
        bad = []
        for rel, lineno, block in self._blocks():
            head = block.split(";")[0]
            if re.search(r"\bVALUES\b", head, re.I) or not re.search(r"\bSELECT\b", head, re.I):
                bad.append(f"{rel}:{lineno}")
        self.assertEqual(
            [], bad,
            "assignment/gate_run 에 VALUES 로 넣는다 — 스냅샷을 앱이 계산하면 안 된다: " f"{bad}",
        )

    def test_probe_found_the_inserts(self) -> None:
        """0개를 훑으며 통과하는 상태를 막는다."""
        self.assertGreaterEqual(len(self._blocks()), 3,
                                "assignment/gate_run INSERT 를 못 찾았다 — 정규식이 눈멀었다")


class TestRule4NodeCannotClaimItsGrade(unittest.TestCase):
    """**절대규칙 4** — `trust_domain`·`compute_tier_max` 는 Core 가 부여한다."""

    GRADE = ("trust_domain", "compute_tier_max", "is_gate_runner", "org_id")

    def _model_fields(self, name: str) -> set[str]:
        tree = ast.parse(CORE_MAIN.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef) and n.name == name:
                return {
                    t.target.id for t in n.body
                    if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
                }
        return set()

    def test_redeem_body_has_no_grade_field(self) -> None:
        """**여기가 핵심이다.** 소진은 관리 키 없이 열린 유일한 쓰기 경로다."""
        fields = self._model_fields("NodeRedeem")
        self.assertTrue(fields, "NodeRedeem 모델을 못 찾았다")
        leaked = sorted(set(self.GRADE) & fields)
        self.assertEqual([], leaked, f"소진 본문이 등급을 주장할 수 있다: {leaked}")

    def test_credential_body_has_no_grade_field(self) -> None:
        fields = self._model_fields("CredentialIssueBody")
        self.assertTrue(fields, "CredentialIssueBody 모델을 못 찾았다")
        self.assertEqual([], sorted(set(self.GRADE) & fields))

    def test_redeem_handler_reads_the_invite_not_the_body(self) -> None:
        src = CORE_MAIN.read_text(encoding="utf-8")
        tree = ast.parse(src)
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and n.name == "node_redeem"), None)
        self.assertIsNotNone(fn, "node_redeem 핸들러가 없다")
        assert fn is not None
        body = ast.get_source_segment(src, fn) or ""
        for field in ("trust_domain", "compute_tier_max"):
            with self.subTest(field=field):
                self.assertIn(f'invite["{field}"]', body,
                              f"{field} 를 초대장에서 안 읽는다")
                self.assertNotIn(f"body.{field}", body,
                                 f"{field} 를 소진 **본문**에서 읽는다 — 절대규칙 4 위반")


class TestRule8GateRunnerIsTeamOnly(unittest.TestCase):
    """**절대규칙 8** — 게이트는 team gate-runner Node 에서만. 제출자가 자기를 채점할 수 없다."""

    def test_app_refuses_non_team_gate_runner(self) -> None:
        src = REGISTRY.read_text(encoding="utf-8")
        self.assertRegex(src, r"if is_gate_runner and source != \"team\"",
                         "registry 가 team 이 아닌 게이트러너를 막지 않는다")

    def test_schema_has_the_constraint(self) -> None:
        """앱 가드는 우회된다. **DB 가 마지막이다.**"""
        self.assertIn("ck_gate_runner_team", SCHEMA.read_text(encoding="utf-8"),
                      "schema 에 ck_gate_runner_team 이 없다")

    def test_redeem_never_makes_a_gate_runner(self) -> None:
        src = CORE_MAIN.read_text(encoding="utf-8")
        tree = ast.parse(src)
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and n.name == "node_redeem"), None)
        assert fn is not None
        self.assertIn("is_gate_runner=False", ast.get_source_segment(src, fn) or "",
                      "초대 소진이 게이트러너를 만들 수 있다")

    def test_gate_run_insert_checks_the_runner(self) -> None:
        gate = (ROOT / "apps" / "core" / "app" / "gate.py").read_text(encoding="utf-8")
        self.assertIn("is_gate_runner", gate,
                      "gate_run INSERT 가 러너의 자격을 안 본다")


class TestRule7NoUncontrolledIntake(unittest.TestCase):
    """**절대규칙 7 (D8′)** — 금지 대상은 「자유 업로드」가 아니라 **비통제 수집**이다."""

    BANNED = re.compile(r"file_?token|presigned|signed_?url|upload_?url", re.I)

    def test_no_uncontrolled_intake_identifier(self) -> None:
        """주석·docstring 은 세지 않는다 — 금지 문구를 **적어 둔 것**이 위반이 되면 안 된다."""
        hits = []
        for path, tree in _parsed():
            for n in ast.walk(tree):
                if isinstance(n, ast.Name) and self.BANNED.search(n.id):
                    hits.append(f"{path.relative_to(ROOT)}:{n.lineno} {n.id}")
                elif isinstance(n, ast.Attribute) and self.BANNED.search(n.attr):
                    hits.append(f"{path.relative_to(ROOT)}:{n.lineno} .{n.attr}")
                elif isinstance(n, ast.arg) and self.BANNED.search(n.arg):
                    hits.append(f"{path.relative_to(ROOT)}:{n.lineno} arg {n.arg}")
            for n in _live_strings(tree):
                if self.BANNED.search(n.value):
                    hits.append(f"{path.relative_to(ROOT)}:{n.lineno} {n.value!r}")
        self.assertEqual([], hits, f"비통제 수집 경로로 읽히는 이름: {hits}")

    def test_the_rule_is_still_written_down(self) -> None:
        """금지 문구가 사라지면 다음 사람이 왜 안 되는지 모른다."""
        self.assertIn("fileToken", CORE_MAIN.read_text(encoding="utf-8"),
                      "D8′ 금지 근거 주석이 사라졌다")


class TestRule3NoTierStringCompare(unittest.TestCase):
    """**절대규칙 3** — 텍스트 정렬은 `L < M < S` 로 **의도와 반대**다."""

    @staticmethod
    def _name_of(node: ast.AST) -> str:
        if isinstance(node, ast.Attribute):
            return node.attr
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            return str(node.slice.value)
        return ""

    def test_no_ordering_comparison_on_tier(self) -> None:
        hits = []
        for path, tree in _parsed():
            for n in ast.walk(tree):
                if isinstance(n, ast.Compare) and any(
                        isinstance(o, (ast.Lt, ast.Gt, ast.LtE, ast.GtE)) for o in n.ops):
                    names = [self._name_of(x) for x in [n.left, *n.comparators]]
                    if any("tier" in s.lower() for s in names if s):
                        hits.append(f"{path.relative_to(ROOT)}:{n.lineno}")
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        and n.func.id in ("sorted", "max", "min") and n.args):
                    if "tier" in self._name_of(n.args[0]).lower():
                        hits.append(f"{path.relative_to(ROOT)}:{n.lineno} {n.func.id}")
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "sort"
                        and "tier" in self._name_of(n.func.value).lower()):
                    hits.append(f"{path.relative_to(ROOT)}:{n.lineno} .sort")
        self.assertEqual(
            [], hits,
            "compute_tier 를 앱이 직접 비교·정렬한다 — tier_compatible 행렬에 맡긴다: " f"{hits}",
        )

    def test_the_matrix_exists(self) -> None:
        self.assertIn("tier_compatible", SCHEMA.read_text(encoding="utf-8"),
                      "tier_compatible 행렬이 schema 에 없다")


class TestProbeActuallyScans(unittest.TestCase):
    """훑는 범위가 비면 위 검사 **전부**가 공허하게 통과한다."""

    def test_enough_files(self) -> None:
        self.assertGreater(len(_py_files()), 15,
                           f"파이썬 파일을 {len(_py_files())}개밖에 못 찾았다")

    def test_docstrings_are_actually_excluded(self) -> None:
        """제외가 너무 넓으면 살아 있는 문자열도 같이 빠진다."""
        tree = ast.parse('"""doc .pt"""\nx = "live.pt"\n')
        live = [n.value for n in _live_strings(tree)]
        self.assertEqual(["live.pt"], live)


if __name__ == "__main__":
    unittest.main()
