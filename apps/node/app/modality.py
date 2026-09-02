"""모달리티가 **로컬 골든셋 폴백을 쓸 수 있는가.**

## 왜 따로 있나

`main._run` 안에 이렇게 적혀 있었다:

    elif modality in (
        "text", "text_embed", "series", "table_extract", "text_ner", "text_extract",
        "text_rank", "text_pii",
    ):
        raise HTTPException(400, "… Core 가 중개한 입력이 필요하다")
    else:
        cid = _case_id(input_ref)          # ← 로컬 골든셋(EuroSAT 이미지)으로 떨어진다

**포함식이라 기본값이 「골든 폴백」이었다.** 목록에 없으면 데모 데이터로 돈다.
오늘은 그 목록이 정확히 `ARCH_MODALITY` 값에서 이미지 둘을 뺀 것이라 맞다.
문제는 **자라는 방향**이다.

**새는 길은 하나다** — `ARCH_MODALITY` 에 새 모달리티를 더하고 **이 목록을 안 고치는**
것. 그러면 그 능력은 **사용자 입력을 요구하는 대신 로컬 골든 이미지로 떨어진다.**

> **다른 하나는 이미 막혀 있다 (실측).** 「arch 가 `ARCH_MODALITY` 에 없다」는 경우도
> `_modality_of` 가 `"image"` 로 떨어뜨리지만, 그 뒤 `build_model` 이
> `unknown arch …` 로 던지고 `_run` 이 **422** 로 바꾼다. 게다가
> `tests/test_text_modality` 가 `ARCH_REGISTRY == ARCH_MODALITY` 를 **이미 못박는다.**
> **조용한 오답이 아니라 시끄러운 실패다** — 과장하지 않는다.

[#154](https://github.com/gncorpseo-commits/capnet/pull/154)(빈 첨부 → 데모 데이터가
대신 돌았다)와 같은 모양이고, 손으로 적은 목록이 카탈로그를 못 따라간
[#171](https://github.com/gncorpseo-commits/capnet/pull/171)과도 같은 자리다.

## 무엇을 바꿨나 — **기본값을 뒤집었다**

폴백을 **가진** 쪽을 적는다. 여기 없는 것은 **Core 중개 입력을 요구한다** (D8′).
모르는 모달리티가 들어오면 **거절**이 기본이다.

## 왜 별 모듈인가

`main.py` 는 `fastapi` 를, `tiny_cnn.py` 는 `torch` 를 import 한다 — 둘 다
의존성 없는 단위 검사에서 **불러올 수 없다.** 이 판단만 표준 라이브러리로 떼어
두면 `tests/test_modality_fallback.py` 가 **실제로 호출해** 볼 수 있다.
"""

from __future__ import annotations

# 로컬 골든셋 폴백이 있는 모달리티.
#
# 골든셋은 EuroSAT **이미지** 케이스다 (`docs/spec/golden/`). 그래서 여기 들어올 수
# 있는 것은 그 이미지를 그대로 먹을 수 있는 모달리티뿐이다 — 이름이 `image` 로
# 시작하는지를 검사가 함께 본다 (`tests/test_modality_fallback.py`).
#
# **개수를 못박지 않는다.** 이미지 계열 모달리티는 늘 수 있다.
GOLDEN_FALLBACK_MODALITIES = frozenset({"image", "image_embed"})


def requires_core_input(modality: str) -> bool:
    """이 모달리티는 **Core 중개 입력이 있어야만** 도는가.

    모르는 모달리티는 **True** — 데모 데이터로 떨어지지 않는다.
    """
    return modality not in GOLDEN_FALLBACK_MODALITIES
