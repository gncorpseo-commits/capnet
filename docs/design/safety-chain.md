# 안전 사슬 — Node 등록에서 Agent 사용까지

> **제품 주장:** 「아무 기기·아무 Agent 나 돌리지 않는다. 등록·신원·계약·도메인·증적이
> 맞지 않으면 실행되지 않는다.」
>
> 골든셋 성적 평가는 **선택(품질 프로파일)** 이다 (D18·D20). 이 문서가 다루는 것은
> **안전·신뢰 검증**이며, 그것이 CapNet 의 핵심 기능이다.
>
> 작성: 2026-08-13 (`4f7f6d0` 기준) · 갭 분석은 **코드를 읽어 확인한 것만** 적는다.

---

## 1. 사슬 — 각 칸이 무엇으로 막히는가

기기가 등록되고 Agent 가 실행되기까지 통과해야 하는 관문이다.
**「누가 막는가」가 앱이면 약하고, DB 면 강하다.**

| # | 관문 | 무엇을 막나 | 막는 주체 | 상태 |
|---|------|-------------|-----------|------|
| 1 | Node 등록 | Node 가 자기 등급을 주장하는 것 | 앱 (`create_node` 는 관리 API) | ✅ |
| 2 | 게이트러너 자격 | 아무 기기나 채점자가 되는 것 | **DB** `CHECK (NOT is_gate_runner OR provision_source='team')` | ✅ |
| 3 | 등급 정합 | `public` 기기가 `team` 조달로 들어오는 것 | **DB** `ck_trust_provision_align` | ✅ |
| 4 | Node 신원 | 기기 사칭 | 앱 `verify_credential` (강제는 **플래그**) | ⚠️ 기본 꺼짐 |
| 5 | Agent 등록 | pickle 가중치 | 앱 `assert_safetensors` (형식 + `.pt/.pth` URI) | ✅ |
| 6 | Agent 신원 | 선언과 다른 가중치 | **DB** `agent_node_ready` 복합 FK — `weights_sha256_seen` 이 `agent.weights_sha256` 과 같아야 READY 진입 | ✅ |
| 7 | 실행 가중치 | 이름만 맞는 다른 파일 | Node `_resolve_weights` — **로컬 파일을 해싱해** 일치하는 것만 로드 | ✅ |
| 8 | 계약 | 계약을 못 지키는 Agent | 러너가 **실행해서** 검증 (B2 · `arch`·`max_params`·`input_schema`·`output_schema`·`preprocess`) | ✅ |
| 9 | 라우팅 | 승인 밖 도메인·티어 | **DB** 복합 FK (`domain_compatible`·`tier_compatible`) | ✅ |
| 10 | 실행 권한 | 배정 없는 호출 | Node `_my_assignment` → **403** | ✅ |
| 11 | 입력 | 비통제 수집 | D8′ — Core 중개·해시·MIME/preprocess 계약 | ✅ |
| 12 | 증적 | 「무엇이 돌았는지 모른다」 | **DB** `assignment` + `gate_run` + `audit_log` | ✅ |
| 13 | 폭주 | 조용한 무한 재시도 | **DB** `CHECK (attempt_no <= capability_max_attempts)` + 워커 종결 | ✅ |
| 14 | 관리 API | 익명 등록·증서 발급 | 앱 `_require(role)` (강제는 **플래그**) | ⚠️ 기본 꺼짐 |

**13칸 중 11칸이 서 있다.** 남은 둘(4·14)은 코드가 아니라 **기본값** 문제다.

---

## 2. 구멍

### G1 — 강제가 기본 꺼짐 (CI 가드는 **닫힘** · S1) 🟠

`REQUIRE_API_KEY` · `REQUIRE_NODE_CREDENTIAL` 기본값이 `0` 이다. `compose.prod.yaml` 이
둘을 `1` 로 뒤집지만 **선택 오버레이**다. 폐쇄망 조직이 `compose.yaml` 단독으로 올리면
**누구나 `team`·`L`·게이트러너 Node 를 등록**할 수 있다 (`0009` 가 적은 SD-010 상태 그대로).

**더 나쁜 것은 CI 가 이 불변식을 하나도 안 지킨다는 점이다.**

| 검사 | CI | 무엇을 보나 |
|------|----|-------------|
| `check_api_key` (23) · `check_node_credential` (17) | ✅ | **DB 계층** 키·증서 로직 |
| `check_enforcement` (20) | ✅ **S1 로 추가** | **앱의 강제 분기** — `_actor`·`_require`·`_authenticated_node`·`_assert_node_matches` 의 401/403 |
| `prod_room.sh` (14) | ❌ 수동 | HTTP 계층 종단 확인 (그대로 둔다) |

**회귀는 이제 CI 가 잡는다.** 강제 우회를 일부러 주입해 `20/20 → 17/20` 으로 떨어지는 것을
확인했다 (변이 검사). 남은 것은 **기본값 자체** — `compose.yaml` 단독은 여전히 열려 있고,
닫으려면 `compose.prod.yaml` 을 써야 한다. 그건 운영 선택이지 코드 결함이 아니다.

### G2 — 초대 경로가 없다 🟠

`node.provision_source` 는 `team | invited | public` 을 받는다. 그런데 **`invited` 를 만드는
절차가 없다.** 지금은 관리자가 직접 `POST /v1/nodes` 를 부른다.

「러닝크루가 자기 기기를 내놓는다」는 시나리오에는 **가입 요청 → 승인 → 증서 발급**이 필요하다.
값은 스키마에 있고 경로가 없다 — `attempt_no` 와 같은 모양이다.

### G3 — 「누가 내 데이터를 돌릴 수 있나」를 한 면에서 못 본다 🟠

`GET /v1/ops/status` 가 `enforcement`·`nodes_without_credential`·`drift_routable` 을 준다.
`GET /v1/nodes-liveness` 가 생존을 준다. 하지만 **한 기기에 대해 「왜 이 기기가 실행 가능한가」**
(등급·조달·증서·바인딩·계약)를 한 번에 보는 면이 없다. 운영자가 여러 조회를 이어 붙여야 한다.

### G4 — 증서 회전 절차가 런북에 없다 🟡

`revoke_credential` 은 있고 「폐기 후 재발급」이 원칙인데, **무중단 회전 순서**가 문서에 없다.
`operate-production.md` §5 에 한계로만 적혀 있다.

### G5 — arch 미선언 Agent 가 남아 있다 🟡

`agent.arch` 는 nullable 이다 (legacy). golden 능력은 게이트가 잡고, 계약 능력은 `contract_check`
가 `arch=None` 을 실패로 처리한다. `agent_arch_unbound` 뷰로 드러나긴 하지만, **등록 시점에
막지는 않는다.**

---

## 3. 의도적으로 약화·후순위 (기록)

- **골든 acc·A/B 등가 강제** — 선택 프로파일이다 (D18). 「모든 Agent 성적 평가」는 본체가 아니다
- **D6 사전학습 해제** — 별도 Proposal. 출품 라이선스(절대규칙 6)와 분리
- **C 백업·복구 리허설 · 폰 Node · Contribution 장부** — 이 이슈의 다음 칸
- **TLS** — 온프레/VPN 전제면 계속 후순위. 인터넷 Node 를 열기 직전에 강제

---

## 4. 보장 / 불보장

| 보장 | 근거 |
|------|------|
| 승인하지 않은 신뢰 도메인으로 라우팅되지 않는다 | DB 복합 FK (9) |
| 선언과 다른 가중치로 실행되지 않는다 | `agent_node_ready` FK (6) + Node 해시 대조 (7) |
| 배정 없는 실행은 거부된다 | 403 (10) |
| 누가·무엇으로·언제 실행했는지 남는다 | `assignment`·`gate_run`·`audit_log` (12) |

| **불보장** | 이유 |
|---|---|
| Node 에 평문이 남지 않는다 | 추론은 평문을 요구한다. **TEE 없이 원리적으로 불가** |
| Node 가 거짓 보고를 못 한다 | 계약 검증은 러너가 수행하고 Core 는 받아 적는다. 절대규칙 8(게이트러너 전용)이 그 신뢰의 근거다 |
| 두 Agent 가 같은 답을 낸다 | 등가는 선택 프로파일의 **관측값**이다 (D17) |

**Trust Domain 이 민감도 제한 수단이다** — 평문이 남을 수 있다는 전제에서, 어떤 기기까지
갈 수 있는지를 도메인으로 좁힌다.
