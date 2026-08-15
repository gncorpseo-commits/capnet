"""능력 카탈로그 52 의 정합과 「골든은 채점 가능한 출력에만」을 고정한다.

## 왜 있는가

카탈로그는 문서고, 문서는 조용히 어긋난다. 여기서 잡는 것은 셋이다.

1. **카탈로그가 52 를 유지하는가** — 항목을 추가·삭제하면서 합계표를 안 고치는 일이 생긴다.
   합계가 본문과 다르면 「몇 개를 지원한다」는 말이 근거를 잃는다.
2. **`freeform` 에 골든 프로파일이 붙지 않는가** — DB CHECK(`0018`)와 앱 검증
   (`capability.py`)과 **문서**가 같은 말을 해야 한다. 셋 중 하나만 풀려도 구멍이다.
3. **격리 전 잠금 셋이 문서에 남아 있는가** — `code.generate`·`tool.plan`·`tool.action`.

## 판정 방식과 그 한계

문서는 **표 행을 파싱**하고, 앱은 **실제로 호출**한다(DB 없이 — 검증이 `conn` 을 쓰기 전에
`ValueError` 로 끝나기 때문이다). DB CHECK 자체는 여기서 못 돌린다 —
그건 `clean_room`/`prod_room` 의 몫이고, 여기서는 **마이그레이션에 그 CHECK 가 있는지**만 본다.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "core"))

CATALOG = ROOT / "docs" / "spec" / "capability-catalog.md"
MIGRATION = ROOT / "migrations" / "0018_no_golden_on_freeform.sql"

# 이 리포의 단위 잡은 의존성 0 으로 돈다 (`run_tests.sh`). `capability.py` 는 psycopg 를
# import 하므로 여기서는 대개 못 불러온다 — 그럴 땐 소스 텍스트로 대신 보고, 실제 호출
# 검사는 의존성이 있는 환경에서만 돌린다. 「없으면 조용히 통과」가 아니라 **skip 으로 보인다.**
try:  # noqa: SIM105
    import psycopg  # noqa: F401
    _HAS_PSYCOPG = True
except ModuleNotFoundError:
    _HAS_PSYCOPG = False

EXPECTED_TOTAL = 52
EXPECTED_BY_KIND = {"closed_set_labels": 10, "structured": 26, "freeform": 16}

# 격리(v제품-2) 전에는 라우팅을 열지 않는 셋. 산출물이 **실행**되는 능력들이다.
LOCKED_UNTIL_ISOLATION = ("code.generate", "tool.plan", "tool.action")

# 카탈로그 표의 능력 행:  | 3 | `image.segment` | image | `structured` | none | v제품-1 |
_ROW = re.compile(
    r"^\|\s*(\d+)\s*\|\s*`([a-z][a-z0-9_.]*)`\s*\|\s*([a-z]+)\s*\|\s*"
    r"`(closed_set_labels|structured|freeform)`\s*\|\s*\*{0,2}(golden|none)\*{0,2}\s*\|\s*(.+?)\s*\|$"
)


def _rows() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        m = _ROW.match(line.strip())
        if m:
            out.append({
                "no": m.group(1), "code": m.group(2), "modality": m.group(3),
                "kind": m.group(4), "profile": m.group(5), "generation": m.group(6),
            })
    return out


class TestCatalogShape(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = _rows()

    def test_exactly_52(self) -> None:
        self.assertEqual(len(self.rows), EXPECTED_TOTAL,
                         f"카탈로그 항목이 {len(self.rows)}개다 (52 여야 한다)")

    def test_numbering_is_1_to_52_without_gaps(self) -> None:
        """번호가 1..52 로 빠짐없이 이어지는가. 표를 손으로 고치면 여기가 먼저 깨진다."""
        self.assertEqual([r["no"] for r in self.rows],
                         [str(i) for i in range(1, EXPECTED_TOTAL + 1)])

    def test_codes_unique(self) -> None:
        codes = [r["code"] for r in self.rows]
        dupes = {c for c in codes if codes.count(c) > 1}
        self.assertFalse(dupes, f"code 가 중복이다: {sorted(dupes)}")

    def test_kind_counts_match_summary(self) -> None:
        counts: dict[str, int] = {}
        for r in self.rows:
            counts[r["kind"]] = counts.get(r["kind"], 0) + 1
        self.assertEqual(counts, EXPECTED_BY_KIND)


class TestGoldenOnlyOnScoreable(unittest.TestCase):
    """「잴 수 없는 것에 점수를 붙이지 않는다」를 문서·앱·마이그레이션 세 곳에서 본다."""

    def test_catalog_has_no_freeform_golden(self) -> None:
        bad = [r["code"] for r in _rows() if r["kind"] == "freeform" and r["profile"] == "golden"]
        self.assertFalse(bad, f"freeform 인데 golden 이다: {bad}")

    def test_app_source_rejects_freeform_golden(self) -> None:
        """앱 소스에 그 분기가 **있는가** — 이 환경엔 `psycopg` 가 없어 import 를 못 한다.

        **주석을 걷어내고 본다.** 그러지 않으면 「왜 막는지」 설명해 둔 주석이 검사를
        만족시켜, 정작 `raise` 를 지워도 통과한다 — 변이 검사에서 실제로 그렇게 새어 나갔다.
        실제 호출 검사는 아래가 하고, 그건 의존성이 있는 환경에서만 돈다.
        """
        src = (ROOT / "apps" / "core" / "app" / "capability.py").read_text(encoding="utf-8")
        code_only = "\n".join(
            line.split("#", 1)[0] for line in src.splitlines()
        )
        self.assertIn('output_kind == "freeform"', code_only,
                      "capability.py 에 freeform 분기가 없다")
        self.assertIn("ck_capability_golden_scoreable", code_only,
                      "거절 메시지가 어느 제약인지 말하지 않는다")

    @unittest.skipUnless(_HAS_PSYCOPG, "psycopg 없음 — 의존성 있는 환경에서만 돈다")
    def test_app_call_rejects_freeform_golden(self) -> None:
        """앱이 **DB 에 가기 전에** 거절하고, 어느 제약인지 말해 준다.

        `conn=None` 로 부른다 — 검증이 `conn` 을 쓰기 전에 끝나야 통과하는 검사이기도 하다.
        """
        from app.capability import create_capability

        with self.assertRaises(ValueError) as ctx:
            create_capability(
                None,  # type: ignore[arg-type]
                code="text.summarize", version=1, name="x", description=None,
                input_schema={}, output_schema={},
                output_kind="freeform", compute_tier="M", trust_domain_min="team",
                mvp_eligible=False, quality_profile="golden",
                golden_set_ref="g", golden_set_sha256="a" * 64,
                golden_set_size=40, golden_metrics={"min_accuracy": 0.68},
            )
        self.assertIn("ck_capability_golden_scoreable", str(ctx.exception))

    @unittest.skipUnless(_HAS_PSYCOPG, "psycopg 없음 — 의존성 있는 환경에서만 돈다")
    def test_app_call_still_allows_structured_golden(self) -> None:
        """`structured` 는 막지 않는다 — 채점기가 없을 뿐 원리적으로는 잴 수 있다.

        여기서는 `conn=None` 때문에 결국 실패하지만, **freeform 과 같은 이유로는** 아니어야 한다.
        이 구분이 없으면 위 검사가 「golden 이면 다 막힌다」로 조용히 넓어져도 통과한다.
        """
        from app.capability import create_capability

        with self.assertRaises(Exception) as ctx:
            create_capability(
                None,  # type: ignore[arg-type]
                code="text.rank", version=1, name="x", description=None,
                input_schema={}, output_schema={},
                output_kind="structured", compute_tier="M", trust_domain_min="team",
                mvp_eligible=False, quality_profile="golden",
                golden_set_ref="g", golden_set_sha256="a" * 64,
                golden_set_size=40, golden_metrics={"min_accuracy": 0.68},
            )
        self.assertNotIn("ck_capability_golden_scoreable", str(ctx.exception))

    def test_migration_adds_the_check(self) -> None:
        """**주석을 걷어내고** 본다.

        처음 쓸 때 `assertNotIn("NOT VALID", …)` 가 「NOT VALID 로 우회하지 않는다」라고
        적어 둔 **주석을 잡았다.** 설명을 지워야 통과하는 검사가 될 뻔했다 — `test_ui_invariants`
        에서 한 번 겪은 것과 같은 모양이라, 여기서는 처음부터 `strip_sql_comments` 를 쓴다.
        """
        from app.migrate_lint import strip_sql_comments

        raw = MIGRATION.read_text(encoding="utf-8")
        sql = strip_sql_comments(raw)
        self.assertIn("ck_capability_golden_scoreable", sql)
        self.assertIn("ADD CONSTRAINT", sql)
        # 제약 **추가**만 (절대규칙 1). 삭제·완화가 섞여 들어오면 여기서 걸린다.
        self.assertNotIn("DROP CONSTRAINT", sql)
        self.assertNotIn("NOT VALID", sql)


class TestIsolationLock(unittest.TestCase):
    def test_locked_capabilities_marked_v2(self) -> None:
        """산출물이 실행되는 셋은 v제품-2(격리) 세대로 표시돼 있어야 한다."""
        by_code = {r["code"]: r for r in _rows()}
        for code in LOCKED_UNTIL_ISOLATION:
            self.assertIn(code, by_code, f"{code} 가 카탈로그에 없다")
            self.assertIn("v제품-2", by_code[code]["generation"],
                          f"{code} 의 유통 세대가 v제품-2 가 아니다 — 격리 전에 열린다")

    def test_av_absence_is_stated(self) -> None:
        """「AV 가 있다」고 쓰지 않는다. 없다고 적힌 문장이 사라지면 실패한다."""
        text = CATALOG.read_text(encoding="utf-8")
        self.assertIn("바이러스 검사(AV)는 없다", text)


if __name__ == "__main__":
    unittest.main()
