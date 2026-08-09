# Capability Network (CapNet) — 통합 기획서

**문서 버전:** v4.7 (사이클 폐쇄 · Capability = 인터페이스 계약)  
**작성일:** 2026-07-31 · **개정:** 2026-08-09  
**기반:** v4.4 + §2.5·§14 문헌·§15 완료=최소 증서  
**제품명:** Capability Network (CapNet) · 약어 CN  
**상위:** ai-agent-store (첫 제품 = CapNet)  
**스키마:** [`docs/spec/schema.sql`](../spec/schema.sql) (**v4.4** — 이번 개정은 DDL 변경 없음)  

> v4.3: 호환 행렬 자체도 rank 규칙에 묶여, 정책 독성 INSERT가 불가.  
> v4.4: PASSED 게이트·task 도메인 하한까지 DB 사슬로 닫힘. Phase 1 스키마 동결 후보.  
> **v4.5: 사슬은 Capability → Agent → `weights_sha256`만. 교체는 게이트+증적. 완료=최소 증서.**
> **v4.6: 계약은 품질 하한을 보장한다. 등가성은 보장하지 않고 관측만 한다 (§7.1 · SD-009).**
> **v4.7: Capability = 인터페이스 계약. 골든셋 게이트는 선택적 품질 프로파일(§4.4). 사이클 폐쇄.**

------------------------------------------------------------------------

# 0. v4.4 → v4.5 패치 (문서만)

| # | 결함 | 수정 |
|----|------|------|
| D-IIS | Capability를 이름·별칭으로 취급하면 구현 교체가 증적 없이 일어남 | §2.5. **Model Identifier / alias 계층을 사슬에 넣지 않음** |
| D-PRV | “실행 기록”을 새 테이블·UI로 오해 | Execution Provenance = `assignment` / `gate_run` / Agent 해시 / Node 스냅샷의 **개념 이름** |
| D-DONE | 텔레메트리 실패를 완료 실패와 동일시 | §15. 완료 = 최소 증서. `audit_log` 실패 ≠ 무조건 `FAILED` |

스키마 v4.4 동결 후보는 유지. `node_credential` 등 DDL은 별도 마이그레이션 이슈.

------------------------------------------------------------------------

# 0a. v4.3 → v4.4 패치

| # | 결함 | 수정 |
|---|------|------|
| P14 | `gate_run` PASSED를 `runner_node_id` 없이 / non–gate-runner로 기록 가능 | `runner_node_id NOT NULL` + `runner_is_gate_runner=true` → `node(id, is_gate_runner)` 복합 FK (`is_gate_runner⇒team`은 기존 CHECK) |
| P15 | `agent_capability.gate_status='PASSED'`를 `gate_run_id` 없이 설정 가능 | `gate_run_passed` 증서 + `PASSED⇔gate_run_id` CHECK + 복합 FK (agent·capability·PASSED 일치) |
| P16 | `capability.trust_domain_min`이 Task에 미반영 | `domain_min_compatible` + task에 `capability_trust_domain_min` 스냅샷 + 복합 FK |

**검증 13–15:** runner 없는/비러너 PASSED · 근거 없는 PASSED · min=team인데 public Task → 거부.

사슬:

```text
gate_run (team gate-runner만) → gate_run_passed → agent_capability PASSED → agent_capability_passed → assignment
task.trust_domain ≥ capability.trust_domain_min (domain_min_compatible)
```

------------------------------------------------------------------------

# 0a. v4.2 → v4.3 패치

| # | 결함 | 수정 |
|---|------|------|
| P12 | `domain_compatible`/`tier_compatible`에 규칙 위반 행을 넣으면 12종 FK가 **잘못된 정책을 신뢰** | 행렬에 rank 컬럼 + `rank` 테이블 복합 FK + `CHECK` (privacy/tier 순서) |
| P13 | “규칙은 DB에” 철학의 유일한 예외였던 행렬 | 예외 제거. rank 위조 INSERT도 FK로 거부 |

**검증 11–12:** `('team','public')`, `('L','S')` 행렬 INSERT 거부.

------------------------------------------------------------------------

# 0a. v4.1 → v4.2 패치

| # | 결함 | 수정 |
|---|------|------|
| P8 | assignment의 task/capability 스냅샷이 원본에 미연결 → team Task를 public/S로 **거짓 기재**해도 행렬만 맞으면 INSERT 성공 | `UNIQUE (task.id, capability_id, trust_domain)` + `UNIQUE (capability.id, compute_tier)` ← assignment 복합 FK |
| P9 | 재할당 시 이전 스냅샷 복사로도 동일 버그 | 원본 FK가 복사본을 거부(원본과 다르면 실패) |
| P10 | `agent_node_ready` 가중치 일치가 주석(앱) 의존 | READY = `agent_node(…, weights_sha256_seen)` ∩ `agent(id, weights_sha256)` 이중 FK |
| P11 | 바인딩 중 가중치 교체·드리프트 | live READY/assignment 있으면 `UPDATE agent.weights_sha256` FK 거부 → §7.3 “교체 전 무효화”를 절차로 강제 |

**추가 검증 (7–10):**  
(7) task=team인데 스냅샷 public (8) cap=L인데 스냅샷 S  
(9) seen 해시 ≠ agent 해시 → READY 불가 (10) READY/lease 중 가중치 UPDATE 거부

------------------------------------------------------------------------

# 0a. v4.0 → v4.1 패치 (리뷰 반영)

| # | 결함 | 수정 |
|---|------|------|
| P1 | `compute_tier` TEXT 비교 시 `'L' <= 'S'`가 **참** (알파벳 역순) | `compute_tier_rank` + `tier_compatible` 행렬. 정렬은 **rank 숫자** |
| P2 | §12 라우팅 불변식이 앱에만 있음 → PENDING·public·S tier로 할당 가능 | `agent_capability_passed` / `domain_compatible` / `tier_compatible` / `agent_node_ready` + **assignment 복합 FK** |
| P3 | Node를 public으로 강등(TOCTOU)해도 lease 유지 | `UNIQUE (node.id, trust_domain, compute_tier_max)` ← assignment FK. 강등 시 FK 거부 |
| P4 | §5.1 `⊇` 문장이 tenant→public을 허용하는 것처럼 읽힘 | **privacy_rank** 규칙으로 재정의 (아래 §5.1) |
| P5 | 10주에 고객 검증 0건 | 주 1–2에 인터뷰 3–5건 (기술과 병렬) |
| P6 | work_units에 전력 항 없음 | `energy_wh` 컬럼 예약. **소급 계측 불가** 명시 |
| P7 | S tier 정의만 하고 Phase 1에서 안 건드림 | Phase 1은 **스키마·행렬에 S 포함**. 하드웨어 있으면 주 8 **S smoke 1건**(실패해도 Kill 아님) |

**라우팅 위반 6종 (DB가 거부해야 함):**  
(1) PENDING Agent (2) tenant Task → public Node (3) L Capability → S Node  
(4) TEXT 함정 `'L'<='S'` (5) live lease 중 Node public 강등 (6) unbound/해시 불일치 Node

------------------------------------------------------------------------

# 0b. v3.2 → v4.0 변경 요약 (유지)

| # | 변경 | 논리·기술 근거 |
|---|------|----------------|
| V1 | **쐐기(Wedge) 명시**: 실시간 범용 AI가 아니라 **배치·비동기·데이터 거주지(자기/팀 Node)** | 클라우드 비전 API는 레이턴시·가격에서 이김. 경로 특성(큐·할당·로드)상 대화형 경쟁 불가(v3.2 §6) |
| V2 | 첫 Capability를 `image.analysis` → **`image.classify@1` (closed-set)** 로 재명명 | “분석”은 출력 계약이 모호. 채점 가능한 분류만 추상화 증명에 적합 |
| V3 | **Compute Tier (S/M/L)** — Capability·Node에 계층 | 단일 Node 완결 ↔ 폰/저VRAM 유휴 비전 긴장 해소(v3.2 §14.2) |
| V4 | **Trust Domain**: `team` → `tenant` → `public` | 외부 개방 전에 “자기 조직 플릿” 중간 단계. 법무·격리 부담을 단계화 |
| V5 | **Kill / Pivot 기준** (Phase 1 종료 시) | 게이트 실패·편차 초과·콜드스타트 비경제가 “학습”이지 실패가 아님을 운영 규칙으로 고정 |
| V6 | **경제 초안을 P3에서 P2로 당김** — 내부 `work_units` 계측만(정산 없음) | 보상 없는 외부 Node는 안 켬. 다만 **원가 관측 없이** P3 인센티브를 설계할 수 없음 |
| V7 | **이중 트랙**: Proof Track / Product Track | 증명 하네스와 제품 경로를 섞지 않음(requested_agent_id는 계속 관리자 전용) |
| V8 | **참고 스택·위협 모델·10주 실행 계획** | 기획 → 구현 핸드오프 |

**계승(변경 없음):** safetensors 강제, team gate-runner, 골든셋 게이트, ASSIGNMENT+활성 lease 유니크, Core-only claim, heartbeat 우선 만료, allowlist 입력, Petals 비샤딩.

------------------------------------------------------------------------

# 1. 한 줄 정의 (v4.0)

**Capability Network (CapNet)**는  
사용자가 **능력만 요구**하면, Core가 **신뢰 도메인 안에 등록된 Node**로 라우팅하고,
그 Node의 Agent가 Task를 **단일 노드로 완결**한 뒤 **Core를 통해** 결과를 돌려주는 실행 계층이다.
잘못된 조합은 앱이 아니라 **DB가 거절**하고, 누가 무엇으로 실행했는지 **증적이 남는다**.

**사이클 (v4.7 — 구현 완료):**

```text
사용자 → Core        능력 요구 (Agent·Node를 지정하지 않는다)
        Core 워커     신뢰 도메인·티어가 맞는 Node로 배정
Node  → Core         자기 배정을 가져가 실행 (outbound. NAT 뒤에서도 동작)
Node  → Core         결과 반환
사용자 → Core        결과·증적 조회
```

**사용자는 Node 주소를 모른다.** Node는 Core가 배정하지 않은 실행을 거부한다(403).

**계약이 보장하는 것 / 보장하지 않는 것:**

| | 내용 |
|---|---|
| **보장** | 승인한 신뢰 도메인 밖 Node로 **라우팅되지 않는다** (DB FK 강제) |
| **보장** | 어느 Node·Agent·가중치로 언제 실행됐는지 **증적이 남는다** |
| **보장하지 않음** | Node가 데이터를 남기지 않는다 — 추론은 평문을 요구한다. TEE/HE 없이는 원리적으로 불가 (§5.2) |
| **보장하지 않음** | 두 Agent가 같은 답을 낸다 — 품질 등가는 **선택적 프로파일의 관측값** (§4.4) |

장기 비전은 개인 기기 유휴 자원의 공유다.  
**제품 진입점은 그 비전이 아니다.** 진입점은:

> **데이터가 공공 클라우드 추론 API로 나가기 어려운 조직·개인이,  
> 자기가 통제하는 Node 플릿 위에서 “능력”만 호출하게 한다.**

클라우드 범용 API와 가격·속도 경쟁을 하지 않는다.

------------------------------------------------------------------------

# 2. 전략: 왜 이 구조인가

## 2.1 네 가지 문제 (연결만이 아님)

| 축 | 문제 | v4.0 대응 |
|----|------|-----------|
| 연결 | NAT·간헐 Node | outbound WS, lease, heartbeat(v3.2) |
| 품질 등가성 | 같은 이름 ≠ 같은 결과 | 계약 + 골든셋 게이트 + 증명 모드 |
| 신뢰 | 제3자 디스크에 입력이 남음 | Trust Domain 단계화, PII/allowlist, P3 법무·격리 |
| 경제성 | 전기료 즉시 / 보상 지연 | 팀→테넌트 플릿 먼저, 공공 유휴는 원가 관측 후 |

## 2.2 싸워서는 안 되는 전장

| 전장 | 승자 | 우리 |
|------|------|------|
| 실시간 챗·범용 비전 API | 하이퍼스케일러 | **진입 금지** |
| 초저가 이미지 라벨 (공개 데이터) | 클라우드 API | **진입 금지** |
| 모델 샤딩 협력 추론 | (Petals류, 대역폭 한계) | **비채택** (단일 Node 완결) |

## 2.3 들어갈 전장 (쐐기)

**배치·비동기 Capability 실행 + 데이터 거주지 통제.**

예시(초기 고객 가설, 검증 대상):

- 사내 GPU가 이미 있는데, 모델마다 잡 스크립트가 파편화됨  
- 규정상 원본을 외부 API로 못 보냄 (합성·비식별 데이터로 MVP 증명 후, 테넌트 단계에서 확대)  
- 게이트를 통과한 Agent를 `image.classify@1`로 **교체**하는 비용이, 잡 스크립트 파편화보다 쌈. 교체는 금지되지 않는다. **몰래 바꾸지 못하고**, 게이트+증적이 남는다 (§2.5)  

**가치 제안 한 줄:**  
*같은 계약을 통과한 Agent는 교체할 수 있다. 단, 게이트를 다시 통과하고 실행 증적이 남아야 한다.*
**교체가 보장하는 것은 계약이 정한 품질 하한이지 동일한 출력이 아니다** (§7.1 v4.6 · §2.5).

## 2.4 비전과의 정합 (유휴 공유)

유휴 공유는 **Phase 4+ 공공 Trust Domain**의 목표다.  
그 전에 반드시 거쳐야 할 계단:

```text
① 팀 플릿에서 추상화 증명 (Phase 1)
② 테넌트(자기 조직) 플릿에서 제품 가치 확인 (Phase 2–3)
③ 원가·격리·법무 통과 후 초대/공공 Node (Phase 4+)
```

“처음부터 전 세계 폰을 켠다”는 **경제·신뢰 모두에서 기각**이다 (등록 ≠ 가용).

## 2.5 Interface–Implementation Separation

Capability를 **이름·별칭**으로 취급하면, 같은 호출 뒤에 다른 구현이 끼어든다.  
이는 특정 벤더를 겨냥한 공격 서사가 아니라, **별칭 · 라우터 · 시간 드리프트**가 있는 실행 구조에서 반복되는 플랫폼 문제다 (§14).

**사슬 (이것만):**

```text
Capability (채점 가능한 계약)
  → Agent (구현 단위)
    → weights_sha256 (로드한 바이트)
```

**넣지 않는 것:** Model Identifier, 모델 별칭, “같은 이름 = 같은 모델” 계층.  
별칭을 가운데 끼우면 사슬이 다시 이름으로 붕괴한다.

**교체 규칙:** 교체 자체가 금지인 것은 아니다.  
허용되는 교체는 다음을 동시에 만족한다.

1. 새 Agent가 해당 Capability 게이트를 **통과** (`gate_run` → `gate_run_passed` → … → assignment FK)
2. 실행마다 **Execution Provenance**가 남음

**Execution Provenance**는 새 테이블이 아니다. 이미 있는 행·컬럼의 개념 이름이다.

| 증적 | 어디에 있나 |
|------|-------------|
| 어느 Task를 누가 받아 끝났는가 | `assignment` (lease → SUCCEEDED/FAILED …) |
| 그 Agent가 그 계약에 합격했는가 | `gate_run` + 게이트 사슬 |
| 어떤 바이트를 로드했는가 | `agent.weights_sha256` (`agent_node_ready`와 일치) |
| 어느 신뢰·티어 Node였는가 | assignment의 Node 스냅샷 + 복합 FK |

**MVP 범위:** Provenance UI·대시보드가 아니다.  
**DB 제약으로 위조할 수 없는 최소 증적**이 남는 것이다. 화면은 그 다음이다.

§2.1의 “같은 이름 ≠ 같은 결과”와 §2.3 쐐기는 여기서 만난다.  
진입 가치는 “아무 모델이나 갈아끼우기”가 아니라 **계약·게이트·증적이 붙은 교체**다.

------------------------------------------------------------------------

# 3. 핵심 개념 (v4.0 확장)

| 개념 | 정의 |
|------|------|
| **Capability** | `code@version` + 스키마 + `output_kind` + 골든셋 + **`compute_tier`** + **`trust_domain_min`** |
| **Agent** | safetensors 가중치 + 매니페스트. **능력별** 게이트 통과 시에만 라우팅 |
| **Node** | 실행 장치. `provision_source` / **`trust_domain`** / **`compute_tier_max`** |
| **Assignment** | Task당 lease 이력. 활성 lease ≤ 1 |
| **Gate Run** | team gate-runner에서만 (`gate_run_passed` 증서 → PASSED). Task/Assignment 기계 재사용 |
| **Trust Domain** | `team` / `tenant` / `public` — **privacy_rank**(team=3 > tenant=2 > public=1) |
| **Compute Tier** | S=1 / M=2 / L=3 (**숫자 rank**). Capability.rank ≤ Node.max_rank |
| **Proof Track** | 관리자 키 + `proof_run_id` + A/B 강제 |
| **Product Track** | 사용자·테넌트가 Capability만 호출 (`requested_agent_id` 금지) |
| **Execution Provenance** | 새 테이블이 아님. `assignment` + `gate_run` + `weights_sha256` + Node 스냅샷 (§2.5) |

```text
Capability(계약, tier)
    └─ gate PASSED ── Agent
                         └─ Assignment ── Node(trust_domain, tier_max ≥ 요구)
```

------------------------------------------------------------------------

# 4. Capability 설계: 이름보다 계층

## 4.1 MVP 첫 계약

| 항목 | 값 |
|------|-----|
| code | **`image.classify`** |
| version | `1` |
| output_kind | `closed_set_labels` |
| compute_tier | **M** (팀 GPU 가정; S로 내리면 폰 경로 사전 검증 가능) |
| mvp_eligible | true |
| 입력 | allowlist 데이터셋 ID만 (자유 업로드 없음) |

`image.analysis` 명칭은 폐기한다. 분석·캡션·박스는 Phase 3+ `structured`/`freeform`으로 분리한다.

## 4.2 Compute Tier 규약

| Tier | 의도 | Node 예 | 비전 연결 |
|------|------|---------|-----------|
| **S** | ≤수억 파라미터급, CPU/NPU/저VRAM | 폰, 노트북 iGPU | 장기 “유휴 폰”의 **실제 입구** |
| **M** | 중소형 비전 분류 | 8–12GB급 | MVP 기본 |
| **L** | 대형 비전/멀티모달 | 24GB+ | 팀·테넌트 전용, 공공 유휴와 분리 |

**라우팅 규칙 (구현):** `compute_tier_rank(capability) <= compute_tier_rank(node.max)`  
**금지:** TEXT 문자열 비교 (`'L' <= 'S'`는 SQL에서 참 → 대형 모델이 폰으로 감).  
DB는 `tier_compatible` 룩업만 허용한다.

## 4.3 골든셋 (계승 + 운영 KPI)

v3.2 §6을 유지한다.

| KPI | MVP 기준 |
|-----|----------|
| Agent 간 골든셋 점수 편차 | **&lt; 0.05** |
| 절대 점수 | `golden_metrics` 이상 |
| 게이트 통과율 | **20–80%** (난이도 적정성) |
| warm 경로 Task | &lt; 10초 (목표, 경쟁 지표 아님) |

**게이트 2개 실패 = 유효한 실험 결과.**  
“품질 정규화 없이는 추상화 불가” → 로드맵 pivot (아래 Kill 기준).

------------------------------------------------------------------------

## 4.4 Capability = **인터페이스 계약** (v4.7 재정의)

> **v4.6까지 Capability는 "채점 가능한 계약"이었다.** 골든셋과 통과 기준이 정의의 일부였고,
> 그래서 채점 불가능한 능력(대화·생성·임베딩)은 애초에 표현할 수 없었다.
> **원래 기획 취지(§1)는 범용 실행 계층이었는데** 채점 기계가 그 위에 자라 서사를 점령했다.
> 근거: 이 재정의는 실패가 아니라 §1에서 나왔다.

**Capability가 규정하는 것 (필수):**

| 항목 | 내용 |
|------|------|
| 입출력 스키마 | 무엇을 받고 무엇을 돌려주는가 |
| 전처리 계약 | 게이트와 제품이 동일해야 한다 (D3) |
| 실행 조건 | `compute_tier` · `trust_domain_min` · 입력 allowlist |

**여기까지가 모든 Capability의 공통이다.** 채점 가능성을 요구하지 않으므로
분류·요약·임베딩·대화 어디에도 붙는다.

### 4.4.1 품질 프로파일 (선택)

채점 가능한 능력에는 **품질 프로파일**을 덧붙일 수 있다. `image.classify@1`이 그 첫 사례다.

```text
Capability (인터페이스 계약)          ← 필수
  └ 품질 프로파일 (골든셋·게이트)      ← 선택
```

프로파일이 붙으면 게이트 사슬(`gate_run` → 증서 → 할당 자격)이 작동하고,
안 붙으면 인터페이스 적합성만으로 등록된다.

**프로파일의 알려진 한계 — 계약 핵심이 아니라 이 부속 기능의 한계다:**

| 한계 | 내용 |
|------|------|
| 표본 | 유한 골든셋. n=300에서 SE≈0.026 |
| 분포 | 선언한 데이터셋 밖에서는 보장이 성립하지 않는다 |
| 게이밍 | 골든셋이 정적·공개라 의도적 과적합을 막을 수 없다. **회전 은닉 프로브(Phase 2)가 해법** |
| 등가 | 하한형 게이트는 쌍별 편차를 유계로 만들 수 없다 (SD-009). 등가는 관측값 |

이 한계들은 `golden_metrics.guarantee` 에 기계가 읽는 형태로 박아 두었다.
문서 각주가 아니라 계약의 일부다.

### 4.4.2 임계값의 근거

| 값 | 근거 |
|----|------|
| `min_per_class_recall` **0.10** | **유도.** 균등 C클래스에서 무작위의 클래스별 재현율은 `1/C`. 모든 선언 라벨에서 무작위보다 나아야 한다. 이 항목이 없으면 클래스 2개를 버린 모델이 통과한다 (m=8 → acc 0.80 · f1 0.711, 대수·시뮬레이션 확인) |
| `min_macro_f1` **0.65** | m≥7 강제 (6/10=0.60 < 0.65). 클래스 간 균형 |
| `min_accuracy` **0.68** | **선언된 서비스 수준.** 유도되지 않는다. 허용 구간 (0.447, 0.910]은 실측 — 붕괴 모델 0.447, 무사전학습 32×32 실현 최대 0.910. 실사용자 요구가 생기면 재선언한다 (SD-004 대체) |
| 편차 | **강제 불가.** 하한형 게이트의 상한은 `1 − min_accuracy` 로 항등식이며 제약이 아니다. 숫자를 두지 않고 관측만 기록 |

------------------------------------------------------------------------

# 5. Trust Domain과 데이터

## 5.1 도메인 정의

| Domain | privacy_rank | Node 주체 | 입력 데이터 | 전제 |
|--------|--------------|-----------|-------------|------|
| **team** | **3** (가장 사적) | 프로젝트 팀 | 합성·공개·팀 더미 only | Phase 1 |
| **tenant** | **2** | 고객/조직 플릿 | 조직 정책 데이터 | Phase 2–3 |
| **public** | **1** (가장 개방) | 제3자 유휴 | 별도 등급화 전 **금지** | Phase 4+ |

**할당 불변식 (문서 = DB `domain_compatible`):**

> `privacy_rank(node) >= privacy_rank(task)`  
> 즉 Node는 Task가 요구하는 수준 **이상으로 사적**이어야 한다.

| Task domain | 허용 Node | 금지 |
|-------------|-----------|------|
| team | team만 | tenant, public |
| tenant | team, tenant | **public** |
| public | team, tenant, public | — |

`team ⊂ tenant ⊂ public`은 “참여자 집합이 커진다”는 **서사**이지, 할당 연산자 `⊇`가 아니다.  
**데이터가 어디까지 나가도 되는지는 privacy_rank 규칙만 따른다.**

## 5.2 데이터 정책 (강제 지점 — v3.2 계승·강화)

| 정책 | 강제 |
|------|------|
| MVP 자유 업로드 없음 | allowlist `datasetId`만 |
| safetensors only | DB CHECK + 등록 시 sha256 |
| gate-runner = team | `is_gate_runner ⇒ provision_source=team` |
| fileToken 수명 = lease | 만료 후 GET 거부 |
| 다운로드 이후 통제 불가 | 문서·법무에 명시. **토큰 ≠ 면책** |

## 5.3 위협 모델 (요약)

| 위협 | MVP 완화 | 이후 |
|------|----------|------|
| Pickle RCE | safetensors | — |
| 게이트 조작 | team gate-runner FK + `gate_run_passed` 사슬 (v4.4) | — |
| 이중 할당 | 활성 lease UNIQUE | — |
| 가중치 드리프트 | sha256_seen | — |
| 악성 연산·OOM | **미완화**(팀 Node 신뢰) | cgroup·timeout·max tensor (P3 진입) |
| 입력 유출 to public | domain 분리, public 미개방 | 법무·암호화·TEE 검토(연구) |

------------------------------------------------------------------------

# 6. 시스템 구조 (계승)

```text
CLI / 나중 UI ──REST──► Core (Registry, Queue, Files, Gate orch.)
                              │
                              │ Assignment + fileToken (WS push)
                              ▼
                     Node Runtime (outbound WS)
```

| 규칙 | 이유 |
|------|------|
| Node → Core outbound WS | NAT |
| Core worker만 큐 claim | 이중 디스패치 방지 |
| 모델 비샤딩 | Petals형 대역폭 함정 회피 |
| 게이트 = team runner | 신뢰 경계 |

상태 전이·heartbeat 우선·늦은 결과 폐기는 **v3.2 §9 그대로**.

------------------------------------------------------------------------

# 7. MVP (Phase 1) — 증명 트랙

## 7.1 증명 대상 (v4.6 재정의 — SD-009)

**Capability 계약이 품질 하한을 보장하는가** (E2E는 전제 조건).

> **v4.5까지는 "추상화가 성립하는가"였고 4번이 `점수 편차 < 0.05`였다.**
> 2026-08-09 홀드아웃 실측에서 이 조건은 **반증됐다** (최선 0.0967, 임계의 약 2배).
> 원인은 모델이 아니라 계약 설계다 — 통과 기준이 하한(`acc ≥ t`)인데 등가 기준은
> 구간(`|Δ| ≤ d`)이라, **하한형 게이트는 쌍별 편차를 구조적으로 유계로 만들 수 없다.**
> 따라서 등가성을 계약 조건에서 내리고 **관측값**으로 격하한다.
> 근거·경위: `docs/ops/phase1-verdict.md` §4.6.5 · §6.1.1 · SD-009.
>
> **이 변경은 기준을 실패한 뒤에 이루어졌다.** 그 사실을 여기 남긴다.
> 대신 4번을 더 약한 조건으로 바꾸지 않고, **새로 반증 가능한 조건**으로 교체했다.

통과:

1. `image.classify@1` + 골든셋 G  
2. Agent A, B가 **해당 능력**에 대해 PASSED  
3. 증명 모드로 A/B 교체 할당  
4. **게이트 통과가 하한을 예측한다** — 게이트에 쓰이지 않은 별도 홀드아웃에서도
   통과 Agent **전원**이 하한(`min_accuracy` ∧ `min_macro_f1` ∧ `max_invalid_rate`)을 유지  
5. Product Track에서는 Agent 선택 UI/필드 없음  

**계약이 보장하는 것과 보장하지 않는 것:**

| | 내용 |
|---|---|
| **보장한다** | 통과한 Agent는 계약이 정한 품질 **하한**을 만족한다. 그 사실에 DB 증서가 남는다 |
| **보장하지 않는다** | 통과한 두 Agent가 **같은 답**을 낸다. 통과자 사이의 점수 폭은 계약이 제한하지 않는다 |

등가성(`|Δacc|`, `label_agreement`)은 **측정해서 보고하되 판정에 쓰지 않는다.**
등가를 계약으로 보장하려면 통과 기준이 하한이 아니라 **폭이 정해진 구간**이어야 하며,
그것은 별도 Capability 버전(`@2`)의 설계 문제다.

## 7.2 Kill / Pivot 기준 (Phase 1 종료 시 의무 판정)

| 결과 | 판정 | 다음 |
|------|------|------|
| **하한 유지**(§7.1-4) ∧ 통과율 20–80% | **Go** | Phase 2 (테넌트 설계) |
| 통과율 &gt; 80% + 편차 큼 | 골든셋 **너무 약함** | 계약 강화 후 재실험 (구현 확장 금지) |
| 통과율 &lt; 20% | 골든셋 **너무 강함** 또는 모델군 부적합 | 메트릭·티어 재설정 |
| A만 통과, B 반복 실패 | **추상화 실패(현 계약)** | 단일 벤더 고정 제품으로 pivot **또는** 계약 재정의 |
| 둘 다 통과하나 점수 폭이 큼 | **계약이 등가를 보장 못 함** (v4.6에서 판정 축 아님) | 관측값으로 기록. 등가가 필요하면 `@2`에서 구간형 통과 기준 |
| warm도 &gt; 30s 만성 | 상주 정책·티어 재검토 | 하이브리드 스케줄 개편 |
| 팀이 10주 내 9번(증명) 미도달 | 실행 역량 부족 | 범위 재축소(게이트 시뮬레이터 등) |

**실패를 숨기지 않는 것이 v4.0의 운영 원칙이다.**

## 7.3 MVP에서 제외 (v3.2 + α)

```text
❌ 실시간 UI / 자유 업로드
❌ public Node / 보상 토큰
❌ 자동 재할당 (스키마만 유지)
❌ freeform·생성형 출력
❌ 외부 개발자 셀프서브 온보딩
```

------------------------------------------------------------------------

# 8. 경제 모델 (정직한 초안)

## 8.1 원칙

1. **공공 유휴에 보상 없이 의존하지 않는다.**  
2. Phase 1은 **비용 센터**(학습).  
3. Phase 2부터 **원가를 숫자로** 남긴다.  
4. 정산·토큰 경제는 Phase 5+ — 그 전에 **내부 work_units 계측만**.

## 8.2 work_units (Phase 2 계측, 정산 없음)

```text
work_units ≈ f(compute_tier, duration_s, vram_gb_peak, energy_wh?)
```

- `duration_ms` / `vram_mb_peak`: assignment에 기록 (P2부터 채움)  
- **`energy_wh`(전력):** 스키마에 예약. **미계측 구간은 소급 불가** — P2 시작 시점부터만 의미 있음  
- 용도: “Capability 1000건 ≈ GPU·전력 원가 X” 리포트. 과금은 계약 문제.

## 8.3 예상 수익 논리 (가설 — 검증 대상)

| 단계 | 누가 돈/예산을 내는가 | 무엇에 |
|------|----------------------|--------|
| P1 | 팀 R&D | 증명 |
| P2–3 | 조직 IT/보안 | **거주지 준수 + 계약형 교체** 운영비 |
| P4+ | (미정) Node 제공 보상 ↔ 요청자 수수료 | 원가 데이터 없이는 설계 금지 |

클라우드보다 싸서가 아니라, **못 보내는 데이터** 또는 **이미 산 GPU의 가동률**이 가치다.

------------------------------------------------------------------------

# 9. 로드맵 (이중 트랙)

| Phase | Proof Track | Product Track | 진입 조건 |
|-------|-------------|---------------|-----------|
| **1** | `image.classify@1` A/B 추상화 판정 | CLI만, team domain | — |
| **2** | spot-check, 재할당 가동 | **tenant** domain 설계, work_units 계측, 최소 UI | P1 Go |
| **3** | 다 Capability(S tier 1건 추가) | 첫 테넌트 플릿 파일럿 | 격리 초안 + 법무 킥오프 |
| **4** | — | invited Node, 인센티브 초안 | **격리 강제 + 법무 완료** |
| **5** | quorum/평판 | public 제한 개방 | 검증 체계 |
| **6** | — | 경제·정산 | 원가 모델 안정 |

UI는 Phase 2 — “검증에 불필요”였던 v3.2 판단을 유지하되, 테넌트 파일럿부터는 **호출면**이 필요하다.

------------------------------------------------------------------------

# 10. 참고 아키텍처 (핸드오프)

선택이 아닌 **기본안**. 교체 가능하되 이유 없이 바꾸지 않는다.

| 계층 | 기본안 | 이유 |
|------|--------|------|
| Core API | Python 3.12 + FastAPI | WS·비동기·팀 생산성 |
| DB | PostgreSQL 16 | v3.2 제약·부분 인덱스·SKIP LOCKED |
| 큐 | DB claim (FOR UPDATE SKIP LOCKED) | 외부 큐 도입 전 단순 |
| Object | 로컬/S3호환 | fileToken 발급 |
| Node Runtime | Python + 지정 추론 백엔드 | safetensors 로드 |
| 관측 | AUDIT_LOG + 구조화 로그 | 증명·원가 |

OpenAPI는 **Product Track 공개 API만** 먼저 고정. Proof 전용 엔드포인트는 별도 태그.

------------------------------------------------------------------------

# 11. API 스케치 (v4.0 델타)

v3.2 API에 추가·변경:

```http
POST /api/capabilities          # + compute_tier, trust_domain_min
POST /api/tasks                 # capability=image.classify@1, trust_domain, datasetId
POST /api/proof-runs            # 관리자 — A/B 번들 (기존)
GET  /api/metrics/work-units    # Phase 2+ — 정산 아님
```

Task 예:

```json
{
  "capability": "image.classify@1",
  "trust_domain": "team",
  "input": { "datasetId": "golden-ic1", "caseId": "case-017" }
}
```

------------------------------------------------------------------------

# 12. 데이터 모델 (v4.4)

상세: [`docs/spec/schema.sql`](../spec/schema.sql)

| 구성 | 요지 |
|------|------|
| rank + 호환 행렬 | 정직한 오조합 차단. **행렬 행도 rank+CHECK에 묶임 (v4.3)** |
| `gate_run_passed` / `agent_capability_passed` | 게이트·라우팅 PASSED 증서 (v4.4 사슬) |
| `domain_min_compatible` | Task 도메인 ≥ Capability `trust_domain_min` (v4.4) |
| **task / capability 복합 UNIQUE** | 스냅샷이 **원본 행**과 일치해야 함 (v4.2) |
| **node 복합 UNIQUE** | 강등 TOCTOU (v4.1) · gate-runner 복합 UNIQUE (v4.4) |
| **agent_node_ready ↔ agent.weights_sha256** | 드리프트·교체를 DB가 차단 (v4.2) |
| 계측 | `duration_ms`, `vram_mb_peak`, `energy_wh` |

**세 층:**  
(A) 행렬 = “이 조합이 정책상 허용인가”  
(B) 원본 FK = “스냅샷이 이 Task/Capability/Node/Agent의 **실제 값**인가”  
(C) 게이트 사슬 = “PASSED가 **team gate-runner에서 나온 실측 run**인가”

(A)+(B)만 있으면 근거 없는 PASSED가 통과한다. (A)+(B)+(C)여야 한다.

liveness(heartbeat)만은 시계열이라 FK로 못 막으며 Core 스캐너 담당.

------------------------------------------------------------------------

# 13. 10주 실행 계획 (Phase 1)

| 주 | 기술 트랙 | 시장 트랙 (병렬, 일정 비중 작음) |
|----|-----------|----------------------------------|
| 1 | DB **v4.4** 적용, `image.classify@1`+골든셋, **라우팅·게이트 위반 SQL 테스트** | 가설 문장 확정, 인터뷰 대상 5명 리스트 |
| 2 | Agent 등록 + safetensors/sha256 | **고객·후보 인터뷰 3–5건** (거주지·배치·기존 GPU 가동률) |
| 3–4 | gate-runner + gate_run + `agent_capability_passed` 유지 경로 | 인터뷰 메모 → §2.3 가설 갱신 |
| 5–6 | Task/Assignment FK 스냅샷 + 큐/WS/heartbeat | — |
| 7 | allowlist 파일 + Agent A 추론 | — |
| 8 | Agent B + 증명 A/B. **가능하면 S-tier smoke**(없으면 스킵·기록) | — |
| 9 | §7.2 판정 + **인터뷰 요약을 같은 리포트에 첨부** | 시장 Go/모호/Kill 한 줄 |
| 10 | OpenAPI·버퍼 | — |

**주 9 기술 판정 없이 Phase 2 코드 금지.**  
시장 근거가 비어도 기술 Go는 가능하나, 리포트에 **“고객 대화 0건”이면 Product Track 착수 보류**로 적는다.

------------------------------------------------------------------------

# 14. 선행 사례와 포지션

제품 포지션 (기존):

| 비교 | 함의 |
|------|------|
| Petals | 샤딩 금지 → 우리는 스케줄링 분산 |
| DePIN GPU 마켓 | 등록 ≠ 가용 → 공공 유휴는 마지막 |
| 클라우드 비전 API | 가격·속도 비경쟁 → 거주지·계약 교체가 가치 |
| “AI 에이전트 스토어” 마케팅 | 스토어 UI보다 **계약 런타임**이 본제품 |

문헌 역할 (§2.5 · Provenance by Design의 외부 앵커). **구현 명세가 아니다.**

| 문헌 | CapNet에서의 역할 |
|------|-------------------|
| Sculley et al., 2015. *Hidden Technical Debt in Machine Learning Systems* | ML 운영 부채·숨은 결합. Capability를 이름만으로 두면 부채가 **플랫폼 구조**가 된다 |
| Chen, Zaharia, Zou, 2023. *How is ChatGPT’s behavior changing over time?* | 같은 API 이름 아래 **시간 드리프트**. 별칭 ≠ 동일 구현의 실측 사례 |
| Gao, Liang, Guestrin, 2024. *Model Equality Testing* (ICLR 2025) | 출력 등가성 검정 프레임. 골든셋·편차 임계의 문헌 앵커 (채점 공식의 복제는 아님) |
| Stanford CRFM, *Foundation Model Transparency Index* (FMTI) | 투명성 공시 기준. 우리는 공시 UI가 아니라 **실행 증적**으로 접근 |
| NIST, *AI Risk Management Framework* (AI RMF) | 위험 관리·거버넌스 어휘. §15 완료=증서와 정합하는 외부 언어 |

서지 (본문 인용용, 링크는 확인일 2026-08-06):

- Sculley, D. et al. (2015). Hidden Technical Debt in Machine Learning Systems. *NIPS 2015*. https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems
- Chen, L., Zaharia, M., & Zou, J. (2023). How is ChatGPT’s behavior changing over time? https://arxiv.org/abs/2307.09009
- Gao, I., Liang, P., & Guestrin, C. (2024). Model Equality Testing: Which Model Is This API Serving? *ICLR 2025*. https://arxiv.org/abs/2410.20247
- Stanford CRFM. Foundation Model Transparency Index. https://crfm.stanford.edu/fmti/
- NIST (2023). Artificial Intelligence Risk Management Framework (AI RMF 1.0). https://www.nist.gov/itl/ai-risk-management-framework

------------------------------------------------------------------------

# 15. 철학 (v4.0 · v4.5 추가)

1. 계약이 채점되지 않으면 Capability가 아니다.  
2. 추상화 증명은 스케줄러 기본 동작과 분리한다 (Proof Track).  
3. 유휴 공유는 비전이고, **거주지 통제형 플릿**이 제품 입구다.  
4. 티어로 하드웨어 다양성을 설계에 넣는다.  
5. 경제는 관측 다음에 온다.  
6. Kill 기준 없는 MVP는 프로젝트가 아니라 습관이다.  
7. **실행 기록이 없는 계산은 완료된 계산이 아니다.** (Provenance by Design)  
   - **완료** = 최소 증서: 해당 Task의 `assignment`(종료 상태) + `weights_sha256` + 그 Agent를 할당 가능하게 만든 `gate_run`(게이트 사슬).  
   - `audit_log`는 관측·텔레메트리다. 파티션 미생성·삽입 실패만으로 Task를 무조건 `FAILED`로 뒤집지 않는다. 최소 증서가 있으면 완료이고, 감사 로그 공백은 관측 공백으로 남긴다.

------------------------------------------------------------------------

# 16. 문서 이력

| 버전 | 내용 |
|------|------|
| v3.0–v3.1 | 복원·전제 교정 |
| v3.2 | 리뷰 병합, 스키마 S1–S11, 증명 모드·gate-runner |
| **v4.0** | 쐐기·티어·Trust Domain·Kill 기준·경제 초안·10주 계획 |
| **v4.1** | 티어 rank·라우팅 복합 FK·§5.1 privacy 규칙·인터뷰 병렬·energy_wh |
| **v4.2** | task/capability 스냅샷 원본 FK·가중치 READY 이중 FK |
| **v4.3** | 호환 행렬 rank FK + CHECK — 정책 독성 INSERT 차단 |
| **v4.4** | 게이트 사슬(`gate_run_passed`)·`trust_domain_min` 강제 — Phase 1 동결 후보 |
| **v4.5** | §2.5 IIS · Execution Provenance(개념) · §14 문헌 · §15 완료=최소 증서. **스키마 변경 없음** |
| **v4.7** | §1 사이클 폐쇄(Core 중개·Node 검증) · §4.4 Capability = 인터페이스 계약, 골든셋은 선택 프로파일 · 보장/불보장 명시. **스키마 변경 없음** |
| **v4.6** | §7.1 증명 대상 재정의 — 등가성을 계약 조건에서 **관측값**으로 격하, 4번을 「하한 예측」으로 교체. §7.2 Go 행·신규 행. 근거 SD-009. **스키마 변경 없음** |

**스키마 동결 제안:** v4.4를 Phase 1 DDL 기준으로 둔다. 이후 변경은 마이그레이션 이슈로만. 문서 v4.5 ≠ 스키마 v4.5.

유실 방지: Windows `C:\Users\wjsto\pjt\ai-agent-store`를 정본으로 두고, 원격 Git에 즉시 push. WSL 사용 시 **ext4 홈**에 두고 `/mnt/c`에만 두지 않는다.

------------------------------------------------------------------------

# 최종 정의

> **Capability Network (CapNet)**는 사용자가 능력만 요구하면 승인된 신뢰 도메인 안에서,  
> 신뢰 도메인 안의 Node에서 Task를 단일 완결하는 실행 계층이다.  
> MVP는 세상을 유휴 공유로 바꾸지 않는다.  
> **같은 계약을 통과한 Agent를 바꿔도 결과가 등가인지**를 팀 플릿에서 증명하고,  
> 그다음에야 테넌트 거주지 제품과 공공 유휴로 계단을 오른다.
