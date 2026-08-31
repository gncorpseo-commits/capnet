"""`safety.pii` 규칙 — **선언한 패턴만** 찾고, 찾아본 목록을 결과가 들고 다닌다.

## 이 파일이 조심하는 것

「PII 를 찾는다」는 능력은 **놓치면 없느니만 못하다.** 사람은 결과가 비면 「검사했으니
없다」로 읽는다. 그래서 카탈로그가 `safety.malware_hint` 에 이미 적어 둔 규율을 그대로 쓴다 —
**탐지가 아니라 참고다.**

**주장하지 않는 것:**

- **놓친 것이 없다고 말하지 않는다** — 선언한 패턴만 본다. 자유 문장 속 이름·주소·계좌
  설명문은 **못 찾는다**
- **실제 개인정보다** — `krrn_like`·`card_like` 의 `_like` 는 **꼴이 같다**는 뜻이다.
  Luhn 을 통과한 16자리가 실제 카드라는 뜻이 아니고, 6-7 자리 숫자쌍이 실제 주민번호라는
  뜻도 아니다
- **비식별화·마스킹 도구다** — 원문을 고쳐 주지 않는다
- **개인정보 보호 준수(컴플라이언스)** — 아무것도 보증하지 않는다

`quality_profile='none'` · 골든셋 없음 · 재현율·정밀도 숫자 없음.

## 결과가 자기 한계를 들고 다닌다

`patterns_checked` 를 항상 같이 낸다. **목록에 없는 것은 「찾지 않았다」는 뜻이지
「없다」는 뜻이 아니다.** 이 칸이 없으면 빈 `findings` 가 「깨끗하다」로 읽힌다.

## 원문을 결과에 그대로 담지 않는다

찾은 자리의 글자를 그대로 돌려주면 **결과 자체가 새 유출면**이 된다 — 결과는 DB 증적에
남고 화면에 그려지고 로그를 탄다. 그래서 `text` 는 **가려서** 낸다(`mask`). 대신
`start`·`end` 는 그대로 준다 — **어디에 있었는지**는 알려 줘야 쓸모가 있다.
`text[start:end]` 로 원문을 다시 볼 수 있는 쪽은 **원문을 가진 사람**뿐이다.

## 규칙 (전부 여기 적는다 — 결과가 왜 그런지 설명 가능해야 한다)

1. 패턴은 `PII_PATTERNS` 순서대로 본다. **겹치면 먼저 온 것이 이긴다** (`text.ner` 과 같다).
2. `email` · `ipv4` · `ipv6` · `uuid` — `text.ner` 과 같은 뜻·같은 span 규약.
3. `krrn_like` — `NNNNNN-NNNNNNN` 꼴. **날짜부(앞 6자리)가 달력에 맞아야** 한다.
   그게 없으면 임의의 13자리 숫자가 전부 걸린다.
4. `card_like` — 13..19 자리(구분자 `-`·공백 허용)이고 **Luhn 을 통과**해야 한다.
   Luhn 은 오타 검사지 실재 검사가 아니다 — 그래서 `_like` 다.
5. `phone_kr_like` — `0N(N)-NNN(N)-NNNN` 꼴. 국가번호 `+82` 형태도 같은 라벨로 본다.
   `ipv6` 는 **축약(`::`)을 다 풀지 않는다** — `fe80::1ff:fe23:4567:890a` 에서 뒷부분만
   걸릴 수 있다. **자리를 알리는 데는 쓸모가 있고, 「전체를 잡았다」고는 못 한다.**
6. 마스킹은 라벨마다 다르다 (`_mask_*`). **원문 복원이 불가능해야** 하고, 동시에
   **무엇이었는지 감은 남아야** 한다 — 그 둘의 절충이라 완벽하지 않다.
"""

from __future__ import annotations

import re
from typing import Any

# 결과에 그대로 실린다. **찾아본 것의 정본**이다 — 여기 없으면 안 찾은 것이다.
PII_LABELS: tuple[str, ...] = (
    "email",
    "krrn_like",
    "card_like",
    "phone_kr_like",
    "ipv6",
    "ipv4",
    "uuid",
)

_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_UUID = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# 축약(`::`) 포함 전체 문법을 정규식으로 다 담지 않는다 — 흔한 꼴만 본다.
_IPV6 = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b")
_KRRN = re.compile(r"\b(\d{6})-([1-8]\d{6})\b")
_CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
_PHONE_KR = re.compile(r"(?:\+82[ -]?|\b0)(?:1[016789]|2|[3-6]\d)[ -]?\d{3,4}[ -]?\d{4}\b")


def _valid_ipv4(span: str) -> bool:
    parts = span.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def _valid_krrn_date(six: str) -> bool:
    """앞 6자리가 `YYMMDD` 로 말이 되는가. 실재 여부가 아니라 **꼴**만 본다."""
    month, day = int(six[2:4]), int(six[4:6])
    return 1 <= month <= 12 and 1 <= day <= 31


def luhn_ok(digits: str) -> bool:
    """Luhn 체크섬. **오타 검사이지 실재 검사가 아니다** — 그래서 `_like` 다."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _keep_digits(span: str) -> str:
    return "".join(c for c in span if c.isdigit())


def _mask_email(span: str) -> str:
    """`ops@example.dev` → `o**@e******.dev` — 도메인 끝만 남긴다."""
    local, _, domain = span.partition("@")
    host, _, tld = domain.rpartition(".")
    return f"{local[:1]}{'*' * max(len(local) - 1, 1)}@{host[:1]}{'*' * max(len(host) - 1, 1)}.{tld}"


def _mask_tail(span: str, keep: int) -> str:
    """숫자만 남기고 **끝 `keep` 자리**만 보인다. 구분자는 버린다."""
    digits = _keep_digits(span)
    if len(digits) <= keep:
        return "*" * len(digits)
    return "*" * (len(digits) - keep) + digits[-keep:]


def _mask_krrn(span: str) -> str:
    """앞 6자리(생년월일 꼴)도 **가린다.** 뒤 첫 자리만 남긴다 — 성별·세기 자리다."""
    digits = _keep_digits(span)
    return "*" * 6 + "-" + digits[6:7] + "*" * 6


def _mask_generic(span: str) -> str:
    return f"{span[:1]}{'*' * max(len(span) - 1, 1)}"


_MASKS = {
    "email": _mask_email,
    "krrn_like": _mask_krrn,
    "card_like": lambda s: _mask_tail(s, 4),
    "phone_kr_like": lambda s: _mask_tail(s, 4),
    "ipv4": _mask_generic,
    "ipv6": _mask_generic,
    "uuid": _mask_generic,
}


def mask(label: str, span: str) -> str:
    """라벨에 맞게 가린다. **원문 복원이 불가능해야 한다.**"""
    return _MASKS.get(label, _mask_generic)(span)


def _accept(label: str, span: str, m: re.Match[str]) -> bool:
    if label == "ipv4":
        return _valid_ipv4(span)
    if label == "krrn_like":
        return _valid_krrn_date(m.group(1))
    if label == "card_like":
        digits = _keep_digits(span)
        return 13 <= len(digits) <= 19 and luhn_ok(digits)
    return True


_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", _EMAIL),
    ("krrn_like", _KRRN),
    ("card_like", _CARD),
    ("phone_kr_like", _PHONE_KR),
    ("uuid", _UUID),
    ("ipv6", _IPV6),
    ("ipv4", _IPV4),
)


def find_pii(text: str) -> dict[str, Any]:
    """`{"patterns_checked": [...], "findings": [...]}`.

    `findings` 가 비어 있어도 **「PII 가 없다」가 아니다** — `patterns_checked` 에 적힌
    것만 찾아봤다는 뜻이다.
    """
    used: list[tuple[int, int]] = []
    out: list[dict[str, Any]] = []

    def _free(start: int, end: int) -> bool:
        return all(end <= s or start >= e for s, e in used)

    for label, pat in _PATTERNS:
        for m in pat.finditer(text):
            start, end = m.start(), m.end()
            span = text[start:end]
            if not _accept(label, span, m):
                continue
            if not _free(start, end):
                continue
            used.append((start, end))
            out.append({
                "label": label,
                "start": start,
                "end": end,
                "text": mask(label, span),
            })

    out.sort(key=lambda r: (r["start"], r["end"]))
    return {"patterns_checked": sorted(PII_LABELS), "findings": out}
