"""`text.rank` 규칙 — 질의 한 줄과 후보 여러 줄의 **어휘 겹침**으로 순위를 매긴다.

## 무엇을 하나 · 무엇을 하지 않나

`text.ner` 은 **타입 있는 span** 을 찾고, `text.extract` 는 **이름표가 붙은 필드**를 뽑고,
`table.extract` 는 **격자**를 읽는다. 여기는 그 어느 것도 아니다 — 후보 줄들을
**질의와 얼마나 같은 낱말을 쓰는가**로 줄 세운다.

**뜻을 모른다.** 어휘가 겹치는 정도만 센다 — 「자동차」와 「차량」은 **안 겹친다**.
동의어·어형 변화·문맥을 보지 않는다. 의미 유사도가 필요하면 `text.embed` 이고,
학습된 관련도가 필요하면 `retrieve.dense`·`retrieve.rerank` 다. 여기가 아니다.

**품질을 주장하지 않는다** — `quality_profile='none'` · 골든셋 없음.

## 규칙 (전부 여기 적는다 — 결과가 왜 그런지 설명 가능해야 한다)

1. **첫 번째 비어 있지 않은 줄이 질의**다. 그 뒤의 비어 있지 않은 줄들이 **후보**다.
   빈 줄은 어디에 있든 건너뛴다 (후보 번호를 밀지 않는다 — `line` 은 원본 줄 번호다).
2. 토큰은 **유니코드 글자·숫자의 연속**이다. 그 밖의 문자(공백·문장부호·`_`)는 경계다.
3. 토큰은 **소문자로 접는다.** 한글·숫자는 대소문자가 없어 그대로다.
4. 점수는 **자카드**다 — `|질의 ∩ 후보| / |질의 ∪ 후보|`. 0..1 · 소수 4자리 반올림.
   집합이라 **한 줄에 같은 낱말이 여러 번 나와도 한 번으로 센다** (길이가 점수를 밀지 않는다).
5. 정렬은 점수 **내림차순**, 동점이면 **원래 줄 번호 오름차순**이다.
   같은 입력이면 언제나 같은 순서가 나온다 — 순위에 우연이 없어야 증적이 뜻을 갖는다.
6. 질의에 토큰이 하나도 없으면 (기호만 있는 줄 등) **모든 후보가 0 점**이고
   순서는 원래 줄 순서다. 0 점을 「관련 없음」으로 **해석하지 않는다** — 낱말이 안 겹쳤을 뿐이다.

`overlap` 은 실제로 겹친 토큰을 정렬해 담는다. **왜 그 점수인지 사람이 대조**할 수 있어야
하기 때문이다 — `text.ner`·`text.extract` 가 `start`·`end` 를 주는 것과 같은 이유다.
"""

from __future__ import annotations

import re
from typing import Any

# 유니코드 글자·숫자의 연속. `[^\W_]` = 낱말 문자에서 밑줄을 뺀 것.
_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(line: str) -> set[str]:
    """규칙 2·3 — 글자·숫자 연속을 소문자로 접어 **집합**으로 돌려준다."""
    return {m.group(0).lower() for m in _TOKEN.finditer(line)}


def jaccard(a: set[str], b: set[str]) -> float:
    """규칙 4 — 합집합이 비면 0.0 (0 으로 나누지 않는다)."""
    union = a | b
    if not union:
        return 0.0
    return round(len(a & b) / len(union), 4)


def rank_lines(text: str) -> dict[str, Any]:
    """`{"query": ..., "ranking": [...]}` 을 돌려준다. 규칙은 모듈 docstring 참조."""
    query = ""
    query_tokens: set[str] = set()
    have_query = False
    scored: list[dict[str, Any]] = []

    for line_no, raw in enumerate(text.split("\n")):
        line = raw.strip()
        if not line:
            continue
        if not have_query:
            # 규칙 1 — 첫 번째 비어 있지 않은 줄이 질의다.
            query, query_tokens, have_query = line, tokenize(line), True
            continue
        tokens = tokenize(line)
        scored.append(
            {
                "line": line_no,
                "text": line,
                "score": jaccard(query_tokens, tokens),
                "overlap": sorted(query_tokens & tokens),
            }
        )

    # 규칙 5 — 점수 내림차순, 동점은 원래 줄 번호 오름차순.
    scored.sort(key=lambda r: (-r["score"], r["line"]))
    ranking = [
        {
            "rank": i + 1,
            "line": row["line"],
            "text": row["text"],
            "score": row["score"],
            "overlap": row["overlap"],
        }
        for i, row in enumerate(scored)
    ]
    return {"query": query, "ranking": ranking}
