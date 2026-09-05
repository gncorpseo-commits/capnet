r"""체크리스트·런북의 **세면 나오는 숫자**가 실물과 같은가 (배치 B #84).

## 왜 있는가

`contest-submission-checklist.md` 와 `shoot-day-runbook.md` 는 8/25 에 패킹하는 사람이
**그대로 믿고 실행**하는 문서다. 거기 적힌 N 이 낡으면 그 사람은 낡은 N 을 확인하고 지나간다.
`9/9`·`51/51`·가중치 `9종`·`완료 — 18개 적용` 은 이미 다른 검사가 본다. **나머지**를 전수했다.

## 실측 (2026-09-06)

| 문서의 숫자 | 실물 | 어디서 세나 |
|---|---|---|
| 마이그레이션 **18개 적용** (체크리스트) | 18 | `migrations/*.sql` |
| 위반 **6종** · `×6` · **6건** (둘 다) | 6 | `demo_violations.sql` 의 `RAISE NOTICE` |
| 위반 **14종 실측 표** (체크리스트) | 14 | `docs/error/pg-violations.md` 표 행 |
| sanity **3종** (둘 다) | 3 | `sanity.sh` 의 `for mode in …` |
| 데모 골든 **N=40** (런북) | 40 | `docs/spec/golden/manifest-image-classify-v1.json` |
| 프로브 라우트 **5 → 24** (둘 다) | 24 | `prod_room.sh` 의 `chk "무인증 …"` 단건 6 + 루프 18 |
| 능력 **6종** 데모 재현 (체크리스트 169) | **9** — 낡았다 → 「당시 6 · 지금 9」로 고쳤다 | `capability-catalog.md` 행 |

## 재현

```bash
python3 -m unittest tests.test_ops_docs_counted_claims
```
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "ops" / "contest-submission-checklist.md"
RUNBOOK = ROOT / "docs" / "ops" / "shoot-day-runbook.md"
DOCS = (CHECKLIST, RUNBOOK)


def _text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _migrations() -> int:
    return len(list((ROOT / "migrations").glob("*.sql")))


def _violation_demos() -> int:
    return len(re.findall(r"RAISE NOTICE", _text(ROOT / "scripts" / "demo_violations.sql")))


def _violation_table_rows() -> int:
    return len(re.findall(r"^\| \d+", _text(ROOT / "docs" / "error" / "pg-violations.md"), re.M))


def _sanity_modes() -> int:
    m = re.search(r"^for mode in ((?:\w+ ?)+); do", _text(ROOT / "scripts" / "sanity.sh"), re.M)
    assert m, "sanity.sh 의 for mode 를 못 찾았다"
    return len(m.group(1).split())


def _demo_golden_cases() -> int:
    doc = json.loads(_text(ROOT / "docs" / "spec" / "golden" / "manifest-image-classify-v1.json"))
    return len(doc["cases"])


def _unauth_probes() -> int:
    lines = _text(ROOT / "scripts" / "prod_room.sh").splitlines()
    singles = sum(1 for l in lines if re.match(r'^\s*chk "무인증 (?!GET)', l))
    loop, i = 0, 0
    while i < len(lines):
        if lines[i].startswith("for path in"):
            j = i + 1
            while "; do" not in lines[j]:
                j += 1
            paths = [l for l in lines[i + 1:j + 1] if re.match(r'^\s*"/v1', l)]
            if "무인증" in " ".join(lines[j:j + 6]):
                loop += len(paths)
            i = j
        i += 1
    return singles + loop


def _capabilities() -> int:
    return len(re.findall(r"^\| `?[a-z_]+\.[a-z_]+", _text(ROOT / "docs" / "spec" / "capability-catalog.md"), re.M))


class TestCountedClaimsMatchTheThingCounted(unittest.TestCase):
    def test_migration_count_in_checklist(self) -> None:
        self.assertIn(f"마이그레이션 **{_migrations()}개 적용", _text(CHECKLIST))

    def test_violation_demo_count(self) -> None:
        n = _violation_demos()
        self.assertIn(f"위반 {n}종", _text(CHECKLIST))
        body = _text(RUNBOOK)
        self.assertIn(f"위반 {n}종", body)
        self.assertIn(f"×{n}", body)
        self.assertIn(f"**{n}건**", body)

    def test_violation_table_rows(self) -> None:
        self.assertIn(f"위반 {_violation_table_rows()}종 실측 표", _text(CHECKLIST))

    def test_sanity_mode_count(self) -> None:
        n = _sanity_modes()
        self.assertIn(f"sanity {n}종", _text(CHECKLIST))
        self.assertIn(f"{n}종 **FAILED**", _text(RUNBOOK))

    def test_demo_golden_n(self) -> None:
        self.assertIn(f"골든 N={_demo_golden_cases()}", _text(RUNBOOK))

    def test_probe_route_count(self) -> None:
        n = _unauth_probes()
        for doc in DOCS:
            with self.subTest(doc=doc.name):
                self.assertRegex(_text(doc), rf"5 ?→ ?{n}\b", f"{doc.name} 의 프로브 라우트 수가 {n} 이 아니다")

    def test_capability_count_next_to_the_old_six(self) -> None:
        """169행은 당시 기록이라 지우지 않는다 — 대신 **지금 값**이 옆에 붙어 있어야 한다."""
        n = _capabilities()
        self.assertIn(f"지금은 **{n}종**", _text(CHECKLIST))


class TestProbeActuallyCounts(unittest.TestCase):
    def test_todays_values(self) -> None:
        got = {
            "migrations": _migrations(), "violation_demos": _violation_demos(),
            "violation_rows": _violation_table_rows(), "sanity": _sanity_modes(),
            "golden": _demo_golden_cases(), "probes": _unauth_probes(), "capabilities": _capabilities(),
        }
        self.assertEqual({"migrations": 18, "violation_demos": 6, "violation_rows": 14, "sanity": 3,
                          "golden": 40, "probes": 24, "capabilities": 9}, got, got)


if __name__ == "__main__":
    unittest.main()
