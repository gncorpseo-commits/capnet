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
    "timeseries": frozenset({"text/csv", "application/json"}),
    "code": frozenset({"text/plain"}),
}

# 모달리티 기본값과 **선언이 다른** 능력. 정본은 Core 의 `capability.input_schema`
# 이고 여기는 그 요약이다 — 어긋나면 Core 가 400 을 준다 (여기서 통과시켜도 못 돈다).
#   - image.classify : 골든셋이 JPEG 뿐이라 계약도 JPEG 만이다 (0012 · 측정 없이 주장 없음)
#   - table.extract  : 평문 표를 받는다 (`scripts/table_demo.sh`)
#   - text.*         : 평문만 (json 은 계약 밖)
_CODE_MIME: dict[str, frozenset[str]] = {
    "image.classify": frozenset({"image/jpeg"}),
    "table.extract": frozenset({"text/plain"}),
    "text.ner": frozenset({"text/plain"}),
    "text.classify": frozenset({"text/plain"}),
    "text.embed": frozenset({"text/plain"}),
    "image.embed": frozenset({"image/jpeg"}),
}


def modality_of_capability(code: str) -> str:
    return code.split(".", 1)[0]


def allowed_media_types(capability_code: str) -> frozenset[str]:
    override = _CODE_MIME.get(capability_code)
    if override is not None:
        return override
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
