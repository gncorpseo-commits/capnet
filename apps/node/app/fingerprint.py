"""safetensors 가중치 지문 (Decision 2-C · C2).

## 무엇을 하는가

가중치 파일을 열어 **텐서 이름 · shape · dtype** 을 읽고, 그것을 정규화해 sha256 을 낸다.

## 왜 필요한가

계약 게이트의 원칙은 **「계약을 말로 받지 않는다 — 러너가 실행해서 판정한다」**(B2)였다.
그런데 그 원칙은 **우리 코드가 그 모달리티를 실행할 수 있을 때만** 성립한다.
`text.generate` 를 실행하려면 제출자의 코드가 필요하고, 그건 절대규칙 5 와 정면으로 닿는다.

C2 는 그 사이를 메운다 — **파일을 열되 실행하지 않는다.**

## 왜 torch 도 safetensors 라이브러리도 쓰지 않는가

safetensors 파일은 맨 앞 8바이트가 헤더 길이(little-endian u64)이고, 그 다음이 JSON 헤더다.
**그 JSON 만 읽으면 텐서 목록을 알 수 있다** — 텐서 본문(bytes)은 건드리지 않는다.

이렇게 하는 이유가 셋 있다.

1. **`s-public` Node 에는 torch 가 없다.** `apps/node/Dockerfile` 이 조건부로만 설치한다.
   torch 를 요구하면 지문 검사를 돌릴 수 있는 기기가 좁아진다.
2. **텐서 본문을 메모리에 올리지 않는다.** 10GB 가중치의 헤더는 수십 KB 다.
3. **역직렬화가 아니다.** JSON 파싱과 정수 읽기뿐이라 임의 코드 실행 여지가 없다 —
   절대규칙 5 가 pickle 을 막는 이유가 여기서도 그대로 지켜진다.

## 무엇을 보장하지 않는가

**「그 파일이 그 구조다」까지만 말한다.** 「그 계약대로 동작한다」는 **보장하지 않는다.**
동작 판정은 참조 구현이 있는 모달리티(현재 image/torch)에서 `arch`·`max_params` 가 하고,
임의 모델로 넓히려면 격리 러너(C3 · v제품-2)가 선행한다. 이 한계를 문서에서 지우지 않는다.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

# 헤더 길이 필드 8바이트 뒤에 JSON 이 온다.
_HEADER_LEN_BYTES = 8

# 헤더가 이보다 크면 읽지 않는다. 정상 모델의 헤더는 수십 KB 수준이고,
# 상한이 없으면 조작된 파일 하나로 러너 메모리를 채울 수 있다.
MAX_HEADER_BYTES = 64 * 1024 * 1024

# dtype 문자열 → 요소당 바이트. 파라미터 수를 셀 때는 쓰지 않지만,
# 알 수 없는 dtype 을 조용히 넘기지 않으려고 목록을 둔다.
KNOWN_DTYPES = frozenset({
    "BOOL", "U8", "I8", "F8_E5M2", "F8_E4M3",
    "I16", "U16", "F16", "BF16",
    "I32", "U32", "F32",
    "I64", "U64", "F64",
})


class FingerprintError(ValueError):
    """가중치를 지문화할 수 없다. 게이트에서는 실패로 본다."""


def read_header(path: str | Path) -> dict[str, Any]:
    """safetensors 헤더 JSON 을 읽는다. 텐서 본문은 읽지 않는다."""
    p = Path(path)
    size = p.stat().st_size
    if size < _HEADER_LEN_BYTES:
        raise FingerprintError(f"파일이 너무 작다 ({size} bytes) — safetensors 가 아니다")
    with p.open("rb") as fh:
        raw_len = fh.read(_HEADER_LEN_BYTES)
        (header_len,) = struct.unpack("<Q", raw_len)
        if header_len == 0:
            raise FingerprintError("헤더 길이가 0 이다")
        if header_len > MAX_HEADER_BYTES:
            raise FingerprintError(
                f"헤더가 상한을 넘는다 ({header_len} > {MAX_HEADER_BYTES})"
            )
        if _HEADER_LEN_BYTES + header_len > size:
            # 잘린 파일이거나 safetensors 가 아니다. 여기서 걸러야 아래 JSON 파싱이
            # 엉뚱한 이유로 실패하지 않는다.
            raise FingerprintError(
                f"헤더 길이({header_len})가 파일 크기({size})를 넘는다 — 잘렸거나 형식이 아니다"
            )
        blob = fh.read(header_len)
    try:
        header = json.loads(blob)
    except json.JSONDecodeError as exc:
        raise FingerprintError(f"헤더가 JSON 이 아니다: {exc}") from exc
    if not isinstance(header, dict):
        raise FingerprintError("헤더가 객체가 아니다")
    return header


def tensor_signature(header: dict[str, Any]) -> list[dict[str, Any]]:
    """`__metadata__` 를 뺀 텐서 목록을 **이름 순으로 정렬**해 돌려준다.

    정렬하는 이유: 같은 모델을 다시 저장하면 키 순서가 달라질 수 있는데,
    그것 때문에 지문이 바뀌면 지문이 「구조」가 아니라 「저장 순서」를 재게 된다.
    """
    sig: list[dict[str, Any]] = []
    for name, spec in header.items():
        if name == "__metadata__":
            continue
        if not isinstance(spec, dict):
            raise FingerprintError(f"텐서 항목이 객체가 아니다: {name}")
        dtype = spec.get("dtype")
        shape = spec.get("shape")
        if not isinstance(dtype, str) or dtype not in KNOWN_DTYPES:
            raise FingerprintError(f"{name}: 알 수 없는 dtype {dtype!r}")
        if not isinstance(shape, list) or not all(
            isinstance(d, int) and d >= 0 for d in shape
        ):
            raise FingerprintError(f"{name}: shape 형식이 아니다 ({shape!r})")
        sig.append({"name": name, "dtype": dtype, "shape": shape})
    if not sig:
        raise FingerprintError("텐서가 하나도 없다")
    sig.sort(key=lambda t: t["name"])
    return sig


def count_params(signature: list[dict[str, Any]]) -> int:
    """shape 만으로 파라미터 수를 센다 — **torch 없이.**

    지금 계약 게이트에서 `max_params` 는 참조 구현(torch)일 때만 필수다(Decision 2-C).
    이 값은 그 밖의 모달리티에서도 **증적에 남겨 두려고** 계산한다 —
    필수 검사로 올리려면 별 Decision 이 필요하다.
    """
    total = 0
    for t in signature:
        n = 1
        for d in t["shape"]:
            n *= d
        total += n
    return total


def fingerprint(path: str | Path) -> dict[str, Any]:
    """가중치 파일의 구조 지문.

    반환: `sha256` (정규화 서명의 해시) · `tensor_count` · `param_count` · `signature`.
    """
    header = read_header(path)
    sig = tensor_signature(header)
    # 정규화: 정렬된 (이름, dtype, shape) 만. 공백·키 순서에 흔들리지 않게 separators 고정.
    canonical = json.dumps(
        [[t["name"], t["dtype"], t["shape"]] for t in sig],
        separators=(",", ":"), ensure_ascii=False,
    )
    return {
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "tensor_count": len(sig),
        "param_count": count_params(sig),
        "signature": sig,
    }
