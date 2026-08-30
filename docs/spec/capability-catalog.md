# 능력 카탈로그 — 52 (제품 정본)

> **정본.** 능력 `code` · `output_kind` · 기본 `quality_profile` · 모달리티 · 유통 세대는 여기서만 읽는다.
> 근거: 브리지 Decision 2 (2026-08-15) — A 채택 · B 채택 · C2 · E · F · G.
> 갱신: 2026-08-30

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
| 4 | `image.embed` | image | `structured` | none | v제품-1 ✅ **구현됨** |
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
| 13 | `text.classify` | text | `closed_set_labels` | none | v제품-1 ✅ **구현됨** |
| 14 | `text.extract` | text | `structured` | none | v제품-1 ✅ **구현됨** |
| 15 | `text.ner` | text | `structured` | none | v제품-1 ✅ **구현됨** |
| 16 | `text.embed` | text | `structured` | none | v제품-1 ✅ **구현됨** |
| 17 | `text.summarize` | text | `freeform` | none | v제품-1 |
| 18 | `text.generate` | text | `freeform` | none | v제품-1 |
| 19 | `text.translate` | text | `freeform` | none | v제품-1 |
| 20 | `text.rewrite` | text | `freeform` | none | v제품-1 |
| 21 | `text.qa` | text | `freeform` | none | v제품-1 |
| 22 | `text.chat` | text | `freeform` | none | v제품-1 |
| 23 | `text.moderate` | text | `closed_set_labels` | none | v제품-1 |
| 24 | `text.rank` | text | `structured` | none | v제품-1 ✅ **구현됨** |

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
| 35 | `table.extract` | doc | `structured` | none | v제품-1 ✅ **구현됨** |
| 36 | `doc.classify` | doc | `closed_set_labels` | none | v제품-1 |
| 37 | `doc.summarize` | doc | `freeform` | none | v제품-1 |
| 38 | `doc.qa` | doc | `freeform` | none | v제품-1 |
| 39 | `timeseries.forecast` | table | `structured` | none | v제품-1 ✅ **구현됨** |
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
| `table` | `encoding` · `max_rows` · **`window`**(시계열) | `{"encoding":"utf-8","max_rows":10000,"window":24}` |
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
| `doc` | `text/plain` **만** — `application/pdf` 는 새 의존성이라 받지 않는다 (§`table.extract`) |
| `table` | `text/csv` · `application/json` |
| `code` | `text/plain` |

**코드 접두는 모달리티가 아니다.** `timeseries.forecast` 의 모달리티는 `table` 이고
`table.extract` 는 `doc` 이다. 코드 앞부분으로 모달리티를 추론하면 어긋난다 —
capreq 가 그렇게 하다가 `timeseries.forecast` 첨부를 **통째로 거절**했다 (2026-08-29).

그리고 **위 표는 상한이고, 능력이 선언한 `mediaTypes` 가 정본이다.**
`image.classify` 는 모달리티상 3종이 허용되지만 계약은 `image/jpeg` 하나다 (`0012` ·
측정 없이 주장 없음). 클라이언트가 선검사를 두려면 표가 아니라 **선언**을 따라야 한다.

---

## 5. 계약 게이트 — 지금 무엇이 검증되고 무엇이 안 되는가

**이 절은 현재 코드의 사실이다.** 바뀌면 여기를 고친다.

계약 게이트런의 필수 검사는 **arch 로 갈린다** (`required_contract_checks`).

| 집합 | 항목 | 언제 |
|---|---|---|
| **공통 5** | `input_schema` · `output_schema` · `preprocess` · `weights_fingerprint` · **`max_params`** | **항상** |
| **참조 구현 +1** | `arch` | Core 의 `REFERENCE_ARCHS` 에 있을 때 |

`REFERENCE_ARCHS` 는 **우리 러너에 빌더가 있는 arch** 다 (현재 `TinyEuroSAT`·`TinyEuroSATB`).
이것은 정책이 아니라 **코드 사실**이라 DB 행(`agent_arch`)이 아니라 상수로 둔다 —
`agent_arch` 는 「등록해도 되는가」(FK 로 막는다)이고, 이쪽은 「실행할 수 있는가」다.
둘이 어긋나면 `test_contract_checks_by_arch` 가 잡는다.

**`image.classify@1` 은 6종 전부를 요구한다 — 무회귀다.**

### 무엇을 실제로 확인하는가

| 검사 | 참조 구현일 때 | 비참조일 때 |
|---|---|---|
| `weights_fingerprint` | safetensors 헤더의 텐서 이름·shape·dtype → 구조 sha256 | **같다** |
| `preprocess` | 선언을 **적용해** 추론 | 선언이 **읽히는지**만 |
| `input_schema` | 계약 샘플로 **실추론** | `mediaTypes` **선언 정합**만 |
| `output_schema` | 실제 출력을 계약과 대조 (**배열·중첩 객체까지** · D-out) | 스키마 **선언 정합**만 |
| `max_params` | 로드 후 torch 로 셈 | **지문의 shape 합계로 셈** (D-maxp) |
| `arch` | 모델을 세워 로드 | **보고하지 않는다** |

비참조 경로가 `arch` 를 `false` 로 보내지 않는 것은 의도다 — `false` 는
「검사했는데 떨어졌다」로 읽힌다. **아예 없는 것이 「검사하지 않았다」의 정직한 표현**이다.

**`max_params` 는 다르다.** 지문의 shape 합계로 **실제로 셀 수 있으므로** 비참조에서도
판정한다(D-maxp) — 「실행해야만 알 수 있는 값」이 아니었다. 이게 빠져 있는 동안
비참조 모델에는 **파라미터 상한이 없었다.** 상한 정본은 `agent_arch.max_params`(DB 행)다.

### 지문은 왜 torch 도 safetensors 라이브러리도 안 쓰는가

safetensors 는 맨 앞 8바이트가 헤더 길이이고 그다음이 JSON 헤더다. **그 JSON 만 읽는다.**

1. `s-public` Node 에는 **torch 가 없다**(`Dockerfile` 이 조건부 설치). 요구하면 돌릴 수 있는 기기가 좁아진다
2. 10GB 가중치여도 **헤더만** 읽는다 — 텐서 본문을 메모리에 올리지 않는다
3. **역직렬화가 아니다.** JSON 파싱과 정수 읽기뿐 — 절대규칙 5 가 pickle 을 막는 이유가 여기서도 지켜진다

실측: `eurosat_scratch` 텐서 8개 · 파라미터 **94,538** (`0008` 의 「~93k」와 일치) ·
`eurosat_scratch_b` 텐서 23개 · **24,685** · `placeholder` 텐서 1개 · **1**.
셋의 지문이 전부 다르다.

### Decision 2-C — C2 를 지금, C3 를 목표로

B2 가 세운 **「계약을 말로 받지 않는다 — 러너가 실행해서 판정한다」**는
**우리 코드가 그 모달리티를 실행할 수 있을 때만** 성립한다. `text.generate` 를 실행하려면
제출자의 코드가 필요하고, 그건 절대규칙 5 와 유통 세대에 정면으로 닿는다.

> **그래서 무엇을 보장하지 않는가 (명시).**
> 지문은 **「그 파일이 그 구조다」**까지만 말한다. **「그 계약대로 동작한다」는 보장하지 않는다.**
> 실행해서 판정하는 것은 참조 구현이 있는 모달리티(현재 image/torch)뿐이며,
> 그 밖에서는 **선언과 파일 구조의 정합**까지가 게이트가 아는 전부다.
> 실행 기반 판정을 임의 모델로 넓히려면 **격리 러너(C3 · v제품-2)가 선행**한다.

이 문장을 제품 문구에서 빼지 않는다. 없는 보장을 파는 것보다 못 하는 것을 적는 편이 낫다.
러너도 같은 말을 **증적에 남긴다**(`_notes._limits`) — 통과 사실만 보고 동작 보장으로 읽지 않게.

### 종단 실측 (2026-08-15 · 격리 스택)

`text.classify@1`(`quality_profile='none'`)을 등록하고 계약 게이트를 **끝까지** 돌렸다.

| arch | 결과 |
|---|---|
| `TinyTextCNN` (**비참조**) | `weights_fingerprint` · `preprocess` · `input_schema` · `output_schema` **4종 통과** → `gate_run PASSED` → 바인딩. **이미지 밖 능력이 계약 게이트를 통과한 첫 사례다** |
| `TinyEuroSAT` (**참조**) | 위 4종 + `arch`(로드 성공) + `max_params`(94538 ≤ 2000000) + **샘플 실추론**(`label='annual_crop'`) **6종 통과** — 무회귀 |

비참조 쪽 증적에는 한계가 그대로 적힌다:
`선언 정합 (mediaTypes=['image/jpeg']) — **샘플 추론은 하지 않았다**`.

### 새 모달리티를 붙이려면 `agent_arch` 행이 먼저다

비참조 arch 로 Agent 를 등록하려다 **HTTP 400** 을 받았다:

```text
unknown arch 'TinyTextCNN' — agent_arch 에 없는 아키텍처다
```

`agent.arch` → `agent_arch` FK 가 막는다(`0008` · I1). **설계대로다** — 허용 목록이 코드가 아니라
DB 행이므로 아무 arch 나 들어오지 못한다. 다만 **`agent_arch` 에 행을 넣는 API 가 없다.**
지금은 운영자가 DB 에 직접 넣어야 한다. 52개로 넓히려면 이 등록 경로가 필요하고,
그건 **관리 API 이므로 별 Decision** 이다 (아무나 arch 를 늘리면 allowlist 가 무의미해진다).

### 실행기 — 모달리티 디스패치 (단계 5)

**`arch` 가 어느 실행기로 갈지 정한다** (`ARCH_MODALITY`). 전처리 어휘로 짐작할 수도 있지만
(`is_text_preprocess`), 그건 계약만 있고 arch 를 모를 때의 차선책이다. `arch` 는 Core 가
말한 값이고 게이트가 **그 값으로 승인**했으므로, 「승인한 것과 실행한 것이 같다」를
지키려면 그쪽으로 갈라야 한다 (I1).

| arch | 모달리티 | 실행기 |
|---|---|---|
| `TinyEuroSAT` · `TinyEuroSATB` | image | `app.infer.predict_image` |
| `TinyTextClassifier` | text | `app.infer_text.predict_text` |

**텍스트에는 `caseId` → 로컬 골든 폴백이 없다.** 입력은 Core 중개로만 온다 (D8′) —
없으면 400 이다. 이미지 데모 경로(로컬 골든셋 40장)는 그대로 남는다.

### `text.classify` 참조 구현 — 무엇을 주장하지 않는가

`text.classify` 는 `quality_profile='none'` 이다. **골든셋도 채점도 없다 — 품질을 주장하지 않는다.**
참조 모델(`text_struct_scratch.safetensors`)이 있는 이유는 「텍스트 모달리티가 계약 게이트와
실행 경로를 통과한다」를 보이기 위해서지 분류 성능을 파는 것이 아니다.

| | |
|---|---|
| 과제 | 짧은 문자열의 **구조** 6종 (`email`·`url`·`ipv4`·`uuid`·`iso_date`·`plain`) |
| 학습 데이터 | **규칙으로 생성** — 외부 말뭉치 없음 (절대규칙 6 · 2차 라이선스 검증에 얹을 것이 없다) |
| 구조 | 해시 문자 n-gram 가방 → `Linear`. **24,582 파라미터** |
| 학습 | scratch · `scripts/train_text_scratch.sh` (CPU 수 초) |

홀드아웃 정확도는 `.meta.json` 에만 남긴다. **제품 문구로 쓰지 않는다** —
SD-008 의 교훈(학습셋으로 잰 값을 성능으로 말하지 않는다)과 같은 규율이다.

해시는 `blake2b` 로 고정한다. 파이썬 `hash()` 는 **실행마다 값이 달라져서**
(`PYTHONHASHSEED`) 학습한 모델을 다음 실행에서 못 쓴다 — 조용히 정확도만 떨어지는 종류의
고장이라 `test_text_modality` 가 기준값으로 못박는다.

### 종단 실측 — 계약 게이트까지 (2026-08-15 · 격리 스택)

`scripts/text_demo.sh` 로 arch 등록 → 능력 등록 → 계약 샘플 → 계약 게이트 → 바인딩을 돌렸다.

```text
OK   weights_fingerprint — 텐서 2개 · 파라미터 24582
OK   arch — TinyTextClassifier 로 로드 성공
OK   max_params — 24582 <= 100000
OK   preprocess — 선언 적용: encoding=utf-8 normalize=NFC max_chars=8000
OK   input_schema — 선언 전처리로 샘플 추론 성공 (27 bytes · text)
OK   output_schema — label='email' 이 계약을 만족한다
gate_run PASSED
```

### 작업 접수 — `inputId` 가 있으면 allowlist 를 건너뛴다 (D8′ · **Decision A**)

전에는 `POST /v1/tasks` 가 `datasetId` 를 **무조건** allowlist 와 대조해서, 이미지 밖
모든 작업이 막혔다. 텍스트에는 맞는 `datasetId` 가 없어 통과시키려면 `eurosat-rgb` 를
적어야 했고, 그러면 **증적에 없던 데이터셋이 남는다** — 제품 주장을 스스로 깨는 관문이었다.

**allowlist 는 비통제 수집을 막으려고 있다.** `inputId` 가 있으면 바이트는 이미 Core 를
거쳐 왔고, **수집 시점에 능력에 묶였으며**(복합 FK) 해시·크기·MIME 이 계약과 대조됐다.
그 경로에서 datasetId 를 다시 묻는 것은 통제를 더하지 않는다.

지금은 요청자가 `text-demo` 처럼 **참인 이름**을 적고 그대로 증적에 남는다.

실측 (2026-08-16 · 격리 스택):

| 요청 | 결과 |
|---|---|
| `inputId` 없음 + allowlist 밖 | **400** — 종전대로 막힌다 |
| `inputId` 없음 + `eurosat-rgb` | 200 — 데모 경로 무회귀 |
| 없는 `inputId` | **404** — 건너뛰기가 무검증이 아니다 |
| `inputId` 있음 + `text-demo` | **200 → COMPLETED** |

**바이트를 받는 문(`POST /v1/inputs`)은 건드리지 않았다** — 계약·해시·크기·MIME 대조 그대로.
「자유 업로드 경로를 만들지 않는다」는 유지된다 (절대규칙 7).

### 종단 실측 — 텍스트가 **완주했다** (2026-08-16)

```text
text demo OK — 텍스트가 계약 게이트와 실행 경로를 완주했다
label= url  confidence= 0.3115…
증적: assignment=… node=…-030 agent=… status=SUCCEEDED
경계: 신뢰도메인 task=team -> node=team · 티어 capability=M <= node_max=M
```

입력은 URL 문자열이었고 라벨도 `url` 이 나왔다. **다만 그 정확도를 주장하지 않는다** —
`quality_profile='none'` 이라 골든셋도 채점도 없다.

### `text.ner` — 규칙 span · `structured` 배열+객체 (PR-B · 2026-08-27)

**일반 NER 을 주장하지 않는다.** 사람·조직명은 다루지 않고, `text.classify` 와 같은
**구조 종류**(`email`·`url`·`ipv4`·`uuid`·`iso_date`)만 **위치(span)** 와 함께 낸다.
추론은 정규식(`app/ner_patterns.py`)이고, `RuleTextNer` arch · `rule_ner.safetensors` 는
**파라미터 0** 자리표시자다(step6 §3 「모델 없이도 됨」).

종단: `scripts/ner_demo.sh` — 계약 게이트 → Task `{ inputId }` → `entities[]` 증적.

### `text.extract` — 이름표가 붙은 필드 · **새 학습 0** (Wave C · 2026-08-29)

**자연어 이해를 주장하지 않는다.** 문장에서 사실을 뽑지 못하고 값의 뜻도 모른다.
한 줄에 `이름: 값` 꼴로 **이름표가 붙어 있는 것**만 가져오고, 「그런 줄이 있었다」까지만 말한다.

세 능력이 텍스트를 읽지만 보는 것이 다르다 — 이 구별이 카탈로그가 커질 때의 관문이다.

| 능력 | 무엇을 찾나 | 키가 있나 |
|---|---|---|
| `text.ner` | 타입 있는 span (`email`·`ipv4`·…) | ❌ 위치만 |
| **`text.extract`** | **`키: 값` 필드** | ✅ 줄에 적힌 이름표 |
| `table.extract` | 격자 (행 × 열) | 열 인덱스 |

**규칙을 전부 적는다** (`app/extract_patterns.py`). 결과가 왜 그런지 설명할 수 없으면
규칙 기반이라고 말할 자격이 없다 — 구분자는 첫 `:` 또는 `=` 하나 · 앞머리 글머리표는 떼고 ·
**키에 글자가 없으면 버린다**(`12:30` 을 필드로 읽지 않는다) · 구분자 뒤가 `//` 면 버린다
(`https://` 의 `https` 를 키로 읽지 않는다) · 같은 키가 여러 번 나오면 **전부 남긴다**.

`start`·`end` 는 **값**의 위치다 — `text.ner` 과 같은 규약이라 증적을 사람이 대조할 수 있다.

**설명이 경계를 말해야 라우터가 구별한다 (2026-08-30 실측).** 카탈로그가 커지면 이웃 능력이
서로의 요청을 가져간다. 실제로 「이메일·IP·날짜 찾아줘」가 `text.extract` 로 갔다 — 두 설명이
각자 하는 일만 적고 **하지 않는 일**을 안 적어서다. 두 `description` 에 서로를 가리키는 한 줄을
넣고 `qwen2.5:3b` 로 프롬프트 5개를 다시 재서 **4/5 → 5/5** 를 확인했다. **n=5 다 — 라우팅
품질을 주장하지 않는다.** 다만 「능력을 더할 때 설명에 경계를 적는다」는 규칙으로 남긴다.

**새 학습이 없다.** `RuleTextExtract` 는 파라미터 0 이고 `rule_extract.safetensors` 는
버퍼 한 칸짜리 자리표시자다 — 그래서 **`rule_ner.safetensors` 와 바이트가 같다**
(sha `15458b00…`). `text.rank` 의 `rule_rank.safetensors` 까지 **셋 다 바이트가 같다**.
구별하는 것은 `arch` 이고, 증적에는 arch 와 sha 가 사실대로 남는다.

**자르지 않고 던진다.** 필드 수가 러너 한도(`NODE_MAX_FIELDS`)를 넘으면 잘라서 돌려주는
대신 실패한다 — 자르면 「필드를 다 읽었다」가 거짓이 되고 쓰는 쪽은 뒤가 잘린 줄 모른다.
이것은 **계약 항목이 아니라 러너 자원 한도**다. 계약이 정하는 것은 `max_chars` 다.

종단 실측 (2026-08-29 · `scripts/text_extract_demo.sh`):

```text
OK   weights_fingerprint — 텐서 1개 · 파라미터 1 · ⚠️ shape 합계(1) ≠ 로드 후 파라미터(0)
OK   arch — RuleTextExtract 로 로드 성공
OK   max_params — 0 <= 1000
OK   preprocess — 선언 적용: encoding=utf-8 normalize=NFC max_chars=8000
OK   input_schema — 선언 전처리로 샘플 추론 성공 (137 bytes · text_extract)
OK   output_schema — 칸 1개(fields)가 계약을 만족한다
gate_run PASSED → 바인딩 → COMPLETED · fields 3건 (Ticket·Severity·Assignee)
증적: node=…030 · team → team · M <= M
```

지문 경고(`shape 합계(1) ≠ 로드 후 파라미터(0)`)는 **정상이다** — 파일에 있는 것은
버퍼이고 버퍼는 `parameters()` 에 들어가지 않는다. `text.ner` 과 같은 이유다.

### `text.rank` — 어휘 겹침 순위 · **새 학습 0** (Wave G · 2026-08-30)

**뜻을 안다고 주장하지 않는다.** 첫 줄을 질의로 보고 나머지 줄들을 **질의와 같은 낱말을
얼마나 쓰는가**로 줄 세운다. 동의어·어형 변화·문맥을 보지 않는다 — 「자동차」와 「차량」은
**안 겹친다**. 의미 유사도가 필요하면 `text.embed`, 학습된 관련도가 필요하면
`retrieve.dense`·`retrieve.rerank` 다. 여기가 아니다.

텍스트를 읽는 능력이 넷이 됐고, 넷이 **내놓는 것**이 다르다.

| 능력 | 무엇을 내놓나 |
|---|---|
| `text.ner` | 타입 있는 span (`email`·`ipv4`·…) — 키가 없다 |
| `text.extract` | `키: 값` 필드 — 줄에 적힌 이름표 |
| `table.extract` | 격자 (행 × 열) |
| **`text.rank`** | **후보 줄의 순위** — 겹친 낱말이 근거다 |

**규칙을 전부 적는다** (`app/rank_rules.py`). 첫 번째 비어 있지 않은 줄이 **질의**이고
그 뒤가 **후보**다 · 토큰은 유니코드 글자·숫자의 연속이고 **소문자로 접는다** · 점수는
**자카드**(`|∩| / |∪|` · 4자리 반올림)이며 **집합이라 같은 낱말이 여러 번 나와도 한 번**이다
(길이가 점수를 밀지 않는다) · 정렬은 점수 내림차순이고 **동점이면 원래 줄 번호 순**이다.

**같은 입력이면 언제나 같은 순서가 나온다.** 순위에 우연이 있으면 증적이 뜻을 잃는다.

결과의 `overlap` 은 실제로 겹친 토큰이다 — **왜 그 점수인지 사람이 대조**할 수 있어야 하기
때문이고, `text.ner`·`text.extract` 가 `start`·`end` 를 주는 것과 같은 이유다.
질의에 토큰이 하나도 없으면 전부 0 점인데, 0 점은 **「관련 없음」이 아니라 「낱말이 안 겹쳤다」**다.

**설명에 「하지 않는 일」을 적는다.** `text.extract` 에서 배운 규칙(바로 위 절)을 그대로
적용해, 등록 `description` 이 `text.embed`·`retrieve.*`·`text.ner`·`text.extract` 를 이름으로
가리킨다. 이웃이 넷이면 경계를 안 적을 때 라우터가 섞을 자리도 넷이다.

**그 경계가 실제로 무는지 재 봤다 (2026-08-30 · `qwen2.5:3b` · n=5).** 같은 프롬프트 5개를
`text.rank` **있는 카탈로그**와 **뺀 카탈로그**에 각각 물어 **차이만** 본다.

| 프롬프트 | rank 있음 | rank 없음 |
|---|---|---|
| 「겹치는 단어 기준으로 줄 세워줘」 | **`text.rank`** conf 1.00 | `None` |
| 「제일 비슷한 줄부터 순서대로」 | `None` | `None` |
| 「로그에서 이메일·IP 찾아줘」 | `text.ner` | `text.ner` |
| 「제목·담당자 같은 항목 뽑아줘」 | `text.ner` ❌ | `text.ner` ❌ |
| 「이 사진이 뭔지 분류해줘」 | `image.classify` | `image.classify` |

읽을 것은 둘이다. ① **`text.rank` 는 자기 것만 가져갔고 이웃의 요청을 뺏지 않았다** —
넣기 전과 후가 나머지 네 줄에서 같다. ② 「비슷한 줄」은 **`text.rank` 가 있어도 안 가져간다.**
「비슷하다」는 의미 유사도이고 등록 설명이 그것을 명시적으로 배제한다 — 라우터가 억지로
집는 대신 비운 것이다.

`text.extract` 요청이 `text.ner` 로 가는 미스는 **`text.rank` 를 빼도 똑같다.** 이 PR 이 만든
것이 아니라 두 이웃 사이에 남아 있던 것이고, 여기서 고치지 않는다.

**n=5 다 — 라우팅 품질을 주장하지 않는다.** confidence 값은 같은 프롬프트에서도 실행마다
흔들린다(0.85 ↔ 0.80). 이 표가 말하는 것은 정확도가 아니라 **넣기 전후의 차이**다.

**자르지 않고 던진다.** 후보 수가 러너 한도(`NODE_MAX_CANDIDATES`)를 넘으면 실패한다 —
자르면 「전부 줄 세웠다」가 거짓이 된다. `text.extract` 의 `NODE_MAX_FIELDS` 와 같은 규율이고,
**계약이 정하는 것은 `max_chars`** 다.

종단 실측 (2026-08-30 · `scripts/text_rank_demo.sh`):

```text
OK   weights_fingerprint — 텐서 1개 · 파라미터 1 · ⚠️ shape 합계(1) ≠ 로드 후 파라미터(0)
OK   arch — RuleTextRank 로 로드 성공
OK   max_params — 0 <= 1000
OK   preprocess — 선언 적용: encoding=utf-8 normalize=NFC max_chars=8000
OK   input_schema — 선언 전처리로 샘플 추론 성공 (119 bytes · text_rank)
OK   output_schema — 칸 2개(query, ranking)가 계약을 만족한다
gate_run PASSED → 바인딩 → COMPLETED
증적: node=…030 · assignment SUCCEEDED · team → team · M <= M
```

지문 경고(`shape 합계(1) ≠ 로드 후 파라미터(0)`)는 **정상이다** — 파일에 있는 것은 버퍼이고
버퍼는 `parameters()` 에 들어가지 않는다. `text.ner`·`text.extract` 와 같은 이유다.

**그 실측이 한계도 같이 보였다.** 질의 `느린 쿼리 인덱스` 에 대해:

```text
1. score=0.7500 overlap=느린,인덱스,쿼리 | 인덱스 없이 느린 쿼리
2. score=0.1667 overlap=느린             | 느린 쿼리를 인덱스로 고쳤다
3. score=0.0000 overlap=-                | 무관한 줄 하나
```

2위 줄은 사람이 보면 1위만큼 관련 있는데 **0.1667** 이다 — 「쿼리를」·「인덱스로」에 조사가
붙어 「쿼리」·「인덱스」와 **다른 토큰**이 되기 때문이다. 이것은 버그가 아니라 **선언한
한계가 실제로 그렇게 나온 것**이다. 한국어 조사·어미를 다루려면 형태소 분석이 필요하고,
그것은 규칙 실행기가 아니라 다른 능력이 할 일이다. **그래서 품질을 주장하지 않는다.**

### `text.embed` — `structured` 의 첫 사례 (단계 6 ①)

`text.classify` 와 **같은 특징 추출·전처리**를 쓴다(두 벌을 만들지 않는다 · D3).
다른 것은 **출력**이다 — 라벨이 아니라 64차원 벡터.

**의미적 유사도를 주장하지 않는다.** 이 사영은 라벨로 학습한 것이 아니라 **고정 시드
초기화**다. 같은 입력이 같은 벡터를, 다른 입력이 다른 벡터를 낸다 — 그 이상은 말하지 않는다.
「임베딩이니까 검색이 잘 된다」로 읽히면 안 되므로 meta·소스·여기에 같은 문장을 적어 둔다.

**라벨 칸을 지어내지 않는다.** 결과 증적에 `label` 키가 **아예 없다** — 빈 문자열로 채우면
「라벨이 있었다」고 거짓말한다. 대신 `label`·`vector` 가 **둘 다 비면 Core 가 거절**한다
(아무것도 안 낸 실행이 COMPLETED 로 기록되면 안 된다 · dummy 는 예외).

종단 실측 (2026-08-16 · 격리 스택 · `scripts/embed_demo.sh`):

```text
OK   weights_fingerprint — 텐서 1개 · 파라미터 262144
OK   max_params — 262144 <= 500000
OK   preprocess — 선언 적용: encoding=utf-8 normalize=NFC max_chars=8000
OK   input_schema — 선언 전처리로 샘플 추론 성공 (27 bytes · text_embed)
OK   output_schema — **벡터 64차원이 계약을 만족한다**
gate_run PASSED → 바인딩 → 작업 COMPLETED (증적에 64차원 벡터, label 키 없음)
```

**`output_schema` 줄이 D-out 이 실제로 무는 첫 증거다.** 전에는 차원이 틀려도 통과했다.

> **곁다리로 확인된 것:** 이 사영은 262,144 파라미터라, 상한을 100,000 으로 등록했을 때
> 계약 게이트가 `max_params` 에서 떨어졌다. **D-maxp 가 실제로 무는 것도 같이 보였다** —
> 그리고 D-arch 에 갱신 경로가 없으므로 빈 볼륨에서 다시 등록해야 했다(설계대로).

### `timeseries.forecast` — 세 번째 모달리티 어휘 (단계 6 ②)

텍스트·이미지가 아닌 입력이 **같은 계약 형판**으로 도는지를 이 능력이 보인다.
입력은 CSV 한 열 또는 JSON 숫자 배열, 출력은 **수치 배열 4개**.

`window` 를 계약에 둔 이유: 모델이 보는 과거 길이가 바뀌면 **같은 가중치가 다른 것을 본다.**
러너가 그대로 셀 수 있는 값이라 계약이 검증할 수 있다(토크나이저를 안 넣은 것과 같은 기준).

**표본이 모자라면 던진다.** 0 으로 채우면 모델이 **없는 과거**를 본 것이 되고,
터지지 않고 조용히 틀린 예측이 나온다.

**학습 데이터는 규칙 생성**(추세+계절성+잡음). 외부 데이터가 0 이라 라이선스 검증에
얹을 것이 없다. **실제 시계열 성능을 주장하지 않는다** — `quality_profile='none'` 이다.

### 출력 이름은 **계약이 정한다**

Node 가 보낸 필드명을 그대로 쓰면, 게이트가 검증한 출력(`forecast`)과 증적에 남는
출력(`vector`)이 갈라진다 — **실제로 그랬다.** 지금은 Core 가 `capability.output_schema`
의 `required` 첫 항목을 읽어 붙인다. Node 는 **값만 보내고 이름은 주장하지 못한다.**

종단 실측 (2026-08-16 · 격리 스택 · `scripts/series_demo.sh`):

```text
OK   weights_fingerprint — 텐서 2개 · 파라미터 100
OK   max_params — 100 <= 500000
OK   preprocess — 선언 적용: encoding=utf-8 max_rows=10000 window=24
OK   input_schema — 선언 전처리로 샘플 추론 성공 (280 bytes · series)
OK   output_schema — 배열 4개가 계약을 만족한다
gate_run PASSED → 바인딩 → 작업 COMPLETED · forecast=[3.624, 5.161, 5.987, 5.739]
```

### `image.embed` — 이미지가 `structured` 를 낸다 · **새 가중치 0** (단계 6 ③)

그동안 **이미지 모달리티는 `closed_set_labels` 만** 냈다. 「이미지 × structured」는
검증된 적이 없는 조합이었고, 미검증 조합에서 형판이 깨지는 것을 이미 두 번 봤다.

**기존 `eurosat_scratch.safetensors` 를 그대로 쓴다.** 임베딩은 그 파일의 **앞부분**
(합성곱 트렁크)이므로 새로 학습할 것도 커밋할 것도 없다 — G-data 의 「기존 자산 재사용」이
실제로 무엇인지 보이는 사례다. **패키지가 커지지 않는다.**

**`strict=False` 를 쓰지 않는다.** 분류기 머리를 버려야 하니 손쉬운 길이지만,
그러면 **트렁크 키가 하나 빠져 있어도 조용히 통과한다** — 랜덤 초기화된 층으로 추론하면서
벡터는 그럴듯하게 나온다. 키를 명시적으로 걸러 내고 **기대한 키가 전부 있는지 확인한 뒤**
strict 로 넣는다.

**계약 게이트가 실행기와 같은 로더를 쓴다.** 처음엔 게이트가 `load_state_dict` 를 그대로
불러 머리 텐서에서 떨어졌다 — **통과할 수 있는 Agent 를 게이트가 떨어뜨린 것**이다.
검증과 실행이 갈리면 어느 쪽이든 틀린다.

**전처리는 분류와 같은 함수**(`load_image_tensor`)를 쓴다. 픽셀 상한도 그 안에 있다 —
임베딩만 상한이 없으면 그쪽으로 큰 이미지가 들어온다.

**유사도를 주장하지 않는다.** 이 트렁크는 10개 라벨 분류로 학습됐고, 그 표현이 다른
목적에 좋다는 근거는 없다. `quality_profile='none'` 이다.

종단 실측 (2026-08-16 · 격리 스택 · `scripts/image_embed_demo.sh`):

```text
OK   arch — TinyEuroSATEmbed 로 로드 성공
OK   max_params — 93248 <= 500000
OK   preprocess — 선언 적용: resize=[32, 32] colorspace=RGB
OK   input_schema — 선언 전처리로 샘플 추론 성공 (2977 bytes · image_embed)
OK   output_schema — 배열 128개가 계약을 만족한다
gate_run PASSED → 바인딩 → COMPLETED · vector 128차원
```

지문 경고(`shape 합계(94538) ≠ 로드 후 파라미터(93248)`)는 **정상이다** —
파일에는 분류기 머리가 들어 있고 트렁크만 로드했기 때문이다. 그 차이가 증적에 남는다.

### `table.extract` — 여러 칸을 내는 출력 · **새 가중치 0** (단계 6 ④)

지금까지 출력은 **한 칸**이었다(`label` 하나 · `vector` 하나 · `forecast` 하나).
이 능력은 `columns`·`rows`·`header_detected` **셋**을 낸다 — 그래서 「출력 이름은 계약이
정한다」를 **집합으로** 지켜야 했다.

**Core 가 계약의 `required` 와 보고된 칸 집합을 대조한다.** 다르면 **422** 이고 받아 적지
않는다. Node 는 값만 내고 모양은 계약이 정한다 — 등급을 주장 못 하는 것과 같은 규율이다.

**새 가중치가 없다.** 열 타입 추론(`email`·`url`·`ipv4`·`uuid`·`iso_date`·`plain`)은
`text.classify` 가 이미 하는 일이라 **`text_struct_scratch.safetensors` 를 그대로 쓴다.**
같은 아키텍처를 다른 능력에 붙였을 뿐이고, 증적에는 `arch` 와 `weights_sha256` 이 사실대로 남는다.

**PDF 를 받지 않는다.** 이 리포는 새 의존성을 늘리지 않는데 PDF 파싱에는 라이브러리가 필요하다.
계약의 `mediaTypes` 는 **`text/plain` 만**이고, CSV 와 마크다운 파이프 표를 읽는다.
**못 하는 것을 할 수 있다고 하지 않는다.**

**자르지 않고 던진다.** 행·열 상한을 넘으면 잘라서 돌려주는 대신 실패한다 —
자르면 「표를 다 읽었다」가 거짓이 되고, 사용자는 뒤가 잘린 줄 모른 채 결과를 쓴다.

**주장하지 않는 것:** 표 이해도. 머리글 판별은 「숫자가 하나도 없으면 머리글」이라는
느슨한 규칙이라 결과에 `header_detected` 로 **그대로 노출**하고, 열 타입은 다수결이라
얼마나 우세했는지를 `support` 로 같이 낸다 — 3/3 과 2/3 을 같게 보이지 않게.

종단 실측 (2026-08-16 · 격리 스택 · `scripts/table_demo.sh`):

```text
OK   preprocess — 선언 적용: encoding=utf-8 max_rows=1000 max_cols=64
OK   input_schema — 선언 전처리로 샘플 추론 성공 (table_extract)
OK   output_schema — 칸 3개(columns, header_detected, rows)가 계약을 만족한다
gate_run PASSED → COMPLETED
columns= [(0, 'ipv4', 1.0), (1, 'uuid', 1.0)] · rows= 2행 · header_detected= True
```

증적에 `label`·`vector` 는 **없다** — 계약이 요구한 칸 셋만 남는다.

### 허용 아키텍처 등록 (D-arch)

`agent.arch` 는 `agent_arch` 를 FK 로 참조한다(`0008` · I1) — **허용 목록이 DB 행**이다.
그 행을 넣는 경로가 없어서 운영자가 DB 에 직접 INSERT 해야 했다. 이제 관리 API 가 있다.

| | |
|---|---|
| `GET /v1/arches` | 목록 (**developer 이상** — 어떤 구조를 받는가는 운영 정보다) |
| `POST /v1/arches` | **추가만** (**admin**) · 중복 409 · 이름 형식 위반 400 |

**갱신·삭제 경로를 만들지 않았다.** `max_params` 는 계약 게이트의 상한이라 사후에 바꾸면
**이미 통과한 증서의 근거가 바뀐다**(D15). 상한을 바꿔야 하면 **새 arch 이름**으로 등록한다.
중복을 `ON CONFLICT DO NOTHING` 으로 넘기지도 않는다 — 다른 상한으로 다시 등록한 운영자가
**성공했다고 믿고 옛 값을 쓰게 된다.**

### 아직 하지 않은 것

**`max_params` 자체의 상한이 없다.** 관리자가 `max_params=10^18` 로 등록하면 사실상 무제한이다.
`agent_arch` 등록이 admin 전용이라 아무나 못 하지만, **숫자 상한은 정책이므로 Decision 이 필요하다** —
여기서 임의로 정하지 않았다.

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
