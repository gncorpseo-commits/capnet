"""실행 한도 — **torch 없이** 읽힌다.

`MAX_PARAMS_DEFAULT` 가 `infer.py` 에 있었는데 그 파일은 최상단에서 `import torch` 를 한다.
계약 게이트의 **비참조 경로**(C2 · D-maxp)는 torch 없는 Node 에서도 파라미터 상한을
판정해야 하므로, 상수만 여기로 꺼냈다. `infer.py` 는 다시 내보낸다.

정본 상한은 **`agent_arch.max_params` (DB 행)** 이다. 여기 값은 Core 가 아무 말도 하지
않았을 때의 기본값일 뿐이다 — 둘을 헷갈리면 「상한을 DB 가 정한다」가 무너진다.
"""

from __future__ import annotations

import os

MAX_PARAMS_DEFAULT = int(os.environ.get("NODE_MAX_PARAMS", 20_000_000))
