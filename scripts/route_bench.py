#!/usr/bin/env python3
"""라우팅 측정 하네스 — 「어디로 갔는지」를 반복해서 센다 (수동 도구).

    PYTHONPATH=capreq/src python3 scripts/route_bench.py --repeats 5
    PYTHONPATH=capreq/src python3 scripts/route_bench.py --set both --descriptions repo

## 왜 있는가

이 저장소는 라우팅 숫자를 두 번 적었다 — `text.extract` 의 「4/5 → 5/5」(#110)와
`text.rank` 의 n=5 표(#116). 둘 다 **그때 손으로 고른 프롬프트**였고 하네스가 없어서
**아무도 재현할 수 없었다.** 그래서 세 번째로 잴 때 앞의 결론이 흔들렸다:

- #116 이 「`text.extract` 요청이 `text.ner` 로 간다」고 적은 미스는 **능력 5종만 등록된
  스택에서 n=1** 로 본 것이었다. 9종을 등록하고 R=5 로 재니 그 프롬프트는 맞게 간다.
- 대신 그때 안 보이던 미스가 재현됐다 (`날짜랑 URL 전부 뽑아줘` → `text.extract`).

**측정이 없으면 주장도 없다.** 이 파일은 그 측정을 되풀이할 수 있게 만든다.

## 무엇을 세나 · 무엇을 주장하지 않나

같은 프롬프트를 `--repeats` 번 물어 **어느 능력으로 갔는지 센다.** 그게 전부다.

**정확도·품질을 주장하지 않는다.** 프롬프트는 사람이 고른 것이고, 「맞다」는 것도 사람이
정한 기대값이다. 모델(`qwen2.5:3b`)·카탈로그 구성·등록된 설명이 바뀌면 숫자가 바뀐다.
이 숫자로 능력을 팔지 않는다 — **변경 전후의 차이**를 보는 데만 쓴다.

## 튜닝 세트와 홀드아웃을 나눈 이유

설명을 손보면서 **같은 프롬프트로 재면 반드시 좋아진다.** 실제로 그랬다 — 어떤 수정안이
튜닝 세트에서 55/60 → 60/60 이었는데 홀드아웃에서는 40/60 → 40/60 으로 **순 효과가 0**
이었다(미스 하나를 고치고 다른 하나를 깼다). 그래서 **HOLDOUT 은 설명을 고칠 때 보지
않는다.** 판정은 홀드아웃으로만 한다.

## `--descriptions repo` 는 무엇인가

`POST /v1/capabilities` 는 같은 `(code, version)` 이 이미 있으면 거절하고 **갱신 경로가
없다.** 데모 스크립트는 그 오류를 삼키고 기존 id 를 쓴다 — 즉 **저장소에서 설명을 고쳐도
이미 등록된 스택에는 안 들어간다.** `repo` 는 `scripts/*_demo.sh` 가 등록하려는 설명을
읽어 카탈로그 위에 덮어 씌워, **빈 볼륨에서 뜬 스택이 할 행동**을 미리 본다.
`live` 와 `repo` 의 차이가 곧 그 드리프트의 크기다.

## 전제

살아 있는 Core(능력이 등록돼 있어야 한다 — `scripts/*_demo.sh`)와 Ollama.
`capreq` 를 `PYTHONPATH` 에 둔다. **새 의존성은 없다** (`httpx` 는 capreq 것).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 사람이 고른 프롬프트다. 「맞다」는 기대값도 사람이 정했다 — 정답표가 아니다.
TUNING: list[tuple[str, str]] = [
    ("로그에서 이메일 주소랑 IP 좀 찾아줘", "text.ner"),
    ("이 글에 나오는 날짜랑 URL 전부 뽑아줘", "text.ner"),
    ("이 문서에서 제목이랑 담당자 같은 항목 뽑아줘", "text.extract"),
    ("Ticket: INC-1 처럼 콜론으로 적힌 항목들 정리해줘", "text.extract"),
    ("회의록에서 '작성자:' '일시:' 같은 줄만 모아줘", "text.extract"),
    ("후보 문장들을 질의랑 겹치는 단어 기준으로 줄 세워줘", "text.rank"),
    ("이 문자열이 이메일인지 URL인지 종류를 알려줘", "text.classify"),
    ("이 문장을 벡터로 바꿔줘", "text.embed"),
    ("이 사진이 뭔지 분류해줘", "image.classify"),
    ("이 이미지를 벡터로 바꿔줘", "image.embed"),
    ("이 표에서 열 타입이랑 행 좀 읽어줘", "table.extract"),
    ("이 시계열 다음 값 예측해줘", "timeseries.forecast"),
]

# **설명을 고칠 때 이 세트를 보지 않는다.** 보는 순간 홀드아웃이 아니게 된다.
HOLDOUT: list[tuple[str, str]] = [
    ("본문에서 연락처 메일이랑 접속 주소만 골라줘", "text.ner"),
    ("여기 적힌 UUID 랑 날짜 위치까지 알려줘", "text.ner"),
    ("리포트 안에 IP 몇 개나 나오는지 표시해줘", "text.ner"),
    ("설정 파일에서 옵션 이름이랑 설정값 짝지어 줘", "text.extract"),
    ("머리말에 붙은 항목명이랑 내용 목록으로 만들어줘", "text.extract"),
    ("질문이랑 단어가 많이 겹치는 문장을 위로 올려줘", "text.rank"),
    ("이 토큰이 어떤 형식에 속하는지 이름 붙여줘", "text.classify"),
    ("문장 임베딩 뽑아줘", "text.embed"),
    ("위성 사진 종류 판별해줘", "image.classify"),
    ("그림 특징 벡터 만들어줘", "image.embed"),
    ("텍스트 표 파싱해서 컬럼 종류 알려줘", "table.extract"),
    ("지난 값들로 다음 구간 추정해줘", "timeseries.forecast"),
]

SETS = {"tuning": TUNING, "holdout": HOLDOUT}

_CODE = re.compile(r'"code"\s*:\s*"([a-z][a-z0-9_.]*)"')
_DESC = re.compile(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"')


def repo_descriptions() -> dict[str, str]:
    """`scripts/*_demo.sh` 가 **등록하려는** 설명. 살아 있는 카탈로그와 다를 수 있다."""
    out: dict[str, str] = {}
    for path in sorted((ROOT / "scripts").glob("*demo*.sh")):
        text = path.read_text(encoding="utf-8")
        for m in _CODE.finditer(text):
            code = m.group(1)
            if code in out:
                continue
            d = _DESC.search(text, m.end(), m.end() + 2000)
            if d:
                out[code] = d.group(1)
    return out


class _Patched:
    """카탈로그 목록은 그대로 두고 **설명만** 갈아 끼운다."""

    def __init__(self, inner, patch: dict[str, str]) -> None:
        self.inner = inner
        self.patch = patch

    def list_capabilities(self):
        from capreq.adapters.base import CapabilityInfo

        return [
            CapabilityInfo(
                code=c.code,
                version=c.version,
                name=c.name,
                description=self.patch.get(c.code, c.description),
            )
            for c in self.inner.list_capabilities()
        ]


def run_set(router, prompts, repeats: int) -> tuple[int, int]:
    hit_total = 0
    for prompt, want in prompts:
        got: Counter[str] = Counter()
        for _ in range(repeats):
            decision = router.route(prompt)
            got[decision.capability_code or "None"] += 1
        hit = got[want]
        hit_total += hit
        others = ", ".join(f"{k}:{v}" for k, v in got.most_common() if k != want)
        print(f"  {hit}/{repeats}  want={want:20s} {others:28s} | {prompt}")
    return hit_total, len(prompts) * repeats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--core", default=os.environ.get("CAPREQ_CORE_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--ollama", default=os.environ.get("CAPREQ_OLLAMA_URL", "http://127.0.0.1:11434"))
    ap.add_argument("--repeats", type=int, default=5, help="같은 프롬프트를 몇 번 물을지")
    ap.add_argument("--set", dest="which", choices=("tuning", "holdout", "both"), default="holdout",
                    help="판정은 holdout 으로만 한다 (기본값)")
    ap.add_argument("--descriptions", choices=("live", "repo"), default="live",
                    help="live=등록된 그대로 · repo=scripts/*_demo.sh 가 등록하려는 설명으로 덮어씀")
    args = ap.parse_args()

    try:
        from capreq.adapters.capnet import CapNetAdapter
        from capreq.ollama import OllamaClient
        from capreq.router import CapabilityRouter
    except ImportError as exc:  # 새 의존성을 넣지 않았으므로 친절히 알려만 준다.
        print(f"capreq 를 못 읽었다 ({exc}). PYTHONPATH=capreq/src 로 실행한다.", file=sys.stderr)
        return 2

    catalog = CapNetAdapter(args.core)
    codes = sorted({c.code for c in catalog.list_capabilities()})
    if args.descriptions == "repo":
        patch = repo_descriptions()
        catalog = _Patched(catalog, patch)
        print(f"# 설명 = repo ({len(patch)}종 덮어씀) — 빈 볼륨에서 뜬 스택이 할 행동")
    else:
        print("# 설명 = live (등록된 그대로)")
    print(f"# 카탈로그 {len(codes)}종: {', '.join(codes)}")

    router = CapabilityRouter(catalog=catalog, llm=OllamaClient(args.ollama))

    names = ("tuning", "holdout") if args.which == "both" else (args.which,)
    for name in names:
        print(f"\n== {name} (R={args.repeats})")
        hit, total = run_set(router, SETS[name], args.repeats)
        print(f"   합계 {hit}/{total}")

    print("\n정확도를 주장하지 않는다 — 프롬프트도 기대값도 사람이 고른 것이다.")
    print("이 숫자는 변경 전후의 차이를 보는 데만 쓴다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
