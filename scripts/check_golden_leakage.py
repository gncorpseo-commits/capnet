#!/usr/bin/env python3
"""골든셋이 학습셋과 겹치는지 검사한다 (홀드아웃 유효성).

게이트 점수가 능력을 재려면 골든 케이스가 학습에 쓰이지 않아야 한다.
겹치면 게이트는 "능력"이 아니라 "학습 데이터 재현"을 재게 된다.

학습셋 정의는 apps/train/train_scratch.py 의 list_images() 와 동일한 규칙을 쓴다.
골든 케이스의 출처는 manifest 의 zip_path 필드다.

표준 라이브러리만 쓴다 (호스트 python3 로 바로 실행).

  python3 scripts/check_golden_leakage.py
  python3 scripts/check_golden_leakage.py --manifest data/golden-n300/manifest-image-classify-n300.json

종료 코드: 0 = 겹침 없음 · 2 = 겹침 발견 · 1 = 실행 오류
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
        print(f"EuroSAT zip 없음: {zip_path} — scripts/download_eurosat.sh 먼저", file=sys.stderr)
        return 1

    train = training_names(zip_path, holdout=not args.no_split)
    mode = "전수(구버전)" if args.no_split else "홀드아웃 제외(현재)"
    print(f"학습셋 이미지 수 [{mode}]: {len(train)}")

    manifests = [Path(m) for m in (args.manifest or DEFAULT_MANIFESTS)]
    leaked = False
    for mp in manifests:
        if not mp.is_file():
            print(f"  (건너뜀 — 없음) {mp}")
            continue
        r = check(mp, train)
        pct = (100.0 * r["in_training_set"] / r["cases"]) if r["cases"] else 0.0
        verdict = "LEAK" if r["in_training_set"] else "clean"
        print(
            "  %-52s cases=%-4d in_train=%-4d (%5.1f%%)  %s"
            % (r["manifest"], r["cases"], r["in_training_set"], pct, verdict)
        )
        if r["no_zip_path"]:
            print(f"      경고: zip_path 없는 케이스 {r['no_zip_path']}건 — 검사 불가")
        if r["sample"]:
            for z in r["sample"]:
                print(f"      예: {z}")
        if r["in_training_set"]:
            leaked = True

    if leaked:
        print(
            "\n겹침 발견. 게이트 점수는 학습 데이터 재현 점수이며 일반화 성능이 아니다.\n"
            "조치: docs/ops/phase1-verdict.md §6.3 (H1–H4)"
        )
        return 2

    print("\n겹침 없음. 골든셋은 홀드아웃이다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
