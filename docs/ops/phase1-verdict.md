# Phase 1 판정 리포트 (§7.2 의무 판정)

> 기획서 [`capnet-plan.md`](../design/capnet-plan.md) **§7.2** — *Phase 1 종료 시 의무 판정*.
> §13 주 9: **판정 없이 Phase 2 코드 금지.** 이 문서가 그 관문이다.
>
> 로드맵상 위치: [`../design/roadmap.md`](../design/roadmap.md) **P1-4**
> 작성: 2026-08-08 · **상태: 작성 중 (P1-3 미완)**

---

## 0. 판정 요약

| 축 | 기준 (§7.2) | 실측 | 충족 |
|----|-------------|------|------|
| A/B 편차 | < 0.05 | 0.0467 (n=300, 사슬 밖) | ⚠️ 조건부 — §3 |
| 통과율 | 20–80% | **측정 중** | ⏳ |

**판정: 미확정.** 통과율 축이 비어 있어 §7.2 표의 어느 행에도 아직 들어가지 않는다.

> 이 문서는 결과가 좋게 나오도록 기준을 고쳐 쓰지 않는다. 기준은 §7.2에 고정돼 있고,
> 여기서는 실측만 채운다. 밴드 밖이면 밴드 밖이라고 적는다.

---

## 1. §7.1 증명 대상 5개

기획서 §7.1이 Phase 1의 통과 조건으로 못 박은 다섯 가지다.

| # | 증명 대상 | 판정 | 증거 |
|---|-----------|------|------|
| 1 | `image.classify@1` + 골든셋 G | ✅ | seed capability + 데모 골든 N=40 manifest |
| 2 | Agent **A, B**가 해당 능력에 PASSED | ✅ **2026-08-08 달성** | §2 |
| 3 | 증명 모드로 A/B 교체 할당 | ✅ **2026-08-08 달성** | §2 |
| 4 | 점수 편차 < 0.05 | ⚠️ 조건부 | §3 |
| 5 | Product Track에 Agent 선택 없음 | ✅ | `claim.py` — Task는 capability + datasetId + caseId만 받는다 |

---

## 2. §7.1-2 · §7.1-3 — 사슬 위 A/B 교체 (달성)

`scripts/proof_ab.sh` 1회 실행. 채점은 team gate-runner(`node-m-team`)에서만 했다.

### 2.1 실게이트 결과 (데모 골든 N=40)

| Agent | 백본 | epoch | accuracy | macro_f1 | 게이트 |
|-------|------|-------|----------|----------|--------|
| `proof-agent-a` | TinyEuroSAT | 80 | 0.7000 | 0.6982 | **PASSED** |
| `proof-agent-b` | TinyEuroSATB | 40 | 0.8250 | 0.8198 | **PASSED** |

임계 AND: `accuracy ≥ 0.68` ∧ `macro_f1 ≥ 0.65` ∧ `invalid_rate ≤ 0.02` (SD-004 실측 보정값).

**B가 DB 게이트 증서를 받은 것은 이번이 처음이다.** 이전까지 B는 오프라인 점수만 있었다 (SD-001 범위 한정).

### 2.2 DB가 기록한 사슬

`gate_run` → `gate_run_passed` → `agent_capability_passed` 를 psql로 직접 확인했다.

| agent | status | `dummy` | acc | cases | `gate_run_passed` | `agent_capability_passed` |
|-------|--------|---------|-----|-------|-------------------|---------------------------|
| proof-agent-a | PASSED | **false** | 0.7000 | 40 | ✅ | ✅ |
| proof-agent-b | PASSED | **false** | 0.8250 | 40 | ✅ | ✅ |

`dummy=false`가 핵심이다. seed의 dummy PASSED는 배관용이며 품질 증명이 아니다.

### 2.3 교차 할당 (UC-7)

동일 `caseId=ic1-0001`을 `requestedAgentId`로 A·B에 각각 지정해 실행했다.

| agent | input_ref | `requested = assigned` | assignment | task | 결과 label |
|-------|-----------|------------------------|------------|------|-----------|
| proof-agent-a | `{"datasetId":"eurosat-rgb","caseId":"ic1-0001"}` | **true** | SUCCEEDED | COMPLETED | `annual_crop` |
| proof-agent-b | 동일 | **true** | SUCCEEDED | COMPLETED | `annual_crop` |

스냅샷도 함께 확인했다: `task_trust_domain=team` · `node_trust_domain=team` · `capability_tier=M` · `node_tier_max=M`.

**여기서 증명된 것:** 게이트를 통과한 두 Agent가 **사슬 위에서** 교체 가능하다. 지정 실행은 `agent_capability_passed`를 거치므로, 게이트를 통과하지 않은 Agent는 지정해도 할당되지 않는다.

**여기서 증명되지 않은 것:** case 1건의 일치는 등가성의 통계적 근거가 아니다. 그것은 §3의 몫이다.

---

## 3. §7.1-4 — 편차 < 0.05 (조건부)

| 항목 | 값 |
|------|-----|
| Agent A (TinyEuroSAT, 80ep) n=300 | acc **0.8800** · f1 0.8797 |
| Agent B (TinyEuroSATB, 40ep) n=300 | acc **0.9267** · f1 0.9266 |
| paired `abs_diff` | **0.046667** ≤ 0.05 → **WITHIN_THRESHOLD** |
| SE_a / SE_b | 0.01876 / 0.01505 |
| **label_agreement** | **0.8933** |

**본 판정 세션에서 재현했다** (2026-08-08). `extract_golden_n300` → `score_n300` ×2 → `compare_ab`.
골든 n=300 manifest sha256 `c80d9816fedfb0f1ca9379a5edf7d729fad3a543e38b9f870b584ffef683ce6c` ·
클래스당 30건 균등. 이전 세션 기록(A 0.880 · B 0.927 · diff 0.0467)과 **일치**했다 —
추출이 결정적이며 숫자가 재현 가능하다는 뜻이다.

### 3.0 정확도가 같다고 같은 예측기는 아니다

`label_agreement = 0.8933`. 300건 중 **32건에서 A와 B가 서로 다른 라벨을 냈다.**

편차 축(§7.1-4)은 **집계 정확도**만 본다. 그 기준으로는 통과다. 그러나 호출자 입장에서
"Agent가 바뀌어도 같은 답"은 성립하지 않는다 — 10.7%의 케이스에서 답이 달라진다.

이것은 계약 위반이 아니다. `image.classify@1` 계약은 closed-set 라벨과 집계 임계를 규정할 뿐
케이스별 일치를 요구하지 않는다. 다만 **대체 가능성을 어느 수준에서 주장하는지**를
보고서·영상에서 흐리면 안 된다:

- 주장 가능: "같은 계약을 통과한 Agent로 교체해도 **계약이 보장하는 품질 수준**이 유지된다"
- 주장 불가: "교체해도 **같은 답**이 나온다"

§2.3의 case 1건 AGREE는 이 89.3%의 한 표본일 뿐이며, 그 자체로는 아무것도 증명하지 않는다.

### 3.1 이 값에 붙는 세 가지 한정

1. **사슬 밖 측정이다.** `score_n300`이 `app.score_gate`를 컨테이너에서 직접 실행하고, `compare_ab`가 점수 JSON 두 개를 비교한다. `gate_run`·`assignment`를 거치지 않는다. 채점기는 실게이트와 동일 모듈이므로 점수 자체는 신뢰할 수 있으나, **"CapNet이 교체했다"**는 사실은 §2가 증명하고 이 숫자가 증명하지 않는다.
2. **epoch가 불일치한다.** A=80, B=40. 두 Agent의 차이가 백본 차이인지 학습량 차이인지 이 측정은 구분하지 못한다.
3. **SE ≈ 0.019로 임계와 가깝다.** 0.0467과 0.05의 간격이 표준오차보다 크지 않다. 반복 측정에서 임계를 넘을 수 있다.

### 3.2 그래서 "조건부"인 이유

편차 수치는 기준을 만족한다. 그러나 §7.2가 묻는 것은 "이 계약에서 Agent가 대체 가능한가"이고, 위 세 한정 중 2번(epoch 불일치)은 그 질문에 직접 영향을 준다. **판정에 쓰되 한정을 함께 적는다.**

---

## 4. 통과율 20–80%

### 4.1 모집단 설계 — **결과를 보기 전에 고정한다**

통과율은 골든셋만의 성질이 아니다. **후보 모집단을 어떻게 고르느냐에 따라 값이 달라진다.**
저epoch 후보를 더 넣으면 내려가고, 고epoch를 더 넣으면 올라간다.
따라서 결과를 본 뒤 후보를 추가·제외하면 그것은 측정이 아니라 조작이다.

**설계 (2026-08-08, 결과 확인 전 고정):**

- 축 = 두 scratch 백본 × epoch 사다리. 두 축 모두 **대칭으로** 채운다.
- `TinyEuroSAT`: **5 · 20 · 40 · 80** epoch
- `TinyEuroSATB`: **5 · 10 · 20 · 40** epoch
- 총 **8 후보.** seed는 전부 `20260806` 고정, 사전학습 없음, 전부 EuroSAT scratch.
- 분모에서 제외: **sanity floor**(상수·난수·스키마 위반). 설계상 반드시 실패하므로
  포함하면 통과율을 인위적으로 낮춘다. floor는 §5에서 따로 본다.
- 채점: team gate-runner 1곳, 데모 골든 N=40, 임계 AND 0.68 / 0.65 / 0.02.

이 설계를 바꾸려면 바꾼 이유와 시점을 이 절에 적는다.

### 4.2 중간 기록 — 5 후보 시점

사다리를 완성하기 전 5개 시점의 값이다. **판정에 쓰지 않는다.** 기록만 남긴다.

| candidate | epoch | acc | macro_f1 | gate |
|-----------|-------|-----|----------|------|
| `eurosat_scratch` (TE) | 80 | 0.7000 | 0.6982 | PASSED |
| `eurosat_scratch_b` (TEB) | 40 | 0.8250 | 0.8198 | PASSED |
| `eurosat_scratch_c5` (TE) | 5 | 0.6000 | 0.5893 | **FAILED** |
| `eurosat_scratch_d10` (TEB) | 10 | 0.7000 | 0.7013 | PASSED |
| `eurosat_scratch_e20` (TE) | 20 | 0.7500 | 0.7384 | PASSED |

4/5 = **80.0%** — 밴드 상한에 정확히 걸쳤고 해상도는 20% 단위였다.
이 불안정성이 §4.1의 사다리를 완성하기로 한 이유다.

### 4.3 최종 측정 (8 후보)

*(TEB 5 · TEB 20 · TE 40 학습 후 채운다)*

---

## 5. Sanity floor

*(P1-3과 함께)*

---

## 6. 판정과 다음 행동

*(§4 완료 후)*

---

## 7. 재현 방법

```bash
docker compose up --build -d
bash scripts/proof_ab.sh          # §2 — 실게이트 + 교차 할당
bash scripts/sanity.sh            # §5 — floor 3종 FAILED
```

n=300 축(§3)은 `scripts/extract_golden_n300.sh` → `scripts/score_n300.sh` → `scripts/compare_ab.sh`.
골든 n=300 케이스와 `artifacts/`는 저장소에 없다 (SD-003).
