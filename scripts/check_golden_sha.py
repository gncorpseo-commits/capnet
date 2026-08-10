#!/usr/bin/env python3
"""골든셋 sha 정합 검사 (SD-013).

커밋된 매니페스트에서 **재계산한** sha 를 정본으로 두고, 그 값을 선언한 모든 곳이
같은 값을 말하는지 본다. 하나라도 어긋나면 실패한다.

왜 필요한가
    2026-08-10 홀드아웃 재추출 때 매니페스트만 교체되고 선언부 네 곳이 따라오지 않아
    sha 가 세 갈래로 갈렸다. 사슬 자체는 self-consistent 라서
    (스크립트가 gate_run 스냅샷을 되읽는다) 데모는 그대로 통과했다 — 조용히 틀렸다.
    이 검사는 그 상태를 커밋 전에 잡는다.

정본 정의
    `scripts/extract_golden.py` 가 쓰는 것과 동일한 정본화:
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\\n"
    의 sha256.

사용:
    python3 scripts/check_golden_sha.py            # 전체 검사
    python3 scripts/check_golden_sha.py --print    # 정본 sha 만 출력
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANIFEST = ROOT / "docs/spec/golden/manifest-image-classify-v1.json"
CASES_DIR = ROOT / "docs/spec/golden/cases"

# sha 를 선언하는 곳. (경로, 설명, 추출 함수) — 하나라도 빠지면 이 검사의 의미가 준다.
SPEC_MD = ROOT / "docs/spec/golden/image-classify-v1.md"
MACHINE_PIN = ROOT / "docs/spec/golden/eurosat-rgb.json"
SEED_SQL = ROOT / "apps/core/sql/seed.sql"
REPORT_DRAFT = ROOT / "docs/ops/contest-report-draft.md"

SHA_RE = r"[0-9a-f]{64}"


def canonical_sha256(manifest_path: Path) -> str:
    """extract_golden.py 와 같은 방식으로 매니페스트 sha 를 재계산한다."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def declared_in_spec_md(path: Path) -> str | None:
    m = re.search(rf"`golden_set_sha256`\s*=\s*`({SHA_RE})`", path.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def declared_in_machine_pin(path: Path) -> str | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("golden_demo", {}).get("manifest_sha256")


def declared_in_seed(path: Path) -> str | None:
    """seed 의 capability INSERT 에 있는 golden_set_sha256 리터럴."""
    text = path.read_text(encoding="utf-8")
    # golden_set_ref 바로 다음 줄의 64자 hex 리터럴이 golden_set_sha256 이다.
    m = re.search(
        rf"'docs/spec/golden/manifest-image-classify-v1\.json'\s*,\s*\n\s*'({SHA_RE})'",
        text,
    )
    return m.group(1) if m else None


def declared_in_report(path: Path) -> str | None:
    """보고서는 앞 8자만 인용한다. 접두사로 비교한다."""
    m = re.search(r"`golden_set_sha256`\s*\|\s*`([0-9a-f]{8})", path.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def check_cases(manifest_path: Path, cases_dir: Path) -> list[str]:
    """매니페스트가 적은 케이스 sha 와 실제 파일이 같은지 본다."""
    problems: list[str] = []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for case in data["cases"]:
        f = cases_dir / Path(case["file"]).name
        if not f.is_file():
            problems.append(f"케이스 파일 없음: {case['caseId']} → {f.name}")
            continue
        actual = hashlib.sha256(f.read_bytes()).hexdigest()
        if actual != case["sha256"]:
            problems.append(
                f"케이스 sha 불일치: {case['caseId']} "
                f"매니페스트={case['sha256'][:12]} 실제={actual[:12]}"
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true", dest="print_only",
                    help="정본 sha 만 출력하고 끝낸다")
    args = ap.parse_args()

    if not MANIFEST.is_file():
        print(f"매니페스트 없음: {MANIFEST}", file=sys.stderr)
        return 1

    truth = canonical_sha256(MANIFEST)
    if args.print_only:
        print(truth)
        return 0

    print(f"정본 (매니페스트 재계산): {truth}")

    checks: list[tuple[str, str | None, bool]] = [
        (str(SPEC_MD.relative_to(ROOT)), declared_in_spec_md(SPEC_MD), False),
        (str(MACHINE_PIN.relative_to(ROOT)), declared_in_machine_pin(MACHINE_PIN), False),
        (str(SEED_SQL.relative_to(ROOT)), declared_in_seed(SEED_SQL), False),
        (str(REPORT_DRAFT.relative_to(ROOT)), declared_in_report(REPORT_DRAFT), True),
    ]

    problems: list[str] = []
    for label, declared, is_prefix in checks:
        if declared is None:
            problems.append(f"{label}: sha 선언을 찾지 못했다 — 검사기가 낡았거나 문서가 바뀌었다")
            print(f"  {label:<46s} ???")
            continue
        ok = truth.startswith(declared) if is_prefix else declared == truth
        shown = declared if not is_prefix else declared + "…"
        print(f"  {label:<46s} {shown}  {'OK' if ok else '불일치'}")
        if not ok:
            problems.append(f"{label}: {shown} ≠ 정본 {truth[:12]}…")

    case_problems = check_cases(MANIFEST, CASES_DIR)
    print(f"  케이스 파일 {len(json.loads(MANIFEST.read_text(encoding='utf-8'))['cases'])}건 "
          f"{'OK' if not case_problems else '불일치 ' + str(len(case_problems)) + '건'}")
    problems.extend(case_problems)

    if problems:
        print("\n불일치:")
        for p in problems:
            print(f"  - {p}")
        print("\n골든셋을 교체했다면 위 선언부를 모두 새 sha 로 맞춘다.")
        print("기존 볼륨은 migrations/ 로 올린다 (seed.sql 은 새 볼륨에만 적용된다).")
        return 1

    print("\n정합 OK — 매니페스트·선언부·케이스 파일이 모두 같은 골든셋을 가리킨다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
