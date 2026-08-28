"""능력 코드 → 허용 MIME (Core capability-catalog §4 요약)."""

from __future__ import annotations

# 모달리티 접두 → 업로드 MIME allowlist
_MODALITY_MIME: dict[str, frozenset[str]] = {
    "image": frozenset({"image/jpeg", "image/png", "image/webp"}),
    "video": frozenset({"video/mp4", "video/webm"}),
    "audio": frozenset({"audio/wav", "audio/flac", "audio/mpeg"}),
    "text": frozenset({"text/plain", "application/json"}),
    "doc": frozenset({"text/plain"}),
    "table": frozenset({"text/csv", "application/json"}),
    "code": frozenset({"text/plain"}),
}


def modality_of_capability(code: str) -> str:
    return code.split(".", 1)[0]


def allowed_media_types(capability_code: str) -> frozenset[str]:
    mod = modality_of_capability(capability_code)
    return _MODALITY_MIME.get(mod, frozenset())


def check_media_for_capability(capability_code: str, media_type: str) -> str | None:
    """허용이면 None, 아니면 사람이 읽을 오류 문자열."""
    mt = (media_type or "").split(";")[0].strip().lower()
    if not mt:
        return "파일 MIME 이 비었다"
    allowed = allowed_media_types(capability_code)
    if not allowed:
        return f"{capability_code} 에 대한 업로드 MIME 규칙이 없다"
    if mt not in allowed:
        return (
            f"{capability_code} 는 {sorted(allowed)} 만 받는다 — "
            f"첨부={mt!r}"
        )
    return None
