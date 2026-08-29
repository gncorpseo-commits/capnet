"""`text.extract` 규칙 — 평문에서 **레이블된 필드**(`키: 값`)를 뽑는다.

## 무엇을 하나 · 무엇을 하지 않나

`text.ner` 은 **타입 있는 span**(email·url·ipv4·…)을 위치와 함께 찾는다 — 키가 없다.
`table.extract` 는 **격자**(행×열)를 읽는다.
여기는 그 둘 사이다 — 한 줄에 `이름: 값` 꼴로 **이름표가 붙어 있는** 것만 가져온다.

**자연어 이해를 주장하지 않는다.** 문장에서 사실을 뽑지 못하고, 값의 뜻도 모른다.
「`Date: 2026-08-29` 라는 줄이 있었다」까지만 말한다. 값의 타입 판정도 하지 않는다 —
그건 `text.classify` · `text.ner` 가 할 일이다.

## 규칙 (전부 여기 적는다 — 결과가 왜 그런지 설명 가능해야 한다)

1. **줄 단위**로만 본다. 여러 줄에 걸친 값은 이어 붙이지 않는다.
2. 구분자는 **첫 번째** `:` 또는 `=` 하나. 값 안의 구분자는 값의 일부다.
3. 앞머리 글머리표(`-` `*` `•` `·`)와 공백은 키에서 떼어 낸다.
4. **키에 글자가 하나도 없으면 버린다** — `12:30` 같은 시각을 필드로 읽지 않기 위해서다.
5. 구분자 바로 뒤가 `//` 면 버린다 — `https://…` 의 `https` 를 키로 읽지 않기 위해서다.
6. 키는 1..64자, 값은 strip 후 비어 있지 않아야 한다.
7. 같은 키가 여러 번 나오면 **전부 남긴다.** 마지막 것만 남기면 「한 번만 있었다」가 된다.

`start`·`end` 는 **값**의 위치다 (`text[start:end] == value`) — `text.ner` 과 같은 규약이라
증적을 사람이 대조할 수 있다.
"""

from __future__ import annotations

from typing import Any

# 앞머리 글머리표. 목록으로 적힌 필드를 흔히 본다.
_BULLETS = "-*•·\t "
_SEPARATORS = (":", "=")
MAX_KEY_CHARS = 64


def _first_separator(line: str) -> int:
    """가장 먼저 나오는 `:` 또는 `=` 의 위치. 없으면 -1."""
    found = [line.find(sep) for sep in _SEPARATORS]
    hits = [i for i in found if i >= 0]
    return min(hits) if hits else -1


def find_fields(text: str) -> list[dict[str, Any]]:
    """`{"key","value","line","start","end"}` 목록. 규칙은 모듈 docstring 참조."""
    out: list[dict[str, Any]] = []
    offset = 0
    for line_no, line in enumerate(text.split("\n")):
        line_start = offset
        offset += len(line) + 1  # 개행 한 칸

        sep = _first_separator(line)
        if sep < 0:
            continue

        # 5. URL 스킴을 키로 읽지 않는다.
        if line[sep + 1 : sep + 3] == "//":
            continue

        key = line[:sep].strip(_BULLETS).strip()
        # 4. 글자가 없는 키는 키가 아니다 (시각·비율·좌표).
        if not any(ch.isalpha() for ch in key):
            continue
        # 6. 길이 한도.
        if not key or len(key) > MAX_KEY_CHARS:
            continue

        rest = line[sep + 1 :]
        stripped = rest.strip()
        if not stripped:
            continue

        # 값의 위치 — 앞쪽 공백을 건너뛴 지점부터.
        value_start = line_start + sep + 1 + (len(rest) - len(rest.lstrip()))
        out.append(
            {
                "key": key,
                "value": stripped,
                "line": line_no,
                "start": value_start,
                "end": value_start + len(stripped),
            }
        )
    return out
