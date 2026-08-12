"""계약 검증 — team gate-runner 에서만 돌린다 (B2). 보고가 아니라 **실행**이다.

## 무엇이 문제였나

계약 게이트(`kind='contract'`)는 러너가 보낸 `contract_checks` 가 전부 `true` 인지만 봤다.
그 값을 **아무도 계산하지 않았다** — 러너가 그냥 `true` 를 적어 보내면 통과였다.
D6(사전학습 허용)를 풀면 남의 가중치를 받는데, 그때 이 게이트는 도장만 찍는 절차가 된다.

## 무엇을 실행하나 (B2 Decision 3)

| 항목 | 어떻게 판정하나 |
|------|-----------------|
| `arch` | Core 가 말한 arch 로 모델을 **세우고 가중치를 로드**한다. 구조가 다르면 로드가 깨진다 |
| `max_params` | 로드된 파라미터 수를 세어 상한과 비교한다 |
| `input_schema` | 계약 샘플로 **실제 추론을 돌린다.** 못 읽거나 못 돌리면 실패 |
| `output_schema` | 그 출력이 `output_schema` 를 만족하는지 — closed-set 이면 라벨 집합까지 |

`preprocess` 는 이번 범위 밖이다 (Decision 3). 실수행이 들어올 때 추가한다.

## 왜 러너인가

절대규칙 8. Core 가 스스로 판정을 만들면 「실행과 판정의 분리」가 무너진다.
Core 는 이 출력을 받아 적을 뿐이고, 전부 `true` 인지만 본다.

    python -m app.contract_check --weights /weights/x.safetensors \\
        --arch TinyEuroSAT --max-params 2000000 \\
        --contract /tmp/contract.json --sample /tmp/sample.jpg

stdout 은 `contract_checks` 에 그대로 실을 JSON 하나다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def check_output_schema(out: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, str]:
    """출력이 계약을 만족하는가. jsonschema 를 쓰지 않는다 — 새 의존성 0.

    계약이 실제로 쓰는 것만 본다: `required` · `properties.enum` · 숫자 범위 ·
    `additionalProperties: false`. 계약에 없는 규칙은 검사하지 않는다.
    """
    props = schema.get("properties") or {}
    for key in schema.get("required") or []:
        if key not in out:
            return False, f"required 누락: {key}"
    if schema.get("additionalProperties") is False:
        extra = [k for k in out if k not in props]
        if extra:
            return False, f"허용되지 않은 필드: {', '.join(extra)}"
    for key, value in out.items():
        spec = props.get(key)
        if not isinstance(spec, dict):
            continue
        kind = spec.get("type")
        if kind == "string" and not isinstance(value, str):
            return False, f"{key} 는 string 이어야 한다"
        if kind == "number" and not isinstance(value, (int, float)):
            return False, f"{key} 는 number 이어야 한다"
        allowed = spec.get("enum")
        if allowed is not None and value not in allowed:
            return False, f"{key}={value!r} 은 enum 밖이다"
        if isinstance(value, (int, float)):
            lo, hi = spec.get("minimum"), spec.get("maximum")
            if lo is not None and value < lo:
                return False, f"{key}={value} < minimum {lo}"
            if hi is not None and value > hi:
                return False, f"{key}={value} > maximum {hi}"
    return True, "ok"


def run(
    *, weights: str, arch: str | None, max_params: int | None,
    contract: dict[str, Any], sample: str,
) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    notes: dict[str, str] = {}

    # 1·2. arch 로 세우고 로드한 뒤 파라미터를 센다.
    #      predict_image 가 둘 다 하지만, 무엇이 깨졌는지 구분해서 보고해야 한다.
    from app.infer import MAX_PARAMS_DEFAULT
    from app.tiny_cnn import build_model
    from safetensors.torch import load_file

    params = 0
    try:
        model = build_model(arch) if arch else None
        if model is None:
            checks["arch"] = False
            notes["arch"] = "Core 가 arch 를 말하지 않았다 (legacy Agent) — 계약 검증 불가"
        else:
            model.load_state_dict(load_file(weights))
            params = sum(p.numel() for p in model.parameters())
            checks["arch"] = True
            notes["arch"] = f"{arch} 로 로드 성공"
    except Exception as exc:  # 구조 불일치·allowlist 밖 arch·깨진 파일
        checks["arch"] = False
        notes["arch"] = f"{type(exc).__name__}: {exc}"

    cap = max_params or MAX_PARAMS_DEFAULT
    if checks.get("arch"):
        checks["max_params"] = params <= cap
        notes["max_params"] = f"{params} <= {cap}" if params <= cap else f"{params} > {cap}"
    else:
        checks["max_params"] = False
        notes["max_params"] = "arch 실패로 파라미터를 셀 수 없다"

    # 3. 계약 샘플로 실제 추론. 여기서 도는 것이 input_schema 를 만족한다는 증거다.
    label: str | None = None
    confidence: float | None = None
    if checks.get("arch"):
        try:
            from app.infer import predict_image

            label, confidence = predict_image(
                weights, sample, arch=arch, max_params=max_params
            )
            checks["input_schema"] = True
            notes["input_schema"] = f"샘플 추론 성공 ({Path(sample).stat().st_size} bytes)"
        except Exception as exc:
            checks["input_schema"] = False
            notes["input_schema"] = f"{type(exc).__name__}: {exc}"
    else:
        checks["input_schema"] = False
        notes["input_schema"] = "arch 실패로 추론할 수 없다"

    # 4. 그 출력이 계약을 만족하는가.
    if checks.get("input_schema"):
        out: dict[str, Any] = {"label": label}
        if confidence is not None:
            out["confidence"] = confidence
        ok, why = check_output_schema(out, contract.get("output_schema") or {})
        checks["output_schema"] = ok
        notes["output_schema"] = why if not ok else f"label={label!r} 이 계약을 만족한다"
    else:
        checks["output_schema"] = False
        notes["output_schema"] = "추론 실패로 출력을 검사할 수 없다"

    return {**checks, "_notes": notes, "_params": params}


def main() -> int:
    ap = argparse.ArgumentParser(prog="app.contract_check", description="계약 검증 (B2)")
    ap.add_argument("--weights", required=True)
    ap.add_argument("--arch")
    ap.add_argument("--max-params", type=int)
    ap.add_argument("--contract", required=True, help="capability JSON 파일")
    ap.add_argument("--sample", required=True, help="계약 샘플 파일")
    args = ap.parse_args()

    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    out = run(
        weights=args.weights,
        arch=args.arch,
        max_params=args.max_params,
        contract=contract,
        sample=args.sample,
    )
    print(json.dumps(out, ensure_ascii=False))
    # 하나라도 실패하면 2 — 호출자가 FAILED 로 마감한다 (golden 과 같은 규약).
    hard = [k for k, v in out.items() if not k.startswith("_") and v is not True]
    return 2 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
