"""골든셋 채점. team gate-runner에서만 돌린다. dummy PASSED가 아니다."""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from app.infer import predict_image
from app.tiny_cnn import LABELS

LABEL_SET = set(LABELS)


def macro_f1(y_true: list[str], y_pred: list[str]) -> float:
    scores: list[float] = []
    for lab in LABELS:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        scores.append(0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec))
    return sum(scores) / len(scores)


def load_cases(manifest_path: Path, cases_dir: Path) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out = []
    for case in manifest["cases"]:
        path = cases_dir / f"{case['caseId']}.jpg"
        if not path.is_file():
            raise FileNotFoundError(path)
        out.append({"caseId": case["caseId"], "expected": case["expected"], "path": path})
    return out


def predict_mode(mode: str, weights: str, case: dict, rng: random.Random) -> str:
    if mode == "scratch":
        label, _ = predict_image(weights, str(case["path"]))
        return label
    if mode == "constant":
        return "residential"
    if mode == "random":
        return rng.choice(LABELS)
    if mode == "invalid":
        return "not_a_label"
    raise ValueError(mode)


def score(mode: str, weights: str, cases: list[dict], seed: int = 20260806) -> dict:
    rng = random.Random(seed)
    y_true: list[str] = []
    y_pred: list[str] = []
    per_label: dict[str, dict[str, int]] = defaultdict(lambda: {"n": 0, "ok": 0})
    for case in cases:
        pred = predict_mode(mode, weights, case, rng)
        exp = case["expected"]
        y_true.append(exp)
        y_pred.append(pred)
        per_label[exp]["n"] += 1
        if pred == exp:
            per_label[exp]["ok"] += 1

    invalid = sum(1 for p in y_pred if p not in LABEL_SET)
    passed = sum(1 for t, p in zip(y_true, y_pred) if p == t)
    total = len(cases)
    accuracy = passed / total if total else 0.0
    inv_rate = invalid / total if total else 0.0
    f1 = macro_f1(y_true, y_pred)
    return {
        "mode": mode,
        "dummy": False,
        "cases_total": total,
        "cases_passed": passed,
        "golden_score": accuracy,
        "macro_f1": f1,
        "invalid_rate": inv_rate,
        "per_label": dict(per_label),
        "predictions": [
            {"caseId": c["caseId"], "expected": t, "predicted": p}
            for c, t, p in zip(cases, y_true, y_pred)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="scratch", choices=("scratch", "constant", "random", "invalid"))
    parser.add_argument("--weights", default="/weights/eurosat_scratch.safetensors")
    parser.add_argument("--cases", default="/golden/cases")
    parser.add_argument("--manifest", default="/golden/manifest-image-classify-v1.json")
    parser.add_argument("--min-accuracy", type=float, default=0.68)
    parser.add_argument("--min-macro-f1", type=float, default=0.65)
    parser.add_argument("--max-invalid-rate", type=float, default=0.02)
    args = parser.parse_args()

    cases = load_cases(Path(args.manifest), Path(args.cases))
    result = score(args.mode, args.weights, cases)
    passed = (
        result["golden_score"] >= args.min_accuracy
        and result["macro_f1"] >= args.min_macro_f1
        and result["invalid_rate"] <= args.max_invalid_rate
    )
    result["status"] = "PASSED" if passed else "FAILED"
    result["thresholds"] = {
        "min_accuracy": args.min_accuracy,
        "min_macro_f1": args.min_macro_f1,
        "max_invalid_rate": args.max_invalid_rate,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
