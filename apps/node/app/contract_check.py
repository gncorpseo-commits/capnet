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
| `preprocess` | 계약이 선언한 전처리(`resize`·`colorspace`)를 **적용해서** 추론한다 (0014) |

`preprocess` 는 0013 에서 잠깐 빠져 있었다 — 계약에 값을 적을 자리가 없어서 러너가
검증 없이 불린만 보냈기 때문이다. 0014 가 `input_schema.preprocess` 를 만들면서 돌아왔다.

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


def _is_reference_arch(arch: str | None) -> bool:
    """우리 러너에 이 arch 의 **빌더가 있는가.**

    `ARCH_REGISTRY` 를 직접 본다 — Core 의 `REFERENCE_ARCHS` 와 같은 목록이어야 하고,
    어긋나면 `test_contract_checks_by_arch` 가 잡는다. 여기서 목록을 다시 적지 않는다.
    """
    if not arch:
        return False
    try:
        from app.tiny_cnn import ARCH_REGISTRY
    except ModuleNotFoundError:
        # torch 가 없는 Node. 참조 구현을 세울 수 없으므로 선언 검사 경로로 간다.
        return False
    return arch in ARCH_REGISTRY


def _declaration_only(
    *, arch: str | None, contract: dict[str, Any],
    checks: dict[str, bool], notes: dict[str, str], fp: dict[str, Any] | None,
) -> dict[str, Any]:
    """참조 구현이 없을 때의 계약 검사 — **선언 정합**만 본다 (C2).

    실행하지 않으므로 `arch`·`max_params` 를 보고하지 않는다. Core 도 요구하지 않는다
    (`required_contract_checks`). **거짓으로 true 를 채우지 않는 것**이 이 함수의 요점이다.
    """
    from app.preprocess import resolve_preprocess

    # preprocess — 계약이 선언했고, 그 값이 **읽히는가.**
    declared = (contract.get("input_schema") or {}).get("preprocess")
    try:
        if declared is None:
            raise ValueError("계약이 preprocess 를 선언하지 않았다")
        size, space = resolve_preprocess(declared)
        checks["preprocess"] = True
        notes["preprocess"] = f"선언 확인: resize={list(size)} colorspace={space}"
    except Exception as exc:
        checks["preprocess"] = False
        notes["preprocess"] = f"{type(exc).__name__}: {exc}"

    # input_schema — 계약이 **무엇을 받는지 말했는가.** 샘플을 돌리지 않는다.
    #   `mediaTypes` 미선언은 업로드 자체가 400 이므로(B1), 계약 게이트에서도 거절한다.
    in_schema = contract.get("input_schema") or {}
    media = in_schema.get("mediaTypes")
    if isinstance(media, list) and media and all(isinstance(m, str) for m in media):
        checks["input_schema"] = True
        notes["input_schema"] = (
            f"선언 정합 (mediaTypes={media}) — **샘플 추론은 하지 않았다** "
            f"(arch={arch!r} 는 참조 구현이 아니다)"
        )
    else:
        checks["input_schema"] = False
        notes["input_schema"] = "input_schema.mediaTypes 가 없거나 형식이 아니다"

    # output_schema — 돌려줄 모양을 선언했는가. 출력이 없으니 값 검증은 못 한다.
    out_schema = contract.get("output_schema") or {}
    if out_schema.get("properties") or out_schema.get("required"):
        checks["output_schema"] = True
        notes["output_schema"] = (
            "선언 정합 (properties/required 있음) — **출력 값은 검증하지 않았다**"
        )
    else:
        checks["output_schema"] = False
        notes["output_schema"] = "output_schema 가 비어 있다"

    notes["_limits"] = (
        "참조 구현이 아니므로 실행 판정을 하지 않았다. 지문은 «그 파일이 그 구조다»까지만 "
        "말하며 «계약대로 동작한다»는 보장하지 않는다 (Decision 2-C · C2)."
    )
    return {
        **checks,
        "_notes": notes,
        "_params": (fp or {}).get("param_count", 0),
        "_fingerprint": (fp or {}).get("sha256"),
    }


def run(
    *, weights: str, arch: str | None, max_params: int | None,
    contract: dict[str, Any], sample: str,
) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    notes: dict[str, str] = {}

    # 0. 가중치 지문 (C2 · Decision 2-C) — **모든 모달리티 공통.**
    #
    #    파일을 열되 **실행하지 않는다.** safetensors 헤더의 텐서 이름·shape·dtype 만 읽어
    #    구조 지문을 낸다. torch 도 safetensors 라이브러리도 쓰지 않으므로
    #    torch 없는 Node(`s-public`)에서도 돌고, 10GB 파일이어도 헤더만 읽는다.
    #
    #    **이것이 보장하는 것은 「그 파일이 그 구조다」까지다.**
    #    「그 계약대로 동작한다」는 보장하지 않는다 — 그건 아래 참조 구현 경로가 하고,
    #    임의 모델로 넓히려면 격리 러너(C3 · v제품-2)가 선행한다.
    from app.fingerprint import FingerprintError, fingerprint

    fp: dict[str, Any] | None = None
    try:
        fp = fingerprint(weights)
        checks["weights_fingerprint"] = True
        notes["weights_fingerprint"] = (
            f"텐서 {fp['tensor_count']}개 · 파라미터 {fp['param_count']} · "
            f"구조 sha256={fp['sha256'][:16]}…"
        )
    except FingerprintError as exc:
        checks["weights_fingerprint"] = False
        notes["weights_fingerprint"] = f"{type(exc).__name__}: {exc}"
    except OSError as exc:
        checks["weights_fingerprint"] = False
        notes["weights_fingerprint"] = f"파일을 읽을 수 없다: {exc}"

    # 참조 구현이 아니면 여기서 끝낸다 — 세울 빌더가 없으므로 실행 판정을 할 수 없다.
    # 「할 수 없는 것을 했다고 보고하지 않는다」가 요점이다.
    if not _is_reference_arch(arch):
        return _declaration_only(
            arch=arch, contract=contract, checks=checks, notes=notes, fp=fp,
        )

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

    # 3'. 계약이 전처리를 선언했는가. 선언이 없으면 애초에 게이트런이 시작되지 않지만
    #      (ck_gate_run_contract_needs_preprocess), 러너도 형식을 본다 — 값이 망가져 있으면
    #      적용 자체가 안 된다.
    from app.preprocess import resolve_preprocess

    declared = (contract.get("input_schema") or {}).get("preprocess")
    try:
        size, space = resolve_preprocess(declared)
        if declared is None:
            raise ValueError("계약이 preprocess 를 선언하지 않았다")
        checks["preprocess"] = True
        notes["preprocess"] = f"선언 적용: resize={list(size)} colorspace={space}"
    except Exception as exc:
        checks["preprocess"] = False
        notes["preprocess"] = f"{type(exc).__name__}: {exc}"

    # 3. 계약 샘플로 **선언한 전처리를 적용해** 추론한다.
    #    여기서 도는 것이 input_schema 를 만족한다는 증거다.
    label: str | None = None
    confidence: float | None = None
    if checks.get("arch") and checks.get("preprocess"):
        try:
            from app.infer import predict_image

            label, confidence = predict_image(
                weights, sample, arch=arch, max_params=max_params, preprocess=declared
            )
            checks["input_schema"] = True
            notes["input_schema"] = (
                f"선언 전처리로 샘플 추론 성공 ({Path(sample).stat().st_size} bytes)"
            )
        except Exception as exc:
            checks["input_schema"] = False
            notes["input_schema"] = f"{type(exc).__name__}: {exc}"
    else:
        checks["input_schema"] = False
        notes["input_schema"] = "arch 또는 preprocess 실패로 추론할 수 없다"

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

    # 참조 구현 경로에서는 파라미터 수를 **torch 로 센 값**(`params`)을 정본으로 둔다.
    # 지문의 `param_count` 는 shape 만으로 센 값이라 둘이 같아야 정상이다 —
    # 어긋나면 로드된 모델과 파일이 다르다는 뜻이므로 증적에 함께 남긴다.
    if fp is not None and fp["param_count"] != params:
        notes["weights_fingerprint"] = (
            f"{notes.get('weights_fingerprint', '')} · "
            f"⚠️ shape 합계({fp['param_count']}) ≠ 로드 후 파라미터({params})"
        )
    return {
        **checks,
        "_notes": notes,
        "_params": params,
        "_fingerprint": (fp or {}).get("sha256"),
    }


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
