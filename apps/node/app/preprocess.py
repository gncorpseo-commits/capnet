"""전처리 선언 해석 — **torch 없이** 돈다.

`infer.py` 에 있던 것을 옮겼다. 이유는 하나다: 계약 게이트의 **선언 검사 경로**(C2)가
torch 없는 Node(`s-public` — `apps/node/Dockerfile` 이 조건부로만 설치한다)에서도
돌아야 하는데, `infer.py` 는 모듈 최상단에서 `import torch` 를 한다.

그래서 「선언을 읽는 일」과 「그 선언으로 추론하는 일」을 나눴다.
읽는 쪽은 순수 함수라 의존성이 필요 없다. `infer.py` 는 여기서 가져다 쓴다.

전처리 어휘 자체(모달리티별 키)는 `docs/spec/capability-catalog.md` §4 가 정본이다.
"""

from __future__ import annotations

from typing import Any

# 계약이 전처리를 선언하기 전의 값 (D3 · 32×32 RGB). `image.classify` 의 선언값과 같다 —
# 0014 가 계약에 적어 넣은 것이 바로 이 값이라, 골든 경로의 픽셀 처리는 바뀌지 않는다.
DEFAULT_PREPROCESS: dict[str, Any] = {"resize": [32, 32], "colorspace": "RGB"}


def resolve_preprocess(declared: dict[str, Any] | None) -> tuple[tuple[int, int], str]:
    """계약 선언을 (resize, colorspace) 로 푼다. 없으면 종전 기본값."""
    spec = declared or DEFAULT_PREPROCESS
    size = spec.get("resize") or DEFAULT_PREPROCESS["resize"]
    if not (isinstance(size, (list, tuple)) and len(size) == 2):
        raise ValueError(f"preprocess.resize 형식이 아니다: {size!r}")
    w, h = int(size[0]), int(size[1])
    if w < 1 or h < 1:
        raise ValueError(f"preprocess.resize 가 양수가 아니다: {size!r}")
    space = str(spec.get("colorspace") or DEFAULT_PREPROCESS["colorspace"])
    return (w, h), space


# ── 텍스트 (단계 5) ────────────────────────────────────────────────────────
#
# 카탈로그 §4 의 text 어휘. **토크나이저를 넣지 않는다** — 모델마다 달라 계약이
# 검증할 수 없고, 검증 못 하는 칸은 「선언은 있는데 아무도 확인 안 하는 칸」이 된다
# (`preprocess` 가 0013 에서 정확히 그 상태였다). 길이는 러너가 셀 수 있는 **문자 수**로.
DEFAULT_TEXT_PREPROCESS: dict[str, Any] = {
    "encoding": "utf-8",
    "normalize": "NFC",
    "max_chars": 8000,
}

_NORMALIZE_FORMS = frozenset({"NFC", "NFD", "NFKC", "NFKD"})


def resolve_text_preprocess(
    declared: dict[str, Any] | None,
) -> tuple[str, str, int | None]:
    """텍스트 전처리 선언을 (encoding, normalize_form, max_chars) 로 푼다.

    이미지 쪽 `resolve_preprocess` 와 같은 규약이다 — 형식이 망가져 있으면 **던진다.**
    계약 게이트가 그 예외를 실패로 기록한다. 조용히 기본값으로 떨어지면 「선언한 대로
    돌았다」가 거짓이 된다.
    """
    spec = declared or DEFAULT_TEXT_PREPROCESS
    encoding = str(spec.get("encoding") or DEFAULT_TEXT_PREPROCESS["encoding"])

    form = str(spec.get("normalize") or DEFAULT_TEXT_PREPROCESS["normalize"])
    if form not in _NORMALIZE_FORMS:
        raise ValueError(f"preprocess.normalize 는 {sorted(_NORMALIZE_FORMS)} 중 하나여야 한다: {form!r}")

    raw_max = spec.get("max_chars", DEFAULT_TEXT_PREPROCESS["max_chars"])
    if raw_max is None:
        return encoding, form, None
    max_chars = int(raw_max)
    if max_chars < 1:
        raise ValueError(f"preprocess.max_chars 가 양수가 아니다: {raw_max!r}")
    return encoding, form, max_chars


def is_text_preprocess(declared: dict[str, Any] | None) -> bool:
    """선언이 **텍스트 어휘**인가. 모달리티 디스패치의 보조 판별이다.

    정본 판별은 `arch → 모달리티`(`ARCH_MODALITY`)다 — 이건 계약만 있고 arch 를
    모를 때(legacy)의 차선책이며, 그 사실을 호출부에 적어 둔다.
    """
    if not declared:
        return False
    return any(k in declared for k in ("encoding", "max_chars")) and "resize" not in declared


# ── 표/시계열 (단계 6 ②) ───────────────────────────────────────────────────
#
# 카탈로그 §4 의 table 어휘 + 시계열이 실제로 쓰는 `window`.
# `window` 를 계약에 두는 이유: 모델이 보는 과거 길이가 바뀌면 **같은 가중치가
# 다른 것을 보게 된다.** 러너가 그대로 셀 수 있는 값이라 계약이 검증할 수 있다
# (토크나이저를 안 넣은 것과 같은 기준).
DEFAULT_TABLE_PREPROCESS: dict[str, Any] = {
    "encoding": "utf-8",
    "max_rows": 10000,
    "window": 24,
}


def resolve_table_preprocess(
    declared: dict[str, Any] | None,
) -> tuple[str, int | None, int]:
    """표/시계열 전처리 선언을 (encoding, max_rows, window) 로 푼다.

    이미지·텍스트와 같은 규약이다 — 형식이 망가져 있으면 **던진다.**
    조용히 기본값으로 떨어지면 「선언한 대로 돌았다」가 거짓이 된다.
    """
    spec = declared or DEFAULT_TABLE_PREPROCESS
    encoding = str(spec.get("encoding") or DEFAULT_TABLE_PREPROCESS["encoding"])

    raw_rows = spec.get("max_rows", DEFAULT_TABLE_PREPROCESS["max_rows"])
    max_rows = None if raw_rows is None else int(raw_rows)
    if max_rows is not None and max_rows < 1:
        raise ValueError(f"preprocess.max_rows 가 양수가 아니다: {raw_rows!r}")

    window = int(spec.get("window") or DEFAULT_TABLE_PREPROCESS["window"])
    if window < 2:
        raise ValueError(f"preprocess.window 는 2 이상이어야 한다: {window}")
    return encoding, max_rows, window
