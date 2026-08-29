# STATE — 현재 작업 상태

> **갱신: 2026-08-29** · 종착점 = **Phase 3+ 전체** (D16) · 제품 유통 = **D19** · 출품 후 = **D25 트랙 A** · README는 상태 비보유(링크만)

---

## 대회 정보

팀명 **지엔** · 접수번호 **915**  
일정·제출 정본: [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md)

---

## 지금 어디인가

**서사 전환 완료 (기획서 v4.7) · 사이클 폐쇄 완료.** **2026 대회 출품 제출 완료 (8/27).**

> **출품 이후 트랙 A · D25 (2026-08-27).** 같은 공개 저장소에서 계속 개발한다.
> 출품 재현본 = 태그 [`v0.1.0-contest`](https://github.com/gncorpseo-commits/capnet/releases/tag/v0.1.0-contest) 고정.
> 새 저장소 분기 없음. 이후 작업 = `finn|toma|pl/<topic>` → PR → main.

> **포털 제출 완료 (2026-08-27).** 결과보고서 · 시연(YouTube) · 소스(Release) 포털 업로드 완료.
> G7–G9 ✅. PR [#103](https://github.com/gncorpseo-commits/capnet/pull/103) 머지됨.

> **역할 분담 (2026-08-28).** **Claude = 구현·PR** · **Cursor = 리뷰·설계·Decision**.
> 브리지 Next: `product-handoff-to-claude`. main 머지 = master/사람.

> **P2-2 마감 — 머지됨 (2026-08-29).** PR [#108](https://github.com/gncorpseo-commits/capnet/pull/108)
> → [#109](https://github.com/gncorpseo-commits/capnet/pull/109) 로 **main `7e6d5f9`**.
> 브리지 `pr-c-work-units` Decision(D1-a·D2-a·D3) 구현 · **D4 는 손대지 않았다** (ack 수령).
>
> **#108 은 stacked base(`toma/capreq-result-view`)에만 머지됐다** — #107 이 main 에
> squash 로 들어가 이력이 갈려서, 같은 트리(`5a31f234…`)를 main 에서 딴 브랜치에 얹어
> #109 로 반영했다. **교훈: base 는 항상 `main`.**
>
> - **D26 승격** — 작업량 정본 = **Core 관측**(`finished_at − created_at` · 파생 · 저장 안 함).
>   `duration_ms` = Node 자기신고(추론 구간) **힌트로 유지**. 실측 평균 차 **789 ms**.
> - `vram_mb_peak`·`energy_wh` = **미계측**. RSS 로 채우지 않고 **센다**(완주해도 0).
> - `GET /v1/ops/work-units` 신설 — developer · read-only · 기본 7일(1..90) ·
>   능력별·Node 별 분해. `/v1/ops/status` 미확장. **DDL 0 · 마이그레이션 0.**
> - 검사 둘 신설 — `test_work_units_wiring`(DB 없이 정본 뒤집힘 감지) ·
>   `check_work_units`(claim→complete 완주 후 **관측 ≥ 자기신고**). `run_tests` 247 → **260**.
> - 통합 검사 **`check_work_units` 21/21** (CI · `run 33227726388`) — 관측 1500 ms ≥ 자기신고 3 ms ·
>   뒤집으면 감지 · 조회가 아무것도 쓰지 않음 · 창이 실제로 자름.

> **제품 입구 마감 — 머지됨 (2026-08-29).** PR [#107](https://github.com/gncorpseo-commits/capnet/pull/107)
> · main **`1a15ff1`**.
> capreq 가 「능력을 고른다」에서 멈추지 않고 **상태와 결과를 보여 준다**.
>
> - `capreq/results.py` 신설 — `result_ref` → 표시 요약 (label·entities·vector/forecast·
>   columns/rows). 증적 칸은 결과로 새지 않는다. **새 품질 주장 없음.**
> - `GET /api/tasks/{id}` 신설 · `POST /api/chat` 에 `wait` — 브라우저가 1초 폴링해
>   `QUEUED → ASSIGNED → RUNNING → COMPLETED` 배지와 배정 증적(node·agent·domain·tier)을 그린다.
> - **실행 경로 버그 4건**: `timeseries.forecast` 첨부가 MIME 규칙 부재로 통째로 막혀 있었고,
>   첨부 없는 실행이 LLM 을 두 번 불렀고, 폴링이 `TIMEOUT`·`CANCELED` 에서 안 멈췄고,
>   등록 스크립트 3개의 능력 이름이 복사 실수로 전부 `text embed (fixed projection)` 였다.
> - CI 에 **`capreq` 잡** 신설 (`httpx` 만 설치). capreq 테스트 19 → **32**.
> - **브라우저 종단 스모크는 아직 미실행이다** — 그 세션에 Docker·Ollama 가 없었다.
>   서버 라우트는 컴파일 + 순수 헬퍼 단위 테스트까지만 검증됐다. 절차는 `capreq/README.md`
>   §「눈으로 확인하기」. **Ollama 있는 환경에서 한 번 돌리면 이 문장을 지운다.**

> **제품 1호 — 커밋 완료 (2026-08-28).** Cursor 가 Windows 클론에 써 둔 두 묶음을 WSL 작업
> 리포로 옮겨 심고 PR 을 올렸다. 브랜치는 **`toma/track-a-text-ner-and-inputs`** —
> `toma/post-contest-track-a` 는 원격에 이미 있고 squash 머지된 커밋을 가리켜서
> 같은 이름으로 밀면 force 가 된다(금지). 이름만 다르고 내용은 그 Next 그대로다.
>
> - capreq **입력 챗봇**: 첨부 → Core `POST /v1/inputs` → Task `{ inputId }` (D22) ·
>   `CapNet-Key` 인증 수정 · MIME 선검사. 자유 업로드 경로 없음.
> - **`text.ner`**: RuleTextNer · 규칙 span · 카탈로그 7번째 구현 ·
>   `scripts/ner_demo.sh` **종단 PASSED** (entities 3건 · assignment SUCCEEDED).
> - **게이트가 실제로 걸렸다** — 텐서 0개라 `weights_fingerprint` FAIL. 검사를 약화시키지
>   않고 버퍼 한 칸을 뒀다 (파라미터는 여전히 0 · 가중치 sha 갱신).
> - 재현 검사 복구: 이 세션은 Docker 가 살아 있어 `clean_room` **9/9** ·
>   `prod_room` **27/27** 을 실제로 돌렸다 (직전 세션은 Docker 없어 미실행이었다).

> **Release 발행 (2026-08-27).** 태그 **`v0.1.0-contest`** = `238427d` ·
> [Release](https://github.com/gncorpseo-commits/capnet/releases/tag/v0.1.0-contest) ·
> `capnet-v0.1.0-contest.zip` **2.5MB / 335파일** 첨부. 태그 기준 `run_tests` **240** ·
> `check_submission` **24/24** · `check_release v0.1.0-contest` 통과.
> `clean_room`·`prod_room` 은 Release 환경에 Docker 없어 미실행 (직전 기록 9/9 · 27/27).

> **동기화 (2026-08-25).** PR [#102](https://github.com/gncorpseo-commits/capnet/pull/102) —
> 보고서 PDF/docx · capreq · 제출팩 · `inbox-claude` Next(Release). **main 머지 = master.**

> **사람 개입 정리 (2026-08-25).** 붙임2「팀이 설계」근거를 문서에서 재구성 —
> [`docs/retrospective/human-intervention.md`](docs/retrospective/human-intervention.md)
> (D-결정·반증·절대규칙 vs AI 구현 보조). 기억과 다르면 해당 파일 §4 체크 후 수정.

> **결과보고서 docx (2026-08-25).** 공식 양식에 본문·붙임1(SBOM 10행)·붙임2(유형3·AI 보조 약 30%) 이식.
> [`docs/ops/contest-report-915-gn.docx`](docs/ops/contest-report-915-gn.docx) · PDF 동명.
> 포털 업로드 시 파일명은 공식형 `…_915(지엔).pdf`로 바꿔도 됨. **Release · 포털** 남음.

> **출품 영상 (2026-08-23).** CapCut 내보내기 **172.9s · 1080p · ~38MB**.
> YouTube 일부 공개: **https://youtu.be/RjFiGpmLTbk**
> 제출 패킷: [`contest-submission-pack.md`](docs/ops/contest-submission-pack.md).

> **촬영 A/B PowerShell (2026-08-21).** `scripts/proof_ab.ps1` 포팅 — 본편에서 WSL 없이
> `pwsh -File scripts\proof_ab.ps1`. 실측: A·B 실게이트 PASSED · 교차 Task COMPLETED
> (case `ic1-0001`). 자막은 런북 §2-A 유지.
>
> **런북 리허설 보강 (2026-08-21).** `shoot-day-runbook.md` 에 pwsh·UI·생존 API·Docker 해설·
> EuroSAT/골든셋·sanity/violations/A/B 용어·증적=demo 끝 재강조를 모음.
>
> **CapCut 편집 가이드 (2026-08-22).** `docs/ops/capcut-edit-guide.md` — 분할(`Ctrl+B`)·텍스트/
> 자동캡션·런북 §2 복붙·내보내기 체크. 영상 편집은 사람, 문장 정본은 런북.

> **촬영 A/B PowerShell (2026-08-21).** `scripts/proof_ab.ps1` 포팅 — 본편에서 WSL 없이
> `pwsh -File scripts\proof_ab.ps1`. 실측: A·B 실게이트 PASSED · 교차 Task COMPLETED
> (case `ic1-0001`). 자막은 런북 §2-A 유지.
>
> **런북 리허설 보강 (2026-08-21).** `shoot-day-runbook.md` 에 pwsh·UI·생존 API·Docker 해설·
> EuroSAT/골든셋·sanity/violations/A/B 용어·증적=demo 끝 재강조를 모음.

> **제품 주장이 바뀌었다.** 「채점 가능한 계약」 → **「능력만 요구 · 승인 도메인 안 라우팅 · 실행 증적」** (D18)
> 근거는 실패가 아니라 기획서 §1 원래 취지다. 골든셋 게이트는 **선택적 품질 프로파일**로 내려갔고,
> 그래서 골든셋의 세 구멍(표본·분포·게이밍)이 계약 핵심에서 부속 기능의 한계가 됐다.

**오늘 코드로 닫은 것 — 사이클**

| | 이전 | 지금 |
|---|---|---|
| 스케줄링 | 클라이언트가 `claim` 호출 | **Core 워커가 배정** |
| 실행 | 클라이언트가 기기 직접 호출 | **기기가 자기 배정을 가져감** (outbound·NAT) |
| 무단 호출 | 누구나 가능했음 | **HTTP 403** (실측) |
| 사용자 | 기기 주소를 알아야 했음 | **Core만 안다** |

**보장 / 불보장**

| 보장 | 승인 도메인 밖 라우팅 안 됨 (FK) · 실행 증적이 남고 조회됨 |
|---|---|
| **불보장** | 기기가 데이터를 안 남김 (TEE 없이 원리적 불가) · 두 에이전트가 같은 답 |

| 트랙 | 상태 |
|------|------|
| **출품 (1순위)** | ✅ **포털 제출 완료 (8/27)** · Release `v0.1.0-contest` · **이후 = D25 트랙 A** |
| **Phase 1** | ✅ 완주 · 판정 **Go** (v4.6) |
| **Phase 2** | 사이클 폐쇄 완료. 유휴 판정은 스키마 필요 → SD-007 **해소** |
| **제품 유통 (D19)** | 문서 정본 [`product-distribution.md`](docs/design/product-distribution.md). 1호 = 초대 team/tenant · 경제 비기초. **코드 유통 세대 = v제품-0 직전** |
| **마이그레이션 (SD-007)** | ✅ 러너·`migrations/`·원장. **실 볼륨 0001–0003 적용 완료 (2026-08-10)** → [`guide/migrations.md`](docs/guide/migrations.md) |
| **최소 UI (P2-3)** | ✅ `/ui/nodes.html` 등록·증서 · `/ui/call.html` 능력 호출·증적 · 새 의존성 0 |
| **운영화 (v제품-1)** | ✅ `node_onboard` → `node_bind` → `call` 3단계 · Node 런타임이 증서 전송 · 강제 모드 실측 → [`guide/operate-node.md`](docs/guide/operate-node.md) |
| **성능 (SD-017)** | ✅ 커넥션 풀 — API 15ms→**3.8ms** · 100건 부하 5.4/s→**12.4/s** · 포화 해소 |
| **관리 API 인증** | ✅ `api_key`+역할(user<developer<admin) · 쓰기 11개 보호 · **SD-010 해소** · 강제는 플래그 |
| **Node 신원 (P2-4)** | ✅ `0007` `node_credential` — v4.4 동결 이후 첫 스키마 변경(추가만) · 사칭 403 실측 · 강제는 플래그(기본 꺼짐) |
| **tenant 운용 (P2-1)** | ✅ `0006` — tenant 플릿 Node + `image.classify@2`(min=tenant) · 경계 6종 실측 · **claim 버그 SD-016 발견·수정** |
| **증적 정합 (SD-013)** | ✅ 골든셋 sha `c21d9ef7…` 통일 · **재게이트 29건 완료** · 라우팅 드리프트 31 → **1건**(`seed-agent` placeholder) |
| **B0 증적 절반 복구 (2026-08-12)** | ✅ task 가 **요청자**(`_actor()` — seed admin 하드코딩 제거)와 **요청 신뢰 도메인**(하드코딩 `'team'` 제거)을 기록. 호환은 복합 FK `domain_min_compatible` 가 판정. 실증 11/11 → D23. **tenant 유통이 구조적으로 가능해짐** |
| **문서 위생 — 자라는 숫자 (2026-08-17)** | ✅ **출품 트랙 · 제품 코드 0.** 안전 사슬 표의 **네 칸이 전부 어긋나 있었다**(`check_api_key` 23→22 · `check_node_credential` 17→18 · `check_enforcement` 20→30 · `prod_room` 14→27). **숫자를 맞추지 않고 표에서 뺐다** — 능력을 더할 때마다 느는 값이라 못박으면 다음 사람이 숫자만 고치게 된다. 왜 안 적는지도 남겼다. 반대로 **고정돼야 하는 값**(마이그레이션 세대)은 실물 대조로 유지. 갱신일 넷(`STATE`·런북·카탈로그·**체크리스트 08-08**)을 **최신 CHANGELOG 기준**으로 고정 · `check_release.sh` **INDEX 등록**. `test_doc_counts` **6종** · 변이 3/3 · `run_tests` 234→**240** |
| **제출 패키지 사전 검증 (2026-08-16)** | ✅ **출품 트랙 · 제품 코드 0.** 일정 정본 S4 가 「가중치 바이너리를 넣지 않는다」였는데 **제품은 넣어야 돌아간다**(`check_submission` 이 5종 요구) — 8/25 패킹하는 사람이 망설일 줄이라 실제 정책대로 갈랐다(S4-1 신설). `scripts/check_release.sh` — S2 명령을 그대로 돌리고 **압축본을 연다**: 크기 ≤50MB(**2.3MB**) · 필수 **17종** · 금지 산출물 없음 · `capnet/` prefix. **태그 없이 HEAD 로도 돈다** · `run_tests` 에 물려 매번 본다. 변이 2/2(가중치 누락·`.env` 혼입). D-2 체크리스트 재현 기록도 **08-09 → 08-16**(`6609ce1`)로 갱신하고 **능력 6종 데모 재현** 항목 추가. **남은 것은 전부 사람 몫** — G7 양식·G8 촬영(D-7)·G9 태그/업로드·붙임2 §4 비율 |
| **table.extract (2026-08-16)** | ✅ **단계 6 ④ — 여러 칸을 내는 출력 · 새 가중치 0.** 지금까지 출력은 한 칸이었다(`label`/`vector`/`forecast`). `columns`·`rows`·`header_detected` **셋**을 내면서 **「이름은 계약이 정한다」를 집합으로** 지켰다 — Core 가 `required` 와 키 집합을 대조하고 다르면 **422**. `output` 을 더하면서 **「아무것도 안 냈다」 구멍은 안 열었다**. **가중치 재사용** — 열 타입 추론은 `text.classify` 가 하던 일이라 `text_struct_scratch` 그대로. **PDF 는 받지 않는다**(새 의존성) — 계약·카탈로그 MIME 을 `text/plain` 만으로 고쳤다. **자르지 않고 던진다**(자르면 「다 읽었다」가 거짓). 머리글은 느슨한 규칙이라 `header_detected` 로, 열 타입은 다수결이라 `support` 로 **노출**. 실측 `host→ipv4 · id→uuid` COMPLETED · 증적에 `label`/`vector` 없음. `test_table_extract` **18종** · 변이 3/3 · `run_tests` 207→**219** · 게이트 9/9·27/27 |
| **보고서 능력 5종 실측 (2026-08-16)** | ✅ **출품 트랙 · 코드 0.** 원고의 「분류·요약·임베딩 어디에도 붙는다」는 **주장**이었다 → **능력 5종이 같은 사슬을 통과한 실측**으로 교체(입력 3종·출력 2종). **1차는 서면으로 갈린다**(F2). **다섯 중 넷은 품질을 주장하지 않는다**를 같이 적었다 — 안 적으면 「성능은 왜 안 밝히나」로 읽힌다. **주장은 재현 가능해야** 하므로 구동 절에 데모 넷 + **`bash` 전용** 명시(`.ps1` 없음). 곁다리로 **카탈로그의 `text.classify` 구현 표시 누락**을 찾았다(실물은 다 있었다 · 세어 보니 4→**5**). `test_report_claims` **6종** · 변이 3/3(**능력을 더 구현하면 원고 갱신 강제**) · `run_tests` 201→**207** · `check_submission` 24/24 |
| **촬영 문서 드리프트 정정 (2026-08-16)** | ✅ **출품 트랙 · 코드 0.** 실행기 넷을 얹는 동안 문서가 뒤처졌다 — README `「17개 적용」`·`세대 17` → **18** (심사위원이 첫 화면에서 대조하는 값) · 런북 단위 **68→191** · 출품 점검 **21→24**. **자라는 값은 못박지 않았다** — 검사 수는 실행기마다 늘므로 「숫자가 달라도 이상이 아니다」를 적고 유지돼야 할 것(`clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500`)만 고정. **마이그레이션 세대는 반대로 정확히 고정**(눈으로 대조하는 값). **촬영에 안 넣는 데모 넷**과 그 이유 셋을 명시. `test_shoot_docs` **10종** · 변이 3/3(**마이그레이션 추가 시 4건 실패 → 문서 정정 강제**) · `run_tests` 191→**201** · 재확인 실측 전부 통과 |
| **image.embed (2026-08-16)** | ✅ **단계 6 ③ — 이미지가 `structured` 를 낸다 · 새 가중치 0.** 그동안 이미지는 closed_set 만 냈다 — 미검증 조합. **기존 `eurosat_scratch` 트렁크 재사용**(새 학습·커밋 0 · 패키지 2.2MB/50MB 유지). **계약 게이트가 통과할 Agent 를 떨어뜨렸다** — 게이트가 `load_state_dict` 를 그대로 불러 분류기 머리에서 실패. 검증과 실행이 **같은 로더**를 쓰게 고침. **`strict=False` 안 씀** — 트렁크 키가 빠져도 조용히 통과하면 랜덤 층으로 추론한다. 전처리는 분류와 **같은 함수**(픽셀 상한 포함 · D3). 유사도 주장 없음(10라벨 분류 트렁크). 실측 `vector 128차원` COMPLETED · 데모 4종 전부 무회귀. `test_image_embed` **14종** · 변이 3/3 · `run_tests` 177→**191** · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변 |
| **timeseries.forecast (2026-08-16)** | ✅ **단계 6 ② — 세 번째 모달리티 어휘(`table`)가 같은 형판으로 돌았다.** CSV/JSON 시계열 → 수치 배열 4개. **출력 이름을 Node 가 정하고 있었다** — 계약은 `forecast` 인데 증적엔 `vector` 가 남아 「승인한 것과 실행한 것」이 갈라졌다. Core 가 `output_schema.required[0]` 을 읽어 붙이게 고침(**Node 는 값만 보내고 이름은 주장 못 한다**). **표본 부족은 0 으로 안 채우고 거절** — 채우면 없는 과거를 본 것이 되고 조용히 틀린다. `window` 를 계약에 둔 것도 같은 이유. 학습 데이터 **규칙 생성**(추세+계절성+잡음) · 홀드아웃 MSE 와 **기준선 병기**. 실제 성능 주장 없음. 실측: `forecast=[3.624, 5.161, 5.987, 5.739]` COMPLETED · text/embed 데모 무회귀. `test_series_modality` **18종** · 변이 3/3 · `run_tests` 159→**177** · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변 |
| **text.embed (2026-08-16)** | ✅ **단계 6 ① — `structured` 가 사슬을 탄다.** `text.classify` 와 **같은 특징·전처리**(두 벌 금지 · D3), 출력만 다르다(64차원 벡터). **D-out 이 무는 것을 이 능력이 보였다** — `output_schema — 벡터 64차원이 계약을 만족한다`(전에는 차원이 틀려도 통과). 곁다리로 **D-maxp**(262,144 > 상한 100,000 → FAIL)와 **D-arch 무갱신**도 설계대로 물었다. **라벨 칸을 지어내지 않는다** — 증적에 `label` 키 없음 · `label`·`vector` 둘 다 비면 **Core 가 거절**. **의미적 유사도 주장 없음**(고정 시드 사영). 실행 중 버그 둘(`label` 미초기화 → 배정 전부 FAILED · `CompleteBody.label: str` → 422)을 격리 스택에서 잡았다. `test_embed_modality` **12종** · 변이 3/3 · `run_tests` 147→**159** · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변 |
| **작업 접수 (2026-08-16)** | ✅ **D8′ · Decision A — 거짓말을 시키던 관문을 닫았다.** `POST /v1/tasks` 가 `datasetId` allowlist 를 **무조건** 검사해, 텍스트 작업은 `eurosat-rgb` 를 적어야 통과했다 — **증적에 없던 데이터셋이 남는다.** `inputId` 가 있으면 건너뛴다(바이트가 이미 Core 를 거쳤고 수집 시점에 능력에 묶였다 · 복합 FK). **바이트를 받는 문은 안 건드림** — 절대규칙 7 유지. 실측: `inputId` 없이 allowlist 밖 **400** · 없는 `inputId` **404** · 데모 경로 200 무회귀 · **텍스트 작업 COMPLETED**(`label=url`). `test_task_intake` **6종** · `run_tests` 141→**147** · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변 |
| **structured 출력 검증 (2026-08-16)** | ✅ **D-out — 통과하던 넷이 떨어진다.** `check_output_schema` 를 배열(`items`·`minItems`·`maxItems`)·중첩 객체까지 재귀 검증. **새 의존성 0**(`jsonschema` 안 씀) · DDL 0 · 계약 형식 변경 0. 사유에 **경로**(`boxes[0].h`) — 중첩은 어디가 틀렸는지 없으면 못 고친다. **`bool`을 number 로 통과시키던 것도 막음**(파이썬에서 `bool`은 `int` 하위형). 모르는 어휘(`pattern`·`oneOf`)는 **아는 척하지 않고** 문서에 적음. `closed_set` 판정 **무회귀**(6종 고정). `test_output_schema` **18종** · 변이 3/3 · `run_tests` 123→**141** · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변 |
| **단계 6 준비 (2026-08-15)** | 📄 **문서만 · 구현 0.** [`design/step6-executors.md`](docs/design/step6-executors.md) — **실측: `structured` 출력이 계약 게이트에서 검증되지 않는다**(차원 틀린 벡터·배열 아닌 값·구조 없는 박스가 **전부 통과**). 카탈로그 **26/52 가 `structured`** 라 그쪽 실행기의 선행 조건. **지금까지 주장은 참** — 라우팅되는 건 closed_set 둘뿐이라 `enum` 은 실제로 돌았다. 학습 데이터 라이선스로 카테고리 5등급 분류(**새 데이터 필요 = 대회 트랙 밖**) · 실행기 9단계 형판(2번째부터 싸진다) · 추천 순서 ① 출력검증 → ② 작업접수(Decision 대기) → ③ `text.embed`. **구현은 Decision 후** |
| **text.classify 실행기 (2026-08-15)** | ✅ **단계 5 — 이미지가 아닌 모달리티가 계약 사슬을 탄다.** `arch → 모달리티`(`ARCH_MODALITY`)로 실행기 디스패치 — 전처리 어휘로 짐작하지 않는다(I1). `TinyTextClassifier`(해시 n-gram → Linear · **24,582 파라미터** · scratch) · 학습 데이터는 **규칙 생성**(외부 말뭉치 0 → 라이선스 검증에 얹을 것 없음). 해시는 `blake2b` 고정 — `hash()` 는 실행마다 달라져 학습 모델을 못 쓰게 된다(기준값으로 못박음). **품질 주장 없음**(`quality_profile='none'`). 종단 실측: 계약 게이트 **6종 전부 PASSED**(실추론 `label='email'`) → 바인딩. `test_text_modality` **16종** · 변이 3/3 · `run_tests` 107→**123** · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변. **막힌 칸 하나: `POST /v1/tasks` 가 `datasetId` allowlist 를 무조건 검사** — 텍스트엔 맞는 값이 없다. D8′ 는 「보조」라 했는데 코드는 「필수」. 정책이라 안 건드림 (Decision 대기) |
| **arch 등록 API · 상한 강제 (2026-08-15)** | ✅ **D-arch + D-maxp.** `agent_arch` 는 FK 로 등록을 막는데 **행을 넣는 경로가 없었다** → `GET /v1/arches`(developer) · `POST /v1/arches`(**admin · 추가만**). **갱신·삭제 없음** — `max_params` 를 사후에 바꾸면 이미 통과한 증서의 근거가 바뀐다(D15). 중복은 **409**(조용한 무시 금지). **D-maxp: `max_params` 를 공통 검사로 승격** — 지문 shape 합계로 세므로 torch 없이 판정된다. 그동안 **비참조 모델엔 상한이 아예 없었다.** 종단 실측: 상한 50,000 에 94,538 모델 → **FAIL·바인딩 거부** · 상한 200,000 → PASS · 참조(`TinyEuroSAT`) **6종 무회귀**. API 실측 200/409/400/400. `test_arch_registry` **8종** + 공통집합 소스가드 2종 · `run_tests` 95→**107** · **변이 3/3**(창 넘침·skip 구멍 둘을 변이가 찾아냄) · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변. **남은 것: `max_params` 자체의 상한 없음**(정책 숫자 → Decision) |
| **C2 가중치 지문 (2026-08-15)** | ✅ **이미지 밖 능력이 계약 게이트를 처음 통과했다 (단계 4).** `CONTRACT_CHECKS` 5종 고정 → **arch 로 갈린다**: 공통 4(`input_schema`·`output_schema`·`preprocess`·**`weights_fingerprint`**) + 참조 구현이면 `arch`·`max_params`. 지문은 safetensors **헤더만** 읽어 텐서 이름·shape·dtype 을 sha256 화 — **torch·safetensors 라이브러리 둘 다 안 쓴다**(`s-public` Node 엔 torch 가 없다). 종단 실측: `TinyTextCNN`(비참조) **4종 통과 → PASSED → 바인딩** · `TinyEuroSAT`(참조) **6종 전부**(실추론 포함) — **무회귀**. 비참조는 `arch` 를 `false` 로도 **보고하지 않는다**(「검사 안 했다」의 정직한 표현). 한계(「계약대로 동작은 불보장」)를 **증적에 남긴다**. `test_contract_checks_by_arch` **16종**(변이 3→4건 확인) · `run_tests` 79→**95** · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변. **남은 것: `agent_arch` 등록 API 없음** — 새 모달리티는 DB 직접 삽입이 필요하다 (별 Decision) |
| **능력 카탈로그 52 (2026-08-15)** | ✅ **계약 표면을 52개로 넓혔다 (Decision 2 · 단계 1–3).** 정본 [`spec/capability-catalog.md`](docs/spec/capability-catalog.md) — `output_kind` **10/26/16** · 모달리티별 `preprocess` 어휘 7종(**image 무변경**) · MIME allowlist · 유통 세대. **`0018` — freeform 에 골든 금지**(`ck_capability_golden_scoreable`). 구멍이었다: `mvp_eligible` 만 묶여 있어 **요약 능력에 가짜 골든을 달 수 있었다.** DB 실측 — freeform+golden **거절** · structured+golden **통과**(막힌 건 freeform 뿐). `code.generate`·`tool.plan`·`tool.action` 은 **v제품-2 격리 전 잠금**(`trust_domain_min='team'` · DDL 0). **AV 는 없다고 문서에 박았다.** `test_capability_catalog` **11종**(변이 4/4 확인) · `run_tests` 68→**79** · `clean_room` 9/9 · `prod_room` 27/27 · `acc=0.8500` 불변 |
| **demo.ps1 정렬 (2026-08-15)** | ✅ 로컬 촬영 경로가 `.sh` 와 어긋나 finish **HTTP 400**. `min_per_class_recall` 누락 + claim·직접 `/v1/execute`. → finish 필드 보강 · **Core 중개 폴링**으로 맞춤. 실측: `acc=0.8500` · PASSED · COMPLETED · 「경계」 `team→team` · `M<=M`. wiring 4종 OK |
| **출품 10일 완성도 (2026-08-15)** | ✅ **주장을 정리했다 — 코드 동작은 한 칸만.** README 기대 수치가 `0.7000`(홀드아웃 재추출 전 값)로 남아 있었다 → 정본 `0.8500` · `check_submission` 대조 대상에 **README 추가**(변이 검사 확인). 「데모 compose 는 열려 있다」를 **플래그 이름과 함께** 못박고 세대 9→**17** 정정. 골든셋 정의서 §7 의 `equivalence.max_deviation=0.05` 는 **발급된 적이 없었고**(seed 는 이미 `deviation.enforceable_bound` 로 개정) 문서만 뒤처져 있었다 → seed 에 맞춤. `context-handoff` **D2 취소선**(계약의 *구성*이 폐기 · D18·D20). **증적이 DB 에는 있는데 밖에서 안 보였다** — `GET /v1/tasks/{id}` 가 배정 스냅샷 4열을 안 줘서 API SELECT 를 넓혔다(읽기전용·DDL 0) · `demo.sh`·`demo.ps1` 이 **「경계」 한 줄**을 찍는다. `test_assignment_evidence_wiring` **4종**(신규) 이 schema→API→데모→openapi 사슬 고정 · `run_tests` 64→**68**. **수용 게이트 실측 완료 (2026-08-15 · #75 머지 후 `main`)** — `clean_room` **9/9** · `prod_room` **27/27** · `run_tests` 68 · `check_submission` 21/21. 「경계」 줄이 **데모·강제 두 모드 모두**에서 찍혔다(`task=team -> node=team · capability=M <= node_max=M`) · 골든 `acc=0.8500` `f1=0.8344` 정본 일치 |
| **러닝크루 화면 (2026-08-15)** | ✅ **초대 발행·소진 화면 + 키 입력줄.** `/ui/invite.html`(admin) · `/ui/redeem.html`(**관리 키 불필요** — 초대 토큰이 인증). **소진 화면엔 등급·조직·티어 입력칸이 없다** — 주장할 자리를 안 만든다(절대규칙 4). 토큰은 해시 조각으로 전달·주소창에서 즉시 삭제. 키는 `sessionStorage` 만(탭 닫으면 소멸·URL 미탑재) → **read-auth 이후 못 쓰던 UI 가 강제 모드에서 복귀**. `test_ui_invariants` **8종**(변이 검사 확인) · 강제 모드 실측 401/200 · `prod_room` 27/27. 새 의존성 0 |
| **조직 경계 (2026-08-14)** | ✅ **등급과 소속을 분리 (D24 · `0017`).** `trust_domain='tenant'` 는 민감도지 소속이 아니어서 **A 의 작업이 B 의 기기에 배정됐다** — 조회가 아니라 **실행** 구멍이었다. 스냅샷 2 + 복합 FK 2 + `ck_assignment_org`(**같은 조직이거나 공용이거나**)로 DB 가 판정. `node.org_id IS NULL` = 팀 공용(전 조직 수신). 조직은 **초대장에 박힌다** · Agent 는 공용 카탈로그. **죽어 있던 `owner_id` 하드코딩도 제거.** `check_org_boundary` **14/14**(신규) · 통합 10→**11종** · `clean_room` 9/9 · `prod_room` 27/27. **추가만 · NOT NULL 승격 없음** |
| **조회면 인증·소유권 (2026-08-14)** | ✅ **「증적이 남고 조회된다」의 뒷문을 닫음.** 열린 조회면 15개 중 8개에 역할(공개는 `/health`·카탈로그·allowlist만), `GET /v1/tasks/{id}` 는 **자기 작업만** — 남의 것도 **없는 것도 404**(403은 존재를 흘린다). **DDL 0** — `task.user_id`(B0)를 아무도 안 보고 있었을 뿐. 강제 꺼짐이면 종전대로 통과(`clean_room` 9/9). `check_task_ownership` **10/10**(신규) · `check_enforcement` 23→**30** · `prod_room` 20→**27**. **남은 것: 조직 경계 없음** — developer 키 하나면 tenant 둘을 다 본다 (별 Proposal) |
| **촬영 리허설 (2026-08-14)** | ✅ **D-9 에 런북 타임라인 1회 완주.** `demo.sh` `acc=0.8500` · sanity 3종 FAILED · 위반 **6종 REJECTED** · `proof_ab` A/B 완결 · 증적 출력 · `migrate status` 세대 16 · `check_submission` **20/20**. **촬영일 사고 하나를 미리 잡음** — `demo.ps1`·`smoke_w1.ps1` 이 `arch` 없이 등록해 HTTP 400 (G5 회귀). 촬영은 PowerShell 인데 검증 3종은 `.sh` 만 만져 안 걸리던 구멍. `test_agent_arch_wiring` 으로 고정 |
| **G2 초대 경로 (2026-08-14)** | ✅ **관리 키 없이 함대에 들어온다.** `0016` `node_invite`(추가만) — **등급은 초대장에 박힌다**(소진 본문에 등급 필드 없음 · 절대규칙 4). `team` 초대는 발행 단계에서 거절 · 초대 기기는 채점자 불가(`ck_gate_runner_team`). 만료 7일 · 1회용 · 폐기 · audit, **소진 판정은 DB 조건부 UPDATE**. `check_node_invite` **20/20** · `check_enforcement` 20→**23** · `prod_room` 16→**20**. **수용 게이트가 옛 이미지로 마이그레이션하던 구멍**도 닫음(§3 앞 `dc build`) |
| **G4·G5 (2026-08-14)** | ✅ **안전 사슬 노란 칸 둘 닫힘.** G5 — `POST /v1/agents` 가 `arch` 를 요구(400). 분기는 `_require` **뒤**(앞이면 무인증이 401 대신 422). 등록 스크립트 4개가 학습 기록에서 arch 를 싣는다. **실측: `arch_unbound_routable` 1 → 0**. G4 — 증서 회전 런북(`operate-node.md` §2) · **무중단 불가를 그대로 적음**(활성 증서 1개 제약). **돌려 보고 한 줄 고침** — 멈춘 직후에도 `is_fresh=true`(heartbeat 45초). `check_agent_arch` 9→**13종** |
| **S2 안전 자세 조회면 (2026-08-14)** | ✅ **「누가 내 데이터를 돌릴 수 있나」를 한 면에서 답한다** (G3 닫힘). `GET /v1/ops/safety` — 기기 단위 등급·조달·증서·생사·`accepts_task_domains`·`routable_pairs`·위험 표시 · `by_task_domain` 요약. **읽기전용 · DDL 0 · 새 의존성 0 · 시크릿 없음**(prefix 만). `routable_pairs` 는 `CLAIM_SQL` 후보 조건 그대로 — `check_ops_safety` **21/21** 이 「조회면이 가능이라 한 곳에서 claim 이 실제 배정 · 불가라 한 곳은 claim 도 거절」을 고정. 강제 꺼짐이면 `ok=false`. 통합 8→**9종** · `prod_room` 14→**16종** |
| **절대규칙 7 개정 (2026-08-14)** | ✅ D8′ 정합 — 금지는 「자유 업로드」가 아니라 **비통제 수집**(서명 URL·fileToken). Core 중개 + 계약·해시·크기·MIME·보존은 허용, allowlist 는 **보조**. 규칙서만 결정을 못 따라오고 있었다 (PR #57) |
| **S1 강제 불변식 CI (2026-08-13)** | ✅ **안전 회귀를 CI 가 잡는다.** `check_enforcement` 20종 — 앱 강제 분기 직접 검사(HTTP 서버·새 의존성 0 · `importlib.reload` 로 켜짐/꺼짐 양쪽). **꺼져 있어도 잘못된 키·사칭은 401/403** 을 고정. **변이 검사로 가드 확인** (강제 우회 주입 시 20/20→17/20). 통합 7→8종 |
| **배정 재시도 상한 (2026-08-13)** | ✅ **조용한 무한 재시도 종결.** `claim` 이 `attempt_no` 계수 · `capability.max_attempts`(기본 5) 도달 시 워커가 task `FAILED` · Node 가 `/fail` 로 보고해 `audit_log` 에 이유 기록 · DB 가 상한 초과 배정 거절. **실측: 3회에서 정지, 20초 뒤에도 추가 배정 0** · 골든 `acc=0.8500` 불변 |
| **lease 가 전처리를 나른다 (2026-08-13)** | ✅ **검증과 실행이 같아짐.** `arch`·`max_params` 자리에 전처리도 적재 · 수동 실행 경로(`/v1/execute`)가 배정 행을 버리던 I1 구멍도 닫음. **판별 실측** — 선언만 16×16 L 로 되돌리자 task 가 `ASSIGNED` 에 머물고 채널 불일치 38건 (기본값이면 조용히 성공했을 것). 골든 `acc=0.8500` 불변 |
| **B2 잔여 — preprocess (2026-08-13)** | ✅ `input_schema.preprocess` 선언 자리 신설(`0014`) · 러너가 **선언을 적용해** 검증 · **`CONTRACT_CHECKS` 5 복귀** · 미선언 능력은 계약 게이트 거절. **골든 정확도 `acc=0.8500` 불변** 실측. 실증 16/16 · CI 가드 21/21. 남은 것: 일반 실행은 아직 기본값(lease 가 전처리를 안 나름) |
| **B2 계약 검증 실수행 (2026-08-13)** | ✅ 러너가 `arch`(가중치 로드)·`max_params`(파라미터 수)·`input_schema`(샘플 실추론)·`output_schema`(출력 검증)를 **실행해서** 판정. 샘플=`task_input`(복합 FK) · 샘플 없는 계약 게이트런은 DB 가 거절 · 샘플은 GC 제외 · `preprocess` 는 다음. **arch 틀린 Agent 가 FAILED 로 걸림** 실증 13/13 · CI 가드 18/18 |
| **B1 핫픽스 (2026-08-13)** | ✅ #47 리뷰 반영 — MIME **미선언이면 업로드 400**(`0012` 가 `image.classify` 에 `["image/jpeg"]` 선언) · 업로드 **디스크 스트리밍**(200MB 업로드에 core 상주 메모리 증가 **0MB** 실측 → `mem_limit` 불필요). `max_input_bytes` 불변은 accept(코드 변경 없음). 실증 10/10 |
| **B1 런타임 (2026-08-13)** | ✅ **Core→Node 바이트 전송 완성.** `POST /v1/inputs`(raw body 스트리밍·새 의존성 0) · Node 가 lease 확인 후 받아 **해시 대조** 후 추론·실행 후 삭제 · GC 워커(72h TIMEOUT·종결 후 7일·고아 24h). 별도 볼륨 `capnet_inputs`. 실증 14/14 — **골든셋 40장 밖의 데이터가 처음 흐름** |
| **B1 DDL (2026-08-12)** | ✅ `0011` `task_input` — 크기 계약(32MiB 기본·256MiB 상한) · 보존(종결 후 7일·고아 24h·미완료 72h) · `task.finished_at` · `task_input_purge_due` 뷰. **입력이 수집 시점에 능력에 묶인다**(복합 FK) · 크기는 DB 가 거절. 실증 15/15. **런타임 미착수** — 업로드 API·바이트 저장소·lease 전달·GC 워커 |
| **입력 경로 결정 (2026-08-12)** | ✅ **D22 = Core 중개(2안)** · 서명 URL(1안) 기각 · 데이터셋 등록제(3안) 보조 · **D8′** = 「자유 업로드 금지」→「비통제 수집 금지」. **B1 미착수** — Core→Node 바이트 전송은 아직 없다 (Node 가 `caseId` 로 로컬 골든을 고른다) |
| **② 게이트 선택화 (2026-08-12)** | ✅ **완료 (DDL + 런타임)** — `0010` 품질 프로파일(센티널 CHECK · `gate_run.kind` · 복합 FK) · `POST /v1/capabilities` 가 센티널을 Core 가 채움 · 계약 게이트런(`kind` 는 **능력이 결정**, `contract_checks` 5종 요구). **제약 약화 0 · `claim.py` 무수정.** 실증 DDL 10/10 · API 7/7 · 계약 10/10 · CI 가드 `check_quality_profile` 16/16 → D20. 남은 것: 계약 검증을 **러너가 실제로 수행**(지금은 보고를 받아 적는다) |
| **P1 정문 (2026-08-12)** | ✅ **목표가 제품으로 전환됨.** `compose.prod.yaml` — 인증·증서 강제, postgres 비공개, migrate 수동, `.env` 필수, seed Node `profiles: demo`. 운영 스크립트 7개에 `ccurl` 키 주입. 제품 수용 게이트 `scripts/prod_room.sh` **14/14** · 데모 `clean_room.sh` 9/9 유지 → [`operate-production.md`](docs/guide/operate-production.md) |
| **라이선스 산출물 (2026-08-12)** | ✅ `sbom.json` 에 `psycopg-pool`(LGPL-3.0) 누락 · torch 무버전 → 해소. Dockerfile `ARG` 가 버전 정본 · SBOM 11개 · 붙임1 11행. **`sbom.json` 드리프트 기계 검사는 아직 없음** |
| **새 볼륨 재현 (2026-08-12)** | ✅ README 경로가 `demo.sh` 에서 깨져 있었다 — initdb 는 `schema.sql`(08-03)까지만 넣는데 `0007`–`0009`(08-11)를 적용하는 단계가 없었다. compose 일회성 `migrate` 서비스로 해소 · `CAPNET_AUTO_MIGRATE=0` 으로 끈다 |
| **문서 위생** | README stable-only · 일정 정본 = checklist |
| **역할** | finn · toma · **pl**(동급) · master(merge) — [`github-team-guide`](docs/guide/github-team-guide.md) v1.3 |

### Phase 1 §7.1 좌표 (2026-08-08 실측)

| # | 증명 대상 | 상태 |
|---|-----------|------|
| 1 | `image.classify@1` + 골든셋 | ✅ |
| 2 | Agent **A, B** PASSED | ✅ 사슬 위 실측 (`dummy=false`) |
| 3 | 증명 모드 A/B 교체 할당 | ✅ `honored=true` · assignment 2건 SUCCEEDED |
| 4 | (v4.6) 하한 예측 | ✅ 반증 안 됨 — 통과자 6/6 유지, 최소 0.5 SE |
| 5 | Product Track Agent 선택 없음 | ✅ |

실측 — **홀드아웃 n=300** (2026-08-09, 유효):

| 후보 | 5ep | 10ep | 20ep | 40ep | 80ep |
|------|-----|------|------|------|------|
| TinyEuroSAT | 0.660 ✗ | — | 0.737 | 0.860 | **0.910** |
| TinyEuroSATB | 0.710 | **0.813** | 0.707 | **0.447** ✗ | — |

| 항목 | 결과 |
|------|------|
| 통과율 | **6/8 = 75.0%** — 밴드 안 |
| A/B 편차 (최선 ho80 vs hob10) | **0.0967** · 일치율 0.833 → EXCEEDS |
| A/B 편차 (원래 쌍 ho80 vs hob40) | 0.4633 · 일치율 0.450 → EXCEEDS |
| sanity floor 3종 | 전부 FAILED |
| M25 위반 6종 | 전부 REJECTED |
| 골든셋 누출 | 홀드아웃 n300 **0/300** · 데모 N=40도 holdout 재추출(2026-08-10). **커밋 A는 전수 학습** — 일반화 주장은 재학습 후 |

### 촬영 전 준비 (2026-08-09 완료)

| # | 항목 | 상태 |
|---|------|------|
| ① | **깨끗한 환경 재현** — `scripts/clean_room.sh` · 빈 볼륨 **9/9 통과** (2026-08-11 · 세대 8 기준 재검증) | ✅ |
| ② | `user-guide-ko.md` 새 서사(접수처·장부) | ✅ |
| ③ | README Linux 명령·403 재현·liveness | ✅ |
| ④ | 보고서 PDF·docx | ❌ 촬영 후 |
| ⑤ | 터미널 캡처 | ❌ 촬영 중 |
| ⑥ | Release 태그·zip | ❌ 8/25–26 |

## 체크리스트

6. [ ] 양식·영상·포털 ← **지금 여기**
13. [x] A/B n300 Within · 사슬 위 교체 할당
14. [x] Phase 1 판정 리포트 → **보류(HOLD)**
15. [x] P1-5 완료 — H1~H4. 판정 = **Go 아님**
16. [x] SD-009 계약 재정의 — **C안 채택** (v4.6, 등가성 → 관측값)
17. [x] SD-007 마이그레이션 체계 — 러너·원장·정적 검사. #27 머지 · **실 볼륨 0001–0003 적용 완료**
18. [x] SD-013 골든셋 sha — 선언부 **5곳** 통일 + `check_golden_sha.py`. **재게이트 29건 완료** · `seed-agent` 1건만 남음

## 연구·형제 제품 (대회 Must 밖)

| 항목 | 상태 |
|------|------|
| TeachMe Agent 기획서 | v0.1 · [`docs/research/teachme-plan.md`](docs/research/teachme-plan.md) |

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 0 | **촬영 8/23** — 영상이 보고서를 막는다 (YouTube URL이 양식 필수 칸) | **확정** |
| 1 | 중복수혜 팀 확인 | 제출 전 |
| 2 | **H1–H4를 8/27 전에 할지** (CPU 3–4h · 출품 트랙과 경합) | master |
| 3 | A/B를 보고서 Must로 승격할지 (SD-001) | master |
| 4 | ~~마이그레이션 체계 (SD-007)~~ | ✅ #27 머지 · **실 볼륨 0001–0003 적용 완료** |
| 5 | ~~실험 가중치 `.meta.json` gitignore~~ | ✅ `*.meta.json` ignore · A/B 메타만 예외 |
| 6 | 커밋 A 가중치 `HOLDOUT=1` 재학습 (meta `train_images=27000`) | 출품 전 권장 |
| 7 | 제품 유통 v제품-1 — SD-007 ✅ → **P2-1(tenant 운용) 다음** → credential (D19) | 출품 후 |
| 8 | ~~SD-013 재게이트~~ | ✅ 29건 완료. `seed-agent` 1건도 **SD-015 로 해소** — 시드가 얻을 수 없는 증서를 발급한 결함이었다 |
| 9 | ~~P2-1 tenant 운용~~ · ~~P2-4 node_credential~~ | ✅ 둘 다 완료. 유통 v제품-1 남은 것은 **lease/재할당 운영화 · 기본 모니터링** |
