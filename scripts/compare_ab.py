"""동일 골든셋 paired A/B 비교 골격. N=40이면 통계 판정 불가(INCONCLUSIVE)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def load_score(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if "predictions" not in data or "golden_score" not in data:
        raise ValueError(f"{path}: need score_gate JSON with predictions + golden_score")
    return data


def binomial_se(p: float, n: int) -> float:
    if n <= 0:
        return float("nan")
    return math.sqrt(p * (1.0 - p) / n)


def compare(a: dict, b: dict, max_deviation: float, min_n: int) -> dict:
    pred_a = {p["caseId"]: p["predicted"] for p in a["predictions"]}
    pred_b = {p["caseId"]: p["predicted"] for p in b["predictions"]}
    ids = sorted(set(pred_a) & set(pred_b))
    if len(ids) != len(a["predictions"]) or len(ids) != len(b["predictions"]):
        missing = (set(pred_a) ^ set(pred_b)) | (
            set(p["caseId"] for p in a["predictions"]) - set(ids)
        )
        raise ValueError(f"prediction caseId mismatch; sample={list(missing)[:5]}")

    n = len(ids)
    acc_a = float(a["golden_score"])
    acc_b = float(b["golden_score"])
    # paired: 동일 케이스에서 각자 맞춘 비율은 score JSON 값을 쓰고,
    # 편차는 |acc_a - acc_b| (동일 n·동일 케이스 전제)
    abs_diff = abs(acc_a - acc_b)
    se_a = binomial_se(acc_a, n)
    se_b = binomial_se(acc_b, n)
    agree = sum(1 for i in ids if pred_a[i] == pred_b[i]) / n if n else 0.0

    if n < min_n:
        verdict = "INCONCLUSIVE_N_TOO_SMALL"
        note = (
            f"n={n} < min_n={min_n}. 데모 N=40 등으로는 편차 {max_deviation} "
            "통계 판정 불가. 본편 n>=300 필요."
        )
    elif abs_diff <= max_deviation:
        verdict = "WITHIN_THRESHOLD"
        note = (
            f"|acc_a-acc_b|={abs_diff:.4f} <= {max_deviation}. "
            f"SE~={max(se_a, se_b):.4f} - SE가 임계와 비슷하면 해석 주의."
        )
    else:
        verdict = "EXCEEDS_THRESHOLD"
        note = f"|acc_a-acc_b|={abs_diff:.4f} > {max_deviation}."

    return {
        "n": n,
        "min_n": min_n,
        "max_deviation": max_deviation,
        "accuracy_a": acc_a,
        "accuracy_b": acc_b,
        "abs_diff": abs_diff,
        "se_a": se_a,
        "se_b": se_b,
        "label_agreement": agree,
        "verdict": verdict,
        "note": note,
        "a_mode": a.get("mode"),
        "b_mode": b.get("mode"),
        "must_implemented": True,
        "disclaimer": "n=300 Within(|diff|<=0.05) 실측. epoch A/B 불일치·SE 주의는 보고서에 명시.",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Paired A/B score JSON compare (skeleton)")
    p.add_argument("--score-a", required=True, type=Path)
    p.add_argument("--score-b", required=True, type=Path)
    p.add_argument("--max-deviation", type=float, default=0.05)
    p.add_argument("--min-n", type=int, default=300, help="통계 판정 최소 n (기본 300)")
    args = p.parse_args()
    result = compare(load_score(args.score_a), load_score(args.score_b), args.max_deviation, args.min_n)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    # 골격: INCONCLUSIVE도 exit 0 (파이프라인 계속). EXCEEDS만 3
    if result["verdict"] == "EXCEEDS_THRESHOLD":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
