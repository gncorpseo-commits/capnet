"""`scripts/check_golden_leakage.py` 가 **못 본 것을 깨끗하다고 말하지 않는가.**

## 왜 있는가

**실제로 그렇게 말하고 있었다 (2026-09-02).** 이 도구는 기본 매니페스트 넷을 훑는데,
없는 파일은 `(건너뜀 - 없음)` 한 줄만 찍고 **종료 코드에 아무 영향을 주지 않았다.**
그래서 넷이 다 없어도 이렇게 끝났다:

    $ python3 scripts/check_golden_leakage.py --manifest NO_SUCH.json
      (건너뜀 - 없음) NO_SUCH.json

    겹침 없음. 골든셋은 홀드아웃이다.
    exit=0

**0건을 보고 「깨끗하다」고 단언했다.** 그리고 이건 가정이 아니다 —
기본 넷 중 **셋은 `data/` 아래라 저장소에 추적되지 않는다** (용량). 즉
**신선한 클론에서 시키는 대로 돌리면 늘 저 자리**였다.

하필 그 셋 중 하나가 `data/golden-n300-holdout/…` 이고,
결과보고서는 **「겹침 0/300, `scripts/check_golden_leakage.py` 로 검증」** 이라고 적는다.
따라 돌린 사람은 **40건만 본 초록**을 받고 300건을 확인했다고 믿게 된다.

이 저장소가 이번 회차 내내 고쳐 온 것과 같은 모양이다 —
**「못 했다」·「안 봤다」를 「없다」·「됐다」로 뭉뚱그린다.**

## 무엇을 고정하나

1. **본 것이 0건이면 답하지 않는다** (`1`). 「깨끗하다」는 판단이 아니라 침묵이어야 한다
2. **일부만 봤으면 그렇다고 말한다** (`3`). 못 본 목록을 이름으로 찍는다
3. 겹치면 그대로 `2`
4. 전부 보고 안 겹쳤을 때만 `0`

## 무엇을 안 보나

**개수를 못박지 않는다.** 몇 종이 있는지는 환경마다 다르다 — `data/` 를 만들었는지
여부로 갈린다. 여기서 보는 것은 **개수가 아니라 「못 본 것이 결과에 반영되는가」** 다.

EuroSAT zip 없이 돈다. 순수 함수 `run_manifests` 를 직접 부른다.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_golden_leakage.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_golden_leakage", SCRIPT)
    assert spec and spec.loader, SCRIPT
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CGL = _load()


def _manifest(tmp: Path, name: str, zip_paths: list[str | None]) -> Path:
    p = tmp / name
    cases = [{"zip_path": z} if z else {} for z in zip_paths]
    p.write_text(json.dumps({"cases": cases}), encoding="utf-8")
    return p


class TestUnseenIsNotClean(unittest.TestCase):
    """못 본 것은 `unseen` 으로 나와야 한다 — 조용히 빠지면 안 된다."""

    def test_missing_file_is_reported_as_unseen(self) -> None:
        checked, leaked, unseen = CGL.run_manifests([Path("NO_SUCH_FILE.json")], set(), emit=lambda _s: None)
        self.assertEqual(checked, 0, "없는 파일을 봤다고 세면 안 된다")
        self.assertEqual(leaked, 0)
        self.assertEqual(len(unseen), 1, unseen)
        self.assertIn("NO_SUCH_FILE.json", unseen[0])

    def test_zero_case_manifest_is_unseen_not_clean(self) -> None:
        """케이스 0건짜리를 `clean` 으로 세면 그것도 같은 거짓말이다."""
        with tempfile.TemporaryDirectory() as d:
            m = _manifest(Path(d), "empty.json", [])
            _checked, leaked, unseen = CGL.run_manifests([m], set(), emit=lambda _s: None)
            self.assertEqual(leaked, 0)
            self.assertEqual(len(unseen), 1, "케이스 0건은 「못 봤다」다")
            self.assertIn("0건", unseen[0])

    def test_cases_without_zip_path_are_unseen(self) -> None:
        """`zip_path` 가 없으면 겹치는지 **알 수 없다** — 경고만 찍고 넘기면 안 된다."""
        with tempfile.TemporaryDirectory() as d:
            m = _manifest(Path(d), "noref.json", ["a/b/c.jpg", None, None])
            checked, leaked, unseen = CGL.run_manifests([m], set(), emit=lambda _s: None)
            self.assertEqual(checked, 1)
            self.assertEqual(leaked, 0)
            self.assertEqual(len(unseen), 1, "zip_path 없는 케이스가 있으면 부분 검사다")
            self.assertIn("zip_path", unseen[0])

    def test_full_clean_run_has_nothing_unseen(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            m = _manifest(Path(d), "ok.json", ["x/y/1.jpg", "x/y/2.jpg"])
            checked, leaked, unseen = CGL.run_manifests([m], {"other/z.jpg"}, emit=lambda _s: None)
            self.assertEqual((checked, leaked, unseen), (1, 0, []))

    def test_leak_is_counted(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            m = _manifest(Path(d), "leak.json", ["x/y/1.jpg"])
            checked, leaked, unseen = CGL.run_manifests([m], {"x/y/1.jpg"}, emit=lambda _s: None)
            self.assertEqual((checked, leaked, unseen), (1, 1, []))


class TestExitCodesAreDocumented(unittest.TestCase):
    """머리말이 코드와 같은 말을 하는가 — 문서만 고치고 끝내는 것을 막는다."""

    def test_docstring_declares_every_exit_code(self) -> None:
        doc = CGL.__doc__ or ""
        for code in ("0", "1", "2", "3"):
            self.assertIn(f"{code} =", doc, f"종료 코드 {code} 의 뜻이 머리말에 없다")

    def test_source_no_longer_claims_clean_unconditionally(self) -> None:
        """예전 문구가 조건 없이 남아 있으면 회귀다."""
        src = SCRIPT.read_text(encoding="utf-8")
        # 「겹침 없음. 골든셋은 홀드아웃이다.」 를 조건 없이 찍던 자리
        self.assertNotIn('_out("겹침 없음. 골든셋은 홀드아웃이다.")', src)
        self.assertIn("종 전부 봤다", src, "몇 종을 봤는지 말하지 않으면 같은 함정이다")


if __name__ == "__main__":
    unittest.main()
