r"""학습 스크립트가 **런타임과 같은 핀**으로 torch·safetensors·numpy·pillow 를 깔도록 강제됐는가 (최종 G · G2 · `#151` 형제).

## 왜 있는가

`#151` 이 SBOM 도구를 핀했다. 형제를 훑으니 학습 스크립트 다섯(`train_*.sh` 넷 · `train_scratch.ps1`)이 `pip install -q torch …` 를
**무버전**으로 깔고 있었다 — Dockerfile 은 `TORCH_VERSION=2.13.0+cpu` 로 핀하는데, 2차 심사(F4) 때 재학습하면 다른 torch 로
다른 가중치가 나올 수 있다. 정본을 두 번 적지 않고 **읽는다**: torch 는 Dockerfile ARG, 나머지는 `apps/node/requirements.txt`.

## 실측 (2026-09-07)

| 스크립트 | 전 | 후 |
|---|---|---|
| `train_scratch.sh`·`train_scratch.ps1` | `torch torchvision safetensors pillow` 무버전 | `torch==$torch_ver` … 넷 다 정본에서 읽음 |
| `train_text_scratch.sh`·`train_series_scratch.sh`·`train_text_embed.sh` | `torch safetensors numpy` 무버전 | 셋 다 정본에서 읽음 |

## 재현

```bash
python3 -m unittest tests.test_training_pins_match_the_runtime
```
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import hash_comment_free  # noqa: E402

SH = sorted((ROOT / "scripts").glob("train_*.sh"))
PS1 = ROOT / "scripts" / "train_scratch.ps1"


class TestTrainingReadsTheRuntimePins(unittest.TestCase):
    def test_four_shell_scripts(self) -> None:
        self.assertEqual(4, len(SH), [p.name for p in SH])
        for p in SH:
            with self.subTest(script=p.name):
                body = hash_comment_free(p)
                self.assertIn("s/^ARG TORCH_VERSION=//p", body, "Dockerfile 에서 torch 핀을 안 읽는다")
                self.assertIn("s/^safetensors==//p", body, "requirements 에서 safetensors 핀을 안 읽는다")
                self.assertRegex(body, r'torch==\$torch_ver', "torch 를 핀 없이 깐다")
                self.assertRegex(body, r'safetensors==\$sf_ver')
                # 최종 G1: `-q` 없는 `pip install torch` 가 빠져나갔다 — 플래그를 선택으로
                self.assertNotRegex(body, r"pip install(?: -\w+)* (torch|torchvision|safetensors|numpy|pillow)\b", "무버전 설치가 남아 있다")
                self.assertIn('exit 1', body[body.index("torch_ver="):body.index("docker run")], "핀을 못 읽으면 멈춰야 한다")

    def test_powershell_twin(self) -> None:
        body = hash_comment_free(PS1)
        self.assertIn('Select-String "^ARG TORCH_VERSION=(.+)$"', body)
        self.assertIn('Select-String "^safetensors==(.+)$"', body)
        self.assertIn('torch==$torchVer', body)
        self.assertNotRegex(body, r"pip install(?: -\w+)* (torch|torchvision|safetensors|pillow)\b")

    def test_the_pins_exist_at_the_sources(self) -> None:
        df = (ROOT / "apps" / "node" / "Dockerfile").read_text(encoding="utf-8")
        self.assertRegex(df, r"(?m)^ARG TORCH_VERSION=\S+", "Dockerfile ARG 가 없다")
        req = (ROOT / "apps" / "node" / "requirements.txt").read_text(encoding="utf-8")
        for name in ("safetensors", "numpy", "pillow"):
            self.assertRegex(req, rf"(?m)^{name}==\S+")


if __name__ == "__main__":
    unittest.main()
