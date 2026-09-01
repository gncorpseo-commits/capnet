"""EuroSAT 아카이브 sha256 이 **열 곳에서 같은 값인가**.

## 왜 있는가

이 값은 **재현의 출발점**이다. 심사위원이든 다음 사람이든 `EuroSAT_RGB.zip` 을 받아
이 sha 로 대조한 뒤에야 골든셋·게이트·`acc=0.8500` 이 뜻을 갖는다.
`NOTICE` 가 그 값을 적어 두고 있고, 그것이 곧 **배포 문서의 약속**이다.

그런데 지금 같은 값이 **열 곳**에 손으로 적혀 있고, 서로 같은지 보는 검사가 없었다.

`check_golden_sha.py` 가 막는 사고와 **똑같은 모양**이다 — 그때는
「매니페스트만 교체되고 선언부 네 곳이 따라오지 않아 sha 가 세 갈래로 갈렸다.
사슬이 self-consistent 라서 데모는 그대로 통과했다 — **조용히 틀렸다**」.

데이터셋 sha 는 아직 안 갈렸다. **갈리기 전에 막는다.**

## 정본

`docs/spec/golden/eurosat-rgb.json` 의 `archive_sha256`.
데이터셋 선언이 한곳에 모여 있는 유일한 파일이라 여기를 정본으로 삼는다.

## 왜 「한 곳으로 합치기」를 하지 않았나

열 곳 가운데 `seed.sql`·`update_thresholds.sql` 은 **DB 시드**라 리터럴이어야 하고,
`download_eurosat.{sh,ps1}` 은 **의존성 없이 도는 셸**이라 JSON 을 읽게 만들면
그 성질을 잃는다. `NOTICE` 는 배포 문서다.

**그래서 인라인은 그대로 두고 대조만 한다** — 이 저장소가 골든셋 sha 에 쓰는 방식과 같다.

## 무엇을 안 보나

**개수를 못박지 않는다** — 새 자리가 늘 수 있다. 다만 **줄어들면** 걸린다
(하한을 둔다). 새로 인라인하는 자리는 아래 목록에 같이 적는다.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON_FILE = ROOT / "docs" / "spec" / "golden" / "eurosat-rgb.json"

# 값을 인라인해 둔 자리. **왜 인라인인지**를 같이 적는다 — 합치자는 제안이 올 때
# 되풀이해 조사하지 않게.
DECLARED_IN = {
    "NOTICE": "배포 문서 — 받는 사람이 여기서 대조한다",
    "apps/core/sql/seed.sql": "DB 시드 — 리터럴이어야 한다",
    "apps/core/sql/update_thresholds.sql": "같음",
    "scripts/download_eurosat.sh": "의존성 없이 도는 셸 — JSON 파서를 넣지 않는다",
    "scripts/download_eurosat.ps1": "같음 (Windows)",
    "scripts/extract_golden.py": "골든셋 추출 전 아카이브 검증",
    "docs/spec/golden/image-classify-v1.md": "골든셋 명세",
    "docs/spec/golden/manifest-image-classify-v1.json": "매니페스트",
    "docs/ops/contest-report-draft.md": "결과보고서 초안",
}

HEX64 = re.compile(r"\b[0-9a-f]{64}\b")


def canonical() -> str:
    doc = json.loads(CANON_FILE.read_text(encoding="utf-8"))
    sha = doc.get("archive_sha256")
    assert isinstance(sha, str) and len(sha) == 64, f"정본 sha 를 못 읽었다: {sha!r}"
    return sha


class TestDatasetShaIsOneValue(unittest.TestCase):
    def test_every_declaration_site_agrees(self) -> None:
        sha = canonical()
        wrong: list[str] = []
        for rel in sorted(DECLARED_IN):
            p = ROOT / rel
            if not p.is_file():
                wrong.append(f"{rel} (파일 없음)")
                continue
            if sha not in p.read_text(encoding="utf-8"):
                wrong.append(rel)
        self.assertEqual(
            wrong, [], f"정본과 다른(또는 사라진) 선언 자리: {wrong}"
        )

    def test_no_stray_copy_disagrees(self) -> None:
        """`EuroSAT_RGB` 를 말하는 **같은 줄**에 다른 64-hex 가 있으면 갈린 것이다."""
        sha = canonical()
        bad: list[str] = []
        for rel in sorted(DECLARED_IN):
            p = ROOT / rel
            if not p.is_file():
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if "EuroSAT_RGB" not in line:
                    continue
                for h in HEX64.findall(line):
                    if h != sha:
                        bad.append(f"{rel}:{i} {h[:12]}…")
        self.assertEqual(bad, [], f"아카이브 줄에 다른 sha 가 있다: {bad}")

    def test_site_list_did_not_shrink(self) -> None:
        """자리가 **줄면** 어딘가에서 지워졌다는 뜻이다. 느는 것은 막지 않는다."""
        self.assertGreaterEqual(len(DECLARED_IN), 9, "선언 자리 목록이 줄었다")

    def test_probe_reads_a_real_sha(self) -> None:
        self.assertRegex(canonical(), r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
