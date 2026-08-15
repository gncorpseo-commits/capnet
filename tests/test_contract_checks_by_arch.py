"""계약 검사 집합이 arch 로 갈리는 것과 가중치 지문을 고정한다 (Decision 2-C · C2).

## 왜 있는가

`CONTRACT_CHECKS` 는 5종 고정 튜플이었고, 그 5종이 전부 **이미지·torch 전용**이었다.
그래서 `text.summarize` 같은 능력은 계약 게이트를 통과할 방법이 아예 없었다
(`agent_capability_passed` 미발급 → `assignment` FK 위반 → 라우팅 불가).

C2 가 그것을 갈랐다. 여기서 고정하는 것은 셋이다.

1. **`image.classify` 경로 무회귀** — 참조 구현(`TinyEuroSAT`)은 **종전 6종 전부**를 요구한다.
   촬영이 이 경로 위에 있으므로 여기가 느슨해지면 안 된다.
2. **비참조 arch 는 공통 5종** — 실행할 수 없는 것(`arch`)은 요구하지도 보고하지도 않지만,
   **`max_params` 는 지문으로 실제로 잰다** (D-maxp). 상한 없는 모델이 들어오지 못한다.
3. **두 목록이 어긋나지 않는가** — Core 의 `REFERENCE_ARCHS`(실행 가능 목록)와
   Node 의 `ARCH_REGISTRY`(빌더 목록)는 같아야 한다. 한쪽만 늘면 조용히 깨진다.

## 판정 방식과 그 한계

지문은 **실제 가중치 파일**로 돌린다(저장소에 들어 있다). Core 쪽 검사 집합 함수는
psycopg 없이 import 할 수 없으므로, 없으면 skip 하고 소스 텍스트로 대신 본다.
DB CHECK 와 종단 동작은 `clean_room`/`prod_room` 의 몫이다.
"""

from __future__ import annotations

import importlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# `apps/node` 와 `apps/core` 는 **둘 다 `app` 패키지**를 갖는다. sys.path 에 한 번 올려
# 두는 방식은 못 쓴다 — `unittest discover` 가 다른 테스트 모듈(예: `test_migrate_lint`)을
# 먼저 import 하면서 core 를 앞에 꽂으면, 이 파일의 node import 가 조용히 core 로 간다.
# **혼자 돌리면 통과하고 전체로 돌리면 깨지는** 종류라, 매번 명시적으로 전환한다.


def _purge_app_modules() -> None:
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]


class AppPathMixin:
    """검사가 도는 **동안만** `app` 이 우리 쪽을 가리키게 하고, 끝나면 되돌린다.

    import 직후에 되돌리면 안 된다 — `contract_check.run` 은 호출 시점에
    `from app.preprocess import …` 를 하므로 그때도 경로가 살아 있어야 한다.
    반대로 되돌리지 않으면 **뒤에 도는 다른 테스트 모듈**의 지연 import 가 엉뚱한 `app` 을 집는다.
    (실제로 그렇게 깨졌다. 혼자 돌리면 통과하고 전체로 돌리면 실패하는 종류였다.)
    """

    APP_DIR = "node"

    def setUp(self) -> None:
        self._saved_path = list(sys.path)
        _purge_app_modules()
        sys.path.insert(0, str(ROOT / "apps" / self.APP_DIR))

    def tearDown(self) -> None:
        sys.path[:] = self._saved_path
        _purge_app_modules()

    @staticmethod
    def mod(modname: str):
        return importlib.import_module(f"app.{modname}")

WEIGHTS = ROOT / "apps" / "node" / "weights" / "eurosat_scratch.safetensors"
WEIGHTS_B = ROOT / "apps" / "node" / "weights" / "eurosat_scratch_b.safetensors"
PLACEHOLDER = ROOT / "apps" / "node" / "weights" / "placeholder.safetensors"

try:
    import psycopg  # noqa: F401
    _HAS_PSYCOPG = True
except ModuleNotFoundError:
    _HAS_PSYCOPG = False


class TestFingerprint(AppPathMixin, unittest.TestCase):
    """지문은 **파일을 열되 실행하지 않는다** — torch 없이 돌아야 한다."""

    def test_reads_real_weights_without_torch(self) -> None:
        fingerprint = self.mod("fingerprint").fingerprint

        fp = fingerprint(WEIGHTS)
        self.assertEqual(len(fp["sha256"]), 64)
        self.assertGreater(fp["tensor_count"], 0)
        # 0008 이 「TinyEuroSAT ~93k」로 적어 둔 값과 자릿수가 맞아야 한다.
        # shape 만으로 센 값이므로 torch 로 센 값과 같아야 한다.
        self.assertEqual(fp["param_count"], 94538)

    def test_torch_is_not_imported(self) -> None:
        """`app.fingerprint` 가 torch 를 끌고 오지 않는다.

        `s-public` Node 에는 torch 가 없다(`Dockerfile` 이 조건부로 설치한다).
        여기서 torch 를 요구하면 지문을 돌릴 수 있는 기기가 좁아진다.
        """
        src = (ROOT / "apps" / "node" / "app" / "fingerprint.py").read_text(encoding="utf-8")
        # **import 문만** 본다. 문서 문구에 「safetensors」가 나오는 것은 당연하고,
        # 그것까지 잡으면 설명을 지워야 통과하는 검사가 된다 (0018 에서 한 번 겪었다).
        imports = [
            ln.strip() for ln in src.splitlines()
            if ln.strip().startswith(("import ", "from "))
        ]
        self.assertFalse(
            [ln for ln in imports if "torch" in ln or "safetensors" in ln],
            f"무거운 의존성을 import 한다: {imports}",
        )

    def test_distinguishes_different_models(self) -> None:
        """다른 구조는 다른 지문이어야 한다 — 같으면 지문이 아무것도 안 재는 것이다."""
        fingerprint = self.mod("fingerprint").fingerprint

        a, b, p = (fingerprint(w)["sha256"] for w in (WEIGHTS, WEIGHTS_B, PLACEHOLDER))
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, p)

    def test_stable_across_calls(self) -> None:
        fingerprint = self.mod("fingerprint").fingerprint

        self.assertEqual(fingerprint(WEIGHTS)["sha256"], fingerprint(WEIGHTS)["sha256"])

    def test_rejects_non_safetensors(self) -> None:
        mod = self.mod("fingerprint")
        FingerprintError, fingerprint = mod.FingerprintError, mod.fingerprint

        with tempfile.NamedTemporaryFile(suffix=".safetensors", delete=False) as fh:
            fh.write(b"not a safetensors file at all")
            path = fh.name
        try:
            with self.assertRaises(FingerprintError):
                fingerprint(path)
        finally:
            Path(path).unlink()

    def test_rejects_empty_file(self) -> None:
        mod = self.mod("fingerprint")
        FingerprintError, fingerprint = mod.FingerprintError, mod.fingerprint

        with tempfile.NamedTemporaryFile(suffix=".safetensors", delete=False) as fh:
            path = fh.name
        try:
            with self.assertRaises(FingerprintError):
                fingerprint(path)
        finally:
            Path(path).unlink()


class TestDeclarationOnlyPath(AppPathMixin, unittest.TestCase):
    """참조 구현이 아닐 때 — 선언만 보고, **했다고 거짓 보고하지 않는다.**"""

    CONTRACT = {
        "input_schema": {
            "mediaTypes": ["text/plain"],
            "preprocess": {"resize": [1, 1], "colorspace": "RGB"},
        },
        "output_schema": {"required": ["label"], "properties": {"label": {"type": "string"}}},
    }

    def _run(self, **over):
        run = self.mod("contract_check").run

        kwargs = dict(
            weights=str(WEIGHTS), arch="SomeTextModel", max_params=None,
            contract=self.CONTRACT, sample="/dev/null",
        )
        kwargs.update(over)
        return run(**kwargs)

    def test_reports_common_five_only(self) -> None:
        out = self._run()
        reported = {k for k in out if not k.startswith("_")}
        self.assertEqual(
            reported,
            {"input_schema", "output_schema", "preprocess",
             "weights_fingerprint", "max_params"},
        )

    def test_does_not_claim_arch(self) -> None:
        """모델을 세우지 않았으므로 `arch` 를 **보고하지 않는다.**

        `False` 로 보내는 것도 안 된다 — 그러면 「검사했는데 떨어졌다」로 읽힌다.
        아예 없는 것이 「검사하지 않았다」의 정직한 표현이다.

        `max_params` 는 다르다 — 지문의 shape 합계로 **실제로 잰다** (D-maxp).
        """
        out = self._run()
        self.assertNotIn("arch", out)
        self.assertIn("max_params", out)

    def test_all_common_checks_pass_on_good_contract(self) -> None:
        out = self._run(max_params=10_000_000)
        for k in ("input_schema", "output_schema", "preprocess",
                  "weights_fingerprint", "max_params"):
            self.assertIs(out[k], True, f"{k} 가 통과하지 않았다: {out['_notes'].get(k)}")

    def test_max_params_is_enforced_without_torch(self) -> None:
        """**상한을 넘으면 떨어진다** — 이게 D-maxp 의 요점이다.

        eurosat_scratch 는 94,538 파라미터다. 상한을 그 아래로 주면 실패해야 한다.
        비참조 경로라 모델을 세우지 않고 **지문의 shape 합계**로만 판정한다.
        """
        out = self._run(max_params=1000)
        self.assertIs(out["max_params"], False)
        self.assertIn("94538", out["_notes"]["max_params"])

    def test_max_params_passes_under_cap(self) -> None:
        out = self._run(max_params=94_538)
        self.assertIs(out["max_params"], True, out["_notes"]["max_params"])

    def test_missing_media_types_fails(self) -> None:
        """`mediaTypes` 미선언은 업로드 자체가 400 이다(B1). 계약 게이트도 거절한다."""
        contract = {
            "input_schema": {"preprocess": {"resize": [1, 1], "colorspace": "RGB"}},
            "output_schema": {"required": ["label"]},
        }
        out = self._run(contract=contract)
        self.assertIs(out["input_schema"], False)

    def test_missing_preprocess_fails(self) -> None:
        contract = {
            "input_schema": {"mediaTypes": ["text/plain"]},
            "output_schema": {"required": ["label"]},
        }
        out = self._run(contract=contract)
        self.assertIs(out["preprocess"], False)

    def test_limits_are_stated_in_evidence(self) -> None:
        """「계약대로 동작한다는 보장이 아니다」가 **증적에 남는다.**

        이 문장이 사라지면 사람이 통과 사실만 보고 동작 보장으로 읽는다.
        """
        out = self._run()
        self.assertIn("보장하지 않는다", out["_notes"]["_limits"])


@unittest.skipUnless(_HAS_PSYCOPG, "psycopg 없음 — 의존성 있는 환경에서만 돈다")
class TestRequiredSet(AppPathMixin, unittest.TestCase):
    APP_DIR = "core"

    def _core_fn(self):
        return self.mod("gate").required_contract_checks

    def test_reference_arch_requires_all_six(self) -> None:
        """**무회귀** — 촬영 경로(`TinyEuroSAT`)는 종전 6종 전부를 요구한다."""
        required_contract_checks = self._core_fn()

        req = required_contract_checks("TinyEuroSAT")
        self.assertEqual(
            set(req),
            {"input_schema", "output_schema", "preprocess",
             "weights_fingerprint", "arch", "max_params"},
        )

    def test_unknown_arch_requires_common_five(self) -> None:
        """비참조도 `max_params` 를 요구한다 (D-maxp) — 상한 없는 모델을 막는다."""
        required_contract_checks = self._core_fn()

        self.assertEqual(
            set(required_contract_checks("SomeTextModel")),
            {"input_schema", "output_schema", "preprocess",
             "weights_fingerprint", "max_params"},
        )

    def test_null_arch_requires_common_four(self) -> None:
        """legacy Agent(arch NULL)도 공통 4종. 참조 구현이라 말할 근거가 없다."""
        required_contract_checks = self._core_fn()

        self.assertNotIn("arch", required_contract_checks(None))


class TestCommonSetSource(unittest.TestCase):
    """`CONTRACT_CHECKS_COMMON` 을 **소스로** 본다 — psycopg 없이도 도는 가드.

    `required_contract_checks` 를 직접 부르는 검사는 psycopg 가 있어야 해서 skip 된다.
    그 상태에서 `max_params` 를 공통 집합에서 빼는 변이가 **아무 검사에도 안 걸렸다** —
    비참조 모델의 파라미터 상한이 조용히 사라지는 회귀다 (D-maxp).
    """

    def test_common_set_includes_max_params(self) -> None:
        src = (ROOT / "apps" / "core" / "app" / "gate.py").read_text(encoding="utf-8")
        block = src.split("CONTRACT_CHECKS_COMMON")[1].split(")")[0]
        names = set(re.findall(r'"(\w+)"', block))
        self.assertEqual(
            names,
            {"input_schema", "output_schema", "preprocess",
             "weights_fingerprint", "max_params"},
            "공통 검사 집합이 바뀌었다 — 비참조 모델의 상한이 사라졌을 수 있다",
        )

    def test_reference_only_set_is_arch(self) -> None:
        src = (ROOT / "apps" / "core" / "app" / "gate.py").read_text(encoding="utf-8")
        block = src.split("CONTRACT_CHECKS_REFERENCE")[1].split(")")[0]
        self.assertEqual(set(re.findall(r'"(\w+)"', block)), {"arch"})


class TestRegistryDrift(unittest.TestCase):
    """Core 의 실행 가능 목록과 Node 의 빌더 목록이 어긋나면 조용히 깨진다."""

    def test_reference_archs_matches_node_registry(self) -> None:
        core_src = (ROOT / "apps" / "core" / "app" / "gate.py").read_text(encoding="utf-8")
        node_src = (ROOT / "apps" / "node" / "app" / "tiny_cnn.py").read_text(encoding="utf-8")

        # 문자열로 뽑는다 — Core 는 psycopg, Node 는 torch 를 요구해서 둘 다 import 가 안 된다.
        core_names = set(re.findall(r'"(\w+)"', core_src.split("REFERENCE_ARCHS")[1].split("}")[0]))
        node_names = set(re.findall(r'"(\w+)":', node_src.split("ARCH_REGISTRY")[1].split("}")[0]))
        self.assertEqual(
            core_names, node_names,
            "gate.REFERENCE_ARCHS 와 tiny_cnn.ARCH_REGISTRY 가 다르다 — "
            "한쪽만 늘리면 계약 게이트가 조용히 어긋난다",
        )


if __name__ == "__main__":
    unittest.main()
