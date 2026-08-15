# 단계 6 — 카테고리별 실행기, 무엇이 먼저인가 (준비 문서)

> **준비 문서다. 구현이 아니다.** 여기서 정하는 것은 「무엇을 어떤 순서로」이고,
> 각 항목의 착수는 Decision 을 따른다.
> 근거: 브리지 Decision 2-G (단계 1→6) · 단계 5 구현에서 실측된 사실.
> 작성: 2026-08-15

---

## 0. 요약 — 실행기를 더 만들기 전에 닫아야 할 것이 있다

단계 5(`text.classify`)를 만들면서 **실행기 하나를 붙이는 데 무엇이 드는지**가 드러났다.
그 경험으로 나머지를 보면, 다음 실행기를 바로 얹는 것보다 **먼저 닫아야 할 구멍**이 있다.

| # | 무엇 | 왜 먼저인가 |
|---|------|-------------|
| **G-out** | `structured` 출력 검증이 **사실상 없다** | 카탈로그 52 중 **26개**가 `structured` 다. 지금 붙이면 게이트가 통과시키는 근거가 없다 |
| **G-task** | `POST /v1/tasks` 의 `datasetId` allowlist | 이미지 밖 모든 작업이 막힌다 (**Decision 대기 중**) |
| **G-data** | 참조 구현의 **학습 데이터 라이선스** | 카테고리마다 다르다. 어떤 것은 규칙 생성이 되고 어떤 것은 안 된다 |

**G-out 과 G-task 를 닫기 전에는 실행기를 더 얹어도 「돈다」를 말할 수 없다.**

---

## 1. G-out — `structured` 출력은 지금 검증되지 않는다 (실측)

`apps/node/app/contract_check.py` 의 `check_output_schema` 는 `required` ·
`additionalProperties` · 스칼라 `type` · `enum` · 숫자 범위만 본다.
**배열·객체 내부를 보지 않는다.**

2026-08-15 실측 — 네 가지 위반이 **전부 통과**한다:

| 출력 | 계약 | 결과 |
|---|---|---|
| `{"vector":[0.1,0.2,0.3]}` | `array` · `minItems:3` · `maxItems:3` | 통과 (정상) |
| `{"vector":[0.1]}` | 같음 | **통과** ← 차원이 틀렸다 |
| `{"vector":"not-a-vector"}` | `type: array` | **통과** ← 배열이 아니다 |
| `{"boxes":[{"x":"a"}]}` | `items.required:[x,y,w,h]` | **통과** ← 구조가 없다 |

### 왜 지금까지 문제가 아니었나

라우팅되는 능력이 `image.classify`(closed_set) 하나였다. `enum` 검사는 실제로 동작하므로
**닫힌 라벨 집합에서는 계약이 지켜졌다.** 단계 5 의 `text.classify` 도 closed_set 이라
같다. 즉 **지금까지의 주장은 참이었고**, 구멍은 아직 쓰지 않은 영역에 있다.

### 무엇을 하자는 것인가

`check_output_schema` 를 배열·중첩 객체까지 보게 넓힌다. **새 의존성 0** —
`jsonschema` 를 넣지 않는다(이 리포의 규율). 계약이 실제로 쓰는 것만 손으로 본다:

- `type: array` + `items`(스칼라/객체) + `minItems`/`maxItems`
- 중첩 객체의 `required` · `properties` · `additionalProperties`
- 기존 스칼라·`enum`·범위 검사는 **그대로** (무회귀)

**DDL 0 · 계약 형식 변경 0.** 지금 계약들이 쓰는 표현을 더 정확히 볼 뿐이다.

> **이건 「제약 추가」다.** 통과하던 것이 떨어질 수 있다 — 다만 지금 `structured` 로
> 라우팅되는 능력이 **하나도 없으므로** 실제로 떨어질 대상이 없다. 지금이 가장 싼 시점이다.

---

## 2. G-task — 작업 접수 (Decision 대기)

`POST /v1/tasks` 가 `datasetId` 를 **무조건** allowlist 와 대조한다
(`ALLOWED_DATASET_IDS = {"eurosat-rgb"}`). 텍스트 작업에는 맞는 값이 없고,
`eurosat-rgb` 를 적으면 통과하지만 **증적에 거짓 데이터셋이 남는다.**

D8′ 는 allowlist 를 「보조 경로」라 했는데 코드는 **필수 관문**이다.
안 A/B/C 는 `docs/bridge/inbox-cursor.md` 에 올려 뒀다 (추천: **A** — `inputId` 가 있으면 건너뛴다).

**이 칸이 열리기 전에는 어떤 새 실행기도 「작업이 완주한다」를 보일 수 없다.**
계약 게이트까지는 보일 수 있다 (단계 5 가 그랬다).

---

## 3. G-data — 카테고리마다 학습 데이터 사정이 다르다

단계 5 에서 **과제를 고른 기준**이 여기였다. 구조 분류(`email`·`url`·…)를 고른 이유는
성능이 아니라 **규칙으로 생성할 수 있어서**다 — 외부 말뭉치가 0 이면 절대규칙 6 과
2차 라이선스 검증에 새로 얹을 것이 없다.

나머지를 같은 잣대로 나누면:

| 등급 | 뜻 | 카테고리 |
|---|---|---|
| **자체 생성 가능** | 규칙으로 데이터를 만든다. 라이선스 0 | `text.*`(구조·형식류) · `table.extract` · `timeseries.*` · `code.embed` · `retrieve.*` · `*.embed` |
| **기존 자산 재사용** | 이미 있는 EuroSAT 로 된다 | `image.embed` · `image.quality` · `video.*`(EuroSAT 프레임 합성) |
| **새 데이터 필요** | 라벨된 외부 데이터가 있어야 한다 | `image.detect`·`image.segment`·`image.ocr` · `audio.*` · `mm.*` |
| **모델 없이도 됨** | 규칙 기반이 정직한 구현 | `safety.pii`(패턴) · `text.ner`(일부) |
| **격리 선행** | v제품-2 전 라우팅 잠금 | `code.generate` · `tool.plan` · `tool.action` |

**「새 데이터 필요」는 이번 대회 트랙에서 손대지 않는 편이 좋다.** 라이선스 검증이
2차에 있고, 데이터 하나를 잘못 들이면 그 검증이 통째로 흔들린다.

---

## 4. 실행기 하나를 붙이는 데 드는 것 (단계 5 실측)

| 단계 | 산출물 | 단계 5 에서 |
|---|---|---|
| 1 | 모달리티 `preprocess` 어휘 | 카탈로그 §4 (이미 **8종 정의됨**) |
| 2 | 특징 추출 (torch-free) | `app/text_features.py` |
| 3 | 참조 arch + `ARCH_MODALITY` 등록 | `app/tiny_text.py` · `tiny_cnn.py` |
| 4 | 학습 스크립트 + 가중치 | `apps/train/train_text_scratch.py` (96KB) |
| 5 | 실행기 | `app/infer_text.py` |
| 6 | 계약 게이트 분기 | `contract_check.py` |
| 7 | 실행 경로 분기 | `node/main.py::_run` |
| 8 | 종단 데모 | `scripts/text_demo.sh` |
| 9 | 검사 + 변이 | `tests/test_text_modality.py` (16종) |

**3–7 은 이제 형판이 있다.** 다음 모달리티는 1·2·4·8·9 가 주된 일이고, 3·5·6·7 은
같은 자리에 한 줄씩 늘리면 된다. 즉 **두 번째 실행기부터 값이 싸진다.**

---

## 5. 추천 순서

| # | 무엇 | 왜 |
|---|---|---|
| **1** | **G-out — `structured` 출력 검증** | 26개를 여는 선행 조건. 지금은 떨어질 대상이 0 이라 가장 싸다. DDL 0 · 새 의존성 0 |
| **2** | **G-task** (Decision 후) | 이미지 밖 작업이 완주하려면 필수 |
| **3** | **`text.embed`** | **새 데이터가 필요 없다** — 텍스트 특징·전처리를 그대로 쓴다. `structured` 첫 사례라 G-out 을 실제로 검증한다 |
| **4** | `image.embed` | 기존 EuroSAT 자산 재사용. 이미지 형판 그대로 |
| **5** | `table.extract` · `timeseries.forecast` | 자체 생성 가능 · 새 모달리티 어휘를 두 번째로 시험 |
| — | `audio.*` · `mm.*` · `image.detect/segment/ocr` | **대회 트랙 밖.** 새 데이터 라이선스가 필요하다 |
| — | `code.generate` · `tool.*` | **v제품-2 격리 전 금지** |

**3번을 첫 실행기로 고른 이유**는 성능이 아니라 **검증 가능성**이다.
임베딩은 「차원이 맞는가·수치인가」가 계약의 전부라, G-out 이 실제로 동작하는지가
그 한 능력으로 드러난다.

---

## 6. 하지 않을 것 (명시)

- **한 PR 에 52 런타임** — Decision 2-G 가 금지했다. 실행기는 하나씩
- **`jsonschema` 의존성 추가** — 계약이 쓰는 것만 손으로 본다
- **freeform 채점** — 정답 집합이 없다 (`ck_capability_golden_scoreable` · `0018`)
- **성능 주장** — `quality_profile='none'` 인 능력에 정확도를 붙여 팔지 않는다
- **새 외부 데이터셋** — 2차 라이선스 검증 전까지

---

## 7. 관련 문서

- 카탈로그·모달리티 어휘·계약 게이트: [`../spec/capability-catalog.md`](../spec/capability-catalog.md)
- 유통 세대·격리: [`product-distribution.md`](./product-distribution.md)
- 결정 이력: [`../context-handoff.md`](../context-handoff.md)
