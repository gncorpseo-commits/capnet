# CapNet — 2026 오픈소스 개발자대회 Contest MVP 계획·시나리오

> **시나리오·UC 정본.** 대회 **일정·제출 마감은** [`contest-submission-checklist.md`](./contest-submission-checklist.md) **만** 본다.  
> 갱신: 시나리오가 바뀔 때만 · 2026-08-08 (일정 절 → 링크로 축소)

**출품명:** CapNet (Capability Network)  
**상위 레포/공간:** ai-agent-store  
**근거:** [capnet-plan.md](../design/capnet-plan.md) v4.4 · [docs/spec/schema.sql](../spec/schema.sql) v4.4  
**쉬운 안내:** [docs/guide/user-guide-ko.md](../guide/user-guide-ko.md)  
**골든셋 정본:** [docs/spec/golden/image-classify-v1.md](../spec/golden/image-classify-v1.md) v0.2  
**대회:** [2026 오픈소스 개발자대회](https://www.oss.kr/pages/2) (접수 완료) · 제출 안내 [notice/39](https://osscontest.kr/notice/39)  
**문서 버전:** v0.3 · 시나리오 본문 2026-08-01  

---

## 0. 한 줄 목표

> **출품일까지**, 심사관이 clone → 기동 → 데모 한 번에  
> 「Capability 계약 → 게이트 합격 → Task 완주 → **규칙 위반 거절**」을  
> **오픈소스로 재현**할 수 있게 한다.

본편 Phase 1(10주·Kill 판정·n=300 골든셋)과 **분리**한다.  
Contest MVP는 Phase 1의 **시연 가능한 최소 슬라이스**이다.

```text
본편:     Phase 1 (10주) → Phase 2–3 테넌트 → … → 공공 유휴
대회:     Contest MVP ⊂ Phase 1 슬라이스
          정식 Kill 판정(기획서 §7.2)·테넌트는 출품 이후
```

**변별점:** 오케스트레이션 데모가 아니라, **라우팅·게이트 규칙을 DB가 강제**하고 위반이 거절되는 것을 보여 준다 (M25).

---

## 1. 대회 일정

**정본:** [`contest-submission-checklist.md`](./contest-submission-checklist.md) §1 (F1–F5) · §6 일정 표.  
날짜·마감·제출물 종류를 이 파일에 다시 쓰지 않는다.

---

## 2. 출품 MVP가 보여 줄 시나리오 (인수 기준)

```text
1) Capability `image.classify@1` 등록 (골든셋·메트릭)
2) Agent 등록 (safetensors + sha256) — EuroSAT scratch 학습 가중치
3) team gate-runner Node에서 게이트 → PASSED
4) Task 1건 → 동일 Node 추론 → 결과(label)
5) (Must) 라우팅·게이트 위반 시도 → DB가 거절 (M25)
6) (Should) Agent B 교체 후에도 같은 Capability로 Task 성공
```

**완료 정의:** 타인 PC(또는 검증 환경)에서  
`clone → compose up → demo` (+ `demo_violations`) 로 **1–5**가 재현되면 출품 OK.

---

## 3. 개발 일정 (∼8.27)

| 주 | 날짜(대략) | 산출물 |
|----|------------|--------|
| **W0** | 8/1–3 | 범위 동결, **가중치=scratch 확정**, LICENSE, CapNet 출품명, 골든셋 `docs/spec/golden/` 편입, 주최 문의 |
| **W1** | 8/4–10 | PG v4.4, Core CRUD+게이트. **claim/gate = `INSERT … SELECT` 고정**(§3.1) |
| **W2** | 8/11–17 | **8/11–15** Node 1·Agent 1·Task 1 완주 / **8/16–17 버퍼**. UC-7은 W3 |
| **W3** | 8/18–24 | demo·violations·compose·README·영상·보고서. (여유 시 UC-7) |
| **W3.5** | 8/25–27 | 라이선스 스캔·패킹 (SPDX는 의존성 추가 시점부터 누적) |

### 3.1 W1 구현 규칙 (필수)

claim·gate INSERT는 스냅샷 컬럼을 **앱이 수기 입력하지 않는다.**  
원본 행에서 끌어오는 `INSERT … SELECT`만 허용한다. (ORM으로 Assignment만 채우면 FK 폭발 → 제약 끄기 → 변별점 상실)

```text
gate_run(PASSED) → gate_run_passed → agent_capability(PASSED, gate_run_id)
                 → agent_capability_passed → 그제서야 assignment 가능
```

### 3.2 밀렸을 때 버리는 순서

```text
1순위 버림:  UC-7 A/B (S2)         → 영상은 위반 데모로 대체
2순위:        WS → 폴링 (M15)       → 보고서에 “데모는 폴링, WS는 본편”
3순위:        heartbeat 스캐너 (M17) → 데모 중 세션 유지
4순위:        sanity 3종 → 1종
절대 안 버림: M25 · M4 · M11
```

---

## 4. 최소 기능 (Must / Non-goal / Should)

### 4.1 Must

#### 레포·운영
| ID | 기능 |
|----|------|
| M1 | 공개 Git + LICENSE(Apache-2.0 또는 MIT) + NOTICE |
| M2 | README: 5분 기동·시연 명령 (**출품명 CapNet**) |
| M3 | docker compose: Postgres + Core + 데모 Node |
| M4 | `scripts/demo` — §2 시나리오 1–4 E2E |
| M25 | `scripts/demo_violations` — **위반 6종 전부** DB 거부 (아래). 최소 3종으로 축소하지 않음 |

**M25 고정 6종** (구현 비용 ≈ SQL 스크립트. PG16에서 이미 검증됨):

1. 게이트 미통과 Agent로 할당  
2. team Task → public Node  
3. L Capability → S Node  
4. 라이브 lease 중 Node 강등  
5. READY 존재 시 가중치 교체  
6. PASSED 근거 run을 사후 무효화 시도  

보고서 1장: 위반 표 + 거부한 제약 이름.  
영상: 105–135초 1–3종 터미널 상세 / 135–150초 4–6종 결과 표.

#### 데이터·계약
| ID | 기능 |
|----|------|
| M5 | schema.sql v4.4 적용 |
| M6 | `image.classify@1` seed |
| M7 | 골든셋 **데모 N=30–50** + manifest sha256 (통계 판정용 n=300은 본편) |
| M8 | allowlist `datasetId`만 |

#### Core API (CLI/curl, UI 없음)
| ID | 기능 |
|----|------|
| M9 | Capability / Agent / Node 등록·조회 |
| M10 | 바인딩·sha256 → READY |
| M11 | Gate → PASSED 사슬 |
| M12 | Task claim → Assignment → 완료 (`INSERT … SELECT`) |
| M13 | 결과 조회 |
| M14 | Proof Agent 지정 — **Should에 가깝게**, W3 여유 시 |

#### Node Runtime
| ID | 기능 |
|----|------|
| M15 | Core 연결 (데모: **폴링 허용**, WS는 본편) |
| M16 | lease → safetensors → 추론 → 결과 |
| M17 | 데모 중 세션 유지 (만료 스캐너는 후순위) |
| M18 | gate-runner 게이트 추론 (= M16) |

#### 채점·게이트
| ID | 기능 |
|----|------|
| M19 | closed-set 채점 |
| M20 | min_accuracy → PASSED/FAILED |
| M21 | sanity **3종**(상수·난수·스키마 위반) FAILED — 시간 없으면 상수 1종 |

#### 출품물
| ID | 기능 |
|----|------|
| M22 | 결과보고서 (서두에 [user-guide-ko](../guide/user-guide-ko.md) 요지) |
| M23 | 시연 영상 ≤3분 (§7) |
| M24 | 라이선스 점검 — **의존성 추가 시점 SPDX 누적** + W3.5 최종 스캔 |

### 4.2 Non-goals

- tenant / public 제품화, UI, 과금, work_units 대시보드  
- 골든셋 n=300·통과율 20–80% **확정**·기획서 §7.2 Kill 전부  
- 자동 재할당, S-tier 폰, 샤딩, 셀프 온보딩  
- **ImageNet 등 사전학습 가중치 동봉/다운로드** (라이선스 위험)

### 4.3 Should

| ID | 기능 |
|----|------|
| S2 | Agent A/B **다른 소형 백본**(둘 다 EuroSAT scratch) |
| S3 | golden_set_sha256 불일치 시 게이트 거부 |
| S4 | OpenAPI YAML 초안 |

---

## 5. 역할 정의

| 역할 | 하는 일 | 대회·시연에서 |
|------|---------|----------------|
| **Admin** | Capability·게이트·위반 데모·Proof | 시연 진행자 |
| **Developer** | Agent 등록·바인딩·scratch 학습 | 모델 제공자 |
| **User** | Capability만 호출 | 제품 트랙 |
| **Node 운영자** | Node 기동·세션 | 팀 GPU |
| **재현 사용자** | clone→demo | 심사·멘토 |

쉬운 말: [user-guide-ko.md](../guide/user-guide-ko.md)

---

## 6. 유스케이스 시나리오

### UC-1. Admin — Capability·골든셋 등록
Core 기동(M3) → Capability(M5–6, M9) → 골든셋·allowlist(M7–8).

### UC-2. Node 운영자 — team gate-runner
Runtime 연결(M15) → Node `is_gate_runner=true`(M9) → 세션(M17).

### UC-3. Developer — Agent 등록·바인딩
scratch safetensors+sha256(M9) → READY(M10).

### UC-4. Admin — 게이트 (핵심)
gate_run → 채점 → PASSED 사슬(M11, M16, M18–20).  
게이트 절차 근거: 기획서 **§7.1·위협 모델**, Kill 표는 §7.2(본편).

### UC-5. Admin — Sanity floor
상수·난수·스키마 위반 Agent → 전부 FAILED(M21).

### UC-6. User — Product Track Task
capability + datasetId + caseId(M12, M8) → 결과(M13). Agent 선택 없음.

### UC-7. Admin — Proof A/B (Should, W3)
Agent B PASSED 후 지정 실행(M14). 정식 편차 &lt; 0.05는 출품 Must 아님.

### UC-8. Node — 추론 일상
lease → 추론 → 결과(M15–17).

### UC-9. Developer — 가중치 교체 시도
READY 중 변경 → 거부 (M25에 포함).

### UC-10. 재현 사용자
compose → demo → demo_violations(M1–4, M25, M24).

### UC-11. Admin — 위반 거절 데모 (Must, M25)
§4.1 M25 목록을 순서대로 실행, 각 FK/CHECK 거부 확인.

### 매트릭스

| UC | Admin | Dev | User | Node | 재현 | 주요 M# |
|----|:-----:|:---:|:----:|:----:|:----:|---------|
| 1–5 | ● | ○ | | ● | | M5–11, M21 |
| 6 | | | ● | ● | | M8,12,13 |
| 7 | ● | ○ | | ● | | M14 |
| 11 위반 | ● | | | | ● | **M25** |
| 10 재현 | | | | | ● | M1–4, M25 |

---

## 7. 3분 시연 영상 스토리보드 (리뷰 재배분)

| 초 | 화면 | 말/자막 |
|----|------|---------|
| 0–20 | 문제 | 능력만 요구한다. 그런데 **어디서 돌았는지 답할 수 있는가** |
| 20–45 | UC-1 | Capability 등록 |
| 45–75 | UC-4 + UC-5 | 게이트 PASSED + **sanity FAILED** |
| 75–105 | UC-6 | User는 Agent 몰라도 Task 성공 |
| **105–135** | **UC-11** | **위반 1–3종** 터미널로 천천히 (도메인 / 게이트 미통과 / 티어) |
| **135–150** | **UC-11** | **위반 4–6종** 결과 표로 스치듯 (제약 이름 보이게) |
| 150–170 | UC-7 또는 스키마 한 장 | A/B 성공 시 삽입, 아니면 사슬 다이어그램 |
| 170–180 | repo | CapNet OSS, compose 재현 |

---

## 8. 쉬운 설명

전체 본문: **[docs/guide/user-guide-ko.md](../guide/user-guide-ko.md)** (IT 비전문가용 · 영문 파일명).

보고서·발표 서두 요약:

- Capability = 시험 과목 · Agent = 수험생 · Node = **우리 쪽 컴퓨터**(데모=노트북 한 대)  
- 게이트 = 합격 시험 · Task = 실전  
- **잘못된 조합은 장부(DB)가 거절** (고장 아님)  
- 사용자는 과목과 허용된 입력만 — **AI가 바뀌어도 요청법은 그대로**  

---

## 9. 라이선스·데이터 (검증 대비)

| 항목 | 방침 |
|------|------|
| 출품·repo 표기 | **CapNet** (상위 공간명 ai-agent-store와 혼동 금지) |
| 프로젝트 | Apache-2.0 또는 MIT + NOTICE |
| 데모 데이터 | EuroSAT (MIT). Zenodo `7711810` + archive_sha256 고정 권장 |
| Copernicus | Sentinel 이용약관 한 줄 인용 |
| **모델 가중치** | **EuroSAT만으로 scratch 학습. 사전학습 가중치 미사용.** 학습 스크립트·시드 repo 포함 |
| pip/npm | 추가 시점 SPDX 기록 + W3.5 스캔 |
| 골든셋 n | 데모 30–50 / 본편 300+ — 보고서에 **분리 명시** |
| 데모 ≠ 제품 도메인 | “시연용. 첫 고객 도메인과 별개” |

---

## 10. 포지셔닝

> **CapNet**은 AI 챗·모델 마켓이 아니라,  
> 사용자가 능력만 요구하면 승인된 신뢰 도메인 안의 기기로만 라우팅하고,  
> 신뢰 도메인 안 Node에서 Task를 완결하는 오픈소스 실행 계층이다.  
> 규칙의 상당 부분을 **DB가 강제**하며, 위반은 거절된다 (schema v4.4).

---

## 11. 리스크와 완화

| 리스크 | 완화 |
|--------|------|
| 오케스트레이션으로 보임 | **M25를 영상·보고서 중심** |
| W2 지연 | UC-7→W3, Node 1·Agent 1·Task 1만 |
| 가중치 라이선스 탈락 | scratch only (§9) |
| ORM으로 FK 우회 | W1 `INSERT … SELECT` (§3.1) |
| 재현 실패 | M4 + M25 + compose |
| n=30 통계 오해 | 보고서에 데모/본편 분리 |

---

## 12. 제출 체크리스트 (8.25–27)

- [ ] M1–M13, M15–M21, **M25** 동작  
- [ ] UC-1→4→6→11 (+ 가능 시 7)  
- [ ] LICENSE / NOTICE / README (CapNet)  
- [ ] [user-guide-ko.md](../guide/user-guide-ko.md) 링크  
- [ ] [golden/image-classify-v1.md](../spec/golden/image-classify-v1.md) 정본 1개  
- [ ] 결과보고서 (위반 표 1장)  
- [ ] 시연 영상 ≤3분 (§7)  
- [ ] 소스·가중치 출처 깨끗  
- [ ] SPDX/라이선스 자가 점검  
- [ ] **상대 링크 전부 클릭 확인** (한글 파일명·깨진 링크 없음)  

---

## 13. W0 체크리스트 (8/1–3)

1. [x] 모델 가중치 = EuroSAT scratch 확정 (문서)  
2. [x] M25 **6종 고정**·영상 105–135/135–150 재분배  
3. [x] claim/gate INSERT 패턴 문서화  
4. [ ] 출품명 CapNet + LICENSE 초안 (코드 레포)  
5. [x] 골든셋 **정본 1개** `docs/spec/golden/image-classify-v1.md` v0.2 + 중복/한글 파일 제거  
6. [x] 파일명 영문화 (`user-guide-ko.md`)  
7. [ ] contest@oss.kr 문의 (배점·repo URL·zip 인코딩)  
8. [x] UC-7 → W3 · W2 버퍼 **8/16–17**  
9. [x] 사용안내: “우리 쪽 컴퓨터”·“AI 바뀌어도 요청법 동일”  

---

## 14. 관련 문서

| 문서 | 역할 |
|------|------|
| [capnet-plan.md](../design/capnet-plan.md) | 본편 전략·스키마·Phase 1 |
| [docs/spec/schema.sql](../spec/schema.sql) | DDL v4.4 |
| [docs/guide/user-guide-ko.md](../guide/user-guide-ko.md) | **IT 비전문가용 안내** |
| [docs/spec/golden/image-classify-v1.md](../spec/golden/image-classify-v1.md) | **골든셋 정본 v0.2** |
| 본 문서 | Contest MVP 계획·시나리오 |

---

## 15. 문서 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v0.1 | 2026-08-01 | 초판 |
| v0.2 | 2026-08-01 | M25 Must, INSERT, scratch, 영상 재배분 |
| v0.3 | 2026-08-01 | 문서세트 리뷰: 골든셋 정합·영문 파일명·M25 6종 고정·W2 버퍼 날짜·사용안내 보강 |
