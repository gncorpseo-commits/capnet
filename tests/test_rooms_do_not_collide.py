r"""두 방(`clean_room` · `prod_room`)과 데모 스택이 **포트·프로젝트명으로 부딪히지 않는가** (배치 B #96).

## 왜 있는가

방은 「빈 볼륨에서 다시 올린다」이므로 데모 스택이 떠 있는 옆에서 돌아야 한다. 프로젝트명이 같으면
`compose down -v` 가 남의 볼륨을 지우고, 호스트 포트가 겹치면 `up` 이 실패하거나 — 더 나쁘게 —
**남의 Core 를 두들기고 통과**한다.

## 실측 (2026-09-06)

| 스택 | 프로젝트 | 호스트 포트 |
|---|---|---|
| 데모 `compose.yaml` | 디렉터리 이름 | 5432 · 8000 · 8001 · 8002 · 8003 |
| `clean_room.sh` | `capnet-cleanroom` | 18800 · 18801 — 나머지 셋(`postgres`·`s-team`·`s-public`)은 `!override []` |
| `prod_room.sh` | `capnet-prod` | 18830 · 18831 — `compose.prod.yaml` 이 전부 닫고 둘만 연다 |

세 집합은 서로 겹치지 않는다. 런북·README 의 `8000`·`8001` 은 데모 스택 이야기다.

## 재현

```bash
python3 -m unittest tests.test_rooms_do_not_collide
```
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

COMPOSE = ROOT / "compose.yaml"
ROOMS = {"clean_room": ROOT / "scripts" / "clean_room.sh", "prod_room": ROOT / "scripts" / "prod_room.sh"}


def _demo_ports() -> set[int]:
    body = hash_comment_free(COMPOSE)
    return {int(m) for m in re.findall(r'-\s*"(?:\$\{\w+:-)?(\d+)\}?:\d+"', body)}


def _demo_services_with_ports() -> set[str]:
    body = hash_comment_free(COMPOSE)
    out, cur = set(), None
    for ln in body.splitlines():
        m = re.match(r"^  (\w[\w-]*):\s*$", ln)
        if m:
            cur = m.group(1)
        if cur and re.match(r"^\s+ports:", ln):
            out.add(cur)
    return out


def _room(name: str) -> tuple[str, set[int], set[str]]:
    """(프로젝트명, 여는 호스트 포트, `ports: !override` 로 손댄 서비스)."""
    body = hash_comment_free(ROOMS[name])
    proj = re.search(r'^proj=(?:"\$\{\w+:-)?([a-z-]+)', body, re.M)
    assert proj, f"{name}: proj 를 못 찾았다"
    ports = {int(m) for m in re.findall(r'^(?:core|node)_port=(?:"\$\{\w+:-)?(\d+)', body, re.M)}
    touched = set(re.findall(r"^  ([\w-]+):\n\s+ports: !override", body, re.M))
    return proj.group(1), ports, touched


class TestNothingCollides(unittest.TestCase):
    def test_project_names_are_distinct_and_not_the_demo(self) -> None:
        names = {n: _room(n)[0] for n in ROOMS}
        self.assertEqual(2, len(set(names.values())), names)
        for n, proj in names.items():
            with self.subTest(room=n):
                self.assertNotIn(proj, ("capnet", ROOT.name), f"{n} 이 데모 프로젝트명을 쓴다")

    def test_host_ports_are_pairwise_disjoint(self) -> None:
        sets = {"demo": _demo_ports(), **{n: _room(n)[1] for n in ROOMS}}
        self.assertGreaterEqual(len(sets["demo"]), 4, sets["demo"])
        for n in ROOMS:
            self.assertEqual(2, len(sets[n]), sets[n])
        names = sorted(sets)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                with self.subTest(pair=(a, b)):
                    self.assertEqual(set(), sets[a] & sets[b], f"{a} 와 {b} 의 호스트 포트가 겹친다")

    def test_clean_room_overrides_every_demo_port(self) -> None:
        """데모 compose 에 `ports:` 가 있는 서비스는 clean_room 이 전부 다시 정한다 — 안 하면 5432 가 새로 뜬다."""
        touched = _room("clean_room")[2]
        self.assertEqual(_demo_services_with_ports(), touched, "clean_room 이 손대지 않은 포트가 있다")

    def test_prod_room_layers_the_closed_overlay(self) -> None:
        body = hash_comment_free(ROOMS["prod_room"])
        self.assertIn('-f "$root/compose.yaml" -f "$root/compose.prod.yaml" -f "$ov"', body)
        self.assertIn("ports: !override []", hash_comment_free(ROOT / "compose.prod.yaml"))


class TestDocsTalkAboutTheDemoPortsOnly(unittest.TestCase):
    def test_runbook_and_readme_use_demo_ports(self) -> None:
        room_ports = set().union(*(_room(n)[1] for n in ROOMS))
        for doc in (ROOT / "README.md", ROOT / "docs" / "ops" / "shoot-day-runbook.md"):
            with self.subTest(doc=doc.name):
                ports = {int(p) for p in re.findall(r"(?:127\.0\.0\.1|localhost):(\d{4,5})", doc.read_text(encoding="utf-8"))}
                self.assertTrue(ports, f"{doc.name} 에 주소가 없다")
                self.assertEqual(set(), ports & room_ports, f"{doc.name} 이 방의 포트를 데모처럼 적는다")


if __name__ == "__main__":
    unittest.main()
