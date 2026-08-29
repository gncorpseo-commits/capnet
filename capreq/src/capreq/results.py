"""Core `result_ref` → 화면 표시용 요약.

능력마다 결과 모양이 다르다 — `label`·`confidence` (분류) · `vector`/`forecast`
(임베딩·예측) · `entities` (NER) · `columns`·`rows` (표). 계약이 정한 칸 이름을
그대로 읽어 옮기기만 한다. **새 품질 주장은 하지 않는다** — 없는 칸은 없는 대로 둔다.
"""

from __future__ import annotations

import json
from typing import Any

# Core 가 증적용으로 항상 붙이는 칸 (`complete.py`). 결과 요약에서는 따로 뺀다.
_META_KEYS = frozenset({"dummy", "weights_sha256"})

# 계약이 정한 벡터 칸 이름. `complete.py` 의 `_output_key` 가 붙이는 값이다.
_VECTOR_KEYS = ("vector", "forecast", "embedding")

# 표 앞부분만 보여 준다. 벡터 128차원·행 1000개를 화면에 다 뿌리지 않는다.
VECTOR_HEAD = 8
TABLE_ROW_HEAD = 10

_TABLE_KEYS = frozenset({"columns", "rows", "header_detected"})
_LABEL_KEYS = frozenset({"label", "confidence"})


def parse_result_ref(source: Any) -> dict[str, Any] | None:
    """task dict · `result_ref` 문자열 · 이미 풀린 dict 중 무엇을 받아도 dict 를 돌려준다."""
    ref = source
    if isinstance(source, dict) and "result_ref" in source:
        ref = source.get("result_ref")
    if isinstance(ref, str):
        try:
            ref = json.loads(ref)
        except json.JSONDecodeError:
            return None
    return ref if isinstance(ref, dict) else None


def extract_label(source: Any) -> str | None:
    ref = parse_result_ref(source)
    if ref is None:
        return None
    lab = ref.get("label")
    return str(lab) if lab is not None else None


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def summarize_result(source: Any) -> dict[str, Any]:
    """표시용 요약. 있는 칸만 담는다 — 빈 dict 면 「보여 줄 결과가 없다」."""
    ref = parse_result_ref(source)
    if ref is None:
        return {}

    out: dict[str, Any] = {}

    if ref.get("label") is not None:
        out["label"] = str(ref["label"])
    if _is_number(ref.get("confidence")):
        out["confidence"] = float(ref["confidence"])

    ents = ref.get("entities")
    if isinstance(ents, list):
        out["entities"] = [e for e in ents if isinstance(e, dict)]

    for key in _VECTOR_KEYS:
        val = ref.get(key)
        if isinstance(val, list) and val and all(_is_number(v) for v in val):
            out["vector"] = {
                "name": key,
                "dim": len(val),
                "head": [float(v) for v in val[:VECTOR_HEAD]],
                "truncated": len(val) > VECTOR_HEAD,
            }
            break

    cols = ref.get("columns")
    rows = ref.get("rows")
    if isinstance(cols, list) and isinstance(rows, list):
        body = [r for r in rows if isinstance(r, list)]
        out["table"] = {
            "columns": cols,
            "rows": body[:TABLE_ROW_HEAD],
            "row_count": len(body),
            "truncated": len(body) > TABLE_ROW_HEAD,
            "header_detected": bool(ref.get("header_detected")),
        }

    if ref.get("dummy") is not None:
        out["dummy"] = bool(ref["dummy"])

    # 계약이 새 칸을 들고 오면 조용히 삼키지 말고 그대로 넘긴다.
    known = _META_KEYS | _LABEL_KEYS | _TABLE_KEYS | {"entities"} | set(_VECTOR_KEYS)
    other = {k: v for k, v in ref.items() if k not in known}
    if other:
        out["other"] = other

    return out
