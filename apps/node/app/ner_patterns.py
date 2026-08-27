"""규칙 기반 개체명 — `text.classify` 와 같은 구조 종류만 찾는다.

**품질을 주장하지 않는다.** 사람 이름·조직명·감정은 다루지 않는다 —
외부 NER 말뭉치 없이 정직하게 할 수 있는 범위만 `text.ner` 의 첫 구현이다.
"""

from __future__ import annotations

import re
from typing import Any

# `text.classify` 닫힌 라벨 중 **위치가 있는** 것만. `plain` 은 span 이 없다.
NER_LABELS = ("email", "url", "ipv4", "uuid", "iso_date")

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "email",
        re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    ),
    (
        "url",
        re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+"),
    ),
    (
        "uuid",
        re.compile(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        ),
    ),
    (
        "ipv4",
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    ),
    (
        "iso_date",
        re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    ),
)


def _valid_ipv4(text: str) -> bool:
    parts = text.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def find_entities(text: str) -> list[dict[str, Any]]:
    """겹치지 않는 span 목록. 우선순위는 `_PATTERNS` 순서."""
    used: list[tuple[int, int]] = []
    out: list[dict[str, Any]] = []

    def _free(start: int, end: int) -> bool:
        return all(end <= s or start >= e for s, e in used)

    for label, pat in _PATTERNS:
        for m in pat.finditer(text):
            start, end = m.start(), m.end()
            span = text[start:end]
            if label == "ipv4" and not _valid_ipv4(span):
                continue
            if not _free(start, end):
                continue
            used.append((start, end))
            out.append({
                "label": label,
                "start": start,
                "end": end,
                "text": span,
            })

    out.sort(key=lambda e: (e["start"], e["end"]))
    return out
