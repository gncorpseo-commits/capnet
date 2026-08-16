"""평문 표 파싱 — **torch 없이** 돈다 (단계 6 ④).

## 무엇을 받나

`text/plain` 안의 표. 두 모양만 읽는다.

- **CSV** — 쉼표로 나뉜 줄
- **마크다운 파이프 표** — `| a | b |` (구분선 `|---|` 은 건너뛴다)

**PDF 는 받지 않는다.** 이 리포는 새 의존성을 늘리지 않는데(THIRD-PARTY 한 줄이 늘
따라붙는다) PDF 파싱에는 라이브러리가 필요하다. 계약의 `mediaTypes` 에 `text/plain` 만
선언하고, 그 한계를 카탈로그에도 적는다 — **못 하는 것을 할 수 있다고 하지 않는다.**

## 왜 따로 있는가

파싱은 순수 함수라 의존성이 필요 없고, 학습·추론·검사가 **같은 함수**를 써야 한다(D3).
"""

from __future__ import annotations

from pathlib import Path


def parse_table(
    path: str | Path,
    *,
    encoding: str,
    max_rows: int | None,
    max_cols: int | None,
) -> list[list[str]]:
    """행 목록을 돌려준다. 각 행은 셀 문자열 목록이다.

    행/열 상한을 넘으면 **던진다.** 잘라서 돌려주면 「표를 다 읽었다」가 거짓이 된다 —
    사용자는 뒤가 잘린 줄 모른 채 결과를 쓴다.
    """
    raw = Path(path).read_bytes()
    try:
        text = raw.decode(encoding)
    except (UnicodeDecodeError, LookupError) as exc:
        raise ValueError(f"입력이 계약 인코딩({encoding})이 아니다: {exc}") from exc

    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # 마크다운 구분선(`|---|:--:|`)은 데이터가 아니다.
            if cells and all(set(c) <= set("-: ") and c for c in cells):
                continue
        else:
            cells = [c.strip() for c in stripped.split(",")]
        rows.append(cells)

    if not rows:
        raise ValueError("표를 찾지 못했다 (빈 입력이거나 CSV·파이프 표가 아니다)")
    if max_rows is not None and len(rows) > max_rows:
        raise ValueError(f"행이 {len(rows)}개로 max_rows({max_rows})를 넘는다")

    width = max(len(r) for r in rows)
    if max_cols is not None and width > max_cols:
        raise ValueError(f"열이 {width}개로 max_cols({max_cols})를 넘는다")

    # 열 수를 맞춘다 — 짧은 행은 빈 셀로 채운다. 이건 자르는 것이 아니라 채우는 것이라
    # 정보를 잃지 않는다(원래 없던 칸은 빈 문자열이 사실이다).
    return [r + [""] * (width - len(r)) for r in rows]


def looks_like_header(row: list[str]) -> bool:
    """첫 행이 머리글인가 — **숫자가 하나도 없으면** 머리글로 본다.

    느슨한 판별이고, 그래서 결과에 `header_detected` 로 **그대로 노출한다.**
    맞다고 우기지 않는다.
    """
    for cell in row:
        try:
            float(cell)
        except ValueError:
            continue
        return False
    return any(c for c in row)
