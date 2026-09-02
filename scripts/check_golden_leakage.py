#!/usr/bin/env python3
"""골든셋이 학습셋과 겹치는지 검사한다 (홀드아웃 유효성).

게이트 점수가 능력을 재려면 골든 케이스가 학습에 쓰이지 않아야 한다.
겹치면 게이트는 "능력"이 아니라 "학습 데이터 재현"을 재게 된다.

학습셋 정의는 apps/train/train_scratch.py 의 list_images() 와 동일한 규칙을 쓴다.
골든 케이스의 출처는 manifest 의 zip_path 필드다.

표준 라이브러리만 쓴다 (호스트 python3 로 바로 실행).

  python3 scripts/check_golden_leakage.py
  python3 scripts/check_golden_leakage.py --manifest data/golden-n300/manifest-image-classify-n300.json

종료 코드: 0 = 지정한 매니페스트를 **전부 보고** 겹침 없음 · 2 = 겹침 발견 ·
          3 = **부분 검사** (일부가 없어 못 봤다) · 1 = 실행 오류 (zip 없음 · 본 것이 0건)

## 왜 3 이 따로 있나

기본 매니페스트 넷 중 **셋은 `data/` 아래라 저장소에 없다** (용량 때문에 추적하지
않는다). 그래서 신선한 클론에서 이 도구를 그냥 돌리면 셋을 건너뛰는데,
예전에는 그러고도 **`0` 과 「겹침 없음. 골든셋은 홀드아웃이다」** 를 찍었다.

보고서는 이 도구로 **「겹침 0/300」** 을 검증했다고 적는다. 그 300건짜리 매니페스트가
바로 없는 셋 중 하나다 — 시키는 대로 돌린 사람은 **40건만 본 초록**을 받고
300건을 확인했다고 믿게 된다. 「못 봤다」를 「깨끗하다」로 뭉뚱그린 것이다.

**본 것이 0건이면 답할 자격이 없다 → 1.** 일부만 봤으면 **그렇다고 말한다 → 3.**
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

# train_scratch.py 의 FOLDER_TO_LABEL 키와 같아야 한다.
FOLDERS = {
    "AnnualCrop",
    "Forest",
    "HerbaceousVegetation",
    "Highway",
    "Industrial",
    "Pasture",
    "PermanentCrop",
    "Residential",
    "River",
    "SeaLake",
}

DEFAULT_MANIFESTS = [
    "docs/spec/golden/manifest-image-classify-v1.json",
    "data/golden-n300/manifest-image-classify-n300.json",
    "data/golden-n300-holdout/manifest-image-classify-n300.json",
    "data/golden-n300-train/manifest-image-classify-n300.json",
]

# apps/train/train_scratch.py · scripts/extract_golden.py 와 규칙이 같아야 한다.
HOLDOUT_MOD = 5


def is_holdout(name: str) -> bool:
    return int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16) % HOLDOUT_MOD == 0


def training_names(zip_path: Path, holdout: bool = True) -> set[str]:
    """train_scratch.py 가 실제로 학습에 쓰는 집합.

    holdout=True  → 홀드아웃 제외 (현재 기본 동작, HOLDOUT=1)
    holdout=False → 전수 (구버전 동작, HOLDOUT=0). SD-008 최초 발견 재현용
    """
    with zipfile.ZipFile(zip_path) as zf:
        names = set()
        for name in zf.namelist():
            if not name.lower().endswith(".jpg"):
                continue
            parts = name.replace("\\", "/").split("/")
            if len(parts) >= 3 and parts[1] in FOLDERS:
                if holdout and is_holdout(name):
                    continue
                names.add(name)
    return names


def check(manifest_path: Path, train: set[str]) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = manifest.get("cases") or []
    zip_paths = [c.get("zip_path") for c in cases]
    missing_field = sum(1 for z in zip_paths if not z)
    overlap = [z for z in zip_paths if z and z in train]
    return {
        "manifest": str(manifest_path),
        "cases": len(cases),
        "no_zip_path": missing_field,
        "in_training_set": len(overlap),
        "sample": overlap[:3],
    }


def _out(s: str = "", *, err: bool = False) -> None:
    """Windows cp949 콘솔에서도 깨지지 않게 ASCII 하이픈만 쓴다."""
    stream = sys.stderr if err else sys.stdout
    try:
        stream.write(s + "\n")
    except UnicodeEncodeError:
        stream.buffer.write((s + "\n").encode(stream.encoding or "utf-8", errors="replace"))
        stream.buffer.flush()


def run_manifests(manifests: list[Path], train: set[str], emit=_out) -> tuple[int, int, list[str]]:
    """매니페스트 목록을 훑는다 → `(본 것, 겹친 것, 못 본 것들)`.

    zip 없이도 도는 순수 함수라 회귀 검사가 여기를 직접 부른다.
    **「못 봤다」를 돌려주는 것이 이 함수의 일이다** — 부르는 쪽이 그걸 삼키면 안 된다.
    """
    checked = 0
    leaked = 0
    unseen: list[str] = []
    for mp in manifests:
        if not mp.is_file():
            emit(f"  (못 봄 - 파일 없음) {mp}")
            unseen.append(f"{mp} — 파일이 없다")
            continue
        r = check(mp, train)
        checked += 1
        pct = (100.0 * r["in_training_set"] / r["cases"]) if r["cases"] else 0.0
        verdict = "LEAK" if r["in_training_set"] else "clean"
        emit(
            "  %-52s cases=%-4d in_train=%-4d (%5.1f%%)  %s"
            % (r["manifest"], r["cases"], r["in_training_set"], pct, verdict)
        )
        if not r["cases"]:
            # 케이스 0건짜리 매니페스트를 "clean" 으로 세면 그것도 같은 거짓말이다.
            emit("      케이스가 0건이다 - 이 매니페스트로는 아무것도 못 봤다")
            unseen.append(f"{mp} — 케이스가 0건")
        elif r["no_zip_path"]:
            emit(f"      경고: zip_path 없는 케이스 {r['no_zip_path']}건 - 검사 불가")
            unseen.append(f"{mp} — zip_path 없는 케이스 {r['no_zip_path']}건")
        for z in r["sample"]:
            emit(f"      예: {z}")
        if r["in_training_set"]:
            leaked += 1
    return checked, leaked, unseen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default="data/eurosat/EuroSAT_RGB.zip")
    ap.add_argument("--manifest", action="append", help="반복 지정 가능. 없으면 기본 4종")
    ap.add_argument(
        "--no-split",
        action="store_true",
        help="홀드아웃 분할 이전 동작으로 검사 (전수 학습 가정). SD-008 재현용",
    )
    args = ap.parse_args()

    zip_path = Path(args.zip)
    if not zip_path.is_file():
        _out(f"EuroSAT zip 없음: {zip_path} - scripts/download_eurosat.sh 먼저", err=True)
        return 1

    train = training_names(zip_path, holdout=not args.no_split)
    mode = "전수(구버전)" if args.no_split else "홀드아웃 제외(현재)"
    _out(f"학습셋 이미지 수 [{mode}]: {len(train)}")

    manifests = [Path(m) for m in (args.manifest or DEFAULT_MANIFESTS)]
    checked, leaked, unseen = run_manifests(manifests, train)

    if leaked:
        _out("")
        _out("겹침 발견. 게이트 점수는 학습 데이터 재현 점수이며 일반화 성능이 아니다.")
        _out("조치: docs/ops/phase1-verdict.md 6.3 (H1-H4)")
        return 2

    if checked == 0:
        _out("")
        _out(f"본 것이 0건이다 - 지정한 매니페스트 {len(manifests)}종을 하나도 못 봤다.", err=True)
        _out("깨끗한지 아닌지 **답할 수 없다**. 매니페스트 경로를 확인한다.", err=True)
        return 1

    if unseen:
        _out("")
        _out(f"본 {checked}종에서는 겹침이 없다. 그런데 {len(unseen)}종은 **못 봤다**:")
        for u in unseen:
            _out(f"  - {u}")
        _out("")
        _out("**부분 검사다.** 「골든셋은 홀드아웃이다」라고 말할 수 없다 -")
        _out("못 본 것 중에 보고서가 근거로 드는 n300 홀드아웃이 있을 수 있다.")
        _out("전부 보려면: scripts/extract_golden.py 로 data/golden-n300* 을 만든다.")
        return 3

    _out("")
    _out(f"겹침 없음 - {checked}종 전부 봤다. 골든셋은 홀드아웃이다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
