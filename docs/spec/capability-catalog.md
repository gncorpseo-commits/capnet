# 능력 카탈로그 — 52 (제품 정본)

> **정본.** 능력 `code` · `output_kind` · 기본 `quality_profile` · 모달리티 · 유통 세대는 여기서만 읽는다.
> 근거: 브리지 Decision 2 (2026-08-15) — A 채택 · B 채택 · C2 · E · F · G.
> 갱신: 2026-08-15

---

## 0. 이 문서가 정하는 것 / 정하지 않는 것

**정한다** — 어떤 `code` 가 존재하고, 출력이 어떤 종류이며, 골든셋을 붙일 수 있는지,
어떤 모달리티 어휘로 전처리를 선언하는지, 어느 유통 세대에서 라우팅되는지.

**정하지 않는다** — 각 능력의 구체적 `input_schema`/`output_schema` JSON. 그건 능력을
실제로 등록할 때 계약서(`docs/spec/golden/…` 또는 등록 요청 본문)가 갖는다.
이 문서는 **표면**이지 계약 자체가 아니다.

**이 문서만으로는 아무것도 라우팅되지 않는다.** 능력이 실제로 쓰이려면
`POST /v1/capabilities` 등록 → Agent 등록(`arch` 필수) → **team gate-runner** 의 계약
게이트런 → `agent_capability_passed` → `claim` 배정을 거쳐야 한다. 절대규칙 8은 그대로다.

---

## 1. 왜 52 인가 — 그리고 왜 카탈로그가 병목이 아닌가

이미지 분류 하나만 도는 것은 제품이 아니다. 사람이 여러 종류의 에이전트를 올리는 것이
전제이므로 능력 표면을 먼저 정의한다.

**다만 이 문서를 쓰는 것으로 52개가 동작하지 않는다.** 코드를 읽고 확인한 사실:

| | 상태 |
|---|---|
| **등록** (`capability` INSERT) | **지금도 된다.** D20(`0010`)이 `output_kind` 3종과 `quality_profile='none'` + 센티널을 깔아 뒀다 — DDL 불필요 |
| **라우팅** | **막힌다.** 계약 게이트가 이미지·torch 전용이다 (§5) |

그래서 확장의 실제 작업은 카탈로그가 아니라 **계약 게이트의 모달리티 일반화**다.

---

## 2. 축 — 모달리티 × 출력 종류

두 축은 **독립**이다. 섞어 쓰지 않는다.

- **모달리티** = 어떤 바이트가 흐르는가 → `preprocess` 어휘와 MIME allowlist 를 정한다
- **`output_kind`** = 무엇이 돌아오는가 → 골든셋을 붙일 수 있는지를 정한다

| `output_kind` | 뜻 | 골든 프로파일 |
|---|---|---|
| `closed_set_labels` | 선언된 라벨 집합에서 하나 | **가능** (선택) |
| `structured` | 스키마가 있는 구조 (박스·벡터·구간·순위) | 가능하나 **채점기 없음** — 현재 전부 `none` |
| `freeform` | 자유 텍스트 | **금지** — `ck_capability_golden_scoreable` (`0018`) |

**`freeform` 에 골든을 붙일 수 없는 이유**는 「측정이 약해서」가 아니라 **「정답 집합을
정의할 수 없어서」**다. 요약문은 맞다/틀리다로 갈리지 않으므로 골든셋 정의서 §6 의 채점
규칙(결정적 · 부분점수 없음 · 퍼지 매칭 금지)이 애초에 성립하지 않는다.
잴 수 없는 것에 점수를 붙이고 그 점수로 보장을 파는 경로를 DB 가 막는다.

`structured` 를 막지 않는 것은 **원리적으로는 잴 수 있기** 때문이다(코사인 유사도 · IoU ·
nDCG). 채점기가 아직 없다는 것과 못 잰다는 것은 다르다.

---

## 3. 카탈로그 52

`P` = 기본 `quality_profile` · `세대` = 라우팅이 열리는 유통 세대 (§6).

### Vision (12)

| # | `code` | 모달리티 | `output_kind` | P | 세대 |
|---|--------|---------|---------------|---|------|
| 1 | `image.classify` | image | `closed_set_labels` | **golden** | v제품-1 ✅ **구현됨** |
| 2 | `image.detect` | image | `structured` | none | v제품-1 |
| 3 | `image.segment` | image | `structured` | none | v제품-1 |
| 4 | `image.embed` | image | `structured` | none | v제품-1 |
| 5 | `image.caption` | image | `freeform` | none | v제품-1 |
| 6 | `image.ocr` | image | `structured` | none | v제품-1 |
| 7 | `image.quality` | image | `structured` | none | v제품-1 |
| 8 | `video.classify` | video | `closed_set_labels` | none | v제품-1 |
| 9 | `video.detect` | video | `structured` | none | v제품-1 |
| 10 | `video.embed` | video | `structured` | none | v제품-1 |
| 11 | `video.summarize` | video | `freeform` | none | v제품-1 |
| 12 | `video.transcribe` | video | `structured` | none | v제품-1 |

### Language (12)

| # | `code` | 모달리티 | `output_kind` | P | 세대 |
|---|--------|---------|---------------|---|------|
| 13 | `text.classify` | text | `closed_set_labels` | none | v제품-1 |
| 14 | `text.extract` | text | `structured` | none | v제품-1 |
| 15 | `text.ner` | text | `structured` | none | v제품-1 |
| 16 | `text.embed` | text | `structured` | none | v제품-1 |
| 17 | `text.summarize` | text | `freeform` | none | v제품-1 |
| 18 | `text.generate` | text | `freeform` | none | v제품-1 |
| 19 | `text.translate` | text | `freeform` | none | v제품-1 |
| 20 | `text.rewrite` | text | `freeform` | none | v제품-1 |
| 21 | `text.qa` | text | `freeform` | none | v제품-1 |
| 22 | `text.chat` | text | `freeform` | none | v제품-1 |
| 23 | `text.moderate` | text | `closed_set_labels` | none | v제품-1 |
| 24 | `text.rank` | text | `structured` | none | v제품-1 |

### Audio (6)

| # | `code` | 모달리티 | `output_kind` | P | 세대 |
|---|--------|---------|---------------|---|------|
| 25 | `audio.transcribe` | audio | `structured` | none | v제품-1 |
| 26 | `audio.classify` | audio | `closed_set_labels` | none | v제품-1 |
| 27 | `audio.embed` | audio | `structured` | none | v제품-1 |
| 28 | `audio.diarize` | audio | `structured` | none | v제품-1 |
| 29 | `speech.synthesize` | text | `structured` | none | v제품-1 |
| 30 | `speech.translate` | audio | `freeform` | none | v제품-1 |

`speech.synthesize` 의 **입력**은 텍스트다(출력이 오디오). 모달리티 축은 **입력** 기준이므로
`text` 로 둔다 — `preprocess` 는 입력에 적용되기 때문이다. 출력 오디오는 `structured`
(참조 + 해시 + 포맷)로 돌려주며, 바이트는 입력과 같은 보존 정책을 따른다.

### Multimodal (4)

| # | `code` | 모달리티 | `output_kind` | P | 세대 |
|---|--------|---------|---------------|---|------|
| 31 | `mm.classify` | multimodal | `closed_set_labels` | none | v제품-1 |
| 32 | `mm.qa` | multimodal | `freeform` | none | v제품-1 |
| 33 | `mm.embed` | multimodal | `structured` | none | v제품-1 |
| 34 | `mm.generate` | multimodal | `freeform` | none | v제품-1 |

### Structured / Docs (6)

| # | `code` | 모달리티 | `output_kind` | P | 세대 |
|---|--------|---------|---------------|---|------|
| 35 | `table.extract` | doc | `structured` | none | v제품-1 |
| 36 | `doc.classify` | doc | `closed_set_labels` | none | v제품-1 |
| 37 | `doc.summarize` | doc | `freeform` | none | v제품-1 |
| 38 | `doc.qa` | doc | `freeform` | none | v제품-1 |
| 39 | `timeseries.forecast` | table | `structured` | none | v제품-1 |
| 40 | `timeseries.anomaly` | table | `structured` | none | v제품-1 |

### Code / Tools (7)

| # | `code` | 모달리티 | `output_kind` | P | 세대 |
|---|--------|---------|---------------|---|------|
| 41 | `code.complete` | code | `freeform` | none | v제품-1 |
| 42 | `code.generate` | code | `freeform` | none | **v제품-2** ⛔ |
| 43 | `code.review` | code | `freeform` | none | v제품-1 |
| 44 | `code.embed` | code | `structured` | none | v제품-1 |
| 45 | `tool.plan` | text | `structured` | none | **v제품-2** ⛔ |
| 46 | `tool.action` | text | `structured` | none | **v제품-2** ⛔ |
| 47 | `agent.route` | text | `closed_set_labels` | none | v제품-1 |

`agent.route` 가 `closed_set_labels` 인 것은 우연이 아니다 — **후보 집합이 선언돼 있으면
채점 가능하다.** 라우팅 능력은 원리적으로 골든을 붙일 수 있는 몇 안 되는 항목이다.

### Safety (3)

| # | `code` | 모달리티 | `output_kind` | P | 세대 |
|---|--------|---------|---------------|---|------|
| 48 | `safety.classify` | text | `closed_set_labels` | none | v제품-1 |
| 49 | `safety.pii` | text | `structured` | none | v제품-1 |
| 50 | `safety.malware_hint` | code | `closed_set_labels` | none | v제품-1 |

**`safety.malware_hint` 의 `_hint` 는 이름 그대로다.** 「탐지」가 아니라 「참고」이며,
**바이러스 검사(AV)가 아니다** (§7). 이 능력이 있다는 것을 AV 가 있다는 뜻으로 쓰지 않는다.

### Retrieval (2)

| # | `code` | 모달리티 | `output_kind` | P | 세대 |
|---|--------|---------|---------------|---|------|
| 51 | `retrieve.dense` | text | `structured` | none | v제품-1 |
| 52 | `retrieve.rerank` | text | `structured` | none | v제품-1 |

### 합계

| `output_kind` | 개수 |
|---|---|
| `closed_set_labels` | **10** |
| `structured` | **26** |
| `freeform` | **16** |
| **계** | **52** |

`mvp_eligible` 은 `closed_set_labels` 10개에만 붙일 수 있다
(`ck_capability_mvp_scoreable`). 현재 실제로 붙은 것은 `image.classify` 하나다.

---

## 4. 모달리티별 `preprocess` 어휘 (Decision 2-B)

`preprocess` 는 **러너가 적용할 수 있는 선언**이어야 한다 — B2/`0014` 가 세운 규율이다.
선언만 하고 적용하지 않으면 「검증한 그것」과 「실행한 그것」이 달라진다.

| 모달리티 | 키 | 예 |
|---|---|---|
| `image` | `resize:[w,h]` · `colorspace` | `{"resize":[32,32],"colorspace":"RGB"}` |
| `video` | `fps` · `max_frames` · `resize:[w,h]` · `colorspace` | 프레임 추출 후 **image 규칙 재사용** |
| `audio` | `sample_rate_hz` · `channels` · `max_seconds` | `{"sample_rate_hz":16000,"channels":1,"max_seconds":30}` |
| `text` | `encoding` · `normalize` · `max_chars` | `{"encoding":"utf-8","normalize":"NFC","max_chars":8000}` |
| `doc` | `encoding` · `max_pages` | |
| `table` | `encoding` · `max_rows` · `max_cols` | |
| `code` | `encoding` · `max_bytes` · `language` | |
| `multimodal` | 위 어휘를 **파트별로** 선언 | `{"parts":{"image":{…},"text":{…}}}` |

**`image` 어휘는 바뀌지 않는다.** `image.classify@1` 의 `{"resize":[32,32],"colorspace":"RGB"}`
는 그대로다 — 골든 경로의 픽셀 처리가 바뀌면 `acc=0.8500` 이 움직인다.

### 토크나이저를 계약에 넣지 않는다

텍스트에서 `max_tokens` 를 쓰고 싶어지지만 **넣지 않는다.** 토큰화는 모델마다 다르고,
계약이 검증할 수 없는 값을 계약에 적으면 「선언은 있는데 아무도 확인하지 않는 칸」이 된다 —
`preprocess` 가 `0013` 에서 잠깐 그 상태였고 그래서 필수 검사에서 빠졌었다.
길이 제한은 **`max_chars`(바이트가 아니라 문자)** 로 선언한다. 러너가 그대로 셀 수 있다.

### MIME allowlist

`input_schema.mediaTypes` 는 이미 강제된다 — **미선언이면 업로드 400**(B1 핫픽스).
모달리티별 허용 목록:

| 모달리티 | MIME |
|---|---|
| `image` | `image/jpeg` · `image/png` · `image/webp` |
| `video` | `video/mp4` · `video/webm` |
| `audio` | `audio/wav` · `audio/flac` · `audio/mpeg` |
| `text` | `text/plain` · `application/json` |
| `doc` | `application/pdf` · `text/plain` |
| `table` | `text/csv` · `application/json` |
| `code` | `text/plain` |

---

## 5. 계약 게이트 — 지금 무엇이 검증되고 무엇이 안 되는가

**이 절은 현재 코드의 사실이다.** 바뀌면 여기를 고친다.

`CONTRACT_CHECKS` (`apps/core/app/gate.py`) 5종을 **전부 present + 전부 true** 여야 통과한다.
하나라도 빠지면 거절 → `agent_capability_passed` 미발급 → `assignment` FK 위반 → 라우팅 불가.

| 검사 | 구현 | 이미지 밖에서 |
|---|---|---|
| `arch` | `ARCH_REGISTRY` = `TinyEuroSAT` · `TinyEuroSATB` **둘뿐** | allowlist 밖 → `False` |
| `max_params` | torch `p.numel()` | `arch` 실패 시 자동 `False` |
| `preprocess` | `{resize, colorspace}` 해석 | 다른 어휘는 못 읽는다 |
| `input_schema` | 샘플로 `predict_image` **실추론** | 이미지가 아니면 못 돈다 |
| `output_schema` | 라벨 검증 | `freeform` 에 뜻이 약하다 |

### Decision 2-C — C2 를 지금, C3 를 목표로

B2 가 세운 **「계약을 말로 받지 않는다 — 러너가 실행해서 판정한다」**는
**우리 코드가 그 모달리티를 실행할 수 있을 때만** 성립한다. `text.generate` 를 실행하려면
제출자의 코드가 필요하고, 그건 절대규칙 5 와 유통 세대에 정면으로 닿는다.

**채택 = C2 — 가중치 지문 검증.** safetensors 를 로드해 **텐서 키 · shape · dtype 집합**을
계약 선언과 대조한다. safetensors 로드는 역직렬화가 아니라 텐서 읽기이므로
**임의 코드 실행이 아니다** — 절대규칙 5 안에 있다.

> **그래서 무엇을 보장하지 않는가 (명시).**
> C2 는 **「그 파일이 그 구조다」**까지만 말한다. **「그 계약대로 동작한다」는 보장하지 않는다.**
> 실행해서 판정하는 것은 참조 구현이 있는 모달리티(현재 image/torch)뿐이며,
> 그 밖에서는 **선언과 파일의 정합**까지가 게이트가 아는 전부다.
> 실행 기반 판정을 임의 모델로 넓히려면 **격리 러너(C3 · v제품-2)가 선행**한다.

이 문장을 제품 문구에서 빼지 않는다. 없는 보장을 파는 것보다 못 하는 것을 적는 편이 낫다.

---

## 6. 유통 세대와 잠금 (Decision 2-E)

`docs/design/product-distribution.md` 의 세대를 그대로 쓴다.

| 세대 | 무엇이 열리나 |
|---|---|
| **v제품-1** | 팀·초대 조직의 Node. 가중치는 safetensors, 실행 코드는 **우리 것** |
| **v제품-2** | 남의 Agent 코드 — **컨테이너 격리 · 자원/시간/네트워크 제한** |

### v제품-2 전까지 라우팅을 잠그는 셋

`code.generate` · `tool.plan` · `tool.action`.

이 셋은 **산출물이 실행되는 순간** 위험이 실현된다. 모델이 위험한 게 아니라 출력의 용도가
그렇다 — 계획을 세우고 행동을 하고 코드를 만든다. 격리 없이 열면
**「승인 도메인 안에서만 돈다」는 주장이 무의미**해진다. 실행이 Node 밖으로 나가기 때문이다.

**집행 방법 (DDL 0):** 이 셋은 `trust_domain_min='team'` 으로만 등록한다.
`domain_compatible` 이 tenant·public Node 로의 배정을 이미 막으므로, 팀 자체 기기 밖으로
나가지 않는다. **새 제약이 필요 없다** — 있는 축을 쓴다.

`code.complete` · `code.review` 는 잠그지 않는다. 산출물이 **사람에게 보여지는 텍스트**이며
자동 실행 경로가 없기 때문이다. 이 구분이 흐려지면(예: 리뷰 결과를 자동 적용) 그때 다시 잠근다.

---

## 7. 보안 — 있는 것과 **없는 것** (Decision 2-E)

> **바이러스 검사(AV)는 없다.** 「공통 필수 AV 스캔」이 있다고 주장하지 않는다.

**있는 것:**

| 통제 | 근거 |
|---|---|
| safetensors 형식 봉쇄 (`.pt`/`.pth`/pickle 거부) | 절대규칙 5 · `assert_safetensors` |
| `weights_sha256` 선언·바인딩 + Node 로컬 재해싱 | 안전 사슬 6·7 |
| placeholder 가중치 감지 · 라우팅 차단 | SD-015 · `0005` |
| 입력 MIME · 크기 · 해시 대조 (Core 중개) | B1 · D8′ |
| 모달리티별 MIME allowlist | §4 |

**없는 것 (선택 · 미구현):**

- **AV/멀웨어 스캔.** 넣는다면 **업로드 시점 Core 중개 경로**에 붙는 것이 맞다 —
  Node 가 아니다. Node 에 두면 기기마다 다른 것을 신뢰하게 되고, 그건 Node 가
  자기 안전성을 주장하는 것과 같아진다(절대규칙 4의 정신). **별 Decision 이 필요하다.**
- **가중치 내용 검사.** 지문(C2)은 구조를 보지 내용을 보지 않는다.

`safety.malware_hint` 능력이 카탈로그에 있는 것은 **AV 가 있다는 뜻이 아니다.**
그건 사용자가 호출하는 능력이지 플랫폼의 통제가 아니다.

---

## 8. 관련 문서

- 계약·게이트 결정: [`../context-handoff.md`](../context-handoff.md) D18 · D20 · D17
- 유통 세대: [`../design/product-distribution.md`](../design/product-distribution.md)
- 안전 사슬: [`../design/safety-chain.md`](../design/safety-chain.md)
- 골든셋 정의서 (채점 규칙 §6): [`golden/image-classify-v1.md`](./golden/image-classify-v1.md)
