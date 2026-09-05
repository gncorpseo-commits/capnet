r"""「**0** 이어야 한다」고 적은 것을 **다시 잴 수 있는가** (G3).

G3 는 「「오늘은 0」인 전수의 재현 명령을 `tests/` 에 남겼는가 — 없으면 핀」이다.
문서의 「0건」 주장 **열일곱**을 훑어 둘이 남았다 — 나머지는 시장·회차 기록이라 대상이 아니다.

## ① 운영 안내가 부르는 지표 넷

`operate-production.md` §7 은 운영자에게 이렇게 시킨다:

```text
- nodes_without_credential 이 0
- drift_routable · arch_unbound_routable 이 0
- api_keys_active 가 1 이상
```

**그 이름이 응답에 없으면 운영자의 확인은 조용히 아무것도 안 본다.** `python3 -m json.tool`
로 보면 없는 키는 그냥 안 보이고, 「0 이다」와 「필드가 없다」가 화면에서 **같아 보인다.**
`#207`(끊긴 Node 가 한가한 Node 처럼 보였다)과 같은 모양이다.

## ② 대회 제출 문서의 「외부 AI API 호출 **0건**」

`contest-report-form-draft.md` 의 독립 구동 항목이다. 심사에서 확인하는 주장인데
**세는 검사가 없었다.** 라우팅은 **로컬 Ollama**(`127.0.0.1:11434`)를 쓰고 추론은 로컬
torch 다 — 그 사실을 코드에서 다시 낸다.

## 실측 (2026-09-05)

| 무엇 | 값 |
|---|---|
| 안내가 부르는 지표 이름 | **4** — 전부 `ops/status` SQL 에 있다 ✅ |
| `apps/` · `capreq/src` 의 외부 AI 호스트 | **0** ✅ |
| 외부 호스트 참조 전체 | **2** — 둘 다 `modality.py` 주석의 GitHub 링크 |
| LLM 백엔드 | `CAPREQ_OLLAMA_URL` 기본 `http://127.0.0.1:11434` (로컬) |

## 무엇을 안 보나

**응답을 실제로 받아 보지 않는다** — 살아 있는 Core 가 필요하다. 여기는 **이름이 SQL 에
있는가**만 본다. 값이 0 인지는 운영자가 위 `curl` 로 본다.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "apps" / "core" / "app" / "main.py"
GUIDE = ROOT / "docs" / "guide" / "operate-production.md"
REPORT = ROOT / "docs" / "ops" / "contest-report-form-draft.md"
TREES = (ROOT / "apps", ROOT / "capreq" / "src")

sys.path.insert(0, str(ROOT / "tests"))
from _srcguard import code_only  # noqa: E402

# 운영 안내 §7 이 이름으로 부르는 지표.
OPS_METRICS = ("nodes_without_credential", "drift_routable",
               "arch_unbound_routable", "api_keys_active")

# 상용 AI API 호스트·SDK. 하나라도 있으면 「독립 구동」 주장이 거짓이 된다.
EXTERNAL_AI = re.compile(
    r"api\.openai\.com|openai|anthropic|generativelanguage|googleapis|"
    r"bedrock|cognitiveservices|azure\.com|huggingface\.co|replicate\.com")


def _python_files() -> list[Path]:
    out: list[Path] = []
    for tree in TREES:
        if tree.is_dir():
            out += [p for p in tree.rglob("*.py") if "__pycache__" not in p.parts]
    return sorted(out)


class TestOpsMetricsExist(unittest.TestCase):
    """없는 필드는 「0」과 **화면에서 같아 보인다**."""

    def test_every_named_metric_is_produced(self) -> None:
        body = MAIN.read_text(encoding="utf-8")
        missing = [m for m in OPS_METRICS if f"AS {m}" not in body]
        self.assertEqual([], missing, f"안내가 부르는데 응답에 없는 지표: {missing}")

    def test_the_guide_still_names_them(self) -> None:
        """안내가 그 이름을 그만 부르면 이 검사는 **아무것도 안 지킨다**."""
        guide = GUIDE.read_text(encoding="utf-8")
        missing = [m for m in OPS_METRICS if m not in guide]
        self.assertEqual([], missing, f"운영 안내에서 사라진 지표: {missing}")

    def test_the_guide_gives_a_command(self) -> None:
        self.assertIn("/v1/ops/status", GUIDE.read_text(encoding="utf-8"),
                      "안내가 그 값을 어떻게 보는지 안 적는다")


class TestNoExternalAiApi(unittest.TestCase):
    """대회 제출 문서의 「외부 AI API 호출 **0건**」 — 세는 검사가 없었다."""

    def test_no_module_reaches_a_commercial_ai_host(self) -> None:
        files = _python_files()
        self.assertGreaterEqual(len(files), 40, f"{len(files)}개만 봤다")
        bad = []
        for path in files:
            for i, line in enumerate(code_only(path).splitlines(), 1):
                if EXTERNAL_AI.search(line):
                    bad.append(f"{path.relative_to(ROOT).as_posix()}:{i}")
        self.assertEqual([], bad, f"외부 AI API 참조: {bad}")

    def test_the_llm_backend_is_local_by_default(self) -> None:
        cfg = (ROOT / "capreq" / "src" / "capreq" / "config.py").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1:11434", cfg, "라우팅 LLM 의 기본이 로컬이 아니다")

    def test_the_claim_is_still_written(self) -> None:
        claim = "외부 AI API 호출"
        self.assertTrue(claim in REPORT.read_text(encoding="utf-8"),
                        f"제출 문서에서 그 주장이 사라졌다: «{claim}»")


class TestProbeActuallyScans(unittest.TestCase):
    def test_the_detector_discriminates(self) -> None:
        """주석의 링크를 잡거나 진짜를 놓치면 위 검사가 쓸모없다."""
        self.assertTrue(EXTERNAL_AI.search('url = "https://api.openai.com/v1/chat"'))
        self.assertTrue(EXTERNAL_AI.search("from anthropic import Anthropic"))
        self.assertFalse(EXTERNAL_AI.search('return "http://127.0.0.1:11434"'))
        self.assertFalse(EXTERNAL_AI.search("https://github.com/gncorpseo-commits/capnet"))

    def test_comments_are_stripped_before_looking(self) -> None:
        """주석에 든 이름을 위반으로 세면 **설명을 벌주는 검사**가 된다."""
        probe = ROOT / "tests" / "__ai_probe.py"
        probe.write_text('# openai 를 쓰지 않는다\nX = 1\n', encoding="utf-8")
        try:
            self.assertFalse(EXTERNAL_AI.search(code_only(probe)))
        finally:
            probe.unlink()


if __name__ == "__main__":
    unittest.main()
