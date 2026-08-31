# Changelog

## 데모 다섯 종도 설명을 DB 에 맞춘다 (Wave K) — 2026-08-31

Wave I(#122)가 셋만 고쳤다. **나머지 다섯**을 같은 패턴으로 마친다.
**코드·DDL·의존성 0** — 스크립트 다섯과 검사뿐이다.

| 데모 | 능력 |
|---|---|
| `embed_demo.sh` | `text.embed` |
| `text_demo.sh` | `text.classify` |
| `table_demo.sh` | `table.extract` |
| `series_demo.sh` | `timeseries.forecast` |
| `image_embed_demo.sh` | `image.embed` |

이제 **능력을 등록하는 스크립트 여덟 개 전부**가 기존 능력을 만나면 등록 본문의
`description` 과 DB 를 비교해 **다를 때만** `PATCH /v1/capabilities/{id}` 한다.
**문구를 데모에서 새로 짓지 않는다** — 정본은 저장소이고 DB 를 거기에 맞출 뿐이다.

### 검사를 목록에서 **파생**으로 바꿨다

`test_capability_patch_wiring` 이 데모 이름을 손으로 세고 있었다(Wave I 때 셋).
**아홉 번째 데모에서 또 갈라질 자리**다 — 이번 달에 세 번 겪은 그 모양이라 고쳤다.
이제 「`POST /v1/capabilities` 를 하는 스크립트」를 찾아서 **전부** 검사한다.

`demo.sh` 는 여기 안 걸린다. `image.classify` 는 **seed 가 넣기 때문에 등록하지 않는다** —
예외를 적어 둔 게 아니라 **대상이 아닌 것**이다. 검사가 그 사실도 같이 고정한다.

`PATCH` 본문에 계약 칸이 섞이지 않는지 보는 검사도 더했다. Core 가 400 으로 막지만,
데모가 **시도조차 하지 않게** 한다.

### 실측 (2026-08-31 · 살아 있는 스택)

드리프트를 **일부러 만들어** 확인했다 — `text.classify`·`table.extract` 의 DB 설명을
저장소에 없는 문자열로 바꾼 뒤 데모를 돌렸다.

```text
text_demo          이미 있음 → …  설명 동기화 — DB 가 저장소보다 낡아 있었다 (PATCH)
table_demo         이미 있음 → …  설명 동기화 — DB 가 저장소보다 낡아 있었다 (PATCH)
embed_demo         이미 있음 → …  (이미 최신 — PATCH 안 함)
image_embed_demo   이미 있음 → …  (이미 최신 — PATCH 안 함)
series_demo        이미 있음 → …  (이미 최신 — PATCH 안 함)
```

다섯 다 종단 완주했고, 그 뒤 **능력 9종의 설명이 저장소와 전부 일치**한다.
재현: `bash scripts/<이름>_demo.sh` (Core·Docker 필요).

**라우팅 숫자는 적지 않는다.** 이 변경은 설명을 저장소에 맞출 뿐이고, 그 효과의 크기는
`scripts/route_bench.py` 로만 말한다 (`docs/guide/measured-claims.md`).

### 검증

`run_tests` 352 → **355** OK (skip 7) · `check_submission` **27/27** · `check_release` OK.
변이 확인: `table_demo` 에서 upsert 블록을 지우면 **4종이 실패한다**.

## 측정 숫자는 재현 명령 없이 쓰지 않는다 — 규칙 (문서만) — 2026-08-31

**코드 · DDL · 의존성 · CI 검사 0.** 브리지 `measured-claims-repro-command` Decision (A).

### 규칙

> 측정 숫자를 `capability-catalog.md` 나 `STATE.md` 에 쓸 때는 같은 커밋에 그 숫자를 다시 낼
> 명령이나 `scripts/` 도구를 적는다. 없으면 숫자를 쓰지 않는다.
> `CHANGELOG` 에는 명령 대신 **「무엇으로 쟀나」**(도구·조건·표본·환경)를 적는다.
> 재현이 원리적으로 불가능하면 **그렇게 적는다** — 「1회 · 밴드를 모른다」처럼.

정본은 `docs/guide/measured-claims.md`. `CLAUDE.md` 에는 **한 줄과 링크만** 둔다 —
두 곳에 적으면 갈라진다(그게 이번 세션에 세 번 난 사고다).

### 「개수」는 대상이 아니다

「9종」·「352」·「가중치 8종」은 **세면 나오는 값**이고 이미 실물과 대조하는 검사가 있다
(`check_submission.REQUIRED_WEIGHTS` ↔ `test_checklist_claims` 등). 거기에 명령을 붙이라 하면
`run_tests` 를 수백 번 적는 일이 된다. 대상은 **실행해야 아는 값**뿐이다 — `acc=`·홀드아웃
`N/M`·ms·게이트 통과 수.

### 이 규칙이 **못 막는 것**을 문서 안에 적었다

`text.extract` 「4/5 → 5/5」(#110)·`text.rank` n=5 표(#116)는 막았을 것이다 — 명령이 없으니
숫자를 못 쓴다. 그런데 **「저장소 설명 40/60」(#120)은 못 막는다.** 그때 명령은 있었고
(`scripts/route_bench.py`) **도구가 틀렸다.** 재현 명령은 「누가 다시 잴 수 있는가」를 열 뿐
**「그 도구가 맞는가」는 보지 않는다.** 그걸 잡은 건 **다른 조건과의 대조**였다.

그래서 이 규칙을 **「드리프트 대책」이라고 부르지 않는다.** 「정본 하나 + 파생」 → 「둘이면
대조」 → **이 규칙** → 「종단 한 번 돌리기」의 **셋째 층**이다.

### 검사를 붙이지 않았고, 그 사실을 문서가 적는다

카탈로그의 측정 숫자 여덟 곳 중 **일곱이 이미 `route_bench.py` 를 가리켜** 검사의 값이
크지 않다고 봤다(Decision (c) = (A)). 그래서 **이 문서 자신이 「적혀만 있고 기계가 잇지 않는
줄」**이고, guide §7 이 그것을 숨기지 않고 적는다 — (B) 좁은 검사로 갈 조건까지 함께.

### 검증

`run_tests` **352** OK (skip 7) · `check_submission` **27/27** · `check_release` OK.
문서만 바뀌므로 편집 전후 수치가 같다.

## 설명 드리프트를 연다 — `PATCH /v1/capabilities/{id}` (Wave I) — 2026-08-31

**DDL 0 · 새 의존성 0 · 계약 JSONB 불변.** Decision (b).

### 무엇이 문제였나

등록(`POST /v1/capabilities`)은 `(code, version)` UNIQUE 로 **한 번뿐**이고 갱신 경로가
없었다. 데모 스크립트는 그 충돌을 삼키고 기존 id 만 찾아 썼다. 그래서 **저장소에서
`description` 을 고쳐도 이미 등록된 스택에는 영원히 안 들어갔다.** 라우터는 DB 의 설명을
읽으므로, 오래 돌아간 스택은 저장소와 **다른 문구로** 라우팅했다. 이 개발 스택의 `text.ner`
설명은 저장소 어디에도 없는 옛 문자열이었다.

### 연 것은 하나뿐이다

```http
PATCH /v1/capabilities/{id}   ← admin
{ "description": "…" }
```

계약 칸은 **전부 400** 이다 — `input_schema`·`output_schema`·`compute_tier`·
`trust_domain_min`·`quality_profile`·`golden_*`·`max_input_bytes`·`max_attempts`·
`mvp_eligible`·`code`·`version`. 그것들은 `task_input` 복합 FK · `gate_run` · `assignment`
**스냅샷의 원본**이고, **원본이 움직이면 이미 찍힌 스냅샷이 거짓말이 된다.** 바꾸려면 새
버전을 등록한다.

화이트리스트를 **손으로 세지 않는다** — Pydantic `extra="forbid"` 로 모델이 막는다.
계약 칸이 늘어도 여기가 뒤처지지 않는다.

### 데모는 저장소를 정본으로 DB 를 맞춘다

`ner_demo.sh`·`text_extract_demo.sh`·`text_rank_demo.sh` 가 기존 능력을 만나면 등록 본문의
`description` 과 DB 를 비교해 다를 때만 PATCH 한다. **문구를 데모에서 새로 짓지 않는다** —
정본은 저장소이고 DB 를 거기에 맞출 뿐이다 (Decision (a): 홀드아웃에 맞춘 문구 튜닝 금지).

여덟 개가 아니라 **셋만** 고쳤다 — 한 번에 다 바꾸면 무엇이 숫자를 움직였는지 못 가른다.

### 실측 — 그리고 앞선 숫자 하나를 철회한다

동기화는 실제로 됐다 (`text.ner`·`text.extract` 가 옛 문자열 → 저장소 문구 · `text.rank` 는
이미 최신이라 **건너뛰었다**). 그 뒤 `route_bench` 홀드아웃:

| 언제 | 값 |
|---|---|
| DB 가 낡았을 때 | **30/60** (1회) |
| 동기화 뒤 | **36 · 36 · 38** (3회) · `repo` 조건 **37** |

**개선폭을 말하지 않는다.** 같은 조건도 **2점씩 흔들리고**, 30 은 한 번만 잰 값이라 밴드를
모른다.

그리고 **#120 이 카탈로그에 적은 「저장소 설명 40/60」을 철회한다.** 그 값은
`--descriptions repo` 로 잰 것인데, 그 경로가 `CapabilityInfo` 를 새로 지으면서
**`output_kind` 를 떨어뜨리고 있었다.** 라우터 프롬프트는 `kind=` 를 넣으므로 그 조건은
「설명만 바꾼 카탈로그」가 아니었다 — **한 번에 둘을 바꿔 놓고 설명 덕이라 읽었다.**
래퍼를 `dataclasses.replace()` 로 고쳤고(칸을 손으로 세지 않는다), 같은 조건은 **37/60** 이다.

### 검증

| 검사 | 결과 |
|---|---|
| `run_tests` | 334 → **352** OK (skip 7) |
| `tests/integration/check_capability_patch.py` (신규 · DB) | **6/6** — 계약 16칸이 PATCH 전후 **동일** · 계약 칸 17종 전부 거절 |
| `tests/test_capability_patch_wiring.py` (신규) | `SET` 절에 계약 칸을 끼우면 **2종 실패** · `extra:forbid` 를 빼면 **1종 실패** (변이로 확인) |
| `tests/test_route_bench.py` | `_Patched` 가 `description` 외 필드를 **하나도** 안 바꾸는지 dataclass 필드를 순회해 확인 |
| 데모 3종 종단 | 전부 완주 · 「설명 동기화 (PATCH)」 실측 |

## 라우팅 숫자를 재현 가능하게 만들고, 옛 숫자를 정정한다 — 2026-08-30

**측정 도구 하나 + 문서 정정.** 제품 코드 0 · DDL 0 · 새 의존성 0.

### 왜

이 저장소는 라우팅 숫자를 두 번 적었다 — `text.extract` 의 **「4/5 → 5/5」**(#110)와
`text.rank` 의 **n=5 표**(#116). 둘 다 그때 **손으로 고른 프롬프트**였고 하네스가 없어
**아무도 재현할 수 없었다.** 세 번째로 잴 때 그중 하나가 뒤집혔다.

### 정정

- **#116 의 미스 보고를 취소한다.** 「제목·담당자 같은 항목 뽑아줘」가 `text.ner` 로 간다고
  적었지만, 그건 **능력 5종만 등록된 스택에서 n=1** 로 본 것이다. **9종을 모두 등록하고 R=5**
  로 재니 **5/5 로 `text.extract`** — 맞게 간다.
- 재현되는 미스는 따로 있다: 「이 글에 나오는 날짜랑 URL 전부 뽑아줘」 → `text.extract` **5/5**.
- **#110 의 「4/5 → 5/5」는 지우지 않고 옆에 적는다** — 같은 홀드아웃에서 옛 설명 **30/60** →
  저장소 설명 **40/60** 이므로 **경계 문장의 방향은 맞았다.** 틀렸던 것은 **작은 자기 선택
  표본으로 「고쳤다」고 말한 것**이다.

### `scripts/route_bench.py` 신설

같은 프롬프트를 R 번 물어 **어디로 갔는지 센다.** 그게 전부다 — 정확도를 주장하지 않는다.

- **튜닝 세트와 홀드아웃을 나눈다.** 설명을 손보면서 같은 프롬프트로 재면 반드시 좋아진다.
  실제로 그랬다 — 어떤 수정안이 튜닝 **55/60 → 60/60** 이었는데 홀드아웃은 **40/60 → 40/60**
  으로 **순 효과 0** 이었다(미스 하나를 고치고 다른 하나를 깼다). **그래서 그 수정안을 넣지
  않았다.** 기본값이 `--set holdout` 인 이유도 같다 — 좋아 보이는 숫자가 먼저 나오면 안 된다.
- `--descriptions repo` 는 `scripts/*_demo.sh` 가 **등록하려는** 설명으로 덮어 **빈 볼륨에서
  뜬 스택이 할 행동**을 미리 본다. `live` 와의 차이가 곧 아래 드리프트의 크기다.

### 겸사겸사 드러난 것 — 카탈로그 설명이 저장소와 갈라진다

`POST /v1/capabilities` 는 같은 `(code, version)` 에 갱신 경로가 없고(`UniqueViolation`)
데모 스크립트는 그 오류를 삼키고 기존 id 를 쓴다. **저장소에서 설명을 고쳐도 이미 등록된
스택에는 안 들어간다.** 그 차이가 홀드아웃 **10점**이다. 빈 볼륨은 저장소 설명으로 뜨므로
**오래 돌아간 스택만** 나빠진다 — 그래서 아무 검사도 못 봤다. **Core 변경이라 고치지 않고
브리지에 올렸다** (`routing-measured-not-fixed`).

### 검증

`tests/test_route_bench.py` **12종** 신설 — 홀드아웃이 튜닝과 겹치지 않는가 · 두 세트가
실행 능력 9종을 다 덮는가 · 도구가 「정확도를 주장하지 않는다」고 스스로 말하는가 ·
정정한 문구가 다시 지워지지 않는가. `run_tests` 322 → **334**.

## 제품 입구가 능력 아홉 중 둘의 결과를 못 그리고 있었다 (Step 3) — 2026-08-30

**표시 계층만.** Core 스키마·DDL·실행 경로·계약 0 · **새 의존성 0**.

`capreq/results.py` 는 #107 때 **능력이 넷일 때** 쓰였다. 그 뒤 **#110 `text.extract`**(`fields`)
와 **#116 `text.rank`**(`query`·`ranking`)가 들어왔는데 요약기가 그 칸 이름을 몰랐다.
둘 다 `other` 폴백으로 떨어져 `chat.html` 이 `JSON.stringify` 로 **원시 JSON 한 줄**을 뿌렸다.

폴백 자체는 설계대로다 — 「계약이 새 칸을 들고 오면 조용히 삼키지 말고 그대로 넘긴다」.
**삼키지는 않았지만 제품 입구에서 아홉 중 둘이 읽을 수 없는 모양이었다.**

### 고친 것

- `results.py` — `fields` 요약(`key`·`value`·`line`, `start`/`end` 는 대조용으로 유지) ·
  `ranking` 요약(`query` + `rank`·`score`·`overlap`·`text`)
- `chat.html` — 두 표 렌더러. `other` 폴백은 **남긴다** (다음 새 칸도 삼키지 않아야 한다)
- `capreq/README.md` 「눈으로 확인하기」 §3 — 아홉 능력의 결과 모양 여섯 개 표로

### 새 주장을 만들지 않았다

`score` 를 「관련도」·「정확도」로 부르지 않는다. 숫자와 `overlap`(겹친 토큰)을 그대로 옮기고,
화면에 **「겹친 낱말 수로 매긴 순서입니다 — 뜻을 비교한 것이 아닙니다」**를 붙인다.
순위를 다시 정렬하지 않고, 필드 값의 타입도 판정하지 않는다.

**화면 자르기는 데이터 자르기가 아니다.** 앞 20개만 그리되 `count` 는 전체를 말하고
`truncated` 가 사실을 밝힌다. 실행기는 여전히 자르지 않고 던진다
(`NODE_MAX_FIELDS`·`NODE_MAX_CANDIDATES`).

### `chat.html` 에 검사가 하나도 없었다

이 드리프트가 두 번 일어난 이유다 (#110·#116). `capreq/tests/test_chat_html_unit.py` 신설 —
`summarize_result` 를 **실제로 돌려** 나온 칸 이름마다 화면에 그리는 자리가 있는지 본다.
칸 목록을 손으로 두 번 적지 않는다. `chat.html` 에서 `result.ranking` 을 전부 지우면
**이 검사가 실패한다**(확인). 서버 경로에 검사가 0 이라 첨부 버그를 아무도 몰랐던 #112 와
같은 자리다.

**한계:** 부분 문자열 검사라 렌더러를 **반쯤** 지우면 통과한다. 그리고 **브라우저에서
실제로 그려지는지는 여전히 못 본다** — 헤드리스가 없다 (#107 이후 계속).

### 검증

capreq 단위 38 → **52**. 살아 있는 Core 로 `/api/tasks/{id}` 실측 — `text.rank` 는
`ranking.query="느린 쿼리 인덱스"` + 3줄, `text.extract` 는 `fields` 3건이 **구조화 요약으로**
나왔고 `other` 로 새지 않았다. `chat.html` 은 `node --check` 로 문법만 봤다.

## 카탈로그 +1: `text.rank` — 겹친 낱말이 근거다 (Wave G) — 2026-08-30

**9번째 실행기.** DDL 0 · 새 의존성 0 · 새 학습 0 · 외부 말뭉치 0.
카탈로그 §3 #24 에 **이미 선언돼 있던** 능력을 구현한 것이다 (새 능력을 만든 게 아니다).

### 무엇을 하나

첫 번째 비어 있지 않은 줄을 **질의**로 보고, 그 뒤의 줄들을 **질의와 같은 낱말을 얼마나
쓰는가**로 줄 세운다. 결과는 `{"query", "ranking":[{"rank","line","text","score","overlap"}]}`.

**뜻을 안다고 주장하지 않는다.** 동의어·어형 변화·문맥을 보지 않는다 — 「자동차」와 「차량」은
**안 겹친다**. 의미 유사도는 `text.embed`, 학습된 관련도는 `retrieve.dense`·`retrieve.rerank`
몫이다. 타입 span 은 `text.ner`, `키: 값` 필드는 `text.extract`, 격자는 `table.extract` 다.

텍스트를 읽는 능력이 넷이 됐고 **내놓는 것**이 갈린다:

```text
text.ner       타입 span (키 없음)
text.extract   「키: 값」 필드 (줄에 적힌 이름표)
table.extract  격자 (행 × 열)
text.rank      후보 줄의 순위 (겹친 낱말이 근거)
```

### 규칙을 전부 적었다 (`app/rank_rules.py`)

결과가 왜 그런지 설명할 수 없으면 규칙 기반이라 말할 자격이 없다.

- 첫 비어 있지 않은 줄 = 질의 · 나머지 = 후보. 빈 줄은 **후보 번호를 밀지 않는다**
  (`line` 은 원본 줄 번호다 — `text.extract` 와 같은 규약)
- 토큰 = 유니코드 글자·숫자의 연속 · **소문자로 접는다**
- 점수 = **자카드** `|∩|/|∪|` (4자리 반올림). **집합이라 같은 낱말이 여러 번 나와도 한 번** —
  줄이 길다고 점수가 오르지 않는다
- 정렬 = 점수 내림차순 · **동점이면 원래 줄 번호 순.** 같은 입력이면 언제나 같은 순서다 —
  순위에 우연이 있으면 증적이 뜻을 잃는다
- 질의에 토큰이 없으면 전부 0 점. 0 점은 **「관련 없음」이 아니라 「낱말이 안 겹쳤다」**다

`overlap`(겹친 토큰)을 결과에 넣는다 — **왜 그 점수인지 사람이 대조**할 수 있어야 하고,
`text.ner`·`text.extract` 가 `start`·`end` 를 주는 것과 같은 이유다.

### 설명에 「하지 않는 일」을 적는다

`text.extract` 에서 배운 것(#110·#112)을 그대로 적용했다. 등록 `description` 이
`text.embed`·`retrieve.*`·`text.ner`·`text.extract` 를 **이름으로** 가리킨다.
이웃이 넷이면 경계를 안 적을 때 라우터가 섞을 자리도 넷이다.

### 새 학습이 없다

`RuleTextRank` 는 파라미터 0 이고 `rule_rank.safetensors` 는 버퍼 한 칸짜리 자리표시자다.
그래서 `rule_ner.safetensors` · `rule_extract.safetensors` 와 **셋 다 바이트가 같다**
(sha `15458b00…`). 숨기지 않고 meta·카탈로그·체크리스트에 적었다 — **구별하는 것은 `arch`**
이고 증적에는 arch 와 sha 가 사실대로 남는다.

### 자르지 않고 던진다

후보 수가 러너 한도(`NODE_MAX_CANDIDATES`)를 넘으면 잘라서 돌려주는 대신 실패한다 —
자르면 「전부 줄 세웠다」가 거짓이 된다. **계약 항목이 아니라 러너 자원 한도**이고,
계약이 정하는 것은 `max_chars` 다.

### 종단 실측이 한계도 같이 보였다 (2026-08-30)

`scripts/text_rank_demo.sh` — 계약 게이트 6검사 OK · `gate_run PASSED` → 바인딩 →
`COMPLETED` · 증적 `node=…030` · `team → team` · `M <= M`. 그런데 결과가 이랬다:

```text
질의: 느린 쿼리 인덱스
1. score=0.7500 overlap=느린,인덱스,쿼리 | 인덱스 없이 느린 쿼리
2. score=0.1667 overlap=느린             | 느린 쿼리를 인덱스로 고쳤다
```

2위 줄은 사람이 보면 1위만큼 관련 있는데 0.1667 이다 — 「쿼리를」·「인덱스로」에 **조사가
붙어** 다른 토큰이 되기 때문이다. **버그가 아니라 선언한 한계가 실제로 그렇게 나온 것**이다.
한국어 조사·어미를 다루려면 형태소 분석이 필요하고 그건 규칙 실행기가 할 일이 아니다.
숨기지 않고 카탈로그에 적었다 — **그래서 품질을 주장하지 않는다.**

### 이웃 라우팅을 뺏지 않았는지 격리해서 쟀다 (n=5 · 품질 주장 아님)

같은 프롬프트 5개를 `text.rank` **있는 카탈로그**와 **뺀 카탈로그**에 각각 물어 차이만 봤다
(`qwen2.5:3b`). `text.rank` 는 자기 것만 가져갔고(「겹치는 단어 기준으로 줄 세워줘」 → conf 1.00),
나머지 네 줄은 넣기 전후가 **같다**. 「제일 비슷한 줄」은 `text.rank` 가 있어도 안 가져간다 —
「비슷하다」는 의미 유사도이고 등록 설명이 그것을 배제한다.

`text.extract` 요청이 `text.ner` 로 가는 미스는 **`text.rank` 를 빼도 똑같다** — 이 변경이
만든 것이 아니라 두 이웃 사이에 남아 있던 것이다. 여기서 고치지 않고 브리지에 적었다.

### 검증

`tests/test_text_rank.py` **31종** 신설 · `run_tests` 291 → **322**.
필수 가중치 7종 → **8종** (`check_submission` · `check_release` · 체크리스트 S4-1).
`step6-executors` §3 「모델 없이도 됨」이 **셋**이 됐다 — 추정이 아니라 실측이다.

## 사용 안내 §5.1 이 제품보다 뒤에 있었다 — 사실 동기화 (Wave F) — 2026-08-30

**문서 한 파일 · 코드 0 · DDL 0.** 새 주장·새 숫자 0.

`docs/guide/user-guide-ko.md` §5.1 은 D22 이전 문구였다 — 「**미리 허용된** 사진(또는
번호)을 고릅니다」 · 「아무 사진이나 마음대로 올리기 → **허용된 묶음만**」. 그런데 D8′·D22 로
Core 중개 수집이 들어왔고 capreq 가 그 경로를 쓴다 (#112 에서 종단 실측). **제품이 하는
일을 못 한다고 적은 문장**이었다.

### 고친 것

- §5.1 입력을 **두 갈래**로 적는다 — ① 파일을 붙이면 접수처가 직접 받아 지문(해시)·크기·
  형식·올린 사람을 장부에 적고 그 번호로 일감을 만든다 ② 첨부 없는 데모는 허용된 번호이며
  **사진 과목에만** 있다 (#112: 글·표 과목은 첨부가 없으면 거절한다).
- 「안 되는 것」을 **「접수처를 건너뛰고 넣기」**로 바꾼다. D8′ 가 기각하는 것은 «자유 업로드»가
  아니라 **«비통제 수집»**(링크·임시 열쇠)이다. 「어디로 갔는지 장부가 답할 수 없다」가 그 이유다.
- 받는 **형식·크기는 과목이 정한다**는 사실을 명시 — 과목이 정해 두지 않았으면 접수처는
  파일을 받지 않는다 (`capability.input_schema.mediaTypes` · `max_input_bytes`).
- §8 한 장 요약의 사용자 한 줄을 위와 맞춘다.
- 문서 이력에 v0.3(§1.5 · #111 에서 들어왔는데 기록이 빠져 있었다) · v0.4 를 적는다.

### 안 한 것

「이제 아무 파일이나 올릴 수 있습니다」 같은 **범위를 넓히는 새 문장** · 보존·삭제 정책 문구
신설 · §1.5 · §7 FAQ · 코드 · 스키마 · DDL.

검증: `run_tests` **291** OK (skipped 7) · `check_submission` **26/26**.

## capreq 첨부가 한 번도 동작하지 않았다 — 종단 실측으로 잡았다 — 2026-08-30

Ollama 가 설치돼 **#107 이후 처음으로 브라우저와 같은 경로를 끝까지** 돌렸다.
그 자리에서 버그 둘이 나왔다. **DDL 0 · 새 의존성 0.**

### 1. 첨부가 조용히 버려졌다 (제품 1호부터 있던 버그)

```python
from fastapi import UploadFile
...
if isinstance(up, UploadFile) and up.filename:   # 항상 False 였다
```

`fastapi.UploadFile` 은 `starlette` 것의 **하위 클래스**이고 `request.form()` 이 돌려주는
것은 **starlette 인스턴스**다 — 부모 인스턴스는 자식 클래스의 instance 가 아니다.
그래서 첨부 분기가 **한 번도 실행되지 않았고**, 요청은 allowlist 데모 경로로 떨어져
`datasetId=eurosat-rgb · caseId=ic1-0001` 로 텍스트 능력 작업을 만들었다.

`starlette.datastructures.UploadFile` 로 검사한다 (`fastapi` 것이 그 하위라 둘 다 잡힌다).

### 2. 그 작업은 영원히 QUEUED 였다 — 이제 미리 거절한다

Node 는 **이미지 밖 모달리티에 로컬 골든셋 폴백이 없다**(D8′). 첨부 없이 보낸 텍스트
작업은 `400 text 실행에는 Core 가 중개한 입력이 필요하다` 로 재시도만 하다 FAILED 가 된다
(실측: 한 작업당 attempt 5회). 클라이언트가 **만들기 전에** 거절한다 —
`{code} 는 파일 첨부가 필요하다`. 이미지의 `caseId` 데모 경로는 그대로 둔다.

### 3. 왜 아무도 몰랐나 — 서버 경로에 검사가 0 이었다

`capreq/tests/test_server_unit.py` **6종** 신설 (FastAPI `TestClient` · Core·Ollama 대역).
**고침을 되돌리면 4종이 실패한다** — 확인했다. CI `capreq` 잡에 `fastapi` ·
`python-multipart` 를 넣었다 (둘 다 `capreq[server]` 의 것이고 이미 고지돼 있다).
capreq 검사 32 → **38**.

### 4. 라우팅 설명도 손봤다 (실측 4/5 → 5/5)

같은 실행에서 「이메일·IP·날짜 찾아줘」가 `text.extract` 로 갔다. 두 능력의 설명이
경계를 말하지 않아서다. 실제 `qwen2.5:3b` 로 프롬프트 5개를 옛/새 설명에 각각 돌려
**4/5 → 5/5** 를 확인하고 반영했다 (`ner_demo.sh` · `text_extract_demo.sh` ·
`sample-catalog.json`). **n=5 다 — 품질을 주장하지 않는다.**

> 이미 등록된 DB 의 설명은 바뀌지 않는다. 능력 설명 갱신 API 가 없고 버전을 올릴 만한
> 변경도 아니다 — 새로 세우는 스택부터 적용된다.

### 종단 실측 (2026-08-30 · Ollama 0.33.2 · `qwen2.5:3b`)

```text
/api/health      capabilities=4 · executor=true · input_upload=true
/api/chat        첨부 + 실행 → 라우팅 text.ner@1 conf=1.00 · inputId=cceadef4…
/api/tasks/{id}  1s 만에 COMPLETED
화면에 그려질 것  email ops@example.dev 8-23 · ipv4 10.0.0.7 29-37 · iso_date 2026-08-30 41-51
증적            node=…030 · agent=29819aab… · domain=team · tier=M
```

**아직 못 본 것:** 브라우저 자체(`chat.html` 의 JS 렌더링). 헤드리스 브라우저가 없다 —
서버가 주는 JSON 까지만 확인했다.

## 제품 데모 한 파일 — `scripts/product_demo.sh` (Wave D) — 2026-08-29

**제품 코드 0 · DDL 0 · 새 의존성 0.** 스크립트 하나 + 문서 셋 + 검사 하나.

제품 주장을 읽을 수는 있어도 **한 번에 돌려 볼 수는 없었다.** 데모가 흩어져 있어
「능력만 말하고, 파일을 붙이면, 승인 Node 에서 실행되고, 증적이 조회된다」를 보려면
서너 개를 순서를 알고 돌려야 했다. 한 파일로 모았다.

| 단계 | 부르는 것 | 보이는 것 |
|---|---|---|
| 1 | `GET /health` | 접수처가 살아 있나 |
| 2 | `GET /v1/capabilities` | 무엇을 할 수 있나 (등록된 능력 표) |
| 3 | — | `text.ner` 이 없으면 `ner_demo.sh` 로 등록·게이트까지 (한 번만) |
| 4 | `POST /v1/inputs` → `POST /v1/tasks` | **능력만 말한다** — 기기 주소가 어디에도 없다 (D22·D8′) |
| 5 | `GET /v1/tasks/{id}` | 결과 + **어느 기기·어느 Agent·어느 경계** |
| 6 | `GET /v1/ops/work-units` | 얼마나 돌았나 — Core 관측(정본)과 Node 힌트를 나란히 (D26) |

**Core 의 공개 API 만 부른다.** DB 를 직접 보지 않는다 — 심사·동료가 같은 명령으로 같은 것을
볼 수 있어야 하기 때문이다. `set -euo pipefail` 이고 중간에 멈추면 어디서 멈췄는지 찍는다.

**3번이 있는 이유:** 데모가 「먼저 저걸 돌리세요」로 끝나면 한 파일이 아니다.

**품질을 주장하지 않는다.** 여기 쓰는 `text.ner` 은 `quality_profile='none'` 이다 —
이 스크립트가 보이는 것은 **경로와 증적**이지 정확도가 아니고, 그 문장을 스크립트·가이드
양쪽에 적었다.

**실측** (로컬 스택 · exit 0):

```text
결과 — 찾은 span 3 건 (email · ipv4 · iso_date)
어디서 돌았나 — node=…030 · agent=29819aab…
경계          — task=team -> node=team · capability=M <= node_max=M
최근 7일 · 종결 배정 3건 · Core 관측 합 8222 ms · Node 힌트 합 6912 ms
vram_mb_peak · energy_wh — 미계측 (0 · 0)
```

**문서:** `README.md` 빠른 시작에 ★ 한 줄 + 실행 스크립트 표 · `user-guide-ko.md` §1.5
「제품 체험」(두 명령). **`.ps1` 판은 없다**는 것도 적었다 — 촬영은 PowerShell 로 한다.

**검사:** `tests/test_product_demo.py` **10종** — 다섯 단계를 **전부** 부르는가 · 증적 네 값을
찍는가 · `dummy` 실행을 성공으로 세지 않는가 · 요청에 기기를 지목하는 칸이 없는가 ·
품질을 주장하지 않는다고 적었는가. 한 칸이라도 빠지면 **주장의 일부가 증명되지 않은 채**
데모가 초록으로 끝나는데, 그게 이 검사가 막는 유일한 사고다. `run_tests` 281 → **291**.
## 카탈로그 +1 — `text.extract` (8번째 실행기 · Wave C) — 2026-08-29

**DDL 0 · 새 의존성 0 · 새 학습 0 · 외부 말뭉치 0.** 카탈로그 구현 **7종 → 8종**.

**무엇을 하나.** 평문 한 줄에 `이름: 값` 꼴로 **이름표가 붙어 있는 것**만 가져온다.
「그런 줄이 있었다」까지만 말한다 — **자연어 이해를 주장하지 않는다.** 값의 뜻도 타입도
판정하지 않는다(그건 `text.classify`·`text.ner` 몫이다).

텍스트를 읽는 능력이 셋이 됐고, 그 셋이 **무엇을 찾는지**가 갈린다:
`text.ner` = 타입 span(키 없음) · **`text.extract` = `키: 값` 필드** · `table.extract` = 격자.

**규칙을 전부 적었다** (`app/extract_patterns.py` docstring). 결과가 왜 그런지 설명할 수
없으면 규칙 기반이라 말할 자격이 없다 — 구분자는 첫 `:`/`=` 하나 · 글머리표는 뗀다 ·
**키에 글자가 없으면 버린다**(`12:30` ✗) · 구분자 뒤가 `//` 면 버린다(`https://` ✗) ·
같은 키가 여러 번 나오면 **전부 남긴다**. `start`·`end` 는 **값**의 위치라
`text[start:end] == value` 다 — `text.ner` 과 같은 규약이라 증적을 사람이 대조할 수 있다.

**새 학습이 없다.** `RuleTextExtract` 는 파라미터 0 이고 `rule_extract.safetensors` 는
버퍼 한 칸(`rule_marker`)짜리 자리표시자다 — `text.ner` 에서 배운 패턴 그대로다
(state dict 가 완전히 비면 `weights_fingerprint` 가 막는데, 그 검사는 약화시키지 않았다).
그래서 **`rule_ner.safetensors` 와 바이트가 같다**(sha `15458b00…`). 숨기지 않고
meta·카탈로그·체크리스트·PR 에 적었다 — 구별하는 것은 `arch` 이고 증적에 사실대로 남는다.

**자르지 않고 던진다.** 필드 수가 러너 한도(`NODE_MAX_FIELDS`)를 넘으면 실패한다.
자르면 「필드를 다 읽었다」가 거짓이 되고 쓰는 쪽은 뒤가 잘린 줄 모른다 (`table.extract` 규율).
이것은 **계약 항목이 아니라 러너 자원 한도**다 — 계약이 정하는 것은 `max_chars` 다.

**종단 실측** (`scripts/text_extract_demo.sh` · 로컬 스택):

```text
OK   weights_fingerprint · arch · max_params(0 <= 1000) · preprocess · input_schema
OK   output_schema — 칸 1개(fields)가 계약을 만족한다
gate_run PASSED → 바인딩 → COMPLETED · fields 3건 (Ticket·Severity·Assignee)
증적: assignment SUCCEEDED · node=…030 · team → team · M <= M
```

이름표가 없는 줄(`not a field line`)은 필드로 읽지 않았다 — 데모가 그것도 검사한다.

**검사:** `tests/test_text_extract.py` **21종** 신설 (규칙 11 · 배선 4 · 정직한 주장 4 · 가중치 2).
`run_tests` 260 → **281**. 가중치 필수 목록 6종 → **7종**(`check_submission`·`check_release`·
체크리스트 S4-1 — `test_checklist_claims` 가 셋을 대조한다).

**브리지·문서 정리(같은 PR):** `pr-c-work-units`·`product-handoff-to-claude` Confirm →
`status: done` + ack 기록 · **#107 Confirm 블록을 뒤늦게 채웠다**(Decision 이 필요 없는
범위라 Proposal 없이 가면서 Confirm 도 같이 빠졌다) · `STATE.md` 의 「PR 대기」를
머지됨으로 정정 · `step6-executors.md` 의 「모델 없이도 됨」을 **추정에서 실측으로**.

## work_units 계측 마감 — 정본은 Core 관측이다 (P2-2 · D26) — 2026-08-29

**DDL 0 · 새 컬럼 0 · 마이그레이션 0 · 새 의존성 0.** 브리지 `pr-c-work-units`
Decision(D1-a · D2-a · D3) 을 그대로 구현했다. **D4(조회 인증)는 손대지 않았다.**

**로드맵이 실물과 달랐다.** P2-2 는 「`duration_ms`·`vram_mb_peak` 계측」이었는데
**컬럼은 이미 있었다.** 남아 있던 것은 「무엇을 정본으로 볼 것인가」다.

**정본 = Core 관측** (`assignment.finished_at − created_at`). 저장하지 않는 파생값이다.
`assignment.duration_ms` 는 Node 가 **자기 추론 구간만** 잰 값이라 **힌트**로 함께 낸다 —
지우지 않는 이유는 「관측 − 자기신고 = 일 밖에서 쓴 시간」이 둘이 있어야 나오기 때문이다.
근거는 **절대규칙 4의 확장**이다: Node 가 자기 등급을 주장할 수 없다면 자기 일의 양도
같은 질문을 받는다. 실측 평균 차 **789 ms**(최대 +1982) · 자기신고 최소 0 ms 인데 관측은 수백 ms.

**`vram_mb_peak` · `energy_wh` 는 미계측이다.** CPU 함대이고 재는 장치가 없다.
RSS 로 대신 채우면 **칸 이름이 거짓말이 된다** — 채우지 않고 **센다**
(`vram_measured`·`energy_measured` · 완주해도 0).

**읽는 길 하나:** `GET /v1/ops/work-units` — `developer` · read-only · 시크릿 없음 ·
기본 최근 7일(`?days=` 1..90). 건수 · Core 관측 ms 합/평/최대 · Node 힌트 ms 합/평 ·
**능력별 · Node 별 분해**. `/v1/ops/status` 는 확장하지 않았다. 종결된 배정만 센다.

**컬럼의 뜻을 DDL 정본에 적었다** — `docs/spec/schema.sql` 의 `assignment` 안 주석 6줄.
`COMMENT ON` 마이그레이션을 새로 만들지 않은 것은 Decision 이 「DDL 추가 없음」이어서다
(세대 18→19 는 README·런북 표기까지 따라 고쳐야 한다). 살아 있는 DB 에서 보여야 하면 올린다.

**검사 둘 (신설):**

- `tests/test_work_units_wiring.py` — **DB 없이** 정본이 뒤집혔는지 본다. 쓰기 없음 ·
  `canonical == "core_observed_ms"` · 미계측을 채우지 않음 · 기본 창 7일 · 라우트↔문서↔스키마.
- `tests/integration/check_work_units.py` — claim → complete 로 배정을 실제 완주시킨 뒤
  **관측 ≥ 자기신고**를 두 방향으로 본다 (Proposal §3-5 의 회귀 검사).

`run_tests` 247 → **260**.

**검사가 자기 설명에 걸렸다 (다섯 번째).** `vram` 을 RSS 로 대체하지 못하게 「`rss` 단어
금지」로 썼더니 **「RSS 로 대체하지 않는다」고 적어 둔 응답 문자열**에 걸렸다. 이번엔 주석도
docstring 도 아니라 코드가 내보내는 값이라 `_srcguard` 로도 못 걷어낸다. 단어 금지 대신
**「무엇을 했나」**로 바꿨고 `tests/_srcguard.py` 표에 5번으로 적었다.

## capreq 결과 표시 · 상태 폴링 (제품 입구 마감) — 2026-08-29

**Core 스키마·DDL 변경 0 · 새 의존성 0.** capreq 가 「고르기」에서 멈추지 않고
**실행 상태와 결과를 눈으로 보여 주는** 데까지 간다.

**결과 표시:** `capreq/results.py` 신설 — Core `result_ref` 를 표시용으로 요약한다.
계약이 정한 칸 이름을 그대로 읽는다: `label`·`confidence` · `entities` ·
`vector`/`forecast`(dim + 앞 8개) · `columns`·`rows`(앞 10행) · 그 밖의 칸은 `other`.
증적 칸(`weights_sha256`)은 결과로 새지 않는다. **새 품질 주장 없음.**

**상태 폴링:** `POST /api/chat` 에 `wait` 추가 — `false` 면 Task 만 만들고 즉시 반환한다.
`GET /api/tasks/{id}` 신설(Core 응답을 옮길 뿐 새로 판정하지 않는다). 브라우저는
`wait=false` 로 보내고 1초 간격으로 폴링해 `QUEUED → ASSIGNED → RUNNING → COMPLETED`
배지를 갱신하고, 종결되면 배정 증적(node·agent·domain·tier)을 한 줄 붙인다.
CLI·JSON 호출은 기본값 `wait=true` 로 종전과 같다.

**고친 것 (실행 경로 버그):**

- `timeseries.forecast` 첨부가 **통째로 막혀 있었다** — `media.py` 에 `timeseries`
  모달리티가 없어 「업로드 MIME 규칙이 없다」로 떨어졌다. 능력별 override 표를 두고
  계약(`input_schema.mediaTypes`)에 맞췄다. `image.classify` 는 JPEG 만(0012),
  `table.extract` 는 평문.
- 첨부 없는 실행이 **LLM 을 두 번** 불렀다 — `route()` 뒤에 `route_and_maybe_execute()`
  가 다시 라우팅했고, 응답에 실린 판단과 실제 실행한 판단이 갈릴 수 있었다.
- 폴링이 `COMPLETED`·`FAILED` 만 종결로 봤다. `TIMEOUT`·`CANCELED` 는 poll_max 까지
  헛돌았다 (schema.sql 의 status 8종 중 4종이 종결).
- 카탈로그 등록 스크립트 3개의 이름이 복사 실수로 전부 `"text embed (fixed projection)"`
  이었다 (`image.embed`·`table.extract`·`timeseries.forecast`). 이 이름은 라우터
  allowlist 프롬프트에 그대로 들어간다.

**검증:** `capreq` CI 잡 신설 — `httpx` 만 설치하고 `capreq/tests` 를 돌린다
(위 `unit` 잡의 「의존성 설치 없음」은 그대로). 19 → **32 테스트**
(`test_results_unit` 12 · `test_capnet_unit` 9 · `test_media_unit` +4).
어댑터 테스트는 `httpx.MockTransport` 로 Core 없이 D8′ 본문·종결 상태·오류 매핑을 본다.

## capreq 입력 챗봇 + text.ner (제품 1호) — 2026-08-28

**Core 스키마·DDL 변경 0.** 설계·초안은 Cursor, 정리·수정·검증은 Claude.

**capreq 입력 챗봇 (PR-A):** 웹 UI 파일 첨부(+·드래그) + 자연어 → Qwen 라우팅 →
`POST /v1/inputs` → `/v1/tasks` `{ inputId }`.

- `CapNetAdapter`: 인증 헤더를 `CapNet-Key` 로 수정(Core `apikey.SCHEME` 과 일치) ·
  `upload_input()` · `inputId` 실행 경로.
- MIME 선검사(`capreq/media.py`) · `python-multipart`(Apache-2.0) server 의존 ·
  `THIRD-PARTY-LICENSES.md` 한 줄 추가.
- **자유 업로드 경로 없음** — 바이트는 Core 가 받는다(D8′ · 해시·크기·MIME·보존).

**text.ner (PR-B):** `RuleTextNer` · 규칙 span(`email`·`url`·`ipv4`·`uuid`·`iso_date`) ·
`quality_profile='none'` · `scripts/ner_demo.sh` · 카탈로그 **7번째 구현**.

- **게이트가 걸렸다:** 텐서 0개면 `weights_fingerprint` 가 「텐서가 하나도 없다」로 FAIL.
  검사를 약화시키지 않고 버퍼 `rule_marker` 한 칸을 뒀다 — `parameters()` 밖이라
  파라미터 수는 여전히 **0**. 가중치 재생성 (16B → 76B · sha `15458b00…`).
- 데모 실측: 계약 게이트 PASSED · Task COMPLETED · `entities` 3건(email·ipv4·iso_date) ·
  assignment SUCCEEDED · team→team · M ≤ M.
- 필수 가중치 **5종 → 6종** (`check_submission` · `check_release` · 체크리스트 S4-1).
  `v0.1.0-contest` zip 은 5종 그대로 — 그 기록은 고치지 않았다.

**검사 둘을 실물에 맞췄다 (의도 불변):** `test_series_modality` 의 D8′ 폴백 금지 목록에
`text_ner` 추가 · `test_report_claims` 는 제출 원고(6종)를 얼린 채 `POST_CONTEST` 에
이름을 적어야 늘 수 있게 했다.

**검증:** `run_tests` **247** · `check_submission` **25/25** · `check_release` 통과 ·
`clean_room` **9/9** · `prod_room` **27/27** · `ner_demo.sh` 종단 PASSED.

## 출품 포털 제출 완료 · 이후 트랙 A — 2026-08-27

**제품 코드 0 · DDL 0.**

- 대회 포털 제출 완료 (결과보고서 · 시연 · 소스). G7–G9 ✅.
- **D25 (트랙 A):** 공개 저장소 `capnet`에서 계속 개발. 출품 재현본은 태그
  [`v0.1.0-contest`](https://github.com/gncorpseo-commits/capnet/releases/tag/v0.1.0-contest)
  로만 고정(이동·재작성 금지). 새 저장소 분기 없음.

## Release `v0.1.0-contest` — 2026-08-27

**제품 코드 0 · DDL 0 · 출품 트랙.**

- 태그 `v0.1.0-contest` = `238427d` · GitHub Release 발행 · `capnet-v0.1.0-contest.zip` 첨부 (2.5MB · 335파일).
- 태그 기준 재검증: `run_tests` 240 · `check_submission` 24/24 · `check_release v0.1.0-contest` 통과.
  (`clean_room`·`prod_room` 은 이 환경에 Docker 가 없어 미실행 — 직전 기록 9/9 · 27/27.)
- `contest-submission-pack.md` §3·§10 · checklist G9 = 🔶 (**포털 업로드**만 사람 몫으로 남음).

## 결과보고서 최종본 + 사람 개입 정리 — 2026-08-25

**제품 코드 0 · DDL 0 · 출품 트랙.**

- `docs/ops/contest-report-915-gn.{docx,pdf}` — 공식 양식 이식 최종 (저장소 ASCII명 · 포털은 `_915(지엔)`).
- `docs/ops/contest-submission-pack.md` · checklist G7: docx/PDF ✅ · Release·포털 남음.
- `docs/retrospective/human-intervention.md` — 팀 설계(D-결정·반증) vs AI 구현 보조 재구성.
- 시연 mp4 경로: `…CAPNET.mp4` (파일명 끝 공백 제거 반영).

## capreq — 로컬 LLM 능력 라우터 (독립 모듈) — 2026-08-24

**DDL 0 · Core 스키마 비변경.**

- 신규 `capreq/` — 자연어 → 등록 capability 코드. 기본 모델 **Qwen2.5** (`qwen2.5:3b`, Ollama).
  Gemma는 `CAPREQ_OLLAMA_MODEL`로 전환.
- 어댑터: CapNet (`GET /v1/capabilities` · 선택 `POST /v1/tasks`) / 정적 JSON / 실행 없음.
- CLI: `route` · `chat` · `serve`(선택 FastAPI). 단위 검사 4.
- CapNet 제품 주장과 분리: capreq = 입구 라우터, Core = 실행·통제·증적.

## YouTube 시연 URL 확정 — 2026-08-23

**제품 코드 0 · DDL 0.**

- 시연 영상 일부 공개: https://youtu.be/RjFiGpmLTbk
- `contest-report-form-draft.md` · `contest-submission-pack.md` · checklist G8 반영.

## 출품 제출 패킷 + 시연 영상 완료 — 2026-08-23

**제품 코드 0 · DDL 0.**

- `docs/ops/contest-submission-pack.md` — 영상·보고서·Release·포털 체크리스트 한 파일.
- 시연 mp4: CapCut 내보내기 **172.9s · 1080p · ~38MB** (≤3분·≤200MB 충족).
- 남음: YouTube URL · 양식 PDF · `v0.1.0-contest` Release.

## CapCut 편집 가이드 — 2026-08-22

**제품 코드 0 · DDL 0.**

- `docs/ops/capcut-edit-guide.md` — PC 자르기(`Ctrl+B`)·텍스트/자동캡션·런북 §2 복붙·내보내기.
- `docs/INDEX.md` · `shoot-day-runbook.md` 링크.

## 촬영 런북 리허설 보강 + proof_ab.ps1 — 2026-08-21

**제품 코드 0 · DDL 0.**

- `scripts/proof_ab.ps1` — `proof_ab.sh` PowerShell 포팅. 본편에서 WSL 없이 A/B.
  실측: A·B 실게이트 PASSED · 교차 Task COMPLETED.
- `docs/ops/shoot-day-runbook.md` — 리허설 Q&A 반영: `pwsh`·한글·UI URL·생존 API·
  Docker/`down -v` 해설·EuroSAT 라벨·골든셋·sanity/violations/A/B 용어·
  160–170=demo 끝 재강조·GitHub README 컷. 스토리보드 150–160 한 줄.
- 자막 §2-A(같은 답·편차 수치 금지)는 그대로.

## 자라는 숫자를 문서에서 뺐다 — 넷 다 어긋나 있었다 (출품 위생) — 2026-08-17

**제품 코드 0 · DDL 0 · 새 실행기 없음.**

### 안전 사슬 표의 네 칸이 전부 틀렸다

| 표기 | 실물 |
|---|---|
| `check_api_key` (23) | **22** |
| `check_node_credential` (17) | **18** |
| `check_enforcement` (20) | **30** |
| `prod_room.sh` (14) | **27** |

**숫자를 맞추지 않고 표에서 뺐다.** 이 검사들은 능력·강제 경로를 더할 때마다 는다 —
표에 못박아 두면 **다음 사람이 숫자만 고치게** 되고, 안 고치면 조용히 어긋난다.
넷이 동시에 틀어져 있었다는 것이 그 증거다.

봐야 할 것은 **「전부 통과」**이고, 개수는 `run_tests.sh` 와 `prod_room.sh` 출력이
그때그때 말한다. **왜 안 적는지도 문서에 남겼다** — 없으면 다음 사람이 「빠졌네」 하고 채운다.

### 반대로 고정돼야 하는 것은 고정했다

마이그레이션 세대처럼 **눈으로 대조하는 값**은 실물과 정확히 맞아야 한다.
`test_doc_counts` 가 둘을 갈라서 본다 — **자라는 값은 못박히면 실패**,
**고정 값은 어긋나면 실패.**

### 갱신일이 내용보다 오래돼 있었다

`STATE`(08-15) · 런북(08-15) · 카탈로그(08-15) · **체크리스트(08-08)**.
「오늘」을 요구하면 매일 실패하므로, **최신 CHANGELOG 항목보다 오래되지 않았는가**로 본다.

### 새 산출물이 문서 지도에 없었다

`scripts/check_release.sh` 가 `INDEX` 에 안 올라가 있었다 — 안 올리면 다음 사람이 못 찾는다.

### 변이 검사

개수를 다시 못박으면 **FAIL** · `INDEX` 에서 빼면 **FAIL** · 갱신일을 되돌리면 **FAIL** (3/3).

`run_tests` 234 → **240** · `check_submission` 24/24 · `check_release` 통과.

## 제출 패키지를 미리 검증한다 — 8/25 에 처음 보면 늦다 (출품 트랙) — 2026-08-16

> **정정 (같은 PR).** 아래 「일정 정본 정정」이 **첫 커밋에 들어가지 않았다.**
> 원인은 내 실수다 — `check_release.sh` 변이 검사에서 쓴 `git reset --hard` 가
> **아직 커밋하지 않은 문서 편집을 지웠다.** 테스트는 전부 통과했는데,
> **문서를 보는 검사가 없어서** 아무도 못 잡았다.
>
> 리뷰가 그 구멍을 짚었다. 이제 실제로 고쳤고 **`test_checklist_claims`(9종)로 고정**했다 —
> 같은 유실을 재현하면 **6건이 실패한다.**
>
> 겸사겸사 하나 더 찾았다: 「자체 scratch 가중치 **2종**은 저장소에 유지」가 남아 있었다.
> 능력이 `image.classify` 하나였을 때의 값이고, 지금은 **5종**이 필요하다.

**코드 변경 0(제품) · DDL 0 · 실행기 미착수.**

### 일정 정본이 실제 정책과 어긋나 있었다

`contest-submission-checklist.md` S4 가 **「넣지 않는 것: … 학습 가중치 바이너리」**로
적혀 있었다. 그런데 제품은 가중치를 **넣어야** 돌아간다 — README 가 「가중치와 골든셋
40장이 저장소에 들어 있다」고 말하고, `check_submission` 은 **5종을 요구**한다.

8/25 에 패킹하는 사람이 이 줄을 보면 **지워야 하나 망설인다.** 실제 정책대로 갈랐다:

| | |
|---|---|
| **넣지 않는 것** | EuroSAT 원본 zip · **실험** 가중치(`*_ho*`·`*_hob*`) · `.env` · 캐시 |
| **반드시 넣는 것** (S4-1 신설) | 데모용 가중치 **5종** + `placeholder` |

### zip 을 실제로 열어 본다

`scripts/check_release.sh` — 체크리스트 S2 의 명령을 그대로 돌리고 **압축본을 연다.**
「명령이 있다」가 아니라 「그 명령의 결과가 조건을 만족한다」를 본다.

- 크기 ≤ **50MB** (현재 **2.3MB**)
- 필수 **17종** (라이선스 4 · compose 2 · 스키마 · 데모 3 · 가중치 6)
- 금지 산출물 없음 (`.git` · `.env` · 실험 가중치)
- 최상위 `capnet/` prefix

**태그 없이 `HEAD` 로도 돈다** — 8/25 전에 아무 때나 돌려 볼 수 있다.
`run_tests` 에 물려 이제 **매번** 같이 본다.

### 변이 검사

필수 가중치를 하나 빼면 **FAIL**, `.env` 를 넣으면 **FAIL**. 둘 다 잡는다.

### 재현 기록도 갱신했다

D-2 체크리스트의 「깨끗한 환경 재현 확인」이 **2026-08-09** 에 멈춰 있었다 →
**2026-08-16 · `6609ce1`** (`clean_room` 9/9 · `prod_room` 27/27 · 마이그레이션 18개
체크섬 일치)로 갱신하고, **능력 6종 데모 재현** 항목을 더했다.

### 남은 것은 전부 사람 몫

G7 `hwp/docx`+PDF(양식 파일이 저장소에 없다) · G8 촬영 **D-7**·YouTube ·
G9 태그·Release·포털 업로드 · 붙임2 §4 **AI 보조도구 비율**(근거 수치는 재측정해 뒀다).

## table.extract — 여러 칸을 내는 출력 · 새 가중치 0 (단계 6 ④) — 2026-08-16

**DDL 0 · 새 의존성 0 · 새 가중치 0 · `image.classify@1` 무회귀.**

지금까지 출력은 **한 칸**이었다(`label` 하나 · `vector` 하나 · `forecast` 하나).
이 능력은 `columns`·`rows`·`header_detected` **셋**을 낸다.

### 「출력 이름은 계약이 정한다」를 집합으로 지켰다

단계 6 ② 에서 Core 가 `output_schema.required[0]` 로 **한 칸** 이름을 붙이게 했다.
여러 칸에는 그 방식이 안 통한다. 그래서 **키 집합을 대조**한다 — 계약이 요구한 칸과
정확히 같아야 받고, 다르면 **422** 다. Node 는 값만 내고 모양은 계약이 정한다.

`output` 필드를 더하면서 **「아무것도 안 냈다」 구멍을 열지 않았다** —
`label`·`vector`·`output` 이 전부 비면 여전히 거절한다(dummy 는 예외).

### 새 가중치가 없다

열 타입 추론(`email`·`url`·`ipv4`·`uuid`·`iso_date`·`plain`)은 `text.classify` 가
이미 하는 일이다. **`text_struct_scratch.safetensors` 를 그대로 쓴다** —
같은 아키텍처를 다른 능력에 붙였을 뿐이고 증적에는 `arch`·`weights_sha256` 이 사실대로 남는다.

### 못 하는 것을 할 수 있다고 하지 않았다

카탈로그의 `doc` MIME 은 원래 `application/pdf` · `text/plain` 이었다.
**PDF 파싱에는 라이브러리가 필요하고 이 리포는 새 의존성을 늘리지 않는다.**
계약을 `text/plain` 만으로 선언하고 **카탈로그의 MIME 표도 고쳤다** — 선언만 남겨 두면
「PDF 도 된다」로 읽힌다.

### 자르지 않고 던진다

행·열 상한을 넘으면 잘라서 돌려주는 대신 실패한다. 자르면 「표를 다 읽었다」가 거짓이 되고
사용자는 뒤가 잘린 줄 모른다. 짧은 행을 **채우는** 것은 반대다 — 없던 칸은 빈 문자열이 사실이다.

### 주장하지 않는 것을 결과에 실어 보낸다

머리글 판별은 「숫자가 하나도 없으면 머리글」이라는 느슨한 규칙이라 `header_detected` 로
**그대로 노출**한다. 열 타입은 다수결이라 `support` 로 우세도를 같이 낸다 —
**3/3 과 2/3 을 같게 보이지 않게.**

### 실측

```text
OK   output_schema — 칸 3개(columns, header_detected, rows)가 계약을 만족한다
columns= [(0, 'ipv4', 1.0), (1, 'uuid', 1.0)] · rows= 2행 · header_detected= True
```

`host` 열을 `ipv4` 로, `id` 열을 `uuid` 로 맞혔다. 증적에 `label`·`vector` 는 **없다**.

`run_tests` 207 → **219** (변이 3/3) · `clean_room` **9/9** · `prod_room` **27/27** ·
`acc=0.8500` 불변 · 데모 5종 전부 무회귀.

### 변이 검사가 내 검사를 또 잡았다

`support` 를 지우는 변이가 **통과했다** — 검사가 키 이름만 찾았는데 그 문자열이
계약 스키마에도 있었다. **값을 계산해 담는 줄**을 보게 고쳤다.
## 보고서에 능력 5종 실측을 넣었다 — 주장을 증거로 바꿨다 — 2026-08-16

**출품 트랙(B). 코드 변경 0 · DDL 0 · 실행기 미착수.**

### 「붙는다」는 주장이었다

원고 §주요기능 1) 이 「채점 가능성을 요구하지 않으므로 **분류·요약·임베딩 어디에도 붙는다**」
고 적고 있었다. 지금은 실물이 있다 — **능력 5종이 같은 계약 게이트와 배정 경로로 돌았다.**

| 능력 | 입력 | 출력 | 품질 프로파일 |
|---|---|---|---|
| `image.classify` | 이미지 | 닫힌 라벨 | **golden** |
| `text.classify` | 텍스트 | 닫힌 라벨 | none |
| `image.embed` | 이미지 | 벡터 128 | none |
| `text.embed` | 텍스트 | 벡터 64 | none |
| `timeseries.forecast` | 표 | 수치 배열 4 | none |

**1차는 서면으로 갈린다**(F2). 주장을 증거로 바꾸는 것이 그 자리에서 값이 크다.

### 프레이밍을 조심했다

**다섯 중 넷은 품질을 주장하지 않는다.** 그 사실을 같이 적었다 — 안 적으면
「능력이 다섯인데 성능은 왜 안 밝히나」로 읽힌다.

원고에 적은 것은 **모델 성능이 아니라 계약과 라우팅이 능력 종류에 매이지 않는다**는 것이다.
품질 주장은 선택 프로파일을 붙인 `image.classify` 하나에서만 한다(§7 그대로).

### 주장은 재현 가능해야 한다

5종을 주장하면서 명령을 안 주면 **심사위원이 확인할 수 없는 주장**이 된다.
구동 절에 네 데모를 넣고 **`bash` 전용**임을 명시했다(`.ps1` 이 없다 — 없는 것을
있다고 하면 그것이 거짓이 된다).

### 곁다리로 찾은 것 — 카탈로그 표시 누락

`text.classify` 가 단계 5 에서 구현됐는데 **카탈로그의 「구현됨」 표시가 빠져 있었다.**
실물(`tiny_text.py` · 가중치 · 데모)은 다 있었다. 그래서 원고를 쓰려고 세어 보니 4 였고,
실제로는 **5** 였다. 표시를 채웠다.

### 다음에 어긋나지 않게

`test_report_claims` — 원고가 이름을 부른 능력이 **카탈로그에서 구현됨인가** ·
「5종」과 실제 개수가 **같은가** · 「넷은 품질을 주장하지 않는다」가 **사실인가** ·
원고가 부른 **데모가 실재하는가** · **`.ps1` 을 약속하지 않았는가**.

변이 검사: 능력을 하나 더 구현 표시하면 **원고 갱신이 강제된다**. 데모를 지우거나
한계 문구를 빼도 걸린다 (3/3).

### 실측

`run_tests` 201 → **207** · `check_submission` **24/24** · 골든 수치 대조 통과
(새 능력들의 정확도를 원고에 **적지 않았다** — 적었으면 여기서 걸렸을 것이다).

## 촬영 문서 드리프트 정정 — 내가 늘린 숫자를 문서가 못 따라왔다 — 2026-08-16

**출품 트랙. 코드 변경 0 · DDL 0.** 실행기를 넷 얹는 동안 문서가 뒤처져 있었다.

| 어디 | 표기 | 실제 |
|---|---|---|
| README `logs migrate` 예상 출력 | 「17개 적용」 | **18개** |
| README 재현 확인 문구 | 세대 17 · `0001`–`0017` | **세대 18 · `0001`–`0018`** |
| 런북 `logs migrate` · `migrate status` | 17 | **18** |
| 런북 촬영 전 점검 | 단위 **68** · 출품 점검 **21** | **191** · **24** |
| 런북 실측 기준 | `ec9db6b` (08-15) | **`b1cecc5` (08-16)** |

**README 쪽이 더 급했다.** 심사위원이 첫 화면에서 그대로 따라 하는 값이다 —
「18개 적용」이 나오는데 문서가 17이라고 하면 거기서 멈춘다.

### 자라는 값을 「같아야 하는 값」으로 적지 않는다

검사 수는 실행기를 얹을 때마다 는다(68 → 191). 그걸 표에 못박아 두면 다음 사람이
**숫자만 고치게** 된다 — 검사가 일을 시키는 꼴이다.

그래서 런북에 **「숫자가 달라도 그 자체는 이상이 아니다」**를 적고, 대신 **무엇이 유지돼야
하는지**(`clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500`)를 못박았다.

**마이그레이션 세대는 반대로 정확히 고정했다** — 그건 눈으로 대조하는 값이라
어긋나면 바로 혼란이 된다. `test_shoot_docs` 가 파일 수와 문서 표기를 대조한다.

### 촬영에 **넣지 않는 것**을 적었다

`text_demo` · `embed_demo` · `series_demo` · `image_embed_demo` 넷은 촬영에 넣지 않는다.
이유 셋: ① 3분에 안 들어간다 ② 전부 `.sh` 라 PowerShell 판이 없다
③ **품질을 주장하지 않는 능력들**이라 화면에 띄우면 성능을 본 것으로 읽힌다.

근거 ②③ 이 실물과 맞는지도 검사로 고정했다 — `.ps1` 이 생기거나 데모가 한계 문구를
빼면 런북이 거짓이 되므로 그때 실패한다.

### 재확인 실측 (`main` = `b1cecc5`)

`run_tests` **191** · `check_submission` **24/24** · `clean_room` **9/9** ·
`prod_room` **27/27** · 마이그레이션 **18개 적용 · 체크섬 일치** ·
골든 `acc=0.8500` `f1=0.8344` · 패키지 **2.2 MB / 상한 50 MB**.

### 변이 검사

**마이그레이션을 하나 늘리자 4건이 실패했다** — 다음에 DDL 을 추가하면 문서 정정이
강제된다. 런북의 「자라는 값」 문구를 지우거나 데모의 한계 문구를 빼도 걸린다 (3/3).

## image.embed — 이미지가 structured 를 낸다 · 새 가중치 0 (단계 6 ③) — 2026-08-16

**DDL 0 · 새 의존성 0 · 새 가중치 0 · 새 학습 0 · `image.classify@1` 무회귀.**

그동안 **이미지 모달리티는 `closed_set_labels` 만** 냈다. 「이미지 × structured」는
검증된 적이 없는 조합이고, 미검증 조합에서 형판이 깨지는 것을 이미 두 번 봤다
(출력 이름 · 로더). 이번에도 하나 나왔다.

### 계약 게이트가 통과할 Agent 를 떨어뜨렸다

게이트의 `arch` 검사가 `load_state_dict` 를 그대로 불러 **분류기 머리 텐서에서 실패**했다.
실행기는 트렁크만 거르는데 게이트는 그걸 몰랐다 — **검증과 실행이 갈린 것**이다.
같은 로더를 쓰게 고쳤다.

### 새 가중치를 만들지 않았다

`eurosat_scratch.safetensors` 가 이미 있고, 임베딩은 그 파일의 **앞부분**이다.
새로 학습할 것도 커밋할 것도 없다 — 「기존 자산 재사용」이 실제로 무엇인지 보이는 사례이며,
**패키지가 커지지 않는다**(현재 2.2MB / 상한 50MB).

### `strict=False` 를 쓰지 않았다

머리를 버려야 하니 손쉬운 길이지만, 그러면 **트렁크 키가 하나 빠져도 조용히 통과한다** —
랜덤 초기화 층으로 추론하면서 벡터는 그럴듯하게 나온다. 키를 명시적으로 걸러 내고
기대한 키가 전부 있는지 확인한 뒤 strict 로 넣는다.

### 전처리를 분류와 공유한다

`load_image_tensor` 를 뽑아 분류·임베딩이 **같은 함수**를 쓴다(D3). 픽셀 상한도 그 안에
있다 — 임베딩만 상한이 없으면 그쪽으로 큰 이미지가 들어온다.

### 지문 경고는 정상이다

`shape 합계(94538) ≠ 로드 후 파라미터(93248)` — 파일에 분류기 머리가 있고 트렁크만
로드했기 때문이다. **그 차이가 증적에 남는다.**

### 실측

`run_tests` 177 → **191** (변이 3/3) · `clean_room` **9/9** · `prod_room` **27/27** ·
`acc=0.8500` 불변 · text·embed·series 데모 **전부 무회귀**.

## timeseries.forecast — 세 번째 모달리티 어휘 (단계 6 ②) — 2026-08-16

**DDL 0 · 새 의존성 0 · 새 외부 데이터 0 · `image.classify@1` 무회귀.**

텍스트·이미지가 아닌 입력이 **같은 계약 형판**(선언 → 러너가 적용 → 실추론 → 출력 대조)으로
도는지를 이 능력이 보였다. 형판이 두 모달리티에만 맞춰져 있었다면 여기서 드러났을 것이다.

### 출력 이름을 Node 가 정하고 있었다

계약은 `forecast` 를 요구하는데 증적에는 `vector` 가 남았다 — **게이트가 검증한 출력과
증적에 남는 출력이 갈라진 것**이다. 「승인한 것과 실행한 것이 같다」가 깨지는 자리다.

Core 가 `capability.output_schema` 의 `required` 첫 항목을 읽어 붙이게 고쳤다.
**Node 는 값만 보내고 이름은 주장하지 못한다** — 등급을 주장하지 못하는 것과 같은 규율이다.

### 표본이 모자라면 던진다

0 으로 채우면 모델이 **없는 과거**를 본 것이 된다. 터지지 않고 **조용히 틀린 예측**이
나오는 종류라, 채우지 않고 거절한다.

`window` 를 계약에 둔 것도 같은 이유다 — 모델이 보는 과거 길이가 바뀌면 같은 가중치가
다른 것을 본다. 러너가 그대로 셀 수 있는 값이라 계약이 검증할 수 있다.

### 학습 데이터는 규칙 생성

추세 + 계절성 + 잡음. 외부 데이터가 0 이라 절대규칙 6 과 2차 라이선스 검증에 얹을 것이 없다.
홀드아웃 MSE 와 **「마지막 값 반복」 기준선**을 함께 남겼다 — 숫자 하나만 있으면
좋은지 나쁜지 알 수 없다. **실제 시계열 성능은 주장하지 않는다**(`quality_profile='none'`).

### 종단 실측

```text
OK   preprocess — 선언 적용: encoding=utf-8 max_rows=10000 window=24
OK   input_schema — 선언 전처리로 샘플 추론 성공 (280 bytes · series)
OK   output_schema — 배열 4개가 계약을 만족한다
gate_run PASSED → 작업 COMPLETED · forecast=[3.624, 5.161, 5.987, 5.739]
```

`text.classify` · `text.embed` 데모도 함께 돌려 무회귀를 확인했다.

### 실측

`run_tests` 159 → **177** (변이 3/3) · `clean_room` **9/9** · `prod_room` **27/27** ·
`acc=0.8500` 불변.

## text.embed — structured 출력이 사슬을 탄다 (단계 6 ①) — 2026-08-16

**DDL 0 · 새 의존성 0 · 새 학습 데이터 0 · `image.classify@1` 무회귀.**

`text.classify` 와 **같은 특징 추출·전처리**를 쓴다(두 벌을 만들지 않는다 · D3).
다른 것은 출력이다 — 라벨이 아니라 **64차원 벡터**.

### D-out 이 실제로 무는 것을 이 능력이 보였다

계약 게이트가 `output_schema — **벡터 64차원이 계약을 만족한다**` 로 통과했다.
**전에는 차원이 틀려도 통과했다.** `structured` 첫 사례를 고른 이유가 이것이었다 —
임베딩 계약은 「차원이 맞는가·수치인가」가 전부라, 검증이 도는지가 한 능력으로 드러난다.

**곁다리로 D-maxp 도 보였다.** 이 사영은 262,144 파라미터라, 상한을 100,000 으로
등록했을 때 게이트가 `max_params` 에서 떨어졌다. 그리고 D-arch 에 갱신 경로가 없으므로
빈 볼륨에서 다시 등록해야 했다 — **셋 다 설계대로 물었다.**

### 라벨 칸을 지어내지 않는다

임베딩 결과 증적에 `label` 키가 **아예 없다.** 빈 문자열로 채우면
「라벨이 있었다」고 거짓말한다. 대신 **`label`·`vector` 가 둘 다 비면 Core 가 거절**한다 —
아무것도 안 낸 실행이 COMPLETED 로 기록되면 안 된다(dummy 는 예외, 그쪽은 이미 증적에 남는다).

### 의미적 유사도를 주장하지 않는다

이 사영은 라벨로 학습한 것이 아니라 **고정 시드 초기화**다. 같은 입력이 같은 벡터를,
다른 입력이 다른 벡터를 낸다 — 그 이상은 말하지 않는다.
「임베딩이니까 검색이 잘 된다」로 읽히지 않게 meta·소스·카탈로그에 같은 문장을 적었다.

### 실행 중에 잡은 버그 둘

1. **`label` 미초기화** — 임베딩 분기는 `label`·`confidence` 를 채우지 않는데 결과 보고가
   그 이름을 무조건 읽었다. `cannot access local variable 'label'` 로 **배정이 전부 FAILED**
   가 됐다. 초기화를 앞으로 올리고 검사로 고정했다
2. **`CompleteBody.label: str`** — 라벨이 없으면 Core 가 422 로 거절했다. 선택으로 바꾸고
   `vector` 를 받게 했다. **동시에** 「둘 다 비면 거절」을 넣어 구멍을 만들지 않았다

둘 다 격리 스택에서 실행해 보고서야 드러났다. 단위 검사만으로는 안 보였을 종류다.

### 실측

`run_tests` 147 → **159** (변이 3/3) · `clean_room` **9/9** · `prod_room` **27/27** ·
`acc=0.8500` 불변 · 텍스트 데모 무회귀(`label=url`).

## 작업 접수 — 거짓말을 시키던 관문을 닫았다 (D8′ · Decision A) — 2026-08-16

**DDL 0 · 새 의존성 0 · 데모 경로 무회귀.** 바뀐 것은 조건 한 줄이다.

`POST /v1/tasks` 가 `datasetId` 를 **무조건** allowlist 와 대조했다. 텍스트 작업에는 맞는
값이 없어서, 통과시키려면 `eurosat-rgb` 를 적어야 했다 — **증적에 없던 데이터셋이 남는다.**
「내 데이터가 어디로 갔는지 답한다」가 제품 주장인데 그 답을 거짓으로 만드는 관문이었다.

### 왜 건너뛰어도 되는가

allowlist 는 **비통제 수집**을 막으려고 있다(D8′). `inputId` 가 있으면 바이트는 이미
Core 를 거쳐 왔고, **수집 시점에 능력에 묶였으며**(`task_input.capability_id` 복합 FK)
해시·크기·MIME 이 계약과 대조됐다. 그 경로에서 datasetId 를 다시 묻는 것은
통제를 더하지 않는다 — **거짓말을 시킬 뿐이다.**

### 무엇을 안 건드렸나

**바이트를 받는 문(`POST /v1/inputs`)** — 계약·해시·크기·MIME 대조 그대로.
「자유 업로드 경로를 만들지 않는다」(절대규칙 7)는 유지된다. 건너뛴 것은
**작업 접수의 datasetId 대조** 하나뿐이고, 그것도 `inputId` 가 있을 때만이다.

### 실측 (격리 스택)

| 요청 | 결과 |
|---|---|
| `inputId` 없음 + allowlist 밖 | **400** — 종전대로 막힌다 |
| `inputId` 없음 + `eurosat-rgb` | 200 — 데모 경로 무회귀 |
| 없는 `inputId` | **404** — 건너뛰기가 무검증이 아니다 |
| `inputId` 있음 + `text-demo` | **200 → COMPLETED** |

### 텍스트가 완주했다

```text
label= url  confidence= 0.3115…
증적: assignment=… node=…-030 agent=… status=SUCCEEDED
경계: 신뢰도메인 task=team -> node=team · 티어 capability=M <= node_max=M
```

단계 5 에서 계약 게이트까지 갔던 경로가 **작업 완주까지** 이어졌다.
정확도는 주장하지 않는다 — `quality_profile='none'` 이다.

### 실측

`run_tests` 141 → **147** · `clean_room` **9/9** · `prod_room` **27/27** · `acc=0.8500` 불변.

## structured 출력 검증 — 통과하던 넷이 떨어진다 (D-out) — 2026-08-16

**새 의존성 0 · DDL 0 · 계약 형식 변경 0 · `closed_set` 판정 무회귀.**

전에는 스칼라만 봤다. 카탈로그 52 중 **26개**가 `structured` 인데, 그쪽 출력은
계약 게이트가 사실상 아무것도 확인하지 않았다. 실측으로 통과하던 넷이 이제 떨어진다:

| 출력 | 이전 | 지금 |
|---|---|---|
| `{"vector":[0.1]}` (`minItems:3`) | 통과 | **거절** — `vector 원소 1개 < minItems 3` |
| `{"vector":"not-a-vector"}` | 통과 | **거절** — `vector 는 array 이어야 한다` |
| `{"vector":[0.1,"x",0.3]}` | 통과 | **거절** — `vector[1] 는 number 이어야 한다` |
| `{"boxes":[{"x":"a"}]}` | 통과 | **거절** — `required 누락: boxes[0].y` |

### 사유에 **경로**를 넣었다

`structured` 는 중첩이라 「어디가 틀렸는지」가 없으면 제출자가 고칠 수 없다.
`boxes[0].h` 처럼 짚어 준다.

### `bool` 을 number 로 통과시키지 않는다

파이썬에서 `bool` 은 `int` 의 하위형이다. 먼저 거르지 않으면 `{"confidence": True}` 가
`type: number` · `minimum:0` · `maximum:1` 을 **전부 만족한다.** 조용히 지나갈 종류라 검사에 박았다.

### 모르는 어휘를 아는 척하지 않는다

`$ref` · `oneOf` · `pattern` · `format` 은 지금 어느 계약도 쓰지 않는다.
반쯤 구현해 두면 「검사했다」로 읽히므로 **통과시키되 그 사실을 문서에 적었다.**
쓰기 시작하면 그때 넓힌다.

### 왜 지금이었나

`structured` 로 라우팅되는 능력이 **하나도 없었다.** 즉 떨어질 대상이 0 이라
제약을 넓히기 가장 싼 시점이었다. `image.classify`·`text.classify`(둘 다 closed_set)의
판정은 바뀌지 않는다 — 검사 6종으로 고정했다.

### 실측

`run_tests` 123 → **141** (변이 3/3) · `clean_room` **9/9** · `prod_room` **27/27** ·
`acc=0.8500` 불변.

## 단계 6 준비 — 실행기를 더 얹기 전에 (문서) — 2026-08-15

**문서만. 구현 0 · 코드 0 · DDL 0.** 허용 범위(「단계 6 준비 문서/Proposal만」) 안이다.

### `structured` 출력이 계약 게이트에서 검증되지 않는다 (실측)

`check_output_schema` 는 배열·중첩 객체 내부를 보지 않는다. 네 가지 위반이 전부 통과했다 —
차원이 틀린 벡터, 배열이 아닌 값, 구조가 없는 박스 목록.

**카탈로그 52 중 26개가 `structured`** 다. 그쪽 실행기를 얹으면 게이트가
「계약을 만족한다」고 적을 근거가 없다.

**지금까지의 주장은 참이었다.** 라우팅되는 능력이 `image.classify`·`text.classify`
(둘 다 closed_set)뿐이라 `enum` 검사가 실제로 동작했다. 구멍은 **아직 쓰지 않은 영역**에 있고,
그래서 지금이 고치기 가장 싼 시점이다 — **떨어질 대상이 0 이다.**

### 학습 데이터 라이선스로 카테고리를 나눴다

단계 5 에서 과제를 고른 기준(「규칙으로 생성 가능한가」)을 나머지에 적용했다.
**「새 데이터 필요」(audio·mm·image.detect/segment/ocr)는 대회 트랙 밖**으로 뒀다 —
2차 라이선스 검증이 있고, 데이터 하나를 잘못 들이면 그 검증이 통째로 흔들린다.

### 두 번째 실행기부터 싸진다

실행기 하나에 드는 9단계를 단계 5 실측으로 적었다. 3~7(arch 등록·실행기·게이트 분기·
실행 분기)은 이제 형판이 있어 한 줄씩 늘리면 된다. 남는 일은 특징 추출·학습·데모·검사다.

### 추천 순서

① `structured` 출력 검증 → ② 작업 접수(Decision 대기) → ③ **`text.embed`**.
셋째를 고른 이유는 성능이 아니라 **검증 가능성**이다 — 임베딩은 「차원이 맞는가·수치인가」가
계약의 전부라, 첫 항목이 실제로 도는지가 그 하나로 드러난다. 새 데이터도 필요 없다.

## text.classify 실행기 — 이미지가 아닌 모달리티가 사슬을 탄다 (단계 5) — 2026-08-15

**DDL 0 · 새 의존성 0 · `image.classify@1` 무회귀 · 한 PR 에 52 런타임 없음.**

### 실행기는 `arch` 로 갈린다

전처리 어휘로도 짐작할 수 있지만(`is_text_preprocess`), 정본은 **`ARCH_MODALITY`** 다.
`arch` 는 Core 가 말한 값이고 **게이트가 그 값으로 승인했다** — 「승인한 것과 실행한 것이
같다」를 지키려면 그쪽으로 갈라야 한다 (I1).

**텍스트에는 `caseId` → 로컬 골든 폴백이 없다.** 입력은 Core 중개로만 온다 (D8′).
이미지 데모 경로는 그대로 남는다.

### 학습 데이터를 **생성**했다

과제는 짧은 문자열의 **구조** 6종(`email`·`url`·`ipv4`·`uuid`·`iso_date`·`plain`)이다.
감정 분석·주제 분류였다면 남의 말뭉치가 필요했다 — **규칙으로 만들 수 있는 과제**를 골라서
외부 데이터가 0 이고, 절대규칙 6 과 2차 라이선스 검증에 새로 얹을 것이 없다.
쓸모없는 과제도 아니다: 「이 필드가 이메일인가 IP 인가」는 문서 라우팅·PII 선별의 앞단이다.

모델은 해시 문자 n-gram 가방 → `Linear`, **24,582 파라미터**. 은닉층을 두지 않은 것은
의도다 — 여기서 보이려는 것은 **경로**이지 모델이 아니다.

**품질을 주장하지 않는다.** `text.classify` 는 `quality_profile='none'` 이라 골든셋도
채점도 없다. 홀드아웃 정확도는 `.meta.json` 에만 남기고 제품 문구로 쓰지 않는다
(SD-008 의 교훈과 같은 규율).

### `hash()` 를 쓰면 학습한 모델을 다음 실행에서 못 쓴다

파이썬 문자열 해시는 `PYTHONHASHSEED` 로 **실행마다 달라진다.** 특징 버킷이 바뀌므로
같은 가중치가 다른 입력을 보게 되고, **터지지 않고 정확도만 조용히 떨어진다.**
`blake2b` 로 고정하고, 버킷 값을 **기준값으로 못박았다.**

### 검사가 설명을 잡는 사고 — **네 번째**. 이번엔 한 곳으로 모았다

`assertNotIn("hash(", …)` 가 「`hash()` 를 쓰지 않는다」는 **docstring** 을 잡았다.
`localStorage`(#74) · `NOT VALID`(`0018`) · `ON CONFLICT`(`arch.py`)에 이어 네 번째다.

매번 그 자리에서 고치면 다섯 번째가 온다. **`tests/_srcguard.py` 로 뽑았다** —
`ast` 로 주석과 docstring 만 비운다(삼중따옴표를 통째로 지우면 SQL 리터럴까지 사라진다).
그 네 번의 이력을 헬퍼 문서에 적어 뒀다.

### 변이 검사가 또 자기 자신을 잡았다

처음 쓴 「`PYTHONHASHSEED` 를 바꿔 하위 프로세스로 확인」 검사가 **변이를 넣어도 통과**했다 —
하위 프로세스가 낡은 `__pycache__` 를 집었기 때문이다. **불안정한 가드는 없느니만 못하다.**
기준값 고정으로 바꾸고 하네스가 캐시를 지우게 했다. 그 뒤 변이 **3/3** 잡힌다.

### 종단 실측 — 계약 게이트까지

```text
OK   weights_fingerprint — 텐서 2개 · 파라미터 24582
OK   arch — TinyTextClassifier 로 로드 성공
OK   max_params — 24582 <= 100000
OK   preprocess — 선언 적용: encoding=utf-8 normalize=NFC max_chars=8000
OK   input_schema — 선언 전처리로 샘플 추론 성공 (27 bytes · text)
OK   output_schema — label='email' 이 계약을 만족한다
gate_run PASSED → 바인딩 완료
```

### ⚠️ 작업 접수 한 칸이 막혀 있다

`POST /v1/tasks` 가 `datasetId` 를 **무조건** allowlist 와 대조한다
(`ALLOWED_DATASET_IDS = {"eurosat-rgb"}`). 텍스트 작업에는 맞는 값이 없다.
`eurosat-rgb` 를 적으면 통과하지만 **증적에 거짓 데이터셋이 남는다** — 그래서 안 했다.

D8′ 는 allowlist 를 「보조 경로」로 남긴다고 했는데 코드는 아직 **필수**다.
Core 중개 입력이 있으면 바이트가 이미 계약에 묶여 있고 해시·크기·MIME 도 검증됐으므로
그 경우 대조는 뜻이 없다. **정책이라 임의로 바꾸지 않았다.**

### 실측

`run_tests` 107 → **123** · `clean_room` **9/9** · `prod_room` **27/27** · `acc=0.8500` 불변.

## arch 등록 API · 비참조 파라미터 상한 (D-arch · D-maxp) — 2026-08-15

**DDL 0.** 두 Decision 을 함께 구현했다 — 하나가 없으면 다른 하나가 반쪽이기 때문이다.

### D-arch — 막는 문은 있는데 여는 문이 없었다

`agent.arch` 는 `agent_arch` 를 FK 로 참조한다(`0008` · I1). 없는 arch 로는 Agent 등록이
막히고 **그건 설계대로다.** 그런데 그 행을 넣는 경로가 없어서, 새 모달리티를 붙이려면
운영자가 DB 에 직접 INSERT 해야 했다 — 제품 경로가 아니다.

| | |
|---|---|
| `GET /v1/arches` | 목록 · **developer 이상** (어떤 구조를 받는가는 운영 정보다) |
| `POST /v1/arches` | **추가만** · **admin** |

**갱신·삭제를 만들지 않은 것이 설계다.** `max_params` 는 계약 게이트의 상한이라 사후에
올리면 **이미 통과한 증서의 근거가 바뀐다**(D15) — 증적이 「그때 무엇을 기준으로
통과했는가」를 답하지 못하게 된다. 상한을 바꿔야 하면 **새 arch 이름**으로 등록한다.

**중복을 조용히 넘기지도 않는다.** `ON CONFLICT DO NOTHING` 이면 다른 상한으로 다시 등록한
운영자가 **성공했다고 믿고 옛 값을 쓴다.** 409 로 지금 값을 함께 알려 준다.

### D-maxp — 비참조 모델에는 상한이 **아예 없었다**

C2 를 넣을 때 `max_params` 를 참조 구현 쪽에 뒀다. 그래서 비참조 arch 는 파라미터 상한
없이 통과했다. 그런데 **지문의 shape 합계로 셀 수 있으므로** 「실행해야만 알 수 있는 값」이
아니었다 — 공통 검사로 올렸다.

`CONTRACT_CHECKS_COMMON` 5종(+`max_params`) · `CONTRACT_CHECKS_REFERENCE` 1종(`arch`).

`MAX_PARAMS_DEFAULT` 도 `infer.py`(최상단 `import torch`)에서 `app/limits.py` 로 꺼냈다 —
`preprocess` 때와 같은 이유다. **상한 정본은 `agent_arch.max_params`(DB 행)**이고 그 값은
기본값일 뿐이라는 것도 적어 뒀다.

### 종단 실측 (격리 스택)

| 시도 | 결과 |
|---|---|
| `POST /v1/arches` 신규 | **200** |
| 같은 이름 재등록 | **409** — 현재 `max_params` 를 함께 알려 준다 |
| `arch="Tiny Model;DROP"` | **400** |
| `max_params=0` | **400** (`agent_arch_max_params_check`) |
| 비참조 · 상한 **50,000** · 모델 94,538 | **FAIL → gate_run FAILED → 바인딩 거부** |
| 비참조 · 상한 **200,000** | PASS → 바인딩 |
| 참조 `TinyEuroSAT` | **6종 전부** (샘플 실추론 포함) — 무회귀 |

다섯째 줄이 D-maxp 의 요점이다. **그 전에는 저 모델이 상한 없이 통과했다.**

### 변이 검사가 가드 구멍 둘을 찾았다

처음 쓴 검사는 변이 3종 중 **1종만** 잡았다.

1. **창이 다음 엔드포인트까지 넘쳤다.** `_require("admin")` 을 `developer` 로 바꿔도,
   고정 길이로 자른 창에 바로 뒤 `capabilities_create` 의 `_require("admin")` 이 들어와
   통과했다. 다음 `@app.` 앞까지만 자르게 고쳤다
2. **검사가 skip 되는 클래스에만 있었다.** `max_params` 를 공통 집합에서 빼는 변이는
   `psycopg` 없는 환경에서 **아무 검사에도 안 걸렸다.** 소스로 보는 가드를 따로 추가했다

고친 뒤 **3/3 전부** 잡힌다.

### 검사가 설명을 잡는 사고 — 세 번째

`assertNotIn("ON CONFLICT", …)` 가 「`ON CONFLICT DO NOTHING` 으로 넘기지 않는다」는
**docstring** 을 잡았다. `localStorage`(#74) · `NOT VALID`(`0018`)에 이은 세 번째다.

이번엔 `ast` 로 **docstring 만** 걷어냈다 — 삼중따옴표를 통째로 지우면 SQL 리터럴까지
사라져 `UPDATE`·`DELETE` 검사가 무력해진다.

### 실측

`run_tests` 95 → **107** · `clean_room` **9/9** · `prod_room` **27/27** · `acc=0.8500` 불변.

### 남은 것

**`max_params` 자체의 상한이 없다.** admin 이 `10^18` 로 등록하면 사실상 무제한이다.
**정책 숫자이므로 임의로 정하지 않았다** — Decision 이 필요하다.

## C2 가중치 지문 — 계약 게이트가 이미지를 벗어났다 (단계 4) — 2026-08-15

Decision 2-C. **DDL 0.** `text.summarize` 같은 능력은 계약 게이트를 통과할 **방법이 없었다** —
`CONTRACT_CHECKS` 5종이 전부 이미지·torch 전용이었기 때문이다.

### 원칙이 어디까지 성립하는지 먼저 적는다

B2 가 세운 **「계약을 말로 받지 않는다 — 러너가 실행해서 판정한다」**는
**우리 코드가 그 모달리티를 실행할 수 있을 때만** 성립한다. `text.generate` 를 실행하려면
제출자의 코드가 필요하고, 그건 절대규칙 5 와 유통 세대에 정면으로 닿는다.

그래서 필수 검사를 **arch 로 갈랐다**:

| 집합 | 항목 | 언제 |
|---|---|---|
| 공통 4 | `input_schema` · `output_schema` · `preprocess` · **`weights_fingerprint`** | 항상 |
| 참조 +2 | `arch` · `max_params` | `REFERENCE_ARCHS` 에 있을 때 |

### 지문은 파일을 **열되 실행하지 않는다**

safetensors 는 맨 앞 8바이트가 헤더 길이이고 그다음이 JSON 헤더다. **그 JSON 만 읽는다.**
torch 도 safetensors 라이브러리도 쓰지 않는다 — `s-public` Node 에는 **torch 가 없고**
(`Dockerfile` 이 조건부 설치), 10GB 가중치여도 헤더는 수십 KB 이며, JSON 파싱과 정수 읽기뿐이라
**역직렬화가 아니다**(절대규칙 5 가 pickle 을 막는 이유가 여기서도 지켜진다).

실측: `eurosat_scratch` 텐서 8개 · **94,538** 파라미터 — `0008` 이 적어 둔 「TinyEuroSAT ~93k」와 맞는다.
`eurosat_scratch_b` 23개 · 24,685 · `placeholder` 1개 · 1. **셋의 지문이 전부 다르다.**

### 「검사 안 했다」를 `false` 로 적지 않는다

비참조 경로는 `arch`·`max_params` 를 **아예 보고하지 않는다.** `false` 로 보내면
「검사했는데 떨어졌다」로 읽히기 때문이다. 없는 것이 정직한 표현이고, Core 도 요구하지 않는다.

한계는 **증적에 남긴다** — `_notes._limits` 에 「지문은 «그 파일이 그 구조다»까지만 말하며
«계약대로 동작한다»는 보장하지 않는다」. 통과 사실만 보고 동작 보장으로 읽지 않게.

### 종단 실측 — 이미지 밖 능력이 처음으로 통과했다

격리 스택에 `text.classify@1`(`quality_profile='none'`)을 등록하고 계약 게이트를 끝까지 돌렸다.

| arch | 결과 |
|---|---|
| `TinyTextCNN` (비참조) | 공통 4종 통과 → `gate_run PASSED` → 바인딩 |
| `TinyEuroSAT` (참조) | 6종 전부 — `arch` 로드 · `max_params` 94538≤2000000 · **샘플 실추론** `label='annual_crop'` |

**전자가 이번 작업의 요점이다.** 그동안 불가능했던 경로다.

### 새 모달리티에는 `agent_arch` 행이 먼저 필요하다 (남은 구멍)

비참조 arch 로 Agent 를 등록하려다 **HTTP 400** 을 받았다 —
`unknown arch 'TinyTextCNN' — agent_arch 에 없는 아키텍처다`. FK 가 막은 것이고 **설계대로다.**
다만 **`agent_arch` 에 행을 넣는 API 가 없다.** 52개로 넓히려면 그 등록 경로가 필요하고,
아무나 arch 를 늘리면 allowlist 가 무의미해지므로 **별 Decision** 이다.

### 전처리 해석을 torch 밖으로 꺼냈다

`resolve_preprocess` 가 `infer.py` 에 있었는데 그 파일은 최상단에서 `import torch` 를 한다.
그대로 두면 「torch 없는 Node 에서도 돈다」가 거짓이 된다. `app/preprocess.py` 로 옮기고
`infer.py` 는 다시 내보낸다.

### 테스트가 **혼자 돌면 통과하고 전체로 돌면 깨졌다**

`apps/node` 와 `apps/core` 는 **둘 다 `app` 패키지**를 갖는다. sys.path 에 올려 두는 방식이라
다른 테스트 모듈이 core 를 먼저 꽂으면 node import 가 조용히 core 로 갔다.
검사가 도는 **동안만** 경로를 바꾸고 `tearDown` 에서 되돌리게 고쳤다 —
import 직후에 되돌리면 안 된다(러너가 **호출 시점에** 지연 import 를 한다).
단독·역순·전체 세 가지로 확인했다.

`safetensors` 문자열 검사가 또 **문서 문구**를 잡을 뻔했다 — import 문만 보게 고쳤다.

### 실측

`run_tests` 79 → **95** · `clean_room` **9/9** · `prod_room` **27/27** · 골든 `acc=0.8500` 불변.
통합 검사(`run_integration.sh`)는 **이 호스트에서 못 돌렸다** — `psql`·`psycopg` 가 없다. CI 몫이다.

## 능력 카탈로그 52 — 계약 표면 · freeform 골든 금지 — 2026-08-15

Decision 2 의 단계 1–3. **이미지 분류 하나만 도는 것은 제품이 아니다**는 지시를 표면부터 넓혔다.

### 카탈로그는 병목이 아니었다

먼저 확인한 사실 — **52개 「등록」은 지금도 된다. DDL 이 필요 없다.** D20(`0010`)이
`output_kind` 3종과 `quality_profile='none'` + 센티널을 이미 깔아 뒀기 때문이다.

**막히는 곳은 라우팅이다.** 계약 게이트가 이미지·torch 전용이라(`ARCH_REGISTRY` 는
`TinyEuroSAT`·`TinyEuroSATB` 둘뿐, `preprocess` 어휘는 `{resize, colorspace}`,
`input_schema` 검사는 `predict_image` 실추론) `text.summarize` 는 게이트를 통과할 방법이 없다.
그건 단계 4 에서 다룬다. 이번 PR 은 **표면과 규율**이다.

### 잴 수 없는 것에 점수를 붙일 수 있었다

`ck_capability_mvp_scoreable` 은 **`mvp_eligible` 만** 묶는다. 그래서
`output_kind='freeform'` + `quality_profile='golden'` 이 **DB 에서도 앱에서도 통과했다.**
요약 능력에 골든셋 40건과 `min_accuracy` 를 달고 「품질 하한을 보장한다」고 쓸 수 있었다는 뜻이다.

**골든셋의 알려진 세 구멍과는 다른 종류의 문제다.** 그 셋(표본·분포·게이밍)은
「측정이 약하다」이고, 이건 **「측정이 아예 없는데 있는 척한다」**이다. 요약문은 맞다/틀리다로
갈리지 않으므로 골든셋 정의서 §6 의 채점 규칙이 애초에 성립하지 않는다.

`0018` 이 `ck_capability_golden_scoreable` 을 **추가**한다(절대규칙 1 — 추가만).
**`structured` 는 막지 않는다** — 임베딩·검출·랭킹은 원리적으로 잴 수 있다(코사인·IoU·nDCG).
채점기가 없다는 것과 못 잰다는 것은 다르다.

DB 실측:

| 시도 | 결과 |
|---|---|
| `freeform` + `golden` | **REJECTED** — `ck_capability_golden_scoreable` |
| `structured` + `golden` | **통과** (막힌 것이 freeform 뿐임을 확인) |

### 산출물이 실행되는 셋은 격리 전에 열지 않는다

`code.generate` · `tool.plan` · `tool.action` — 모델이 위험한 게 아니라 **출력의 용도**가 그렇다.
격리 없이 열면 실행이 Node 밖으로 나가므로 「승인 도메인 안에서만 돈다」가 무의미해진다.

**집행에 새 제약을 만들지 않았다.** `trust_domain_min='team'` 으로만 등록하면
`domain_compatible` 이 이미 tenant·public 배정을 막는다 — **있는 축을 쓴다.**

`code.complete`·`code.review` 는 잠그지 않았다. 산출물이 사람에게 보여지는 텍스트이고
자동 실행 경로가 없기 때문이다. 그 구분이 흐려지면 그때 다시 잠근다.

### AV 는 없다 — 있다고 쓰지 않는다

카탈로그 §7 에 **「바이러스 검사(AV)는 없다」**를 박고, 있는 것(safetensors 봉쇄 ·
`weights_sha256` 바인딩 · placeholder 감지 · 입력 MIME/크기/해시)만 나열했다.
`safety.malware_hint` 능력이 카탈로그에 있는 것은 **AV 가 있다는 뜻이 아니다** — 그건
사용자가 호출하는 능력이지 플랫폼의 통제가 아니다.

### 토크나이저를 계약에 넣지 않았다

텍스트 `preprocess` 에서 `max_tokens` 를 쓰고 싶어지지만 넣지 않았다. 토큰화는 모델마다
다르고, **계약이 검증할 수 없는 값을 계약에 적으면 「선언은 있는데 아무도 확인 안 하는 칸」**이
된다 — `preprocess` 가 `0013` 에서 정확히 그 상태였고 그래서 필수 검사에서 빠졌었다.
길이는 러너가 그대로 셀 수 있는 `max_chars` 로 선언한다.

### 검사가 또 주석을 잡을 뻔했다

`assertNotIn("NOT VALID", …)` 가 「NOT VALID 로 우회하지 않는다」라고 적어 둔 **주석**을 잡았다.
`test_ui_invariants` 에서 겪은 것과 같은 모양이라 `strip_sql_comments` 로 고쳤다.

**반대 방향도 났다.** 앱 소스 가드가 「왜 막는지」 설명한 **주석에 만족해**, 정작 `raise` 를
지워도 통과했다 — 변이 검사에서 드러났다. 주석을 걷어내고 `output_kind == "freeform"` 분기
자체를 보게 고쳤다. **변이 4종 전부 잡히는 것을 확인했다.**

### 실측

`run_tests` 68 → **79** · `clean_room` **9/9** · `prod_room` **27/27** ·
마이그레이션 **18개 적용 · 체크섬 일치** · 골든 `acc=0.8500` 불변.

## A/B 자막 확정 · README 재실행 함정 — 2026-08-15

Decision 1(안 **B**)과 ack 를 그대로 구현했다. **코드 변경 0.**

### 빼면 안 되는 줄을 「뺄 수 없게」 적었다

A/B 구간 자막은 두 줄이다:

> 같은 능력으로 **다른 에이전트에 교체 배정**됩니다. 계약을 통과한 것만 후보가 됩니다.
> 다만 **두 에이전트가 같은 답을 낸다고는 말하지 않습니다.**

**둘째 줄이 핵심이다.** 빼면 첫 줄이 곧바로 등가 주장으로 읽힌다 — 그리고 3분 영상 편집에서
가장 먼저 잘려 나갈 후보가 정확히 저런 단서 줄이다. 그래서 런북에
**「시간이 모자라면 구간 전체를 들어내지, 둘째 줄만 지우지 않는다」**를 명시했다.

**점수 숫자를 화면에 띄우지 않는다**도 넣었다. 자막이 무엇을 말하든 숫자 두 개가 뜨면
시청자는 비교한다 — 자막으로 막을 수 있는 종류의 오해가 아니다.

금지 문구는 표로 못박았다: 「Within」·「편차 0.05 이내」·「|Δacc|≈0.047」·「n300 |diff|≤0.05」·
「같은 답」·「대체 가능」. 앞의 넷은 **누출된 골든셋**으로 잰 값이고(홀드아웃 재측정은
0.0967 · EXCEEDS), 뒤의 둘은 D17 이 계약 보장에서 내린 주장이다.

### README — 두 번째 실행이 첫 번째와 다르다

심사위원의 **첫** 실행은 안전하다. clone 직후엔 볼륨이 없기 때문이다. 문제는 2차 기능테스트
재실행이나 리뷰어의 두 번째 기동이다 — `docker compose down` 은 볼륨을 남기고, 그러면
initdb 가 **아예 돌지 않아** `migrate` 가 `0005` 에서 멈춘다.

실패 메시지가 「placeholder 가중치 Agent 에 라우팅 증서가…」라 **원인이 볼륨이라는 걸
알아채기 어렵다.** 그래서 메시지를 README 에 같이 적어 뒀다 — 검색해서 찾을 수 있게.

## 수용 게이트 실측 · 촬영 문서 정정 — 2026-08-15

#75·#76 이 머지된 `main` 에서 **Docker 로 실제 돌렸다.** 그리고 그 과정에서 촬영 문서가
오늘 실측과 어긋나 있는 칸을 넷 찾았다. 코드 변경은 **없다.**

### 실측 — `main` = `ec9db6b`

| 게이트 | 결과 |
|---|---|
| `run_tests` | **68/68** · `check_submission` 21/21 · 골든셋 sha 정합 OK |
| `clean_room` (빈 볼륨) | **9/9** |
| `prod_room` (강제 프로파일) | **27/27** |
| 골든 점수 | `acc=0.8500` `f1=0.8344` — 정본 일치 |

**#75 가 못 돌린 것을 여기서 갚았다.** 새로 붙인 「경계」 줄이 **데모·강제 두 모드 모두**에서
찍히는 것을 확인했다:

```text
경계: 신뢰도메인 task=team -> node=team · 티어 capability=M <= node_max=M
```

### 촬영 30분 전에 막힐 뻔했다

런북 §0 이 `docker compose down` 이었다. **`-v` 가 없다.** 그러면 볼륨이 남고, postgres 가
기존 데이터로 떠서 `initdb`(`schema.sql`+`seed.sql`)가 **아예 돌지 않는다.** 옛 볼륨의
placeholder 증서를 `0005` 가 잡아 마이그레이션이 멈춘다 — 오늘 Windows 에서 실제로 겪었다.

```text
실패 0005_seed_agent_not_routable.sql: placeholder 가중치 Agent 에 라우팅 증서가 아직 5 건 남아 있다
```

**가드가 옳다.** 통과시키면 dummy 라우팅이 되살아난다(SD-015). 고칠 것은 볼륨이었고,
런북에 `-v` 와 함께 **왜 그런지**를 적었다. 스토리보드는 이미 `down -v` 였다 — 런북만 뒤처져 있었다.

### 타임라인이 `bash` 와 PowerShell 을 섞고 있었다

촬영은 Windows 인데 45–75초와 150–160초가 `bash scripts/…` 였다. Windows 에 `bash` 는 없다.
`arch` 누락(G5)·`demo.ps1` finish 400(#76)과 **같은 종류**의 사고다.

45–75 는 `demo.ps1` 로 바꿨다. **150–160 은 못 바꾼다 — `proof_ab.ps1` 이 존재하지 않는다.**
`scripts/` 의 PowerShell 열 개를 세어 확인했고(`compare_ab.ps1` 은 사슬 **밖** 도구다),
그 칸만 **미리 녹화한 클립**으로 처리하도록 적었다. 촬영 중 WSL 전환은 안 한다.

### A/B 자막은 **반증된 수치**를 들고 있었다 — 쓰지 않는다

스토리보드 「실측 Within · n300 `|diff|≤0.05` · |Δacc|≈0.047」은 **누출된 골든셋으로 잰 값**이다
(골든셋이 학습셋 안에 있었다 — roadmap §1.2). 홀드아웃 n=300 재측정은 **0.0967 · EXCEEDS** 이고,
D17 이후 **등가성은 계약 보장이 아니라 관측값**이다.

그대로 촬영하면 **반증된 보장을 출품 영상에서 주장**하게 된다. 그래서 수치를 지우고
**「자막 미확정 · Decision 대기」**로 표시했다 — 문구를 내가 새로 짓지 않았다(제품 주장이다).
「A/B 교체가 된다」는 사실 자체는 사슬 위 실측이므로 촬영 가능하다고 남겼다.

### 자막에 한 문장 늘렸다

3번(「승인하지 않은 도메인은 DB 가 거절합니다」)은 **부정형**이다. 새 「경계」 줄은 같은 규칙이
**통과시킨 경우**를 보여 준다. 둘을 붙여야 「막기만 하는 게 아니라 판정한다」가 된다.

### 제출 양식의 낡은 근거 하나

붙임2 §4 가 「저장소 코드 5,054줄 중 390줄 ≈ 8%」를 근거로 들고 있었다. 2026-08-08 값인데
저장소가 그 뒤 **3배 이상** 커졌다. 재측정(**16,903줄** · 테스트·검증 4,093줄)으로 갈음하고,
**비율 자체는 팀이 정한다**고 못박았다 — 그건 측정이 아니라 신고다.

### G7 은 내가 못 한다

`hwp/docx` 이식·PDF 저장이 남았는데 **양식 파일이 저장소에 없고** 이 환경에 한글·Office 도 없다.
사람이 해야 한다. 대신 이식이 기계적으로 끝나도록 남은 TODO 를 위처럼 정리해 뒀다.

## 출품 10일 완성도 — 문서·계약·데모 출력 — 2026-08-15

코드가 아니라 **주장**을 정리했다. 촬영 D-8 · 내부 마감 D-11 이고, 1차는 서면으로만 갈린다(F2).

### 심사위원이 먼저 보는 숫자가 틀려 있었다

`README:51` 이 `acc=0.7000` 을 들고 있었다. 홀드아웃 재추출(SD-008)로 데모 골든 40장이 바뀐 뒤
**원고는 고쳐졌는데 README 만 남아 있었다.** 정본(`docs/spec/demo-expectation.json`)은 `0.8500` 이다.

같은 일이 또 벌어지지 않게 `check_submission` 의 대조 대상에 **README 를 넣었다.** 변이 검사로
확인했다 — `0.7000` 으로 되돌리자 `README.md:51` 을 집어낸다.

### 「열려 있다」를 사고가 아니라 **선택**으로 적는다

README 에 그 문단은 이미 있었다. 없던 것은 **플래그 이름**(`REQUIRE_API_KEY` ·
`REQUIRE_NODE_CREDENTIAL` · `CAPNET_AUTO_MIGRATE`)과 **최신 세대**였다 — 「세대 9 · `0001`–`0009`」로
멈춰 있었는데 실제는 `0017` 까지다. 바로 위 `logs migrate` 예상 출력도 「9개」→「17개」로 고쳤다.

### 반증된 보장은 이미 발급되지 않고 있었다

골든셋 정의서 §7 이 `equivalence.max_deviation = 0.05` 를 **발급 필드로** 적고 있었다.
그런데 실제 발급값(`seed.sql`)에는 그게 **없다** — `deviation.enforceable_bound = "1 - min_accuracy"`
와 `"tautological under a floor gate; NOT a constraint"` 로 이미 개정돼 있었다.

즉 **틀린 보장이 나간 적은 없고, 문서만 뒤처져 있었다.** 그래서 문서를 seed 에 맞추고
「발급 정본은 seed.sql 이다 — 다르면 seed 가 옳다」를 §7 머리에 박았다. 왜 빠졌는지도 절로 남겼다:
하한형 게이트가 강제할 수 있는 유일한 상한은 `1 - min_accuracy` = **0.32** 라는 동어반복이고,
편차를 실제로 묶으려면 밴드형 통과 기준이 필요하다(SD-009 → D17 → D18).

`compare_ab.py --max-deviation` 은 **그대로 뒀다.** 계약 발급이 아니라 관측 도구다.

### D2 는 「이름이 아니라 계약」이 아니라 **계약의 구성**이 폐기됐다

`context-handoff` D2 에 취소선을 그었다. 근거란에 **무엇이 살아남고 무엇이 죽었는지**를 적었다 —
「이름이 아니라 계약」은 유효하고, 골든셋·게이트를 계약에 **포함**시킨 부분이 D17 에서 무너졌다.
개정 후: 계약 = 인터페이스(스키마·전처리·실행조건), 골든셋+게이트 = 선택 품질 프로파일(D18·D20).

### 증적이 DB 에는 있는데 **밖에서 볼 수 없었다**

`assignment` 는 배정 시점의 `task_trust_domain`·`node_trust_domain`·`capability_tier`·`node_tier_max`
를 스냅샷으로 들고 있다 — **앱이 계산한 값이 아니라 DB 가 복합 FK 로 검증한 값**이고, 제품 주장
(「승인한 신뢰 도메인 안의 기기로만 간다」)의 증적이 정확히 이 넷이다.

그런데 `GET /v1/tasks/{id}` 가 `id·status·agent_id·node_id·finished_at` 만 돌려주고 있었다.
**「조회해서 찍기」가 성립하지 않았다.** psql 직결은 `compose.prod` 에서 postgres 가 비공개라
제품 경로에서 깨지고, `/v1/ops/safety` 는 기기 단위라 「이 배정이 왜 허용됐나」를 못 찍는다.
그래서 **API SELECT 를 넓혔다** — 읽기전용 · DDL 0 · 인증/소유권 분기는 그 앞단이라 무수정.

```text
증적: assignment=… node=… agent=… status=SUCCEEDED
경계: 신뢰도메인 task=team -> node=team · 티어 capability=M <= node_max=M
```

**`demo.ps1` 도 같이 고쳤다.** 촬영은 PowerShell 인데 검증 3종은 `.sh` 만 만진다 — 직전에
정확히 그 비대칭으로 사고가 났다(G5 · `arch` 누락 HTTP 400).

### 사슬은 세 칸이고, 한 칸만 빠져도 조용히 무의미해진다

`tests/test_assignment_evidence_wiring.py` **4종** — 컬럼이 있다(schema) → API 가 준다 →
데모가 찍는다(`.sh` **와** `.ps1`) → openapi 에 적힌다. `test_openapi_drift` 는 **경로만** 보고
필드는 못 잡으므로(#73 의 `org_id` 누출이 그 모양이었다) 이 건에 한해 그 구멍을 막았다.

변이 검사로 확인했다 — API SELECT 를 되돌리고 `.ps1` 만 안 고친 상태에서 **2건 실패**.

### 돌리지 못한 것

**`clean_room.sh` · `prod_room.sh` 를 못 돌렸다.** 이 세션에서 Docker Desktop 이 WSL 에 붙어 있지
않다(`docker` 명령 자체가 없다). `run_tests` 는 64→**68종** 전부 통과했지만 **새 출력 두 줄을
실제로 찍어 보지는 못했다.** 정적 가드로 사슬만 고정했고, 한계로 적어 둔다.

## 러닝크루 화면 — 초대 발행·소진 + 키 입력줄 — 2026-08-15

G2(초대 경로)는 **API 로만** 있었다. 「러닝크루가 자기 기기를 내놓는다」를 하려면
초대받은 사람이 `curl` 을 쳐야 했다. 화면만 붙인다 — **새 기능·새 능력·메일 없음.**

### 소진 화면은 **입력칸이 없는 것**이 설계다

`/ui/redeem.html` 에는 등급·조직·티어 입력칸이 **없다.** 초대장이 이미 정했고 요청은
바꾸지 못하기 때문이다(절대규칙 4). 「무시한다」가 아니라 **주장할 자리를 만들지 않는다** —
G2 에서 `NodeRedeem` 에 등급 필드를 안 만든 것과 같은 규율을 화면에도 적용했다.

**관리 키도 만지지 않는다.** 초대받은 사람에게는 키가 없고 초대 토큰이 인증이다.
전용 래퍼 `apiInvite()` 를 쓰며, 키를 붙이는 `api()` 는 이 화면에서 쓰지 않는다.

초대 링크는 토큰을 **해시 조각**(`#…`)에 담고 열자마자 주소창에서 지운다 —
쿼리스트링은 서버 접근 로그·브라우저 기록·Referer 로 샌다.

### 키 입력줄 — UI 가 다시 쓸모 있어졌다

read-auth(#69) 뒤 최소 UI 는 **강제 모드에서 아무것도 못 했다**(키를 안 보냈다).
문서에 「데모 전용」이라고 적어 뒀던 바로 그 상태다. 화면 위에 키줄을 붙여 되돌렸다.

키는 **`sessionStorage` 에만** 산다 — 서버로는 요청 헤더로만 가고 Core 는 저장하지 않는다.
`localStorage` 가 아닌 것은 의도다: **탭을 닫으면 사라진다.** URL 에는 절대 싣지 않는다.

페이지마다 있던 `api()`·`esc()` 중복을 **공용 `app.js`** 로 모았다 — 한쪽만 고쳐지는 일을 막는다.

### 눌러 볼 수 없으니 **되면 안 되는 것**을 검사한다

브라우저가 CI 에 없고 단위 잡은 의존성 0 이라 헤드리스도 못 쓴다.
`tests/test_ui_invariants.py` (8종) 는 텍스트로 판별되는 **정책 위반**만 본다 —
소진 화면이 관리 키를 만지는지 · 등급 입력칸이 생겼는지 · 키가 URL 에 실리는지 ·
외부 자산이 붙었는지 · `localStorage` 를 쓰는지 · 헬퍼를 다시 정의하는지.

**검사가 주석을 잡는 사고가 한 번 났다.** 「왜 `localStorage` 를 안 쓰는지」 적어 둔
설명 문구가 위반으로 걸렸다 — **설명을 지워야 통과하는 검사**가 될 뻔했다.
`//` 주석을 걷어내고 코드만 보게 고쳤고, 그 사정을 검사에 적어 뒀다.
변이 검사로 확인했다 (소진 화면에 등급 칸을 넣자 실패).

### 실측 — 강제 모드에서

| | |
|---|---|
| `/ui/redeem.html` · `/ui/app.js` | 200 |
| 초대 발행 — 키 없음 / 있음 | **401 / 200** |
| **초대 소진 — 관리 키 없이 초대 토큰만** | **200** |
| 함대 조회 — 키 없음 / 있음 | **401 / 200** |

`prod_room` **27/27** · `run_tests` 전부(UI 불변식 8종 포함) · `check_submission` 21/21 ·
데모 스택에서 발행 → 소진 → 재소진 **401** 왕복.

**JS 문법은 검사하지 못했다** — 이 환경에 `node` 가 없다. 대신 `$("…")` 참조가 전부
실재 `id` 인지, 괄호가 균형인지를 정적으로 확인했다. 한계로 적어 둔다.

## D24 뒤처리 — 내 변경이 남긴 문서 구멍 넷 — 2026-08-14

코드가 아니라 **기록**이 뒤처져 있었다. 전부 최근 PR 들에서 내가 만든 미완성이다.

| 구멍 | 무엇이 문제였나 |
|---|---|
| `openapi.yaml` 에 `org_id` **0건** | `POST /v1/nodes`·`/v1/nodes/invites` 본문에 배선해 놓고 문서에 안 적었다. **드리프트 가드가 못 잡는다** — 경로만 보고 필드는 안 보기 때문이다 |
| `STATE` 헤더 `갱신: 2026-08-12` | 그 뒤로 행을 여럿 붙여 놓고 헤더는 그대로 뒀다 |
| `INDEX` 에 `demo-expectation.json` 없음 | 정본을 새로 만들어 놓고 문서 지도에 안 올렸다 |
| 안전 사슬 표에 조직·조회 칸 없음 | 「13칸」 표가 D24·read-auth 이후에도 그대로였다 |

### 사슬 표는 숫자만 바꾼 게 아니다

`15 조직 경계` · `16 조회 격리` 를 **칸으로 추가**했다. 이 둘은 문서를 처음 쓸 때
**세지도 않았던** 것이다 — 「누가 볼 수 있나」와 「어디서 도는가」를 등급 하나로 덮고 있다고
착각했기 때문이다. 등급은 민감도이지 소속이 아니다. 다중 조직을 가정하자 둘 다 열려 있었다.
그 착각을 표에 남겨 뒀다.

**13칸 중 11 → 16칸 중 14.** 남은 둘(Node 신원·관리 API)은 여전히 코드가 아니라 **기본값** 문제다.

### 드리프트 가드의 한계도 드러났다

`test_openapi_drift` 는 **경로만** 본다. 필드가 늘어난 것은 못 잡는다 —
이번에 `org_id` 3개가 그렇게 새어 나갔다. 필드까지 보려면 YAML 파서가 필요한데
CI 단위 잡은 의존성 0 이라 지금은 못 한다. **한계를 알고 쓰는 검사**로 남긴다.

문서만. 코드·동작 변경 0. `run_tests` 전부 · `check_submission` 21/21.

## 조직 경계 — 등급과 소속을 분리한다 (D24) — 2026-08-14

**조회 문제가 아니라 실행 문제였다.** read-auth(#69)로 「누가 볼 수 있나」는 닫았지만
「**어디서 도는가**」는 열려 있었다. Proposal 에서 프로브로 재현한 그대로다 —
**조직 A 의 작업이 조직 B 의 tenant 기기에 배정됐다.**

원인은 **등급을 소속으로 쓴 것**이다. `trust_domain='tenant'` 는 **민감도 등급**이지
**어느 조직**이 아니다. tenant 가 둘이면 둘 다 `'tenant'` 라 `domain_compatible` 이
구별할 수가 없었다. 제품 주장(「승인하지 않은 신뢰 도메인으로 라우팅되지 않는다」)은
참이지만, **같은 등급의 다른 조직**은 승인한 적이 없는데도 라우팅됐다.

### 설계 — 도메인·티어와 같은 모양

`0017` — `org` 테이블 + `app_user`·`node`·`task`·`node_invite` 에 `org_id`. **추가만.**
배정은 스냅샷 둘(`task_org_id`·`node_org_id`) + 복합 FK 둘 + CHECK 하나가 판정한다.

    ck_assignment_org — 같은 조직이거나, 공용 기기이거나. 그것뿐이다.

행렬 테이블이 없다 — 도메인·티어와 달리 **순서가 아니라 동일성**이기 때문이다.
`claim` 은 후보 단계에서도 조직을 보고(P2-1 에서 배운 것 — 안 그러면 가용성이 깨진다),
**판정은 DB 가** 한다 (절대규칙 2).

**`IS NOT DISTINCT FROM` 을 쓴 이유가 있다.** 그냥 `=` 로 쓰면 `task_org_id` 가 NULL 인 행이
**어느 조직 기기로든** 통과한다 — 비교가 NULL 이고 CHECK 는 NULL 을 통과시키기 때문이다.
그게 바로 닫으려는 구멍이라 「모르면 거절」로 못박았다.

### 지금 동작을 깨지 않는다

기존 `app_user`·`task` 는 `default` org 로 백필하고 **기존 Node 는 NULL(공용)로 뒀다.**
공용 기기는 모든 조직의 작업을 받으므로 데모·심사 경로가 그대로 돈다 —
`clean_room` **9/9** 가 그것을 실측한다. **`NOT NULL` 승격은 하지 않았다**:
조직을 쓰지 않는 배포를 계속 지원한다.

### 죽어 있던 소유자 축도 살렸다

`node.owner_id`·`agent.owner_id` 가 앱에서 **시드 admin 으로 하드코딩**돼 있었다 —
컬럼은 있는데 아무 뜻이 없었다. 이제 실제 등록자가 들어간다. 초대로 들어온 기기는
**초대 발행자**가 소유자다. 라우팅 판정은 `org_id` 만 쓴다 (Decision 6).

### 조회도 조직으로 걸린다

- `GET /v1/tasks/{id}` — 운영자는 **자기 조직 안에서만** 남의 작업을 본다.
  조직 없는 `admin` 은 팀 운영자로 보고 전체를 본다
- **좁아진 지점이 하나 있다.** 전에는 `developer` 면 남의 작업을 다 봤는데, 이제 **조직 없는
  `developer` 는 못 본다.** CI 가 이걸 잡았다 — `check_task_ownership` 이 옛 규칙을 담고
  있어서 실패했다. **검사를 고쳐 통과시킨 게 아니라, 규칙을 세 갈래로 나눠 다시 썼다**
  (같은 조직 developer · 조직 없는 developer · 조직 없는 admin)
- `GET /v1/nodes` · `/v1/nodes-liveness` — **자기 조직 + 공용**만

### 검사 — `check_org_boundary` 14/14 (신규)

| 무엇 | |
|---|---|
| A 의 작업 → B 의 기기 | `claim` 이 **고르지 않는다** |
| 앱을 건너뛰고 직접 INSERT | **`ck_assignment_org` 가 거절** |
| 거짓 조직 스냅샷 | **복합 FK 가 거절** (`assignment_task_org_fkey`) |
| 공용 기기(NULL) | 모든 조직의 작업을 받는다 |
| 같은 조직 기기 | 정상 배정 — **가용성이 안 깨진다** |
| 남의 조직 작업 조회 | **404** · 함대 목록은 자기 조직 + 공용만 |
| 초대 소진 | 조직이 **초대장**에서 온다 · 소유자가 실제로 기록된다 |

회귀: 통합 10 → **11종** · `run_tests` 전부 · `clean_room` **9/9** · `prod_room` **27/27**.

**남은 것** — 조직별 쿼터·요금은 없다(경제는 비기초 · D19). TLS · rate limit ·
C 백업 · 관리키 회전은 보류 그대로.

## 조회면 인증과 소유권 — 「증적이 남고 조회된다」의 뒷문을 닫는다 — 2026-08-14

**쓰기는 전부 잠겨 있었는데 읽기는 15개가 열려 있었다.** 가장 날카로운 것은
`GET /v1/tasks/{id}` — **추론 결과(`result_ref`)와 증적 전체**를 인증 없이 줬다.
제품 문구가 「증적이 남고 조회된다」인데 실제로는 **「누구나 조회된다」** 였다.
`task_id` 만 알면 남의 작업 결과를 봤다.

**DDL 은 필요 없었다.** `task.user_id` 에 요청자가 이미 기록되고 있었다 (B0·D23) —
판정할 데이터가 이미 있었고, 그걸 **아무도 보지 않고 있었다**.

### 등급 배치

| 등급 | 경로 |
|---|---|
| **공개 유지** | `/health` · `/` · `/openapi.yaml` · `/v1/datasets` · `/v1/capabilities`(+단건) |
| **user** | `/v1/tasks/{id}`(+소유권) · `/v1/inputs/{id}` |
| **developer** | `/v1/nodes`(+단건) · `/v1/nodes-liveness` · `/v1/agents`(+단건) · `/v1/ops/status` · `/v1/internal/gate-runs/{id}` |
| **admin** | `/v1/nodes-credentials` |

능력 카탈로그를 공개로 둔 것은 **제품 주장의 앞면**이기 때문이다 — 「능력만 요구하면 된다」.
`/v1/nodes-credentials` 를 admin 으로 올린 것은 S2 때 남긴 비일관을 닫은 것이다:
`/v1/ops/safety` 는 잠갔으면서 같은 정보의 일부를 주는 조회면은 열려 있었다.

### 소유권 — 남의 작업도, **없는 작업도** 404

403 이 아니라 404 다. 403 은 「그 id 는 존재한다」를 흘린다. 둘이 구별되지 않아야
존재를 캐지 못한다. `developer` 이상은 운영상 남의 작업도 본다.

### 안전판 — 강제가 꺼져 있으면 아무것도 안 깨진다

`_require` 의 레거시 경로 덕에 **키 없이 부르면 종전대로 통과**한다.
`clean_room` **9/9** 가 그것을 실측한다. **키가 오면 역할과 소유권은 언제나 본다** (S1 규율).

### 검사 — 「막힌다」가 아니라 「무엇이 안 보이나」

- **`check_task_ownership` 10/10 (새로 만듦)** — 소유자 200 · 남 404 · 없는 작업도 404 ·
  `developer` 는 봄 · 강제 꺼짐이면 통과 · **응답에 요청자가 실린다**(B0 가 기록한 것이 조회로 이어진다)
- `check_enforcement` 23 → **30종** — 무인증 조회면 401 · `user` 로 증서 조회면 403 ·
  **능력 카탈로그는 공개**(결정을 검사로 고정)
- `prod_room` 20 → **27종** — 제품 프로파일에서 **남의 작업이 실제로 404**

**이 검사는 SAVEPOINT 로 못 굴린다.** 핸들러가 자기 커넥션을 열어 시험 데이터가 보이려면
커밋해야 한다 (`check_revocation` 과 같은 사정). 대신 끝에서 지우고, 지워졌는지도 검사한다.

### 옮긴 것

`prod_room` §4 의 `enforcement` 표시를 §8-3 으로 옮겼다 — §4 는 admin 키 발급 **전**이라
이제 그 자리에서 401 이다.

### 남은 것 — **조직 경계가 없다**

`app_user` 에 소속이 없어서 **`developer` 이상 키 하나면 다른 tenant 의 작업도 보인다.**
지금의 tenant 격리는 「어디서 실행되나」(라우팅)까지다. 다중 조직에 열려면 이 칸이 먼저이고,
DDL 이자 D19 유통 모양을 정하는 결정이라 **별 Proposal** 로 분리했다.
최소 UI 는 키를 보내지 않아 **강제 모드에서 데모 전용**임을 문서에 명시했다.

## 결과보고서 갱신 — 증거를 최신화한다 (Q2–Q4) — 2026-08-14

Decision Q2–Q4. **제품 주장·보장 문구(D18)는 건드리지 않았다** — 8/13–14 에 들어온 것들이
원고에 **0건**이어서 증거만 최신화한다.

### Q2 — 본문에 둘, 나머지는 한 줄

본문은 **2쪽 고정 표**라 추가는 곧 삭제다. Decision 대로 **①②만 본문**에 넣었다.

- **입력 통제 (D8′·B1)** — 보고서 1절이 「내 데이터가 어디로 갔는지 답할 수 있는가」인데
  정작 **입력 이야기가 없었다.** Core 가 해시·크기·MIME 를 계약과 대조해 받고, 기기가 다시
  해시를 대조한 뒤 실행하고 끝나면 지운다. **바이트는 휘발성, 해시와 증적은 남는다** —
  1절의 질문에 답하는 근거가 이것이다
- **계약 검증 실수행 (B2)** — 「계약」을 주장하면서 예전엔 **보고를 받아 적었다.**
  지금은 채점 기기가 실행해서 판정한다

③초대(G2) · ④안전 조회면(S2) · ⑤재시도 상한·강제 CI 는 **한 줄로** 묶었다.

**분량을 쟀다** — 본문 압축본 3578 → 4102자였다가, 새로 넣은 문장을 조여 **3970자**(+392).
2쪽 표에 실제로 들어가는지는 양식 파일에서 사람이 확인해야 한다.

### Q3 — 「가장 중요한 수정」이 낡아 있었다

혁신성 절은 「Core 가 중개한다는 주장과 동작을 일치시킨 것」을 가장 중요한 수정으로 적는데,
**그때는 배정만 중개였다** — 데이터는 기기가 로컬에서 골랐다. B1 이후 **입력 바이트도
Core 가 나른다.** 같은 주장이 실제로 더 참이 됐으므로 그렇게 고쳤다.

### Q4 — 6종 유지 + 한 줄

촬영 자산이 위반 6종 기준이라 시연 목록은 그대로 두고, 이후 늘어난 제약을 한 줄로 덧붙였다 —
재시도 상한 초과 배정 · 샘플 없는 계약 심사 · 초대 등급·소진 한도. **거절의 주체는 계속 DB다.**

회귀: `check_submission` **21/21** (예고 수치 정본 대조 포함) · `run_tests` 전부.

## 보고서 예고 수치 정정 — 재현과 어긋나 있었다 — 2026-08-14

**심사위원이 README 대로 재현하면 보고서와 다른 숫자를 봤을 것이다.**

원고 두 개가 「기대 출력」으로 예고한 값이 `acc=0.7000 · f1=0.6982` 였는데,
지금 돌리면 **`0.8500 · 0.8344`** 다. 원인은 **SD-008 홀드아웃 재추출(2026-08-10)** —
같은 가중치인데 데모 골든 40장이 바뀌었다. 원고 마지막 수정은 8/12 였고 그때 이미 어긋나 있었다.

**10곳을 고쳤다** (원고 2개 × 5). 고친 것은 「지금 돌리면 이렇게 나온다」고 **예고한** 자리뿐이다.

**`phase1-verdict.md` 의 `0.7000` 들은 그대로 둔다** — 2026-08-08 Phase 1 실측 **기록**이다.
그건 역사이고, 고치면 기록 조작이다. 이 구분이 이 커밋의 요점이다.

### 흩어진 선언부가 원인이므로 정본을 만든다

`docs/spec/demo-expectation.json` 하나만 값을 갖고, `check_submission` 이 원고를 대조한다
(`check_demo_expectation`). **골든셋 sha 를 한 곳으로 모은 SD-013 과 같은 이유·같은 모양**이다.

판정은 두 모양만 좁게 잡는다 — 이름에 **붙은** 값(`acc=…` · `정확도 …` · `macro_f1 …`)과
실측 표의 행(`|` 로 시작 + `dummy=false`). 넓게 잡았더니 **다른 실측을 오탐**했다:
A/B 통과자 폭 `0.1767`, n=300 paired `|Δacc| 0.0467`. 둘 다 데모 기대치가 아니다.
「0개를 대조하며 통과」하는 상태도 검사가 막는다.

변이 검사로 확인했다 — 한 곳을 `0.7000` 으로 되돌리자 실패, 원복하니 통과.

회귀: `check_submission` 20 → **21종 · 21/21**.

## 촬영 리허설 — `.ps1` 이 촬영일에 깨질 뻔했다 — 2026-08-14

D-9 에 촬영 런북(`shoot-day-runbook.md`)의 타임라인 명령을 **순서대로 한 번 돌렸다.**
리허설 주간(8/18–22)을 기다리지 않은 이유는, 8/13–14 에 들어온 변경이 촬영 경로를
건드렸기 때문이다 — 특히 G5(`arch` 등록 필수).

**찾은 것 — 촬영은 PowerShell 로 하는데 `.ps1` 을 안 고쳤다.**

G5 에서 `POST /v1/agents` 가 `arch` 를 요구하게 바꾸면서 셸 스크립트 넷은 고쳤지만
`demo.ps1` · `smoke_w1.ps1` 을 놓쳤다. 리눅스에서 도는 검증 3종(`run_tests` ·
`clean_room` · `prod_room`)은 `.sh` 만 만지므로 **어느 검사에도 안 걸렸다.**
촬영 당일 첫 명령에서 **HTTP 400** 을 만났을 것이다.

- `demo.ps1` — `arch` 를 sha 와 **같은 증언**(Node `/health` 의 학습 기록)에서 뽑는다
- `smoke_w1.ps1` — 정상 등록 경로에 `arch` 추가. 그리고 **`.pth` 거부 검사에도** 넣었다:
  안 넣으면 「arch 없음」으로 400 이 나서 **「.pth 를 거부했다」가 엉뚱한 이유로 통과**한다

**같은 종류의 누락(「한쪽 계열만 고침」)을 검사로 고정했다** —
`tests/test_agent_arch_wiring.py`. `POST /v1/agents` 를 부르는 스크립트에 `arch` 가
없으면 실패하고, **`.sh`·`.ps1` 양쪽이 대상에 잡혔는지**까지 본다.
`prod_room.sh` 는 예외다 — 「무인증 401」을 보는 검사라 본문이 일부러 불완전하다.
예외 목록이 낡는 것도 검사가 본다. 변이 검사로 확인했다 (`demo.ps1` 의 arch 를 지우자 실패).

**리허설 결과 — 나머지는 전부 재현됐다.** `demo.sh` `PASSED acc=0.8500` ·
sanity 3종 FAILED · 위반 **6종 REJECTED** · `proof_ab` A/B 둘 다 완결 · 증적 줄 출력 ·
`nodes-liveness` · `migrate.sh status` 세대 16 · 촬영 전 기계 점검 3종 통과
(`check_submission` **20/20** — 워킹트리 포함).

회귀: `run_tests` 52 → **56**.

## G2 — 초대 경로 · 관리 키 없이 함대에 들어온다 — 2026-08-14

`node.provision_source` 는 `invited` 를 받는데 **그 값을 만드는 절차가 없었다.** 값은 스키마에
있고 경로가 없다 — `attempt_no` 와 같은 모양이다. 그래서 「러닝크루가 자기 기기를 내놓는다」가
실제로는 **관리자 수작업**이었다.

### 등급은 초대장에 박힌다 — 그게 절대규칙 4 를 지키는 유일한 길

관리자가 발행할 때 `trust_domain`·`compute_tier_max` 를 정하고, 신청자는 **소진**할 뿐이다.
소진 요청 본문(`NodeRedeem`)에는 **등급 필드가 아예 없다** — 주장할 자리를 만들지 않았다.

    ① admin 이 초대 발행 (등급·티어·만료가 박힌다 · 평문은 한 번만)
    ② 초대받은 사람이 토큰으로 소진 — 관리 키 없이
    ③ Core 가 초대장 등급으로 Node 생성 + 증서 발급 (원스텝)
    ④ 소진 (audit_log · node_invite_redemption)

`0016` — `node_invite` · `node_invite_redemption` · `node_invite_status` 뷰. **추가만.**

**기존 제약이 이미 지켜 준다.** `ck_invite_domain` 이 `team` 초대를 **발행 단계에서** 막고
(발행은 됐는데 소진이 안 되는 초대장을 만들지 않는다), `ck_trust_provision_align` 이
`(team, invited)` 를 거절하며, `ck_gate_runner_team` 때문에 초대로 들어온 기기는
**채점자가 될 수 없다** — 절대규칙 8 이 그대로 선다. 새로 막을 게 없었다.

### 이 기능의 위험은 「소진이 관리 키 없이 열린다」는 것이다

지금까지 쓰기는 **전부** 키 뒤에 있었다. 초대받은 사람에게는 키가 없으므로 이 경로만 예외다.
완화를 겹쳤다 — 만료(기본 7일) · 1회용(기본) · 폐기 · 증적, 그리고 **소진 판정은 DB 가 한다**:
조건부 UPDATE 의 WHERE 절이므로 앱을 건너뛰어 `CLAIM_SQL` 을 직접 두들겨도 상한을 못 넘고,
두 요청이 동시에 와도 한쪽만 통과한다.

`check_enforcement` 가 **「막는 주체가 API 키 강제가 아니다」** 까지 고정한다 —
키를 요구하면 초대받은 사람이 못 쓰기 때문이다. 열려 있다는 것과 아무나 쓴다는 것은 다르다.

**실측** — `check_node_invite` **20/20** · `check_enforcement` 20 → **23종** ·
`prod_room` 16 → **20종**. 제품 프로파일에서 **관리 키 없이 소진**해
`tenant/invited/게이트러너 아님/증서 받음` 을 확인했고, 같은 초대 두 번째는 **401**.

### 수용 게이트가 옛 이미지로 마이그레이션하고 있었다

8-2 를 붙이자 초대 발행이 **500** 이었다. `0016` 이 적용되지 않아서다 —
`prod_room` §3 이 `dc run … migrate up` 을 **빌드 전에** 돌리는데, `migrations/` 는
이미지에 COPY 되므로 **옛 이미지의 마이그레이션 목록**이 적용된다. 직전 PR 에서 §4 에
`--build` 를 넣었지만 그건 **런타임만** 덮었다 — 그래서 「새 마이그레이션이 없는 DB 위에
새 코드가 뜨는」 상태가 남아 있었다. §3 앞에 `dc build core` 를 넣어 닫았다.

**새 DDL 을 붙이지 않았으면 이 구멍은 계속 안 보였다.**

## G4·G5 — 증서 회전 런북 · arch 를 등록에서 요구한다 — 2026-08-14

안전 사슬의 남은 노란 칸 둘. **DDL 0 · 새 의존성 0.**

### G5 — `POST /v1/agents` 가 `arch` 를 요구한다

`agent.arch` 는 nullable 이고(legacy), 없는 값이면 FK 가 막았지만 **아예 안 보내면 통과**했다.
그러면 실행 아키텍처를 Node 로컬 `meta.json` 이 정한다 — I1 이 닫으려던 바로 그 구멍이다.

없으면 **400**. `agent.arch` 는 **nullable 로 둔다** — legacy 행을 지우거나 백필을 강제하지
않기 위해서다. 그래서 「새로 만들지 않는다」는 DB 가 아니라 앱이 지키고, 그 분기를 검사가 본다.

**분기를 `_require` 뒤에 뒀다.** 앞에 두면(= pydantic 필수 필드로 두면) 본문 검증이 인증보다
먼저 도는 탓에 강제 모드에서 **무인증 요청이 401 대신 422** 를 받는다 —
`prod_room` 의 「무인증 쓰기는 401」이 깨진다. 검사 하나가 **분기의 위치 자체**를 고정한다.

등록 스크립트 넷(`demo` · `node_bind` · `proof_ab` · `pass_rate`)이 `arch` 를 싣는다.
근거는 **학습 기록**이다 — Node `/health` 의 `weights[].arch`(= `<weights>.meta.json`),
`node_bind` 는 러너에서 `_arch_for_weights` 를 부른다(`--arch` 로 덮어쓸 수 있다).
`backfill_agent_arch.sh` 와 **같은 출처**다. Core 는 추측하지 않는다.

**실측 (clean room · 빈 볼륨)** — `demo.sh` 가 등록한 Agent 가 `arch=TinyEuroSAT` 로 남고,
`/v1/ops/safety` 의 `arch_unbound_routable` 이 **1 → 0**. arch 없는 등록은 **HTTP 400**.

### G4 — 증서 회전 런북 (`operate-node.md` §2)

멈춤 → 「일이 안 간다」 확인 → 폐기·재발급 → 재기동 → 확인. 5단계.

**무중단은 되지 않는다는 것을 그대로 적었다.** `node_credential_active_idx` 가 Node 당 활성
증서를 하나로 강제하므로 새 증서를 먼저 발급해 겹칠 수 없다. 겹치려면 스키마가 바뀐다 —
별 Decision 이다. 「무중단 순서」를 지어내지 않고 짧은 중단을 인정했다.

**돌려 보고 한 줄을 고쳤다.** 제품 프로파일에서 실제 회전한 결과
(`cn_99a7a084` → `cn_18209df6` · `credential_valid=true` · `risks` 없음),
**Node 를 멈춘 직후에도 `is_fresh=true`** 였다 — 마지막 heartbeat 이 아직 신선해서다.
`heartbeat_timeout_s`(기본 45초)가 지나야 내려간다. 그 창 안에 폐기하면 배정이 401 로 깨진다.
런북은 이제 `leases_live=0` **그리고** `is_fresh=false` 를 둘 다 기다리라고 적는다.
**돌려 보지 않았으면 틀린 런북을 남겼다.**

확인 단계는 S2 조회면(`/v1/ops/safety`)을 쓴다 — 조회 여러 개를 이어 붙이지 않는다.

회귀: `check_agent_arch` **9 → 13종** · `run_tests` 전부 · `clean_room` 9/9 · `prod_room` 16/16.

**DB 로 올리는 것은 별 Decision** — `arch NOT NULL` 은 legacy 행 처리가 선행이다.

## S2 — 「누가 내 데이터를 돌릴 수 있나」를 한 면에서 답한다 — 2026-08-14

안전 사슬 갭 분석의 **G3**. 이 질문에 답하려면 조회면 넷을 이어 붙여야 했다 —
`/v1/nodes`(등급) · `/v1/nodes-credentials`(증서) · `/v1/nodes-liveness`(생사) ·
`/v1/ops/status`(합계). **기기 하나에 대해 「왜 실행 가능한가」가 한 곳에 없었다.**

**`GET /v1/ops/safety`** — 기기 단위로 등급·조달 경로·증서(prefix·만료·마지막 사용)·생사,
**받을 수 있는 요청 도메인**(`accepts_task_domains`), **라우팅 가능한 (Agent, 능력) 쌍**
(`routable_pairs`), 그리고 위험 표시를 한 번에 준다. `by_task_domain` 은 질문 그대로의 답이다 —
「team 요청을 돌릴 수 있는 기기가 몇 대이고, 그중 몇 대가 살아 있고 증서가 없는가」.

**읽기 전용 · DDL 0 · 새 테이블·뷰 0 · 새 의존성 0.** 시크릿은 나가지 않는다 (prefix 만).

### 이 조회면의 유일한 실패 방식은 **거짓말**이다

실제 배정과 다른 그림을 보여주면, 있으나 마나가 아니라 **해롭다**. 그래서 `routable_pairs` 는
`claim.CLAIM_SQL` 의 후보 조건을 **그대로** 센다 — 증서 유효(`revoked_at IS NULL`) ·
Agent `ACTIVE` · `agent_node_ready` · `tier_compatible`. task 쪽 조건만 뺀 것이다.

`tests/integration/check_ops_safety.py` (21종)가 **둘이 같은 답을 내는지** 고정한다.
필드가 있는지가 아니라 **claim 과 일치하는지**를 본다.

| 검사 | 무엇을 잡나 |
|---|---|
| 조회면이 「가능」이라 한 기기 → `claim` 이 **실제로 배정** | 낙관적 거짓말 |
| 조회면이 「불가」라 한 기기 → `claim` 도 **고르지 않음** | 비관적 거짓말 |
| Agent `DISABLED` → `routable_pairs` 감소 (`agents_ready` 는 유지) | 바인딩과 라우팅 혼동 |
| 증서 폐기 → `credential_valid` · 위험 표시 반영 | 증서 축 누락 |
| 호출 전후 7개 테이블 행 수 불변 | 조회면이 쓰는 것 |
| 증서 해시·발급 토큰이 응답에 **없다** | 시크릿 유출 |

**강제가 꺼져 있으면 `ok=false` 다.** 데모 기본값에서 「안전하다」고 말하는 조회면이라면
그 자체가 결함이다 — 같은 상태를 강제 켜짐/꺼짐에서 **다르게 읽는다**:

    꺼짐 — 증서 없음: 강제를 켜면 이 기기는 잠긴다 (지금은 사칭을 막지 못한다)
    켜짐 — 증서 없음: 강제가 켜져 있어 이 기기는 배정을 가져갈 수 없다

**검사를 쓰다 티어 순서를 반대로 잡았다.** `S=1 · M=2 · L=3` 이라 M 능력은 L 기기에서 **돈다**.
절대규칙 3이 경고하는 바로 그 착각이고, 판정을 `tier_compatible` 에 맡긴 덕에 코드가 아니라
검사만 틀렸다. 비호환 픽스처를 `S` 로 바꿔 통과.

**시드가 드러난 것 하나** — seed Agent 는 `arch` 가 NULL 이라(0008 이전 세대) 게이트를
통과시키면 `arch 미선언 Agent 라우팅 가능 1건` 이 뜬다. 숨기지 않고 위험 표시로 남겼다 (G5).

운영 조회면이라 `_require("developer")` 를 건다 — 강제가 꺼져 있고 키가 없으면 종전대로 통과해
데모 경로를 깨지 않고, 키가 오면 역할은 항상 본다 (S1 과 같은 규율).

회귀: `run_tests` 전부 통과 · 통합 검사 **8 → 9종** · `clean_room` 9/9 · `prod_room` 14/14.

**남은 것** — G2 초대 경로(스키마 추가 · 별 Proposal) · G4 증서 회전 런북 ·
G5 등록 시 arch 요구. `openapi.yaml` 은 `/v1/ops/*`·`/v1/inputs` 가 이미 빠져 있다 —
이 PR 에서 늘리지 않았고, 드리프트 정리는 별건으로 남긴다.

## S1 — 강제 모드 불변식을 CI 가 지킨다 — 2026-08-13

안전 사슬 갭 분석(G1)의 1순위. 「**강제를 켜면 실제로 401 이 나오는가**」를 확인하는 것이
`prod_room.sh`(수동) 에만 있었다. `check_api_key`(23)·`check_node_credential`(17)은 **DB 계층**만
본다 — 키 해시·역할·증서 검증 자체. **안전이 핵심 기능인데 그 회귀를 CI 가 못 잡았다.**

**`tests/integration/check_enforcement.py` (20종)** — `run_integration.sh` 가 자동 수집한다.

- **HTTP 서버를 띄우지 않는다.** 앱의 **강제 분기**를 직접 본다 —
  `_actor`·`_require`·`_authenticated_node`·`_assert_node_matches` 가 `HTTPException(401/403)` 을
  던지는지. `httpx`/`TestClient` 를 끌어오지 않으므로 **새 의존성 0**
- 강제 플래그는 **모듈 상수**라 임포트 시점에 굳는다. 환경변수를 바꾸고 `importlib.reload` 로
  **두 모드를 모두** 확인한다 — `compose.prod.yaml` 이 환경으로 뒤집는 실제 배포 모양이다

| 켜짐 (제품) | 꺼짐 (데모) |
|---|---|
| 키 없음 · 형식 아님 · 없는 키 → **401** | 키 없음 → 통과 (레거시 경로) |
| 역할 부족(user→admin) → **403** | **없는 키는 여전히 401** |
| 증서 없음 · 가짜 증서 → **401** | **역할은 그대로 본다** (403) |
| 다른 Node 증서 → **403** (사칭) | **사칭은 꺼져 있어도 403** |

오른쪽 열이 요점이다 — 「강제가 꺼져 있으니 아무 키나 통과」하는 구간이 없다는 것을 고정한다.
코드 주석이 주장하던 것(「켜지 않아도 키가 오면 항상 검증한다」)이 이제 검사로 남았다.

**변이 검사로 가드가 실제로 잡는지 확인했다.** `_actor` 에서 강제 분기를 지워 넣자
`20/20 → 17/20`, 통합 검사가 `실패 1` 로 떨어졌다. 원복 후 전부 복귀.

**CI 러너 의존성이 모자랐다.** CI 는 `psycopg`·`pydantic-settings` 만 깔고 있었는데 이 검사는
`app.main` 을 임포트한다 — 첫 푸시에서 `ModuleNotFoundError: fastapi` 로 떨어졌다.
로컬은 core 컨테이너(전부 설치됨)라 잡히지 않았다. `fastapi==0.116.1`·`psycopg-pool==3.3.1` 을
러너에 추가했다 — **새 의존성이 아니라 `apps/core/requirements.txt` 와 같은 핀**이다.

이후 **CI 환경을 그대로 재현해** 재확인했다 — 깡통 `python:3.11-slim` 에 `ci.yml` 이 까는 것만
설치하고 돌려 20/20. 로컬 컨테이너와 CI 러너의 환경 차이는 다시 겪지 않게 이 방식으로 본다.

회귀: `run_tests` 전부 통과 · 통합 검사 **7 → 8종 · 8/8** · `clean_room` 9/9 · `prod_room` 14/14.

**남은 것** — G1 의 절반인 **기본값 자체**는 그대로다. `compose.yaml` 단독은 열려 있고 닫으려면
`compose.prod.yaml` 을 쓴다. 그건 운영 선택이지 코드 결함이 아니다. S2(안전 자세 조회면)는 분리.


## 배정 재시도 상한 — 조용한 무한 재시도를 닫는다 — 2026-08-13

직전 PR 에서 기록한 동작이다. 계약이 모델과 맞지 않으면 실행이 매번 깨지는데,

1. Node 가 그 실패를 **Core 에 보고하지 않았다** — 로그에만 쌓였다
2. `attempt_no` 는 스키마에 있었지만 **아무도 세지 않았다** (항상 1)

그래서 lease 만료 → 회수 → QUEUED → 재배정 → 또 실패가 **72h `TIMEOUT` 까지** 돌았다.
실측으로 Node 로그에 채널 불일치 **38건**이 그렇게 쌓였다. **운영에서 보이지 않는 상태다.**

**고친 것 — 세고, 멈추고, 남긴다**

- **센다** — `claim` 이 `attempt_no = (그 task 의 기존 배정 수) + 1` 을 적는다
- **멈춘다** — `capability.max_attempts`(기본 5 · 1–50). 상한에 닿은 task 는 `claim` 이 고르지
  않고, 워커가 `FAILED` 로 종결한다. `finished_at` 이 박히므로 입력 바이트 TTL 도 여기서 시작된다
- **남긴다** — Node 가 `POST /v1/internal/assignments/{id}/fail` 로 보고한다.
  배정은 즉시 `FAILED`, task 는 `QUEUED` 로 돌아가 **다른 기기가 시도**할 수 있다.
  실패 이유가 `audit_log` 에 들어간다 — **로그가 아니라 DB**
- **DB 가 마지막 방어선** — `assignment.capability_max_attempts` 스냅샷 + 복합 FK +
  `CHECK (attempt_no <= capability_max_attempts)`. 앱이 세고 DB 가 거절한다
- **`task_attempts_exhausted` 뷰** — 무엇이 왜 멈췄는지를 SQL 로 본다

`attempt_no` 와 `FAILED` 는 **v4.4 부터 스키마에 있었다.** 코드가 쓰지 않았을 뿐이다 —
`0009`(api_key) 때와 같은 모양이다.

**실측 (빈 볼륨 · 격리 프로젝트) 9/9**

게이트를 통과시킨 뒤 계약을 깨서(`32×32 RGB` → `16×16 L`) 실패를 강제했다.

| | |
|---|---|
| 정상 경로 | ✅ `attempt_no=1/5 SUCCEEDED` · `acc=0.8500` |
| 능력별 상한 지정 (`max_attempts: 3`) | ✅ |
| **시도 계수** | ✅ `1/3 · 2/3 · 3/3` 전부 `FAILED` — **정확히 3회** |
| **워커 종결** | ✅ `gc: exhausted=1` → task `FAILED` · `finished_at` 기록 |
| **재시도 정지** | ✅ 20초 뒤에도 배정 수 3 → 3 (**무한 루프가 멈췄다**) |
| 증적 | ✅ `audit_log` 에 `assignment.failed` 3건 · 이유 포함 |
| 상한 초과 배정 | ✅ DB 가 거절 (`assignment`) |
| 골든 경로 | ✅ `acc=0.8500` — `clean_room`·`prod_room` 동일 |

**`POST /v1/capabilities` 가 `max_attempts` 를 안 받고 있었다** — `max_input_bytes` 때와 같은
누락이라 첫 실행에서 상한 3 이 무시되고 기본 5 로 돌았다. 같이 노출했다.

회귀: `run_tests` 전부 통과 · 통합 검사 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

**남은 것** — 실패가 **일시적인지 영구적인지 구분하지 않는다.** 기기 재시작 같은 일시 장애도
계약 오류와 똑같이 시도를 소모한다. 상한을 5 로 둔 것이 그 완충이지만, 백오프나 오류 분류는 없다.


## lease 가 전처리를 나른다 — 검증과 실행이 같아진다 — 2026-08-13

`0014` 로 계약이 전처리를 선언하게 됐지만, 그 값은 **검증 시점에만** 쓰였다.
일반 실행(`node/_run`)은 여전히 `predict_image` 기본값(32×32 RGB)으로 돌았다 —
**lease 페이로드가 전처리를 나르지 않았기 때문이다.** `image.classify` 는 둘이 같은 값이라
차이가 없었지만, **다른 값을 선언한 능력이 생기면 「검증한 그것」과 「실행한 그것」이 갈라진다.**

**고친 것** — `arch`·`max_params` 를 나르는 바로 그 자리에 전처리도 싣는다.

- `NODE_ASSIGNMENTS_SQL` · `LEASE_DETAIL_SQL` 에 `JOIN capability` + `c.input_schema -> 'preprocess'`
- Node 폴링 경로가 `preprocess=a.get("preprocess")` 로 `predict_image` 에 넘긴다
- 없으면(legacy 능력) 종전 기본값으로 떨어진다

**수동 실행 경로의 구멍도 같이 닫았다.** `POST /v1/execute` 는 `_is_mine()` 으로 배정 여부만
**확인하고 행을 버렸다** — 그래서 `arch` 조차 Core 값을 안 쓰고 로컬 meta 로 떨어지고 있었다 (I1 위반).
`_my_assignment()` 로 바꿔 **행을 그대로 받아** `arch`·`max_params`·`preprocess` 를 전부 쓴다.

**실측 (빈 볼륨 · 격리 프로젝트) 8/8 — 판별 검사가 핵심**

`16×16 L` 을 선언한 능력을 만들어, 선언이 실행에 닿는지를 **반증 가능한 형태**로 확인했다.

| | |
|---|---|
| 검증 경로 — `16×16 L` 선언 | ✅ `RuntimeError: expected input[1, 1, 16, 16] to have 3 channels, but got 1` → **FAILED** |
| 선언만 `32×32 RGB` 로 고침 | ✅ 같은 모델·같은 샘플로 **PASSED** |
| **판별: 바인딩 후 선언만 `16×16 L` 로 되돌림** | ✅ task 가 `ASSIGNED` 에 머물고 Node 로그에 채널 불일치 **38건** |
| 골든 채점 | ✅ `acc=0.8500` — `demo`·`clean_room`·`prod_room` 전부 동일 |

판별 검사가 요점이다. lease 가 전처리를 **안** 날랐다면 기본값(32×32 RGB)으로 **조용히 성공**했을
것이다. 성공하지 않았다는 것이 「선언이 실행에 닿았다」는 증거다.

회귀: `run_tests` 전부 통과 · 통합 검사 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

**알아 둘 동작** — 계약이 모델과 맞지 않는 전처리를 선언하면 그 능력의 task 는 **실패를 반복한다**
(Node 폴링이 재시도하므로 로그에 38건이 쌓였다). lease 만료 후 워커가 회수하고, 끝내 72h 에
`TIMEOUT` 으로 종결된다. 계약 게이트가 그런 능력을 통과시키지 않으므로 정상 경로에서는
일어나지 않지만, **게이트 통과 후 계약을 고치면** 이 상태가 된다. 재시도 상한이 다음 후보다.


## B2 잔여 — `preprocess` 실수행 · 필수 checks 5 복귀 — 2026-08-13

`preprocess` 는 0013 에서 필수 항목에서 빠져 있었다. **계약에 그 값을 적을 자리가 없어서**
러너가 검증 없이 불린만 보냈기 때문이다. `infer.py` 는 32×32 RGB 를 **코드에 박아** 쓰고 있었고,
D3 는 「전처리는 계약의 일부」라고 말하는데 계약은 그것을 말하지 못했다.

**`input_schema.preprocess` 를 만들었다** (`mediaTypes` 와 같은 자리 · `0012` 와 같은 방식).

```json
{"preprocess": {"resize": [32, 32], "colorspace": "RGB"}}
```

- `0014` 가 `image.classify@1·@2` 에 선언을 붙인다 (jsonb 병합 · 멱등 · DDL 없음) · `seed.sql` 동반
- **선언값이 지금 하드코딩된 값과 같다.** 그래서 골든 경로의 픽셀 처리는 **바뀌지 않는다** —
  달라지는 것은 「그 값이 어디서 오는가」뿐이다
- `predict_image(preprocess=...)` — 주면 계약 선언대로, 안 주면 종전 기본값.
  골든 경로는 안 주는 길로 그대로 돈다
- 러너는 **선언을 읽어 적용한 뒤** 샘플 추론한다. 그게 도는 것이 `input_schema` 검증이다
- **`CONTRACT_CHECKS` 4 → 5.** 0013 에서 뺐던 이유(검증 없는 불린)가 사라졌다

**전처리 미선언 능력은 계약 게이트를 거절한다** (Decision accept).
`gate_run.capability_preprocess` 스냅샷 + `CHECK (kind <> 'contract' OR (… IS NOT NULL AND
jsonb_typeof(…) = 'object'))`. 샘플(`0013`)과 **같은 자리에 같은 방식**이다 — `capability` 에
CHECK 를 걸면 기존 볼륨에 선언 없는 ungated 능력이 있을 때 마이그레이션이 실패한다.
jsonb `null` 이나 문자열이 「선언했다」로 통하는 것도 막는다.

증적에 **무엇을 적용해 통과시켰는지**가 남는다 — 나중에 계약이 바뀌어도 이 증서의 근거는 고정된다.

**실측 (빈 볼륨 · 격리 프로젝트) 16/16**

| | |
|---|---|
| 러너 검증 5종 | ✅ `preprocess — 선언 적용: resize=[32, 32] colorspace=RGB` 포함 전부 OK |
| `contract_checks` 기록 | ✅ **5종** · 스냅샷 `{"resize": [32, 32], "colorspace": "RGB"}` |
| 전처리 미선언 능력 | ✅ **400** `ck_gate_run_contract_needs_preprocess` |
| arch 가 틀린 Agent | ✅ `FAILED` · acp 미발급 (회귀 유지) |
| **골든 채점 결과** | ✅ **`acc=0.8500 f1=0.8344`** — `clean_room`·`prod_room` 양쪽 동일 |

CI 가드 `check_quality_profile` 18 → **21/21** (미선언 · jsonb null · 객체 아님 3종 추가).
회귀: `run_tests` 전부 통과 · 통합 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

**남은 것** — 지금 선언은 **검증 시점에만** 적용된다. 일반 실행(`node/_run`)은 여전히
`predict_image` 기본값으로 돈다 — lease 페이로드가 전처리를 나르지 않기 때문이다.
`image.classify` 는 둘이 같은 값이라 차이가 없지만, **다른 값을 선언한 능력이 생기면 갈라진다.**
lease 에 전처리를 실어 보내는 것이 다음이다.


## B2 — 계약 검증을 러너가 실제로 수행한다 — 2026-08-13

계약 게이트(`kind='contract'`)는 러너가 보낸 `contract_checks` 가 전부 `true` 인지만 봤다.
**그 값을 아무도 계산하지 않았다** — 러너가 그냥 `true` 를 적어 보내면 통과였다.
D6(사전학습 허용)를 풀면 남의 가중치를 받는데, 그때 이 게이트는 도장만 찍는 절차가 된다.

**이제 러너가 실행해서 판정한다** (`app/contract_check.py` · 새 의존성 0)

| 항목 | 어떻게 |
|---|---|
| `arch` | Core 가 말한 arch 로 모델을 **세우고 가중치를 로드**한다. 구조가 다르면 로드가 깨진다 |
| `max_params` | 로드된 파라미터 수를 세어 상한과 비교 |
| `input_schema` | 계약 샘플로 **실제 추론**. 못 읽거나 못 돌리면 실패 |
| `output_schema` | 그 출력이 계약을 만족하는지 — closed-set 이면 라벨 집합까지 |

**샘플 = `task_input`** (Decision 1). `capability.sample_input_id` 가 **복합 FK 로 같은 능력의
입력만** 샘플이 되게 한다. 「무엇을 받는가」를 선언했으면 그 예시도 계약의 일부다.

**샘플 없는 계약 게이트런은 DB 가 거절한다** — `gate_run.sample_input_id` +
`CHECK (kind <> 'contract' OR sample_input_id IS NOT NULL)`. `START_SQL` 이 능력의 샘플을
스냅샷하므로, 샘플을 안 붙인 능력은 게이트런 자체가 시작되지 않는다.
「무엇을 근거로 통과시켰는가」가 증적에 남는다.

**샘플은 GC 대상이 아니다** — task 에 연결되지 않으므로 지금 규칙이면 `orphan-24h` 로 하루 만에
지워지고, 그러면 다음 게이트런이 검증을 못 한다. `task_input_purge_due` 에서 제외했다.
샘플은 「휘발성 작업 바이트」가 아니라 계약의 일부다.

**필수 항목을 5 → 4 로 줄였다** — `preprocess` 를 뺐다. 그 값은 러너가 **검증 없이 보내는
불린**이었고, 검증하지 않는 것을 필수로 요구하면 「도장은 찍혔는데 확인은 없다」가 된다.
보내오면 증적에 기록하되 통과 조건에서는 뺀다. 실수행이 들어올 때 다시 올린다 (Decision 3).

**`max_params` 도 Core 가 말한다** — `GET /v1/agents/{id}` 가 `agent_arch` 를 조인해 상한을
돌려준다. 게이트 시점에는 lease 페이로드가 없어 러너가 상한을 알 방법이 없었다 (I1 과 같은 이유).

**실측 (빈 볼륨 · 격리 프로젝트) 13/13**

| | |
|---|---|
| 샘플 없이 계약 게이트런 | ✅ **400** `ck_gate_run_contract_needs_sample` |
| 타 능력 입력을 샘플로 | ✅ 400 (복합 FK) |
| 샘플이 `purge_due` 에 없다 | ✅ (샘플 아닌 고아 입력은 대상) |
| **정상 검증** | ✅ `arch` 로드 · `94538 <= 2000000` · 샘플 추론 · `label='annual_crop'` 계약 만족 |
| **arch 가 틀린 Agent** | ✅ `state_dict` 로드 실패 → **`FAILED`** · **acp 미발급** (golden 과 같은 규약) |
| `GET /v1/agents/{id}.max_params` | ✅ `2000000` |
| golden 경로 `demo.sh` | ✅ rc=0 |

**CI 가드도 고쳤다** — `check_quality_profile` 이 18/18 로 늘었다. `0013` 이후 여러 검사가
**엉뚱한 제약(`ck_gate_run_contract_needs_sample`)으로 통과**하고 있었다. 샘플을 붙여 의도한
제약이 발동하게 고쳤고, 「샘플 없는 계약 게이트런 거절」을 새 불변식으로 추가했다.

회귀: `run_tests` 전부 통과 · 통합 검사 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

**남은 것** — `preprocess` 실수행. 그리고 계약 검증은 여전히 **러너를 신뢰**한다
(절대규칙 8 이 그 근거다). 러너가 거짓 보고를 못 하게 하려면 재현 가능한 실행 증명이 필요한데,
그건 TEE 없이는 이 세대 밖이다.


## B1 핫픽스 — MIME 선언 강제 · 업로드 디스크 스트리밍 — 2026-08-13

#47 리뷰 Decision 2·3. (1) `max_input_bytes` 불변/`@version` 은 **accept** — 코드 변경 없음.

**① MIME 미선언이면 업로드를 거절한다 (Decision 2)**

`assert_media_type` 은 계약이 `input_schema.mediaTypes` 를 선언한 경우에만 대조하고
**선언이 없으면 통과**시켰다. 「계약이 안 정한 것을 코드가 정하지 않는다」는 뜻이었는데,
결과는 **아무 MIME 이나 받는 구멍**이었다 — D8′(비통제 수집 금지)와 어긋난다. 이제 거절한다.

그러면 기존 능력이 선언을 갖고 있어야 한다 — 안 그러면 **유일한 실사용 능력에 업로드가 막힌다.**
`0012` 가 `image.classify` 에 `["image/jpeg"]` 를 선언한다 (jsonb 병합 · 멱등 · DDL 없음).
골든셋이 JPEG 이고 실측한 것도 JPEG 뿐이라 **그것만** 선언한다 — PNG 등은 그 형식으로 실제
추론을 돌려 본 뒤에 계약에 추가한다.

`@2` 로 올리지 않은 이유: D3(전처리는 계약의 일부)는 **채점·실행 조건을 바꿀 때**의 규칙이다.
여기서 한 것은 이미 사실인 것을 **명시**하는 추가이고, 전처리·골든셋 해시·임계값을 건드리지
않았다. 새 형식을 **허용**할 때는 그때 버전을 올린다.

`caseId` 데모 경로는 이 규칙 밖이다 — 업로드가 없다.

**② 업로드를 디스크로 흘린다 (Decision 3)**

청크를 메모리에 모은 뒤 파일로 썼다. 상한이 256MiB 라 최악의 경우 그만큼 상주했고, 동시
업로드 몇 건으로 Core 가 죽는다. 이제 **받는 즉시 쓴다** (`store_stream` 을 async 로).

**실측 — 200MB 업로드에 Core 최대 상주 메모리 증가 0MB** (`VmHWM` 65,420 → 65,804 kB).
그래서 `core` 에 `mem_limit` 을 걸지 않았다. 상한은 메모리가 아니라 디스크에만 걸린다.

**실측 (빈 볼륨 · 격리 프로젝트) 10/10**

| | |
|---|---|
| `0012` 가 `@1`·`@2` 에 `mediaTypes` 선언 | ✅ |
| 선언된 `image/jpeg` | ✅ 200 · 해시 일치 |
| 선언 안 된 `image/png` | ✅ **400** |
| **`mediaTypes` 미선언 능력에 업로드** | ✅ **400** |
| 200MB 업로드 | ✅ 200 · **메모리 증가 0MB** |
| 1KiB 한도 초과 | ✅ 413 (스트리밍 중 끊음) |
| 업로드 바이트로 Node 완주 | ✅ `COMPLETED` |
| 데모 경로 `demo.sh` | ✅ rc=0 |

회귀: `run_tests` 전부 통과 · 통합 검사 7/7 · `clean_room` 9/9 · `prod_room` 14/14.


## B1 런타임 — Core 가 입력을 받아 Node 로 보낸다 (D22) — 2026-08-13

`0011`(#46)이 DDL 을 세웠고, 이 커밋이 **바이트를 실제로 움직인다.** 브리지 Decision
(`topic: B1-task-input`)에 Confirm 후 구현 — 범위는 **API · Node 전달 · GC**.

**이제 되는 것**

```bash
curl -X POST 'localhost:8000/v1/inputs?capability=image.classify&version=1' \
     -H 'content-type: image/jpeg' -H "Authorization: CapNet-Key $KEY" \
     --data-binary @my.jpg          # → {id, sha256, byte_size, storage_state}
curl -X POST localhost:8000/v1/tasks -d '{"inputId":"<id>", ...}'
```

Node 가 그 바이트를 받아 추론한다. **골든셋 40장 밖의 데이터가 처음으로 흐른다.**

**설계**

- **자유 업로드가 아니다** (D8′). 입력은 수집 시점에 능력에 묶이고, 크기는 계약이 정하며
  (DB 가 판정), MIME 은 계약이 선언한 `input_schema.mediaTypes` 와 대조한다
- **새 의존성 0** — `python-multipart` 를 피하려고 multipart 대신 raw body 스트리밍을 쓴다.
  `content-type` 이 media_type 이다. 상한은 **읽는 도중에** 끊는다 (다 받아 놓고 거절하면
  256MiB 를 이미 올린 뒤다)
- **Node 는 lease 가 있어야 바이트를 받는다.** 증서만으로 내려주면 등록된 기기 전부가 남의
  데이터를 읽는다 — 「승인 도메인 안으로만 간다」가 무너진다. `GET /v1/internal/inputs/{id}/bytes`
  는 살아 있는 lease 를 확인한다
- **Node 가 해시를 직접 대조한다.** 전송 중 바뀐 바이트로 추론하면 증적의 sha 와 실행한
  바이트가 달라진다. 다르면 422
- **Node 에 남기지 않는다** — 실행이 끝나면 임시 파일을 지운다
- **바이트는 별도 볼륨** `capnet_inputs`. 증적 DB(`capnet_pg`)와 백업 정책을 분리한다
- `capability.max_input_bytes` 를 `POST /v1/capabilities` 로 정할 수 있게 했다 —
  없으면 한도를 조정할 방법이 아예 없었다
- 데모 경로 유지 — `inputId` 가 없으면 종전 `caseId` → Node 로컬 골든셋

**GC** (`CORE_GC_INTERVAL_S` 기본 300초)

- 정책은 코드가 아니라 `task_input_purge_due` 뷰가 갖는다 — 무엇이 왜 언제 지워지는지 SQL 로 본다
- 72h 미완료 task 를 `TIMEOUT` 종결 → 그때부터 7일
- **바이트만 지우고 행은 남긴다.** `task.finished_at` 을 완료 시 기록한다 (TTL 기준)
- 즉시 삭제 `POST /v1/inputs/{id}/purge` (admin) — 사고·고객 요청용

**실측 (빈 볼륨 · 격리 프로젝트) 14/14**

| | |
|---|---|
| 업로드 | ✅ Core 가 잰 sha = 로컬 sha |
| content-type 없음 · 없는 능력 | ✅ 400 · 404 |
| 1KiB 한도 능력에 3381B | ✅ **413** |
| @1 입력을 @2 task 에 | ✅ 400 `task_input_capability_fkey` |
| **Node 가 업로드한 바이트로 완주** | ✅ `COMPLETED` · 증적 `sha=185b6d75bede… 3381B` |
| lease 없는 Node | ✅ **403** |
| 종결 후 7일 전 | ✅ 보존 (만료 대상 0건) |
| 8일 경과 후 GC | ✅ `purged=1 freed=3381` · 디스크 **GONE** · 행은 남음 |
| PURGED 입력 재사용 | ✅ 409 |
| 데모 경로 `demo.sh` | ✅ rc=0 |

회귀: `run_tests` 전부 통과 · 통합 검사 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

**알게 된 제약** — 입력이 하나라도 들어온 뒤에는 `max_input_bytes` 를 **바꿀 수 없다.**
`task_input` 이 `capability (id, max_input_bytes)` 를 복합 FK 로 참조하므로 UPDATE 가 거절된다.
「어떤 계약 아래 수집됐는지」가 사후에 안 바뀌는 것이라 의도에 맞고, 바꾸려면 새 `@version` 을 만든다.

**브리지** — `docs/bridge/` 를 origin 에 올린다. Windows 클론이 3커밋 뒤처져 리뷰어가 D20·B0·0011 을
못 본 상태로 Decision 을 썼다. 이제 양쪽이 같은 우편함을 쓴다.

## B1 DDL — `0011` task_input · Core 중개 입력 수집 (D22 · D8′) — 2026-08-12

**Core→Node 로 바이트가 전송되지 않는다.** Node 는 `caseId` 로 미리 마운트된 골든셋 40장 중 하나를
고를 뿐이다. 「내 데이터를 남의 기계에 보내면서 어디로 갔는지 답할 수 있는가」가 제품 문구인데
**내 데이터를 보낼 수가 없었다.** 그 첫 칸.

**원칙** — 증적 = 해시·누가·어디로 · **바이트 = 휘발성 작업 저장소.**
바이트를 지워도 `task_input` 행은 남는다. 그래야 나중에도 「어디로 갔는지」에 답한다.
바이트는 DB 가 아니라 별도 볼륨에 둔다 — 「백업에서 입력 바이트는 빼고 증적 DB 는 넣는다」와 맞물린다.

**확정된 숫자** (전부 DB 제약으로)

| | |
|---|---|
| 크기 | 기본 **32MiB** · capability 별 `max_input_bytes` · 절대 상한 **256MiB** |
| 보존 | 종결 후 **7일** · 고아 입력 **24h** · 미완료 task 최대 수명 **72h** |
| GC | Core 워커 주기 삭제가 본경로 (+ 선택적 즉시 purge) |

**설계 요점**

- **입력은 수집 시점에 능력에 묶인다** (D8′ 「계약된 ingest」). `task` 의 복합 FK
  `(input_id, capability_id) → task_input (id, capability_id)` 가 **다른 능력의 입력을 끌어다 쓰는 것을
  막는다** — 계약이 다르면 검증도 달랐기 때문이다
- **크기는 앱이 재지 않는다.** `capability_max_input_bytes` 스냅샷 + 복합 FK + `CHECK (byte_size <= …)`.
  스냅샷만 크게 적어 위조하는 것도 FK 가 막는다
- **`task.finished_at` 추가** — 「완료 후 7일」의 기준이 없었다. `updated_at` 은 claim 회수에서도
  갱신되므로 TTL 기준이 될 수 없다
- **`task_input_purge_due` 뷰** — 무엇이 왜 언제 지워지는지를 사람이 본다. 정책이 워커 코드 안에만
  있으면 보이지 않는다
- 사용자끼리 **중복 제거하지 않는다** — 같은 바이트라도 소유자·신뢰도메인이 다르면 다른 입력이다
- 데모 경로 유지 — `caseId` 만 있는 요청은 `input_id` 가 NULL 이고 바이트도 TTL 도 없다

추가만 — 테이블 1 · 뷰 1 · 컬럼 4 · CHECK 6 · UNIQUE 3 · FK 3. 삭제·완화 0.

**실측 (빈 볼륨 · 격리 프로젝트) 15/15**

| | |
|---|---|
| 기존 능력이 기본 32MiB 로 채워짐 | ✅ 동작 불변 |
| 512MiB 계약 | ✅ 거절 (`capability`) |
| 계약보다 큰 입력 · 스냅샷 위조 · sha 형식 · size 0 | ✅ 전부 거절 (`task_input`) |
| `PURGED` 인데 시각 없음 | ✅ 거절 · 정상 삭제 후 **행은 남음** |
| **@2 입력을 @1 task 에 붙이기** | ✅ 거절 (`task`) · 같은 능력끼리는 통과 |
| 진행 중 task 에 `finished_at` | ✅ 거절 (`task`) |
| `task_input_purge_due` | ✅ `stale-72h · due=…` |
| 멱등 | ✅ `적용할 것 없음 (최신 = 0011)` · verify 11/11 |

회귀: `run_tests` 전부 통과 · 통합 검사 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

**아직 런타임이 없다** — 업로드 엔드포인트 · 바이트 저장소 · lease 전달 · GC 워커.
지금은 DDL 과 제약만 섰고, **Core→Node 바이트 전송은 여전히 없다.**

## B0 — task 가 요청자와 신뢰 도메인을 기록한다 (D23) — 2026-08-12

**「누가 무엇으로 실행했는지 증적이 남는다」의 절반이 비어 있었다.**

```python
user = conn.execute("SELECT id FROM app_user WHERE id = %s", (SEED_ADMIN_ID,))  # 항상 seed admin
SELECT %(user_id)s, c.id, 'QUEUED', 'team', ...                                 # 'team' 리터럴
```

- 모든 task 가 **seed admin 소유**였다. `_actor()` 는 P1 부터 API 키로 요청자를 알고 있었는데
  그 값을 **버리고** 있었다
- `trust_domain` 이 고정이라 **tenant 유통이 구조적으로 불가능**했다. `image.classify@2`(min=tenant)를
  0006 에서 만들어 두고도 tenant task 를 만들 방법이 없었다

**고친 것**

- `user_id` = `_actor()["user_id"]`. 키 없는 경로(강제 꺼진 데모)에서만 seed admin 으로 떨어진다 —
  그때는 「누가 요청했는지 모른다」가 사실이고, 그 사실이 기록되는 것이다
- `trust_domain` 을 요청자가 지정 (`trustDomain`, 기본 `team` — 종전 동작)
- **호환은 앱이 검사하지 않는다.** `task` 의 복합 FK
  `(capability_trust_domain_min, trust_domain) → domain_min_compatible` 이 판정하고,
  앱은 `ForeignKeyViolation` 을 400 으로 옮기며 어느 제약이 거절했는지 그대로 보여 준다

**실측 (강제 모드 · 빈 볼륨 · 격리 프로젝트) 11/11**

| | |
|---|---|
| alice 키로 만든 task | ✅ **alice 소유** (seed admin 아님) |
| admin 키 | ✅ 다른 소유자 — 섞이지 않는다 |
| 무인증 | ✅ 401 (P1 유지) |
| 기본 `trust_domain` | ✅ `team` (종전 동작) |
| `image.classify@1`(min=team) + tenant · public | ✅ **400** `task_capability_trust_domain_min_trust_domain_fkey` |
| `image.classify@2`(min=tenant) + tenant · team | ✅ 200 (rank 3 ≥ 2) |
| 모르는 도메인 | ✅ 400 |
| 증적 조회 | ✅ `alice · tenant · ic1-0007` — 누가·어느 도메인으로 |

회귀: `run_tests` 전부 통과 · 통합 검사 7/7 · `clean_room` 9/9 · `prod_room` 14/14.

**결정 기록** — D8′(비통제 수집 금지로 재해석) · D22(입력 경로 = Core 중개 2안) · D23(B0).
다음은 **B1: `task_input`** — 지금도 Node 는 `caseId` 로 로컬 골든셋을 고를 뿐,
Core→Node 바이트 전송은 **여전히 없다.**

## 계약 게이트 런타임 — 게이트 없는 능력이 실제로 라우팅된다 — 2026-08-12

`0010` 이 DDL 을, 앞 커밋이 `POST /v1/capabilities` 를 세웠다. 남은 것은 **Agent 를 붙이는 길**이었다.

- **종류는 능력이 정한다.** `START_SQL` 이 `CASE WHEN c.quality_profile='none' THEN 'contract'
  ELSE 'golden' END` 로 `kind` 를 뽑는다. 앱이 고르지 않으므로 golden 능력에 계약 게이트런을
  붙이는 경로가 애초에 없다 (DB 복합 FK 는 그 뒤의 방어선)
- **계약 게이트는 채점하지 않는다.** 대신 러너가 무엇을 확인했는지를 요구한다 —
  `input_schema` · `output_schema` · `preprocess` · `arch` · `max_params`. 하나라도 빠지거나
  `true` 가 아니면 PASSED 를 주지 않는다. 「무엇을 근거로 붙었는가」가 `result_summary` 에 남는다
- **골든 통계는 애초에 받지 않는다.** `ck_gate_run_contract_no_golden_stats` 가 DB 에서도 막지만
  앱에서 먼저 400 을 준다 — 「점수를 보냈는데 조용히 사라졌다」가 되면 안 된다
- 반대 방향도 막는다: golden 게이트에 `contract_checks` 를 보내면 400
- `finish`·`get` 응답에 `kind` 를 실었다. `start` 만 주고 `finish` 는 안 주는 것은 비일관이었다

**실측 (빈 볼륨 · 격리 프로젝트) 10/10**

| | |
|---|---|
| ungated 능력 등록 → 게이트런 시작 | ✅ `kind=contract` **자동 결정** |
| contract + 골든 통계 | ✅ 400 |
| `contract_checks` 없음 / 일부 누락 / 하나가 false | ✅ 전부 400 (`contract check not satisfied: max_params`) |
| 전부 확인 보고 | ✅ 200 · `scored_by=contract-v1` |
| **라우팅 증서** | ✅ `text.embed@1 profile=none 근거=contract` |
| golden 게이트에 `contract_checks` | ✅ 400 |

회귀: `run_tests` 전부 통과 · 통합 검사 7/7 · `clean_room` 9/9.

**D20 런타임 완료.** 이제 골든셋 없이 능력을 만들고 Agent 를 붙여 라우팅까지 갈 수 있다.
남은 것은 계약 검증을 **러너가 실제로 수행**하는 것 — 지금은 러너의 보고를 Core 가 받아 적는다.
보고 자체를 검증하지는 않으므로, 러너를 신뢰하는 만큼만 믿을 수 있다 (절대규칙 8 이 그 신뢰의 근거다).

## ② 게이트 선택화 — `0010` 품질 프로파일 (D18 코드 정합) — 2026-08-12

**D18 은 게이트를 «선택적 품질 프로파일» 로 내렸는데 코드가 따라오지 않았다.** 스키마가 게이트를 **6층으로**
강제하고 있었다.

```
capability(golden_set_ref/sha256/size/metrics — 전부 NOT NULL)
  gate_run(PASSED · golden_set_sha256 NOT NULL · CHECK runner_is_gate_runner)
    → gate_run_passed → agent_capability(PASSED ⇒ gate_run_id NOT NULL)
      → agent_capability_passed → assignment (FK)
```

그래서 **새 능력마다 골든셋 40장 + 채점기**가 필요했고 제품이 `image.classify@1` 하나에 묶여 있었다.
`claim.py` 의 JOIN 만 빼는 것으로는 안 된다 — `assignment` 의 FK 가 `agent_capability_passed` 를 참조하므로
INSERT 가 FK 에서 거절된다.

**해법 — 계약 바인딩도 게이트런이다.** 사슬을 끊지 않고 «골든셋 0장짜리 게이트런» 을 하나 더 인정한다.

- `capability.quality_profile` (`golden` | `none`) — `none` 이면 `golden_set_*` 는 **센티널**이고
  CHECK 로 강제된다. **NOT NULL 을 해제하지 않았다.** 읽는 쪽은 숫자가 아니라 프로파일을 먼저 본다
- `gate_run.kind` (`golden` | `contract`) + `capability_quality_profile` 스냅샷 · 복합 FK 로 실제 값과 묶음
- 계약 검증도 **team gate-runner 가 한다** — `runner_is_gate_runner` CHECK 그대로 통과 (절대규칙 8).
  Core 가 스스로 판정을 만들면 「실행과 판정의 분리」가 무너진다
- **`claim.py`·`assignment` FK 는 한 줄도 안 고쳤다.** contract 게이트런이 기존 경로로 증서를 올리므로
  라우팅은 지금 그대로 돈다

추가만 — 컬럼 3 · CHECK 4 · UNIQUE 1 · FK 1. 삭제·완화 0. 러너 정적 검사 10/10 OK.

**실측 (빈 볼륨 · 격리 프로젝트) 10/10**

| | |
|---|---|
| 기존 데이터 | `image.classify@1·@2` → `golden` · 기존 gate_run → `golden` (동작 불변) |
| ungated 능력 생성 | ✅ 센티널 갖춰야만 |
| none 인데 진짜 골든셋 / golden 인데 센티널 / 모르는 프로파일 | ✅ 전부 **거절** (`capability`) |
| golden×contract · none×golden · contract+골든점수 · 러너 아닌 Node | ✅ 전부 **거절** (`gate_run`) |
| 정상 contract 사슬 | ✅ `text.embed@1 profile=none · 근거 kind=contract` 로 **acp 발급** |
| 멱등 | ✅ `적용할 것 없음 (최신 = 0010)` · verify 10/10 체크섬 일치 |

README 102행의 「게이트 미통과 Agent 에는 할당할 수 없다」를 `product-distribution.md` 문구
(「게이트를 **붙인** Capability 에서는」)에 맞췄다. 결정은 D20.

**아직 없는 것** — ungated 능력을 **만들고 계약을 검증하는 런타임**. 지금은 DDL 과 제약만 섰다.
`POST /v1/capabilities` 와 gate-runner 의 contract 검증기가 다음 작업이다.

## P1 정문 — 제품 프로파일 (강제 모드가 기본) — 2026-08-12

**목표가 대회 출품에서 제품으로 바뀌었다.** 대회 일정에 맞춰 미뤄뒀던 것을 순서대로 닫는다. 그 첫 칸.

지금까지 제품 배포를 막던 것은 코드가 아니라 **기본값**이었다. `REQUIRE_API_KEY` · `REQUIRE_NODE_CREDENTIAL`
이 둘 다 `0` 이라 관리 API 쓰기 12개가 열려 있었고, 시스템이 스스로 `/v1/ops/status` 에서 `ok: false` 와
`"관리 API 키가 없다 — 강제를 켜면 잠긴다"` 를 내고 있었다.

**`compose.prod.yaml` 오버레이** — 데모 기본값을 건드리지 않고 제품 기본값을 따로 둔다.

| | 데모 | 제품 |
|---|---|---|
| 관리 API 인증 | 꺼짐 | **강제** |
| Node 증서 | 꺼짐 | **강제** |
| postgres | 호스트 5432 공개 | **비공개** |
| 마이그레이션 | 자동 | **끔** (운영자가 시점을 잡는다) |
| DB 비밀번호 | 기본값 `capnet` | **`.env` 필수** — 없으면 기동 거부 |
| seed Node 3대 | 뜬다 | **안 뜬다** (`profiles: demo`) |

**같이 막힌 것 하나** — 인증을 켜면 운영 스크립트가 전부 401 이었다. `scripts/*.sh` 중 키를 보내는 것이
하나도 없었다. `scripts/lib/http.sh` 의 `ccurl` 로 한 곳에서 헤더를 붙인다 (7개 스크립트 · 39개 호출).
키는 환경변수(`CAPNET_API_KEY`) 또는 **파일**(`CAPNET_API_KEY_FILE`)로 받는다 — 인자로 받으면 `ps` 에 남고,
환경변수는 `docker inspect` 에 뜬다. `/health` 호출은 인증 없이 그대로 둔다.

**증서 주입 경로도 없었다** — compose 에 Node 증서를 넣을 방법이 없어 강제 모드를 증명할 수조차 없었다.
`compose.prod.yaml` 이 `data/node-secrets` 를 `/secrets` 로 마운트하고 `NODE_CREDENTIAL_FILE` 을 준다.

**실측 — `scripts/prod_room.sh` (제품 수용 게이트, 빈 볼륨·격리 프로젝트) 14/14**

| | |
|---|---|
| postgres 호스트 미노출 · 자동 마이그레이션 꺼짐 | ✅ |
| 무인증 `POST /v1/nodes` · `/v1/agents` · 가짜 키 | ✅ **401** |
| CLI 부트스트랩 → admin 키로 쓰기 | ✅ **200** |
| 증서 없는 Node 의 `assignments` | ✅ **401** (사칭 차단) |
| 증서 넣은 Node 하트비트 | ✅ `fresh` |
| **강제 모드에서 `demo.sh` 완주** | ✅ `PASSED acc=0.8500` · 증적 SUCCEEDED |

데모 경로 회귀 — `clean_room.sh` **9/9 유지**. `run_tests.sh` 전부 통과.

**발견 (미해결)** — 본문 검증이 인증보다 먼저 돈다. 잘못된 스키마로 부르면 인증 없이 `422` 가 온다.
쓰기는 일어나지 않지만 스키마 유효성 오라클이 된다. 공개망에서는 앞단 rate limit 이 필요하다.

**다음** — P2 시크릿 위생 · P3 lease 재할당·모니터링 · P4 배포 산출물(태그·digest 핀·백업) ·
P5 대회발 제약 해제(D6 사전학습 금지 폐지 등). 한계는 [`operate-production.md`](../guide/operate-production.md) §3.

## SBOM 드리프트 · torch 핀 (F4 2차 라이선스 검증) — 2026-08-12

**제출용 라이선스 명세서가 실제 빌드와 어긋나 있었다.** 둘 다 2차 검증(F4)이 직접 보는 산출물이다.

- `sbom.json` 에 **`psycopg-pool` 3.3.1 (LGPL-3.0) 이 없었다.** SBOM 생성 08-06, 의존성 추가 08-11 —
  `THIRD-PARTY-LICENSES.md` 에는 들어갔는데 SBOM 만 갱신되지 않았다. **LGPL 항목을 빠뜨린 명세서**를 낼 뻔했다
- `apps/node/Dockerfile` 이 `pip install torch torchvision` 을 **무버전**으로 돌렸는데,
  붙임1 표는 `2.13.0+cpu` · `0.28.0+cpu` 로 단언하고 있었다. 심사 PC 에서 재빌드하면 달라질 수 있다
- `check_submission.py` 는 requirements → `THIRD-PARTY-LICENSES.md` 만 대조하고 `sbom.json` 내용은 보지 않는다.
  그래서 20/20 을 통과한 채로 드리프트가 살아 있었다

**고친 것**

- `ARG TORCH_VERSION=2.13.0+cpu` · `ARG TORCHVISION_VERSION=0.28.0+cpu` — Dockerfile 이 **버전 정본**이 된다.
  `generate_sbom.sh` · `.ps1` 이 그 ARG 를 읽어 쓰므로 두 곳에 적어 어긋날 일이 없다
- `sbom.json` 재생성 — 10 → **11 컴포넌트**. `psycopg-pool 3.3.1` 추가, torch/torchvision 에 버전이 붙었다
  (호스트에 pip 이 없어 `python:3.11-slim` 컨테이너에서 같은 스크립트로 생성)
- 붙임1 표 10 → 11 행 (LGPL 먼저 순서 유지) + 버전 정본 위치 명시

**실측** — `docker build --no-cache --build-arg INSTALL_TORCH=true` 가 rc=0 이고
설치본이 `2.13.0+cpu 0.28.0+cpu` 로 나오는 것을 확인했다. 핀이 실제로 해석된다.

**남은 위험** — `sbom.json` 드리프트를 막는 기계 검사는 아직 없다. 다음 의존성 변경에서 같은 일이 반복될 수 있다.

## 새 볼륨 재현 결함 — compose 일회성 migrate — 2026-08-12

**README 대로 하면 `demo.sh` 가 실패했다.** 빠른 시작에 마이그레이션 단계가 없었다.

- 새 볼륨은 initdb 가 `docs/spec/schema.sql`(최종 수정 08-03)까지만 넣는다. 그 뒤 세대인
  `0007 node_credential` · `0008 agent_arch` · `0009 api_key_hardening`(전부 08-11)은 `migrations/` 에만 있다
- `compose.yaml` 에 적용 단계가 없고 앱 기동에도 없어서, **자동 적용 경로가 0** 이었다
- `clean_room.sh` 가 9/9 로 통과한 것은 그 스크립트가 `migrate up` 을 명시적으로 돌리기 때문이다.
  README 경로는 아무도 돌리지 않고 있었다 — README 의 "2026-08-09 확인" 은 0007~0009 이전이다

**실측 (빈 볼륨 · 격리 프로젝트 · 최신 이미지)**

| | 수정 전 | 수정 후 |
|---|---|---|
| `agent_arch` · `node_credential` · `schema_migration` | 전부 없음 | 존재 |
| `agent.arch` 컬럼 | 없음 | 존재 |
| `GET /v1/internal/nodes/{id}/assignments` | **500** `UndefinedTable: relation "agent_arch" does not exist` | 200 |
| `GET /v1/ops/status` | **500** | 200 · `schema_version=9` |
| `demo_violations.sh` · `sanity.sh` | rc=0 | rc=0 |
| `demo.sh` | **rc=22** (`POST /v1/agents` → `UndefinedColumn: column "arch" of relation "agent"`) | rc=0 · `PASSED acc=0.8500` |

`demo.sh` 는 `curl -sf` 라 500 을 받으면 **아무 메시지도 없이** 죽는다. 심사자가 보는 것은 무출력 실패다.

**고친 방법 — 일회성 `migrate` 서비스** (`postgres` 뒤 · `core` 앞, `service_completed_successfully`)

- **앱 기동 시 자동 DDL 을 넣지 않았다.** 마이그레이션 시점은 앱이 정할 일이 아니라 운영자가 잡는다.
  서비스로 두면 명시적으로 남고 로그도 `docker compose logs migrate` 로 따로 본다
- `CAPNET_AUTO_MIGRATE=0` 이면 즉시 0 으로 빠진다 — 제품 배포는 이걸로 끄고 `scripts/migrate.sh up` 을 직접 돌린다
- postgres 헬스체크는 initdb 중에도 유닉스 소켓으로 통과할 수 있다 (그때 TCP 는 닫혀 있다).
  그래서 healthy 만 믿지 않고 `migrate status` 가 baseline 을 볼 때까지 기다린 뒤 적용한다
- 새 의존성 0 · 앱 코드 변경 0

**남은 것** — `sbom.json` 에 `psycopg-pool` 누락, torch/torchvision 미핀. 2차 라이선스 검증(F4) 트랙이라 따로 간다.

## DB 커넥션 풀 (SD-017 해소) — 2026-08-11

바로 앞 커밋에서 「측정만 남기고 미룬다」고 했던 것을 **master 결정으로 지금** 한다.
우려(촬영 12일 전 · 핵심 배관 · 새 의존성)는 기록으로 남기고 진행했다.

- `psycopg-pool==3.3.1` — psycopg 저자들의 공식 동반 패키지 (LGPL-3.0 · THIRD-PARTY 등재)
- **호출부를 바꾸지 않았다.** `with get_conn() as conn:` 과 커밋/롤백 규약이 그대로다
- **폴백이 있다** — 풀이 꺼져 있거나(`DB_POOL=0`) `psycopg_pool` 을 못 불러오면 예전 방식으로 떨어진다.
  두 경로 모두 실측 확인
- `GET /v1/ops/status` 에 풀 상태 노출 · 꺼져 있으면 경고

### 같은 조건 재측정

| 항목 | before | after |
|------|--------|-------|
| `GET /health` (DB) | 15.2ms | **3.8ms** |
| DB 없는 요청 | 3.3ms | 3.0ms |
| 30건 / 동시 10 | 5.35/s · e2e 1.60s | 5.84/s · e2e **1.23s** |
| 100건 / 동시 25 | 5.44/s · e2e 4.51s | **12.38/s** · e2e **1.94s** |
| 실 스택 `GET /health` | 14.6ms | **3.8ms** |

**DB 요청이 DB 없는 요청과 거의 같아졌다** (3.8 vs 3.0ms) — 커넥션 비용이 사라졌다.
그리고 **포화가 풀렸다**: before 는 부하를 3배 올려도 5.4/s 로 평평했는데 after 는 늘어난다.

회귀 — 통합 6종 · 깨끗한 환경 재현 9/9 · 실 사슬 정상.

**주의:** 풀은 프로세스 안에서만 공유된다. uvicorn 워커를 늘리면
`DB_POOL_MAX × 프로세스 수` 가 postgres `max_connections` 를 넘지 않게 한다.

## 성능 실측 · 운영 조회면 (SD-017 · SD-018) — 2026-08-11

이 시스템의 성능은 **한 번도 측정된 적이 없었다.** 「측정 없이 주장 없음」에 정면으로 걸린다.

- **`scripts/load_probe.py`** — 제출→배정 / 배정→완료 / e2e 를 나눠 잰다.
  느리면 **어디가** 느린지 알아야 하기 때문이다. 일회용 스택에서 돌린다
- **`GET /v1/ops/status`** — 큐·lease·함대·증서·드리프트·arch·강제 플래그를 한 번에.
  숫자만이 아니라 **판정(warnings)까지** 준다

### 실측 결과 (일회용 스택)

| 부하 | 처리량 | e2e p50 |
|------|--------|---------|
| 30건 / 동시 10 | 5.35 건/초 | 1.60s |
| 100건 / 동시 25 | 5.44 건/초 | **4.51s** |

**처리량이 평평하고 지연만 는다** — 포화다. 원인을 분해했다:

| 구간 | p50 |
|------|-----|
| 커넥션 수립 | **10.8ms** |
| `claim_next` (실제 일) | **0.7ms** |
| `reclaim_expired` | 1.8ms |
| DB 여는 API 요청 | 14~15ms |
| DB 없는 API 요청 | **3.3ms** |

**커넥션 풀이 없다** (SD-017). 실제 일보다 커넥션이 15배 비싸다.
`psycopg_pool` 이 답이지만 **새 의존성**이고 촬영 12일 전 핵심 배관이라, 측정만 남기고 미룬다.

> **오귀속 정정:** 처음엔 `reclaim_expired` 를 44ms 로 지목했는데 측정 오류였다 —
> 커밋 없이 한 트랜잭션에 누적해 쟀다. 워커와 동일 조건으로 재니 1.8ms 다. 기록에 남긴다.

조회면은 붙이자마자 실제 문제 2건을 잡았다 (arch 미결속 라우팅 가능 · 관리 키 없음).

## 관리 API 인증 — 정문을 닫는다 (SD-010 해소) — 2026-08-11

**실측으로 드러난 것:** 익명 요청이 `team`·`L등급`·**게이트러너** Node 를 등록하고(HTTP 200)
증서까지 받았다(HTTP 200). 게이트러너가 되면 **자기 Agent 를 자기가 채점해 통과시킬 수 있다** —
FK 사슬·증적·Node 증서가 전부 그 위에 쌓은 심층 방어인데 정문이 열려 있었다.
SD-010 이 「Core API 에 인증이 없다」고 적었고 P2-4 는 그중 Node 사칭만 닫았다.

**스키마가 이미 예견해 뒀다.** `app_user(role IN ('user','developer','admin'))` 과 `api_key` 가
v4.4 부터 있었고 **코드가 쓰지 않았을 뿐**이다. 새 테이블을 만들지 않았다.

- `apps/core/app/apikey.py` — 발급·검증·폐기·역할 판정. 평문은 발급 때 한 번, DB 엔 sha256 만
- **역할 순위를 표로 판정한다** (`user < developer < admin`) — 문자열 정렬은 `compute_tier` 에서
  이미 당한 함정이다
- 쓰기 엔드포인트 **11개**에 최소 역할 부여 — Node 등록·증서·계약 생성·폐기·claim 은 `admin`,
  Agent·바인딩·**gate_run 기록**은 `developer`, Task 는 `user`
- **두 신원이 공존한다** — `CapNet-Node`(기기) · `CapNet-Key`(사람/도구). 섞이지 않는다
- **부트스트랩 CLI** `python -m app.apikey_cli issue` — API 로만 발급하면 첫 키를 못 만들어 잠긴다
- `migrations/0009` — `key_prefix` UNIQUE · `last_used_at` · `api_key_status` 뷰 (추가만)
- `GET /v1/api-keys` (admin) — 시크릿도 해시도 나가지 않는다

**강제는 플래그** (`REQUIRE_API_KEY`, 기본 꺼짐 — 데모 보호). 다만 **키가 오면 항상 검증한다**:

| | 익명 | 위조 키 | user 키 | admin 키 |
|---|---|---|---|---|
| 기본 모드 · Node 등록 | 200 | **401** | **403** | 200 |
| 강제 모드 · Node 등록 | **401** | **401** | **403** | 200 |
| 강제 모드 · gate_run 기록 | **401** | — | **403** | 200 |
| 강제 모드 · Task 생성 | **401** | — | **200** | 200 |

`tests/integration/check_api_key.py` 23종. 러너가 자동으로 집어가 CI 수정이 필요 없었다.

## 통합 검사 격리 — 반창고를 구조로 교체 — 2026-08-11

통합 검사 5개가 **DB 하나를 공유**했다. 넷은 SAVEPOINT + ROLLBACK 으로 스스로 격리하지만
`check_revocation` 은 **커밋해야 한다** — 배정·폐기·복권은 각각 다른 트랜잭션이고
그 경계를 넘나드는 것이 바로 그 검사가 보는 계약이다.

그래서 그 검사가 남긴 상태가 뒤 검사를 오염시켰고, 처음 대응은 반창고였다
(뒤 검사 SETUP 을 멱등하게 · 앞 검사가 뒷정리). 쌍마다 붙이는 대응이라 검사가 늘면 조합이 늘고,
**순서 가정이 코드 어디에도 적히지 않은 채** 남는다.

- **`scripts/run_integration.sh`** — 완전히 마이그레이션된 템플릿을 한 번 만들고
  검사마다 `CREATE DATABASE ... TEMPLATE` 로 복제한다. PostgreSQL 에서 파일 복사라 빠르다.
  DROP 하지 않는다 — 서버가 일회용이다
- **반창고를 걷어냈다** — `check_pg_violations` 의 멱등 SETUP, `check_revocation` 의 뒷정리 코드를 지웠다
- CI 의 개별 5단계를 러너 한 단계로 교체

**구조가 일한다는 증명** (반창고를 뗀 상태에서):

| 실행 | 결과 |
|------|------|
| 공유 DB · 오염원 먼저 | `check_pg_violations` **실패** |
| 템플릿 격리 · 기본/오염원 먼저/역순/같은 검사 두 번 | 전부 **통과** |

첫 줄이 핵심이다 — 격리를 빼면 실제로 깨진다.

만들면서 이름 충돌 2건을 고쳤다: 컨테이너 안에서 `$$` 가 늘 1 이라 재실행 시 DB 명이 겹쳤고,
같은 검사를 두 번 돌리면 또 겹쳤다. 실행 토큰 + 순번으로 해결.

## 안정화 — 깨끗한 환경 재현 · arch 백필 (45→1) — 2026-08-11

### 촬영이 의존하는 재현 검증이 낡아 있었다

촬영 준비 ①(「새 clone·빈 볼륨에서 4개 스크립트 전부 통과」)은 **스키마 세대 4** 때 한 것인데,
그 뒤로 세대가 **8** 까지 올랐고 `CLAIM_SQL`·`seed.sql` 도 바뀌었다.

- **`scripts/clean_room.sh` 신설** — 운영 스택을 건드리지 않고 **별도 프로젝트·별도 포트·빈 볼륨**에서
  전체 배터리를 돌린다. 언제든 다시 확인할 수 있다
- `demo.sh`·`proof_ab.sh`·`pass_rate.sh` 를 `CORE_URL`/`NODE_URL` 로 파라미터화 — 주소가 박혀 있어
  격리 환경에서 못 돌던 것을 푼다
- **실측: 9/9 통과** — 마이그레이션 8개 적용·verify · 새 볼륨 드리프트 0 · 골든셋 sha 정합 ·
  M25 위반 6종 · sanity floor 3종 · demo 사슬 · **능력 호출(Agent 미지정)** · Node 온보딩

### legacy arch 백필 — 45건 → 1건

`migrations/0008` 이 arch 를 계약에 묶었지만 그 이전 Agent 는 `arch IS NULL` 이었다.
그것들의 실행 arch 는 여전히 Node 로컬 파일이 정했다 — I1 이 닫으려던 바로 그 구멍.

- **`scripts/backfill_agent_arch.sh`** — Core 는 가중치 파일을 보지 않으므로 **추측하지 않는다.**
  가중치를 들고 있는 Node 에게 묻고, `weights_sha256` 이 **일치하는** Agent 만 채운다
- Node `/health` 의 `weights[]` 에 `arch` 추가 (학습 기록 `<weights>.meta.json` 의 값 · **Node 의 증언**)
- 실 DB **44건 백필 · 남은 1건은 `seed-agent`**(placeholder · 라우팅 불가) — 정확히 옳은 잔여
- 같은 stdin 버그를 또 만들었다 — `docker compose exec -T` 가 루프의 stdin 을 먹어 **첫 줄만** 처리했다
  (25건만 잡혔다). fd 3 분리 + `psql()` 에 `</dev/null`. `regate.sh` 에서 이미 당한 함정이다

## 남의 Agent 를 받기 위한 첫 두 칸 — arch 결속 · 자원 한도 (I1·I2) — 2026-08-11

새 설계 문서 [`design/foreign-agent-isolation.md`](../design/foreign-agent-isolation.md) —
「남의 Agent」를 **F1(남의 가중치) · F2(남의 아키텍처 선언) · F3(남의 코드)** 세 단계로 쪼개고,
F3 앞에 있는 **코드로 못 푸는 전제**(법무 킥오프 · 고객 1곳)를 명시한다.
Phase 3 진입조건의 「격리 초안」이 이 문서다.

**드러난 구멍 2개 (F1·F2 를 막는 것)**

1. **아키텍처가 계약에 없었다.** `infer.py` 가 Node **로컬 파일**(`meta.json`)에서 arch 를 읽었다.
   Agent 신원은 `weights_sha256` 뿐이라 arch 는 그 해시에 포함되지 않는다 —
   게이트가 승인한 것과 실행한 것이 같다는 보장이 **코드에 없었다**
2. **추론에 자원 한도가 전무했다.** compose 의 `mem_limit` 은 컨테이너 **전체** 한도라,
   한 건의 악성 추론이 같은 Node 의 다른 lease 까지 죽인다

**I1 — arch 를 계약에 묶는다** (`migrations/0008`)

- `agent_arch` 룩업 테이블 — 허용 아키텍처가 **DB 행**이다 (`compute_tier_rank` 와 같은 idiom).
  없는 arch 로는 Agent 등록이 **FK 로** 막힌다 (HTTP 400)
- `agent.arch` → FK. 배정 페이로드가 **Core 의 arch** 를 싣고, Node 는 그것으로 로드한다
- legacy 는 `arch IS NULL` 로 두고 `agent_arch_unbound` 뷰로 드러낸다 —
  **실 DB 실측 45건 · 라우팅 가능 35건.** Core 는 가중치 파일을 보지 않으므로 추측으로 채우지 않았다

**I2 — 실행 자원 한도** (부분)

- 파라미터 수 상한 (`agent_arch.max_params` → 페이로드 → **매 호출** 검사) ·
  입력 픽셀 상한 · torch thread 제한
- 구현 중 「로드할 때만 검사」 버그를 만들었고 실측으로 잡았다 — 캐시된 뒤 상한을 낮춰도 계속 돌았다
- **wall-clock timeout 은 아직 없다.** 파이썬에서 CPU 바운드를 안전히 끊으려면 별도 프로세스가 필요하고,
  그건 F3 의 프로세스 격리와 같은 작업이라 거기서 함께 한다

**검증** — 통합 10종(allowlist 밖 arch 등록 FK 차단 · 페이로드 arch·max_params 전달 · legacy 가시화 · 격리) ·
Node 한도 실측(정상 / 상한 초과 거부 / allowlist 밖 arch 거부 / legacy 경로 유지) · 실 사슬 회귀 통과.

## 최소 UI — Node 등록 · 능력 호출 (P2-3) — 2026-08-11

로드맵 P2-3(「최소 UI · 호출면」)을 채운다. Core 가 직접 서빙한다.

- `/ui/nodes.html` — Node 등록 · 함대 상태(생존·증서) · **증서 발급/폐기**.
  발급 시 평문 시크릿을 **그 자리에서 한 번만** 보여 주고(C3), 파일 주입을 권장한다고 알린다
- `/ui/call.html` — **Agent 를 지정하지 않는** 능력 호출. 결과와 함께 **증적**(기기·Agent·가중치 해시)을
  같이 보여 준다. `dummy=true` 면 「실제 추론이 아니다」를 붉게 띄운다
- `GET /v1/datasets` — 입력 allowlist 조회면 (절대규칙 7)
- `GET /` → `/ui/nodes.html` 리다이렉트

**새 의존성 0** — `StaticFiles` 는 starlette 동봉이다. 외부 자산(CDN·폰트·아이콘)을 쓰지 않아
내부망·오프라인에서 그대로 뜬다. 빌드 단계도 없다.

UI 는 등급을 **Core 가 부여한다**는 것을 화면에 명시하고, 등급 조합 제약(`ck_trust_provision_align`)을
미리 알려 준다 — 실측으로 `team`+`public` 조합은 **400** 으로 거절된다.

**UI 가 하지 않는 것:** Agent 게이트·바인딩 (가중치가 기기에 있어야 하므로 터미널 작업).

## Node 운영화 — 등록부터 능력 호출까지 (v제품-1) — 2026-08-11

증서(P2-4)를 만들었지만 **Node 런타임이 그것을 보내지 않아** 강제를 켤 수 없었다.
그리고 「Capability 로 요청한다」는 제품 경로가 스크립트로도 문서로도 없었다. 둘 다 메운다.

- **Node 런타임이 증서를 실어 보낸다** — heartbeat · assignments · complete 세 경로 모두.
  `NODE_CREDENTIAL_FILE` 로 **파일 주입**을 권장한다 (환경변수 직접 주입은 `docker inspect` 에 노출).
  `/health` 는 `credential_present` 만 알리고 값도 prefix 도 내보내지 않는다
- **`scripts/node_onboard.sh`** — 등록 + 증서 발급 + 0600 파일 + 주입할 환경변수 출력.
  `provision_source` 를 도메인에서 유도한다 (`ck_trust_provision_align` 준수)
- **`scripts/node_bind.sh`** — 가중치 sha 실측 → Agent 등록 → **team gate-runner 에서** 실게이트
  (절대규칙 8) → 통과 시에만 바인딩. 미통과면 exit 2
- **`scripts/call.sh`** — **Agent 를 지정하지 않는** 능력 호출. 증적(node·agent·weights_sha256)을 같이 낸다.
  `dummy=true` 면 exit 2 — 실제 추론이 아닌 것을 성공으로 읽지 않게
- `docs/guide/operate-node.md` — 세 단계가 각각 무엇을 세우는지 · 등급 조합 제약 · 강제 켜는 법 ·
  자주 막히는 곳 · **아직 없는 것**
- `.gitignore` 에 `data/node-secrets/` · `*.credential`

**실측** — 강제 모드(`REQUIRE_NODE_CREDENTIAL=1`)에서 전체 사슬 확인:
증서 없는 heartbeat **401** · 증서 실은 Node 가 `is_fresh=true` · 능력 호출이 실가중치로 완료
(`forest` conf 0.9642 · dummy 아님). 검증 후 시험 증서는 폐기하고 스택을 복구했다.

## P2-4 node_credential — Node 신원 증서 (SD-002 · SD-010) — 2026-08-11

기획서 §16 이 동결한 v4.4 를 **처음으로** 건드리는 변경이다. 로드맵 §3.1 의 선행 조건 셋
(①마이그레이션 도구 ②볼륨 보존 경로 ③승인)이 모두 충족돼 열렸고, **추가만** 한다 (절대규칙 1).

**무엇을 막는가.** Node 경로는 `node_id` 를 **URL 에서 그대로** 받았다 —
`POST /v1/internal/nodes/{node_id}/heartbeat` 를 아무나 부를 수 있었고 방어는
「팀 내부망 전제」뿐이었다 (SD-010). 이제 증서가 오면 Core 가 시크릿을 검증해 node_id 를
**해석**하고 URL 이 주장하는 값과 대조한다.

- `migrations/0007` — `node_credential` + `node_credential_status` 뷰 ·
  활성 증서 1개(부분 UNIQUE) · 이유 없는 폐기 금지 · prefix 형식 CHECK
- `apps/core/app/credential.py` — 발급·검증·폐기. 평문 시크릿은 **응답에 한 번만**, DB 엔 sha256 만 (C3)
- API — `POST /v1/nodes/{id}/credentials` · `.../revoke` · `GET /v1/nodes-credentials`
- **절대규칙 4 를 구조로 강제** — 증서에 등급 컬럼이 **없다.** 발급 API 는 `extra="forbid"` 로
  등급 필드를 **422** 로 거절한다. 등급은 언제나 `node` 행에서 읽는다
- **강제는 플래그** (`REQUIRE_NODE_CREDENTIAL`, 기본 꺼짐 — 데모 경로 유지).
  다만 **토큰이 오면 항상 검증**한다. 잘못된 증서가 통과하는 구간을 만들지 않는다
- 검증: 통합 17종 · HTTP 7종(사칭 **403** · 위조 **401** · 폐기 후 **401** · 강제 모드 **401**) ·
  상태 조회에 시크릿·해시 미노출

초안의 열린 질문 4개를 확정했다 — opaque+해시 / 전 Node·플래그 강제 / `expires_at` 선택·폐기 후 재발급 /
`api_key` 와 통합하지 않음.

## P2-1 tenant 운용 · 시드 결함 2건 (SD-015 · SD-016) — 2026-08-11

- **`migrations/0006` — tenant 신뢰 경계 운용 (P2-1 · D19).** tenant 플릿 Node + `image.classify@2`(`trust_domain_min='tenant'`).
  로드맵은 「DDL 추가가 아니라 운용」이라고만 적었는데, 실제로는 한 칸이 더 있었다 —
  `domain_min_compatible` 상 tenant Task 는 `min='team'` 계약을 **원천적으로 못 쓴다**.
  기존 계약을 낮추지 않고 새 계약을 추가했다 (출품 트랙 불변)
- **`tests/integration/check_tenant_routing.py` 6종** — tenant→tenant 배정(양성 대조) · tenant→team 허용 ·
  **team→tenant 차단** · tenant 가 team 전용 계약 사용 불가 · public 이 tenant 계약 사용 불가 · 거짓 스냅샷 거절

### SD-015 — 시드가 「얻을 수 없는 증서」를 발급했다

`seed-agent` 는 `placeholder.safetensors` 라 **실게이트가 원리적으로 불가능**한데(로드조차 안 된다)
라우팅 가능 증서를 갖고 있었고, UUID 가 가장 낮아 **claim 1순위**였다.
`requestedAgentId` 없는 Task 가 `dummy:true` 라벨을 COMPLETED 로 받았다 — 실 DB 에 **5건**.

- `seed.sql` 이 라우팅 투영을 만들지 않는다 · 기존 볼륨은 `migrations/0005` 가 폐기
- 시드 증서에 기대던 `demo_violations.sql`·`check_pg_violations`·`check_revocation` 을 자립시켰다
- CI 가 「새 볼륨에 placeholder 라우팅 증서 0건」을 검사한다

### SD-016 — claim 이 호환 행렬을 후보 단계에서 보지 않았다

`CLAIM_SQL` 이 `domain_compatible`·`tier_compatible` 을 조인하지 않아, 호환 불가 조합을 **고른 뒤**
INSERT 에서 FK 가 거절했다. 라우팅 차단 보장은 지켜지지만 **가용성이 깨진다** —
team Node 가 바빠 tenant Node 가 먼저 정렬되면 호환 Node 가 있는데도 예외가 나고 Task 가 배정되지 않는다.
tenant Node 를 넣자마자 재현됐다. 두 행렬을 조인해 후보 단계에서 거른다. FK 는 최후 방어로 유지.

## PG 위반 19종 자동 회귀 (M25) — 2026-08-11

이 프로젝트의 중심 주장은 「판정은 앱 `if` 가 아니라 PostgreSQL 제약이 한다」이다.
그 증거가 **수동 실측 기록**(`docs/error/pg-violations.md` 14종)과
**CI 밖 스크립트**(`scripts/demo_violations.sql` 6종)뿐이었다.

- **`tests/integration/check_pg_violations.py` 신설 · 19개** — CI migrate job 에 편입
- **어느 제약이 거절했는지까지 대조한다.** 이게 핵심이다 —
  실제로 `assignment_agent_id_capability_id_fkey` 를 떨어뜨려 보니 그 케이스는 **여전히 거절됐다**
  (다른 FK 가 잡았다). 거절 여부만 보는 시험이었으면 그때 초록이 떴다
- **양성 대조** — 정상 할당은 반드시 통과해야 한다. 없으면 스키마가 통째로 망가져도
  「전부 거절됨」으로 초록이 뜬다
- 전부 SAVEPOINT + 최종 ROLLBACK. 롤백됐는지도 검사한다 (seed 오염 방지)
- 변이 검사 — 제약 2종을 실제로 DROP 해 각각 FAIL 재현
- 만들면서 시험 자체의 결함 3건을 고쳤다: psycopg 다중 문장 · `ck_gate_runner_team` 이 먼저
  걸려 겨냥한 FK 를 못 보던 것 · 스냅샷을 거짓으로 적어 다른 케이스와 같은 것을 시험하던 것
- `scripts/demo_violations.sql` 은 촬영용 6종 시연으로 남긴다 (NOTICE 가 화면에 보인다)

## 출품 패키지 기계 점검 (SD-005) — 2026-08-10

촬영 당일에 사람이 눈으로 훑는 것은 재현되지 않는다. 8/23 촬영·Release 때 또 봐야 하는
항목들이라 자동으로 고정한다.

- **`scripts/check_submission.py` 신설 · 19개 검사** — 표준 라이브러리만 (새 의존성 0)
  - 금지 산출물 미동봉(EuroSAT 원본 · golden-n300 · artifacts · **pickle 계열 가중치**) ·
    필수 scratch 가중치 2종 유지 · 라이선스 4종 · 사전학습 미사용 선언(meta 16건) ·
    의존성 THIRD-PARTY 등재 · 시크릿 리터럴 · 상대 링크 180개 · 골든셋 정본 1개 ·
    골든셋 sha 정합 · 패키지 크기 · 워킹트리 청결
- 현 상태 **19/19 통과** (패키지 0.8 MB / 한도 50 MB)
- 변이 검사로 실제로 잡는지 확인 — 깨진 링크 · `artifacts/` 추적 · `pretrained=true` 각각 FAIL 재현
- `run_tests.sh` · CI unit job · 체크리스트 · 촬영 런북에 편입
- GitHub Wiki 링크(`(Page-Name)`)는 파일이 아니므로 링크 검사에서 제외

## 능력 증서 폐기 경로 (SD-014) · claim 이 agent.status 를 강제 — 2026-08-10

SD-013 재게이트 중 드러난 공백을 메운다. 재게이트가 FAILED 여도 기존 PASSED 증서가 살아남았고,
**폐기할 방법이 아예 없었다.**

- **삭제가 아니라 표시로 끊는다.** `assignment` 가 `agent_capability_passed` 를 FK 로 참조해
  실행 이력이 있는 증서는 삭제 자체가 불가능하다 (실측 20쌍). 이건 증적 보장이다 (D15)
- `migrations/0004` — `revoked_at` · `revoked_reason` · `revoked_gate_run_id` 추가 (DDL 추가만) ·
  `ck_acp_revoked_needs_reason` · 부분 인덱스 · `revoked_capability` 뷰 · `provenance_drift` 가 폐기를 반영
- **근거 없는 폐기는 거부한다** — 현재 골든셋에서 FAILED 인 `gate_run` 이 있어야 한다 (`RevokeRefused` → HTTP 409)
- **복권 경로** — 다시 통과하면 되살아난다 (`MINT_ACP_SQL` 을 `DO NOTHING` → `DO UPDATE`)
- `POST /v1/internal/agent-capabilities/revoke` · `audit_log` 에 `capability_revoked` 기록
- **`agent.status` 가 이제 실제로 강제된다** — 스키마에 선언만 돼 있고 `CLAIM_SQL` 이 보지 않았다 (SD-010 과 같은 계열).
  실 DB 41건 전부 ACTIVE 라 오늘 동작은 안 바뀐다
- `tests/integration/check_revocation.py` 10개 계약 · CI 편입.
  파일명이 `test_` 로 시작하지 않는 것은 의도 — `unittest discover` 가 집어가면 DB 없는 단위 테스트가 깨진다

## 검증 체계 도입 — 테스트 48개 · CI — 2026-08-10

이 리포는 오래 **테스트 0 · CI 0** 이었다. SD-007·SD-013 으로 **DB 밖에서 판정하는 도구**가
셋 생겼고(마이그레이션 정적 검사 · 골든셋 정합 · 계보/체크섬), 이것들은 스키마 제약이 잡아 주지 않는다.

- **`tests/` 신설 · 48개** — 표준 라이브러리 `unittest` 만 (새 의존성 0 · pip 없는 개발 환경 고려)
  - `test_migrate_lint.py` 33개 — 금지 패턴 · **오탐 방지**(정상 `INSERT … SELECT`·주석·PL/pgSQL `BEGIN`) · 허용 표식의 **범위** · 파일명/번호 규칙
  - `test_golden_sha.py` 15개 — 정본화 방식 · 선언부 4곳 일치 · 케이스 40건 · 파서가 조용히 통과하지 않는지 · `split=holdout` 유지
  - 골든 픽스처를 따로 두지 않고 **커밋된 실제 파일**을 본다 — 막으려는 사고가 「커밋된 선언부가 어긋나는 것」이라서
- **`app/migrate_lint.py` 분리** — 정적 검사·로딩이 psycopg·pydantic 없이 import 된다.
  DB 드라이버에 묶여 있어 단독 테스트가 불가능하던 것을 푼 것이고, 테스트 이전에 구조가 옳다
- **`.github/workflows/ci.yml`** — unit job(의존성 설치 없음) + migrate job(postgres 서비스)
  - migrate job 은 **빈 볼륨·기존 볼륨 양쪽**을 회귀 시험한다: baseline 가드 → 새 볼륨 드리프트 0 → 멱등 → 체크섬 잠금 → 구 sha 에서 0003 상승
- `scripts/run_tests.sh` · [`docs/guide/testing.md`](../guide/testing.md)
- 변이 검사로 테스트가 **실제로 실패하는지** 확인: sha 한 글자 변조 → 2건 실패 · 마이그레이션에 `DROP CONSTRAINT` 추가 → 1건 실패
- CI 6단계를 로컬 컨테이너로 그대로 재현해 전부 통과 확인 (첫 실행에서 깨지지 않게)

## 재게이트 29건 · 실 볼륨 마이그레이션 적용 — 2026-08-10

- **실 볼륨에 0001–0003 적용.** `pg_dump` 백업 선행. 적용 시점 드리프트 41건 / 라우팅 가능 31건
- **`scripts/regate.sh` 신설** — 골든셋 교체 후 기존 `agent_id` 를 그대로 두고 게이트만 다시 돈다.
  `proof_ab.sh` 는 실행마다 **새 Agent 를 등록**하므로 재게이트에 쓸 수 없다
- **29건 전부 PASSED** (acc 0.80~0.95). `agent_capability.gate_run_id` 가 새 run(`c21d9ef7…`)으로 이동
- 라우팅 드리프트 **31 → 1건** · 증서 수 31 유지 · assignment 무손실 · `demo.sh` 사슬 정상
- 남은 1건은 `seed-agent` — `placeholder.safetensors` 라 실게이트 불가. 새 볼륨에는 생기지 않는 이 볼륨만의 유물
- 스크립트 버그 1건 수정: `docker compose exec -T` 가 루프 stdin 을 먹어 첫 건만 처리하던 것을 fd 3 분리로 해결

## SD-013 골든셋 sha 정합 — 선언부 5곳 통일 — 2026-08-10

홀드아웃 재추출(#26) 때 매니페스트만 교체되고 선언부가 따라오지 않아 sha 가 갈렸다.
capability 행이 **리포에 없는 골든셋**을 가리켰다 (D15 위반). 사슬이 self-consistent 라 데모는 통과했다 — 조용히 틀렸다.

- 정본 = 커밋된 매니페스트 재계산값 `c21d9ef7…` (`extract_golden.py:175-177` 과 동일 정본화)
- 선언부 4곳 정정: `image-classify-v1.md`(`0341d121…`) · `eurosat-rgb.json` 기계 핀 · `seed.sql` · `contest-report-draft.md`
  (당초 3곳으로 보고했으나 실제로는 기계 핀·보고서 초안을 포함해 **5곳**이었다)
- 매니페스트 실체는 **무변경** — 케이스 40건 sha 가 파일과 전부 일치함을 확인
- `migrations/0003_golden_set_sha256_holdout.sql` — 기존 볼륨 경로. 구 값 한정 UPDATE 라 멱등
- **`scripts/check_golden_sha.py` 신설** — 매니페스트 재계산값 vs 선언부 4곳 vs 케이스 40건 대조.
  정정 전에 돌려 5곳 전부를 잡는 것을 확인한 뒤 고쳤다. 이 검사가 있었으면 #26 에서 걸렸다
- 러너가 서버 `RAISE NOTICE` 를 흘리도록 수정 — 0003 의 드리프트 경고가 삼켜지고 있었다
- 검증: 기존 볼륨(구 sha) 업그레이드 → `c21d9ef7…` · 드리프트 1건 경고 · 멱등 /
  새 볼륨(정본 seed) → 드리프트 0건. 실 볼륨은 미적용
- **재게이트는 미결** — 구 골든셋에서 얻은 PASS 증서가 그대로 라우팅된다 (`drifted_still_routable=1`).
  증서 삭제는 하지 않았다 (절대규칙 8 · D15)

## SD-007 마이그레이션 체계 — 유통 세대 v제품-1 착수 관문 — 2026-08-10

`product-distribution.md` §5 「스키마 제약을 약화하지 않는다. DDL **추가**와 마이그레이션(SD-007)만」의
적용 수단을 만들었다. 기존 볼륨을 `docker compose down -v` 없이 올릴 수 있다.

- **러너** `apps/core/app/migrate.py` — `status` / `verify` / `up [--dry-run]`. 순방향 전용, 다운그레이드 없음
- **원장** `schema_migration` (version · name · checksum · applied_at · applied_by)
- **`migrations/0001_baseline.sql`** — no-op. 신규 볼륨(initdb)과 기존 볼륨이 같은 경로를 타게 하는 장치
- **`migrations/0002_provenance_drift_view.sql`** — `provenance_drift` · `provenance_drift_summary` 뷰 추가.
  골든셋 교체 후 **다른 골든셋에서 얻은 PASS 증서가 그대로 라우팅되는지** 조회 가능하게 (D15)
- **절대규칙을 도구가 강제** — 제약 약화(`DROP CONSTRAINT`·`NOT VALID`…)와
  `assignment`/`gate_run` 수기 `VALUES` INSERT 를 적용 **전에** 정적 거부
- 래퍼 `scripts/migrate.sh` · 문서 [`docs/guide/migrations.md`](../guide/migrations.md) · INDEX 링크
- 새 의존성 **0** (psycopg 만 · alembic 도입 안 함) · compose 무변경 · Dockerfile 에 `COPY migrations` 한 줄
- 검증: 일회용 컨테이너 11종 — 적용·멱등·부분실패 롤백·체크섬 드리프트 양방향·baseline 가드·파일명/번호 규칙·러너 4개 동시 기동.
  동시 기동에서 `CREATE TABLE IF NOT EXISTS` 경합 버그를 발견해 잠금 안으로 옮김
- **실 볼륨 미적용** — 승인 후 `scripts/migrate.sh up`
- **SD-013 신규**: 골든셋 sha 가 매니페스트 `c21d9ef7…` / 문서 `0341d121…` / seed `c8254bcb…` 로 3중 불일치.
  자동 수정하지 않았다 — 정정은 재게이트를 동반한다

## 제품 유통 목표 문서화 (D19) · 데모 골든 홀드아웃 — 2026-08-10

- **D19:** Open Agent + (선택) Open Compute + User-defined Trust Domain. 경제는 선택·비기초. 정본 [`docs/design/product-distribution.md`](../design/product-distribution.md)
- 로드맵 §5.1 · handoff · STATE · INDEX · README 링크 · 사용안내 신뢰 경계 절
- **데모 N=40** `split=holdout` 재추출 · `check_golden_leakage` clean. 커밋 A 가중치는 여전히 `train_images=27000`
- 커밋 서명: `user.name`=finn|toma|pl + 팀 noreply (`CLAUDE.md` · github-team-guide)
- 촬영 런북·regulation sha·handoff A/B Within 무효 반영

## 사이클 폐쇄 + 서사 전환 (v4.7) — 2026-08-09

**코드** — 사용자 → Core → Node → Core → 사용자 사이클을 닫았다
- Core 디스패치 워커 · `GET /v1/internal/nodes/{id}/assignments` (당기는 방식·NAT)
- Node 폴링 루프 + **배정 검증(403)**. 이전에는 기기에 닿는 누구나 추론을 시킬 수 있었다
- `demo.sh`·`proof_ab.sh`에서 기기 직접 호출 제거. 증적 출력 추가
- 스키마 변경 없음

**계약** — 기획서 v4.6 → v4.7
- **Capability = 인터페이스 계약.** 골든셋 게이트는 선택적 품질 프로파일 (D18)
- `min_per_class_recall 0.10` 신설(유도) — 없으면 클래스 2개 버린 모델이 통과(m=8 → 0.80/0.711)
- `min_accuracy 0.68`은 **선언된 서비스 수준**으로 근거 교체 (SD-004 순환 대체)
- 편차는 숫자를 두지 않음 — `1−t`는 항등식이지 제약이 아니다
- `guarantee` 블록 — 무엇에 조건부인지를 기계가 읽는 형태로

**서사** — 전 문서에서 「채점 가능한 계약」 제거
- 기획서 §1·§4.4 · README · 보고서 md·양식 · 런북 · 스토리보드 · Contest MVP · 체크리스트
- 촬영 런북: A/B 20→10초, **증적 10초 신설**. 자막 8문장 교체


## Phase 1 판정 = 보류 · 골든셋 누출 발견 — 2026-08-08

- **P1-1·P1-2 달성**: `scripts/proof_ab.sh` — A/B 실게이트 PASSED(`dummy=false`) + 동일 case 교차 할당(`honored=true`, assignment 2건 SUCCEEDED). §7.1-2·3 사슬 위 달성
- **P1-3**: `scripts/pass_rate.sh` · 8후보 사다리(TE{5,20,40,80}·TEB{5,10,20,40}) → **75.0%**. 모집단 설계는 결과 확인 전 커밋(`7100c9f`)
- **P1-4**: `docs/ops/phase1-verdict.md` — **판정 보류(HOLD)**
- **SD-008 골든셋 ⊂ 학습셋**: 데모 40/40 · n300 300/300이 학습에 쓰인 이미지. 홀드아웃 없음 → 게이트가 능력이 아니라 학습 데이터 재현을 잰다. `scripts/check_golden_leakage.py` (exit 2). **Phase 2 착수 차단**
- 영향 없음: 게이트 사슬 · M25 6종 · sanity floor 3종 · Product Track 구조
- n=300 재현: A 0.8800 · B 0.9267 · abs_diff 0.046667 · **label_agreement 0.8933**(300건 중 32건 라벨 상이)
- 재현성 수정: `demo.sh`·`sanity.sh` 호스트 `python`→`python3`, `demo.sh` f-string 백슬래시 → % 포맷. **.sh 경로는 Linux에서 한 번도 성공한 적이 없었다** (Contest Must M4 직결)
- 보고서 초안 §8에 누출 명시 · §0·§8의 낡은 A/B 서술 정정

## 종착점 Phase 3+ 확장 · Phase 1 좌표 정정 — 2026-08-08

- **D16**: 프로젝트 종착점 = 기획서 §9 Phase 3+ 전체. Contest MVP는 Phase 1 슬라이스 (SD-006)
- `docs/design/roadmap.md` 신설 — Phase 1 완주 → 2 → 3 → 4–6 진입조건·산출물·판정 게이트
- **정정**: A/B n300 Within은 **게이트 사슬 밖 측정**. §7.1 증명 대상 2·3번(Agent B 실게이트 PASSED, 증명 모드 교체 할당) 미달 · 통과율 20–80% 미실측 — STATE·SD-001 반영
- **SD-007**: 마이그레이션 체계 부재 (Phase 2 `node_credential` DDL 선결과제)
- **지정 실행(M14) 배관은 이미 존재** — `task.requested_agent_id` + `claim.py` 조인(`agent_capability_passed` 경유). §7.1-3은 미구현이 아니라 **미실행**이며 막는 것은 Agent B 하나. 실제 공백은 `proof_run_id` 기록·UC-7 절차
- 촬영 런북: UC-7 불가 명시(B 미통과). 스키마·코드 변경 없음

## Team role pl (peer of finn/toma) — 2026-08-08

- `docs/guide/github-team-guide.md` v1.3 · `CONTRIBUTING.md` — 작업 역할 **pl** (`pl/<topic>`, `LGTM (pl)`, finn/toma와 동급). master는 merge 전용

## README stable-only + schedule canon — 2026-08-08

- README: 심사 빠른 시작 상단 · 상태/결정/일정 본문 제거 → STATE·handoff·checklist 링크만
- `contest-submission-checklist.md` = 일정·제출 정본 (notice/39 인용). Contest_MVP §1·handoff §4는 링크

## A/B Must Within (n=300) — 2026-08-08

- Agent A 80ep · B 40ep · n300 abs_diff≈0.0467 → **WITHIN_THRESHOLD** (SD-001 closed)
- 공개 가중치: `eurosat_scratch.safetensors` 갱신 · `eurosat_scratch_b.safetensors` 추가 (gitignore 예외)
- 한계: epoch A≠B · SE≈임계 — 보고서/영상에 명시. 출품 양식·UC-7 반영 가능

## Agent B n300 + A/B measure — 2026-08-08

- `TinyEuroSATB` 20ep → `eurosat_scratch_b.safetensors` (local · gitignore)
- n300: A≈0.817 · B≈0.887 · `|diff|=0.07` → **EXCEEDS_THRESHOLD** · Contest Must 아님 (SD-001)
- 출품 우선: 양식·영상·포털. A/B Must 승격 비권장

## Dual-track contest runbook + Agent B train — 2026-08-07

- `docs/ops/shoot-day-runbook.md` · `gate-chain-slide.md` · 출품 체크리스트 갭/이중 트랙 갱신
- Agent B(`TinyEuroSATB` → `eurosat_scratch_b.safetensors`) 학습 착수 (gitignore · Must 아님)

## E1 n=300 score + A/B skeleton — 2026-08-07

- `TinyEuroSATB` + `ARCH_REGISTRY` / `build_model` · meta `arch`로 infer 로드
- `train_scratch` `ARCH`/`OUT_NAME` · `scripts/score_n300` · `scripts/compare_ab` (n&lt;300 → INCONCLUSIVE)
- 로컬 실측 Agent A n=300: acc≈0.817 · f1≈0.814 (artifacts/ 미커밋). B·paired 미실행
- A/B **Must 아님** (SD-001 미결). 스키마 DDL 변경 없음

## Contest compliance drafts — 2026-08-07

- `docs/ops/regulation-compliance.md` — 운영규정 조항별 준수 근거
- `docs/ops/contest-report-form-draft.md` — 공식 양식용 5P·붙임1·2 초안 문장
- 가중치 raw URL HTTP 200 실측 (제9조 유형3 공개)

## SBOM cyclonedx + retrospective — 2026-08-07

- 호스트 Python 3.12 · `scripts/generate_sbom.ps1` / `.sh` · `enrich_sbom.py` → `sbom.json` (수동본 대체)
- `docs/retrospective/` — TD / Scope Decision / Environment Adaptation 레지스터
- TD-001(수동 SBOM) closed

## Contest deliverables draft — 2026-08-06

- `docs/ops/contest-report-draft.md` — §3 아키텍처(게이트 사슬) · §4 DB 제약 · §6 골든 · §7 재현 · §9 라이선스
- `docs/ops/demo-video-storyboard.md` — 3분 영상 촬영 체크리스트
- `sbom.json` — CycloneDX 1.5 (THIRD-PARTY-LICENSES와 정합)

## node_credential 설계 초안 — 2026-08-06

- `docs/design/node-credential-draft.md` — 발급·검증 원칙. **스키마 DDL 없음**

## Capability API + golden n=300 pipeline — 2026-08-06

- `POST /v1/capabilities` 런타임 등록 (UNIQUE·mvp CHECK는 DB). 스키마 DDL 변경 없음
- `scripts/extract_golden.py --n 300` + `extract_golden_n300` → `data/golden-n300/` (gitignore)
- 데모 N=40과 본편 N=300 분리. A/B Must 미결·미구현

## S3 + OpenAPI — 2026-08-06

- S3: `gate finish`에서 `golden_set_sha256`가 `gate_run` 스냅샷과 불일치하면 거부. 실게이트(`dummy=false`)는 필드 필수
- S4: `docs/spec/openapi.yaml` 초안 + Core `GET /openapi.yaml`. 스키마 DDL 변경 없음

## MVP phase2 — 2026-08-06

- EuroSAT RGB **scratch** TinyEuroSAT → `eurosat_scratch.safetensors` (safetensors만, 사전학습 없음)
- Node: scratch 추론 · Core: `dummy=false` 실게이트 검증(지표 AND) · `score_gate`
- 실측 후 임계 보정: `min_accuracy` 0.68 · `min_macro_f1` 0.65 (가정 0.75/0.72는 실측 위)
- `scripts/demo` 실게이트 PASSED + Task 완주 · `scripts/sanity` floor 3종 FAILED
- torch/torchvision(CPU, node-m-team) · Pillow · THIRD-PARTY 갱신
- **seed/smoke dummy PASSED ≠ 실게이트.** A/B Must 미결·미구현

## MVP phase1 — 2026-08-06

- 골든셋 데모 N=40 manifest + cases/ (균등 스트라이드, 모델 선택 없음)
- 픽셀 전수: EuroSAT RGB 27,000장 전부 64×64×3
- `scripts/demo_violations` M25 6종
- 결과보고서 초안 0·1·2·5·8절
- compose Node 3대 자원 제한 (S/team, S/public, M/team). `node_credential` 없음
- **scratch 학습·실게이트 채점 아님**

## W1 — 2026-08-06 (EuroSAT RGB pin)

- Zenodo `7711810` / `EuroSAT_RGB.zip` 실측: `archive_sha256`, 원본 64×64, Pascal 클래스 폴더
- 핀 파일 `docs/spec/golden/eurosat-rgb.json` · 다운로드 스크립트. **원본 미동봉 · scratch 학습 아님 · 케이스 manifest 없음**
- seed `golden_metrics.dataset`에 archive 핀. `golden_set_sha256`은 빈 placeholder 유지. 스키마 변경 없음

## W1 — 2026-08-06 (CRUD + gate chain API)

- Agent / Node 등록·조회, 바인딩 → READY (`INSERT … SELECT`)
- `gate_run` 시작·종료 사슬 API. **골든셋 추론 아님.** PASSED는 `dummy=true` 기록만
- Node 등급은 Core 관리자 등록. Node 런타임 자기주장 경로 없음
- smoke: .pth 거절 · non-runner 409 · dummy 게이트 후 claim/execute

## W1 — 2026-08-06 (plan v4.5 + dummy Node)

- 기획서 **v4.5**: §2.5 Interface–Implementation Separation, Execution Provenance(개념), §14 문헌, §15 완료=최소 증서. 스키마는 v4.4 유지
- dummy Node: placeholder safetensors 로드 → dummy 추론 → `POST /v1/internal/assignments/{id}/complete`
- smoke: 새 task claim 후 node `/v1/execute`까지. **EuroSAT scratch 학습 아님**

## W1 — 2026-08-05

- `compose.yaml`: PostgreSQL 16 + Core(FastAPI)
- `docs/spec/schema.sql` 적재 + `image.classify@1` seed + datasetId allowlist (`eurosat-rgb`)
- claim: `INSERT … SELECT` + `FOR UPDATE SKIP LOCKED` (`POST /v1/internal/claim`)
- 팀 가이드 v1.2 fast-track (§6.4)

## Docs — 2026-08-05

- 문서 레이아웃 [PR #5](https://github.com/gncorpseo-commits/capnet/pull/5) `main` 머지
- Wiki Home 링크를 `main` 카테고리 경로로 고정

## Docs — 2026-08-03 (layout)

- 문서 트리 정리: `docs/{guide,error,history,design,spec,ops,research}` + [`docs/INDEX.md`](../INDEX.md)
- 위반·함정 본문을 `docs/error/`로 분리 (handoff 중복 제거)
- README 문서 표 → INDEX 위임

## Docs — 2026-08-03

- 팀 GitHub 사용 표준 가이드 v1.1 (`docs/guide/github-team-guide.md`, Wiki 동기화)
- `CONTRIBUTING.md` 추가

## v4.4 — 2026-07-31

게이트 사슬·trust_domain_min 무결성. Phase 1 동결 후보.

- `gate_run`: runner NOT NULL + `node(id, is_gate_runner)` 복합 FK
- `gate_run_passed` 증서 → `agent_capability` PASSED만 근거 있는 run에 연결
- `domain_min_compatible` + task `capability_trust_domain_min`
- 기획서 파일명 `capnet-plan.md`로 정리; `docs/_to_delete` 제거

## Naming — 2026-07-31

제품명 확정: **Capability Network (CapNet)**. 약어 **CN**.  
**ai-agent-store** = 상위 레포/공간 · CapNet = 그 안 첫 제품.  
(이전 가칭: AI World / AI Agent Store)

## Contest — 2026-08-01

- [`Contest_MVP_2026.md`](../ops/Contest_MVP_2026.md) **v0.3** — 문서세트 정합 (골든셋 v0.2, 영문 파일명, M25 6종 고정)
- [`user-guide-ko.md`](../guide/user-guide-ko.md) — IT 비전문가용
- [`golden/image-classify-v1.md`](../spec/golden/image-classify-v1.md) — 골든셋 정본

## v4.3 — 2026-07-31

호환 행렬 무결성.

- `tier_compatible` / `domain_compatible`: rank 컬럼 + rank 테이블 복합 FK + CHECK 순서
- 독성 행렬 INSERT 차단 (team→public, L→S)
- Phase 1 스키마 동결 후보

## v4.2 — 2026-07-31

스냅샷 거짓 기재·가중치 드리프트 패치.

- `UNIQUE (task.id, capability_id, trust_domain)` ← assignment FK
- `UNIQUE (capability.id, compute_tier)` ← assignment FK
- `agent_node_ready` 이중 FK: node seen hash + `agent(id, weights_sha256)`
- live READY/assignment 중 가중치 UPDATE 거부

## v4.1 — 2026-07-31

리뷰 실측 결함 패치.

- `compute_tier_rank` / `tier_compatible` (TEXT `'L'<='S'` 함정 제거)
- `trust_domain_rank` / `domain_compatible` (privacy_rank; tenant ↛ public)
- `agent_capability_passed`, `agent_node_ready`, assignment 복합 FK
- Node `(id, trust_domain, compute_tier_max)` UNIQUE — 강등 TOCTOU
- 문서 §5.1 모순 해소; 10주 인터뷰 3–5건; `energy_wh` 예약

## v4.0 — 2026-07-31

전략·계층·경제 개정. v3.2 기술 골격 유지.

- Wedge: 배치/비동기/거주지 (클라우드 실시간 API 비경쟁)
- First capability: `image.classify@1`
- Compute Tier S/M/L, Trust Domain team→tenant→public
- Kill/Pivot criteria, 10-week Phase 1 plan
- work_units metering from Phase 2 (no settlement)
- Schema: compute_tier, trust_domain*, assignment duration/vram

## v3.2 — 2026-07-31

리뷰 병합 + 자체점검 20항목. Schema S1–S11.

## v3.1 / v3.0

전제 교정 및 WSL 유실 후 복원 통합.
