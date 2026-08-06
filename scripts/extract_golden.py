"""골든셋 균등 추출 (+선택적 픽셀 전수). 모델 선택 없음.

데모 N=40 · 본편 N=300 모두 동일 방식. 산출물은 기본 data/golden-n{N}/ (git 미추적).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

LABEL = {
    "AnnualCrop": "annual_crop",
    "Forest": "forest",
    "HerbaceousVegetation": "herbaceous_vegetation",
    "Highway": "highway",
    "Industrial": "industrial",
    "Pasture": "pasture",
    "PermanentCrop": "permanent_crop",
    "Residential": "residential",
    "River": "river",
    "SeaLake": "sea_lake",
}
CLASSES = list(LABEL.keys())
ARCHIVE_SHA256 = "b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90"


def jpeg_hw(data: bytes) -> tuple[int, int, int] | None:
    i = 2
    n = len(data)
    while i + 8 < n:
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        if marker in (0xD9, 0xDA):
            break
        length = (data[i + 2] << 8) + data[i + 3]
        if 0xC0 <= marker <= 0xC3:
            h = (data[i + 5] << 8) + data[i + 6]
            w = (data[i + 7] << 8) + data[i + 8]
            c = data[i + 9]
            return w, h, c
        i += 2 + length
    return None


def even_stride_picks(names: list[str], per_class: int) -> list[str]:
    if per_class < 1:
        raise ValueError("per_class must be >= 1")
    if len(names) < per_class:
        raise ValueError(f"class has {len(names)} images, need >= {per_class}")
    # 정렬명 균등 간격. k=0..per_class-1 → 구간 (per_class+1) 등분
    return [names[(k + 1) * len(names) // (per_class + 1)] for k in range(per_class)]


def main() -> None:
    parser = argparse.ArgumentParser(description="EuroSAT RGB golden extract (model-free)")
    parser.add_argument("--n", type=int, default=40, help="총 케이스 수 (10의 배수)")
    parser.add_argument("--zip", type=Path, default=Path("/data/EuroSAT_RGB.zip"))
    parser.add_argument("--out", type=Path, default=None, help="출력 디렉터리")
    parser.add_argument(
        "--pixel-scan",
        action="store_true",
        help="zip 전수 픽셀 스캔 (느림). N과 무관하게 아카이브 검증용",
    )
    parser.add_argument(
        "--cases-prefix",
        default="ic1",
        help="caseId 접두 (데모 ic1, 본편 ic1f 등)",
    )
    args = parser.parse_args()

    if args.n % len(CLASSES) != 0:
        raise SystemExit(f"--n must be divisible by {len(CLASSES)}")
    per_class = args.n // len(CLASSES)
    out_dir = args.out or Path(f"/out/golden-n{args.n}")
    cases_dir = out_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / f"manifest-image-classify-n{args.n}.json"
    pixel_path = out_dir / "pixel-scan.json"

    by_class: dict[str, list[str]] = {c: [] for c in CLASSES}
    pixel_hist: Counter[str] = Counter()
    bad = 0

    with zipfile.ZipFile(args.zip) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".jpg"):
                continue
            parts = name.replace("\\", "/").split("/")
            if len(parts) < 3 or parts[0] != "EuroSAT_RGB":
                continue
            cls = parts[1]
            if cls not in by_class:
                continue
            if args.pixel_scan:
                data = zf.read(name)
                hw = jpeg_hw(data)
                if hw is None:
                    bad += 1
                    pixel_hist["unparsed"] += 1
                else:
                    pixel_hist[f"{hw[0]}x{hw[1]}c{hw[2]}"] += 1
            by_class[cls].append(name)

        for cls in CLASSES:
            by_class[cls].sort()

        cases = []
        idx = 1
        for cls in CLASSES:
            picks = even_stride_picks(by_class[cls], per_class)
            for src in picks:
                data = zf.read(src)
                digest = hashlib.sha256(data).hexdigest()
                case_id = f"{args.cases_prefix}-{idx:04d}"
                dest_name = f"{case_id}.jpg"
                (cases_dir / dest_name).write_bytes(data)
                cases.append(
                    {
                        "caseId": case_id,
                        "expected": LABEL[cls],
                        "zip_path": src.replace("\\", "/"),
                        "file": f"cases/{dest_name}",
                        "sha256": digest,
                    }
                )
                idx += 1

    manifest = {
        "capability": "image.classify@1",
        "dataset": "eurosat-rgb",
        "zenodo_record": "7711810",
        "archive": "EuroSAT_RGB.zip",
        "archive_sha256": ARCHIVE_SHA256,
        "preprocessing": {"resize": [32, 32], "bands": "RGB"},
        "selection": {
            "method": "per_class_even_stride_sorted_names",
            "n": args.n,
            "per_class": per_class,
            "model_based": False,
            "note": "데모 n=40과 본편 n=300 분리. n=300은 통계 판정용 골격이며 커밋하지 않음.",
        },
        "scoring_version": 1,
        "labels": list(LABEL.values()),
        "cases": cases,
    }
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    manifest_path.write_text(text, encoding="utf-8")
    manifest_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()

    summary: dict = {
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha,
        "n_cases": len(cases),
        "per_class": per_class,
        "cases_dir": str(cases_dir),
    }
    if args.pixel_scan:
        pixel = {
            "jpeg_scanned": sum(pixel_hist.values()),
            "unparsed": bad,
            "histogram": dict(pixel_hist),
            "all_64x64c3": pixel_hist.get("64x64c3", 0) == 27000 and bad == 0,
        }
        pixel_path.write_text(json.dumps(pixel, indent=2) + "\n", encoding="utf-8")
        summary["pixel"] = pixel
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
