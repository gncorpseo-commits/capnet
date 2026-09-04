# STATE — 현재 작업 상태

> **갱신: 2026-09-04** · 종착점 = **Phase 3+ 전체** (D16) · 제품 유통 = **D19** · 출품 후 = **D25 트랙 A** · README는 상태 비보유(링크만)

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

> **10회차 (2026-09-04) — 환경이 바뀌었다: Docker 가 생겼다.**
>
> 9회차가 「못 본 것」으로 남긴 세 줄 중 **둘을 실제로 봤다** — 큐 #40 재측정이 문을 열었다.
>
> | 큐 | 결과 | PR |
> |---|---|---|
> | **40** | `docker info` **성공** (9회차는 실패) · `pip`·`pwsh`·`uv`·`ruff`·`pytest` **여전히 없음** | — |
> | **11** | `clean_room.sh` **본실행 통과 9 · 실패 0** — 빈 볼륨에서 전부 재현 | — |
> | **35** | capreq 키 검사가 **낱말 하나만** 보고 있었다 — URL 은 열려 있었다 | [#219](https://github.com/gncorpseo-commits/capnet/pull/219) |
> | **36** | `gh … list` 30 잘림을 **고쳤지만 못박지 않았다** — 검사 0 | [#220](https://github.com/gncorpseo-commits/capnet/pull/220) |
> | **34** | Core 가 부르는 컬럼 **335건 · 드리프트 0** — 세던 검사 0 | (이 PR) |
>
> **큐 #40 이 큐 #11 을 열었다.** 8회차·9회차가 두 번 「환경이 없어 못 봤다」고 적은
> `clean_room` 이 이번에 돌았다 — 골든셋 sha 정합 · M25 위반 시연 6건 · sanity floor 3종 ·
> 실게이트 `acc=0.8500 f1=0.8344` · 능력 호출 · Node 온보딩까지 **9/0**.
> 재현 `bash scripts/clean_room.sh` (별도 프로젝트 `capnet-cleanroom` · 포트 18800/18801 ·
> 운영 스택을 건드리지 않는다).
>
> `run_tests` **705 OK (건너뜀 7)** — 재현 `bash scripts/run_tests.sh` ·
> `check_submission` **28/28** · 건너뜀 **여전히 7** (9회차와 같다).
>
> **이번 회차도 스스로를 정정했다** (실측 규율):
> #36 첫 훑기가 **산문 여덟 줄을 위반으로** 셌고(「말한다」와 「돌린다」의 차이) ·
> 두 번째 판은 **펜스 짝이 뒤집혀** `--limit 30` 뮤테이션을 놓쳤다
> (`handoff` 파일이 통째로 ` ```markdown ` 블록이라 산문이 「안쪽」이 된다).
> **뮤테이션을 안 돌렸으면 「검사 신설」이라고 적고 넘어갔다.**
> #34 첫 추출기가 **멀쩡한 컬럼 넷을 「드리프트」로** 셀 뻔했다 — 다중 `ADD COLUMN` 과
> `) PARTITION BY` 를 못 읽었다. **살아 있는 DB(세대 18)와 대조해서** 잡았다.
> 그 대조는 Docker 가 이번에 생겨서(큐 #40) 가능해진 것이다.
>
> **못 본 것:** `prod_room.sh` 본실행 — 자동 승인 분류기가 실행을 막았다.
> 환경이 아니라 **권한** 문제이므로 9회차의 「docker 없음」과 사유가 다르다. 큐에 남긴다.
> `.ps1` — `pwsh` 없음. capreq 단위 — `httpx`·`fastapi` 없음(정본은 CI).

> **9회차 (2026-09-03) — 시드 큐 12–33.** main HEAD = **`26b5d14`** (#204) ·
> **실행 능력 10종** · 열린 PR **열여덟** (8회차 #200–#202 + 9회차 #205–#218).
>
> `queue-expansion.md`(#203) 가 종료 조건을 개정했다 — **번호 큐 소진 ≠ 종료.**
> 시드 12–40 에서 **열넷**을 처리했고 **넷은 코드가 필요 없다고 판정**했다.
>
> | 큐 | 결과 | PR |
> |---|---|---|
> | **12** | `prod_room` 이 라우트 **24 중 5**만 눌렀다 (공개 GET 6→1 · 인증 GET 18→4) | [#205](https://github.com/gncorpseo-commits/capnet/pull/205) |
> | **22** | 「동명 `.ps1`」이 주소를 박아 뒀다 — **23 중 2** | [#206](https://github.com/gncorpseo-commits/capnet/pull/206) |
> | **33** | 과거 버그 주석 **14 중 2**가 미핀 (`inputs.py` · `_report_failure`) | [#207](https://github.com/gncorpseo-commits/capnet/pull/207) |
> | **14–19** | 절대 규칙 여섯 전수 — **위반 0** · 기계가 잇는다 | [#208](https://github.com/gncorpseo-commits/capnet/pull/208) |
> | **20** | 조용히 삼키는 자리 — **결함 0** · 근거 없이 못 늘게 | [#209](https://github.com/gncorpseo-commits/capnet/pull/209) |
> | **21** | 빈 목록 초록 — **실제 0** · 여덟 자리에 바닥 | [#210](https://github.com/gncorpseo-commits/capnet/pull/210) |
> | **23** | `capreq` 버전이 **네 곳** — 둘로 줄이고 못박음 | [#211](https://github.com/gncorpseo-commits/capnet/pull/211) |
| **24** | `openapi` 요청 본문 — **문서대로 보내면 422** (`nodeId` 누락) | [#213](https://github.com/gncorpseo-commits/capnet/pull/213) |
> | **27** | 카탈로그 「구현됨」 10종 ↔ 등록 경로 — **10/10 있다** | [#214](https://github.com/gncorpseo-commits/capnet/pull/214) |
> | **26** | 「CI 가 본다」가 **거짓** — 건너뛴 일곱은 어디에서도 안 돈다 | [#215](https://github.com/gncorpseo-commits/capnet/pull/215) |
> | **28** | 화면이 **사용자가 시키지 않은 능력**으로 작업을 만들 수 있었다 | [#216](https://github.com/gncorpseo-commits/capnet/pull/216) |
> | **31** | 시크릿 검사가 **CI 워크플로는 안 보고 있었다** | [#217](https://github.com/gncorpseo-commits/capnet/pull/217) |
> | **29** | Core 우회는 **하나뿐**이고 문서가 그렇게 적는다 | [#218](https://github.com/gncorpseo-commits/capnet/pull/218) |
> | **25 · 37 · 13 · 32** | **코드 없음** — 이미 덮였거나 살아 있는 주장이 없다 | — |
>
> `run_tests` **692 OK (건너뜀 7)** — 재현 `bash scripts/run_tests.sh` (#218 트리) ·
> `check_submission` **28/28** · 건너뜀 **한 번도 안 줄었다**.
>
> **이번 회차가 다섯 번 스스로를 정정했다** (실측 규율):
> #207 프로브가 **파이썬 파일 버퍼**를 재고 있었고(결함을 지어낼 뻔) ·
> #209 스캐너가 **`return 1`(실패 코드)을 성공으로** 셌고(`1 == True`) ·
> #210 첫 훑기가 **일흔다섯 자리에 잔소리**를 했고(리터럴 튜플까지) ·
> #217 탐지기가 **`CAPNET_API_KEY` 를 못 잡았고**(낱말 경계) ·
> #218 이 `$node_id`·포트 문자열까지 세어 **「우회 일곱 건」이 될 뻔했다**(실제 1건).
> **다섯 다 「결함」이라고 적기 전에 잡았다.**
>
> **못 본 것:** `clean_room`·`prod_room` 본실행 · 종단 데모 — `docker info` 실패.
> `.ps1` 실행 — `pwsh` 없음. `capreq` 단위 — `fastapi`·`pip` 없음(정본은 CI).

> **8회차 (2026-09-03).** `2c57c1e` (#203 큐 확장 전문) 까지 · 실행 능력 10종.
>
> **자율 모드:** [`docs/bridge/queue-expansion.md`](docs/bridge/queue-expansion.md) (큐·종료 정본 · 시드 12–40) ·
> [`docs/bridge/autonomous-mode.md`](docs/bridge/autonomous-mode.md) (루프) ·
> [`docs/bridge/handoff-long-mode-claude.md`](docs/bridge/handoff-long-mode-claude.md) (WSL 붙여넣기).
> **다음 줄: 큐 #12.** 8회차 PR #200·#201·#202 는 열린 채 쌓을 수 있다.
>
> `run_tests` **571 OK (건너뜀 7)** — 재현 `bash scripts/run_tests.sh` (#196·#188 합친 트리).
> capreq 는 **이 환경에서 못 쟀다** — `pip` 가 없어 `httpx`·`fastapi` 가 빠지고
> 모듈 셋이 임포트에서 죽는다 (`52 ran · errors=3`). 정본은 CI 의 `capreq` 잡 ·
> 설치·재현은 [`docs/guide/testing.md`](docs/guide/testing.md) §2. **「못 쟀다」를 안 적고
> 넘어가면 그것이 바로 이번 회차가 고친 결함 열과 같은 모양이다.**
>
> | Wave | PR | 내용 | main |
> |------|-----|------|------|
> | A | [#105](https://github.com/gncorpseo-commits/capnet/pull/105) | capreq 입력 챗봇 + `text.ner` | ✅ |
> | B | [#107](https://github.com/gncorpseo-commits/capnet/pull/107) | capreq 결과·폴링 UI | `1a15ff1` |
> | B′ | [#109](https://github.com/gncorpseo-commits/capnet/pull/109) | `GET /v1/ops/work-units` (D26) | `7e6d5f9` |
> | C | [#110](https://github.com/gncorpseo-commits/capnet/pull/110) | `text.extract` (8번째) | `30a94fb` |
> | D | [#111](https://github.com/gncorpseo-commits/capnet/pull/111) | `scripts/product_demo.sh` | `6d57a69` |
> | E | [#112](https://github.com/gncorpseo-commits/capnet/pull/112) | capreq 첨부 fix + Ollama 종단 | `a7eed90` |
> | — | [#113](https://github.com/gncorpseo-commits/capnet/pull/113) | 브리지·STATE 동기화 (코드 0) | `5080748` |
> | F | [#114](https://github.com/gncorpseo-commits/capnet/pull/114) | `user-guide-ko.md` §5.1 — Core 중개 입력 두 갈래 | `2e43680` |
> | — | [#115](https://github.com/gncorpseo-commits/capnet/pull/115) | 브리지·STATE (Wave F 닫기 · Wave G Proposal) | `fc69d80` |
> | **G** | [#116](https://github.com/gncorpseo-commits/capnet/pull/116) | **`text.rank` (9번째 실행기)** | **`083d53d`** |
> | — | [#117](https://github.com/gncorpseo-commits/capnet/pull/117) | 브리지·STATE (Wave G 닫기 · Step 3 Proposal) | `22d7769` |
> | H | [#118](https://github.com/gncorpseo-commits/capnet/pull/118) | capreq 가 `fields`·`ranking` 을 그린다 | **`c820fc8`** |
> | — | [#119](https://github.com/gncorpseo-commits/capnet/pull/119) | 브리지·STATE + 라우팅 측정 보고 (코드 0) | `45bf8dd` |
> | — | [#120](https://github.com/gncorpseo-commits/capnet/pull/120) | `scripts/route_bench.py` + 카탈로그 숫자 정정 | **`9b613e4`** |
> | — | [#121](https://github.com/gncorpseo-commits/capnet/pull/121) | 브리지·STATE (Decision (b) ack · Wave I Proposal) | `7f8d8c5` |
> | **I** | [#122](https://github.com/gncorpseo-commits/capnet/pull/122) | **`PATCH /v1/capabilities/{id}` + 데모 3종 upsert** | **`50f51ba`** |
> | — | [#123](https://github.com/gncorpseo-commits/capnet/pull/123) | 브리지·STATE (Wave I 닫기) | `2530ba7` |
> | — | [#124](https://github.com/gncorpseo-commits/capnet/pull/124) | 측정 숫자 재현 규칙 Proposal | **`411be33`** |
> | **J** | [#125](https://github.com/gncorpseo-commits/capnet/pull/125) | **측정 숫자 재현 규칙** (문서만 · `docs/guide/measured-claims.md`) | **`2a40af0`** |
> | **K** | [#126](https://github.com/gncorpseo-commits/capnet/pull/126) | 데모 다섯 종 description upsert (여덟 전부) | `c9fcaf3` |
> | — | [#127](https://github.com/gncorpseo-commits/capnet/pull/127) | 브리지·STATE (Wave K·L) | `60f5b5a` |
> | **L** | [#128](https://github.com/gncorpseo-commits/capnet/pull/128) | **`safety.pii` (10번째 실행기)** | **`d240e57`** |
> | — | [#129](https://github.com/gncorpseo-commits/capnet/pull/129) | 브리지·STATE (Wave K·L 닫기) | `f05676e` |
> | **M** | [#130](https://github.com/gncorpseo-commits/capnet/pull/130) | `chat.html` 렌더러 + 흐름 실행 검증 | `0b4f38c` |
> | **N** | [#131](https://github.com/gncorpseo-commits/capnet/pull/131) | 라우팅 벤치가 10종을 덮게 | `074871c` |
> | **O** | [#132](https://github.com/gncorpseo-commits/capnet/pull/132) | 입력 보존·삭제 검사 (D22 선행 조건) | `834280c` |
> | **P** | [#133](https://github.com/gncorpseo-commits/capnet/pull/133) | 검증 체계 문서 | **`10eba27`** |
> | **Q** | [#134](https://github.com/gncorpseo-commits/capnet/pull/134) | 미매칭이면 할 수 있는 것을 보여 준다 | `82720e8` |
> | — | [#135](https://github.com/gncorpseo-commits/capnet/pull/135) | 브리지·STATE (야간 닫기) | `e0df548` |
> | **R** | [#136](https://github.com/gncorpseo-commits/capnet/pull/136) | **`CHANGELOG` 중복 되돌림 + 무결성 검사** | **`f1dd4c8`** |
> | — | [#137](https://github.com/gncorpseo-commits/capnet/pull/137) | 브리지·STATE (Wave Q·R 닫기) | `7ef3abe` |
> | **S** | [#138](https://github.com/gncorpseo-commits/capnet/pull/138) | capreq 미매칭 UX 문서 · 낡은 숫자 셋 | **`a09de5f`** |
> | — | [#139](https://github.com/gncorpseo-commits/capnet/pull/139) | 브리지·STATE (Wave S 닫기 · Proposal 4건 · verify) | `0beca22` |
> | **T** | [#140](https://github.com/gncorpseo-commits/capnet/pull/140) | `chat.html` 픽스처가 요약기 분기를 다 덮게 | `ad6c290` |
> | — | [#141](https://github.com/gncorpseo-commits/capnet/pull/141) | Proposal 3건 (구현 0) | `309be84` |
> | **U** | [#142](https://github.com/gncorpseo-commits/capnet/pull/142) | openapi 드리프트 검사를 **메서드 수준**으로 | `16ade8c` |
> | **V** | [#143](https://github.com/gncorpseo-commits/capnet/pull/143) | `testing.md` ↔ CI 의존성 드리프트 | `3dbd82a` |
> | **W** | [#144](https://github.com/gncorpseo-commits/capnet/pull/144) | skip 사유 허가제 (V 를 포함) | `2a8d36a` |
> | **X** | [#145](https://github.com/gncorpseo-commits/capnet/pull/145) | **`scripts/capreq_demo.sh`** — 제품 입구 종단 (W 를 포함) | **`fd8750d`** |
> | — | [#146](https://github.com/gncorpseo-commits/capnet/pull/146) | 브리지·STATE (Wave T–X 닫기) | **`a4d47dd`** |
> | **Y** | [#147](https://github.com/gncorpseo-commits/capnet/pull/147) | `CHANGELOG` — U·V·W·X 몰아쓰기 + 갱신일 4줄 | `74d47b9` |
> | **Z** | [#148](https://github.com/gncorpseo-commits/capnet/pull/148) | 건너뛴 건수를 배너까지 | `592a09e` |
> | — | [#149](https://github.com/gncorpseo-commits/capnet/pull/149) | 브리지 — 핸드오프 전사 · 기각 블록 닫기 (코드 0) | `3bb0245` |
> | — | [#150](https://github.com/gncorpseo-commits/capnet/pull/150) | 브리지·STATE (Wave Y·Z 닫기 · verify) | **닫음** (#166·#173 대체) |
> | — | [#151](https://github.com/gncorpseo-commits/capnet/pull/151) | README·사용자 가이드가 `capreq_demo.sh` 를 가리키게 | `707eaaa` |
> | — | [#152](https://github.com/gncorpseo-commits/capnet/pull/152) | `measured-claims.md` 가 손으로 센 개수를 못박고 있었다 | `45a62e8` |
> | — | [#153](https://github.com/gncorpseo-commits/capnet/pull/153) | 브리지 — 보존 TTL 사실 넷 (숫자 확정 0) | `efc747f` |
> | **AA** | [#154](https://github.com/gncorpseo-commits/capnet/pull/154) | **빈 파일을 붙이면 데모 데이터가 대신 돌았다** | `39477d9` |
> | — | [#155](https://github.com/gncorpseo-commits/capnet/pull/155) | 브리지 — 조용한 잘림 Proposal (구현 0) | `a95f8fc` |
> | **AB** | [#156](https://github.com/gncorpseo-commits/capnet/pull/156) | **Core 의 로그가 한 줄도 안 나오고 있었다** | `6919557` |
> | — | [#157](https://github.com/gncorpseo-commits/capnet/pull/157) | 브리지 — 2회차 verify | **닫음** (#163 대체) |
> | **AC** | [#158](https://github.com/gncorpseo-commits/capnet/pull/158) | gate 폐기가 관측 절반을 빠뜨렸다 | `ddbd12b` |
> | **AD** | [#159](https://github.com/gncorpseo-commits/capnet/pull/159) | **Core 와 끊긴 Node 가 한가한 Node 처럼 보였다** | `780e327` |
> | **AE** | [#161](https://github.com/gncorpseo-commits/capnet/pull/161) | **카탈로그를 한 번 못 받으면 영영 안 받았다** | `36e586b` |
> | — | [#162](https://github.com/gncorpseo-commits/capnet/pull/162) | 빈 첨부 회귀를 종단 스크립트에 | `9de5245` |
> | — | [#163](https://github.com/gncorpseo-commits/capnet/pull/163)–[#166](https://github.com/gncorpseo-commits/capnet/pull/166) | 브리지 (gate_run · D27 · 3회차 verify · 실패 이유) | `59be37b`·`be352b1`·`fbe0fec` |
> | — | [#167](https://github.com/gncorpseo-commits/capnet/pull/167)–[#170](https://github.com/gncorpseo-commits/capnet/pull/170) | 문서 (INDEX 자리 · capreq README · 러너 가드 · 머지 안내) | `1a10557`·`f738c0e`·`905c576` |
> | **AF** | [#171](https://github.com/gncorpseo-commits/capnet/pull/171) | **`pass_rate.sh` 가 규칙 가중치를 이미지 후보로 집어 죽었다** | `d5cfbc9` |
> | **AG** | [#172](https://github.com/gncorpseo-commits/capnet/pull/172) | **`regate.sh` 가 폐기된 증서를 재게이트 대상으로 집었다** | `3f3c435` |
> | — | [#173](https://github.com/gncorpseo-commits/capnet/pull/173) | 브리지·STATE — 4회차 (코드 0) | **`6179f42`** |
> | **AH** | [#174](https://github.com/gncorpseo-commits/capnet/pull/174) | **라이선스 고지 검사가 capreq 를 안 보고 있었다** | `94519b1` |
> | **AI** | [#175](https://github.com/gncorpseo-commits/capnet/pull/175) | **SBOM 에 capreq 의존성 둘이 빠져 있었다** | `a1f550b` |
> | **AJ** | [#176](https://github.com/gncorpseo-commits/capnet/pull/176) | EuroSAT 아카이브 sha 가 열 곳에 손으로 적혀 있고 대조가 없었다 | `af25fde` |
> | **AK** | [#177](https://github.com/gncorpseo-commits/capnet/pull/177) | **CI 가 `check_release` 를 안 불렀다** — 로컬에서만 도는 검사 | `ede8d7d` |
> | **AL** | [#178](https://github.com/gncorpseo-commits/capnet/pull/178) | capreq 빌드 잔여물이 무시되지 않았다 | `767a764` |
> | **AM** | [#180](https://github.com/gncorpseo-commits/capnet/pull/180) | **누출 검사가 아무것도 안 보고 「깨끗하다」고 말했다** | **닫음** (#184) |
> | **AN** | [#181](https://github.com/gncorpseo-commits/capnet/pull/181) | **통합 검사 0개도 초록이었다** | **닫음** (#184) |
> | **AO** | [#183](https://github.com/gncorpseo-commits/capnet/pull/183) | **purge 가 0행인데 「지웠다」고 답했다** | **닫음** (#184) |
> | **AP** | [#184](https://github.com/gncorpseo-commits/capnet/pull/184) | **데이터셋 목록 실패 시 화면이 하나 지어냈다** | `cbf0a86` |
> | — | [#182](https://github.com/gncorpseo-commits/capnet/pull/182) | 브리지 — 6회차 닫음 · 머지 안내 (코드 0) | `d37b319` |
> | — | [#185](https://github.com/gncorpseo-commits/capnet/pull/185) | STATE 갱신 · **장기 모드 핸드오프 문서** 신설 (코드 0) | `7b1b065` |
> | **AQ** | [#186](https://github.com/gncorpseo-commits/capnet/pull/186) | **깨진 계약이 「Node 는 칸 이름을 주장 못 한다」를 스스로 껐다** | **닫음** (#196) |
> | **AR** | [#187](https://github.com/gncorpseo-commits/capnet/pull/187) | 방 검사 둘도 **0건이면 「전부 재현된다」** 였다 | **닫음** (#196) |
> | **AS** | [#189](https://github.com/gncorpseo-commits/capnet/pull/189) | 모르는 모달리티가 데모 이미지로 떨어졌다 | **닫음** (#196) |
> | **AT** | [#190](https://github.com/gncorpseo-commits/capnet/pull/190) | 안 푼 머지(충돌 마커)가 초록이었다 | **닫음** (#196) |
> | **AU** | [#191](https://github.com/gncorpseo-commits/capnet/pull/191) | 실행기 없는 모달리티가 이미지 분류기로 떨어졌다 | **닫음** (#196) |
> | **AV** | [#192](https://github.com/gncorpseo-commits/capnet/pull/192) | 라우트가 인증 없이 들어와도 안 걸렸다 | **닫음** (#196) |
> | **AW** | [#193](https://github.com/gncorpseo-commits/capnet/pull/193) | 라우트 역할이 조용히 내려가도 안 걸렸다 | **닫음** (#196) |
> | **AX** | [#194](https://github.com/gncorpseo-commits/capnet/pull/194) | Node 라우트 전수 밖 — 고친 뒤 못박지 않았다 | **닫음** (#196) |
> | **AY** | [#195](https://github.com/gncorpseo-commits/capnet/pull/195) | capreq 루프백 전제가 못박혀 있지 않았다 | **닫음** (#196) |
> | **AZ** | [#196](https://github.com/gncorpseo-commits/capnet/pull/196) | **시크릿이 로그·출력으로 나가는 쪽을 안 봤다** | `e211ab3` |
> | — | [#188](https://github.com/gncorpseo-commits/capnet/pull/188) | Step 0 — STATE · 7회차 브리지 (코드 0) | **`757c133`** |
> | — | [#197](https://github.com/gncorpseo-commits/capnet/pull/197) | STATE·handoff — 7회차 머지 후 HEAD (코드 0) | **`34d943f`** |

> **7회차 (2026-09-02) — 결함·예방 열.** #186–#196(닫음 9) · #188 을 `7b1b065` 위에 머지.
> 충돌 0 · `run_tests` **571 (건너뜀 7)** · `check_submission` **28/28** ·
> 열린 PR **전부 CI 3/3 SUCCESS**.
>
> **열 PR이 한 문장으로 묶인다 — 「안 본 것·못 박은 것·기본값 위험」을 초록으로 지나간다.**
>
> | # | 무엇 |
> |---|---|
> | #186 | 깨진 `required` 가 검사를 꺼서 Node 가 아무 칸이나 보고해도 증적에 적혔다 |
> | #187 | `clean_room`·`prod_room` 이 통과 0 · 실패 0 도 초록 |
> | #189 | 모르는 모달리티 → 데모 이미지 (기본값 위험) |
> | #190 | 문서 충돌 마커가 검사 없이 초록 |
> | #191 | 실행기 없는 모달리티 → 이미지 분류기 |
> | #192–#195 | Core·Node·capreq 라우트·역할·루프백 — **고친 뒤 못박지 않음** |
> | **#196** | **시크릿 ↔ 로그·출력 경로 전수·핀 없음** |
>
> **머지:** 코드 갈래 **#196** 하나 · 문서 **#188**. 브리지 `round7-close` 가 정본.
> **열린 Decision 아홉** (+ `output-required-undeclared-policy`).

> **6회차 (2026-09-02) — 실제 결함 넷.** #180–#184(닫음 3) · #182 를 `6179f42` 위에 머지한
> 트리에서 쟀다: 충돌 0 · `run_tests` **487 (건너뜀 7)** · `check_submission` **28/28** ·
> 열린 PR **전부 CI 3/3 SUCCESS**.
>
> **넷 다 같은 모양 — 「0건·0행·0개」를 「없다·됐다·깨끗하다」로 뭉뚱그린다.**
>
> | # | 무엇 |
> |---|---|
> | #180 | 누출 검사가 건너뛴 매니페스트를 보고도 exit 0 · 「겹침 없음」 |
> | #181 | 통합 러너가 검사 0개인데도 초록 |
> | #183 | purge 가 rowcount 0인데 「purged」 |
> | **#184** | **call.html 이 datasets API 실패 시 가짜 목록을 그림** |
>
> **머지 (2026-09-02).** 코드 갈래 **#184** 하나(#180–#183 스택) · 브리지 **#182** ·
> STATE **#179**. `CHANGELOG` 선두 네 항목(#180→#184 순) — `changelog-changeset-rule` Decision
> **여섯 번째 사례**(쌓기로 대가 회피). 브리지 `track-a-post-round6` 가 정본.

> **4회차 (2026-09-02) — 실제 결함 일곱.** 스물여섯을 `a4d47dd` 위에 전부 머지한
> 트리에서 쟀다: 충돌 0 · `run_tests` **453** · capreq **72 (건너뜀 0)** ·
> `check_submission` 통과 · `check_input_purge` **17/17** · 데모 넷 **exit 0** ·
> 열린 PR **전부 CI 3/3 SUCCESS**.
>
> **일곱 다 한 문장이다 — 「못 했다」를 「없다」·「됐다」로 뭉뚱그린다.**
>
> | # | 무엇 |
> |---|---|
> | #154 | 빈 파일 첨부 → 데모 데이터가 대신 돌았다 (`input_id=null` 인데 `label=annual_crop`) |
> | #156 | Core 의 로그가 한 줄도 안 나왔다 (`grep -c "gc:"` → 0) |
> | #158 | gate 폐기가 「같은 규약」이라 적고 관측 절반을 빠뜨렸다 |
> | #159 | Core 와 끊긴 Node 가 한가한 Node 처럼 보였다 |
> | #161 | 카탈로그를 한 번 못 받으면 영영 안 받았다 (`[]` 는 JS 에서 truthy) |
> | #171 | `pass_rate.sh` 가 규칙 가중치를 이미지 후보로 집어 죽었다 |
> | **#172** | **`regate.sh` 가 폐기된 증서를 재게이트 대상으로 집었다** |
>
> **#172 가 가장 무겁다.** 폐기된 것을 재게이트하면 `UPSERT_AC_PASSED` 가
> `gate_run_id` 를 옮겨 **폐기가 되돌려질 수 있다.** 안 터진 것은 Node 에 그 가중치가
> 없어 건너뛰었기 때문 — **우연이지 방어가 아니었다.** 폐기는 안전 주장 중 하나다.
>
> **게이트 사슬은 무회귀다** — `demo.sh` `acc=0.8500 f1=0.8344` · `sanity.sh` 바닥 셋
> FAILED · `proof_ab.sh` AGREE · `pass_rate.sh` 11/16 · `regate.sh` 대상 없음.
> 앞선 verify 표 셋에 이것들이 빠져 있어서 이번에 채웠다.
>
> **머지 완료 (2026-09-02).** #147–#178 중 **28개** 머지 (닫음 4: #150 #157 #160 #165) ·
> 열린 PR **0** · main **`6179f42`**. 머지 뒤 실측 = `run_tests` **472 (건너뜀 7)**
> — 위 「453」은 **머지 전 스물여섯 트리**의 숫자였다.
> 브리지 `verify-round4-and-merge-guide-v2` 가 정본이었다.
>
> **열린 Decision 일곱:** `11th-capability-timeseries-anomaly` ·
> `changelog-changeset-rule`(대가가 **네 번째로** 실측됐다 — 스물여섯 중 하나만 썼다) ·
> `retention-ttl-policy`(+evidence) · `silent-truncation` · `gate-run-stuck-running` ·
> `failure-reason-not-surfaced` · Next.

> **2회차 (2026-09-02) — 실제 결함 넷.** 열세 PR 을 `a4d47dd` 위에 전부 머지한 트리에서
> 쟀다 — 충돌 0 · `run_tests` **440** · capreq **72 (건너뜀 0)** ·
> `check_submission` 통과 · `check_input_purge` **17/17** · 데모 넷 **exit 0**.
>
> **넷 다 같은 모양이다 — 「초록으로 끝나는데 실은 안 보고 있었다」.**
>
> | # | 무엇 | 어떻게 드러났나 |
> |---|---|---|
> | #154 | 빈 파일을 붙이면 **데모 데이터가 대신 돌았다** | `input_id=null` 인데 `label=annual_crop` · `confidence=0.99` |
> | #156 | **Core 의 로그가 한 줄도 안 나왔다** | `docker compose logs core \| grep -c "gc:"` → **0** |
> | #158 | gate 폐기가 「complete.py 와 같은 규약」이라 적고 **관측 절반을 빠뜨렸다** | `except: pass` — 로거조차 없었다 |
> | #159 | **Core 와 끊긴 Node 가 한가한 Node 처럼 보였다** | `except: return []` = 「일이 없다」와 같은 값 |
>
> **#156 이 가장 넓다.** `gc: purged=N freed=N bytes` 는 **D22 보존 정책이 도는 유일한
> 증거**이고, `gc: pass failed`·`worker: claim failed` 는 **예외 경로**다 — 둘 다
> 「죽지 않는다」로 삼키고 로그로만 알리는데 그 로그가 없었다.
>
> **되짚은 것.** #156 을 찾는 도중 「exhausted task 가 QUEUED 로 멈췄다」고 잘못 봤다.
> GC 주기가 300초라 안 돈 것이었고, 로그가 없어서 멈춘 것처럼 보였다.
> **틀린 진단이 진짜 결함을 가리켰다.**
>
> **Decision 넷이 열려 있다:** `11th-capability-timeseries-anomaly` ·
> `changelog-changeset-rule`(이번에 **대가가 또 실측됐다** — PR 열셋 중 **한 개만**
> CHANGELOG 를 쓸 수 있었다) · `retention-ttl-policy`(+evidence) · `silent-truncation`.

> **Wave Y·Z (2026-09-02) · PR 대기.** 셋을 `a4d47dd` 위에 전부 머지한 트리에서 쟀다 —
> 충돌 0 · `run_tests` **420** · capreq **68 (건너뜀 0)** · `check_submission` 통과 ·
> `check_input_purge` **17/17** · `product_demo`·`pii_demo`·`demo_violations`·`capreq_demo`
> **exit 0**. 실패 0.
>
> **Y 는 규율이 남긴 빚을 갚은 것이다.** `CHANGELOG` 선두를 한 PR 만 건드리는 규율(#136
> 교훈) 때문에 U·V·W·X 가 **항목 없이** 머지됐다. 규율은 통했지만(충돌 0) **뒤따르는
> Wave 가 기록을 못 쓴다**는 대가가 실측으로 드러났고, 그 값을
> 브리지 `changelog-changeset-rule` Decision 에 얹었다.
>
> **갱신일 네 줄은 검사가 요구했다.** `test_doc_counts.TestDocDatesAreNotAncient` 가
> STATE·런북·카탈로그·체크리스트의 갱신일을 최신 `CHANGELOG` 이상으로 요구한다.
> **날짜를 소급해 피하지 않았다** — #142–#145 는 실제로 `2026-09-02 00:39` 에 머지됐다.
> 셋을 훑어 낡은 줄이 없음을 확인하고 날짜만 맞췄다.
>
> **Z 는 #144 의 짝이다.** #144 가 skip **사유**를 허가제로 만들었고, Z 는 **건수**를
> 배너까지 끌어올린다. 「`OK (skipped=7)` 은 초록이고 사람은 마지막 줄을 본다」가
> 실제로 6건을 가렸던 것에 대한 나머지 절반이다.
>
> **Decision 대기 (구현 0):** `11th-capability-timeseries-anomaly` (채택·문턱·이름) ·
> `changelog-changeset-rule` · `retention-ttl-policy`.
> `retrieve.dense` 기각은 **ack 수령 — 유지**.
>
> **머지 (2026-09-01).** #139–#145 일곱 PR · 열린 PR **0**. #139↔#141 은 `inbox-cursor.md`
> 끝에서 충돌 — 머지 전 해결. `CHANGELOG` 선두는 #140 만 (#136 교훈 · 충돌 0).
> U·V·W·X 는 CHANGELOG 항목 **없음** — 한 PR 로 몰아 적는 건 다음에.
>
> **Decision 대기:** 11번째 능력 `timeseries.anomaly` · Proposal 3건
> (`changelog-changeset-rule` · `retention-ttl-policy` · `11th-capability-reject`).
>
> **Wave G — 머지됨 (2026-08-30).** [#116](https://github.com/gncorpseo-commits/capnet/pull/116)
> · main **`083d53d`**. `text.rank` = **9번째 실행기**.
> 카탈로그 §3 #24 에 **이미 선언돼 있던** 능력을 구현한 것이다. **DDL 0 · 새 의존성 0 ·
> 새 학습 0 · 외부 말뭉치 0.**
>
> - 첫 비어 있지 않은 줄이 **질의**, 나머지가 후보. 점수는 **자카드** · 동점은 원래 줄 순.
>   `overlap`(겹친 토큰)을 내놓는다 — **왜 그 점수인지 대조**할 수 있어야 한다.
> - **뜻을 모른다.** 「자동차」와 「차량」은 안 겹친다. 의미 유사도는 `text.embed`,
>   학습된 관련도는 `retrieve.*` 몫이라고 등록 설명에 **이름으로** 적었다.
> - **종단 실측이 한계도 같이 보였다** — 「쿼리를」·「인덱스로」의 조사 때문에 사람 눈에
>   1위만큼 관련 있는 줄이 0.1667 이 됐다. 좋아 보이는 예시로 바꾸지 않고 카탈로그에 적었다.
> - **이웃 라우팅을 뺏었는지 격리해서 쟀다** (n=5 · `qwen2.5:3b`) — `text.rank` 있는/뺀
>   카탈로그의 **차이만** 본다. 자기 것만 가져갔고 나머지 네 줄은 전후가 같다.
>   `text.extract`→`text.ner` 미스는 **빼도 똑같다**(이 PR 이 만든 것이 아님 · 범위 밖).
> - `run_tests` 291 → **322** (`test_text_rank.py` 31종) · `check_submission` **27/27** ·
>   필수 가중치 7 → **8종** · `clean_room` **9/9** · `prod_room` **27/27**
>   (`image.classify` 무회귀) · `product_demo.sh`·`text_rank_demo.sh` **exit 0**.
>
> **master Decision (2026-08-30): (a) accept.** 규칙·`overlap`·`quality_profile='none'` 그대로.
> (b) 점수 규칙 변경 · (c) 이웃 설명 수정은 **범위 밖**으로 확인.
>
> **남은 별건:** `text.ner`↔`text.extract` 라우팅 미스 — 손대려면 **별 Proposal** +
> 라우팅 무회귀 실측 필수. 이번에 고치지 않았다.

> **다음 = Step 3 · capreq 결과 표시 (2026-08-30).** 브리지 Proposal
> `capreq-result-view-plus-two`.
> `results.py` 가 #107 때(능력 넷) 쓰인 뒤로 **`text.extract`(`fields`)·`text.rank`(`ranking`)**
> 가 들어왔는데 요약기가 그 칸을 모른다 — **아홉 중 둘이 제품 입구에서 원시 JSON 으로 보인다.**
> 표시 계층만 고친다 · **새 의존성 0** (Playwright 는 별도 Decision).
> **브라우저 JS 렌더링은 #107 부터 계속 미확인** — 헤드리스가 없다. 본 것만 말한다.
>
> master 우선순위: (a) 이 Step 0 → (b) Step 3 → (c) 카탈로그 +1 →
> (d) D4 조회 인증 · `tool.*` · LLM-as-Node · 태그 재발행은 **Proposal 만**.
>
> **구현 = [#118](https://github.com/gncorpseo-commits/capnet/pull/118) 머지됨** ·
> main **`c820fc8`**.
> `fields`(필드 표) · `ranking`(질의 + 순위 표) 렌더러 · `other` 폴백은 남긴다.
> **새 주장 0** — `score` 를 관련도로 부르지 않고 화면에 「겹친 낱말 수로 매긴 순서입니다 —
> 뜻을 비교한 것이 아닙니다」를 붙인다. 재정렬 없음(검사로 고정).
> **화면 자르기는 데이터 자르기가 아니다** — 앞 20개만 그리되 `count` 는 전체를 말한다.
>
> **`chat.html` 에 검사가 하나도 없었다** — 이 드리프트가 #110·#116 두 번 난 이유다.
> `test_chat_html_unit.py` 신설: `summarize_result` 를 실제로 돌려 나온 칸마다 화면에
> 그리는 자리가 있는지 본다(칸 목록을 손으로 두 번 적지 않는다). 변이로 확인 —
> `result.ranking` 을 전부 지우면 실패한다. **한계:** 부분 문자열 검사라 반쯤 지우면
> 통과하고, **브라우저 렌더링은 여전히 못 본다**(헤드리스 없음 · Playwright = Decision).
>
> capreq 단위 38 → **52** · 살아 있는 Core `/api/tasks/{id}` 실측에서 `text.rank`·
> `text.extract` 둘 다 구조화 요약으로 나왔고 `other` 로 새지 않았다.
>
> **능력을 더할 때 따라와야 하는 것에 「화면」이 빠져 있었다** — #110·#116 체크리스트에
> 그 줄이 없었다. 이제 검사가 막는다.

> **라우팅을 제대로 쟀다 — 고치려던 것은 안 고쳤다 (2026-08-30).** 브리지
> `routing-measured-not-fixed`. master 가 「별건 · 실측 필수」로 못박은 `text.ner`↔`text.extract`
> 항목이다. **고치기 전에 재는 것**부터 했고 그 결과가 계획을 바꿨다.
>
> - **#116 Confirm §4 의 미스 보고는 취소한다.** 「제목·담당자…」→`text.ner` 은 **능력 5종만
>   등록된 스택에서 n=1** 로 본 것이었다. 9종 등록 · R=5 로 다시 재니 **5/5 로 맞게 간다.**
>   대신 재현되는 미스는 따로 있다 — 「날짜랑 URL 전부 뽑아줘」→`text.extract` **5/5**.
> - **홀드아웃(수정안을 만들 때 안 쓴 12개 × R=5) 결과:**
>   live 설명 **30/60** · 저장소 설명 **40/60** · 내 수정안 **40/60**.
> - **내 수정안은 넣지 않는다.** 튜닝 세트에서 55→60 이었지만 홀드아웃에서 **순 효과 0** —
>   미스 하나를 고치고 다른 하나를 깼다. **자기가 고른 프롬프트에 맞춘 것**이었다.
> - **#110·#116 의 경계 문장은 효과가 있었다** (30→40). 방향은 옳았다.
> - **진짜 결함:** `POST /v1/capabilities` 는 같은 `(code,version)` 에 **갱신 경로가 없고**
>   데모는 오류를 삼키고 기존 id 를 쓴다 → **저장소에서 설명을 고쳐도 이미 등록된 스택에는
>   영원히 안 들어간다.** 그 차이가 홀드아웃 **10점**이다. 빈 볼륨은 저장소 설명으로 뜨므로
>   **오래 돌아간 스택만** 나빠진다 — 그래서 아무 검사도 못 봤다. #118 의 `chat.html`
>   드리프트와 **같은 종류**다.
> - **Core 변경이라 고치지 않았다** — 갱신 경로 신설 vs 버전 올리기 vs 문서화는 Decision.
> - 문서의 라우팅 숫자(#110 「4/5→5/5」 · #116 n=5 표)는 **자기가 고른 프롬프트**였다.
>   홀드아웃이 40/60 이라는 사실을 옆에 적어 **주장을 좁힌다**.
>
> **하네스·정정 = #120 머지됨 (`9b613e4`).** `scripts/route_bench.py` — 튜닝/홀드아웃을 나누고
> **기본값이 `--set holdout`** 이다(좋아 보이는 숫자가 먼저 나오면 안 된다).
> `tests/test_route_bench.py` 12종 · `run_tests` 322 → **334**.
> 커밋한 스크립트로 재현 확인: live 튜닝 55/60 · **live 홀드아웃 30/60** ·
> **repo 홀드아웃 40/60**.

> **Decision 도착 · 다음 = Wave I (2026-08-31).** master 채팅 Decision (브리지
> `routing-measured-not-fixed`):
>
> - **(a) 설명 튜닝은 하지 않는다** — 튜닝 세트 개선 ≠ 홀드아웃 개선. **문구를 홀드아웃에
>   맞추지 않는다.**
> - **(b) 드리프트는 `PATCH /v1/capabilities/{id}` 로** — **`description` 만** · **DDL 0** ·
>   계약 JSONB 불변. `@2` 버전 올리기·문서-only 는 **범위 밖**.
> - (c)(d) 는 #120 으로 **done**.
>
> **Wave I 범위** (브리지 Proposal `capability-description-patch`):
> admin PATCH 라우트 + Pydantic `extra="forbid"`(화이트리스트를 손으로 세지 않는다) +
> 데모 **셋**(`ner`·`text_extract`·`text_rank`)에 upsert 한 단계.
> 계약 필드(`input_schema`·`compute_tier`·`golden_*` …)는 **전부 400** — 그것들이
> `task_input` 복합 FK·`gate_run`·`assignment` **스냅샷의 원본**이기 때문이다.
>
> **재측정은 실측만 적는다** — 「이제 40/60 보장」 같은 목표치를 쓰지 않는다.
> 이 Wave 가 하는 일은 **데모의 정본을 DB 에 동기화**하는 것뿐이고, 문구는 저장소 그대로다.

> **Wave I — 머지됨 (2026-08-31).** [#122](https://github.com/gncorpseo-commits/capnet/pull/122)
> · main **`50f51ba`**. `PATCH /v1/capabilities/{id}`.
> **DDL 0 · 새 의존성 0 · 계약 JSONB 불변.**
>
> - 연 것은 **`description` 하나**다. 계약 칸은 전부 400 — `task_input` 복합 FK·`gate_run`·
>   `assignment` **스냅샷의 원본**이라 움직이면 이미 찍힌 스냅샷이 거짓말이 된다.
>   화이트리스트를 손으로 세지 않는다(`extra="forbid"`).
> - 데모 **셋**이 등록 본문과 DB 를 비교해 **다를 때만** PATCH. 실측에서 `text.ner`·
>   `text.extract` 는 옛 문자열 → 저장소 문구로 바뀌었고 **`text.rank` 는 이미 최신이라
>   건너뛰었다.** 동기화 뒤 **live == repo (9종 일치)**.
> - `run_tests` 334 → **352** · `check_capability_patch` **6/6**(계약 16칸 PATCH 전후 동일) ·
>   변이로 가드 확인(SET 절 2종 · `extra:forbid` 1종).
>
> **철회: #120 의 「저장소 설명 40/60」.** 그 값은 `route_bench --descriptions repo` 로 잰
> 것인데, 그 경로가 `CapabilityInfo` 를 새로 지으며 **`output_kind` 를 떨어뜨리고 있었다.**
> 라우터 프롬프트가 `kind=` 를 넣으므로 **한 번에 둘을 바꿔 놓고 설명 덕이라 읽은 것**이다.
> `dataclasses.replace()` 로 고쳤고(칸을 손으로 세지 않는다) 같은 조건은 **37/60**.
>
> **지금 서 있는 숫자** (홀드아웃 12개 × R=5): DB 가 낡았을 때 **30/60**(1회) ·
> 동기화 뒤 **36·36·38**(3회) · `repo` **37**.
> **개선폭을 말하지 않는다** — 같은 조건도 **2점씩 흔들린다**(이것도 이번에 처음 쟀다).
> 「5/5 아니면 0/5라 결정적」이라던 앞선 관찰도 과했다.
> 드리프트는 **메커니즘으로 확인**됐고 **크기는 지금 데이터로 말할 수 없다** —
> 코드·데모의 「10점 차」 문구도 전부 걷어냈다.
>
> **이번 세션의 공통 원인: 정본이 둘이면 갈라진다.** `chat.html`(#118) · 카탈로그 설명(#122) ·
> **하네스 자체**(#122) — 셋 다 같은 모양이다. 하네스도 검사가 필요하다는 것을 이번에 배웠다.

> **측정 숫자 재현 규칙 — Proposal 대기 (2026-08-31).** 브리지
> `measured-claims-repro-command` · master Decision 으로 올렸다. **코드 0.**
>
> 규칙안: 「측정 숫자를 카탈로그·`STATE.md` 에 쓸 때 같은 커밋에 재현 명령을 붙인다.
> 없으면 숫자를 쓰지 않는다.」
>
> - 올리기 전에 **셌다** — 카탈로그의 「재야 나오는 숫자」는 **8곳**이고 그중 일곱은 이미
>   `scripts/route_bench.py` 를 가리킨다. 규칙이 새 일을 만드는 게 아니라 최근 몇 Wave 가
>   하던 것에 이름을 붙이는 쪽이다.
> - **범위를 좁혀 역제안했다** — 「재야 나오는 숫자」(`acc=`·홀드아웃 `N/M`·ms)만.
>   「9종」·「352」 같은 **개수는 세면 나오는 값**이라 이미 `check_submission`·
>   `test_report_claims` 가 실물과 대조한다. 거기에 명령을 적으라 하면
>   `run_tests` 를 353번 적는 일이 된다.
> - `CHANGELOG` 은 **그때의 기록**이라 재현이 원리적으로 안 된다. 명령 대신
>   **「무엇으로 쟀나」**(도구·조건·표본)를 적자고 제안했다.
> - **한계를 같이 적었다:** 이 규칙은 #120 의 「40/60」을 **못 막는다.** 명령은 있었고
>   **도구가 틀렸다.** 그건 다른 조건과의 **대조**가 잡았다 — 그러니 이 규칙을
>   드리프트 대책으로 팔지 않는다.
>
> **Decision 도착 (2026-08-31):** (a) 범위 좁힘 accept · (b) `CHANGELOG` 은 명령 대신
> 「무엇으로 쟀나」 accept · **(c) (A) 문서만** · (d) `docs/guide/` 정본.
> (B) 좁은 검사는 **이번 Wave 에서 하지 않는다** — 카탈로그가 이미 거의 지키고 있어
> 값이 크지 않다. 필요해지면 별 Proposal.

> **측정 숫자 규칙 — 머지됨 (2026-08-31).** [#125](https://github.com/gncorpseo-commits/capnet/pull/125)
> · main **`2a40af0`**. **코드·DDL·의존성·CI 검사 0.**
>
> - **정본 = [`docs/guide/measured-claims.md`](docs/guide/measured-claims.md)** ·
>   `CLAUDE.md` 는 **한 줄 + 링크** (두 곳에 적으면 갈라진다).
> - `CLAUDE.md` 안에서는 **절대규칙이 아니라 「작업 방식」**에 넣었다. Decision 자신이
>   「운영 규칙이지 제품 주장·스키마 결정이 아님」이라 D-결정 승격을 안 했는데,
>   절대규칙 머리말은 「어기면 **핵심 주장이 무너진다**」다. 그 여덟과 같은 칸에 두면
>   **그 여덟의 무게가 내려간다.** ack 를 청했다 — 되돌리기 한 줄이다.
> - **규칙이 못 막는 것을 문서 본문에 적었다** — #110·#116 은 막지만 **#120 「40/60」은
>   못 막는다**(명령은 있었고 **도구가 틀렸다**). 「드리프트 대책으로 팔지 말라」를
>   브리지에만 두면 다음 사람이 안 본다.
> - guide **§7 이 자기 처지를 적는다** — (A) 는 검사가 없으니 **이 문서 자신이 「적혀만 있고
>   기계가 잇지 않는 줄」**이다. (B) 로 갈 조건도 같이 적었다.
>
> **master ack (2026-08-31):** `CLAUDE.md` 위치를 「작업 방식」으로 둔 것 **accept** —
> 절대규칙 9번으로 올리지 않는다. **(B) 좁은 검사는 보류.**
> stale `open` 54건은 **(3) 안** — 일괄로 닫지 않고 **`STATE.md` 를 정본**으로 둔다.

> **Wave K — 머지됨 (2026-09-01).** [#126](https://github.com/gncorpseo-commits/capnet/pull/126)
> · main **`c9fcaf3`**. **코드·DDL·의존성 0.**
>
> - Wave I 가 셋만 고쳤던 데모 upsert 를 **나머지 다섯**(`text.embed`·`text.classify`·
>   `table.extract`·`timeseries.forecast`·`image.embed`)까지 마쳤다. 이제 **능력을 등록하는
>   스크립트 여덟 개 전부**가 「다를 때만」 PATCH 한다.
> - **검사를 목록에서 파생으로 바꿨다** — 데모 이름을 손으로 세고 있어서 **아홉 번째에서
>   또 갈라질 자리**였다. 「`POST /v1/capabilities` 를 하는 스크립트」를 찾아서 전부 본다.
>   `demo.sh` 는 **seed 가 넣으므로 대상이 아니다**(예외가 아니다 · 검사가 그것도 고정).
> - **드리프트를 일부러 만들어 봤다** — `text.classify`·`table.extract` 의 DB 설명을
>   저장소에 없는 문자열로 바꾼 뒤 돌리니 그 둘만 PATCH 가 뛰고 셋은 건너뛰었다.
>   다섯 다 종단 완주 · 그 뒤 **능력 9종 설명이 저장소와 전부 일치**.
>   재현: `bash scripts/<이름>_demo.sh`.
> - `run_tests` 352 → **355** · 변이로 확인(`table_demo` 에서 upsert 를 지우면 4종 실패).
> - **라우팅 숫자를 적지 않았다** — 이 스택은 이미 동기 상태여서 「고치기 전」이 없다.

> **Wave L — 착수 (2026-08-31).** 브리지 Proposal `safety-pii-catalog-plus-one`.
> 카탈로그 §Safety **#49 `safety.pii`** — **10번째 실행기**. **DDL·새 의존성·새 학습·
> 외부 데이터 0.** `step6-executors.md` §3 이 「모델 없이도 됨 — 규칙 기반이 정직한 구현」으로
> 지목한 후보다 (Language 잔여는 전부 `freeform` 이라 채점이 금지돼 있다).
>
> **이름이 위험한 능력이라 규율을 먼저 정했다.** 「PII 를 찾는다」는 능력이 놓치면
> 없느니만 못하다 — 사람은 「검사했으니 없다」로 읽는다. 카탈로그의 기존 선례
> (`safety.malware_hint` 의 **「탐지가 아니라 참고」**)를 그대로 따른다:
>
> - 결과가 **`patterns_checked`** 를 들고 다닌다 — **무엇을 찾아봤는지**를 결과가 말한다.
>   목록에 없는 것은 **찾지 않았다**는 뜻이지 없다는 뜻이 아니다
> - `krrn_like`·`card_like` 의 `_like` 는 **꼴이 같다**는 뜻이지 실제 번호라는 뜻이 아니다
> - span 의 `text` 를 **가려서** 낸다 — 위치는 주되 **결과 자체가 새 유출면이 되지 않게**
> - **마스킹·삭제 도구가 아니고, 컴플라이언스를 주장하지 않는다** · `quality_profile='none'`
> - **capreq 표시를 같은 PR 에서 함께 고친다** (#118 교훈 — 능력을 더하면 화면이 따라와야 한다)
>
> **구현 = [#128](https://github.com/gncorpseo-commits/capnet/pull/128) 머지됨** ·
> main **`d240e57`**. **실행 능력 9종 → 10종.**
>
> - 규칙 7종 (`email`·`ipv4`·`ipv6`·`uuid`·`krrn_like`·`card_like`·`phone_kr_like`).
>   `krrn_like` 는 **앞 6자리가 달력에 맞아야** 하고 `card_like` 는 **Luhn 통과**해야 한다 —
>   **Luhn 은 오타 검사지 실재 검사가 아니다.** 그래서 `_like` 다.
> - **`krrn_like` 를 남겼다** (Proposal §6-(c)). 빼면 「PII 를 본다면서 가장 흔한 것을 안 본다」가
>   된다. 대신 규율을 세 겹 — 달력 검사 · **앞 6자리까지 마스킹** · 이름·설명에 「꼴이 같다」.
> - **종단 실측:** 게이트 6검사 OK · `gate_run PASSED` → COMPLETED · `team → team` · `M ≤ M`.
>   **가짜 카드와 날짜꼴 아닌 것이 걸러졌고** 원문은 전부 가려졌다 — 데모가 검사한다.
>   capreq `/api/tasks/{id}` 에서도 `pii` 로 구조화돼 나온다.
>   재현: `bash scripts/pii_demo.sh`.
> - `run_tests` 355 → **384** · capreq 52 → **56** · `check_submission` **28/28**
>   (가중치 8 → **9종**) · `check_release` OK · **`clean_room` 9/9 · `prod_room` 27/27**
>   (`demo.sh` 강제 모드 통과 = **`image.classify` 무회귀**) · `product_demo.sh` exit 0.

> **정정 — 「파일이 겹치지 않는다」는 틀렸다 (2026-09-01).** #126·#127·#128 에 그렇게
> 적었는데 **확인하지 않고 적은 것**이었다. 실제로 합쳐 보니 **#126 과 #128 이 둘 다
> `CHANGELOG.md` 최상단**을 건드려 충돌한다(그 한 곳뿐 · 해결은 「둘 다 유지, 최신이 위」).
>
> **합친 상태에서는 `run_tests` 387 OK · `check_submission` 28/28.**
> 그리고 Wave K 가 데모 목록을 **파생**으로 바꾼 덕에 **Wave L 의 `pii_demo.sh` 를 아무도
> 손대지 않았는데 검사가 알아서 집었다**(9종) — 손으로 셌다면 8 에서 멈춰 새 데모만
> 검사 밖이었을 것이다. **합쳐 보기 전에는 알 수 없었다.**
>
> **머지 순서: #126 → #127 → #128.** 3번에서 `CHANGELOG` 충돌 1건.
> `#128` 을 `#126` 위에 미리 얹지 않은 것은 **stacked PR 금지** 때문이다 — 충돌을 없애려면
> 그 규칙을 어겨야 해서 **규칙을 지키고 충돌을 알리는 쪽**을 골랐다.

> **야간 자율 · Wave M 착수 (2026-09-01 01:40).** 브리지 `night-mode-autonomy` ·
> `chat-render-probe`. master 가 **05:00 까지 스스로 승인하며 진행**하라고 위임했다.
> 되돌리기 비싼 것(스키마·DDL·제품 보장 문구·contest 태그)은 **자율 승인 대상이 아니다.**
>
> **Wave M = `chat.html` 을 실제로 그려 본다.** #107·#112·#118·#128 네 번 연속으로
> 「브라우저 렌더링은 못 봤다」고 적은 자리이고, **거기서 결함이 두 번 나왔다**
> (#118 원시 JSON · #128 고지 개수). **가장 오래 미확인으로 남은 것**이라 골랐다.
>
> **Playwright 를 쓰지 않는다.** `chat.html` 이 실제로 쓰는 브라우저 API 가 적어서
> (`document` 12 · `fetch` 4 · `addEventListener` 3 · `window` **0** · `localStorage` **0**)
> **최소 스텁**으로 `<script>` 를 통째로 실행할 수 있다 — **npm 패키지 0.**
> `node` 가 없으면 **skip** 한다(이 WSL 에 없다) — 루트 `run_tests` 의 「의존성 설치 없음」을
> 깨지 않는다.
>
> **구현 = [#130](https://github.com/gncorpseo-commits/capnet/pull/130) (PR 대기).**
> 렌더러(31종)뿐 아니라 **흐름 전체**(28종)까지 넣었다 — 보내기 → 라우팅 → 폴링 → 결과.
>
> - **#112 의 클라이언트 짝을 처음 봤다.** 그때 고친 것은 서버 쪽이고, **클라이언트가
>   파일을 `FormData` 에 실제로 담는지는 아무도 확인한 적이 없었다.** 맞게 담고 있었다.
> - **문자열 검사가 못 잡던 것을 잡는다** — `result.pii` 몸통만 지우면 문자열 검사는
>   62 OK 로 통과하고 실행 검사는 7종으로 잡는다(변이 확인). 첨부·폴링 변이도 각각 1·5종.
> - **첫 실행에서 24종이 한꺼번에 실패했다** — 스텁에 `childElementCount` 가 없어서였다.
>   **스텁 쪽 결함**이라 고쳤고 주석에 남겼다. **프로브도 틀릴 수 있다**(#120 하네스와 같은 자리).
> - capreq 56 → **66**(node 있을 때) · skip 6(없을 때) · **CI 로그에서 `Ran 66 · OK` 확인.**
>
> **여전히 못 보는 것:** 실제 브라우저의 CSS·레이아웃 · 파일 선택기의 OS 상호작용.
> 그래서 「브라우저에서 봤다」고 쓰지 않고 **「렌더러·흐름을 실행해 DOM 을 봤다」**고 쓴다.

> **Wave N — 착수 (2026-09-01 02:00).** 라우팅 벤치가 **10번째 능력을 안 덮고 있었다.**
> 카탈로그는 `safety.pii` 를 「구현됨」이라 하는데 `scripts/route_bench.py` 의 프롬프트
> 세트와 `test_route_bench.IMPLEMENTED` 는 **9종에서 멈춰 있었다** — `IMPLEMENTED` 가
> **손으로 센 목록**이라 검사가 못 잡았다.
>
> **이번 달 네 번째 같은 모양이다** (데모 목록 · 자른 사실 고지 · 바이트 동일 문구 · 여기).
> `IMPLEMENTED` 를 **카탈로그의 「✅ 구현됨」 행에서 파생**으로 바꾸자 **그 자리에서
> 실패가 떴다** — 그게 이 Wave 의 시작이다.
>
> **구현 = [#131](https://github.com/gncorpseo-commits/capnet/pull/131) (PR 대기).**
> 실측: 능력 10종 · 홀드아웃 13개 × R=5 → **42/65** · `safety.pii` **5/5** ·
> **기존 12개 37/60**(이전 밴드 36·36·38 안) — **10번째 능력이 이웃을 밀어내지 않았다.**
> 재현: `PYTHONPATH=capreq/src python3 scripts/route_bench.py --set holdout --repeats 5`.
> **개선은 주장하지 않는다.**

> **Wave O — PR 대기 (2026-09-01).** [#132](https://github.com/gncorpseo-commits/capnet/pull/132)
> **D22 가 「선행 조건」이라고 못박은 입력 보존·삭제에 검사가 하나도 없었다.**
> 구현은 돼 있었다(`task_input_purge_due` 뷰 · `mark_purged` · GC) — **검사만 없었다.**
> `tests/integration/check_input_purge.py` **17종** · **코드 0 · DDL 0 · 정책 숫자 0.**
>
> - 없으면 조용히 무너지는 것: **뷰의 샘플 제외(0013 B2)가 빠지면 계약 샘플 바이트가
>   24h 뒤 지워지고 게이트가 통째로 못 돈다** · `mark_purged` 가 행까지 지우면
>   「어디로 갔는지 답한다」가 거짓이 된다 · `STORED` 조건이 빠지면 GC 가 무한 재시도한다
> - 「**바이트만 지우고 행은 남는다**」를 고정했다 — `PURGED` 뒤에도 `sha256`·크기·MIME·
>   올린 주체가 그대로다. **이게 「어디로 갔는지」에 답하는 값이다.**
> - **정책 숫자(24h·7d·72h)는 바꾸지 않았다** — 되돌리기 비싼 제품 결정이라 야간 자율
>   대상이 아니다. **지금 값을 읽어서 고정할 뿐이다.**
> - CI 통합 검사 14 → **15 통과** 확인.

> **파생으로 바꾸지 않은 자리도 있다 (2026-09-01).** `check_submission.REQUIRED_WEIGHTS` 는
> 손으로 센 목록이지만 **그대로 뒀다.** 파일 시스템에서 파생하면 **누가 가중치를 지웠을 때
> 목록도 같이 줄어들어 아무것도 안 걸린다.** 「목록을 파생으로」가 언제나 옳은 것이 아니라
> **그 목록이 무엇을 지키는가**에 달렸다.

> **Wave P — PR 대기 (2026-09-01).** [#133](https://github.com/gncorpseo-commits/capnet/pull/133)
> `docs/guide/testing.md` 가 이번 야간에 생긴 **두 부류를 몰랐다** — `node` 실행 프로브
> (없으면 skip)와 라우팅 벤치(수동). §4.6 을 채웠다. **문서만 · 코드 0 · 검사 0.**
>
> **이 Wave 의 중심은 「안 만든 것」이다.** 「능력 N종」이 박힌 자리에 검사를 붙이려다
> **대부분이 과거 서술**임을 봤다 — 「그때 5종만 등록된 스택에서」(정정 기록) ·
> 「능력 6종이 같은 사슬을 통과했다」(**제출 원고**). 일괄 검사를 붙이면 **설명을 지워야
> 통과하는 검사**가 된다(`_srcguard` 의 다섯 사고). **그래서 만들지 않았다.**
>
> **이번 야간에 「안 하는 쪽」을 두 번 골랐다** — 위 `REQUIRED_WEIGHTS` 와 여기.
> 「목록을 파생으로」도 「모든 것에 검사를」도 규칙이 아니다. **그 목록이·그 문장이 무엇을
> 지키는가**에 달렸다.
>
> 대신 **내 문서의 낡은 예시**를 고쳤다 — `measured-claims.md` 가 「능력 9종」을 예로
> 들고 있었는데 10종이 되면서 낡았다. **규칙 문서가 자기 말을 안 지키는 꼴**이라
> 개수 예시는 `N` 으로, 측정 예시에는 **언제 잰 것인지**를 붙였다.

> **Wave Q — 머지됨 (2026-09-01).** [#134](https://github.com/gncorpseo-commits/capnet/pull/134)
> · main `82720e8`.
> **이번 야간의 첫 제품 개선이다.** 라우터가 못 고르면 화면이 「(미매칭)」 한 줄로 끝나
> **사용자가 무엇을 물어야 하는지 알 길이 없었다.** `/api/capabilities` 는 서버에 있는데
> `chat.html` 이 **한 번도 부르지 않았다.**
>
> - 미매칭이면 **「지금 할 수 있는 일 N가지」**를 표로. 한 번만 받고 · 못 받으면 그 줄만 없고 ·
>   **매칭됐을 때는 안 보여 준다.**
> - **미매칭 자체를 줄이려 하지 않았다** — 막다른 골목만 없앴다. 라우팅 튜닝은 Decision (a) 위반.
>   **고르라고 권하지도 않는다** — 고르는 것은 여전히 라우터다. **새 주장 0.**
> - 실측: 「오늘 날씨 어때? 노래 한 곡 불러줘」 → `ok=False · code=None · conf=0.8`.
> - **Wave M 의 흐름 프로브가 어제 생겨서 오늘 값을 했다** — 28 → **35종**으로 이번 변경을
>   실행해서 확인했다. 변이 2종(목록 3 · 캐시 1).

> **Wave S — 머지됨 (2026-09-01).** [#138](https://github.com/gncorpseo-commits/capnet/pull/138)
> · main **`a09de5f`**. Wave Q 가 화면에 넣은 것을 **읽는 사람이 알 수 있게** 적었다 —
> `capreq/README.md` 「못 알아들었을 때」 · `user-guide-ko.md` §7 두 문답. **로직 0.**
>
> - **「고르게 권하지 않는다」를 문서에도 박았다** — 목록을 보여 줄 뿐이고 고르는 것은
>   여전히 라우터다. 사용자 안내에는 이유까지 적었다: **「내가 시킨 것이 아니라 접수처가
>   정했다」는 장부가 유지되려면** 그래야 한다.
> - **낡은 숫자 셋을 다시 안 낡게 고쳤다** — `capabilities=7` 을 `10` 이 아니라 **`N`** 으로.
>   `measured-claims.md` §2 그대로 — **능력이 늘 때마다 고쳐야 하는 숫자는 애초에 적지 않는다.**
> - **`CHANGELOG` 선두를 건드리는 PR 이 하나뿐**이라 **충돌 0** 으로 머지됐다 — 야간의 셋과 대비.

> **Wave R — 머지됨 (2026-09-01).** [#136](https://github.com/gncorpseo-commits/capnet/pull/136)
> · main **`f1dd4c8`**. **`main` 에 실제로 들어간 결함을 고친 것이다.**
>
> 야간에 PR 다섯을 동시에 열어 `CHANGELOG` 충돌 셋이 났고, 「둘 다 남긴다」로 푸는 과정에서
> **파일 중간에 두 번째 `# Changelog` 헤더**가 생기고 **Wave M·N·O 가 159줄 되풀이**됐다
> (3,662 → 3,821줄). **`run_tests` 도 `check_submission` 도 아무것도 걸리지 않았다** —
> 아무도 그 파일의 **모양**을 안 봤기 때문이다. `git pull` 의 diffstat(`7601 +/-`)이 이상해서
> 알아챘다.
>
> - 뒤쪽 159줄을 잘라냈다. 지우기 전에 **위쪽 사본이 온전한지 세 항목 모두 줄 단위로 대조**했다.
> - `tests/test_changelog_integrity.py` — **모양만** 본다(헤더 1개 · 제목 중복 없음 · 맨 위가 헤더).
>   변이: 파일을 두 배로 만들면 **2종 실패**. `run_tests` 388 → **392**.
> - **「최신이 위」는 검사하지 않는다** — 다친 것은 순서가 아니라 중복이다.
>
> **원인은 내 PR 방식이다.** 충돌을 잘 설명하는 것보다 **충돌을 만들지 않는 것**이 낫다.
> 그리고 **「합쳐 봤다」는 「머지된 것을 봤다」가 아니다** — 로컬 시뮬레이션은 **내 해결안**이
> OK 였다는 증거일 뿐이다. 이번 세션부터 **`CHANGELOG` 선두를 건드리는 PR 은 한 번에 하나.**

> **야간 세션 총괄 (2026-09-01 01:24 → 02:30).** 열린 PR **5** (#129~#133).
> **머지 순서 #129 → #130 → #131 → #132 → #133** · 뒤 셋에서 각각 `CHANGELOG` 충돌 1건
> (**둘 다 남기고 최신을 위에**). 합친 상태 실측: **`run_tests` 388 · capreq 66 ·
> `check_input_purge` 17/17 · `clean_room` 9/9 · `prod_room` 27/27 · `check_release` OK.**
>
> **넷 다 「이미 있는데 아무도 안 보던 자리」였다** — `chat.html` 렌더링(#107 부터 네 번) ·
> #112 의 클라이언트 짝 · 라우팅 벤치의 능력 목록 · D22 의 선행 조건.
>
> **제품 기능은 늘지 않았다.** 11번째 능력(`retrieve.dense`)을 검토했다가 **접었다** —
> `text.embed` 는 **문자 n-gram 해시 사영**이라 코사인이 **철자 유사도**이지 의미가 아니다.
> 「dense retrieval」이라는 이름으로 내면 오해를 부르고 실질은 `text.rank` 와 같은 축이다.

> **이번 세션에 손으로 센 목록 셋을 파생으로 바꿨다 (2026-08-31).**
>
> | 어디 | 무엇을 세고 있었나 | Wave |
> |---|---|---|
> | `test_capability_patch_wiring` | 데모 이름 셋 | K |
> | `test_chat_html_unit` | 「자른 사실 고지」 3개 | L |
> | `test_text_rank` | 「셋 다 바이트가 같다」 | L |
>
> 셋 다 **다음 항목이 붙을 때 틀어지는** 자리였고 **실제로 이번에 틀어져서 알았다.**
> 「정본이 둘이면 갈라진다」의 **검사판**이다 — 개수를 손으로 세게 하면 언젠가
> **고치는 대신 검사를 지우게** 된다.
>
> **베이스라인 (Docker·Ollama 있는 세션):** `run_tests` **291** OK (skip 7) ·
> capreq **38** OK · `check_submission` **26/26** · `clean_room` **9/9** · `prod_room` **27/27** ·
> `product_demo.sh` **exit 0**. 불변식 전부 일치한다.

> **Wave F — 머지됨 (2026-08-30).** PR [#114](https://github.com/gncorpseo-commits/capnet/pull/114)
> · main **`2e43680`**.
> `user-guide-ko.md` §5.1 이 D22 이전 문구였다 — 「미리 허용된 사진만」. D8′·D22 로 Core 중개
> 수집이 들어왔고 capreq 가 그 경로를 쓰는데(#112 실측), **제품이 하는 일을 못 한다고 적은
> 문장**이었다. 입력을 **두 갈래**로 적었다 — ① 파일 첨부 → 접수처가 지문·크기·형식·올린
> 사람을 장부에 적는다 ② 데모 번호는 **사진 과목에만**. 「안 되는 것」은 D8′ 그대로
> **「접수처를 건너뛰고 넣기」**다. 받는 형식·크기는 **과목이 정한다**(master: 사실 기술로 승인).
> **코드 0 · DDL 0.**

> **capreq 첨부 버그 — 머지됨 (2026-08-30).** PR [#112](https://github.com/gncorpseo-commits/capnet/pull/112)
> · main **`a7eed90`**.
> Ollama 가 깔려 **#107 이후 처음으로 브라우저와 같은 경로를 끝까지 돌렸고**, 그 자리에서 버그 둘이 나왔다.
>
> - **첨부가 한 번도 동작한 적이 없다 (제품 1호부터).** `fastapi.UploadFile` 은 starlette 것의
>   *하위* 클래스라 `request.form()` 결과에 `isinstance` 가 **항상 False** 였다. 파일이 조용히
>   버려지고 요청은 allowlist 데모 경로로 떨어졌다 → `starlette.datastructures.UploadFile` 로 검사.
> - 그렇게 만들어진 텍스트 작업은 **영원히 QUEUED** 였다 (Node 는 이미지 밖 폴백이 없다 · D8′ ·
>   attempt 5회 소진 후 FAILED 실측). 이제 **만들기 전에** 거절한다. 이미지 caseId 경로는 그대로.
> - **서버 경로에 검사가 0 이라 아무도 몰랐다.** `test_server_unit.py` 6종 신설 —
>   **고침을 되돌리면 4종이 실패한다**(확인). CI `capreq` 잡에 fastapi·python-multipart 추가.
>   capreq 검사 32 → **38**.
> - 라우팅 설명 보정 — 실제 `qwen2.5:3b` 로 프롬프트 5개 측정 **4/5 → 5/5** (n=5 · 품질 주장 아님).
> - **종단 실측:** `/api/chat` 첨부+실행 → `text.ner@1` conf=1.00 → 1s 만에 COMPLETED ·
>   entities 3건 · 증적 node=…030 · team→team · M ≤ M.
> - **아직 못 본 것:** `chat.html` 의 브라우저 JS 렌더링 — 헤드리스 브라우저가 없다.

> **제품 데모 한 파일 — 머지됨 (2026-08-29).** PR [#111](https://github.com/gncorpseo-commits/capnet/pull/111)
> · main **`6d57a69`**.
> `scripts/product_demo.sh` — health → 카탈로그 → **능력만 요청**(기기 주소 없음) →
> 결과·배정 증적 → `GET /v1/ops/work-units` 까지 한 파일. **제품 코드 0 · DDL 0.**
>
> - Core **공개 API 만** 부른다 (DB 직접 조회 없음) · `set -euo pipefail` · **exit 0 실측**.
> - 능력이 없으면 `ner_demo.sh` 로 등록·게이트까지 한 번에 — 「먼저 저걸 돌리세요」로 끝나지 않게.
> - **품질 주장 없음** — `text.ner` 은 `quality_profile='none'`. 경로와 증적만 보인다.
> - `tests/test_product_demo.py` **10종** 신설 · `run_tests` 281 → **291**.
> - 문서: README 빠른 시작 ★ + 스크립트 표 · `user-guide-ko.md` §1.5 「제품 체험」.

> **카탈로그 +1 — 머지됨 (2026-08-29).** PR [#110](https://github.com/gncorpseo-commits/capnet/pull/110)
> · main **`30a94fb`**.
> **`text.extract`** = 8번째 실행기. 평문 `키: 값` 필드만 뽑는다 — **자연어 이해 주장 없음.**
>
> - 텍스트 능력 셋이 **무엇을 찾는지** 갈린다: `text.ner`=타입 span(키 없음) ·
>   `text.extract`=`키: 값` 필드 · `table.extract`=격자.
> - **새 학습 0 · 외부 말뭉치 0.** `RuleTextExtract` 파라미터 0 · 버퍼 한 칸.
>   `rule_extract.safetensors` 는 **`rule_ner` 과 바이트가 같다**(sha `15458b00…`) — 숨기지 않고
>   meta·카탈로그·체크리스트에 적었다. 구별하는 것은 `arch` 다.
> - **종단 PASSED** — `scripts/text_extract_demo.sh` · 계약 게이트 6검사 OK ·
>   Task COMPLETED · fields 3건 · assignment SUCCEEDED · team→team · M ≤ M.
>   이름표 없는 줄은 필드로 읽지 않는다(데모가 검사).
> - `tests/test_text_extract.py` **21종** 신설 · `run_tests` 260 → **281** ·
>   가중치 필수 6종 → **7종**.
> - 브리지 ack 반영 · **#107 Confirm 뒤늦게 채움** · STATE 「PR 대기」 정정.

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
> - **서버 경로 실측 (2026-08-29).** 살아 있는 Core 에 붙여 처음 돌렸다 —
>   `/api/health` · `/api/capabilities` · `/api/tasks/{id}`(실제 완주 task → **entities 3건 요약 +
>   배정 증적**) · 없는 id 는 500 이 아니라 `ok=false` 로 내려온다. **버그 없음.**
> - **브라우저 종단 스모크는 여전히 미실행** — **Ollama 가 없어** `/api/chat` 라우팅과
>   `chat.html` 렌더링을 못 본다. 절차는 `capreq/README.md` §「눈으로 확인하기」.
>   **Ollama 있는 환경에서 한 번 돌리면 이 문장을 지운다.**

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
