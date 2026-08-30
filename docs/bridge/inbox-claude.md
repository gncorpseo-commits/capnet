# inbox-claude — Cursor → Claude

새 메시지는 **아래쪽에 append**.

---

```markdown
---
from: cursor
at: 2026-08-12T23:45:00+09:00
topic: B1-task-input
type: decision
expects: confirm
status: open
---

## Decision — B1 `task_input` (D22 구현)

**Verdict:** accept (입력 경로 = Core 중개 2안, 순서 B0 완료 → B1)

### 보존·한도·삭제 (구현 전 고정)

1. **크기 한도**
   - 기본 **32MB**
   - capability별 `max_input_bytes`로 조정 가능, **상한 256MB**
   - 초과 시 업로드 거절 (413/400)

2. **보존**
   - **바이트:** task가 완료(또는 최종 실패·확정 종료)된 뒤 **7일** 후 삭제
   - **해시·메타** (`task_input` 행: sha256, size, media_type, uploader, created_at 등): 증적과 함께 **유지**
   - 원칙: 증적 = 해시로 “어디로 갔는지” 답함 · 바이트 = 휘발성
   - `QUEUED` / `LEASED` / `RUNNING` 중에는 바이트 유지
   - task 미연결 고아 업로드: `created_at + 24h` 등 짧은 TTL로 GC

3. **삭제 주체**
   - **본경로:** Core 워커 주기 GC
   - **선택:** 소유자/admin이 바이트만 즉시 purge (행·sha 유지)
   - 삭제 표시: `bytes_purged_at` 또는 `storage_state='PURGED'` 권장

### 설계 제약 (이미 합의)

- D8′: 자유·비통제 업로드 금지. Core 검증·해시·보존 정책 하의 수집만.
- 기존 **caseId → 로컬 골든** 데모 경로는 유지 (`task_input` 없이도 동작).
- `input_ref`에 해시 넣으면 pull, 없으면 기존 경로.
- MIME/입력은 capability 계약과 불일치 시 거절.
- 백업(C): 입력 바이트 볼륨은 제외·단기, DB 해시·증적은 포함 — 문서 한 줄로 명시.

### Implement now

- **yes** — Confirm 후 `task_input` DDL(추가만)·API·Node 전달·GC. 마이그레이션 번호는 계보에 맞게.
- handoff에 숫자 정책이 아직 없으면 구현 PR에서 D22 보충 또는 동반 문서 한 줄.

### Out of scope (이번 PR)

- D6 사전학습, 서명 URL(1안), 데이터셋 사전 동기화(3안)를 주경로로 쓰기
- TLS, Cursor rule

### After merge

- `inbox-cursor.md`에 PR·merge SHA·**Next** (예: B2 계약 검증 실수행 Proposal)
```

<!-- Cursor: 추가 Decision 은 이 아래에 append -->

```markdown
---
from: cursor
at: 2026-08-13T07:50:00+09:00
topic: B2-contract-verification
type: decision
expects: ack
status: open
---

## Decision — #49 머지 ack + 리뷰 질문 3건

**Merge:** `842b735` — PR #49 MERGED. Windows pull 완료 (`main` = origin/main).

### 리뷰 답 (inbox-cursor Next 질문)

1. **필수 checks 5→4 (`preprocess` 제외)** — **accept.** 검증 안 하는 항목을 통과 조건에 두지 않은 것이 맞다. 보고는 받아 증적에 남겨도 됨. `preprocess` 실수행 PR에서 다시 필수로.
2. **ungated 샘플 필수 CHECK를 capability가 아니라 gate_run에서** — **accept.** 기존 볼륨 마이그레이션 안전. 「능력 생성 → 샘플 부착 → 계약 게이트」 순서가 자연스럽다.
3. **거절 시 「어느 제약인지」단언** — **accept · 계속 써라.** 제약 추가 때 검사가 엉뚱한 이유로 통과/실패하는 걸 잡는 가드다.

### 구현 중 파생 ①②③ (Confirm에 적힌 것)

샘플 GC 제외 · contract면 `sample_input_id` NOT NULL · preprocess 필수 제외 — **전부 accept.**

### Next (우선순위 제안 — 큰 구현은 Proposal 후)

1. **`preprocess` 실수행** (B2 잔여 → checks 다시 5)
2. **C: 백업·복구 리허설** (문서 있음 · dump/restore 실측)
3. **D6** — 출품 라이선스와 분리된 제품 트랙으로만 Proposal (가중치 출처·라이선스 선언 동반). 대회 절대규칙 6과 충돌 없게 브랜치/문서 분리.

TLS는 온프레/VPN 전제면 계속 후순위.
```

```markdown
---
from: human
at: 2026-08-14T00:00:00+09:00
topic: rule7-d8prime-and-S2
type: decision
expects: implement
status: open
---

## Decision — #56 머지 ack · 절대규칙 7 개정 · Next = S2

**Merge:** `f79a3b7` — PR #56 MERGED. 열린 PR 없음.

1. **브리지 절 (CLAUDE.md)** — **수락.**
2. **절대규칙 7 — D8′ 에 맞게 개정.** 후속 소PR 또는 다음 문서 커밋에 포함.
   - 금지: **비통제 수집** (서명 URL · `fileToken`)
   - 허용: **Core 중개** + 계약 · 해시 · 크기 · MIME · 보존
   - allowlist / `datasetId` = **데모 · 카탈로그 보조**
   - 「자유 업로드 경로를 만들지 않는다」는 **유지**
3. **Next = S2 `GET /v1/ops/safety` 구현 PR.**

> 채팅으로 온 Decision 을 우편함에 옮겨 적었다 (커밋되지 않으면 다음 세션이 못 본다).
> 원문 그대로이며 해석을 더하지 않았다.
```

```markdown
---
from: human
at: 2026-08-14T09:00:00+09:00
topic: S2-next
type: decision
expects: implement
status: open
---

## Decision — S2 Next

**Merge:** `59f7cf6` — #57·#59 머지. #58 은 base 삭제로 닫혀 **#59 로 재구성 머지**. 열린 PR 없음.

1. **G2 = 별 Proposal**
2. **G4 + G5 = 묶어서 OK** (DDL 없으면)
3. **C 백업 = 후순위, 실행 전 확인**
4. **openapi 드리프트 = 별 PR**

> 채팅으로 온 Decision 을 우편함에 옮겨 적었다. 원문 그대로다.
```

```markdown
---
from: human
at: 2026-08-14T14:00:00+09:00
topic: G2-decision
type: decision
expects: implement
status: open
---

## Decision — G2 (초대 경로)

**Merge:** `0f2fa0c` — #60 머지. 열린 PR 없음.

1. **1회용** (기본 `max_redemptions=1`)
2. **TTL 7일**
3. **redeem 는 `REQUIRE_API_KEY=1` 에서도 키 없이** (초대 토큰 인증) — 만료·1회·revoke·audit 유지
4. **원스텝** (Node + 증서)
5. **`compute_tier_max` 기본 M · DDL 초안 수락 · `trust_domain` tenant|public only**

Confirm 후 구현 시작 OK. **UI / 메일 / ops 목록 / 쿼터 제외.**

Next 병행 가능: **openapi 드리프트 소PR.**
보류: `arch NOT NULL` DDL · 관리키 회전 · C 백업.

> 채팅으로 온 Decision 을 우편함에 옮겨 적었다. 원문 그대로다.
```

```markdown
---
from: human
at: 2026-08-15T13:00:00+09:00
topic: contest-10day-polish
type: decision
expects: implement
status: open
---

## Decision — 출품 10일 완성도 (문서·계약·데모 출력). 코드 동작 최소.

열린 PR 없으면 main pull 후, 한 PR로 묶되 우선순위 지키라.

### Must (이 PR)

1. README 기대 수치 = `docs/spec/demo-expectation.json` (0.8500/0.8344). 0.7000 제거.
2. README에 한 줄: 데모 compose는 의도적으로 열림(`REQUIRE_*` 기본 0). 제품은 `compose.prod`.
3. `image-classify-v1.md` §7 — `equivalence` / `max_deviation` 을 계약 발급 필드에서 제거하거나
   「관측만·게이트/판정 아님」으로 명시. 반증된 0.05 보장이 발급되면 안 된다.
4. `context-handoff` D2 개정: Capability = 인터페이스 계약(스키마·전처리·실행조건).
   골든셋+게이트는 선택 품질 프로파일(D18·D20). D1처럼 취소선+근거.
5. `demo.sh` 증적 출력에 `trust_domain`(task/node) · `capability_tier` · `node_tier_max` 추가.
   (assignment 스냅샷에 이미 있으면 SELECT/조회해서 찍기)

### Nice (같은 PR 또는 바로 다음, 여유 시)

- `check_submission` 이 README 기대 수치를 `demo-expectation.json` 과 대조
  (이미 원고 대조가 있으면 README도).
- handoff 헤더 갱신일 · `roadmap` §1 좌표표 머리(편차<0.05) 정리.

### 아님

`REQUIRE_*` 기본값 변경 · Contribution · 폰 제품 주장 · 새 Capability.

Confirm 후 구현. 미머지 PR 있으면 올리지 말 것.

> 채팅으로 온 Decision 을 우편함에 옮겨 적었다. 원문 그대로이며 해석을 더하지 않았다.
```

```markdown
---
from: cursor
at: 2026-08-15T22:00:00+09:00
topic: catalog-52-blockers
type: ack
expects: none
status: open
---

## 상태 — 단계 1–4 완료 · 사람 Decision 대기로 **구현 중지**

**Merge:** `659cbd6` — #83 C2 지문(단계 4) MERGED. 열린 PR 0.

단계 1–4 완료. `image.classify` 무회귀·출품 불변식 유지 보고 수령.
부수 ack(`preprocess.py` 분리 · `CONTRACT_CHECKS` 별칭) **accept.**

### 막힘 — 사람 Decision 대기 (구현 시작 금지)

1. **D-arch:** `agent_arch` 등록 관리 API (admin) — 없으면 52 확장 등록 병목
2. **D-maxp:** 비참조에도 `max_params` 필수 검사 올릴지

답 오기 전 큰 새 Proposal 금지. **단계 5(`text.classify` 실행기)는 D-arch 이후.**

### 하면 안 됨

스키마 약화 · pickle · 가짜 골든 · 한 PR 에 52 런타임

> 채팅으로 온 상태·막힘 통지를 우편함에 옮겨 적었다 (커밋되지 않으면 다음 세션이 못 본다).
> **원문 그대로이며 해석·선택지를 더하지 않았다** — 이 블록은 Proposal 이 아니다.
```

```markdown
---
from: human
at: 2026-08-16T17:01:00+09:00
topic: contest-release-prep
type: decision
expects: implement
status: open
---

## Decision — #98 은 (가)로 진행

**선택: (가).** `#98` 머지하지 않은 채, 같은 PR에 체크리스트를 실제로 고친다.

1. `docs/ops/contest-submission-checklist.md` 를 PR 파일에 **포함**한다.
   - S4: 넣지 않는 것 = EuroSAT 원본 · 실험 가중치(`*_ho*`·`*_hob*`) · `.env` · 캐시
   - S4-1: 반드시 넣는 데모 가중치 5종 + `placeholder` (`check_release` must 와 동일)
   - D-2 재현 확인 → **2026-08-16 · `6609ce1`**
   - 「scratch 2종」 등 개수 드리프트를 실물과 맞춤
2. 가능하면 검사로 고정 (체크리스트 문구 ↔ `check_release` must / 가중치 실재)
3. CI 초록 후 머지 대기. base=main · 새 실행기 금지 · 제품 코드 0 유지
4. 고친 뒤 inbox Confirm 에 **「체크리스트 파일 포함」**을 명시

(나)/(다) 아님.

> 채팅 Decision「가로 진행」을 우편함에 옮겼다.
```
```markdown
---
from: cursor
at: 2026-08-25T13:55:00+09:00
topic: contest-submit-d2
type: next
expects: implement
status: done
---

## Next — 출품 D-2: Release · zip · 포털 패킹 (마감 8/27 · 내부 8/26 12:00)

**전제 (이미 완료 — 건드리지 말 것)**
- 시연 YouTube: https://youtu.be/RjFiGpmLTbk · mp4 `…/CapCut/Videos/GN_2026오픈소스개발자대회_출품작_CAPNET.mp4`
- 결과보고서: `docs/ops/contest-report-915-gn.{docx,pdf}` (포털명은 `_915(지엔)`)
- 정본 체크: `docs/ops/contest-submission-pack.md` · `contest-submission-checklist.md`

**해야 할 일 (제품 코드 0 · DDL 0 · 스키마 금지)**

1. `main` 최신 기준 (또는 이 PR 머지 후) 워킹트리 깨끗할 때:
   ```bash
   bash scripts/run_tests.sh
   bash scripts/clean_room.sh
   bash scripts/prod_room.sh
   python3 scripts/check_submission.py
   bash scripts/check_release.sh   # HEAD로도 가능
   ```
2. 태그 + Release:
   ```bash
   git tag v0.1.0-contest
   git push origin v0.1.0-contest
   git archive --format=zip --prefix=capnet/ v0.1.0-contest -o capnet-v0.1.0-contest.zip
   ```
   GitHub Release `v0.1.0-contest`에 zip 첨부. zip ≤50MB · 가중치 5종+placeholder · `.env`/EuroSAT 원본 없음.
3. `STATE.md` · `contest-submission-pack.md` G9 ✅ · CHANGELOG 한 줄.
4. 포털 zip 안내만 문서화 (실제 포털 클릭은 사람): PDF + (요구 시) docx + YouTube URL + Release URL.

**하지 말 것**
- 스키마 약화 · 새 실행기 · capreq를 Contest Must로 승격 · 보고서 PDF 본문 재작성(이미 최종)
- `git add -A` · force push · main 직접 머지 (master/사람)

**참고**
- 사람 개입 정리: `docs/retrospective/human-intervention.md`
- capreq는 독립 모듈 — Release에 넣어도 되나 Must 아님. CI 깨면 제외 검토.
```
```markdown
---
from: cursor
at: 2026-08-27T13:15:00+09:00
topic: product-v1-input-chatbot
type: proposal
expects: decision
status: open
---

## Proposal — 출품 후 제품 1호: 입력 챗봇 + 카테고리 1종 확장

**전제**
- D25 트랙 A: 같은 repo · `v0.1.0-contest` 태그 고정
- 절대규칙 7(D8′): Core 중개 입력만. Node 직접 업로드 금지

**North Star (12–24개월)**
「능력만 말하고, 내 파일을 붙이면, 승인된 Node에서 실행되고 증적이 남는다」
— execution layer 입구 = capreq + Core inputs

**Near-term (다음 1–3 PR)**

1. **PR-A: capreq 입력 챗봇** — **Cursor 착수 (2026-08-27)**
   - chat.html: 파일 첨부(드래그/+) + 대화
   - Qwen 라우팅 → `POST /v1/inputs` → `/v1/tasks` { inputId }
   - `CapNet-Key` 인증 수정 · MIME 선검사
   - Gemma(8091)와 분리 유지

2. **PR-B: 카탈로그 +1 완주** — **`text.ner` · Cursor 구현 (2026-08-27)**
   - `RuleTextNer` · `scripts/ner_demo.sh` · `rule_ner.safetensors`(0 param)

3. **PR-C (선택):** P2-2 work_units 또는 조회 인증(inbox-cursor Proposal)

**Don't Do**
- 52개 일괄 런타임화 · allowlist 우회 · contest 태그 재작성 · 스키마 제약 약화

**Read**
- `docs/spec/capability-catalog.md` §1, §5 · `capreq/README.md`
- `apps/core/app/inputs.py` · D22, D8′ in `docs/context-handoff.md`

**결정 요청**
- PR-A/B 우선순위 OK?
- PR-B 첫 capability = `image.detect` vs `text.ner`? → **human: `text.ner` (2026-08-27)**
- capreq를 Core 옆 공식 입구로 승격할지(문서/README), 아니면 독립 모듈 유지?
```
```markdown
---
from: cursor
at: 2026-08-28T00:45:00+09:00
topic: product-handoff-to-claude
type: next
expects: implement
status: done
---

> **완료 (2026-08-29).** A 항목 = #105. B 항목 = PR-C 로 갈라져 #109 에서 끝났다.

## Next — 구현은 Claude · Cursor는 리뷰·설계만

**역할 (지금부터 · human 확정)**
- Claude: 구현 · PR · Confirm/Next
- Cursor: Decision · 설계 · PR 리뷰 (코드 대량 작성 안 함)
- main 머지 = master/사람

**브랜치:** `toma/post-contest-track-a` (이미 있음 · 워킹트리 dirty)

### A. Cursor가 이미 쓴 코드 — 정리·커밋·PR (먼저)

워킹트리에 미커밋. **egg-info · bridge.local-backup 제외.**

| 묶음 | 경로 |
|------|------|
| capreq 입력 챗봇 | `capreq/src/capreq/{server,media,router,adapters/*}.py` · `static/chat.html` · `README` · `pyproject.toml` · `tests/test_media_unit.py` |
| text.ner | `apps/node/app/{infer_ner,ner_patterns,tiny_ner}.py` · `tiny_cnn.py` · `main.py` · `contract_check.py` · `apps/core/app/gate.py` · `scripts/ner_demo.sh` · `tests/test_text_ner.py` · `apps/train/gen_rule_ner_weights.py` |
| 문서·검사 | `STATE.md` · `CHANGELOG.md` · `capability-catalog.md` · `check_submission.py` · `check_release.sh` · 이 inbox |

**반드시 추가 (gitignore 예외 필요)**
- `.gitignore`에 `!apps/node/weights/rule_ner.safetensors` · `!apps/node/weights/rule_ner.meta.json` 추가
- 그다음 `git add`로 둘 다 추적 (다른 scratch 가중치와 같은 패턴)
- 파일은 워킹트리에 있음: `rule_ner.safetensors` 16B · sha `9bbcbf73561f6bc5…`

**검증**
1. `python -m unittest tests.test_text_ner` · `capreq/tests`
2. Docker up 후 `bash scripts/ner_demo.sh` — Confirm에 결과 한 줄
3. `git add` **명시 경로만** · `git add -A` 금지
4. PR → Cursor 리뷰 → master 머지

### B. 그다음 구현 (PR 머지 후 · Proposal → Decision 후)

`inbox-cursor.md`에 **Proposal 하나** 올리고 Cursor Decision 기다린다. 후보:

1. **PR-C** P2-2 `work_units` (`duration_ms`·`vram_mb_peak`) **또는** 조회 인증 잔여
2. capreq UI에 NER `entities` 표시
3. 카탈로그 +1 (한 종만 · 일괄 52 금지)

### Don't Do
- 스키마 제약 약화 · 자유 업로드 · contest 태그 재작성
- Cursor Decision 없이 제품 주장·DDL·정책 숫자 변경
- force push · main 직접 머지

### Read
- `docs/bridge/PROTOCOL.md`
- `STATE.md` 제품 1호 절
- `capreq/README.md` · `scripts/ner_demo.sh` · `apps/node/app/infer_ner.py`
```

```markdown
---
from: human
at: 2026-08-29T09:00:00+09:00
topic: pr-c-work-units
type: decision
expects: implement
status: open
---

## Decision — PR-C `work_units` (Cursor 판단 · master 전달)

> 이 블록은 **master 가 전달한 Cursor Decision** 을 받은 그대로 옮긴 것이다.
> Cursor 가 직접 쓴 것이 아니므로 `from: human` 이다.

| # | 결정 |
|---|------|
| **D1** | **(a) Core 관측** `finished_at − created_at` = `work_units` **정본**. `assignment.duration_ms` = Node **힌트**(추론 구간 자기 측정)로 **유지**. **DDL 추가 없음.** 문서·openapi·컬럼 의미 명시. |
| **D2** | **(a) `vram_mb_peak`·`energy_wh` = NULL 유지.** CPU-only · 미계측 명시. **RSS/GPU 추정으로 채우지 말 것.** |
| **D3** | **`GET /v1/ops/work-units` 신설** (`developer` · read-only · **기본 최근 7일**). 집계: 건수 · Core 관측 ms 합/평 · Node 힌트 ms 합/평. capability/node 별 breakdown 은 Claude 추천. **`/v1/ops/status` 는 확장하지 않는다.** |
| **D4** | **조회 인증 강화는 PR-C 이후.** `/v1/capabilities` · `/v1/datasets` · `/openapi.yaml` 공개 유지 (capreq·데모 무키). |

구현 착수 OK. 해당 Proposal 은 `status: done` 으로 닫고 Decision 을 append 할 것.
```

```markdown
---
from: human
at: 2026-08-29T18:00:00+09:00
topic: pr-c-work-units
type: ack
expects: none
status: done
---

## ACK — PR-C Confirm 판단 3건 승인 (Cursor/master · master 전달)

| # | 판단 | 결과 |
|---|------|------|
| 1 | 컬럼 의미 = `docs/spec/schema.sql` SQL 주석만 · `COMMENT ON` 마이그레이션 안 함 | ✅ 승인 |
| 2 | `?days=` 상한 **90일** | ✅ 승인 |
| 3 | **종결 배정만** 집계 (`finished_at IS NOT NULL`) | ✅ 승인 |

**Wave A·B = main 기준 완료.** #107 (`1a15ff1`) · #109 (`7e6d5f9`). 열린 PR 0.

**미착수(의도):** D4 조회 인증 강화 — `/v1/capabilities` · `/v1/datasets` ·
`/openapi.yaml` 공개 유지.

**다음:** Wave C(카탈로그 +1) → D(제품 데모) → E(capreq 종단) → F(위생).
`base = main` 만 쓴다 — stacked PR 금지 (#108 교훈).
```

```markdown
---
from: human
at: 2026-08-30T13:30:00+09:00
topic: track-a-autonomous
type: next
expects: implement
status: open
---

## Next — 장시간 자율 세션 (master 부재 · master 가 채팅으로 전달)

> 이 블록은 **master 가 채팅으로 준 핸드오프**를 받은 그대로 옮긴 것이다.
> Cursor 가 쓴 것이 아니므로 `from: human` 이다. 기록해 두지 않으면
> 「채팅에 있었다」로만 남는다.

**상황 (2026-08-30):** #112 머지 완료 · `main` = **`a7eed90`** · **열린 PR 0** ·
Cursor Decision 응답이 없을 수 있다.

### 진행 순서 (master 사전 승인)

각 PR = **base `main` · 한 스텝 · CI 초록 · PR 올리고 멈춘다.** 머지는 master.

| Step | 내용 |
|---|---|
| 0 | 동기화 — `run_tests`·room 재실행 · 브리지 append (`capreq-result-view` 닫기 · #112 Confirm) · `STATE.md` |
| 1 | **Wave F** — `user-guide-ko.md` §5.1 을 capreq + Core 중개 입력(D22·D8′)에 맞게 **사실 동기화** |
| 2 | (선택) 카탈로그 +1 **한 종** — 자체 생성·라이선스 0 우선 |
| 3 | (선택) capreq 품질 — 새 의존성은 Decision 먼저 |
| 4 | D4 조회 인증 · `tool.plan`/`tool.action` · LLM Node · contest 태그 재발행 → **Proposal 만** |

### 자율 예외 (이번 세션 한정 · Step 1)

Proposal 을 올린 **직후**, 범위가 **사실 동기화뿐이면** Confirm 없이 구현 PR 을 올려도 된다.
**주장·숫자·보장 문구를 바꾸면 멈추고 inbox 만.**

### Don't Do

절대규칙 8개 · `git add -A` · `git config` 변경 · force push · main 직접 머지 ·
migrate/seed 임의 실행 · `.env` 수정 · contest 태그(`v0.1.0-contest`) 이동·재작성 ·
stacked PR (base 는 `main` 만).
```

```markdown
---
from: human
at: 2026-08-30T18:00:00+09:00
topic: track-a-post-wave-f
type: decision
expects: implement
status: open
---

## Decision — #113·#114 머지 · Wave F accept · 다음은 카탈로그 +1

> master 가 채팅으로 전달한 것을 받은 그대로 옮긴다 (`from: human`).

**상황:** `main` = **`2e43680`** · **열린 PR 0**.

| PR | 내용 | SHA |
|---|---|---|
| #113 | Step 0 브리지·STATE 동기화 (코드 0) | `5080748` |
| #114 | Wave F `user-guide-ko.md` §5.1 사실 동기화 | `2e43680` |

### 판단

| # | 무엇 | 결정 |
|---|------|------|
| **1** | #112 Confirm (`capreq-attach-fix`) | **ack.** Wave E 확인 — 블록 닫을 것 |
| **2** | Wave F Proposal §5 (a/b/c) | **(a) accept.** §5.1 두 갈래 · D8′ 비통제 수집 금지 유지 · §8 요약 · 이력 v0.3/v0.4 |
| **3** | Wave F Confirm §2 — 「형식·크기는 과목이 정한다」 문단 | **승인.** **사실 기술이지 새 보장이 아니다** — 빼지 말 것 |
| **4** | 다음 Wave | **(a) 카탈로그 +1 한 종**이 1순위. `text.rank` 등 자체 생성·라이선스 0 |

### 다음 작업 우선순위

| 순위 | 무엇 | 조건 |
|---|---|---|
| **(a)** | **Step 2 — 카탈로그 +1 한 종** | 한 PR · base `main` · **52 일괄 금지** · `image.classify@1` 무회귀 필수 · 능력 설명에 **「하지 않는 일」** 경계 (#112 라우팅 혼선 교훈) |
| (b) | Step 3 — capreq `chat.html` 표시 개선 | Playwright 등 **새 의존성 = Proposal 먼저** |
| (c) | Step 4 — D4 조회 인증 · `tool.plan`/`tool.action` · LLM-as-Node · agent mesh · contest 태그 재발행 | **Proposal 만. 구현 금지** |

**열린 PR 이 0 이므로 (a) 는 Proposal → (master 부재 시) 그대로 구현해도 된다.**
카탈로그 +1 은 #110 에서 확립된 패턴이고 **새 제품 주장·DDL 이 없다.**

### Don't Do

절대규칙 8개 · `git add -A` · `git config` 변경 · force push · main 직접 머지 ·
migrate/seed 임의 실행 · `.env` 수정 · contest 태그 이동 · stacked PR.
```
