r"""빌드 ARG 가 **사전학습 가중치 경로를 열지 않는가** (큐 #62 · 절대규칙 6).

## 왜 있는가

절대규칙 6 은 「**사전학습 가중치를 쓰거나 동봉하지 않는다. EuroSAT scratch 학습만.
대회 2차 라이선스 검증 대비.**」다. 그런데 `test_absolute_rules_are_enforced` 는 스스로
적는다 — 「규칙 1·**6** 은 여기서 안 본다」.

**빌드 표면은 그 규칙을 조용히 뒤집을 수 있는 자리다.** `INSTALL_TORCH=true` 는 torch 를
깔고, torch 를 깔면 `torchvision.models` 한 줄이면 사전학습 가중치를 **런타임에 내려받는다.**
Dockerfile 의 `curl` 한 줄도 같다. 둘 다 소스에는 「가중치 파일」이 안 보인다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| Dockerfile 의 빌드 ARG | **3** — `INSTALL_TORCH` · `TORCH_VERSION` · `TORCHVISION_VERSION` |
| 그 ARG 가 여는 것 | CPU 휠 인덱스에서 **torch·torchvision 패키지**뿐 |
| `torchvision.models` · `torch.hub` · `from_pretrained` · `timm` | **0** ✅ |
| Dockerfile 안의 `curl`·`wget`·`ADD http` | **0** ✅ |
| 학습 스크립트가 기록하는 값 | `"pretrained": False` — **4곳 전부** ✅ |

**0건이다.** 라이선스 검증에서 「안 썼다」를 말하려면 **그것을 세는 검사**가 있어야 한다.

## 무엇을 안 보나

- **런타임에 사람이 넣는 것.** `/weights` 볼륨에 남의 파일을 넣는 것은 막을 수 없다 —
  그건 가중치 해시·`safetensors` 검사(절대규칙 5)가 다른 각도로 본다
- 패키지 **안에 들어 있는** 가중치. `torch`·`torchvision` 배포본에는 없다
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILES = tuple(sorted(ROOT.glob("apps/*/Dockerfile")))
TREES = (ROOT / "apps", ROOT / "capreq" / "src")

# 오늘의 빌드 ARG. 늘리면 **무엇을 여는지** 여기서 답하게 한다.
ALLOWED_ARGS = {
    "INSTALL_TORCH": "torch 설치 여부 — 패키지만, 가중치 아님",
    "TORCH_VERSION": "휠 버전 핀 (SBOM 이 여기서 읽는다)",
    "TORCHVISION_VERSION": "같음",
}

# 사전학습 가중치를 **내려받는** 길들.
PRETRAINED = re.compile(
    r"torchvision\.models|torch\.hub|from_pretrained|\btimm\b|model_zoo|load_state_dict_from_url")
DOWNLOAD = re.compile(r"^\s*(?:RUN\s+.*\b(?:curl|wget)\b|ADD\s+https?://)", re.M)
ARG = re.compile(r"^ARG\s+([A-Z_][A-Z0-9_]*)", re.M)


def _python_files() -> list[Path]:
    out: list[Path] = []
    for tree in TREES:
        if tree.is_dir():
            out += [p for p in tree.rglob("*.py") if "__pycache__" not in p.parts]
    return sorted(out)


class TestBuildArgsAreAccountedFor(unittest.TestCase):
    def test_every_arg_says_what_it_opens(self) -> None:
        found: set[str] = set()
        for path in DOCKERFILES:
            found |= set(ARG.findall(path.read_text(encoding="utf-8")))
        self.assertTrue(found, "Dockerfile 에서 ARG 를 하나도 못 찾았다")
        new = sorted(found - set(ALLOWED_ARGS))
        self.assertEqual([], new, f"무엇을 여는지 안 적힌 빌드 ARG: {new}")

    def test_the_list_has_no_ghosts(self) -> None:
        found: set[str] = set()
        for path in DOCKERFILES:
            found |= set(ARG.findall(path.read_text(encoding="utf-8")))
        self.assertEqual(set(), set(ALLOWED_ARGS) - found,
                         f"사라진 ARG 가 목록에 남아 있다: {set(ALLOWED_ARGS) - found}")

    def test_no_dockerfile_downloads_anything(self) -> None:
        """`curl` 한 줄이면 소스에 안 보이는 가중치가 이미지에 들어온다."""
        bad = [p.parent.name for p in DOCKERFILES
               if DOWNLOAD.search(p.read_text(encoding="utf-8"))]
        self.assertEqual([], bad, f"Dockerfile 이 무언가를 내려받는다: {bad}")


class TestNoPretrainedPathInCode(unittest.TestCase):
    def test_no_module_reaches_for_pretrained_weights(self) -> None:
        """**여기가 핵심이다.** torch 가 깔려 있으면 한 줄이면 된다."""
        bad = []
        for path in _python_files():
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                if PRETRAINED.search(line):
                    bad.append(f"{path.relative_to(ROOT).as_posix()}:{i}")
        self.assertEqual([], bad, f"사전학습 가중치 경로: {bad}")

    def test_training_scripts_record_pretrained_false(self) -> None:
        """산출물에 남아야 나중에 「안 썼다」를 증명할 수 있다."""
        scripts = sorted((ROOT / "apps" / "train").glob("train_*.py"))
        self.assertGreaterEqual(len(scripts), 4, f"학습 스크립트 {len(scripts)}개")
        bad = [p.name for p in scripts
               if '"pretrained": False' not in p.read_text(encoding="utf-8")]
        self.assertEqual([], bad, f"`pretrained: False` 를 안 적는 학습 스크립트: {bad}")


class TestProbeActuallyScans(unittest.TestCase):
    def test_enough_files_are_read(self) -> None:
        self.assertGreaterEqual(len(_python_files()), 40, len(_python_files()))
        self.assertGreaterEqual(len(DOCKERFILES), 2, [p.parent.name for p in DOCKERFILES])

    def test_the_detector_discriminates(self) -> None:
        """탐지기가 아무것도 못 잡으면 위 검사가 **공허하게** 통과한다."""
        self.assertTrue(PRETRAINED.search("m = torchvision.models.resnet18(weights='DEFAULT')"))
        self.assertTrue(PRETRAINED.search("model = AutoModel.from_pretrained('bert')"))
        self.assertTrue(DOWNLOAD.search("RUN curl -sSL https://example/w.pth -o /w.pth"))
        self.assertFalse(PRETRAINED.search("from safetensors.torch import load_file"))
        self.assertFalse(DOWNLOAD.search('RUN pip install --no-cache-dir -r /app/requirements.txt'))

    def test_the_rule_stays_written(self) -> None:
        rule = "사전학습 가중치를 쓰거나 동봉하지 않는다"
        self.assertTrue(rule in (ROOT / "CLAUDE.md").read_text(encoding="utf-8"),
                        f"CLAUDE.md 에서 절대규칙 6 이 사라졌다: «{rule}»")


if __name__ == "__main__":
    unittest.main()
