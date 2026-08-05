"""골든셋 N=40 균등 추출 + 픽셀 전수. 모델 선택 없음."""
from __future__ import annotations

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

ZIP_PATH = Path("/data/EuroSAT_RGB.zip")
OUT_DIR = Path("/out")
CASES_DIR = OUT_DIR / "cases"
MANIFEST_PATH = OUT_DIR / "manifest-image-classify-v1.json"
PIXEL_PATH = OUT_DIR / "pixel-scan.json"

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


def main() -> None:
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    by_class: dict[str, list[str]] = {c: [] for c in CLASSES}
    pixel_hist: Counter[str] = Counter()
    bad = 0

    with zipfile.ZipFile(ZIP_PATH) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".jpg"):
                continue
            parts = name.replace("\\", "/").split("/")
            if len(parts) < 3 or parts[0] != "EuroSAT_RGB":
                continue
            cls = parts[1]
            if cls not in by_class:
                continue
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
            names = by_class[cls]
            # 균등 간격 4장. 정렬 파일명만 사용 (모델 무관).
            picks = [names[(k + 1) * len(names) // 5] for k in range(4)]
            for src in picks:
                data = zf.read(src)
                digest = hashlib.sha256(data).hexdigest()
                case_id = f"ic1-{idx:04d}"
                dest_name = f"{case_id}.jpg"
                (CASES_DIR / dest_name).write_bytes(data)
                rel_zip = src.replace("\\", "/")
                cases.append(
                    {
                        "caseId": case_id,
                        "expected": LABEL[cls],
                        "zip_path": rel_zip,
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
        "archive_sha256": "b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90",
        "preprocessing": {"resize": [32, 32], "bands": "RGB"},
        "selection": {
            "method": "per_class_even_stride_sorted_names",
            "n": 40,
            "per_class": 4,
            "model_based": False,
        },
        "scoring_version": 1,
        "labels": list(LABEL.values()),
        "cases": cases,
    }
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    MANIFEST_PATH.write_text(text, encoding="utf-8")
    manifest_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()

    pixel = {
        "jpeg_scanned": sum(pixel_hist.values()),
        "unparsed": bad,
        "histogram": dict(pixel_hist),
        "all_64x64c3": pixel_hist.get("64x64c3", 0) == 27000 and bad == 0,
        "checked_at": "2026-08-06",
    }
    PIXEL_PATH.write_text(json.dumps(pixel, indent=2) + "\n", encoding="utf-8")
    summary = {
        "manifest_sha256": manifest_sha,
        "n_cases": len(cases),
        "pixel": pixel,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
