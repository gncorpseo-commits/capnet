r"""`ALLOWED_DATASET_IDS` 가 **쓰이는 곳들과 어긋나지 않는가** (큐 #66 · D8′).

## 왜 있는가

`datasetId` 는 세 군데에 흩어져 있다 — 앱의 allowlist, 시드·데모의 **작업 페이로드**,
화면(`call.html`)이 보여 주는 목록. 하나만 바뀌면 나머지가 조용히 낡는다.

## 갈림이 하나 있다 — **`inputId` 가 있으면 allowlist 를 안 본다**

`#205`(D8′ · Decision A)가 연 자리다. 바이트가 이미 Core 를 거쳤으면 `datasetId` 를 다시
묻는 것은 통제를 더하지 않고 **거짓말을 시킨다** — 텍스트 작업에 맞는 이름이 없어서
`eurosat-rgb` 를 적어야 했고, 그러면 증적에 **없던 데이터셋**이 남았다.

**이 갈림을 모르는 검사는 결함 열 건을 지어낸다.**

```text
datasetId 페이로드            21
  ├ inputId 있음 (자유 이름)  10   전부 "text-demo" — 참인 이름이고 증적에 그대로 남는다
  └ inputId 없음 (allowlist)  11   전부 "eurosat-rgb"
allowlist 밖인데 inputId 없음  0   ✅
```

`#218` 이 `$node_id` 문자열을 세어 「우회 일곱 건」이 될 뻔한 것과 같은 함정이라,
여기서는 **페이로드 단위**로 보고 `inputId` 유무를 함께 읽는다.

## 무엇을 고정하나

1. `inputId` **없는** 작업 페이로드의 `datasetId` 는 전부 `ALLOWED_DATASET_IDS` 안이다
2. `GET /v1/datasets` 가 **그 집합 그대로** 낸다 (화면이 읽는 값)
3. 시드의 `golden_metrics.dataset.id` 와 골든 핀 파일 이름이 그 집합과 맞는다
4. 세는 대상이 비지 않는다

## 무엇을 안 보나

`inputId` 가 있는 페이로드의 이름. **그건 자유이고, 그게 D8′ 의 요지다.**
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = ROOT / "apps" / "core" / "app" / "allowlist.py"
MAIN = ROOT / "apps" / "core" / "app" / "main.py"
SEED = ROOT / "apps" / "core" / "sql" / "seed.sql"
GOLDEN = ROOT / "docs" / "spec" / "golden"

SKIP_DIRS = {".git", "node_modules", "__pycache__", "artifacts", "data"}
PAYLOAD = re.compile(r"\{[^{}]*\\?\"datasetId\\?\"[^{}]*\}")
DATASET_ID = re.compile(r"\\?\"datasetId\\?\"\s*:\s*\\?\"([a-z0-9._-]+)")


def allowed() -> set[str]:
    line = ALLOWLIST.read_text(encoding="utf-8").split("ALLOWED_DATASET_IDS")[1].split("\n")[0]
    return set(re.findall(r'"([a-z0-9._-]+)"', line))


def payloads() -> list[tuple[str, str, bool]]:
    """`(파일, datasetId, inputId 가 같이 있는가)`."""
    out: list[tuple[str, str, bool]] = []
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in (".sql", ".py", ".sh", ".html") or not path.is_file():
            continue
        if SKIP_DIRS & set(path.parts):
            continue
        for m in PAYLOAD.finditer(path.read_text(encoding="utf-8", errors="ignore")):
            blob = m.group(0)
            found = DATASET_ID.search(blob)
            if found:
                out.append((path.relative_to(ROOT).as_posix(), found.group(1),
                            "inputId" in blob))
    return out


class TestUncontrolledPayloadsStayInsideTheAllowlist(unittest.TestCase):
    def test_no_payload_without_input_id_leaves_the_allowlist(self) -> None:
        """**여기가 핵심이다.** 그 경로에서만 allowlist 가 통제다."""
        got = payloads()
        self.assertTrue(got, "datasetId 페이로드를 하나도 못 찾았다")
        allow = allowed()
        bad = sorted({f"{p}: {d}" for p, d, has_input in got
                      if not has_input and d not in allow})
        self.assertEqual([], bad, f"allowlist 밖인데 inputId 가 없다: {bad}")

    def test_input_id_payloads_are_free_and_that_is_the_point(self) -> None:
        """자유 이름을 위반으로 세면 **결함 열 건을 지어낸다** (`#218` 함정)."""
        free = {d for _, d, has_input in payloads() if has_input}
        self.assertTrue(free, "inputId 를 쓰는 페이로드가 하나도 없다 — 전제가 바뀌었다")
        self.assertFalse(free & allowed(),
                         f"자유 이름이 allowlist 와 겹친다 — 갈림이 흐려졌다: {free & allowed()}")

    def test_the_branch_still_exists_in_core(self) -> None:
        """`if body.input_id is None:` 이 사라지면 위 갈림이 거짓이 된다."""
        self.assertTrue("if body.input_id is None:" in MAIN.read_text(encoding="utf-8"),
                        "main.py 에서 D8′ 갈림(if body.input_id is None)이 사라졌다")


class TestTheOtherTwoPlacesAgree(unittest.TestCase):
    def test_the_route_serves_the_allowlist_itself(self) -> None:
        """화면은 `GET /v1/datasets` 를 읽는다 — 그 값이 allowlist 여야 한다."""
        served = 'return {"items": sorted(ALLOWED_DATASET_IDS)}'
        self.assertTrue(served in MAIN.read_text(encoding="utf-8"),
                        f"/v1/datasets 가 allowlist 를 그대로 내지 않는다: «{served}»")

    def test_seed_golden_metrics_names_an_allowed_dataset(self) -> None:
        ids = set(re.findall(r'"dataset"\s*:\s*\{"id"\s*:\s*"([a-z0-9._-]+)"',
                             SEED.read_text(encoding="utf-8")))
        self.assertTrue(ids, "시드에서 golden_metrics.dataset.id 를 못 찾았다")
        self.assertTrue(ids <= allowed(), f"시드가 allowlist 밖 데이터셋을 적는다: {ids - allowed()}")

    def test_the_golden_pin_file_is_named_after_it(self) -> None:
        """핀 파일 이름이 갈리면 README 의 링크가 죽는다."""
        pins = {p.stem for p in GOLDEN.glob("*.json")}
        self.assertTrue(allowed() <= pins,
                        f"allowlist 의 데이터셋에 핀 파일이 없다: {allowed() - pins}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_payloads_are_seen(self) -> None:
        self.assertGreaterEqual(len(payloads()), 15, len(payloads()))

    def test_both_kinds_are_present(self) -> None:
        kinds = {has_input for _, _, has_input in payloads()}
        self.assertEqual({True, False}, kinds, "한 종류만 보고 있다")

    def test_the_pin_file_parses(self) -> None:
        for name in allowed():
            with self.subTest(dataset=name):
                json.loads((GOLDEN / f"{name}.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
