"""표 추출 실행기 — **새 가중치 0** (단계 6 ④).

## 무엇을 하나

평문 표를 셀로 파싱하고(결정적), **각 열의 값 종류를 추론한다**(모델).
출력은 `columns`(열별 추론 타입)와 `rows`(셀 문자열).

## 왜 새 가중치가 없나

열 타입 추론은 `text.classify` 가 이미 하는 일이다 — 문자열의 **구조 종류**
(`email`·`url`·`ipv4`·`uuid`·`iso_date`·`plain`). 그래서 **`text_struct_scratch.safetensors`
를 그대로 쓴다.** 같은 아키텍처를 다른 능력에 붙였을 뿐이고, 증적에는 `arch` 와
`weights_sha256` 이 사실대로 남는다.

## 열 타입은 **다수결**이고, 그 사실을 노출한다

열마다 셀을 분류해 가장 많이 나온 종류를 고른다. 얼마나 우세했는지를 `support` 로
같이 내보낸다 — 3/3 과 2/3 을 같은 것처럼 보이게 하지 않는다.

## 무엇을 주장하지 않는가

**표 이해도.** 머리글 판별은 「숫자가 하나도 없으면 머리글」이라는 느슨한 규칙이고,
그래서 결과에 `header_detected` 로 **그대로 노출한다.** `quality_profile='none'` 이라
골든셋도 채점도 없다.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.limits import MAX_PARAMS_DEFAULT
from app.preprocess import resolve_extract_preprocess
from app.table_features import looks_like_header, parse_table
from app.text_features import features


def extract_table(
    weights_path: str,
    doc_path: str,
    *,
    arch: str | None = None,
    max_params: int | None = None,
    preprocess: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`{"columns": [...], "rows": [...], "header_detected": bool}` 를 돌려준다."""
    import torch
    from safetensors.torch import load_file

    from app.tiny_text import TEXT_LABELS, TinyTextClassifier

    if arch and arch != "TinyTableTyper":
        raise ValueError(f"unknown table arch {arch!r}; known=['TinyTableTyper']")

    model = TinyTextClassifier()
    model.load_state_dict(load_file(weights_path))
    model.eval()

    params = sum(p.numel() for p in model.parameters())
    cap = max_params or MAX_PARAMS_DEFAULT
    if params > cap:
        from app.infer_text import TextResourceLimitExceeded

        raise TextResourceLimitExceeded(f"params {params} > max_params {cap}")

    encoding, max_rows, max_cols = resolve_extract_preprocess(preprocess)
    rows = parse_table(doc_path, encoding=encoding, max_rows=max_rows, max_cols=max_cols)

    header = looks_like_header(rows[0])
    body = rows[1:] if header and len(rows) > 1 else rows

    width = len(rows[0])
    columns: list[dict[str, Any]] = []
    for i in range(width):
        cells = [r[i] for r in body if r[i]]
        if not cells:
            # 값이 하나도 없는 열. 추론할 근거가 없으므로 그렇게 적는다.
            columns.append({"index": i, "type": "plain", "support": 0.0})
            continue
        with torch.no_grad():
            xb = torch.tensor([features(c) for c in cells], dtype=torch.float32)
            idxs = model(xb).argmax(1).tolist()
        counts = Counter(TEXT_LABELS[i2] for i2 in idxs)
        kind, n = counts.most_common(1)[0]
        columns.append({
            "index": i,
            "type": kind,
            # 얼마나 우세했나. 3/3 과 2/3 을 같게 보이지 않게 한다.
            "support": round(n / len(cells), 4),
        })
        if header:
            columns[-1]["name"] = rows[0][i]

    return {"columns": columns, "rows": body, "header_detected": header}
