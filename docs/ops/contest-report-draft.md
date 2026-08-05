# CapNet 결과보고서 초안 (문의 회신 무관)

**상태:** 초안. 서식 미확정 → 절 단위 블록. 제출본은 이후 pdf/docx.  
**갱신:** 2026-08-06  
**쉬운 안내 요지:** [user-guide-ko.md](../guide/user-guide-ko.md)

과장이 섞이면 1차 서면이 무너진다. **된 것과 안 된 것을 분리한다.**

---

## 0. 한 쪽 요약

**문제:** 같은 능력 이름으로 다른 구현이 끼어들어도, 호출자는 알기 어렵다.  
**해법:** Capability를 채점 가능한 계약으로 두고, 게이트·할당 규칙을 PostgreSQL 제약으로 강제한다.  
**증명한 것 (초안 시점):** 스키마 불변식 실측, dummy E2E 배관, 골든셋 데모 N=40 핀, 위반 6종 스크립트, scratch 실게이트 PASSED(acc=0.70, `dummy=false`) + Task 완주, sanity floor FAILED.  
**아직 아닌 것:** 시연 영상, A/B 동등성(미결), `node_credential`.  
**재현:** `docker compose up --build` → `scripts/smoke_w1.ps1`(dummy) → `scripts/demo.ps1`(실게이트) → `scripts/sanity.ps1` → `scripts/demo_violations.ps1`.  
**임계:** 가정 0.75/0.72 → 실측 보정 0.68/0.65. dummy PASSED를 실게이트로 쓰지 않는다.

---

## 1. 문제 정의

스토어에 에이전트를 모아 두는 것은 이미 많다. CapNet이 묻는 것은 그 앞이다.

> 같은 계약을 표방하는 두 Agent를, 사용자가 모르는 채로 바꿔 끼울 수 있는가?

이름만으로는 보장되지 않는다. 별칭·라우터·시간 드리프트는 특정 벤더 공격이 아니라 플랫폼 구조 문제다 (기획서 v4.5 §2.5 · §14).

---

## 2. Capability = 계약

`image.classify@1`은 코드 문자열이 아니라 다음이 묶인 계약이다.

- 입출력 스키마 (closed-set 10라벨)
- 전처리: EuroSAT RGB 원본 64×64 → **32×32** (게이트=제품)
- 골든셋 데모 N=40 + `golden_set_sha256`
- 통과 기준 AND (`min_accuracy` · `min_macro_f1` · `max_invalid_rate`) — **0.68 / 0.65 / 0.02** (실측 보정)

사슬은 **Capability → Agent → weights_sha256** 만. Model Identifier를 두지 않는다.

---

## 5. 위반 실측 (변별점)

원표: [`../error/pg-violations.md`](../error/pg-violations.md) (14종 실측).  
출품 Must M25는 아래 6종을 `scripts/demo_violations.sql`로 재현한다.

| # | 시도 | 기대 |
|---|------|------|
| 1 | 게이트 미통과 Agent 할당 | FK 거부 |
| 2 | team Task → public Node | `domain_compatible` 계열 FK 거부 |
| 3 | L Capability → S Node | `tier_compatible` 계열 FK 거부 |
| 4 | 라이브 lease 중 Node 티어 강등 | FK 거부 |
| 5 | READY 존재 중 가중치 교체 | FK 거부 |
| 6 | PASSED `gate_run` 사후 FAILED | FK 거부 |

앱 `if`가 아니라 **DB가 거절**한다. 제약을 끄거나 `NOT VALID`로 우회하지 않는다.

---

## 8. 한계와 다음 단계

- 데모 N=40이면 대체가능성 통계 판정(편차 0.05)은 **불가** (SE가 임계와 비슷). 본편 n≥300.
- seed Agent의 시드 `gate_run` PASSED는 **배관용**이다. dummy 추론·dummy 게이트를 품질 증명으로 쓰지 않는다.
- A/B 비교(S2)를 Must로 올릴지는 **미결** (기한 8/11). 구현하지 않은 채 문서로만 남긴다.
- `min_accuracy`/`min_macro_f1`는 TinyEuroSAT scratch N=40 실측 후 **0.68/0.65**로 보정했다 (가정 0.75/0.72는 위였음).
- 공공 유휴·테넌트 제품화는 출품 범위 밖이다.

---

## 이 초안에 아직 없는 절

3 아키텍처 그림 · 4 DB 제약 구조 상세 · 6 골든셋 채점 규칙 본문 · 7 재현 절차 확정 · 9 라이선스 표. W2–W3에 채운다.
