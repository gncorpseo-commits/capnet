"""텍스트 특징 추출 — **torch 없이** 돈다 (단계 5).

## 왜 따로 있는가

학습(`apps/train/train_text_scratch.py`)과 추론(`app/infer_text.py`)이 **같은 함수**를
써야 한다. 두 벌이면 한쪽만 고쳐지고, 그 순간 「게이트가 승인한 것」과 「실행한 것」이
달라진다 — D3 가 전처리를 계약의 일부로 못박은 이유와 같다.

torch 를 쓰지 않는 이유도 같다: 계약 게이트의 **선언 검사 경로**와 학습 스크립트가
torch 없는 환경에서도 이 함수를 부를 수 있어야 한다.

## 무엇을 하는가

문자 n-gram 을 해시해 고정 길이 벡터로 만든다 (hashing trick). 어휘 사전이 없으므로
**모델 파일 하나만으로 재현**되고, 학습에 쓰지 않은 문자가 나와도 깨지지 않는다.

해시는 `hashlib.blake2b` 로 고정한다 — 파이썬 `hash()` 는 **실행마다 값이 달라져서**
(`PYTHONHASHSEED`) 학습한 모델을 다음 실행에서 못 쓴다. 그 함정을 여기서 막는다.
"""

from __future__ import annotations

import hashlib
import unicodedata

# 해시 차원. 늘리면 충돌이 줄지만 모델도 커진다.
# 4096 × 라벨 6 = 24,582 파라미터 — scratch 로 CPU 에서 몇 초면 학습된다.
HASH_DIM = 4096

# 문자 n-gram 크기. 2·3 이면 짧은 문자열(이메일·IP)의 구조가 잡힌다.
NGRAMS = (2, 3)


def normalize(text: str, *, form: str = "NFC", max_chars: int | None = None) -> str:
    """계약이 선언한 정규화·길이 제한을 적용한다 (카탈로그 §4 text 어휘).

    `max_chars` 는 **문자** 수다 (바이트가 아니다) — 러너가 그대로 셀 수 있어야
    계약이 검증 가능하다. 토크나이저를 계약에 넣지 않은 것과 같은 이유다.
    """
    out = unicodedata.normalize(form, text)
    if max_chars is not None and max_chars > 0:
        out = out[:max_chars]
    return out


def _bucket(token: str) -> int:
    """안정적인 해시 버킷. `hash()` 를 쓰지 않는다 — 실행마다 달라진다."""
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % HASH_DIM


def features(text: str) -> list[float]:
    """문자 n-gram 해시 가방. L2 정규화해 길이에 덜 휘둘리게 한다."""
    vec = [0.0] * HASH_DIM
    # 경계를 표시해 「시작/끝」 패턴이 잡히게 한다 (예: URL 의 `ht`, 날짜의 `-0`).
    padded = f"\x02{text}\x03"
    for n in NGRAMS:
        if len(padded) < n:
            continue
        for i in range(len(padded) - n + 1):
            vec[_bucket(padded[i:i + n])] += 1.0
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec
