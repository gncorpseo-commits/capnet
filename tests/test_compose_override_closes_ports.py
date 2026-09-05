r"""`compose.prod.yaml` 의 **`!override` 가 정말 덮는가** (큐 #45).

## 왜 중요한가

제품 오버레이의 3번 주장은 「**postgres 를 호스트에 노출하지 않는다**」다. 그 주장 전체가
**한 태그**에 걸려 있다:

```yaml
  postgres:
    ports: !override []          # ← 이게 안 먹으면 5432 가 열린 채 남는다
```

Compose 의 기본 병합은 리스트를 **덧붙인다.** `ports: []` 만 쓰면 `compose.yaml` 의
`"5432:5432"` 가 **그대로 남는다.** `!override` 는 「덧붙이지 말고 갈아끼워라」는
지시이고, 그게 없거나 안 먹으면 **제품 배포가 조용히 DB 를 연다.**

## 실측 (2026-09-05 · Docker Compose v5.3.1)

데몬 없이 `config` 만 돌려 병합 결과를 봤다 (이 세션에는 데몬이 없다).

```bash
export POSTGRES_USER=u POSTGRES_PASSWORD=p POSTGRES_DB=d \
       DATABASE_URL=postgresql://u:p@postgres:5432/d
docker compose -f compose.yaml config                        | grep -c published:   # 5
docker compose -f compose.yaml -f compose.prod.yaml config    | grep -c published:   # 1
docker compose -f compose.yaml -f compose.prod.yaml config | grep 'published: "5432"' # 없음
```

| 무엇 | 결과 |
|---|---|
| `compose.yaml` 단독의 공개 포트 | **5** |
| `+ compose.prod.yaml` | **1** — `core:8000` 만 |
| postgres `5432` | **사라진다** ✅ |

**`!override` 는 덮는다.** 주장은 참이다.

## 그런데 문서가 요구 버전을 낮게 적고 있었다

`!override` 는 **Compose v2.24.0(2024-01)** 에서 들어왔다. README 는 「Compose v2」라고만
적었다 — v2.0–v2.23 은 그 태그를 모른다. 심사자가 그 버전으로 제품 오버레이를 띄우면
**postgres 가 열린 채**이거나 파싱이 깨진다. 「v2」와 「v2.24+」는 다른 말이다.

## 무엇을 고정하나

1. `compose.yaml` 에서 **호스트 포트를 여는 서비스**는 제품 오버레이에서
   `!override` 로 닫히거나, 열어 두는 이유가 적혀 있다
2. `!override` 를 쓰는 파일이 있으면 **문서가 최소 버전을 말한다**
3. 세는 대상이 비지 않는다

## 무엇을 안 보나

**실행 결과를 여기서 재지 않는다.** `docker compose config` 는 CLI 가 있어야 하고
CI 단위 잡에는 없다. 위 실측은 머리말에 명령과 함께 적었다 — 다시 낼 수 있다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "compose.yaml"
PROD = ROOT / "compose.prod.yaml"
README = ROOT / "README.md"
OPERATE = ROOT / "docs" / "guide" / "operate-production.md"

# `!override` 가 들어온 Compose 버전. 새 정책 숫자가 아니라 상류의 사실이다.
MIN_COMPOSE = "2.24"

# 제품에서도 열어 두는 서비스와 **그 이유**.
OPEN_IN_PROD = {
    "core": "제품 API 자체 — 이걸 닫으면 아무도 못 쓴다",
    "node-m-team": "profiles: demo — 제품 배포에서는 아예 안 뜬다",
    "node-s-team": "같음",
    "node-s-public": "같음",
}


def _services_with_ports(path: Path) -> dict[str, list[str]]:
    """`서비스 → 공개 포트 줄`. 들여쓰기만 보고 읽는다 (yaml 의존성 0)."""
    out: dict[str, list[str]] = {}
    service = None
    in_ports = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  ([a-z0-9][a-z0-9._-]*):\s*$", raw)
        if m:
            service, in_ports = m.group(1), False
            continue
        if re.match(r"^    ports:", raw):
            in_ports = True
            if service:
                out.setdefault(service, [])
            continue
        if in_ports and re.match(r"^      - ", raw):
            if service:
                out.setdefault(service, []).append(raw.strip())
            continue
        if raw.strip() and not raw.startswith("      "):
            in_ports = False
    return out


def _overridden(path: Path) -> set[str]:
    """제품 오버레이에서 `ports: !override` 를 받은 서비스."""
    out: set[str] = set()
    service = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  ([a-z0-9][a-z0-9._-]*):\s*$", raw)
        if m:
            service = m.group(1)
        elif re.match(r"^    ports:\s*!override", raw) and service:
            out.add(service)
    return out


class TestProdOverlayClosesWhatItClaims(unittest.TestCase):
    def test_every_open_port_is_closed_or_explained(self) -> None:
        """덧붙이기가 기본이라 `!override` 가 없으면 **열린 채 남는다**."""
        opened = _services_with_ports(BASE)
        self.assertTrue(opened, "compose.yaml 에서 포트를 여는 서비스를 못 찾았다")
        closed = _overridden(PROD)
        stray = sorted(s for s in opened if s not in closed and s not in OPEN_IN_PROD)
        self.assertEqual([], stray, f"제품에서 닫히지도 해명되지도 않은 포트: {stray}")

    def test_postgres_is_closed(self) -> None:
        """제품 오버레이의 3번 주장 — 이게 깨지면 DB 가 인터넷에 선다."""
        self.assertIn("postgres", _services_with_ports(BASE), "기준 파일이 바뀌었다")
        self.assertIn("postgres", _overridden(PROD),
                      "compose.prod.yaml 이 postgres 포트를 `!override` 로 안 닫는다")

    def test_the_excuses_are_real_services(self) -> None:
        known = set(_services_with_ports(BASE))
        ghosts = sorted(s for s in OPEN_IN_PROD if s not in known)
        self.assertEqual([], ghosts, f"없는 서비스를 해명하고 있다: {ghosts}")


class TestTheVersionRequirementIsWritten(unittest.TestCase):
    """`!override` 는 Compose **v2.24+** 다. 「v2」라고만 적으면 심사자가 연 채로 띄운다."""

    def test_prod_overlay_uses_the_tag(self) -> None:
        self.assertTrue("!override" in PROD.read_text(encoding="utf-8"),
                        "오버레이가 `!override` 를 안 쓴다 — 그럼 이 파일의 전제가 바뀐다")

    def test_readme_states_the_minimum(self) -> None:
        self.assertTrue(MIN_COMPOSE in README.read_text(encoding="utf-8"),
                        f"README 가 Compose {MIN_COMPOSE}+ 를 안 적는다")

    def test_operate_guide_states_the_minimum(self) -> None:
        self.assertTrue(MIN_COMPOSE in OPERATE.read_text(encoding="utf-8"),
                        f"운영 안내가 Compose {MIN_COMPOSE}+ 를 안 적는다")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_services_are_read(self) -> None:
        self.assertGreaterEqual(len(_services_with_ports(BASE)), 4,
                                sorted(_services_with_ports(BASE)))

    def test_reader_discriminates(self) -> None:
        """포트를 못 읽거나 아무거나 읽으면 위 전부가 공허하다."""
        opened = _services_with_ports(BASE)
        self.assertIn("postgres", opened)
        self.assertIn('- "5432:5432"', opened["postgres"])
        self.assertNotIn("migrate", opened)
        self.assertEqual({"postgres"}, _overridden(PROD))


if __name__ == "__main__":
    unittest.main()
