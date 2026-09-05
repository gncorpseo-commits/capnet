# Changelog

## 「CI 가 본다」는 목록이 **실제보다 짧았다** (큐 #59) — 2026-09-05

`#215` 가 잡은 것은 「**CI 가 본다**」가 **거짓**이던 자리였다. 이번에는 그 문장이 적힌
**목록 자체**를 `ci.yml` 과 대조했다.

| job | `ci.yml` 의 단계 | `testing.md` §4 가 적던 것 |
|---|---|---|
| `unit` | **4** | **3** — `check_release.sh`(G9) 가 빠졌다 |
| `capreq` | 2 | 2 |
| `migrate` | **9** (의존성 설치·통합 검사 포함) | **6 + 통합** — SD-015 가 빠졌다 |

빠진 둘은 **실제로 도는데 문서에 없다.** 「CI 가 본다」고 적힌 목록이 실제보다 짧으면
안 적힌 단계는 **없는 것처럼 읽히고**, 지우거나 옮겨도 아무도 못 본다 —
`#217`(시크릿 검사가 CI 워크플로를 안 보고 있었다)과 같은 모양이다.

### 검사가 **내가 쓴 주석에 속았다** (적어 둔다)

빠졌던 단계를 문서에 적으면서 그 옆에 「예전에는 `SD-015` 가 빠져 있었다」고 **설명을
달았다.** 그랬더니 목록에서 그 단계를 지우는 뮤테이션이 **통과했다** — 낱말이 설명 문장에
남아 있었기 때문이다. **검사가 자기 글을 근거로 삼은 것이다.**

설명에서 단계 이름을 빼고, 왜 빼는지를 문서에 적었다. `#220` 이 「말하는 문장은 위반이
아니다」로 걸러낸 것의 **거울상**이다 — 이번에는 말하는 문장이 **위반을 덮고** 있었다.

### `ci.yml` 은 고치지 않았다

잡·설치·단계 추가는 열린 Decision (`round9-ci-coverage-proposal`). 고친 것은 **문서**뿐이고
검사는 양쪽을 **대조**만 한다.

### 뮤테이션 3

| 심은 것 | 운 검사 |
|---|---|
| 문서에서 마지막 migrate 단계 삭제 | `test_every_step_is_mentioned` · 번호 목록 수 |
| 문서에서 `check_release.sh` 삭제 | `test_every_step_is_mentioned` |
| `ci.yml` 에 단계 추가 (문서는 그대로) | 대응표 누락 + `test_migrate_step_count_matches` |

재현: `python3 -m unittest tests.test_ci_claims_match_the_workflow` (7 검사 · 827 통과)

## 같은 주장을 **세 경로**로 말한다 — 셋의 모양을 못박는다 (큐 #54) — 2026-09-05

`#200` 은 README 가 「**기기 주소가 없다**」고 부른 **파일이 틀렸던 것**을 고쳤다. 그 옆자리다 —
**세 데모가 각자 무엇을 보이기로 했고, 그게 지금도 참인가.**

| 스크립트 | 문서가 말하는 것 | 경로 |
|---|---|---|
| `demo.sh` | 실게이트 → Task 완주 · 증적 두 줄 | Core 직접 (+ 준비 단계 Node `/health`) |
| `product_demo.sh` | 「**어디에도 기기 주소가 없다**」 | Core 공개 API 만 |
| `capreq_demo.sh` | 사람이 쓰는 **입구**로 같은 것 | capreq → Core |

**같은 주장을 세 번 말하는데 경로가 다르다.** 하나가 조용히 어긋나도 나머지 둘이
초록이면 아무도 모른다.

### 실측 — 셋 다 참이다

| 무엇 | 값 |
|---|---|
| `product_demo.sh` 안의 Node 주소 | **0** ✅ |
| `demo.sh` 의 Node 주소 사용 | **2줄** — 기본값(L8) · `/health`(L13) |
| 그 둘이 `POST /v1/tasks`(L70) **앞인가** | **그렇다** ✅ |
| `capreq_demo.sh` 의 Core 직접 `POST /v1/tasks` | **0** ✅ |

**오늘 결함은 없다.** 나기 전에 막는다.

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| `product_demo` 에 `NODE_URL` 한 줄 | `test_no_node_address_anywhere` |
| `demo.sh` 가 작업 **뒤에** Node 를 부름 | `test_node_use_is_all_before_the_first_task` |
| `demo.sh` 가 `/health` 아닌 Node 경로를 부름 | `test_node_is_only_health` |
| README 에서 그 주장을 삭제 | `test_the_readme_still_makes_that_claim` |

마지막 하나가 이 검사의 핵심이다 — **주장이 사라지면 검사는 아무 말도 안 지키게 된다.**

재현: `python3 -m unittest tests.test_three_demos_same_claim` (9 검사 · 820 통과)

## bash 에서 문서대로 돌리면 A/B 비교가 **자기 산출물을 못 찾았다** (큐 #53) — 2026-09-05

README 는 「**Windows** — 동명 `.ps1`」이라고 적는다. **동명인데 동작이 달랐다** —
`#206` 이 주소에서 그걸 잡았고, 이번에는 **입력 이름과 기본값**을 다시 훑었다.

| 무엇 | 수 |
|---|---|
| `.ps1` | **11** |
| 동명 `.sh` 가 있는 것 | **10** (`smoke_w1` 만 단독) |
| 입력이 맞는 쌍 | **9** |
| **어긋난 쌍** | **1** — `score_n300` |

### ① `score_n300.ps1` 에는 `GOLDEN` 이 없었다

`.sh` 는 `GOLDEN=…` 으로 **홀드아웃**을 잰다 (주석에 용례가 있다). `.ps1` 은
`data\golden-n300` 이 박혀 있어 **Windows 에서는 홀드아웃을 못 쟀다.** `STATE` 는 홀드아웃
숫자를 적는데, 재현 수단이 한쪽에만 있었다.

### ② 산출물 이름이 갈렸고, `compare_ab` 는 옛 이름을 들고 있었다

```text
score_n300.sh  → artifacts/score-n300-eurosat_scratch-golden-n300.json
score_n300.ps1 → artifacts/score-n300-eurosat_scratch.json
compare_ab.*   기본값: artifacts/score-n300-eurosat_scratch.json     ← .sh 산출물과 불일치
```

**bash 에서 문서대로 돌리면** `score_n300.sh` 다음 `compare_ab.sh` 가
`missing … — run score_n300.sh first` 로 끝났다. **방금 돌린 스크립트를 다시 돌리라고**
말하는 것이다. 셋을 한 이름으로 맞췄다 (홀드아웃 결과가 기본 결과를 덮어쓰지 않게
이름에 골든셋을 남긴다).

### 파서가 주석 속 괄호에 걸렸다 (적어 둔다)

`param(` 블록을 「첫 `)` 까지」로 자르니 내가 방금 넣은 주석 `(큐 #53)` 에서 끊겨
**그 뒤 파라미터를 통째로 못 봤다.** 닫는 `)` 만 있는 줄에서 끝내도록 고쳤다 —
`#220` 이 펜스 짝을 세다 뒤집힌 것과 같은 모양이다.

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| `.ps1` 에서 `-Golden` 제거 | `test_every_mapped_param_exists_on_both_sides` |
| `compare_ab.sh` 를 옛 이름으로 | 기본값 대조 2건 |
| `score_n300.sh` 의 `GOLDEN` 기본값 변경 | 사슬 검사 2건 (양쪽) |
| 짝 없는 새 `.ps1` | `test_the_ps1_only_script_is_known` |

**못 쟀다** — `pwsh` 가 없어 `.ps1` 을 돌리지 못했다 (`#206` 과 같은 조건). 고친 줄은
같은 파일이 이미 쓰는 문법이고, 문자열 정합은 검사가 **양쪽 소스에서 뽑아** 대조한다.

재현: `python3 -m unittest tests.test_ps1_parity` (9 검사 · 811 통과)

## SBOM 이 의존성 없이 **조용히** 만들어질 수 있었다 (큐 #55) — 2026-09-05

`#205` 가 남긴 교훈은 「**응답 없음(`000`)을 통과로 세지 마라**」였다. 같은 질문을 셸 쪽
전체에 물었다 — `|| true` · `|| :` 는 **직전 명령의 실패를 지운다.**

### 실측

| 무엇 | 수 |
|---|---|
| `scripts/**/*.sh` 의 `\|\| true` · `\|\| :` | **18** |
| 그중 **실제 결함** | **1** — `generate_sbom.sh` |
| 근거가 서는 자리 | **17** |
| `%{http_code}` 를 받는 자리 | **10** |
| 그중 `000` 이 새는 곳 | **0** — 전부 **허용 목록 비교**(`== "200" \|\| == "409"`) |

### 결함

```bash
grep -v '^\s*#' "$root/apps/core/requirements.txt" || true   # ← 파일이 없어도 넘어간다
```

`grep` 은 파일이 없으면 **2** 로 죽는다. `|| true` 가 그걸 지웠다:

```text
$ bash -c 'set -euo pipefail; { grep -v "^#" /nonexistent/requirements.txt || true; }; echo rc=$?'
grep: /nonexistent/requirements.txt: No such file or directory
rc=0                            ← SBOM 은 core 의존성 없이 만들어지고 exit 0
```

`capreq` 쪽은 `[ -n "$capreq_reqs" ] || exit 1` 로 막혀 있었는데 **`requirements.txt` 둘만
안 막혀 있었다.** 대회 2차 라이선스 검증에 내는 산출물이라 **빠진 채 초록**인 것이 가장 나쁘다.

고친 방법 둘:

1. 파일 존재를 **`pip install` 전에** 본다 — 없는 파일 하나 때문에 몇십 초를 기다리지 않는다
2. `|| true` → `|| [ "$?" -eq 1 ]` — grep 의 **1**(고른 줄 없음)만 봐주고 **2**(읽기 실패)는 죽는다

### 나머지 열일곱은 근거가 선다

`shift`(인자 없음) · 뒷정리(`down -v`·`kill`·`tail`) · `grep -c .`(0건) · 데모의 id 추출
(바로 뒤 `ccurl -sf` 가 다시 확인한다). `ALLOWED_SWALLOW` 가 **파일별 개수**로 못박는다.

### 실제로 돌려 봤다

정적 검사만으로는 가드가 도는지 모른다. 임시 트리에 스크립트를 복사하고 `requirements.txt`
하나를 빼고 **실행**해 종료 코드와 메시지를 확인한다 — Docker 없이 돈다.

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| 존재 가드 삭제 | 실행 검사 **2건** (없는 파일인데 통과) |
| `\|\| [ "$?" -eq 1 ]` 를 `\|\| true` 로 | 표 검사 2건 + `test_grep_only_forgives_no_match` |
| 새 스크립트가 `\|\| true` 로 삼킴 | `test_every_swallow_is_accounted_for` |
| `text_demo` 의 http_code 비교 삭제 | `test_every_http_code_check_is_an_allowlist` |

재현: `python3 -m unittest tests.test_scripts_do_not_swallow_failures` (10 검사 · 802 통과)

## 같은 방을 **27/27** 과 **51/51** 로 부르고 있었다 (큐 #48) — 2026-09-05

`clean_room` · `prod_room` 의 통과 수는 문서 여러 곳에 **손으로** 적혀 있다. 스크립트가
자라면 그 숫자가 낡는데 **아무도 세고 있지 않았다.**

| 어디 | 뭐라고 |
|---|---|
| `docs/ops/shoot-day-runbook.md` | `prod_room` **통과 51** |
| `docs/bridge/queue-batches.md` | `prod_room 51/51` |
| **`docs/ops/contest-submission-checklist.md`** | `prod_room` **27/27** ← 낡았다 |

`#205` 가 프로브 라우트를 **5 → 24** 로 늘리면서 27 이 51 이 됐다. 런북은 따라갔고
**제출 정본 체크리스트는 안 따라갔다** — 심사자가 읽는 쪽이 낡은 것이다.

### 실행 없이 센다

`scripts/room_check_count.py` 가 소스에서 센다. 최상위 `chk`/`step` 은 한 건,
`for path in … ; do … chk … done` 은 **경로 수 × 루프 안 chk 수**.

```bash
python3 scripts/room_check_count.py
# clean_room   9건
# prod_room    51건
```

### 계수기가 파이썬 `for` 에 속아 두 건을 잃을 뻔했다 (적어 둔다)

`prod_room.sh` 안에는 `python3 -c '…'` 로 넘기는 코드가 있고 그 안의
`for n in d["nodes"]:` 도 **열 0 에서 시작한다.** 셸 루프로 잡으면 그 뒤 최상위 `chk`
**두 건이 통째로 사라져 49** 가 나온다 — 실제로 그렇게 나왔다. 셸 `for` 는 줄이 `\` 나
`; do` 로 끝난다. **세는 도구도 틀릴 수 있어서**, 그 함정을 검사에 그대로 심어 뒀다.

### 인용은 위반이 아니다

런북은 「옛 27/27 은 낡았다」고 **적는다.** 그건 주장이 아니라 설명이라, `「…」` 안을
걷어내고 본다 — `#220` 이 백틱을 걷어낸 것과 같은 규율이다.

### 날짜를 지우지 않았다

체크리스트 항목은 `2026-08-16` 재현 기록이다. **숫자만 51 로 바꾸면 그 날의 기록이
거짓이 된다.** 8/16 의 27 은 그때 값으로 두고, `prod_room` 은 **2026-09-04 재측정
51/51** 로 따로 적었다. 재현 명령 둘을 같이 붙였다.

### 뮤테이션 3

| 심은 것 | 운 검사 |
|---|---|
| 체크리스트를 다시 `27/27` 로 | `test_no_stale_room_number` |
| `clean_room` 에 `step` 하나 추가 | 같은 검사 + `test_counts_match_todays_measurement` |
| 계수기를 파이썬 `for` 에 속게 | `test_the_counter_is_not_fooled` (4 ≠ 2) |

재현: `python3 scripts/room_check_count.py` · `python3 -m unittest tests.test_room_numbers_match_scripts`
(7 검사 · 792 통과)

## 주석이 금지한 것을 코드가 하고 있었다 — API 키가 `ps` 에 떴다 (큐 #47) — 2026-09-05

`scripts/lib/*.sh` 의 판정 함수 셋 중 **하나만 검사 밖**이었다. 그리고 그 하나에서
결함이 나왔다.

| 함수 | 파일 | 단위 검사 (전) |
|---|---|---|
| `tally_verdict` | `lib/tally.sh` | ✅ `test_room_tally.py` |
| `probe_verdict` | `lib/authprobe.sh` | ✅ `test_prod_room_auth_probe.py` |
| **`ccurl`** | `lib/http.sh` | **없었다** |

### 결함

`lib/http.sh` 의 「시크릿 위생」은 이렇게 적혀 있다:

> 키는 환경변수로만 받는다. **인자로 받으면 프로세스 목록(ps)에 남는다.**

그래 놓고 헤더를 **curl 의 인자로** 넘기고 있었다. `-H` 의 값도 argv 다. 실측:

```text
$ pgrep -a curl
9951 curl -H Authorization: CapNet-Key ck_deadbeef.SECRETVALUE123 -s --max-time 4 http://…
```

`ps` 는 기본 리눅스에서 **다른 사용자에게도 보인다** (`hidepid` 미설정). 데모·촬영은
공용 워크스테이션에서 돈다 — 「환경변수로만 받는다」의 목적이 여기서 무너져 있었다.

### 고친 방법 — `-H @파일`

curl **7.55+** 는 헤더를 파일에서 읽는다. 파일은 `0600`, 호출이 끝나면 지운다.

```text
$ pgrep -a curl
9980 curl -H @/tmp/capnet-hdr-JdOf7v -s --max-time 4 http://…     ← 키가 안 보인다
```

`|| rc=$?` 로 받는 데 이유가 있다. 호출자는 전부 `set -e` 다 — 그냥 두면 curl 실패 시
**지우기 전에** 셸이 죽어 **시크릿 파일이 `/tmp` 에 남는다.** 고치면서 만들 뻔한 두 번째
결함이라 검사로 못박았다.

### 어떻게 쟀나 — 가짜 `curl`

Docker 도 살아 있는 Core 도 필요 없다. `PATH` 앞에 **argv 를 받아 적는 `curl`** 을 놓고
`ccurl` 을 부른다. 넘기는 것이 그대로 보인다 — `lib/tally.sh` 를 `source` 해서 부르는
`test_room_tally` 와 같은 방식이다.

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| 헤더를 다시 인자로 (원래 코드) | 5건 — argv 노출·파일 권한·삭제 |
| `\|\| rc=$?` 제거 | `…removed_after_failure` — **`set -e` 로 파일이 남는다** |
| 헤더 파일 `0600` → `0644` | `…is_not_world_readable` |
| 검사 없는 새 lib 함수 추가 | `test_no_lib_function_is_unclaimed` |

### 남은 자리 — 다음 줄

`prod_room.sh` 는 `ccurl` 을 안 쓰고 **직접** `-H "Authorization: CapNet-Key $key"` 를
**아홉 번** 넘긴다. 같은 노출이다. 다만 거기는 일회용 게이트 스택의 부트스트랩 키이고,
그 스크립트는 Docker 없이 **돌려 볼 수 없다** — 다음 줄로 남긴다.

재현: `python3 -m unittest tests.test_lib_http_never_leaks_the_key` (10 검사 · 785 통과)

## 「인증이 조회보다 먼저」를 **규칙 두 줄**로 굳혔다 — 오늘 위반 0 (큐 #64) — 2026-09-05

`#223` 은 `prod_room` 이 두 라우트에서 **401 이 아니라 422** 를 받던 것을 잡았다.
구멍이 아니라 **검사가 인증에 닿지 못한** 것이었다. 그 사건을 일반화한다.

### 규칙 1 — 인증 헬퍼가 `get_conn()` 보다 먼저 온다

조회가 먼저면 무인증 요청이 **404** 로 끝난다. 401 과 404 는 다른 말이다:

- **401** 「너는 누구인지 모르겠다」 — 그 id 가 있는지 **말하지 않는다**
- **404** 「그런 건 없다」 — 이미 DB 를 봤다는 뜻이고, **존재 여부가 샌다**

`GET /v1/tasks/{task_id}` 는 소유자가 아니면 404 를 준다 — **403 은 「그 id 는 존재한다」를
흘리기 때문**이다(핸들러 주석). 그 설계가 성립하려면 **인증이 먼저**여야 한다.

### 규칙 2 — 경로 파라미터는 파싱되는 타입이다

`prod_room` §14 는 존재하지 않는 더미 id 로 누른다. 그 더미가 파싱 안 되면 **422** 고,
그 절은 다시 인증을 재지 못한다.

### 실측

| 무엇 | 수 |
|---|---|
| 인증 헬퍼를 부르는 라우트 | **40** |
| 그중 **조회가 인증보다 먼저** | **0** ✅ |
| 경로 파라미터를 받는 인증 라우트 | **19** |
| 타입이 `uuid.UUID` 인 것 | **19** — 전부 ✅ |
| 이 순서를 세던 검사 | **0** |

**오늘은 0 이다. 나기 전에 막는다.**

### 뮤테이션 3

| 심은 것 | 운 검사 |
|---|---|
| `nodes_get` 에서 `_require` 를 `get_conn` 뒤로 | `test_no_route_looks_up_before_authenticating` |
| `node_id: uuid.UUID` → `str` | `test_every_path_param_is_a_uuid` |
| `prod_room` 의 `dummy` 를 UUID 아닌 값으로 | `test_prod_room_dummy_is_a_real_uuid` |

재현: `python3 -m unittest tests.test_auth_comes_before_lookup` (6 검사 · 775 통과)

## 쓰기 라우트 **스물둘 중 셋**만 무인증으로 눌러 보고 있었다 (큐 #49) — 2026-09-05

`#223` 은 조회면에서 같은 것을 잡았다 — 인증 `GET` **열여덟 중 넷**. 고치고 나서
**쓰기 쪽은 그대로 남았다.** 조회면이 열리면 정보가 새고, **쓰기가 열리면 남이 내
플릿에 Node·Agent·작업을 만든다.**

### 실측

| 무엇 | 수 |
|---|---|
| 라우트 전체 | **46** |
| 쓰기 (`POST`/`PUT`/`PATCH`/`DELETE`) | **22** |
| 그중 인증을 부르는 것 | **22** — 공개 쓰기 **0** ✅ |
| `prod_room` 이 **무인증으로** 재는 것 | **3** |

```text
POST /v1/nodes          (키 없음)   → 401   §5
POST /v1/agents         (키 없음)   → 401   §5
POST /v1/nodes/redeem   (토큰 없음) → 401   §8-2
```

나머지 **열아홉**은 강제 모드에서 한 번도 안 눌러 봤다. `ast` 검사는 「인증 헬퍼를
불렀는가」만 보므로 헬퍼를 부르고도 401 이 안 나오는 경우를 못 잡는다 — `#223` 이
실제로 그 자리에서 **두 건**을 찾았다.

### 프로브를 안 늘렸다 — 몸통이 필요하고, 재 볼 수 없다

FastAPI 는 핸들러 본문보다 **먼저** 요청 본문을 검증한다. 몸통 없이 `POST` 하면
인증에 닿기 전에 **422** 고, 그 절은 **인증을 재지 못한다** — `#223` 이 `node_id` 로 겪은
것과 같은 함정이다. 지금 도는 셋이 401 을 받는 것은 **유효한 몸통을 같이 보내기**
때문이다.

열아홉을 늘리려면 라우트마다 유효한 최소 몸통이 필요하고, 그게 맞는지는 **돌려 봐야**
안다. 이 세션에는 Docker 데몬이 없다. 몸통을 잘못 지으면 게이트가 **422 를 인증 실패로
세며 빨개진다.** 재 보지 않은 프로브를 게이트에 얹지 않는다.

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| `POST /v1/agents` 무인증 프로브 삭제 | `test_the_three_unauthenticated_probes_are_still_there` |
| 인증 없는 쓰기 라우트 `POST /v1/ops/wipe` 추가 | `test_no_write_route_is_public` |
| 인증 있는 쓰기 라우트 추가 (재는 건 그대로) | `test_the_gap_is_stated_honestly` (19 → 20) |
| 키 붙은 호출을 무인증으로 세도록 탐지기 훼손 | `test_the_probe_reader_discriminates` |

재현: `python3 -m unittest tests.test_prod_room_write_probes` (6 검사 · 769 통과)

## `!override` 는 **덮는다** — 그런데 문서가 요구 버전을 낮게 적었다 (큐 #45) — 2026-09-05

제품 오버레이의 3번 주장은 「**postgres 를 호스트에 노출하지 않는다**」다. 그 주장 전체가
**한 태그**에 걸려 있다:

```yaml
  postgres:
    ports: !override []      # ← 없으면 병합이 「덧붙이기」라 5432 가 남는다
```

### 실측 — 데몬 없이 `config` 로 쟀다 (Compose v5.3.1)

```bash
export POSTGRES_USER=u POSTGRES_PASSWORD=p POSTGRES_DB=d \
       DATABASE_URL=postgresql://u:p@postgres:5432/d
docker compose -f compose.yaml config                     | grep -c published:   # 5
docker compose -f compose.yaml -f compose.prod.yaml config | grep -c published:   # 1
```

| 무엇 | 결과 |
|---|---|
| `compose.yaml` 단독 공개 포트 | **5** |
| `+ compose.prod.yaml` | **1** — `core:8000` 만 |
| postgres `5432` | **사라진다** ✅ |
| `!override` 를 지우고 다시 재면 | **2** · `published: "5432"` **부활** |

**태그는 하중을 받고 있다.** 주장은 참이다.

### 그런데 README 는 「Compose v2」라고만 적었다

`!override` 는 **v2.24.0 (2024-01)** 에서 들어왔다. v2.0–v2.23 은 그 태그를 모른다.
심사자가 그 버전으로 제품 오버레이를 띄우면 **postgres 가 열린 채**이거나 파싱이 깨진다.
「v2」와 「v2.24+」는 다른 말이다 — README·운영 안내를 고쳤다.

### 뮤테이션 3

| 심은 것 | 결과 |
|---|---|
| `!override` 제거 (정적) | `test_postgres_is_closed` 외 3건 |
| `!override` 제거 (**실제 병합**) | `published` 1 → **2** · `5432` 부활 |
| README 를 「Compose v2」로 되돌림 | `test_readme_states_the_minimum` |
| 해명 없는 새 공개 포트(`adminer`) 추가 | `test_every_open_port_is_closed_or_explained` |

재현: 위 `docker compose … config` 두 줄 · `python3 -m unittest tests.test_compose_override_closes_ports`
(8 검사 · 763 통과)

## 통합 검사 **열다섯**은 CI 의 **한 줄**로만 돈다 — 그 줄을 못박은 검사는 0 (큐 #42) — 2026-09-05

`#215` 가 잡은 것은 「**CI 가 본다**」가 거짓이던 자리였다. 같은 질문을
`tests/integration/` 에 물었다.

| 무엇 | 답 |
|---|---|
| `tests/integration/check_*.py` | **15** |
| `scripts/run_tests.sh` 가 부르는가 | **아니다** — DB 가 필요하다 |
| 그럼 누가 부르는가 | `ci.yml` 의 `migrate` 잡 **한 줄** |
| 그 한 줄을 못박은 검사 | **0** |

```yaml
      - name: 통합 검사 (검사마다 깨끗한 DB)
        run: scripts/run_integration.sh      # ← 유일한 실행 경로
```

### 왜 기존 둘 사이로 빠졌나

- `test_integration_runner` 는 **러너의 glob** 만 본다 — 파일 이름이 패턴에 맞는가
- `test_ci_matches_run_tests` 는 **`run_tests.sh` 가 부르는 도구**만 본다

`run_integration.sh` 는 `run_tests.sh` 밖이라 **둘 다 안 본다.** 그 줄을 지우거나
`if:` 를 붙이면 검사 열다섯이 **조용히 멈추고 CI 는 초록**이다.

「검사를 짜 놓고 돌지 않는 것은 검사가 없는 것보다 나쁘다 — 있다고 믿게 되기
때문이다」(`test_integration_runner` 머리말). 그 문장이 **러너 자신**에게도 해당했다.

### `ci.yml` 은 고치지 않았다

잡·설치 추가는 열린 Decision (`round9-ci-coverage-proposal`) 이다. **오늘 있는 것을
못박기만** 한다.

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| CI 단계의 `run:` 을 다른 명령으로 | `test_ci_has_a_step_that_runs_the_runner` |
| 그 단계에 `if: github.ref == …` 추가 | `test_that_step_is_not_conditional` |
| 러너의 「0건은 통과가 아니다」 제거 | `test_runner_fails_when_it_finds_nothing` |
| 러너의 glob 을 파일 하나로 고정 | `test_runner_still_globs` |

재현: `python3 -m unittest tests.test_integration_checks_are_run_by_ci` (7 검사 · 755 통과)

## 손으로 적은 **예외 목록 열둘**이 근거 없이 자랄 수 있었다 (큐 #43) — 2026-09-05

이 회차가 세운 검사들은 거의 전부 예외 목록을 하나씩 달고 있다:

```python
ARCHIVES = ("inbox-cursor.md", "inbox-claude.md")   # #226
WITHOUT_ERREXIT = {"prod_room.sh": "큐 #44"}         # #228
OUTSIDE_CLEAN_ROOM = {…열하나…}                      # #229
ALLOWED_READERS = {"_headers"}                       # #196
```

**목록에 한 줄 더 넣으면 검사가 조용히 약해진다.** 「지키는 척」의 마지막 통로다 —
`#230`(바닥 등록부)과 같은 자리이고, 이번에는 **예외 목록** 쪽이다.

### 실측

| 무엇 | 수 |
|---|---|
| `tests/` 의 허용 목록성 상수 | **14** |
| 그것이 든 파일 | **9** |
| 원소 합 | **40** |
| **진짜 예외 목록** | **12** |
| **어휘 집합**(예외가 아님) | **2** — `SKIP_PARTS` · `SKIP_CALLS` |
| 늘어나는 것을 막던 검사 | **0** |

### 어휘를 예외로 세면 「열넷」이 된다 — 그건 틀린 숫자다

`SKIP_PARTS = {"__pycache__", "node_modules"}` 와 `SKIP_CALLS = {"skip", "skipIf", …}` 는
**무엇을 봐줄지**가 아니라 **무엇을 부르는지**를 적은 어휘다. 이름에 `SKIP` 이 들어가
탐지기에 걸릴 뿐이다. `#218` 이 `$node_id` 문자열을 세어 「우회 일곱 건」이 될 뻔한 것과
같은 함정이라, 표가 **종류를 함께** 적는다.

### 표가 못박는 것

1. **새 허용 목록은 등록된다** — 표에 없으면 운다
2. **원소가 늘면 운다** — 줄이는 것은 자유다 (예외가 줄어드는 건 개선이다)
3. **예외는 근거를 코드 옆에 둔다** — 바로 위 주석이거나 값이 이유 문자열이다
4. 사라진 목록은 표에서 빠진다

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| `ARCHIVES` 에 한 줄 추가 | `test_no_allowlist_grew` |
| 표 밖에서 새 `ALLOWED_ROOMS` 생성 | `test_no_allowlist_is_unregistered` |
| `EXEMPT` 위 근거 주석 삭제 | `test_every_exemption_carries_its_reason_in_the_code` |
| 어휘를 예외로 옮김 | `test_exemption_count_is_twelve` · `…vocab_sets_are_marked` |

재현: `python3 -m unittest tests.test_hand_allowlists_are_justified` (9 검사 · 748 통과)

## 바닥을 내리면 **초록이었다** — 92건을 등록부로 못박는다 (큐 #50) — 2026-09-05

이 회차들이 반복해서 잡아 온 결함은 **「0건인데 통과」**다 — `#180`(누출 검사가
아무것도 안 보고 「깨끗하다」) · `#181`(통합 검사 0개도 초록) · `tally.sh`(`pass=0 ·
fail=0` 이 「전부 재현된다」). 고치는 방법은 늘 같았다: **바닥**을 둔다.

```python
self.assertGreaterEqual(len(_sites()), 3, _sites())   # 이번 회차 #220
REFERENCE_FLOOR = 355                                  # #221 · 큐 #41
```

**그런데 바닥 자체를 내리면 아무도 울지 않았다.** `355` → `0` 한 줄이면 전부 초록이고
그 검사들은 **지키는 척**만 하게 된다.

### 실측

| 무엇 | 수 |
|---|---|
| 바닥 단언 `assertGreater[Equal](…, N)` | **90** |
| 이름 붙은 바닥 상수 (`…FLOOR…`·`…MIN…`) | **2** — `REFERENCE_FLOOR` · `MIN_LIMIT` |
| 그것이 든 파일 | **48** |
| 바닥이 **내려가는 것**을 막던 검사 | **0** |

### 상수를 빠뜨렸다가 뮤테이션에 걸렸다 (적어 둔다)

첫 판은 **단언의 리터럴만** 봤다. 그래서 `REFERENCE_FLOOR = 355` 를 `0` 으로 바꾸는
뮤테이션이 **그대로 통과했다** — `self.REFERENCE_FLOOR` 는 단언 자리에 숫자로 보이지
않는다. **뮤테이션을 안 심었으면 절반짜리를 「됐다」고 적을 뻔했다.**

### 등록부

`scripts/floor_registry.py` 가 바닥을 전부 뽑아 `tests/floors.json` 에 적고,
`test_floors_do_not_sag.py` 가 **지금 값이 등록 값보다 낮지 않은가**만 본다.

- **올리는 것은 자유** — 실측이 늘면 `--write` 로 갱신한다
- **내리려면 등록부를 같이 고쳐야 한다** — 한 줄로 조용히 못 낮춘다
- **새 바닥은 등록된다** · **사라진 바닥은 빠진다** (유령을 「지킨다」고 세지 않는다)

키는 `파일::함수#순번` 이다 — 줄 번호로 잡으면 한 줄만 넣어도 전부 어긋난다.

### 뮤테이션 5

| 심은 것 | 운 검사 |
|---|---|
| `REFERENCE_FLOOR` 355 → 0 | `test_no_floor_was_lowered` |
| `MIN_LIMIT` 100 → 30 | 같음 |
| `assertGreaterEqual(len(_sites()), 3)` → `0` | 같음 |
| 등록 없는 새 바닥 | `test_every_floor_is_registered` |
| 검사를 지워 유령이 남음 | `test_registry_has_no_ghosts` |

재현: `python3 scripts/floor_registry.py --check` · `python3 -m unittest tests.test_floors_do_not_sag`
(9 검사 · 739 통과)

## 「깨끗한 환경에서 **전부** 재현된다」 — 능력 열 종 중 **하나**였다 (큐 #46) — 2026-09-05

`#223` 은 `prod_room.sh` 가 라우트 **스물넷 중 다섯**만 눌러 보면서 「제품 프로파일에서
전부 재현된다」를 찍던 것을 잡았다. **형제가 남아 있었다** — `clean_room.sh` 다.

### 실측

| 무엇 | 수 |
|---|---|
| `scripts/` 의 데모 스크립트 | **13** |
| `clean_room.sh` 가 부르는 것 | **2** — `demo.sh` · `demo_violations.sh` |
| `prod_room.sh` 가 부르는 것 | **1** — `demo.sh` |
| 카탈로그 「구현됨」 능력 | **10** |
| 빈 볼륨에서 **종단으로** 도는 능력 | **1** — `image.classify` |

마지막 줄은 이렇게 찍혔다:

```text
깨끗한 환경에서 전부 재현된다.
```

**「전부」가 무엇의 전부인지 적혀 있지 않았다.** 읽는 사람은 능력 열 종이 빈 볼륨에서
재현된 것으로 읽는다. 실제로는 하나다.

### 데모 열하나를 넣지 **않았다** — 재 볼 수 없다

이 세션에는 Docker 가 없다 (`docker info` 실패). 넣은 단계가 실제로 도는지 못 재고
게이트에 얹는 것은 이 저장소가 계속 잡아 온 **「됐을 것」**이다. 대신 두 가지를 했다:

1. **말과 사실을 맞췄다** — 통과 문구가 범위를 밝힌다
2. 새 데모가 **조용히 게이트 밖에서 태어나지 못하게** 못박았다 —
   `OUTSIDE_CLEAN_ROOM` 열하나가 **각자 이유**를 들고 있고, 늘리면 핀이 운다

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| `scripts/audio_demo.sh` 를 새로 만듦 | `test_no_demo_is_silently_outside_the_gate` |
| 통과 문구를 「전부 재현된다」로 되돌림 | `test_clean_room_states_its_scope` |
| 해명 목록에 `demo_violations.sh` 추가 | `test_the_outside_list_is_pinned` |
| `clean_room` 에서 `demo_violations` 단계 제거 | 첫 검사 — **문구만 고치고 단계를 지우면 후퇴다** |

재현: `python3 -m unittest tests.test_clean_room_covers_demos` (8 검사 · 730 통과)

## 중간 실패를 삼키는 스크립트가 **하나** 있었다 — 세던 검사는 **0** (큐 #44) — 2026-09-05

`set -e` 없이 돌면 중간 명령이 실패해도 다음 줄로 넘어간다. 마지막 줄이
`echo "전부 통과"` 면 그 스크립트는 **실패한 채 초록**이다. 이 회차가 계속 잡아 온
모양이다 — `#180`(누출 검사) · `#181`(통합 러너) · `tally.sh`(0건 통과).

### 실측

| 무엇 | 수 |
|---|---|
| `scripts/*.sh` | **37** |
| `set -euo pipefail` | **36** |
| `-e` 가 빠진 것 | **1** — `prod_room.sh` (`set -uo pipefail`) |
| `scripts/lib/*.sh` | **3** — `set` 없음이 **맞다** |
| 이것을 세던 검사 | **0** |

### `prod_room.sh` 는 고치지 않았다 — **못 쟀기 때문이다**

`chk()` 가 `if "$@"; then …` 이라 **`if` 조건 안의 실패는 `-e` 를 발동하지 않는다.**
그래서 `clean_room.sh` 는 같은 모양으로 `-e` 를 켜고도 집계가 멀쩡하다. 즉
`prod_room.sh` 도 켤 수 있어 **보인다.**

그러나 **켠 채로 51/51 을 다시 재 보지 못했다.** 이 세션에는 Docker 가 없다
(`docker info` 실패 — 10회차에는 있었다). 켜면 지금 세지 않는 중간 단계
(`dc run … apikey_cli issue` 등)의 실패가 전체를 중단시킬 수 있고, 그건 실제로
돌려 보고 정할 일이다. **못 쟀다고 적고 못박는다** — 스크립트 안에도 같은 이유를 남겼다.

### `scripts/lib/*.sh` 는 예외가 아니라 규칙이다

`source` 된 파일의 `set -e` 는 그 파일에서 끝나지 않고 **부른 셸의 옵션을 바꾼다.**
라이브러리가 호출자의 오류 처리를 바꾸면 안 된다 — 셋이 `set` 을 안 두는 것이 맞다.
아무도 `source` 하지 않는 lib 가 생기면 그 규칙이 공허해지므로 그것도 같이 본다.

### 뮤테이션 4

| 심은 것 | 운 검사 |
|---|---|
| `set` 없는 새 스크립트 | `test_every_script_sets_euo_pipefail` · `…comes_before_any_command` |
| `set` 앞에 실행 줄 하나 | 같은 둘 — **스무 줄 아래의 `set` 은 그 위를 못 지킨다** |
| `lib/tally.sh` 에 `set -euo pipefail` | `test_libs_set_nothing` · 탐지기 검사 |
| 예외 목록에 `clean_room.sh` 추가 | `…does_not_grow_silently` · `…carry_their_reason_in_the_file` |

재현: `python3 -m unittest tests.test_scripts_set_errexit` (10 검사 · 722 통과)

## 「뷰 컬럼은 정적으로 못 뽑는다」가 **틀렸다** — 사각 27건을 열었다 (큐 #41) — 2026-09-05

`#221`(큐 #34)은 Core 의 SQL 이 없는 컬럼을 부르는지 세면서, 뷰만은
**이름으로만** 알고 컬럼을 통째로 건너뛰었다. 머리말에 그렇게 적어 두었다:

> **뷰의 컬럼** (10개). `CREATE VIEW … AS SELECT` 는 정적으로 컬럼을 못 뽑는다.

**뽑힌다.** 이 저장소의 뷰 정의 12개(재정의 포함) **전부**가 명시 `SELECT` 목록을
갖는다. 최상위 `SELECT *` 는 하나도 없다.

### 걸림돌 셋 — 전부 넘었다

| 모양 | 어디 | 어떻게 |
|---|---|---|
| `LEFT JOIN LATERAL (SELECT * FROM …)` | `node_liveness` | **깊이 0 의 `FROM`** 에서 끊으면 안쪽이 안 섞인다 |
| `CASE … END AS reason` | `task_input_purge_due` | 꼬리의 `AS <이름>` |
| `count(*) FILTER (WHERE …) AS x` | `provenance_drift_summary` | 같음 |

`CREATE OR REPLACE` 재정의는 **뒤가 이긴다** — `0004` 의 `provenance_drift` 가
`0002` 를 덮고, `0013` 의 `task_input_purge_due` 가 `0011` 을 덮는다.

### 실측

| 무엇 | 전 | 후 |
|---|---|---|
| 뷰 | 10 (이름만) | **10 · 컬럼 86** |
| Core 참조 | 335 | **362** |
| 뷰 컬럼 참조 | **0 — 전부 버려졌다** | **27** (뷰 6종) |
| 없는 컬럼 | 0 | **0** |

버려지던 27건에는 `claim.py:26`·`registry.py:294` 의 `node_liveness.is_fresh`
— **큐를 집는 자리**가 들어 있다.

### 못 뽑는 뷰가 생기면 조용히 넘어가지 않는다

`_unresolved_views()` 가 세고 `test_no_view_is_silently_skipped` 가 오늘의 **0** 을
못박는다. 건너뛴 채 두면 그 뷰의 참조가 말없이 사라져 검사가 **지키는 척**만 한다.

### 뮤테이션 3

| 심은 것 | 운 검사 |
|---|---|
| `node_liveness` 의 `AS is_fresh` → `is_fresh_x` | `claim.py:26`·`registry.py:294` 를 짚었다 |
| `agent_arch_unbound` 를 `SELECT *` 로 | `test_no_view_is_silently_skipped` |
| 최상위 `FROM` 판정에서 깊이 무시 | `safety.py:68 agent_arch_unbound.routable` 이 사라졌다 |

재현: `python3 -m unittest tests.test_core_sql_columns_exist` (8 검사 · 712 통과)

## 새 런북이 생기자 `gh … list` 검사가 **눈을 감았다** — 2026-09-05

`#220`(큐 #36)은 「`gh pr list` 는 `--limit 100` 없이 쓰지 않는다」를 못박으며
런북 **셋을 상수로** 적었다:

```python
RUNBOOKS = (autonomous-mode.md, handoff-long-mode-claude.md, queue-expansion.md)
```

`#225` 가 **네 번째 런북** `docs/bridge/queue-batches.md` 를 만들고 「상태확인」
S0–S7 복붙 블록을 그리로 옮겼다. 세션이 실제로 붙여 넣는 명령이 **검사 범위 밖으로**
나간 것이다. 같은 커밋에서 `handoff` 의 두 자리는 산문(백틱)이 되었다.

### 바닥이 있었기 때문에 알았다

`main` 이 빨갰다 — `test_at_least_one_call_is_seen` 이 `2 not greater than or equal to 3`.

```text
docs/bridge/autonomous-mode.md:42   git fetch/pull main · gh pr list --limit 100
docs/bridge/autonomous-mode.md:213  gh pr list --state open --limit 100
```

`queue-batches.md:42` 의 `gh pr list --state open --limit 100` 은 **세지지 않았다.**
바닥(`≥3`)이 없었으면 검사는 **아무것도 안 지킨 채 초록**이었을 것이다 —
`#210` 이 「바닥을 내리면 초록」으로 잡은 것과 같은 자리다.

### 고친 것 — 목록을 버렸다

손으로 적는 대신 `docs/bridge/*.md` 를 훑고 **우편함 둘**만 뺀다:

```python
ARCHIVES = ("inbox-cursor.md", "inbox-claude.md")   # 고쳐진 결함의 「이전」을 보존한다
```

새 런북이 생기면 **이 파일을 고치지 않아도** 들어온다.

### 뮤테이션 3 — 새로 덮인 자리에서 심었다

| 심은 것 | 운 검사 |
|---|---|
| `queue-batches.md:42` 를 `--limit 30` | `test_every_limit_is_big_enough` |
| `queue-batches.md:42` 에서 `--limit` 제거 | `test_every_call_passes_a_limit` |
| `ARCHIVES` 에 `queue-batches.md` 추가 | 바닥·범위·핀 **3건** |

재현: `python3 -m unittest tests.test_gh_list_is_never_truncated`
(런북 4 · 자리 3 · 709 통과 · 건너뜀 7)

## 인증을 재는 절이 **두 라우트의 인증을 안 재고 있었다** — 2026-09-04

`prod_room.sh` §14 는 「무인증이면 전부 401」을 **강제 모드에서 실제로** 재는
유일한 자리다. ast 검사(`test_every_route_declares_its_auth`)는 「인증 헬퍼를
불렀는가」만 보기 때문이다.

이 환경에서 **처음으로 돌렸더니** (큐 #40 이 Docker 를 열었다) **49 통과 · 2 실패**:

```text
GET /v1/internal/capabilities/{id}/sample  (키 없음) → HTTP 422
GET /v1/internal/inputs/{id}/bytes         (키 없음) → HTTP 422
```

### 구멍이 아니었다 — **검사가 안 닿고 있었다**

두 핸들러는 `node_id` 를 **기본값 없는 쿼리 파라미터**로 받는다:

```python
def input_bytes(input_id: uuid.UUID, node_id: uuid.UUID, authorization: ... = Header(...)):
    _assert_node_matches(node_id, authorization)
```

FastAPI 는 **핸들러 본문보다 먼저** 파라미터를 검증한다. `?node_id=` 없이 부르면
`_assert_node_matches` 가 **아예 안 불린다.** 422 는 인증 판정이 아니라
**인증에 닿기 전에 멈춘 것**이다.

`?node_id=` 를 채워 다시 재니 **둘 다 401** 이다:

```text
===== 결과: 통과 51 · 실패 0 =====
제품 프로파일에서 전부 재현된다.
```

**인증은 멀쩡했다. 그것을 확인한다고 믿던 두 줄이 확인하지 않고 있었다.**
`#205`(큐 #12)가 눌러 보는 라우트를 **5 → 24** 로 늘리면서 심은 자리다.
넓힐 때 필수 파라미터를 안 본 것이고, 그때는 **이 스크립트를 돌릴 환경이 없었다.**

### 옛 숫자도 낡아 있었다

촬영 런북이 `prod_room` **27/27** 이라고 적고 있었다. 지금은 **51** 이다 — 같은 #205 가
늘린 결과다. 실측으로 바꿨다.

### 지키는 검사 — `test_prod_room_auth_probe` (12 → 14건)

| 검사 | 무엇을 막나 |
|---|---|
| `test_probe_supplies_every_required_query_param` | 필수 쿼리 파라미터를 빼먹으면 실패 — `main.py` 시그니처에서 **기본값 없는 인자**를 뽑아 대조한다 |
| `test_probe_finds_the_routes_that_need_params` | 그런 라우트를 하나도 못 찾으면 실패 (공허한 초록 방지) |

`_norm()` 이 쿼리를 떼도록 고쳤다 — 안 그러면 라우트 표와 안 맞아
「유령을 누른다」로 뒤집힌다.

**뮤테이션 4/4 잡는다** — 한쪽만 빼먹음 · **둘 다 빼먹음(오늘의 실제 상태)** ·
핸들러에 새 필수 파라미터 · §14 절 소멸.
재현: `bash scripts/prod_room.sh` (별도 프로젝트 `capnet-prod` · 포트 18830/18831)

## Core 가 부르는 컬럼이 스키마에 있는지 **아무도 안 세고 있었다** — 2026-09-04

큐 #34. 컬럼 이름을 잘못 적으면 **임포트도 되고 테스트도 통과한다.**
그 SQL 이 실제로 돌 때 `UndefinedColumn` 이 나고, 그건 **사용자 요청 한복판**이다.

스키마 세대가 **18** 이다. `ALTER TABLE … ADD COLUMN` 이 열여덟 번 지나갔다.
코드가 그걸 따라갔는지 세는 검사는 **없었다.** DDL 은 건드리지 않는다 — 드리프트만 본다.

### 실측 (2026-09-04) — 드리프트 **0**

| 무엇 | 수 |
|---|---|
| 정적 추출 테이블 | **27** · 컬럼 **217** · 뷰 **10** |
| 대조한 `<관계>.<컬럼>` 참조 | **335** · 관계 **20종** |
| 스키마에 없는 컬럼 | **0** |
| 그 0 을 **지키던** 검사 | **0** |

### 추출기를 먼저 **살아 있는 DB 와 대조했다**

`docs/spec/schema.sql` + `migrations/*.sql` 을 정적으로 읽는다 — DB 없이 돌아야
하기 때문이다. 그런데 **그 추출기가 맞는지부터 증명해야** 한다. Docker 가 이번에
생겼으므로(큐 #40) 세대 18 DB 의 `information_schema.columns` 와 맞췄다:

**27 테이블 · 컬럼 불일치 0.** 남은 셋(`schema_migration` ·
`audit_log_2026_08` · `audit_log_2026_09`)은 **런타임 산물**이라 DDL 파일에 없는 것이 맞다.

### 첫 추출기가 컬럼 넷을 놓쳤다 (이번 회차 세 번째 자기정정)

| 놓친 것 | 왜 |
|---|---|
| `agent_capability_passed.revoked_reason` · `.revoked_gate_run_id` | 한 `ALTER TABLE` 에 `ADD COLUMN` 이 **여럿** (0004) |
| `gate_run.capability_quality_profile` | 같은 모양 (0010) |
| `audit_log.*` | `CREATE TABLE … ) PARTITION BY RANGE (at);` — 닫는 괄호 뒤가 `;` 가 아니다 |

**DB 와 대조하지 않았으면 멀쩡한 컬럼 넷을 「드리프트」라고 적을 뻔했다.**
정본과 맞춰 보지 않은 추출기는 그 자체가 **결함 생성기**다.
`test_migrations_are_applied_on_top` 이 이 넷을 이름으로 못박는다.

### 별칭이 안 풀리면 참조가 **조용히 빠진다**

`FROM task t` 에서 별칭 하나만 지웠더니 참조가 **335 → 317** 로 줄었다.
검사는 그대로 초록이었다 — 세는 대상이 사라진 것을 아무도 안 보기 때문이다.
그래서 바닥을 **330** 으로 가깝게 뒀다. #210 이 여덟 자리에 바닥을 깐 것과 같은 이유다.

### 무엇을 안 보나 — 정직하게 적는다

- **뷰의 컬럼** (10개). `CREATE VIEW … AS SELECT` 는 정적으로 컬럼을 못 뽑는다.
  이름으로만 알고 컬럼은 건너뛴다 — **여전히 사각지대다**
- **한정 없는 컬럼** (`WHERE status = …`). 어느 관계인지 정적으로 못 정한다
- 문자열 조립 SQL. 이 저장소는 그렇게 쓰지 않지만 쓰면 안 보인다

### 지키는 검사 — `test_core_sql_columns_exist` (5건 신설)

**뮤테이션 5/5 잡는다** — 오타 컬럼(claim) · 오타 컬럼(main) · 마이그레이션 컬럼 소멸 ·
별칭 미해결 · 스키마 파일 부재.
재현: `python3 -m unittest tests.test_core_sql_columns_exist` (의존성 0 · DB 불필요)

## `gh … list` 가 30 에서 조용히 잘리는 것을 **고쳤지만 못박지 않았다** — 2026-09-04

큐 #36. `gh pr list` 의 **기본 상한은 30** 이고, 넘으면 오류가 아니라 **조용히 잘린다.**
이 저장소는 그것에 **이미 한 번 당했다** — 머지 프로브가 잘린 채
「전부 충돌 0」이라고 적고 있었다 (`inbox-cursor.md:7087`·`7216`).

고친 뒤 **글로만 적었다.** 세 런북이 「`--limit 100` 필수」라고 말할 뿐,
복붙 블록에서 옵션이 빠져도 **아무 검사도 울지 않았다.**
`#194` 가 연 자리와 같다 — 고치고 못박지 않은 과거 버그.

### 실측 (2026-09-04) — 오늘 어기는 곳은 없다

| 무엇 | 수 |
|---|---|
| 저장소 전체 `gh … list` | **22** |
| 그중 **실행 문맥** | **4** |
| 그 넷 중 `--limit` 없는 것 | **0** |
| 그 0 을 **지키던** 검사 | **0** |

### 첫 훑기가 여덟을 오탐했다 (이번 회차 첫 자기정정)

```text
- `gh pr list` without `--limit 100`          금지 규칙을 적은 줄
**`gh pr list` 의 기본 상한은 30 이다.**       왜 붙이는지 설명하는 줄
for b in $(gh pr list -R … --json …)          고쳐진 결함의 인용
```

**「명령을 말한다」와 「명령을 돌린다」는 다르다.** `#218` 이 `$node_id`·포트 문자열을
세어 「우회 일곱 건」이 될 뻔한 것과 같은 함정이다.

### 두 번째 판이 **지키는 척만 했다** (두 번째 자기정정)

「펜스 친 블록 안쪽만」으로 바꿨더니 `handoff-long-mode-claude.md` 에서 **뒤집혔다** —
그 파일은 **전체가 하나의 ` ```markdown ` 블록**이고 그 안에 ` ```bash ` 가 또 있다.
여는/닫는 짝만 세면 산문(29·40·162)이 「안쪽」, 진짜 복붙 명령(48)이 「바깥」이 된다.

그래서 **`--limit 30` 으로 낮춘 뮤테이션이 그대로 통과했다.** 산문 셋이 우연히
`--limit 100` 이라는 **글자**를 품고 있어 초록이었던 것이다.
**뮤테이션을 안 돌렸으면 「검사 신설」이라고 적고 넘어갔다.**

### 무엇으로 바꿨나 — **백틱을 걷어낸다**

산문은 명령을 **`` `백틱` ``에 넣어** 말하고, 돌아가는 명령은 코드블록에 **맨몸**으로 있다.
인라인 코드를 지운 뒤 보면 문서 구조(펜스 중첩)에 기대지 않는다 — 22 → **4**.

### 지키는 검사 — `test_gh_list_is_never_truncated` (6건 신설)

| 검사 | 무엇을 막나 |
|---|---|
| `test_every_call_passes_a_limit` | 복붙 블록·스크립트·CI 에서 `--limit` 이 빠지면 실패 |
| `test_every_limit_is_big_enough` | 100 보다 작게 낮추면 실패 (세 런북이 이미 적은 값) |
| `test_at_least_one_call_is_seen` | 세는 대상이 0 이 되면 실패 — 공허한 초록 방지 |
| `test_detector_discriminates` | 백틱 산문을 잡거나 맨몸 명령을 놓치면 실패 |

**뮤테이션 5/5 잡는다.** 재현: `python3 -m unittest tests.test_gh_list_is_never_truncated`

### 범위에서 뺀 것 — `inbox-cursor.md`

**우편함 아카이브다.** 8천 줄이 지나간 회차의 기록이고 위 인용처럼 **고쳐진 결함의
「이전」**을 일부러 보존한다. 여기를 강제하면 **역사를 고쳐 쓰게 된다.**

## capreq 키 검사가 **낱말 하나만 보고 있었다** — URL 은 열려 있었다 — 2026-09-04

큐 #35. `#192`·`#193`(Core) · `#194`(Node) 가 「키가 출력으로 새는가」를 전수했고,
`test_capreq_binds_loopback` 이 capreq 쪽을 맡았다. 그 파일의 3번 주장이
「**키는 헤더로만 나간다**」였는데, 그것을 지키던 검사는 한 줄이었다:

```python
self.assertIn("authorization", src.lower(), "키를 헤더로 안 보낸다")
```

**어댑터 소스에 그 낱말이 있기만 하면 통과한다.**

### 실측 (2026-09-04) — 오늘 새는 곳은 **없다**. 그런데 막지도 않았다

| 무엇 | 수 |
|---|---|
| `self.api_key` 를 **읽는** 자리 | **1** (`_headers()`) |
| 키를 URL·쿼리에 싣는 자리 | **0** |
| 그 0 을 **지키던** 검사 | **0** |

키를 URL 에 심은 뮤테이션 셋이 **일곱 검사를 전부 초록으로 통과했다**:

```python
f"?capability={capability_code}&version={capability_version}&key={self.api_key}"
f"{self.core_url}/{self.api_key}/v1/capabilities"
f"{self.core_url}/v1/tasks/{task_id}?k={self.api_key}"
```

셋 다 `_headers()` 를 건드리지 않으므로 `authorization` 은 그대로 있다.
**URL 은 헤더와 다르다** — 프록시 로그·`Referer`·브라우저 히스토리·Actions 로그에
값이 그대로 남고, 지워도 캐시에 남는다. `#217` 이 Actions 로그를 「가장 나쁜 자리」라고
적은 것과 같은 이유다.

### 무엇으로 바꿨나 — **낱말이 아니라 읽는 자리**

키를 어디에 싣든 **먼저 `self.api_key` 를 읽어야 한다.** 그래서 읽는(`ast.Load`)
자리를 세고 `_headers()` 하나로 묶는다. 쓰기(`__init__` 의 `self.api_key = api_key`)는
세지 않는다 — 보관은 정상이다. 읽는 자리를 묶으면 **쿼리·경로·본문·로그가 한꺼번에** 닫힌다.

### 지키는 검사 — `test_capreq_binds_loopback` (7 → 9건)

| 검사 | 무엇을 막나 |
|---|---|
| `test_only_the_header_builder_reads_the_key` | `_headers()` 밖에서 키를 읽으면 실패 |
| `test_probe_finds_the_reader` | 읽는 자리가 0 이 되면 위 검사가 공허해지므로 실패 |

**뮤테이션 4/4 잡는다** — 쿼리스트링 · URL 경로 · 폴링 URL · 헤더 빌더 제거.
재현: `python3 -m unittest tests.test_capreq_binds_loopback` (의존성 0).

`ALLOWED_READERS` 를 늘리려면 **거기 적고 왜 안전한지 근거를 남겨야** 한다.

## Core 를 우회하는 스크립트는 **하나뿐이고, 문서가 그렇게 적는다** — 2026-09-03

큐 #29. 제품 주장의 한 줄이다 — 「사용자는 기기 주소를 모른다. 기기는 Core 가
배정하지 않은 실행을 거부한다.」 #200 이 그 주장을 **틀린 파일에 붙여 놓은 것**을 고쳤다.
이건 그 옆자리다 — **말이 아니라 스크립트가 실제로 무엇을 부르는가.**

### 실측

| 무엇 | 수 |
|---|---|
| Node URL 을 **부르는** 스크립트 | **9** |
| 그중 **`/health` 만** 부르는 것 | **8** |
| **실행·claim 을 직접 부르는 것** | **1** — `smoke_w1.ps1` |

`/health` 는 준비 단계다 — 가중치 해시·`arch` 를 **그 기기의 증언**에서 뽑는다(운영자 몫).
남은 하나가 `POST $node/v1/execute` (212행)와 `POST $core/v1/internal/claim` (203행)을 부른다.

**그건 결함이 아니다.** `README` 가 그 스크립트를 「**dummy 게이트 배관** + placeholder
추론」이라고 적는다. `main.py:1548` 의 주석 「이전에는 클라이언트가 claim 을 직접
호출하고 Node 에도 직접 접속했다」가 가리키는 **그 시절의 도구**이고, 그 사실이
문서에 남아 있다. **「Core 우회 1건」이 아니라 「의도된 배관 smoke 하나」다.**

### 탐지기가 **여섯 자리를 오탐했다** (적어 둔다 — 이번 회차 네 번째)

처음 판은 `\$\{?(?:node|NODE_URL)\}?` 였다. 이것이 잡은 것들:

```text
$node_id                       UUID 변수
"${node_port}:8001"            compose 포트
$core + $node                  SBOM 목록
\"$node\"                       JSON 본문의 node_id
```

**뒤에 `/` 를 요구하니 여섯이 한 번에 빠졌다** — 「Node 를 **언급**한다」와
「Node 를 **부른다**」는 다르다. 그대로 뒀으면 **「우회 일곱 건」**이라고 적을 뻔했다.

### 지키는 검사 — `test_scripts_go_through_core` (7건)

`/health` 밖으로 Node 를 부르거나 `internal/claim` 을 부르는 스크립트는
`PLUMBING` 에 **근거와 함께** 적혀 있어야 한다. 근거가 `README` 를 인용하므로
**그 문장이 사라지면 근거도 빈다** — 검사가 그것도 본다.

**뮤테이션 5종 전부 물렸다** — Node 를 직접 실행하는 새 스크립트 ·
기존 데모가 claim 을 부름 · 근거 비우기 · **유령 항목** · 탐지기 눈멀게 하기.

### 큐 #32 — **코드 없음** (같이 잰 것)

compose 헬스체크 전수. **1건**이고 `pg_isready -U … -d …` 다 —
**항상 성공하는 명령이 아니다** (DB 가 안 뜨면 실패한다). 다른 서비스에는 헬스체크가 없고,
기동 순서는 `depends_on` 과 `migrate` 일회성 잡이 잡는다. **더할 것이 없다.**

`run_tests` **692 OK (건너뜀 7)** · `check_submission` **28/28**.

## 시크릿 검사가 **CI 워크플로는 안 보고 있었다** — 2026-09-03

큐 #31. #196 이 「시크릿이 런타임 출력으로 나가는가」를 전수해 못박았다.
그 검사가 훑는 범위는 이렇다:

```python
for p in sorted(tree.rglob("*.py")): ...
for p in sorted((ROOT / "scripts").glob("*.sh")): ...
```

**`.github/workflows/*.yml` 은 범위 밖이었다.**

그런데 Actions 로그는 **가장 나쁜 자리**다 — 공개 저장소에서 누구나 읽고,
지워도 캐시·포크·알림에 남는다. `echo "${{ secrets.X }}"` 한 줄이면 끝난다.

### 실측 — 오늘 새는 곳은 없다

| 무엇 | 수 |
|---|---|
| 워크플로 파일 | **1** (`ci.yml`) |
| `${{ secrets.* }}` 사용 | **0** |
| 시크릿 낱말을 출력하는 `echo`/`printf`/`cat` | **0** |
| `set -x` (블록의 모든 명령을 값과 함께 로그로) | **0** |

`POSTGRES_PASSWORD: capnet` 은 **일회용 서비스 컨테이너**의 값이고 `echo` 되지 않는다.

### 내 탐지기가 **이 저장소의 키 이름을 못 잡았다** (적어 둔다)

처음 판은 `\b(?:secret|password|…|api[_-]?key)\b` 였다.
그런데 **`CAPNET_API_KEY` 를 못 잡았다** — `_` 가 단어 문자라 `_API` 앞에 경계가 없다.

**#196 이 「낱말 목록에 `cred` 가 없어 `$cred` 를 못 잡았다」로 겪은 것과 같은 함정이다.**
검사를 짜면서 만든 `test_detector_discriminates` 가 그걸 잡았다 — 그 검사가 없었으면
「CI 는 깨끗하다」를 **눈먼 탐지기로** 말할 뻔했다.

### 무엇을 고정하지 않았나

- `${{ secrets.* }}` **사용 자체**. 배포·토큰이 필요해질 수 있다 — 막는 것은 **출력**이다
- 워크플로 안의 **리터럴 값**. 일회용 테스트 DB 비밀번호가 그렇고 그건
  `check_submission.check_secrets` 의 몫이다 — 겹치면 어느 검사가 지키는지 흐려진다

**뮤테이션 6종 전부 물렸다** — 시크릿 환경변수 `echo` · `secrets` 표현식 출력 ·
`set -x` · `password` 를 `cat` · 훑는 범위 비우기 · **탐지기를 낱말 경계로 되돌리기**.

### 큐 #13 — **코드 없음** (같이 잰 것)

compose·Dockerfile 의 바인딩을 전수했다. **어긋난 곳 0.**

| 자리 | 값 | 판정 |
|---|---|---|
| `apps/core/Dockerfile` · `apps/node/Dockerfile` | `--host 0.0.0.0` | **정상** — 컨테이너 안이고, 노출은 compose `ports:` 가 정한다 |
| `capreq` `serve`·`gemma` `--host` | `127.0.0.1` | `test_capreq_binds_loopback` 이 못박는다 (#195) |
| postgres 호스트 노출 | prod 오버레이가 `ports: !override []` | `prod_room` §1 이 실제로 누른다 |

**세 축이 이미 덮여 있다.** 새 검사를 더하면 어느 것이 지키는지 흐려진다.

`run_tests` **685 OK (건너뜀 7)** · `check_submission` **28/28**.

## 화면이 **사용자가 시키지 않은 능력**으로 작업을 만들 수 있었다 — 2026-09-03

큐 #28. `call.html` 의 제출 핸들러:

```js
const [code, version] = ($("c-cap").value || "image.classify|1").split("|");
```

`/v1/capabilities` 를 못 받으면 그 `<select>` 는 `(없음)`(값이 빈 문자열)이 된다.
그대로 제출하면 **`image.classify@1` 로 작업이 만들어진다** — 사용자는 고른 적이 없다.

**바로 아래 데이터셋은 같은 함정을 이미 고쳤다** (#184·#189 — 「못 받았으면 못 받았다고
한다」). 능력 쪽은 남았고, `test_ui_invariants` 는 **`catch` 블록만** 봐서 못 잡았다 —
이 폴백은 `catch` 밖에 있다.

빈 값이면 **거절**하게 했다. `caseId` 가 이미 그렇게 한다.

### 검사를 넓혔다 — `||` 기본값도 본다

`test_no_domain_value_is_used_as_a_fallback` — `catch` 안이든 밖이든,
**서버 카탈로그가 주는 값**을 `||` 기본값으로 쓰면 실패한다.
두 검사가 같은 목록(`INVENTED`)을 본다 — 갈리면 한쪽만 지켜진다.

### 내 검사가 **같은 함정에 빠져 있었다** (적어 둔다)

뮤테이션으로 `INVENTED = ()` 를 넣었더니 **두 검사가 다 초록이었다.**
목록을 비우면 아무것도 안 훑는다 — 이 회차 #210 이 고친 「0건을 훑으며 통과」를
**내가 만든 검사가 하고 있었다.**

바닥을 넣었다: `INVENTED` 는 **비어 있으면 안 되고**, 각 항목이 **카탈로그의 능력 코드**
이거나 **allowlist 의 데이터셋 id** 여야 한다. 비워도, 가짜를 넣어도 걸린다.

**뮤테이션 5종 전부 물렸다** — 원래 `||` 폴백으로 되돌리기 · 다른 페이지에 데이터셋
폴백 심기 · `catch` 안에 능력 리터럴 · **목록 비우기** · **목록에 가짜 값 넣기**.

`run_tests` **678 OK (건너뜀 7)** · `check_submission` **28/28**.

## 「CI 가 본다」가 **거짓이었다** — 건너뛴 일곱은 어디에서도 안 돈다 — 2026-09-03

큐 #26. `test_skip_reasons` 는 건너뛰는 **사유**를 허가 목록으로 관리한다.
그 목록이 「어디서 도는가」를 **적기만** 하고, 아무도 대조하지 않았다.

### 실측 — 두 사유가 거짓이었다

```text
"psycopg 없음 …"    적힌 근거: 「CI 의 migrate 잡에서는 실제로 돈다」
"capreq 를 못 읽었다" 적힌 근거: (어디서 도는지 안 적음)
```

`ci.yml` 을 열었다:

| 잡 | 무엇을 discover 하나 | 무엇을 설치하나 |
|---|---|---|
| `unit` | **`tests`** | **없음** |
| `capreq` | `capreq/tests` | httpx · fastapi · multipart · **setup-node** |
| `migrate` | `scripts/run_integration.sh` = **`tests/integration/check_*.py`** | psycopg · fastapi 등 |

**`tests/` 를 보는 것은 `unit` 잡 하나뿐이고, 그 잡은 아무것도 설치하지 않는다.**
migrate 잡이 돌리는 것은 `tests/integration/check_*.py` — **다른 파일**이다.

그래서 건너뛴 일곱은 **CI 어디에서도 안 돈다**:

| 사유 | 파일 | 실제로 도는 곳 |
|---|---|---|
| `psycopg 없음` (5) | `test_arch_registry` · `test_contract_checks_by_arch` · `test_capability_catalog` | **없음** |
| `capreq 를 못 읽었다` (2) | `test_route_bench` | **없음** |
| `node 가 없다` (2) | `capreq/tests/test_chat_render` | ✅ `capreq` 잡 (setup-node 있음) |

**「CI 가 본다」고 적어 두면 그 순간부터 아무도 다시 안 센다.** 이 회차가 고쳐 온
「보고 있다고 믿는데 안 보고 있다」와 정확히 같은 모양이다.

### 고친 것 — 근거에 `runs_in` 을 붙였다

`ALLOWED` 를 `사유 → (근거, runs_in)` 으로 바꿨다.
`runs_in` 이 잡 이름이면 **`ci.yml` 이 그 트리를 discover 하는지 대조**하고,
`None` 이면 근거에 **「안 돈다」가 적혀 있어야** 통과한다.

**CI 를 고치지 않았다.** unit 잡에 의존성을 넣거나 migrate 잡에 `discover -s tests` 를
더하는 것은 **config 변경**이라 (`CLAUDE.md`) 혼자 하지 않는다 — inbox 에 Proposal 로 올린다.
여기서 한 것은 **거짓 주장을 사실로 맞추고, 다시 거짓이 될 수 없게** 한 것이다.

### 내가 #207 에서 넣은 경고를 같이 지웠다

`test_input_contract_rejections_actually_run` 머리말에 `grep … "a\|b"` 를 적었더니
`SyntaxWarning: invalid escape sequence` 가 났다. **지금은 경고지만 다음 세대에서는 에러**다.
docstring 을 raw 로 바꾸고, **검사 소스에 파이썬 경고가 남지 않는지** 보는 검사를 넣었다 —
스위트가 경고를 흘리면 **진짜 경고가 묻힌다.**

**뮤테이션 4종 전부 물렸다** — 「CI 가 본다」를 거짓으로 되돌리기 ·
capreq 잡이 그 트리를 안 보게 하기 · **잘못된 이스케이프 다시 넣기** · `ci.yml` 잡 이름 바꾸기.

`run_tests` **676 OK (건너뜀 7)** · `check_submission` **28/28**.

## 카탈로그가 「구현됨」이라 적은 열 종이 **정말 등록되는가** — 2026-09-03

큐 #27. `test_report_claims` 는 **원고가 부른 능력**이 카탈로그에서 「구현됨」인지 본다.
**반대 방향은 아무도 안 봤다** — 카탈로그가 「구현됨」이라 적은 능력에
**실제로 등록되는 길이 있는가.**

길이 없으면 그 능력은 **문서에만 있다.** 심사위원이 재현하면 `GET /v1/capabilities` 에
안 나오고, 그때 **나머지 아홉의 신뢰도까지** 같이 떨어진다.

### 실측 — **10/10 길이 있다**

| 능력 | 등록 경로 |
|---|---|
| `image.classify` | `call.sh` · `seed.sql` |
| `image.embed` | `image_embed_demo.sh` |
| `text.classify` | `text_demo.sh` |
| `text.extract` | `text_extract_demo.sh` |
| `text.ner` | `ner_demo.sh` · `product_demo.sh` |
| `text.embed` | `embed_demo.sh` |
| `text.rank` | `text_rank_demo.sh` |
| `table.extract` | `table_demo.sh` |
| `timeseries.forecast` | `series_demo.sh` |
| `safety.pii` | `pii_demo.sh` |

재현: `python3 -m unittest tests.test_catalog_has_a_registration_path -v`

7회차 inbox 가 「전부 있다 (데모 9 + seed 1)」를 **손으로** 확인했다.
같은 것을 기계가 하게 했다 — **손으로 센 것은 다음 줄이 늘 때 안 다시 센다.**

### 무엇을 고정하지 않았나

- **개수**(`10`). 자라는 값이라 못박으면 사람이 숫자만 고친다
- 「구현됨이 **아닌**」 줄 — 선언만 있는 능력은 정상이다 (**D27 `retrieve.*`** 가 그 예다)
- 그 데모가 **실제로 도는지** — Docker 가 필요하다. 보는 것은 **길의 존재**다

**뮤테이션 4종 전부 물렸다** — 길 없는 능력을 「구현됨」으로 추가 ·
기존 능력의 등록 경로 제거 · 표 파서 눈멀게 · **찾기를 항상 참으로**.

`run_tests` **670 OK (건너뜀 7)** · `check_submission` **28/28**.

## 문서대로 보내면 **422** 였던 자리 — 2026-09-03

큐 #24. 경로·메서드는 `#142` 가, 머리말(`info`)은 `#201` 이 못박았다.
**요청 본문은 아직 밖이었다.** 전수했다.

`requestBody` 스키마가 있는 오퍼레이션 **11** 중 **하나가 깨져 있었다**:

```text
POST /v1/internal/assignments/{assignment_id}/fail
  문서:  properties: { reason }
  모델:  FailBody(node_id: uuid.UUID = Field(alias="nodeId"), reason: str = "")
```

**`nodeId` 가 통째로 빠져 있었다.** 기본값이 없으니 필수다 —
문서를 그대로 따라 `{"reason": "…"}` 만 보내면 **422** 다. `required:` 도 없었다.

**Node 는 동작하고 있었다.** `_report_failure` 가 `nodeId` 를 보내기 때문이다.
그래서 아무도 몰랐다 — **문서만 보고 붙이는 쪽만 막힌다.** 두 사본 다 고쳤다.

### `populate_by_name` — 오탐 셋을 걸러 냈다

첫 훑기는 셋을 더 잡았다: `SampleBody`(`input_id` vs `inputId`) ·
`RevokeBody`(`agent_id` vs `agentId`) · 그리고 `credential_issue`(모델을 못 찾음).

**앞의 둘은 틀린 것이 아니다** — 세 모델 다 `model_config = {"populate_by_name": True}` 라
필드명도 alias 도 받는다. 표기를 한쪽으로 모으는 것은 **계약의 모양**이라 하지 않았다
(`CLAUDE.md` 브리지절). 셋째는 `Body | None = None` 형태를 파서가 못 읽은 것이라 파서를 고쳤다.

**「어긋난 것 넷」이라고 적지 않았다** — 실제로 깨진 것은 하나다.

### 지키는 검사 — `test_openapi_request_schema_agrees` (7건)

1. 문서가 적은 속성은 **모델이 받는 이름**이어야 한다 (필드명 **또는** alias)
2. 모델의 **필수 필드**(기본값 없음)는 문서에 있어야 한다 — **이게 `nodeId` 를 잡았다**
3. `required:` 의 이름도 모델이 받아야 한다 · 스키마가 있으면 핸들러가 실재해야 한다

**`pyyaml` 을 쓰지 않는다.** CI 단위 잡에는 `pip install` 단계가 **없다**
(`python3 -m unittest discover` 뿐). 처음 판은 `import yaml` 이었고 **로컬에서만 돌았을 것이다** —
`test_openapi_drift` 가 같은 이유로 텍스트 파싱을 쓴다고 적어 둔 것을 뒤늦게 봤다.
손파서로 바꾸고 **같은 11건이 나오는지 대조**했다.

**응답 스키마는 안 본다** — 45개 중 0건이고 채우는 것은 `openapi-response-schemas`
**Decision** 대기다 (#202). 부재를 못박으면 채우는 것을 막는다.

**뮤테이션 6종 전부 물렸다** — `nodeId` 를 다시 빼기(**원래 상태**) · 모델에 새 필수 필드 추가 ·
문서에 모델이 안 받는 속성 · `required` 에 없는 이름 · **필수 판정을 전부 「선택」으로** ·
**파서 들여쓰기 규약 깨기**.

`run_tests` **666 OK (건너뜀 7)** · `check_submission` **28/28**.

## `capreq` 도 버전을 **네 곳**에 흩어 두고 있었다 — 2026-09-03

큐 #23. #201 이 Core 에서 같은 사고를 잡았다 — `openapi.yaml` 은 `0.3.0`,
`FastAPI(version=)` 은 `0.2.0`. **같은 서비스가 두 버전을 말했다.**
그 검사는 Core 두 자리만 못박았다. 나머지를 전수했다.

| 어디 | 값 |
|---|---|
| `capreq/pyproject.toml` | `0.1.0` |
| `capreq/src/capreq/__init__.py` `__version__` | `0.1.0` |
| `server.py` `FastAPI(version=…)` | `0.1.0` **(리터럴)** |
| `gemma_server.py` `FastAPI(version=…)` | `0.1.0` **(리터럴)** |

재현:

```bash
grep -rnE "^version = |__version__|FastAPI\(.*version=" capreq/pyproject.toml capreq/src
```

**오늘은 넷 다 같다.** 그런데 맞추는 것이 없다 — 하나만 올리면 조용히 갈린다.
**Core 가 실제로 그렇게 갈렸다.**

### 고친 것 — 자리를 넷에서 둘로

두 서버의 **리터럴을 없앴다.** 이제 `capreq.__version__` 하나에서 온다.
남은 자리는 둘(`pyproject.toml` · `__init__.py`)이고 검사가 **같은지 본다.**

`pyproject.toml` 은 빌드가 읽고 `__version__` 은 코드가 읽는다. 둘을 합치려면 동적 버전
배관이 필요해 **한쪽이 움직이면 걸리게** 하는 쪽을 골랐다.

### 무엇을 고정하지 않았나

**버전 값 자체.** `0.1.0` 을 박으면 올릴 때마다 검사가 일을 시킨다 —
`test_doc_counts` 가 적은 그 함정이다. 보는 것은 **서로 같은가** 하나다.

Node(`apps/node/app/main.py`)의 `0.2.0` 은 **대조 상대가 없다** — 스펙 파일이 없어
갈릴 자리가 없다. 짝이 생기면 그때 넣는다. **지금 넣으면 지킬 것이 없는 검사가 된다.**

### 뮤테이션 **6종 전부 물렸다**

`pyproject` 만 올리기 · `__version__` 만 올리기 · 서버가 리터럴로 되돌아가기 ·
**임포트 없이 이름만 쓰기** · `version=` 을 빼기 · `__version__` 을 `"dev"` 로 바꾸기.

### 못 쟀다

`capreq` 단위 검사는 **로컬에서 못 돌린다** (`fastapi` 없음). 정본은 CI 의 `capreq` 잡이고,
이 변경은 그 잡이 임포트하는 모듈 둘을 건드린다.

`run_tests` **659 OK (건너뜀 7)** · `check_submission` **28/28**.

## 검사가 **빈 목록을 돌며 초록**이 되지 않게 — 2026-09-03

큐 #21. 이 회차들이 고쳐 온 결함의 **원형**이다 — #181 은 통합 러너가 0개를 돌고
「통과 0 · 실패 0」을 찍었고, #187 은 방 판정이 같은 모양이었다.
`for x in f(): self.assertX(...)` 는 **`f()` 가 비면 아무것도 안 보고 통과한다.**

### 결론부터 — **실제로 초록이 되는 검사는 0건**이었다

훑기를 세 번 좁혔다:

```text
테스트 함수 721 → 단언이 루프 안에만 75 → 계산된 컬렉션 31 → **호출 결과 8**
```

그리고 **훑기를 믿지 않고 대상을 비워서** 확인했다. 추출기가 아무것도 못 찾게 만들자
`test_text_extract` 는 **21건 중 6건이 실패**했고, PII 규칙을 비우자 `test_safety_pii` 는
**32건 중 11건이 실패**했다. **형제 검사가 받쳐 주고 있었다.**

**「구멍 여덟」이라고 적지 않았다** — #192 가 「결함 11건」이라고 적지 않은 것과 같다.

### 그래도 고친 이유

받쳐 주는 것이 **다른 검사**라는 것은, **그 형제를 지우는 순간 조용히 구멍이 난다**는 뜻이다.
호출 결과를 도는 여덟 자리에 바닥 한 줄씩 넣어 **스스로 서게** 했다.

| 검사 | 무엇이 비면 초록이었나 |
|---|---|
| `test_migrate_lint::…lint_clean` | 마이그레이션 디렉터리를 못 읽을 때 |
| `test_modality_fallback::…is_decided` | 모달리티 어휘가 빌 때 |
| `test_node_core_unreachable` ×2 | **`except` 를 통째로 지웠을 때** |
| `test_node_routes_are_pinned::…credential` | `health` 가 빈 dict 일 때 |
| `test_pass_rate_script::…arch_names` | arch 목록이 빌 때 |
| `test_safety_pii::…original_span` | 스캐너가 아무것도 못 찾을 때 |
| `test_text_extract::…the_value` | 추출기가 아무것도 못 찾을 때 |

### 넓게 잡은 첫 판은 **일흔다섯 자리에 잔소리**를 했다 (적어 둔다)

처음 훑기는 리터럴 튜플(`for m in ("a", "b"):`)까지 「바닥 없음」으로 셌다.
그대로 검사로 만들었으면 **일흔다섯 자리를 고치라고 요구**했을 것이고,
그러면 사람이 **검사를 끄는 쪽**을 고른다.

좁힌 기준 셋: **호출 결과만** · **같은 함수 안**만 · 개수는 못박지 않는다.
그 좁힘 자체가 검사로 남아 있다 (`test_literal_loops_are_not_flagged`).

### 지키는 검사 — `test_loop_tests_have_a_floor` (4건)

**뮤테이션 5종 전부 물렸다** — 넣은 바닥 다시 빼기 · **바닥 없는 새 검사 파일 투입** ·
탐지기를 헐겁게(전부 통과) · 훑는 범위 비우기 · **리터럴까지 잡는 잔소리 판**.
마지막 둘이 양방향이다 — 헐거워져도, **과하게 잡아도** 실패한다.

`run_tests` **653 OK (건너뜀 7)** · `check_submission` **28/28**.

## 조용히 삼키는 자리 — 오늘은 없고, **근거 없이 늘 수 없게** 했다 — 2026-09-03

큐 #20. 이 회차들이 고쳐 온 결함은 한 모양이다 — **아무것도 못 봤는데 초록으로 끝난다**
(#180 누출 검사 0건 · #181 통합 러너 0개 · #187 방 판정 · #205 공개 프로브의 `000`).
`except Exception: pass` 는 그 모양을 **한 줄로** 만든다.

### 실측 — 결함 0건

| 무엇 | 수 |
|---|---|
| 광범위 `except` (`Exception`·`BaseException`) | **25** |
| **bare `except:`** | **0** |
| 본문이 `pass`/`continue` **뿐** | **1** — `compare_ab.py` 의 stdout 인코딩 |
| `contextlib.suppress(Exception)` | **1** — Node 실패 보고 |
| 삼키고 **성공값**을 돌려주는 자리 | **0** |

**스캐너를 믿지 않고 열셋을 다 열었다.** 나머지 스물셋은 전부 재던지거나 · 로그하거나 ·
**실패 상태를 기록한다** — `checks[...] = False`(계약 게이트 넷) · `r.error = …`(부하 프로브) ·
`ok=False`(capreq) · `_note_core_error`(Node). `db.py` 의 `return None` 하나가 성공값 후보로
남았는데, 그것은 **경고를 남기고 직결로 폴백**하는 자리였다.

### 스캐너가 `return 1` 을 **성공**으로 셌다 (적어 둔다)

「삼키고 성공으로 끝나는 자리」를 `x.value in (True, 0)` 으로 걸렀더니
`main()` 의 **실패 종료 코드** `return 1` 이 잡혔다 — 파이썬에서 `1 == True` 이기 때문이다.
**뜻이 정반대인 것을 같은 것으로 셌다.**

`is True` 로 고치고 나서야 후보가 `db.py` 하나로 좁혀졌다. 그대로 뒀으면
「결함 셋」이라고 적을 뻔했다 — #192 가 「결함 11건」이라고 안 적은 것과 같은 자리다.

### 지키는 검사 — `test_no_silent_exception_swallowing` (7건)

**막지 않고 근거를 적게 만든다** (`test_every_route_declares_its_auth` 의 `PUBLIC` 과 같은 방식).

1. **bare `except:` 는 0** — 어떤 근거로도 허용하지 않는다 (`KeyboardInterrupt` 까지 먹는다)
2. `pass`/`continue` 뿐인 광범위 `except` 는 `ALLOWED` 에 **근거와 함께**
3. `contextlib.suppress(Exception)` 도 같은 규율
4. **유령 금지** — 사라진 자리가 목록에 남으면 다음 사람이 「허용된 거였지」로 넘어간다

목록의 키는 **`(파일, 감싸는 함수)`** 다. 줄 번호로 잡으면 위쪽을 한 줄만 고쳐도 깨지고,
그러면 사람이 검사를 고치게 된다.

**뮤테이션 6종 전부 물렸다** — bare except 투입 · 근거 없는 `except: pass` ·
근거 없는 `suppress` · **허용된 자리를 없애 유령 만들기** · 근거 비우기 · 훑는 범위 비우기.

`run_tests` **649 OK (건너뜀 7)** · `check_submission` **28/28**.

## 절대 규칙 여섯을 **기계가 전수한다** — 2026-09-03

큐 14–19. `CLAUDE.md` 의 절대 규칙은 「이것을 어기면 프로젝트의 핵심 주장이 무너진다」고
적혀 있다. 그런데 **지키는 것은 사람의 기억**이었다.

전수했다. **오늘 새는 곳은 없다** — 그리고 그것이 이 검사를 만드는 이유다
(7회차 #192–#196 과 같은 자리: 「오늘 0 · 지키는 것이 없어서 → 검사」).

| 규칙 | 무엇 | 오늘 |
|---|---|---|
| **5** | pickle · `.pt` · `.pth` 로드 | **0건** — 로드는 전부 `safetensors.torch.load_file` |
| **2** | `assignment` · `gate_run` INSERT | **5자리 전부** `INSERT … SELECT` |
| **4** | Node 가 자기 등급을 주장 | **0건** — 소진은 초대장, 등록은 admin |
| **8** | 게이트가 제출자 Node 에서 | **0건** — 앱 가드 + `ck_gate_runner_team` + `INSERT … SELECT` |
| **7** | 자유 업로드 · 서명 URL · `fileToken` | **0건** — 금지 문구가 **주석에만** 있다 |
| **3** | `compute_tier` 앱 문자열 비교 | **0건** |

재현:

```bash
python3 -m unittest tests.test_absolute_rules_are_enforced -v
```

### `grep` 으로 재면 **금지 문구 자체가 위반으로 잡힌다**

`apps/core/app/main.py:433` 은 이렇게 **적는다**:

```text
금지되는 것은 「자유 업로드」가 아니라 **비통제 수집**(서명 URL·fileToken)이다.
```

`grep -i fileToken` 은 이 줄을 위반으로 센다. **규칙을 적어 둔 것과 쓴 것은 다르다.**
그래서 문자열·호출·인자 이름을 `ast` 로 보고 **주석과 docstring 은 세지 않는다.**
`_live_strings` 가 그 경계이고, 그 경계가 너무 넓지 않은지도 검사한다
(`test_docstrings_are_actually_excluded`).

### 규칙 4 가 가장 좁은 자리

`POST /v1/nodes/redeem` 은 **관리 키 없이 열린 유일한 쓰기 경로**다.
그래서 셋을 함께 못박는다 — 요청 모델에 등급 필드가 **없다** ·
핸들러가 `invite["trust_domain"]` 을 읽고 `body.trust_domain` 을 **안 읽는다** ·
`is_gate_runner=False` 로 만든다.

### 무엇을 **안** 봤나

규칙 1(schema 제약 약화)·6(사전학습 가중치)은 여기서 안 본다 —
`test_migrate_lint`·`test_license_coverage`·`check_submission` 이 이미 본다.
**겹쳐 두면 어느 검사가 진짜로 지키는지 흐려진다.**

### 뮤테이션 — **9종 전부 물렸다**

`torch.load` 로 가중치 읽기 · `.pth` 경로 상수 두기 · `assignment` 를 `VALUES` 로 INSERT ·
소진 본문에 `trust_domain` 필드 넣기 · **소진 핸들러가 초대장 대신 본문을 읽기** ·
소진이 게이트러너를 만들게 하기 · `registry` 의 team 가드 제거 ·
서명 URL 파라미터 추가 · `compute_tier` 를 `<` 로 비교.

`run_tests` **642 OK (건너뜀 7)** · `check_submission` **28/28**.

## 고쳤다고 **주석에만** 적힌 자리 — 둘은 아무도 안 돌려 봤다 — 2026-09-03

큐 #33. 「`TODO`/`FIXME`/`이전에는` 주석 중 못박힌 검사가 없는 과거 버그」를 전수했다.

### 실측 — `TODO`·`FIXME` 는 **진짜 0건**

```bash
grep -rnE "TODO|FIXME|XXX|HACK" --include=*.py --include=*.sh apps/ scripts/ capreq/src tests/
```

걸린 것은 전부 `mktemp -t capnet-XXXXXX` 였다. **미뤄 둔 일이 코드에 없다.**

### 과거 버그 주석 **열넷** — 열둘은 이미 못박혀 있었다

| 자리 | 못박은 검사 |
|---|---|
| `complete.py:166` 깨진 `required` | `test_broken_contract_does_not_disable_check` |
| `complete.py:237` 「안 봤다」 경고 | 같은 검사 (#186 이 뮤테이션 안 물려 추가한 자리) |
| `main.py:1217` `purged_now: True` | `test_purge_does_not_claim_it_purged` |
| `main.py:1548` 클라이언트가 claim 직접 | `test_route_roles_are_pinned` |
| `apikey.py:5` 관리 API 무인증 | `test_every_route_declares_its_auth` |
| `node/main.py:516` `else: predict_image` | `test_executor_dispatch_covers_vocabulary` |
| `node/main.py:570` `if NODE_ID and …` | `test_node_routes_are_pinned` (#194) |
| `capreq/server.py:142` 빈 첨부 | capreq 단위 + `capreq_demo.sh` |
| … 그 외 넷 | 있음 |

**둘은 없었다.**

```text
grep -rl "assert_media_type\|allowed_media_types\|InputTooLarge" tests/   → 없음
grep -rl "_report_failure" tests/ capreq/tests                           → 없음
```

### ① `inputs.py` — 문지기를 **한 번도 돌려 본 적이 없다**

`apps/core/app/inputs.py` 는 Core 중개 수집(D8′)의 문지기다. 주석 둘이 과거 버그를 적는다:

```text
inputs.py:75   처음에는 「선언이 없으면 검사하지 않는다」였다
inputs.py:111  처음에는 청크를 메모리에 모은 뒤 파일로 썼다. 상한이 256MiB 라 …
```

`test_docs_can_claims`(#200) 가 `"if allowed is None:" in inputs` 를 보지만 그건 **텍스트**다 —
소스를 그대로 두고 동작만 바꾸면 통과한다.

**이 파일은 돌릴 수 있었다.** 의존성이 `hashlib`·`os`·`uuid`·`pathlib` 뿐이고
`psycopg` 는 타입 주석과 `except` 절에만 쓰인다. **돌릴 수 있는데 안 돌리고 있었다.**

`test_input_contract_rejections_actually_run` (11건) — 형식 계약 거절 넷 ·
`store_stream` 다섯(해시·크기 · **소비 중 파일이 자란다** · 상한에서 끊고 지운다 ·
빈 입력 · 중간 예외) · 스텁 위생 둘.

### 내 프로브가 **파이썬 파일 버퍼**를 재고 있었다 (적어 둔다)

「받는 즉시 쓴다」를 8바이트 청크로 재니 `[0, 0, 0, 0, 0]` 이 나왔다.
**결함을 하나 지어낼 뻔했다** — 구현은 이미 흘려 쓰고 있었고, `open(path, "wb")` 의
기본 버퍼가 `close()` 전까지 디스크에 안 내보낸 것이다.

**검사가 구현이 아니라 버퍼를 재고 있었다.** 실제 청크는 `inputs.CHUNK` = **1MiB** 다.
버퍼보다 큰 청크로 바꾸니 그제야 이 검사가 보려는 것을 봤다.

#201 의 「우연히 맞았다」와 같은 부류다 — **숫자가 이상하면 구현부터 의심하지 않는다.**

### ② `node/main.py` — 실측 38건이 적힌 사고인데 핀이 없었다

```text
보고하지 않으면 실패가 lease 만료(60초)로만 드러나고 … 로그에만 쌓이고 증적에는 없다.
실측으로 채널 불일치 38건이 그렇게 쌓였다.
```

`test_node_reports_failure_to_core` (7건) — 정의 · 실패 경로(`/fail`) · **`except` 절에서
실제로 호출** · 보고 실패를 삼킴 · **Core 에 받는 라우트가 있음**.
`fastapi` 가 필요해 `ast` 로 본다 (돌리는 것은 `prod_room`·통합 잡의 몫).

### 뮤테이션 — **11종 전부 물렸다**

입력 계약 여섯: 형식 미선언 통과 · **버퍼링 구현으로 복원** · 상한 판정을 끝까지 읽은 뒤로 ·
거절 시 안 지움 · 빈 입력 수용 · 오류 문구에서 허용 목록 제거.

Node 다섯: `except` 호출 삭제(정의만 남김) · 실패 경로를 완료 경로로 · `try` 제거 ·
Core 라우트 제거 · 함수 통째 삭제.

`run_tests` **623 OK (건너뜀 7)** · `check_submission` **28/28**.
**건너뜀이 7 그대로다** — 내 `psycopg` 스텁이 다른 검사를 끄지 않았다 (#186 이 저지른 사고).

## 「동명 `.ps1`」이 동작은 달랐다 — 2026-09-03

`clean_room.sh` 는 별도 프로젝트와 **다른 포트**(18800/18801)로 스택을 띄운 뒤
`demo.sh` 를 **그대로** 돌린다. `prod_room.sh` 도 같다(18830/18831).
그게 되는 이유는 하나다 — **스크립트가 주소를 환경에서 받기 때문이다.**

주소를 박아 두면 **격리 방을 띄워 놓고도 운영 스택을 친다.** 조용히, 초록으로.

### 실측 — 23 중 2

| | 수 |
|---|---|
| 주소를 쓰는 스크립트 | **23** |
| 환경에서 받는다 | **21** |
| **박아 뒀다** | **2** — `demo.ps1` · `smoke_w1.ps1` |

재현:

```bash
python3 - <<'EOF'
import pathlib, re
ADDR=re.compile(r'(?:127\.0\.0\.1|localhost):(?:800[0-9]|8090)')
SH=re.compile(r'\$\{(?:CORE_URL|NODE_URL|CAPREQ_URL)(?::-)?'); PS=re.compile(r'\$env:(?:CORE_URL|NODE_URL|CAPREQ_URL)')
bad=[p.name for p in sorted(pathlib.Path("scripts").glob("*")) if p.suffix in (".sh",".ps1")
     for t in [p.read_text(encoding="utf-8", errors="replace")]
     if ADDR.search(t) and not (PS if p.suffix==".ps1" else SH).search(t)]
print("박아 둔 스크립트:", bad or "없음")
EOF
```

`.sh` 는 **20/20 전부** 받는다. `.ps1` 셋 중에서는 `proof_ab.ps1` 만 따라갔다.

### 왜 어긋났나 — **고치고 짝을 안 따라갔다**

`CHANGELOG` 에 이 줄이 있다:

```text
- `demo.sh`·`proof_ab.sh`·`pass_rate.sh` 를 `CORE_URL`/`NODE_URL` 로 파라미터화 —
  주소가 박혀 있어
```

**같은 이름의 `.ps1` 짝은 그때 안 따라갔고, 그 뒤로 아무도 못 봤다.**
`README` 는 「**Windows** — 동명 `.ps1`」이라고 적는다 — 동명인데 **동작이 다르다.**

`proof_ab.ps1` 이 이미 쓰는 문법 그대로 두 줄을 맞췄다.

### 지키는 검사 — `test_scripts_take_addresses_from_env` (6건)

목록을 박지 않는다. **주소를 쓰는 스크립트를 훑어** 덮어쓰기 통로가 있는지 본다.
주소를 안 쓰는 것(`sanity.ps1` 은 `docker exec` 만 한다)은 대상이 아니다.

격리 방이 **실제로 그것에 기대고 있는지**도 같이 본다 —
`export CORE_URL`/`NODE_URL` 과 **18xxx 격리 포트**. 방이 기본 포트로 돌아가면
덮을 수 있어도 의미가 없다.

**뮤테이션 6종 전부 물렸다** — `demo.ps1` 되돌리기 · **주소 박은 새 스크립트 투입** ·
`.sh` 짝만 잃기 · 방이 `CORE_URL` 을 안 내보냄 · 방이 격리 포트를 버림 ·
**패턴을 헐겁게 해 전부 통과시키기**.

### 못 쟀다 (숨기지 않는다)

**`.ps1` 을 실제로 돌리지 못했다** — 이 환경에 `pwsh` 가 없다.
고친 두 줄은 같은 저장소 `proof_ab.ps1` 의 문법 그대로다.

전수하면서 확인만 하고 **안 고친 것들** (전부 맞았다):
`operate-node.md` 의 `credential_present` (Node `/health` 에 있다) ·
촬영 런북·원고의 `8001`/`8002`/`8003` ↔ compose 서비스 대응 · `sanity.ps1`·
`demo_violations.ps1` (HTTP 를 안 쓴다). 원고는 **Decision 대기라 손대지 않았다.**

`run_tests` **605 OK (건너뜀 7)** · `check_submission` **28/28**.

## 제품 게이트가 **라우트 스물넷 중 다섯**만 눌러 보고 있었다 — 2026-09-03

`prod_room.sh` 는 강제 모드(`compose.prod.yaml`)를 빈 볼륨에서 e2e 로 증명하는
**제품 수용 게이트**다. 무엇을 실제로 누르는지 세어 봤다.

| | 코드에 있는 것 | `prod_room` 이 누르던 것 |
|---|---|---|
| **공개 GET** | **6** | **1** (`/health`) |
| **인증 GET** | **18** | **4** |

재현:

```bash
python3 - <<'EOF'
import sys, re, pathlib; sys.path.insert(0, "tests")
from test_every_route_declares_its_auth import _routes, _authenticated, PUBLIC
r = _routes()
print("공개 GET", sum(1 for v,p,_n,_c in r if v=="GET" and (v,p) in PUBLIC))
print("인증 GET", sum(1 for v,p,_n,c in r if v=="GET" and _authenticated(c)))
EOF
```

### 왜 이게 구멍인가 — `ast` 는 **응답을 안 본다**

`test_every_route_declares_its_auth` 는 「**인증 헬퍼를 불렀는가**」만 본다.
**강제 모드에서 진짜 401 이 나오는가**를 재는 것은 `prod_room.sh` 뿐이다.
그런데 그것이 손으로 고른 다섯 개만 눌렀다.

반대 방향이 더 나쁘다. `PUBLIC` 주석은 `/v1/capabilities` 를 두고
「제품 입구(capreq)가 **키 없이** 읽어 라우팅한다」고 적는다. **그 전제가 제품
프로파일에서 참인지 아무도 재지 않았다.** 잠기면 입구가 통째로 죽는데도.

**§13(공개 GET 6 전수) · §14(인증 GET 18 무인증 401 전수)** 를 넣었다.

### `000` — 공개 프로브가 **조용히 초록**이 되는 자리

`prod_room.sh` 의 `code()` 는 `curl` 이 실패하면 **`000`** 을 낸다.

- 인증 프로브는 `= 401` 이라 `000` 이 실패로 떨어진다 — 안전했다
- **공개 프로브는 「401 이 아니면 통과」다** — 그대로 썼으면 **Core 가 안 떠 있을 때
  「공개 GET 여섯 개 정상」으로 초록**이었다

이 회차들이 고쳐 온 것과 같은 모양이다 (0건·0행·공허 `any` 를 통과로 세기).
**넣기 전에 잡았다.** 판정을 `scripts/lib/authprobe.sh` 로 빼고
**응답이 아닌 것(`000`·빈 값·비숫자·세 자리 아님)은 먼저 실패**로 못박았다.

`lib/tally.sh` 와 같은 이유로 함수로 뺐다 — `prod_room.sh` 는 Docker 가 있어야 돌지만
**판정은 그냥 돌고**, `tests/test_prod_room_auth_probe.py` 가 `bash` 로 실제로 부른다.

### 지키는 검사 — `test_prod_room_auth_probe` (12건)

목록을 코드에 박지 않는다. **`ast` 로 라우트를 뽑아 `prod_room.sh` 의 `for path in` 과
대조한다** — 라우트가 늘면 스크립트를 같이 고치게 된다.

**뮤테이션 7종 전부 물렸다** — 공개 GET 하나 빼기 · 인증 GET 하나 빼기 ·
판정에서 `000` 통과시키기 · 공개 판정이 `401` 도 통과시키기 ·
**새 인증 GET 라우트를 코드에만 추가** · **§13 절 통째 삭제**(공허한 통과) ·
판정을 인라인으로 되돌리기.

### 못 쟀다 (숨기지 않는다)

**`prod_room.sh` 를 실제로 돌리지 못했다** — `docker info` 실패. 잰 것은
**「무엇을 누르기로 적었는가」와 「그 판정이 옳은가」** 둘이다. 판정 함수는 실제로
불러서 표를 확인했고, 스크립트는 `bash -n` 까지다. 본실행은 Docker 있는 세션(큐 40).

`run_tests` **599 OK (건너뜀 7)** · `check_submission` **28/28**.

## 같은 Core 가 **두 버전**을 말하고 있었다 — 2026-09-03

큐 #5 는 `openapi.yaml` 의 **응답 스키마** 드리프트를 보라고 했다. 재 보니
드리프트 이전의 사실이 나왔고, 옆에서 **다른 드리프트**가 걸렸다.

### 걸린 것 — `info` 는 아무도 안 보고 있었다

| 어디 | 값 |
|---|---|
| `apps/core/openapi.yaml` · `docs/spec/openapi.yaml` | `info.version: 0.3.0` |
| `apps/core/app/main.py:118` `FastAPI(version=…)` | **`0.2.0`** |

같은 Core 인데 `GET /openapi.yaml` 은 `0.3.0`, `GET /openapi.json` 은 `0.2.0` 을 준다.
붙이는 쪽은 어느 쪽을 믿어야 할지 알 수 없다.

`test_openapi_drift` 는 **경로와 메서드**를 못박고 있었다 (#61 · #142). 머리말(`info`)은
범위 밖이었다. `0.3.0` 은 `#61` 때부터 있었으니 그 사이 내내 갈려 있었다.

**앱을 스펙에 맞췄다** (`0.2.0` → `0.3.0`). 스펙 두 사본은 이미 서로 같고
(`test_openapi_drift.test_two_copies_match`) 문서가 정본이다.

### 지키는 검사 — `test_openapi_drift` 에 3건

`test_version_agrees_with_the_app` · `test_title_agrees_with_the_app` ·
`test_info_parser_actually_finds_things`(파서가 눈멀어 `None == None` 으로 통과하는 것 방지).

**뮤테이션 7종 전부 물렸다** — 앱 버전 되돌리기 · YAML 만 올리기 · 제목 바꾸기 ·
`version=` 제거 · YAML `info.version` 삭제 · **호출을 한 줄로 접고 뒤에 미끼 두기** ·
`FastAPI(` 호출 자체 제거.

### 스캐너가 자기 호출 밖을 훑고 있었다 (적어 둔다)

첫 파서는 `^app = FastAPI\((.*?)^\)` 였다. 호출을 **한 줄로 접자** 그 정규식이 파일
뒤쪽의 **다른 `)`** 까지 훑었고, 그런데도 답이 맞아 **뮤테이션이 통과했다**.
「물리지 않는다」가 아니라 **「우연히 맞았다」** 는 쪽이라 더 나빴다.
범위를 **괄호 균형**으로 닫고, 호출 뒤에 미끼 `version=` 을 두는 뮤테이션을 더했다.

### 응답 스키마 — **오늘 0건이다.** 고치지 않았다

| 무엇 | 실측 |
|---|---|
| 문서화된 오퍼레이션 | **45건** |
| `requestBody` 스키마 | 있다 |
| **2xx 응답 스키마** | **0건** — 전부 산문 `description` 뿐 |

재현:

```bash
python3 -c "
import yaml
s=yaml.safe_load(open('apps/core/openapi.yaml',encoding='utf-8'))
ops=[(m,p) for p,o in s['paths'].items() for m in o if m in ('get','post','put','patch','delete')]
sch=[(m,p) for m,p in ops if any((r or {}).get('content',{}).get(ct,{}).get('schema') for c,r in (s['paths'][p][m].get('responses') or {}).items() if str(c).startswith('2') for ct in ((r or {}).get('content') or {}))]
print(f'오퍼레이션 {len(ops)}건 · 2xx 응답 스키마 있는 것 {len(sch)}건')"
```

**드리프트가 아니라 부재다.** 45개 응답 스키마를 **소스 파싱으로 손으로 써 넣는 것**은
하지 않았다 — 그러면 아무도 안 지키는 새 드리프트 면을 하나 더 만드는 것이고,
큐가 「소스 파싱으로는 약하다」고 미리 적어 둔 그대로다. 이건 스펙 **모양**을 정하는
일이라 `inbox-cursor.md` 에 Proposal 로 올린다.

### 못 쟀다 (숨기지 않는다)

실제 스키마 추출(`app.openapi()`)은 **못 했다** — `fastapi`·`pydantic`·`psycopg` 없음 ·
`pip` 없음 · `python3 -m venv` 는 `ensurepip` 가 없어 실패 · `docker info` 실패.
정본은 CI 다.

`run_tests` **587 OK (건너뜀 7)** · `check_submission` **28/28**.

## `README` 가 **틀린 파일**을 가리키고 있었다 — 2026-09-03

측정 숫자(마이그레이션 세대·`acc=`)는 이미 전수했다. 남아 있던 것은 **서술형 주장**이다 —
「이 스크립트에는 기기 주소가 없다」처럼 숫자가 아니라 **문장**이라 아무도 안 보던 쪽.

`README`·`user-guide-ko` 를 전수했다. **어긋난 것은 한 종이다.**

### 무엇이 틀렸나

`README` 는 제품의 대표 주장을 이렇게 적고 있었다:

```text
`scripts/demo.sh` 어디에도 기기 주소가 없다.
```

실물:

```text
scripts/demo.sh:8   node="${NODE_URL:-http://127.0.0.1:8001}"
scripts/demo.sh:13  ccurl -sf "$node/health"
```

**거짓이다.** `demo.sh` 는 준비 단계에서 Node 를 직접 부른다 — 가중치 해시와 `arch` 를
그 기기의 증언에서 뽑기 때문이고, 그건 **운영자 몫이라 정상**이다.
`POST /v1/tasks` 부터는 Core 하고만 말한다 (스크립트 자신의 주석 74–76 행이 그렇게 적는다).

기기 주소가 정말로 한 줄도 없는 것은 **`product_demo.sh`** 쪽이다.

| 스크립트 | Node 주소 참조 | 재현 |
|---|---|---|
| `product_demo.sh` | **0건** | `grep -nE 'NODE_URL\|:800[1-9]' scripts/product_demo.sh` |
| `demo.sh` | **1건** (8행) | 같은 명령 |
| `sanity.sh` · `capreq_demo.sh` | 0건 | 같은 명령 |

**`README` 를 실물에 맞췄다.** 주장을 약하게 만든 것이 아니라 **이름을 옳은 파일로
옮겼다** — 사용자 경로에 기기 주소가 없다는 것은 그대로 참이다.

### 원고 세 줄은 손대지 않았다 — Decision 대기

같은 문장이 `contest-report-draft.md` 두 곳과 `contest-report-form-draft.md` 한 곳에 있다.
원고는 **제출한 산출물**이라 (`test_report_claims` 가 「고쳐 쓰지 않는다」고 적는다)
혼자 고치지 않는다. `inbox-cursor.md` 에 Proposal 로 올렸다.

### 지키는 검사 — `test_docs_can_claims`

**문장을 읽고, 그 문장이 이름을 부른 파일을 실제로 잰다.** 목록을 코드에 박지 않았다.

| 무엇 | 어긋나면 |
|---|---|
| 「어디에도 기기 주소가 없다」의 **대상** | 그 스크립트에 `NODE_URL`·`:8001` 이 있으면 실패 |
| 부르는 스크립트·라우트·강제 플래그·상대 링크 | 없는 것을 부르면 실패 |
| `403` 본문 인용 | Node 코드 문구와 갈리면 실패 |
| 제품 오버레이 넷 | 하나라도 안 뒤집으면 실패 |
| 「번호 고르기는 사진 과목에만」 | allowlist 가 늘면 실패 |
| `demo_violations` 건수 · 위반 종수 | SQL·표 실물과 다르면 실패 |

**뮤테이션 8종 전부 물렸다** — 이름 되돌리기 · `product_demo.sh` 에 주소 넣기 ·
깨진 링크 · allowlist 확장 · 403 문구 변경 · 오버레이 끄기 · `TEST7` 추가 ·
**주장 문장 삭제**(공허한 통과 막기).

### 스캐너 한계 (적어 둔다)

`grep` 은 주석 안의 주소와 진짜 호출을 구분하지 못한다. 그래서 「참조 0건」이라는
**더 센 조건**으로 잡았다 — 주석에라도 주소가 있으면 「어디에도 없다」는 못 쓴다.

`run_tests` **584 OK (건너뜀 7)** · `check_submission` **28/28**.

## 시크릿이 **로그로 나가는 쪽은 아무도 안 봤다** — 2026-09-02

`CLAUDE.md` 보안절이 **「시크릿을 로그·커밋 메시지·출력에 노출하지 않는다」** 고 적는다.
그 규칙을 보는 것은 `check_submission.check_secrets` **하나**인데, 그건
**패키징 대상 파일에 시크릿 값이 박혀 있는가**를 본다.

**런타임에 흘러 나가는 쪽은 아무도 안 봤다** — `logger.info(...)` 나 `echo` 에
키·증서가 실리면 그 값은 **컨테이너 로그·CI 출력·터미널 기록**에 남는다.

**전수했다. 새는 곳은 없다.** 유일하게 키를 찍는 곳은 발급 CLI 하나이고,
그건 코드가 스스로 적고 있다 — 「이번 한 번만 보인다 — 저장은 해시만 된다」.

### 검사를 만들면서 **네 번 틀렸다** (적어 둔다)

이번 항목의 값은 결과보다 **과정**에 있다. 도구가 조용히 눈이 멀 수 있다는 것을
네 번 확인했다:

| # | 무엇을 놓쳤나 | 어떻게 알았나 |
|---|---|---|
| 1 | `out["secret"]` 같은 **첨자 문자열** | 첫 판이 **0건**인데 발급 CLI 는 분명히 키를 찍는다 |
| 2 | 셸 오탐 셋 (파이프로 **파일**에 쓰기 둘 · `$secret_file` **경로** 하나) | 눈으로 확인 |
| 3 | 낱말 목록에 **`cred` 가 없어** `$cred` 를 못 잡음 | **뮤테이션이 안 물렸다** |
| 4 | 줄 첫머리만 봐서 `if …; then echo …` 를 통째로 건너뜀 | **뮤테이션이 또 안 물렸다** |

**「뮤테이션이 안 물린다」를 두 번 다 그냥 넘기지 않았다.**

### 좁힌 자리

- `echo` **뒤쪽만** 본다 — 앞쪽 조건절(`if [ -n "$key" ]`)까지 보면 **마스킹한 출력**을 오탐한다
- `$secret_file`·`key_prefix`·`credential_present` 는 **이름에 시크릿 낱말이 있어도
  값은 시크릿이 아니다** — 따로 뺀다
- 파이프·리다이렉트가 있는 줄은 화면이 아니다

### 남긴 예외 둘 — **근거를 적어야 통과한다**

| 자리 | 왜 |
|---|---|
| `apikey_cli.py` 의 `print` | 키 **발급** CLI. 해시만 저장하므로 이때 안 보여 주면 운영자가 키를 가질 방법이 없다 |
| `run_integration.sh` 의 `$PGPASSWORD` | `url_for()` 는 **함수 반환값**을 `echo` 로 내보내는 셸 관용구다 — 호출자가 전부 `$(url_for …)` 로 받는다. 값도 일회용 postgres 의 것(`capnet`) |

### 무엇으로 쟀나

`tests/test_secrets_never_reach_output.py` **8건.**

**뮤테이션 4종이 물렸다** — Core 로그에 증서 싣기 · 셸이 `$cred` 를 화면에 ·
`prod_room` 의 마스킹 벗기기 · **스캐너 자신의 눈을 멀게 하기**(첨자 무시).
마지막 것이 이 파일의 핵심이다 — **검사가 헛도는 것을 검사가 잡는다.**

## capreq 의 **루프백 전제가 못박혀 있지 않았다** — 2026-09-02

앞의 셋이 **Core**(인증·역할)와 **Node** 를 전수해 못박았다.
**capreq — 제품 입구 — 가 남아 있었다.**

capreq 의 라우트 다섯(`/` · `/api/health` · `/api/capabilities` ·
`/api/tasks/{id}` · `/api/chat`)에는 **인증이 없다.** 그게 맞다 — 운영자가 자기
기계에서 띄우는 도구다. **그 전제가 바로 「루프백에만 뜬다」이다:**

```python
ps.add_argument("--host", default="127.0.0.1")
```

**그 기본값이 조용히 `0.0.0.0` 이 되면** 망에 닿는 누구나 이 프로세스를 통해
Core 를 부를 수 있다 — capreq 는 운영자의 `CAPNET_API_KEY` 를 **헤더에 실어**
보내기 때문이다 (`adapters/capnet.py`). 인증 없는 창구가 **키를 가진 대리인**이 된다.

**오늘은 루프백이다** (`serve` · `gemma` 둘 다). **그런데 그걸 지키는 검사도,
README 의 한 줄도 없었다.**

### 무엇을 고정하나

1. `serve` · `gemma` 의 `--host` 기본값이 **루프백**이다
2. 소스에 `0.0.0.0` 이 **상수로** 적힌 곳이 없다
3. 서버 응답이 **API 키를 담지 않는다** — 키는 헤더로만 나간다
4. 라우트 다섯이 **선언과 정확히 같다** (인증이 없으니 늘 때마다 눈에 띄어야 한다)

**`--host 0.0.0.0` 을 금지하지 않는다.** 일부러 열어야 할 때가 있다 —
막는 것은 **말없이 기본값이 바뀌는 것**이다.

### 어디에 뒀나

**`capreq/tests` 가 아니라 `tests/` 에 뒀다.** 그쪽은 `run_tests.sh` 가 부르지 않고
CI 의 capreq 잡에서만 돈다 (`docs/guide/testing.md` §2). 이건 **보안 기본값**이라
어디서든 돌아야 한다. 의존성이 하나도 없어서(capreq 소스를 **데이터로** 읽는다)
여기 둘 수 있었다.

### 무엇으로 쟀나

`tests/test_capreq_binds_loopback.py` **7건** · `capreq/README.md` 에 전제 한 절.

**뮤테이션 3종이 물렸다** — `serve` 기본값을 `0.0.0.0` 으로(2건) ·
`/api/health` 가 키를 담게(1건) · 선언 없는 새 라우트(1건).

## Node 는 **전수 밖이었다** — 고쳐 놓고 못박지 않은 자리 — 2026-09-02

앞의 둘이 **Core** 라우트 46개를 전수해 못박았다 (인증 · 역할).
**Node 는 그 밖이었다.**

Node 는 라우트가 둘뿐이지만(`/health` · `POST /v1/execute`) 열리면 더 나쁘다.
`execute` 의 머리말이 그렇게 적고 있다:

> 이게 없으면 Node에 네트워크로 닿는 **누구나 추론을 시킬 수 있다.**
> Core의 도메인·티어 FK는 assignment 기록을 막지만 Node 직접 호출은 막지 못한다.

> **닫힌 실패.** NODE_ID 가 없으면 배정 여부를 확인할 수단이 없으므로 실행하지 않는다.
> **이전에는 `if NODE_ID and ...` 여서 NODE_ID 미설정 노드가 무방비였다.**

**그 「이전에는」이 실제로 있었던 버그다. 고쳐 놓고, 그것을 못박은 검사가 없었다.**

### 무엇을 고정하나

1. 모든 Node 라우트가 **가드를 부르거나** `PUBLIC` 에 근거와 함께 적혀 있다
2. `execute` 는 `NODE_ID` 가 없으면 **503** — 닫힌 실패
3. 배정이 없으면 **403** · 그 가드가 **`_run` 보다 먼저** 온다
   (뒤에 있으면 **이미 추론한 다음에** 거절하는 꼴이다)
4. `/health` 는 증서를 **`bool()` 로 감싼 유무만** 내보낸다 — 값도 prefix 도 아니다.
   그렇다고 **유무마저 빼지도 못한다** (운영자가 증서 상태를 못 본다)

### 무엇으로 쟀나

`tests/test_node_routes_are_pinned.py` **11건.** `fastapi` 없이 `ast` 로 구조를 본다.

**뮤테이션 3종이 물렸다:**

| 뮤테이션 | 결과 |
|---|---|
| **옛 버그 복원** — `NODE_ID` 없으면 검사 없이 통과 | **1건 실패** |
| `/health` 가 `bool()` 없이 증서를 그대로 내보낸다 | **1건 실패** |
| 가드 없는 새 라우트(`GET /v1/weights-dump`)를 넣는다 | **1건 실패** |

**Node 를 띄워서 눌러 보지는 않았다** — `fastapi` 가 없다.
`scripts/prod_room.sh` 가 강제 모드에서 실제로 누르지만 **Docker 가 있어야** 돈다.

## 라우트의 **역할이 조용히 내려가도 안 걸렸다** — 2026-09-02

바로 앞 항목(**인증을 거치는가**)은 `_require("admin")` 을 `_require("developer")` 로
바꿔도 **통과한다** — 여전히 인증 헬퍼를 부르기 때문이다.

**그 변이는 이 저장소가 이미 놓친 적이 있다.** `tests/test_arch_registry.py` 가
그 경위를 적고 있다:

> 고정 길이로 자르면 창이 **다음 핸들러까지 넘친다.** 실제로 그래서
> `_require("admin")` 을 `developer` 로 바꾸는 변이를 놓쳤다 — 바로 뒤
> `capabilities_create` 의 `_require("admin")` 이 창 안에 들어와 통과시켰다.

그 뒤로도 **개별 엔드포인트 검사 몇 개**만 역할을 못박는다
(`/v1/arches` · `PATCH /v1/capabilities/{id}`). **나머지 서른 몇 개는 아무도 안 본다.**

### 실측 — 오늘 어긋난 곳은 없다

| 등급 | 수 | 무엇 |
|---|---|---|
| `admin` | **15** | 신원·증서·초대·계약·정책 — **만들거나 지우는 것** |
| `developer` | **14** | Agent 등록·게이트런·운영 조회 |
| `user` | **4** | 제품 경로 — 입력·작업 |
| Node 증서 | **6** | `/v1/internal/…` (역할이 아니라 기기 신원) |
| 초대 토큰 | **1** | `POST /v1/nodes/redeem` |
| 공개 | **6** | 앞 항목의 `PUBLIC` 이 근거와 함께 갖는다 |

### 무엇을 고정하나

1. 라우트 → 등급이 선언과 **정확히 같다** — **내려가도, 올라가도** 걸린다
2. 선언에 유령이 없다 · `_require` 를 쓰는데 분류 안 된 라우트가 없다
3. 한 핸들러가 **서로 다른 역할을 두 번** 요구하지 않는다 (무엇이 참인지 모른다)

**역할이 「맞는지」는 판단하지 않는다.** 그건 정책이고 사람이 정한다 (D24 · read-auth).
여기서 보는 것은 **정해 둔 것에서 말없이 움직이지 않는가** 하나다.

### 무엇으로 쟀나

`tests/test_route_roles_are_pinned.py` **7건.** `fastapi` 없이 돈다.

**뮤테이션 2종이 물렸다** — 증서 발급을 `admin → developer` 로 **내리기**(1건) ·
작업 조회를 `user → developer` 로 **올리기**(1건). **양방향 다 잡는다.**

## 라우트가 **인증 없이 들어와도 아무것도 안 걸렸다** — 2026-09-02

인증 검사가 **엔드포인트마다 임시로** 붙어 있었다 — `test_arch_registry` 가
`POST /v1/arches` 를, `test_capability_patch_wiring` 이 `PATCH /v1/capabilities/{id}` 를
본다. **새 라우트를 인증 없이 넣으면 아무것도 안 걸린다.**

`scripts/prod_room.sh` 가 몇 개를 실제로 눌러 보지만 **Docker 가 있어야** 돌고,
보는 것도 **손으로 고른 여섯 개**다.

### 실측 — 오늘은 새는 곳이 없다

`ast` 로 Core 라우트를 전수했다:

| | 수 |
|---|---|
| Core 라우트 | **46** |
| 인증 헬퍼를 부른다 | **40** |
| 공개 | **6** — 전부 `GET` |

공개 여섯: `/` · `/health` · `/openapi.yaml` · `GET /v1/capabilities`(둘) ·
`/v1/datasets`. STATE 가 적은 「공개는 `/health`·카탈로그·allowlist만」
(2026-08-14 · D24 read-auth)과 **정확히 일치**한다.

> **처음 훑었을 때 11개가 「인증 없음」으로 나왔다.** 스캐너가
> `_assert_node_matches` 를 몰라서였다 — `/v1/internal/…` 다섯은 전부 그걸로
> Node 증서를 보고 URL 의 `node_id` 까지 대조한다 (SD-010).
> **도구를 못 믿고 코드를 열어 확인했다.**

### 무엇을 고정하나

1. 모든 라우트가 **인증 헬퍼를 부르거나** `PUBLIC` 에 **근거와 함께** 적혀 있다
2. **쓰기(POST·PUT·PATCH·DELETE)는 공개가 하나도 없다**
3. `PUBLIC` 에 유령(실재하지 않는 라우트)이 없다

**역할의 높낮이는 안 본다** (`admin` 인지 `developer` 인지) — 그건 엔드포인트마다
다르고 개별 검사가 이미 있다. 여기서 보는 것은 **인증을 거치기는 하는가** 하나다.

### 무엇으로 쟀나

`tests/test_every_route_declares_its_auth.py` **7건.** `fastapi` 없이 돈다.

**뮤테이션 2종이 물렸다** — 인증 없는 새 조회 라우트를 넣기(1건) ·
기존 라우트에서 `_require` 를 떼기(1건).

## **실행기가 없는 모달리티는 이미지 분류기로 떨어졌다** — 2026-09-02

[#189](https://github.com/gncorpseo-commits/capnet/pull/189)가 **입력 선택**의
불안전한 기본값을 뒤집었다. **실행기 선택에도 같은 것이 남아 있었다:**

```python
elif modality in ("text", "text_embed"):
    ...
else:
    label, confidence = predict_image(...)      # ← 이름 없는 것은 전부 여기로
```

**기본값이 「이미지 분류기」였다.** 실측하면 오늘 `else` 로 가는 것은 `image` 하나뿐이라
맞다:

```text
실행기 분기가 이름으로 잡는 모달리티:
  image_embed, series, table_extract, text, text_embed,
  text_extract, text_ner, text_pii, text_rank
어휘 전체:  위 아홉 + image
이름 없이 else 로 가는 것:  ['image']
```

**문제는 자라는 방향이다.** `ARCH_MODALITY` 에 새 모달리티를 더하고 위에 분기를
안 만들면 그 능력이 **조용히 이미지 분류기로 돈다.** arch 는 등록돼 있으니
`build_model` 도 통과한다 — 「무엇으로 돌았나」가 증적과 갈라진다.

### 바뀐 것

`else` 를 **`elif modality == "image"`** 로 이름 붙이고, 남는 `else` 는 **501** 로
「실행기가 이 Node 에 없다」고 말한다.

**동작 변경 0.** `arch=None` 인 legacy Agent 는 `_modality_of` 가 `"image"` 로
떨어뜨리므로 이름 붙은 분기로 간다 — 종전 그대로다.

### 무엇으로 쟀나

`tests/test_executor_dispatch_covers_vocabulary.py` **6건.** `ARCH_MODALITY` 와
실행기 분기를 **양쪽 다 파싱해 집합으로 대조한다** (`torch`·`fastapi` 없이 돈다).
분기가 부르는 `app.infer*` 모듈이 실재하는지도 본다.

**뮤테이션 2종이 물렸다** — 남는 `else` 를 다시 `predict_image` 로(1건) ·
어휘에 `audio` 만 더하고 분기를 안 만들기(1건).

> **이 검사가 처음에 자기 주석에 걸렸다.** 「예전에는 `predict_image` 로
> 떨어졌다」고 적은 **설명 문단**이 위반으로 잡혔다. `_srcguard.code_only` 로
> 주석을 빼서 고쳤다 — 이 저장소에서 **여섯 번째** 같은 사고다.
> **설명을 지워야 통과하는 검사를 만들지 않는다.**

## **안 푼 머지가 초록이었다** — 충돌 마커를 문서에서 본다 — 2026-09-02

**이번 세션에 실측했다.** 머지 프로브가 `CHANGELOG.md` 에서 충돌했고,
그 **마커가 그대로 남은 트리**에서 전체 검증을 돌렸더니:

```text
Ran 518 tests · OK (skipped=7)
28/28 통과
```

**아무것도 안 걸렸다.** `<<<<<<< HEAD` · `=======` · `>>>>>>> origin/…` 세 줄이
3·73·184 행에 그대로 있는데도.

### 왜 기존 검사가 못 잡았나

`test_changelog_integrity` 는 **바로 이 사고를 보라고** 만든 검사다 (2026-09-01 ·
두 번째 `# Changelog` 헤더와 159줄 중복). 그런데 보는 것은 **헤더 개수·제목 중복** —
**잘못 푼 머지**다. **안 푼 머지**는 그 그물을 빠져나간다. 같은 사고의 다른 얼굴이다.

### 왜 문서만 보나

**코드는 이미 시끄럽다** — 파이썬에 마커가 남으면 `SyntaxError` 로 임포트가 죽고,
셸은 `bash -n` 이 잡는다. **조용한 것은 마크다운뿐이다.** 그래서 머지가 자주
충돌하는 셋만 본다: `CHANGELOG.md` · `STATE.md` · `docs/bridge/inbox-*.md`.

**리포 전체를 훑지 않는다.** 「X 를 쓰지 않는다」를 텍스트로 검사했다가 **X 를 설명한
문단이 걸린** 사고가 다섯 번 났다 (`tests/_srcguard.py`). 이 검사 파일 자신도
마커를 설명하므로 **대상에서 뺀다.**

### 오탐을 막은 자리

`=======` **단독 줄은 마크다운 setext 제목 밑줄**일 수 있다. 그래서 혼자서는 안 센다 —
여는 마커(`<<<<<<< `)가 같은 파일에 있을 때만 함께 센다. diff3 방식의 `||||||| `도 본다.

### 무엇으로 쟀나

`tests/test_no_conflict_markers.py` **7건.** 탐지기 자체를 가짜 텍스트로 시험한다
(파일을 더럽히지 않는다) — 진짜 충돌 · diff3 · setext 밑줄 · 깨끗한 글.

**실제로 재현해서 확인했다** — 아까 초록으로 지나간 그 세 줄을 다시 넣자
`FAIL: test_no_markers_left (doc='CHANGELOG.md')` 로 걸렸고, 빼자 다시 통과했다.

## **모르는 모달리티는 데모 이미지로 떨어졌다** — 기본값을 뒤집는다 — 2026-09-02

Node 가 「Core 중개 입력이 없을 때」를 이렇게 갈랐다:

```python
elif modality in (
    "text", "text_embed", "series", "table_extract", "text_ner", "text_extract",
    "text_rank", "text_pii",
):
    raise HTTPException(400, "text 실행에는 Core 가 중개한 입력이 필요하다")
else:
    cid = _case_id(input_ref)          # ← 로컬 골든셋(EuroSAT 이미지)으로 떨어진다
```

**포함식이라 기본값이 「골든 폴백」이었다.** 목록에 없으면 데모 데이터로 돈다.

### 오늘은 맞다 — 문제는 자라는 방향이다

실측: `ARCH_MODALITY` 의 값 **10종** 중 목록에 없는 것은 `image` · `image_embed` 둘뿐이라
지금은 정확히 맞다.

**새는 길은 하나다** — `ARCH_MODALITY` 에 새 모달리티를 더하고 **이 목록을 안 고치면**,
그 능력은 **사용자 입력을 요구하는 대신 로컬 골든 이미지로 떨어진다.**

> **처음에 「길이 둘」이라고 적었다가 정정했다.** 「arch 가 `ARCH_MODALITY` 에 없다」는
> 쪽도 `_modality_of` 가 `"image"` 로 떨어뜨리지만, 그 뒤 `build_model` 이
> `unknown arch …` 로 던지고 `_run` 이 **422** 로 바꾼다. 게다가
> `tests/test_text_modality` 가 `ARCH_REGISTRY == ARCH_MODALITY` 를 **이미 못박고**
> 있다 (실측: 오늘 양쪽 11키 동일). **조용한 오답이 아니라 시끄러운 실패다** —
> 고친 것을 크게 말하지 않는다.

[#154](https://github.com/gncorpseo-commits/capnet/pull/154)(빈 첨부 → 데모 데이터가
대신 돌았다)와 같은 모양이고, 손으로 적은 목록이 카탈로그를 못 따라간
[#171](https://github.com/gncorpseo-commits/capnet/pull/171)과 같은 자리다.

### 바뀐 것 — **기본값을 뒤집었다**

`apps/node/app/modality.py` 신설. **폴백을 가진 쪽**만 적는다:

```python
GOLDEN_FALLBACK_MODALITIES = frozenset({"image", "image_embed"})

def requires_core_input(modality: str) -> bool:
    return modality not in GOLDEN_FALLBACK_MODALITIES
```

모르는 모달리티는 **거절**이 기본이다. **동작 변경 0** — 오늘 어휘 10종의 판정은
전부 그대로다 (검사가 열 종을 하나씩 확인한다).

**왜 별 모듈인가.** `main.py` 는 `fastapi` 를, `tiny_cnn.py` 는 `torch` 를 import 한다 —
둘 다 의존성 없는 단위 검사에서 불러올 수 없다. 이 판단만 표준 라이브러리로 떼면
검사가 **실제로 호출**할 수 있다.

### 무엇으로 쟀나

`tests/test_modality_fallback.py` **10건.** `app/modality.py` 를 **실제로 불러
호출한다.** `ARCH_MODALITY` 는 정규식으로 읽는다 (`test_pass_rate_script` 와 같은 이유).

**뮤테이션 3종이 물렸다** — 판정을 옛 포함식으로 되돌리기(**5건**) ·
폴백 집합에 이미지 아닌 것 넣기(2건) · 어휘에 없는 유령 넣기(2건).

### 기존 검사 넷을 **지우지 않고 옮겼다**

`test_safety_pii` · `test_text_rank` · `test_series_modality` · `test_text_modality` 가
**옛 포함식의 문자열**을 못박고 있어서 처음에 넷 다 실패했다.

**불변식은 옳다 — 보는 자리만 낡았다.** 그래서 지우지 않고 같은 불변식을 새 기제에
물렸다 (「이 모달리티는 폴백 목록에 없다」). **옮긴 뒤에도 물리는지 따로 확인했다** —
폴백 집합에 네 이름을 넣자 넷 다 다시 실패했다.
## 방 검사 둘도 **0건이면 「전부 재현된다」** 였다 — 2026-09-02

`clean_room.sh` · `prod_room.sh` 가 이렇게 끝났다:

```bash
printf '===== 결과: 통과 %d · 실패 %d =====\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
echo "…에서 전부 재현된다."
```

`pass=0 · fail=0` 이면 `fail -eq 0` 이 참이라 **「전부 재현된다」를 찍고 `exit 0`** 한다.

이 회차가 고쳐 온 것의 **셋째 사례**다 — [#180](https://github.com/gncorpseo-commits/capnet/pull/180)
(누출 검사가 0건을 보고 「깨끗하다」) · [#181](https://github.com/gncorpseo-commits/capnet/pull/181)
(통합 러너가 0개를 보고 「통과 0 · 실패 0」).

**#180·#181 보다 가볍다. 과장하지 않는다.** 두 스크립트의 `chk`/`step` 호출은
**인라인 하드코딩**이라 0건이 되려면 스무 줄 넘게 지워야 한다 — glob 이 빗나가는
#181 과는 다르다. 다만 `set -e` 가 없는 `prod_room` 은 앞 단계가 죽어도 계속 가므로
「빠져나갔는데 초록」이 아주 먼 이야기는 아니다.

### 왜 함수로 뺐나 — **검사할 수 있게**

두 스크립트는 **Docker 가 있어야 끝까지 돈다.** 판정이 맨 끝에 인라인으로 있으면
그 줄을 **검사할 방법이 없다** (이 세션에는 Docker 가 없다).

판정 한 줄을 `scripts/lib/tally.sh` 의 `tally_verdict` 로 빼면 **그냥 부를 수 있다.**
두 스크립트가 같은 꼬리를 복사해 갖고 있던 것도 함께 없앴다.

```text
tally_verdict 0 0 → exit 1 · 「0건은 통과가 아니다」  (전에는 exit 0 + 성공 문구)
tally_verdict 3 0 → exit 0 · 성공 문구
tally_verdict 2 1 → exit 1 · 성공 문구 없음
```

### 무엇으로 쟀나

`tests/test_room_tally.py` **8건.** 함수를 `bash -c` 로 **실제로 부른다** — Docker 불필요.
두 스크립트가 그것을 쓰는지, 옛 인라인 판정이 남지 않았는지, `bash -n` 이 통과하는지도 본다
(`source` 를 잘못 넣으면 **Docker 가 있는 곳에서만** 터진다).

**뮤테이션 2종이 물렸다** — 0건 바닥을 `if false` 로 죽이니 **2건 실패** ·
`clean_room` 을 옛 인라인 판정으로 되돌리니 **1건 실패**.

**두 스크립트를 끝까지 돌려 보지는 못했다** (Docker 없음). 바꾼 것은 꼬리 두 줄이고,
`bash -n` 과 함수 단위 실행으로 덮었다. **「지난번 됐으니 된다」로 적지 않는다.**

## **깨진 계약이 「Node 는 칸 이름을 주장 못 한다」를 스스로 껐다** — 2026-09-02

`complete.py` 는 Node 가 보고한 출력 칸이 계약과 **정확히 같아야** 받는다:

```python
required = set(_required_keys(conn, assignment_id))
given = set(output)
if required and given != required:      # ← required 가 비면 통째로 꺼진다
    raise OutputKeysMismatch(...)
```

그리고 `_required_keys` 는 **「선언 안 함」과 「선언이 깨졌다」를 구분하지 않았다:**

```python
if isinstance(required, list) and all(isinstance(k, str) for k in required):
    return required
return []                                # ← ["label", 5] 도 여기로 떨어졌다
```

실측 (스텁 커넥션으로 실제 함수를 돌려서):

| `output_schema.required` | 옛 `_required_keys` | 옛 `_output_key` |
|---|---|---|
| `["label"]` | `["label"]` | `"label"` |
| **`["label", 5]`** | **`[]`** | **`"vector"`** |
| **`"label"`** (문자열) | **`[]`** | **`"vector"`** |

계약 하나가 깨져 있으면 **두 가지가 동시에 조용히** 일어났다:

1. 칸 검사가 통째로 꺼져 **Node 가 아무 칸이나 보고해도 그대로 증적에 적혔다**
2. `_output_key` 가 계약과 무관한 `"vector"` 로 떨어져 **「게이트가 검증한 출력」과
   「증적에 남는 출력」이 갈라졌다** — 바로 그 갈라짐을 막으려고 있는 코드가,
   계약이 깨지면 **스스로 열렸다**

**오늘 새고 있지는 않다.** 등록된 능력 10종은 전부 `required` 를 문자열 목록으로
선언한다 (데모 9 + seed 1). **나기 전에 막는다** — #169 와 같은 자리다.

### 바뀐 것

- **깨진 `required` → `BrokenOutputContract`** (`OutputKeysMismatch` 의 하위형이라
  `main.py` 가 이미 잡아 **422**). 배선 변경 0
- **선언이 아예 없는 것**(`None`·`[]`)은 **동작 그대로** — 다만
  `logger.warning("output keys unchecked …")` 로 **안 봤다는 사실을 남긴다**.
  「required 가 없으면 거절할지」는 정책이라 브리지 Decision 으로 올린다

### 무엇으로 쟀나

`tests/test_broken_contract_does_not_disable_check.py` **13건.** DB 없이 돈다 —
`complete.py` 의 `psycopg` 는 주석에만 쓰이므로 빈 모듈로 세우고, 세 질의를
SQL 본문으로 갈라 주는 가짜 커넥션으로 **`complete_assignment` 를 그대로 돌린다.**

**뮤테이션 3종이 물렸다** — 옛 `_required_keys` 복귀(**14건 실패**) ·
`BrokenOutputContract` 상속 끊기(1건) · 로그 분기 `if False`(1건).

> **세 번째는 처음에 안 물렸다.** 그때 검사는 `_required_keys` 만 보고 있었고
> 로그 분기는 밖이었다. **「뮤테이션이 안 물린다」를 그냥 넘기지 않고** 가짜 커넥션을
> 만들어 `complete_assignment` 까지 덮었다.

> **내 검사가 다른 검사를 껐다 (같은 회차 · 같은 모양).** 처음에는
> `sys.modules["psycopg"]` 에 스텁을 **남긴 채** 끝냈다. 그러자 psycopg 가 진짜로
> 필요한 검사들이 그 스텁을 집어 **`run_tests` 가 skip 7 → 2 로 줄고 5건이 에러**가 났다.
> 넣었던 것만 되돌리도록 고쳤다. **이번 회차가 고치는 것과 정확히 같은 실수를
> 내가 검사에서 했다** — 적어 둔다.

## 데이터셋 목록을 **못 받으면 화면이 하나 지어냈다** — 2026-09-02

`call.html` 의 `loadOptions()` 가 이랬다:

```js
try {
  const caps = await api("/v1/capabilities");
  …
} catch (e) { $("c-cap").innerHTML = `<option>${esc(e.message)}</option>`; }   // 에러를 올린다
try {
  const ds = await api("/v1/datasets");
  $("c-dataset").innerHTML = (ds.items || []).map(…).join("");
} catch { $("c-dataset").innerHTML = '<option>eurosat-rgb</option>'; }          // 지어낸다
```

**같은 함수 안에서 규약이 갈려 있었다.** 능력 목록은 못 받으면 에러를 보여 주는데,
데이터셋은 **서버가 준 적 없는 `eurosat-rgb`** 를 서버가 준 것처럼 보여 줬다.

빈 목록도 마찬가지였다 — `[].map().join("")` 은 `""` 라 `<select>` 가 통째로 비는데,
바로 위 `c-cap` 에는 `|| '(없음)'` 이 있었다.

**심각도는 낮다.** `/v1/datasets` 는 무인증이라 서버가 죽으면 위 줄이 이미 빨갛다.
그래도 고친다 — 이번 회차가 고친 것이 전부 **「못 했는데 됐다고 말한다」** 이고,
이건 그 계열의 마지막 한 자리였다.

### 바뀐 것

실패하면 **에러 메시지**를, 빈 목록이면 **`(없음)`** 을 보여 준다 — `c-cap` 과 같은 규약.

### 무엇으로 쟀나

`tests/test_ui_invariants.py` **2건 추가** (총 10건).
**`catch` 블록 안에 도메인 값 리터럴이 있는지**를 본다 — 중괄호 균형으로 블록을
잘라 내고 `eurosat-rgb`·`image.classify` 같은 값을 찾는다. 에러 메시지나 `(없음)` 은
서버 데이터가 아니라 대상이 아니다.

`test_catch_probe_actually_sees_catches` 를 함께 넣었다 — **`catch` 를 하나도 못 찾으면
위 검사가 0건을 훑고 통과한다.** 이번 회차가 고친 것과 같은 함정이라 검사 자신에게도 적용했다.

**뮤테이션이 물렸다** — 옛 폴백을 되돌리자 실패했다.

## purge 가 **한 행도 안 바꾸고 「지웠다」** 고 답했다 — 2026-09-02

`POST /v1/inputs/{id}/purge` 가 이랬다:

```python
marked = mark_purged(conn, input_id)      # STORED 인 것만 → 0행이면 None
removed = purge_blob(input_id)
return {**(marked or row), "purged_now": True, "file_removed": removed}
```

`mark_purged` 가 `None` 이어도 — **UPDATE 가 한 행도 안 바꿔도** — `purged_now: True`
였다. 더 나쁜 것은 `marked or row` 다. 위에서 읽어 둔 **옛 행**을 함께 실어 보내
응답이 **자기모순**이 됐다:

```json
{"storage_state": "STORED", "bytes_purged_at": null, "purged_now": true}
```

### 가상의 경우가 아니다

`storage_state` 는 `STORED` · `PURGED` 둘뿐이고(0011) 위에 `PURGED` 조기 반환이 있다.
그러니 `marked is None` 은 **경쟁**뿐이다 — 읽은 뒤 UPDATE 전에 다른 쪽이 지웠다.

그 「다른 쪽」이 **같은 프로세스의 배경 스레드**다. `_gc_loop` 가 주기적으로
`task_input_purge_due` 를 훑어 같은 `mark_purged` 를 부른다.

**바이트는 어느 쪽이든 지워지므로 데이터 피해는 없다.** 거짓말한 것은 **응답**이다.

### 바뀐 것

0행이면 사실을 **다시 읽어** `purged_now: False` 로 돌려준다.
`storage_state` 도 그때의 진짜 값(`PURGED`)이 나간다. 로그도 남긴다.
성공 응답은 이제 `marked` **하나만** 펼친다 — 대체값이 없다.

### 무엇으로 쟀나

`tests/test_purge_does_not_claim_it_purged.py` **3건.** `app.main` 은 fastapi 를
import 하므로 의존성 없는 환경에서 **모듈을 못 불러온다** — 그래서 `ast` 로 본다
(표준 라이브러리로 파싱된다).

**뮤테이션 2종이 물렸다** — 경쟁 분기를 `if False` 로 죽이니 **1건 실패**,
`marked or row` 를 되돌리니 **2건 실패**.

DB 를 띄우는 쪽은 `tests/integration/check_input_purge.py` 가 이미 `mark_purged` 의
「STORED 만 바꾼다」를 고정하고 있다 (CI 의 migrate 잡).

## 통합 검사 **0개도 초록**이었다 — 2026-09-02

`scripts/run_integration.sh` 는 `tests/integration/check_*.py` 를 glob 으로 집는데,
**하나도 못 찾았을 때를 세지 않았다.** 루프가 안 돌고 끝에서 이렇게 끝난다:

```text
  서버 127.0.0.1:5432 · 검사 0개
  …
===== 통합 검사: 통과 0 · 실패 0 =====
검사끼리 상태를 공유하지 않는다 — 순서를 바꿔도 같은 결과다.
exit=0
```

**CI 의 `integration` 잡이 이 스크립트를 그대로 부른다.** glob 이 한 번 빗나가면
(디렉터리 이름 변경 · 패턴 변경 · 체크아웃 누락) **통합 검사 0개로 CI 가 초록**이 된다.

[#169](https://github.com/gncorpseo-commits/capnet/pull/169) 는 **「파일 하나가
패턴을 벗어나면 조용히 안 돈다」** 를 막았다. 그런데 **전부가 안 잡히는 경우**는
그 검사 밖이었다 — `test_probe_actually_finds_things` 는 러너가 아니라 **파이썬
쪽에서** glob 을 세므로, 러너 자신이 0건일 때 어떻게 끝내는지는 아무도 안 봤다.

`find` 는 디렉터리가 없어도 **프로세스 치환 안이라 `set -e` 에 안 걸린다.**

### 바뀐 것

`checks` 가 비면 `psql` 보다 **먼저** 멈춘다 (`exit 1`).
「0건은 통과가 아니다」와 경로·패턴을 찍는다.

### 무엇으로 쟀나

`tests/test_integration_runner.py` **3건 추가** (총 6건). 임시 트리에 러너를 복사하고
**실제로 돌린다** — postgres 없이 돈다는 것 자체가 요구사항이라 그것도 단언한다
(`test_guard_runs_before_psql`). 가드가 늦으면 「postgres 가 없어서」로 실패가 뭉개진다.

**뮤테이션이 물렸다** — 가드를 `if false` 로 죽이자 **3건이 실패**했고, 그 출력이
고치기 전 동작을 그대로 보여 줬다: `검사 0개` → psql 로 진행.

## 누출 검사가 **아무것도 안 보고 「깨끗하다」** 고 말했다 — 2026-09-02

`scripts/check_golden_leakage.py` 는 없는 매니페스트를 `(건너뜀 - 없음)` 한 줄로 넘기고
**종료 코드에 반영하지 않았다.** 그래서 넷이 다 없어도 이렇게 끝났다:

```text
$ python3 scripts/check_golden_leakage.py --manifest NO_SUCH.json
  (건너뜀 - 없음) NO_SUCH.json

겹침 없음. 골든셋은 홀드아웃이다.
exit=0
```

**가정이 아니다.** 기본 매니페스트 넷 중 **셋은 `data/` 아래라 저장소에 추적되지 않는다**
(용량). 즉 **신선한 클론에서 시키는 대로 돌리면 늘 저 자리**였고, 하필 그 셋 중 하나가
`data/golden-n300-holdout/…` 이다. 결과보고서는 이 도구로 **「겹침 0/300 검증」** 을
주장한다 — 따라 돌린 사람은 **40건만 본 초록**을 받고 300건을 확인했다고 믿게 된다.

### 무엇을 바꿨나

| 상황 | 전 | 후 |
|---|---|---|
| 본 것이 **0건** | `0` · 「겹침 없음」 | **`1`** · 「답할 수 없다」 |
| **일부만** 봤다 | `0` · 「겹침 없음」 | **`3`** · 못 본 목록을 이름으로 찍는다 |
| 케이스 0건 매니페스트 | `clean` 로 셈 | **못 본 것**으로 셈 |
| `zip_path` 없는 케이스 | 경고만 · 결과 무영향 | **못 본 것**으로 셈 |
| 겹침 발견 | `2` | `2` (그대로) |
| 전부 보고 안 겹침 | `0` | `0` — 다만 **몇 종을 봤는지 같이 찍는다** |

`data/` 를 만든 이 환경에서 기본 실행은 그대로 `2` 다 (n300·n300-train 은 **일부러**
학습셋이다). 신선한 클론은 이제 `3` — 「40건은 깨끗하다, 300건은 못 봤다」.

### 무엇으로 쟀나

`tests/test_golden_leakage_honesty.py` **7건.** EuroSAT zip 없이 도는 순수 함수
`run_manifests` 를 직접 부른다. **뮤테이션 3종이 전부 물렸다** — 없는 파일 무시 /
`zip_path` 없는 케이스 무시 / 옛 문구 복귀. 셋 다 검사가 잡았다.

이 도구는 `run_tests.sh` 에도 CI 에도 **없다.** EuroSAT zip(94MB)이 저장소에 없어
CI 가 돌릴 수 없기 때문이다 — 그래서 **정직성 쪽만** 단위 검사로 고정했다.

## 검사가 조용히 줄어 있었다 — 네 건을 몰아 적는다 (Wave U·V·W·X) — 2026-09-02

**동작 변경 0.** 네 PR 모두 코드를 안 고쳤다 — 검사·문서·도구만이다.
`CHANGELOG` 선두를 한 PR 만 건드리도록 갈라 두느라 U·V·W·X 는 항목 없이 머지됐다
(#136 교훈). **여기서 한 건으로 몰아 적는다.**

### 관통하는 사고 하나

넷 다 같은 자리를 가리킨다 — **초록으로 끝나는데 실은 안 보고 있었다.**

| PR | 무엇이 안 보이고 있었나 |
|---|---|
| [#142](https://github.com/gncorpseo-commits/capnet/pull/142) | 이미 문서에 있는 **경로에 메서드를 더하면** openapi 드리프트 검사가 조용했다 |
| [#143](https://github.com/gncorpseo-commits/capnet/pull/143) | **검증 방법을 적은 문서**가 CI 보다 덜 적어, 그대로 따라하면 3건이 실패했다 |
| [#144](https://github.com/gncorpseo-commits/capnet/pull/144) | `node` 가 사라져 **6건이 skip** 됐는데 `OK (skipped=6)` 은 초록이다 |
| [#145](https://github.com/gncorpseo-commits/capnet/pull/145) | **제품 입구**에 종단 검사가 없어, 첨부가 버려져도 전부 통과였다 |

### #142 — openapi 드리프트를 **메서드 수준**으로

정규식이 HTTP 메서드를 잡아 놓고 `routes()` 가 버렸다. 그래서 Wave I 의
`PATCH /v1/capabilities/{id}` 는 이 검사에 안 걸렸고 문서에는 **손으로** 넣었다.

`(메서드, 경로)` 쌍으로 올렸다. **스펙 자체는 안 고쳤다** — 경로 드리프트가 이미 0
이었고(라우트 46 · 공개 38 · openapi 39 · 양쪽 차집합 없음), `openapi.yaml` 두 사본은
한 글자도 안 바뀌었다.

무엇으로 쟀나: 뮤테이션 2종 — 문서에 있는 경로에 `@app.delete` 추가 / 라우트 없는
`delete:` 를 문서에 추가. 둘 다 새 검사가 걸렀고, **기존 검사는 첫 번째를 통과시켰다.**

### #143 — `testing.md` ↔ CI

이 문서는 capreq 테스트 실행법으로 오래 **`httpx` 하나**만 적었다. 서버 경로(첨부) 검사가
들어오면서 CI 는 `fastapi`·`python-multipart` 까지 깔게 됐는데 문서는 그대로였다.

문서대로 깔고 돌리면 첨부 검사 3건이 실패한다. 메시지가
`The python-multipart library must be installed` 이라 **제품 결함처럼 보인다** —
이번에 실제로 그렇게 오해했다가 `capreq/pyproject.toml` 의 `server` extra 를 보고 되짚었다.

`tests/test_testing_doc.py` 가 CI 를 정본으로 잇는다. 패키지 **이름만** 비교한다 —
버전 핀까지 보면 핀 올릴 때마다 문서를 고쳐야 해서 아무도 안 지킨다.

**§3 「지금 있는 것」 표도 걷어냈다.** 테스트 파일 둘만 적혀 있었는데 그 사이 `tests/` 는
스물아홉이 됐다. 개수를 강제하는 검사를 붙이지 않고 **목록을 지웠다** — 파일이 늘 때마다
문서를 고치게 만드는 검사는 `test_doc_counts` 가 이미 금지한다.

### #144 — skip 사유를 허가제로

세션 도중 환경이 바뀌어(python 3.13 → 3.14 · `node` 없음 · `httpx`/`fastapi` 없음)
capreq 스위트가 **68 → 50 ran / 6 skipped** 로 줄어 있었다. 빠진 6건이 `chat.html` 을
실제로 실행하는 프로브 — 「문자열 검사는 반쯤 지운 렌더러를 통과시킨다」를 재현해 보고
넣은, 이 저장소에서 가장 값나가는 클라이언트 검사다. 아무 경고도 없었다.

`tests/test_skip_reasons.py` 가 사유 문자열을 허가 목록으로 만든다. `ast` 로 **호출**만
본다 — 설명 문단에 적은 낱말이 걸리면 안 된다(`_srcguard` 사고 5건).

**개수는 못박지 않았다.** 몇 건이 건너뛰어지는지는 환경마다 다른 것이 정상이고,
못박으면 psycopg 가 있는 환경에서 거짓 실패가 난다.

### #145 — 제품 입구 종단 (`scripts/capreq_demo.sh`)

다른 `*_demo.sh` 는 전부 **Core 를 직접** 부른다. 사람이 쓰는 입구는 `capreq` 인데
그 경로에는 종단 검사가 없었다. 없어서 **첨부가 한 번도 동작하지 않았다**(`7936a0f`) —
단위 검사도 `chat_flow_probe.js` 도 통과하고 있었다. `fetch` 를 스텁으로 막기 때문이다.

문장 + 첨부 → 라우팅 → **`input_id`**(첨부가 Core 를 거쳤다는 유일한 증거 · D8′) →
작업 → 완주 → 증적·경계까지 밟는다.

**종료 코드가 배선과 라우팅을 가른다** — 1 = 배선 끊김(고칠 버그) · 2 = 라우팅 빗나감.
로컬 LLM 은 매번 같지 않아 같이 세면 검사가 흔들린다. **라우팅 정확도는 여기서 재지
않는다** (`route_bench` 가 홀드아웃으로 잰다).

무엇으로 쟀나: 살아 있는 스택 + `qwen2.5:3b` · 2026-09-01 · 1회.
`text.extract@1` 로 라우팅돼 `COMPLETED` · assignment SUCCEEDED · 경계 team→team · M≤M.
같은 문장이 앞선 시도에서는 `text.ner` 로 갔다 — **알려진 라우팅 흔들림**이고 스크립트가
그것을 실패로 세지 않는 것이 의도다.

### 도구를 되살린 것도 적어 둔다

`node` 를 유저스페이스로 복구(`~/.local/node`)하고 `capreq[server]` 를 제대로 깔아
capreq 를 **68 · 건너뜀 0** 으로 되돌렸다. 중간에 난 실패 3건은 **제품 결함이 아니라
설치 누락**이었다 — 그렇게 오해했던 것을 함께 적는다.

### 검증

`run_tests` 392 → **411** OK · capreq **68**(건너뜀 0) · `check_submission` **29/29** ·
`check_input_purge` **17/17** · `product_demo`·`pii_demo`·`demo_violations`·`capreq_demo`
**exit 0**. 일곱 PR 을 `main` 위에 전부 머지한 워크트리에서 쟀다.

## 픽스처가 뒤처져 `safety.pii` 렌더러가 검사 밖이었다 (Wave T) — 2026-09-01

**이번 달 다섯 번째 「손으로 센 목록」.** 코드 0 · 새 의존성 0.

### 무엇이 뒤처져 있었나

`capreq/tests/test_chat_html_unit.py` 의 `EVERY_SHAPE` 는 **능력이 내는 결과 칸을 한데 모은
픽스처**다. Wave L 이 `safety.pii` 를 더하면서 `results.py` 와 `chat.html` 은 고쳤는데
**이 픽스처는 안 고쳤다.**

결과: `test_every_summary_key_has_a_renderer` 가 **`pii` 를 아예 보지 않았다** —
`result.pii` 를 **통째로 지워도 통과**했다.

### 그때 진단이 절반만 맞았다

Wave M 에서 이 파일의 한계를 「부분 문자열 검사라 **반쯤 지운** 렌더러를 통과시킨다」고
적었다. 맞지만 **통째로 지운 것까지 통과한 이유는 그게 아니었다** — **픽스처에 그 칸이
없었기 때문**이다. 주석을 정정했다.

### 고친 것

1. `EVERY_SHAPE` 에 `patterns_checked`·`findings` 추가
2. **`test_fixture_covers_every_summariser_branch` 신설** — `results.py` 소스에서
   `out["…"]` 키를 **뽑아** 픽스처가 그걸 다 만드는지 대조한다. **손으로 세지 않는다**
3. 정규식이 0개를 찾으며 통과하는 상태도 막았다

### 변이로 확인

```text
chat.html 의 result.pii 를 통째로 지우면
  전 → 통과 (구멍)
  후 → test_every_summary_key_has_a_renderer 실패 「화면이 모르는 결과 칸: ['pii']」

픽스처에서 pii 칸을 빼면 (뒤처짐 재현)
  → test_fixture_covers_every_summariser_branch 실패 「픽스처가 안 만드는 칸: ['pii']」
```

### 손대지 않은 것

`STATE.md`·브리지·`measured-claims.md` 의 「능력 9종」은 **과거 서술**이다 —
「그때 9종이었다」·「2026-08-31 기준」. **고치면 거짓이 된다** (Wave P 의 판단 그대로).

### 검증

capreq 단위 66 → **68** OK · `run_tests` **392** 그대로.

## 미매칭 화면을 문서에 적는다 · 낡은 숫자 셋 (Wave S) — 2026-09-01

**문서만.** 코드 0 · 검사 0 · 새 의존성 0. Wave Q(#134)가 화면에 넣은 것을 **읽는 사람이
알 수 있게** 적는다.

### `capreq/README.md` — 「못 알아들었을 때」 절 신설

라우터가 못 고르면 「(미매칭)」과 이유 아래에 **「지금 할 수 있는 일 N가지」**가 표로 뜬다.
화면 예시를 그대로 실었다.

**무엇을 하지 않는지**를 같이 적었다 — **고르라고 권하지 않는다**(목록을 보여 줄 뿐이고
고르는 것은 여전히 라우터다 · 추천도 정렬도 없다) · **새 주장 0**(Core 가 준 이름·설명 그대로) ·
**매칭됐을 때는 안 보여 준다** · **미매칭 자체를 줄이려 하지 않았다**(라우팅 문구 손질은 별개 판단).

### 낡은 숫자 셋을 고쳤다

같은 절이 **자기 개수를 손으로 세고 있었다:**

| 전 | 후 |
|---|---|
| 「띄운 뒤 **세 가지**만 본다」 (실제 넷) | **네 가지** |
| `capabilities=7` | `capabilities=N` |
| 「**아홉** 능력이 내는 모양은 여섯」 | 「**등록된 능력**이 내는 모양은 여섯 가지」 |

`measured-claims.md` 가 「개수 예시는 `N` 으로」라고 적어 둔 그대로다 — **능력이 늘 때마다
고쳐야 하는 숫자는 애초에 적지 않는다.**

### `docs/guide/user-guide-ko.md` §7 — 쉬운 말로 두 문답

「말했는데 못 알아들었다고 하면요?」 · 「목록에 없는 일을 시키면요?」

**목록은 보여 주기만 하고 골라 주지 않는다**는 것을 사용자 말로 적었다 —
**그래야 「내가 시킨 것이 아니라 접수처가 정했다」는 장부가 유지된다.**

### 검증

`run_tests` **392** 그대로 (문서만).

## `CHANGELOG` 이 머지에서 다쳤다 — 되돌리고 검사를 붙인다 (Wave R) — 2026-09-01

**정본이 조용히 두 배가 됐고 아무것도 걸리지 않았다.**

### 무슨 일이 있었나

야간에 PR **다섯**을 동시에 열었다. 코드 PR 마다 `CHANGELOG` 최상단에 항목이 들어가서
**셋이 충돌**했고, 「둘 다 남긴다」로 푸는 과정에서

- 파일 **중간에 두 번째 `# Changelog` 헤더**가 생기고
- 그 아래로 **Wave M·N·O 가 통째로 되풀이**됐다 (159줄 · 파일이 3,662 → 3,821줄)

`run_tests` 도 `check_submission` 도 **아무것도 걸리지 않았다** — **아무도 이 파일의
모양을 보지 않았기 때문**이다.

### 원인은 내 PR 방식이다

**동시에 연 다섯 개가 전부 같은 줄(최상단)을 건드렸다.** 충돌을 미리 알리고 해결법까지
적었지만, **충돌 자체를 만들지 않는 편이 나았다.** 「합쳐서 확인했다」도 **머지 전** 상태를
본 것이지 **머지된 결과**를 본 것이 아니었다.

### 고친 것

되풀이된 뒤쪽 159줄을 잘라냈다. 위쪽 사본이 온전한지 **세 항목 모두 줄 단위로 대조**한 뒤
지웠다 — 뒤쪽에만 있는 내용은 없었다. 항목 **123 → 120** (고유 120).

### 다시 못 생기게 — `tests/test_changelog_integrity.py`

**모양만** 본다. 내용은 사람이 쓴다.

1. `# Changelog` 헤더가 **하나**뿐인가
2. `## ` 항목 제목이 **겹치지 않는가**
3. 맨 위가 `# Changelog` 인가

변이 확인: 파일을 통째로 두 배로 만들면 **2종이 실패**한다.

**「최신이 위」는 검사하지 않는다.** 날짜 역순을 강제하면 같은 날 여러 항목의 순서까지
검사가 정하게 된다 — 이번에 다친 것은 순서가 아니라 **중복**이다. **다친 것만 본다.**

### 검증

`run_tests` 388 → **392** OK (skip 7) · `check_submission` **28/28**.

## 미매칭이면 막다른 골목이었다 (Wave Q) — 2026-09-01

**제품 입구 개선.** Core 스키마·DDL 0 · 새 의존성 0 · **새 제품 주장 0.**

### 무엇이 문제였나

라우터가 능력을 못 고르면 화면은 **「(미매칭)」과 이유 한 줄**로 끝났다. 사용자는
**무엇을 물어야 하는지 알 길이 없다.** `/api/capabilities` 는 서버에 있는데
**`chat.html` 이 한 번도 부르지 않았다.**

라우팅 실측(#131)에서 홀드아웃 13개 중 **둘이 `None`**(라우터가 비움)으로 나왔다 —
드문 일이 아니라 **실제로 관측되는 자리**다.

### 고친 것

미매칭이면 「지금 할 수 있는 일 N가지」를 **표로 보여 준다** — `code@version` · 이름 · 설명.
카탈로그는 **한 번만 받아 두고** 다시 안 받는다. 못 받으면 **그 줄만 없다**(화면은 그대로).

**새 주장을 만들지 않는다** — Core 카탈로그에 있는 것을 그대로 옮긴다. 그리고
**고르라고 권하지 않는다**: 목록을 보여 줄 뿐이고 **고르는 것은 여전히 라우터**다.
매칭됐을 때는 목록을 들이밀지 않는다 — 방해가 된다.

### 검증 — 흐름 프로브로 실행해서 봤다

`chat_flow_probe.js` 28 → **35종**. 새로 고정한 것:

- 미매칭이면 **목록이 실제로 그려진다**
- **두 번째부터는 다시 안 받는다**
- **매칭되면 안 보여 준다**
- **카탈로그를 못 받아도 미매칭은 그린다** (목록 줄만 없다)

변이 확인: 목록 표시를 지우면 **3종**, 캐시를 없애 매번 받게 하면 **1종** 실패.

### 검증

capreq 단위 **66** OK · 프로브 단언 31 + **35** = 66종 · `run_tests` **388** 그대로.

## 검증 체계 문서가 새 검사 두 부류를 몰랐다 (Wave P) — 2026-09-01

**문서만.** 코드 0 · 검사 0 · 새 의존성 0.

`docs/guide/testing.md` 는 「무엇을 자동으로 막는가」를 설명하는 문서인데, 이번에 생긴
**두 부류가 없었다** — 다음 사람이 그게 있는 줄 모른다.

### 채운 것 — §4.6 「CI 밖에서 도는 것 두 부류」

| 방식 | 무엇 | 왜 CI 밖인가 |
|---|---|---|
| **없으면 skip** | `chat_render_probe.js` · `chat_flow_probe.js` | `node` 가 필요하다 (CI 에는 있다) |
| **수동 도구** | `scripts/route_bench.py` | **Ollama 와 등록된 능력**이 있어야 한다 |

같이 적은 것: 문자열 검사가 「반쯤 지운 렌더러」를 통과시킨다는 것(실측) ·
라우팅 판정은 **홀드아웃으로만** 한다는 것과 그 이유(튜닝 세트에서 55→60 이던 수정안이
홀드아웃에서 **순 효과 0**이었다).

**「없으면 skip」은 「없으면 조용히 통과」와 다르다** — skip 개수가 출력에 남고,
프로브가 **몇 종을 단언했는지**도 파이썬 쪽에서 다시 본다. 0 건 통과를 막는 것이 핵심이다.

§5「아직 없는 것」에 **실제 브라우저**를 더했다 — 스텁은 CSS·레이아웃과 파일 선택기의
OS 상호작용을 못 본다. 「브라우저에서 봤다」고 쓰지 않는 이유다.

### 검사를 만들지 **않은** 판단

「능력 N종」이 문서에 박힌 자리를 훑었다. 대부분은 **과거 서술**이었다 —
「그때 5종만 등록된 스택에서」·「능력 6종이 같은 사슬을 통과했다(제출 원고)」.
**제출 원고는 얼어 있어야 맞고**(`test_report_claims.POST_CONTEST` 가 그래서 있다),
과거 서술은 고치면 거짓이 된다.

그 자리에 일괄 검사를 붙이면 **설명을 지워야 통과하는 검사**가 된다 — `tests/_srcguard.py`
가 다섯 번의 사고로 기록해 둔 함정이다. **그래서 검사를 만들지 않았다.**

### 대신 내 문서의 낡은 예시를 고쳤다

`measured-claims.md` 가 「능력 9종」을 예로 들고 있었는데 **10종이 되면서 낡았다** —
규칙 문서가 자기 말을 안 지키는 꼴이다. 개수 예시는 `N` 으로 바꾸고, 측정 예시에는
**언제 잰 것인지**를 붙였다. 그 이유도 문서 안에 적었다.

### 검증

`run_tests` **387** OK · 문서만 바뀌므로 수치 변화 없음.

## 입력 보존·삭제에 검사가 하나도 없었다 (Wave O) — 2026-09-01

**D22 는 Core 중개 수집을 허용하면서 「보존·삭제 정책이 선행 조건」이라고 못박았다.**
그 정책은 구현돼 있다 — `task_input_purge_due` 뷰 · `mark_purged` · Core 워커의 GC.
**그런데 검사가 하나도 없었다.** `tests/integration/check_input_purge.py` **17종** 신설.

**코드 0 · DDL 0 · 정책 숫자 변경 0** — 지금 정책이 무엇인지 **읽어서** 고정할 뿐이다.

### 없으면 무엇이 조용히 무너지나

| 무엇이 빠지면 | 무슨 일이 |
|---|---|
| 뷰의 `NOT EXISTS (… capability.sample_input_id …)` (0013 B2) | **계약 샘플 바이트가 24시간 뒤 지워지고** 계약 게이트가 통째로 못 돈다 |
| `mark_purged` 가 행까지 지우게 되면 | **「어디로 갔는지 답할 수 있다」가 거짓**이 된다 — 제품 주장이 사라지는데 아무도 모른다 |
| `WHERE storage_state = 'STORED'` | 이미 지운 것을 GC 가 **무한히 다시 집는다** |

### 고정한 것 (실측 17/17)

- **정책이 SQL 에 있다** — `reason` 세 종이 뷰에서 나온다:
  `orphan-24h`(task 없는 업로드) · `finished-7d`(종결 후) · `stale-72h`(미완료 최대 수명)
- **아직 살아 있는 것은 안 지운다** — 방금 끝난 task · 도는 중인 task · 1시간짜리 고아
- **계약 샘플은 대상에서 빠진다** — 붙기 전엔 고아라 대상이었다가, 붙는 순간 **뷰에서 사라진다**
- **바이트만 지우고 행은 남는다** — `PURGED` 뒤에도 `sha256`·`byte_size`·`media_type`·
  `uploaded_by` 가 **그대로다**. 이게 「어디로 갔는지」에 답하는 값이다
- **두 번 돌려도 안전하다** — `mark_purged` 는 `STORED` 인 것만 바꾸고, `PURGED` 는 목록에서 빠진다

### 쓰다가 배운 것

`task` 의 `capability_trust_domain_min` 은 **스냅샷이고 복합 FK 가 걸려 있다.** 검사도
앱과 같은 태도로 `capability` 에서 **`INSERT … SELECT` 로 복사**한다 — 검사가 손으로
채우면 그 검사만 통과하는 상태를 만든다.

`uploaded_by` 는 `app_user` 를 가리키는 **FK** 다. 「누가 올렸나」가 실제 사람을 가리켜야
증적이 뜻을 갖는다는 것이 스키마에 이미 박혀 있었다.

재현: `scripts/run_integration.sh check_input_purge` (DB 필요).

### 검증

통합 검사 13 → **14종**. `run_integration.sh` 가 `tests/integration/check_*.py` 를
자동으로 줍는다 — **CI 배선 변경 없음.** `run_tests` **388** 그대로.

## 라우팅 벤치가 10번째 능력을 안 덮고 있었다 (Wave N) — 2026-09-01

**검사 하나를 파생으로 바꾸자 그 자리에서 실패가 떴다.** 코드 0 · DDL 0 · 새 의존성 0.

### 무엇이 뒤처져 있었나

카탈로그는 `safety.pii` 를 **「구현됨」**이라 하는데, `scripts/route_bench.py` 의 프롬프트
세트와 `tests/test_route_bench.py` 의 `IMPLEMENTED` 는 **9종에서 멈춰 있었다.**
Wave L 이 능력을 더했는데 라우팅 벤치가 안 따라왔고, **`IMPLEMENTED` 가 손으로 센 목록이라
검사가 못 잡았다.**

**이번 달 네 번째 같은 모양이다:**

| 어디 | 무엇을 세고 있었나 | 언제 |
|---|---|---|
| `test_capability_patch_wiring` | 데모 이름 셋 | Wave K |
| `test_chat_html_unit` | 「자른 사실 고지」 3개 | Wave L |
| `test_text_rank` | 「셋 다 바이트가 같다」 | Wave L |
| **`test_route_bench`** | **구현 능력 9종** | **여기** |

### 고친 것

`IMPLEMENTED` 를 **카탈로그의 「✅ 구현됨」 행에서 파생**한다. 바꾸자마자
`test_both_sets_cover_every_implemented_capability` 가 **`safety.pii` 가 빠졌다고 실패했다** —
그게 이 Wave 의 시작이다. 정규식이 0개를 찾으며 통과하는 상태도 같이 막았다.

프롬프트 세트에 `safety.pii` 를 넣었다 (튜닝·홀드아웃 각 하나).

### 실측 — 10번째 능력이 이웃을 밀어내지 않았다

능력 10종 등록 · 홀드아웃 13개 × R=5 (`qwen2.5:3b`):

```text
합계 42/65
  safety.pii   5/5   ← 새 능력이 자기 것을 가져간다
  기존 12개    37/60 ← 이전 밴드(36·36·38) 안
```

재현: `PYTHONPATH=capreq/src python3 scripts/route_bench.py --set holdout --repeats 5`
(능력 10종 등록 선행 · Ollama 필요).

**개선을 주장하지 않는다.** 같은 조건도 2점씩 흔들린다는 것을 이미 쟀고, 37 은 그 밴드 안이다.
여기서 말하는 것은 **「새 능력을 더해도 이웃이 안 밀렸다」** 하나뿐이다.

### 검증

`run_tests` 387 → **388** OK (skip 7) · `check_submission` **28/28**.
## `chat.html` 을 처음으로 실행해 봤다 (Wave M) — 2026-09-01

**#107 · #112 · #118 · #128 — 네 번 연속으로 「브라우저 렌더링은 못 봤다」고 적은 자리**다.
이 저장소에서 **가장 오래 미확인**이었고, 거기서 결함이 **두 번** 나왔다
(#118 새 결과 칸이 원시 JSON 으로 샘 · #128 자른 사실 고지가 빠질 뻔함).

**제품 코드 0 · 새 npm 패키지 0.**

### Playwright 를 쓰지 않았다

`chat.html` 이 실제로 쓰는 브라우저 API 가 적다 — `document` 12 · `fetch` 4 ·
`addEventListener` 3 · `window` **0** · `localStorage` **0**. 그래서 **최소 DOM·fetch 스텁**
(순수 JS 몇십 줄)으로 `<script>` 를 통째로 실행하고 `renderSummary()` 를 **진짜로 호출**한다.

`node` 가 없으면 **skip** 한다 — 루트 `run_tests` 의 「의존성 설치 없음」을 깨지 않는다.
CI `capreq` 잡에 `actions/setup-node` 한 단계를 넣어 **거기서는 실제로 돈다.**

### 문자열 검사가 못 잡던 것을 잡는다 (변이로 확인)

`test_chat_html_unit.py` 는 부분 문자열 검사라 **「반쯤 지운 렌더러」를 통과시킨다** —
그 한계를 그 파일이 스스로 적어 뒀었다. 실제로 재현했다:

```text
result.pii 분기만 남기고 몸통을 지웠을 때
  문자열 검사 (test_chat_html_unit)   62 OK   ← 통과시킨다
  실행 검사   (chat_render_probe.js)  7종 실패 ← 잡는다
```

### 흐름도 실행한다 — `chat_flow_probe.js`

렌더러 하나가 아니라 **보내기를 누른 뒤 벌어지는 전부**를 돌린다:
`onsubmit` → `fetch("/api/chat")` → `renderRouting` → `pollTask` → `renderSummary`.

**#112 는 첨부가 제품 1호부터 서버에 한 번도 닿지 않은 버그였다.** 그때 고친 것은
**서버 쪽**(`isinstance`)이고, **클라이언트가 파일을 실제로 `FormData` 에 담는지는 아무도
확인한 적이 없다.** 여기서 처음 봤다 — 맞게 담고 있었다.

같이 고정한 것: `wait=false` 로 보내고 폴링한다 · 첨부에 `content-type` 을 손으로 붙이지
않는다(boundary 가 깨진다) · **성공 뒤 첨부를 비운다**(같은 파일이 두 번 가지 않게) ·
HTTP 오류·상태 조회 실패·미매칭에서 **말풍선이 `bad`** 가 된다 · **빈 입력이면 요청을
만들지 않는다**.

변이로 확인: `fd.append("file", …)` 를 지우면 **1종**, `pollTask` 호출을 지우면 **5종** 실패.

### 무엇을 보나 — 31종 + 28종

능력 10종이 내는 **결과 모양 전부**를 렌더러에 넣고 DOM 을 본다. 특히:

- `safety.pii` — **빈 결과에도** 「찾아본 패턴」과 「**「없다」가 아니라 못 찾았다**」가 붙는가
- 화면이 **가림을 되돌리지 않는가** (`o**@e******.dev` 가 그대로 그려지는가)
- 자른 사실 고지가 **`truncated` 일 때만** 붙는가
- 모르는 칸이 **삼켜지지 않고** 「그 밖의 출력」으로 남는가

첫 실행에서 **24종이 한꺼번에 실패**했다 — 스텁에 `childElementCount` 가 없어서였다
(`renderSummary` 가 그 값으로 최종 append 를 정한다). 스텁 쪽 결함이라 고쳤고,
**그 사실을 스텁 주석에 남겼다.**

### 여전히 못 보는 것

실제 브라우저의 **CSS·레이아웃**과 **사용자 상호작용**(드래그앤드롭·폼 제출).
그래서 **「브라우저에서 봤다」고 쓰지 않는다** — **「렌더러를 실행해 DOM 을 봤다」**가 맞는 말이다.

### 검증

capreq 단위 56 → **66** (`node` 있을 때) · **skip 6** (없을 때) ·
프로브 단언 **31 + 28 = 59종**. `run_tests` **387** 그대로.

## 카탈로그 +1: `safety.pii` — 탐지가 아니라 참고다 (Wave L) — 2026-08-31

**10번째 실행기.** DDL 0 · 새 의존성 0 · 새 학습 0 · 외부 말뭉치 0.
카탈로그 §Safety **#49 에 이미 선언돼 있던** 능력을 구현한 것이다.

### 이름이 위험한 능력이라 규율을 먼저 정했다

「PII 를 찾는다」가 **놓치면 없느니만 못하다** — 사람은 결과가 비면 「검사했으니 없다」로
읽는다. 그래서 이 카탈로그가 `safety.malware_hint` 에 이미 적어 둔 규율을 그대로 썼다:
**「탐지」가 아니라 「참고」다.**

**주장하지 않는 것:** 놓친 것이 없다 · 실제 개인정보다 · 마스킹/비식별화 도구다 ·
개인정보 보호 준수를 보증한다. `quality_profile='none'` · 재현율·정밀도 숫자 없음.

### 결과가 자기 한계를 들고 다닌다

`patterns_checked` 를 **항상** 같이 낸다 — **목록에 없는 것은 「찾지 않았다」는 뜻이지
「없다」는 뜻이 아니다.** 이 칸이 없으면 빈 `findings` 가 「깨끗하다」로 읽힌다.
capreq 화면도 그 문장을 그대로 보여 준다(「찾은 자리 없음 — 「없다」가 아니라
「이 패턴들로는 못 찾았다」입니다」).

### 원문을 결과에 담지 않는다

찾은 자리의 글자를 그대로 돌려주면 **결과 자체가 새 유출면**이 된다 — 결과는 증적에 남고
화면에 그려지고 로그를 탄다. 그래서 `text` 는 **가려서** 낸다(`ops@example.dev` →
`o**@e******.dev`). `start`·`end` 는 그대로 준다 — 원문을 다시 볼 수 있는 쪽은
**원문을 가진 사람**뿐이다.

### 규칙 (`app/pii_rules.py` 에 전부)

`email`·`ipv4`·`ipv6`·`uuid`·`krrn_like`·`card_like`·`phone_kr_like`.
`krrn_like` 는 **앞 6자리가 달력에 맞아야** 하고(없으면 임의의 13자리가 다 걸린다),
`card_like` 는 13..19자리이고 **Luhn 을 통과**해야 한다 — **Luhn 은 오타 검사지 실재
검사가 아니다.** 그래서 `_like` 다. 겹치면 먼저 온 패턴이 이긴다.
`ipv6` 는 **축약(`::`)을 다 풀지 않아** 뒷부분만 걸릴 수 있다 — 숨기지 않고 적었다.

**자르지 않고 던진다** (`NODE_MAX_PII_FINDINGS`) — 자르면 「전부 찾아봤다」가 거짓이 되고,
**PII 능력에서 그 거짓말은 특히 나쁘다.**

### capreq 표시를 같은 PR 에서 고쳤다 (#118 교훈)

`results.py` 가 `findings`·`patterns_checked` 를 모르면 또 원시 JSON 으로 떨어진다.
요약기·화면·검사를 함께 넣었다 — **능력을 더할 때 화면이 따라와야 한다.**

그 과정에서 **하드코딩된 개수 두 개**를 파생으로 바꿨다: `chat.html` 의 「자른 사실 고지」
개수(3 → 렌더러 수만큼)와 카탈로그의 「셋 다 바이트가 같다」(→ 정규식). 개수를 손으로
세게 하면 언젠가 **고치는 대신 검사를 지우게** 된다.

### 실측 (2026-08-31 · `scripts/pii_demo.sh`)

```text
OK  weights_fingerprint / arch / max_params(0<=1000) / preprocess / input_schema
OK  output_schema — 칸 2개(findings, patterns_checked)가 계약을 만족한다
gate_run PASSED → 바인딩 → COMPLETED · 증적 team → team · M <= M

찾아본 패턴: card_like, email, ipv4, ipv6, krrn_like, phone_kr_like, uuid
  email          o**@e******.dev
  phone_kr_like  *******5678
  krrn_like      ******-1******
  card_like      ************1111
```

같은 입력의 **가짜 카드(`1234 5678 9012 3456`)와 날짜꼴 아닌 것(`991301-…`)은 걸러졌다.**
데모가 그것을 검사한다. capreq `/api/tasks/{id}` 에서도 `pii` 로 구조화돼 나오고
`other` 로 새지 않는다.

재현: `bash scripts/pii_demo.sh` (Core · Docker 필요).

### 검증

`run_tests` 355 → **384** (`tests/test_safety_pii.py` 28종) · capreq 52 → **56** ·
`check_submission` **28/28** (필수 가중치 8 → 9종) · `check_release` OK.

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
