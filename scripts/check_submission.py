#!/usr/bin/env python3
"""출품 패키지 기계 점검 (SD-005).

`docs/ops/contest-submission-checklist.md` 의 항목 중 **기계로 확인 가능한 것**만 본다.
영상·촬영·포털 업로드는 사람이 한다 — 여기서 다루지 않는다.

왜 있나
    촬영 당일에 사람이 눈으로 훑는 것은 재현되지 않는다. 8/23 에 한 번 더,
    Release 만들 때 또 한 번 봐야 하는 항목들이라 자동으로 고정해 둔다.

표준 라이브러리만 쓴다 (새 의존성 0). git 은 서브프로세스로 부른다.

    python3 scripts/check_submission.py
    python3 scripts/check_submission.py --verbose
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 동봉하면 안 되는 것 — 원본 데이터셋·대용량 산출물·안전하지 않은 가중치 형식
FORBIDDEN_TRACKED = [
    (r"EuroSAT.*\.zip$", "EuroSAT 원본 (D6 · 라이선스 · 용량)"),
    (r"^data/golden-n300", "본편 골든셋 n300 (SD-003)"),
    (r"^artifacts/", "실험 산출물"),
    (r"\.(pt|pth|pkl|pickle)$", "pickle 계열 가중치 — 로드가 곧 임의 코드 실행 (절대규칙 5)"),
]

# 반드시 남아 있어야 하는 것 — 삭제하면 재현이 깨진다
REQUIRED_WEIGHTS = [
    "apps/node/weights/eurosat_scratch.safetensors",
    "apps/node/weights/eurosat_scratch_b.safetensors",
    # text.classify 참조 모델 (단계 5). 학습 데이터는 규칙 생성 — 외부 말뭉치 없음.
    "apps/node/weights/text_struct_scratch.safetensors",
    # text.embed 참조 사영 (단계 6 ①). 라벨 학습 없음 — 고정 시드 초기화.
    "apps/node/weights/text_embed_scratch.safetensors",
    # timeseries.forecast 참조 모델 (단계 6 ②). 학습 데이터는 규칙 생성.
    "apps/node/weights/series_scratch.safetensors",
    # text.ner 규칙 기반 (PR-B). 파라미터 0 · rule_ner.safetensors.
    "apps/node/weights/rule_ner.safetensors",
    # text.extract 규칙 기반 (Wave C). 파라미터 0 — rule_ner 과 **바이트가 같다**
    # (둘 다 버퍼 rule_marker 한 칸). 구별하는 것은 arch 다.
    "apps/node/weights/rule_extract.safetensors",
    # text.rank 규칙 기반 (Wave G). 파라미터 0 — 위 둘과 **셋 다 바이트가 같다**.
    "apps/node/weights/rule_rank.safetensors",
    # safety.pii 규칙 기반 (Wave L). 파라미터 0 — 위 셋과 **넷 다 바이트가 같다**.
    "apps/node/weights/rule_pii.safetensors",
]

REQUIRED_FILES = ["LICENSE", "NOTICE", "THIRD-PARTY-LICENSES.md", "sbom.json"]

# 시크릿으로 의심되는 값. 문서의 예시(placeholder)는 걸러낸다.
SECRET_PATTERNS = [
    (r"(?i)\b(aws_secret_access_key|api[_-]?secret)\s*[=:]\s*['\"][A-Za-z0-9/+=]{16,}", "자격증명 리터럴"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "개인키"),
    (r"(?i)\bghp_[A-Za-z0-9]{30,}", "GitHub 토큰"),
]

ZIP_LIMIT_MB = 50

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout


def tracked_files() -> list[str]:
    return [line for line in git("ls-files").splitlines() if line]


def check_forbidden(files: list[str]) -> None:
    for pattern, why in FORBIDDEN_TRACKED:
        hits = [f for f in files if re.search(pattern, f)]
        check(not hits, f"미동봉: {why}", ", ".join(hits[:3]))


def check_required_weights(files: list[str]) -> None:
    for path in REQUIRED_WEIGHTS:
        check(path in files, f"필수 가중치 유지: {Path(path).name}")
    stray = [f for f in files if f.endswith(".safetensors") and f not in REQUIRED_WEIGHTS
             and not f.endswith("placeholder.safetensors")]
    check(not stray, "실험 가중치는 커밋하지 않는다", ", ".join(stray[:3]))


def check_required_files(files: list[str]) -> None:
    for path in REQUIRED_FILES:
        check(path in files, f"필수 파일: {path}")


def check_no_pretrained() -> None:
    """D6 — 사전학습 가중치 미사용. meta 가 pretrained=false 라고 선언해야 한다."""
    metas = sorted((ROOT / "apps/node/weights").glob("*.meta.json"))
    checked = 0
    bad: list[str] = []
    for m in metas:
        try:
            data = json.loads(m.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            bad.append(f"{m.name}: 읽기 실패")
            continue
        if data.get("pretrained") is not False:
            bad.append(f"{m.name}: pretrained={data.get('pretrained')!r}")
        checked += 1
    check(checked > 0 and not bad,
          f"사전학습 미사용 선언 (meta {checked}건)", "; ".join(bad[:3]))


def _pyproject_deps(path: Path) -> list[str]:
    """`pyproject.toml` 의 **런타임·extra 의존성** 이름만.

    `tomllib` 는 표준 라이브러리다 (3.11+) — 이 스크립트의 「의존성 설치 없음」 규약을
    깨지 않는다. 처음엔 정규식으로 짰다가 `[tool.setuptools] packages.find` 의
    `where = ["src"]` 와 `package-data` 까지 의존성으로 집었다. **파서를 쓴다.**

    `[build-system] requires` 는 안 본다 — 빌드 도구는 배포물에 안 들어간다.
    """
    import tomllib

    with path.open("rb") as fh:
        doc = tomllib.load(fh)
    project = doc.get("project") or {}
    specs: list[str] = list(project.get("dependencies") or [])
    for extra in (project.get("optional-dependencies") or {}).values():
        specs.extend(extra)
    names: list[str] = []
    for raw in specs:
        name = re.split(r"[\[=<>!~;\s]", raw)[0].strip().lower()
        if name:
            names.append(name)
    return names


def check_deps_declared(files: list[str]) -> None:
    """의존성이 THIRD-PARTY-LICENSES.md 에 적혀 있는가 (CLAUDE.md 저장소 규칙).

    **`capreq/pyproject.toml` 이 빠져 있었다 (2026-09-02).** 검사는 `apps/core`·`apps/node`
    의 `requirements.txt` 만 봤는데, `capreq` 는 저장소에 함께 배포되는 모듈이고
    자기 의존성을 `pyproject.toml` 로 선언한다 (`httpx` · extra 로 `fastapi`·`uvicorn`·
    `python-multipart`).

    지금은 그 넷이 전부 고지돼 있어 **통과하고 있었다** — 구멍이 잠재해 있었을 뿐이다.
    `CLAUDE.md` 는 「의존성을 추가하는 커밋에서 한 줄을 같이 넣는다. **예외 없음**」이라고
    적는데, 검사가 보는 범위에 예외가 있었다.
    """
    declared = (ROOT / "THIRD-PARTY-LICENSES.md").read_text(encoding="utf-8").lower()
    missing: list[str] = []
    seen = 0
    for req in ("apps/core/requirements.txt", "apps/node/requirements.txt",
                "apps/train/requirements.txt"):
        p = ROOT / req
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = re.split(r"[\[=<>!~;]", line)[0].strip().lower()
            if name:
                seen += 1
                if name not in declared:
                    missing.append(name)
    for proj in ("capreq/pyproject.toml",):
        p = ROOT / proj
        if not p.is_file():
            continue
        for name in _pyproject_deps(p):
            seen += 1
            if name not in declared:
                missing.append(name)
    # **0개를 훑으며 통과하는 상태를 막는다.** 경로가 바뀌면 조용해지는 것이 이 검사의
    # 원래 실패 방식이었다.
    check(seen > 5 and not missing,
          f"의존성이 THIRD-PARTY-LICENSES 에 있다 ({seen}건 확인)",
          ", ".join(sorted(set(missing))))


def check_secrets(files: list[str]) -> None:
    check(".env" not in files, ".env 미추적")
    hits: list[str] = []
    for f in files:
        p = ROOT / f
        if not p.is_file() or p.stat().st_size > 512_000:
            continue
        if p.suffix in (".jpg", ".png", ".zip", ".safetensors"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern, why in SECRET_PATTERNS:
            if re.search(pattern, text):
                hits.append(f"{f}: {why}")
    check(not hits, "시크릿 리터럴 없음", "; ".join(hits[:3]))


def check_links() -> None:
    """상대 링크가 실제 파일을 가리키는가.

    GitHub Wiki 링크(`(Page-Name)` — 확장자도 슬래시도 없는 것)는 파일이 아니므로 제외한다.
    """
    broken: list[str] = []
    total = 0
    for f in ROOT.rglob("*.md"):
        if ".git" in f.parts:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", text):
            target = m.group(2).split("#")[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if "/" not in target and "." not in target:
                continue  # Wiki 페이지명
            total += 1
            if not (f.parent / target).resolve().exists():
                broken.append(f"{f.relative_to(ROOT)} → {target}")
    check(not broken, f"상대 링크 {total}개 유효", "; ".join(broken[:3]))


def check_golden_spec_single() -> None:
    """골든셋 정본이 하나여야 한다 (체크리스트 §문서 위생)."""
    specs = list((ROOT / "docs/spec/golden").glob("image-classify-v*.md"))
    check(len(specs) == 1, "골든셋 정본 spec 1개",
          ", ".join(s.name for s in specs) if len(specs) != 1 else "")


def check_package_size() -> None:
    out = subprocess.run(
        ["git", "archive", "--format=zip", "HEAD"],
        cwd=ROOT, capture_output=True, check=False,
    )
    mb = len(out.stdout) / 1048576
    check(0 < mb <= ZIP_LIMIT_MB, f"패키지 {mb:.1f} MB ≤ {ZIP_LIMIT_MB} MB")


def check_golden_sha() -> None:
    rc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_golden_sha.py")],
        cwd=ROOT, capture_output=True, check=False,
    ).returncode
    check(rc == 0, "골든셋 sha 정합 (SD-013)", "" if rc == 0 else "check_golden_sha.py 실패")


# 원고가 「기대 출력」으로 예고하는 수치. 정본은 docs/spec/demo-expectation.json 하나다.
# README 도 대상이다 — 심사위원이 **가장 먼저** 보고 그대로 돌려 보는 예고표가 거기 있고,
# 실제로 홀드아웃 재추출 뒤 README 만 0.7000 을 들고 남아 있었다 (원고는 고쳐졌는데).
REPORT_DRAFTS = (
    "docs/ops/contest-report-draft.md",
    "docs/ops/contest-report-form-draft.md",
    "README.md",
)
# 「성적 수치」로 보는 두 모양만 좁게 잡는다.
#   ① 이름에 **붙은** 값 — acc=0.8500 · 정확도 0.8500 · macro_f1 0.8344 · f1 0.8344
#   ② 실측 표의 행 — 줄이 `|` 로 시작하고 `dummy=false` 가 있는 것
# 넓게 잡으면 다른 실측을 오탐한다. 실제로 A/B 통과자 폭(0.1767)과
# n=300 paired |Δacc|(0.0467)이 걸렸다 — 둘 다 데모 기대치가 아니라 별개 관측이다.
_ATTACHED = re.compile(r"(?:acc|정확도|macro[-_ ]?f1|f1)\s*[=:]?\s*(0\.\d{4})", re.I)
_TABLE_ROW = re.compile(r"^\|.*dummy=false")
_FOUR_DP = re.compile(r"\b0\.\d{4}\b")


def check_demo_expectation() -> None:
    """보고서가 예고한 재현 수치가 정본과 같은가 (SD-013 과 같은 이유).

    심사위원이 README 대로 돌렸을 때 보는 값이다. 흩어져 있으면 또 어긋난다 —
    실제로 홀드아웃 재추출 뒤 원고가 0.7000 을 그대로 들고 있었다.

    과거 실측 기록(`phase1-verdict.md`)은 **대상이 아니다.** 그건 역사다.
    """
    spec = ROOT / "docs" / "spec" / "demo-expectation.json"
    if not spec.is_file():
        check(False, "데모 기대치 정본이 있다", str(spec))
        return
    exp = json.loads(spec.read_text(encoding="utf-8"))
    allowed = {exp["accuracy"], exp["macro_f1"], exp["invalid_rate"]}

    bad: list[str] = []
    seen = 0
    for rel in REPORT_DRAFTS:
        path = ROOT / rel
        if not path.is_file():
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            nums = _ATTACHED.findall(line)
            if _TABLE_ROW.match(line.strip()):
                nums += _FOUR_DP.findall(line)
            for num in nums:
                seen += 1
                if num not in allowed:
                    bad.append(f"{rel}:{i} {num}")
    check(not bad, "보고서 예고 수치가 정본과 같다",
          f"{seen}개 대조" if not bad else "; ".join(bad[:3]))
    check(seen > 0, "예고 수치를 실제로 찾았다 (0개 대조로 통과 금지)", f"{seen}개")

def check_clean_tree() -> None:
    dirty = [line for line in git("status", "--porcelain").splitlines() if line]
    check(not dirty, "워킹트리 깨끗 (패키징 전)", f"{len(dirty)}개 변경" if dirty else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--skip-tree", action="store_true",
                    help="워킹트리 깨끗함 검사를 건너뛴다 (작업 중 실행용)")
    args = ap.parse_args()

    files = tracked_files()
    if not files:
        print("git 저장소가 아니거나 추적 파일이 없다", file=sys.stderr)
        return 1

    print(f"출품 패키지 점검 — 추적 파일 {len(files)}개\n")
    check_forbidden(files)
    check_required_weights(files)
    check_required_files(files)
    check_no_pretrained()
    check_deps_declared(files)
    check_secrets(files)
    check_links()
    check_golden_spec_single()
    check_golden_sha()
    check_demo_expectation()
    check_package_size()
    if not args.skip_tree:
        check_clean_tree()

    failed = [r for r in results if not r[0]]
    for ok, name, detail in results:
        if ok and not args.verbose:
            continue
        mark = "OK  " if ok else "FAIL"
        print(f"  {mark} {name}" + (f" — {detail}" if detail else ""))

    print()
    print(f"{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        print("\n실패:")
        for _, name, detail in failed:
            print(f"  - {name}" + (f" — {detail}" if detail else ""))
        print("\n영상·촬영·포털 업로드는 이 검사 밖이다 — checklist 를 본다.")
        return 1
    print("기계 점검 통과. 남은 것은 영상·촬영·포털 (사람이 한다).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
