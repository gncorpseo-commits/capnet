"""작업량 조회면이 **정본을 뒤바꾸지 않았는지** 본다 (P2-2 · PR-C · D1–D3).

## 왜 있는가

Decision D1 은 「Core 관측(`finished_at − created_at`)이 정본, Node 자기신고
(`assignment.duration_ms`)는 힌트」다. 이 구별이 코드에서 조용히 뒤집히면
원가 모델이 전송·대기·큐를 뺀 값으로 서고, 그 사실은 숫자만 봐서는 안 보인다.

DB 로 도는 검사는 `tests/integration/check_work_units.py` 에 있다 (관측 ≥ 자기신고).
여기는 **DB 없이** 지킬 수 있는 것만 본다 — CI 단위 잡은 아무것도 설치하지 않는다.

## 무엇을 고정하나

1. 조회면이 **쓰지 않는다** — INSERT/UPDATE/DELETE 가 없다
2. **정본이 관측이다** — `finished_at − created_at` 을 실제로 계산한다
3. **자기신고를 정본이라 부르지 않는다** — `canonical` 은 `core_observed_ms` 다
4. `vram_mb_peak` · `energy_wh` 를 **세기만 하고 채우지 않는다** (D2)
5. 종결된 배정만 센다 (`finished_at IS NOT NULL`)
6. 기본 창이 7일이다 (D3 · 정책 숫자)
7. 라우트가 문서·스키마와 이어져 있다
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from _srcguard import code_only

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "apps" / "core" / "app" / "work_units.py"
MAIN = ROOT / "apps" / "core" / "app" / "main.py"
SCHEMA = ROOT / "docs" / "spec" / "schema.sql"
SPEC = ROOT / "apps" / "core" / "openapi.yaml"

# 설명 안의 단어에 걸리지 않게 주석·docstring 을 걷어낸다 (`_srcguard` 참조).
CODE = code_only(MODULE)


class TestReadOnly(unittest.TestCase):
    def test_no_writes(self) -> None:
        for verb in ("INSERT", "UPDATE ", "DELETE", "CREATE ", "DROP "):
            self.assertNotIn(
                verb, CODE.upper(), f"조회면에 {verb.strip()} 가 있다 — 읽기 전용이다"
            )


class TestCanonicalIsCoreObserved(unittest.TestCase):
    def test_observed_is_computed(self) -> None:
        """정본은 저장하지 않는 파생값이다 — 그러니 여기서 계산해야 한다."""
        self.assertIn("finished_at - a.created_at", CODE.replace("a.finished_at", "finished_at"))
        self.assertIn("EXTRACT(EPOCH", CODE)

    def test_canonical_names_observed(self) -> None:
        m = re.search(r'"canonical":\s*"([a-z_]+)"', CODE)
        self.assertIsNotNone(m, "measure.canonical 이 없다")
        assert m is not None
        self.assertEqual(
            m.group(1), "core_observed_ms",
            "정본이 Core 관측이 아니다 — D1 이 뒤집혔다",
        )

    def test_hint_is_named_a_hint(self) -> None:
        """`duration_ms` 는 `node_hint_ms` 로만 실어 보낸다."""
        self.assertIn("a.duration_ms", CODE)
        self.assertIn("node_hint_ms", CODE)

    def test_relation_is_checked(self) -> None:
        """관측 ≥ 자기신고가 깨지면 응답이 그것을 말해야 한다."""
        self.assertIn("hint_exceeds_observed", CODE)


class TestUnmeasuredStaysUnmeasured(unittest.TestCase):
    """RSS·추정으로 채우면 칸 이름이 거짓말이 된다 (D2).

    **단어 금지로 검사하지 않는다.** 처음엔 `"rss" not in CODE` 로 썼는데, 그 검사가
    「RSS 로 대체하지 않는다」고 적어 둔 `MEASURE` 문자열에 걸렸다 — `_srcguard` 가
    말하는 그 사고의 다섯 번째다(이번엔 주석이 아니라 **문자열 상수**라 걷어낼 수도 없다).
    그래서 「무엇을 쓰지 않았나」 대신 **「무엇을 했나」**를 본다: 세지, 채우지 않는다.
    """

    def test_counts_measured_instead_of_filling(self) -> None:
        self.assertIn("vram_measured", CODE)
        self.assertIn("energy_measured", CODE)
        # 채운다면 계측 장치를 끌어와야 한다. 임포트가 없으면 채울 수단이 없다.
        for mod in ("psutil", "pynvml", "resource"):
            self.assertNotIn(f"import {mod}", CODE, f"{mod} 로 계측을 흉내내려 한다")

    def test_measure_says_unmeasured(self) -> None:
        for key in ("vram_mb_peak", "energy_wh"):
            m = re.search(rf'"{key}":\s*"([^"]+)"', CODE)
            self.assertIsNotNone(m, f"measure 에 {key} 설명이 없다")
            assert m is not None
            self.assertIn("미계측", m.group(1), f"{key} 를 미계측이라 적지 않았다")


class TestWindow(unittest.TestCase):
    def test_only_finished_assignments(self) -> None:
        self.assertIn("finished_at IS NOT NULL", CODE)

    def test_default_window_is_seven_days(self) -> None:
        m = re.search(r"DEFAULT_WINDOW_DAYS\s*=\s*(\d+)", CODE)
        self.assertIsNotNone(m, "기본 창 상수가 없다")
        assert m is not None
        self.assertEqual(m.group(1), "7", "기본 창은 최근 7일이다 (D3)")

    def test_window_has_an_upper_bound(self) -> None:
        self.assertIn("MAX_WINDOW_DAYS", CODE)


class TestWiring(unittest.TestCase):
    def test_route_exists(self) -> None:
        main = code_only(MAIN)
        self.assertIn('@app.get("/v1/ops/work-units")', main)
        self.assertIn('_require("developer"', main)

    def test_documented_in_openapi(self) -> None:
        self.assertIn("/v1/ops/work-units:", SPEC.read_text(encoding="utf-8"))

    def test_schema_records_column_meaning(self) -> None:
        """컬럼의 뜻이 DDL 정본에 적혀 있어야 한다 (D1 — 「어디에도 안 적혀 있다」가 문제였다)."""
        block = re.search(r"CREATE TABLE assignment\b.*?\n\);", SCHEMA.read_text(encoding="utf-8"), re.S)
        self.assertIsNotNone(block)
        assert block is not None
        text = block.group(0)
        self.assertIn("자기신고", text, "duration_ms 가 자기신고임이 schema.sql 에 없다")
        self.assertIn("미계측", text, "vram_mb_peak·energy_wh 가 미계측임이 schema.sql 에 없다")


if __name__ == "__main__":
    unittest.main()
