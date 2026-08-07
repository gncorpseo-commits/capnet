# CapNet 컨텍스트 핸드오프

> 세션 인계용 **결정·미결** 요약. 상세 위반·함정은 `docs/error/`에 둔다 (중복 금지).
> 자동 로드되지 않는다. 필요할 때 `@docs/context-handoff.md`로 부른다.
>
> 문서 지도: [`INDEX.md`](./INDEX.md) · 주간 상태: [`../STATE.md`](../STATE.md)  
> 최종 갱신: 2026-08-06

---

## 1. 확정된 결정과 근거

바꾸려면 근거를 먼저 반박해야 하는 것들이다.

| # | 결정 | 근거 |
|---|------|------|
| D1 | MVP 증명 대상 = **Capability 추상화 성립** (E2E 아님) | E2E는 기성 기술 조합이라 되는 게 당연. 미검증 명제는 "같은 계약의 Agent가 대체 가능한가" |
| D2 | Capability = 이름이 아니라 **계약** (스키마 + 골든셋 + 게이트) | 이름만으로는 대체 가능성이 보장 안 됨 |
| D3 | **전처리는 계약의 일부** (32×32 RGB). Gate·Product·Proof 동일 | 게이트만 열화하면 증명이 제품에 대해 아무 말도 못 함. 바꾸려면 `@2`로 버전 상승 |
| D4 | 게이트 실행은 **team gate-runner Node에서만** | 제출자 Node에서 골든셋을 돌리면 정답 하드코딩으로 게이팅 무력화 |
| D5 | 가중치 **safetensors만** | `.pt`/`.pth`는 pickle 역직렬화 → 로드만으로 임의 코드 실행 |
| D6 | **사전학습 가중치 금지. EuroSAT scratch 학습만** | 대회 2차 라이선스 검증. ImageNet 가중치는 조건 승계 논란 |
| D7 | MVP Node = **팀 자체 조달만** | 인센티브가 P6인데 공급은 P2부터 필요 → 닭-달걀. 외부는 Phase 3+ |
| D8 | 입력은 **allowlist된 datasetId만**. 자유 업로드 경로를 만들지 않음 | fileToken은 다운로드 이후를 통제 못 함. 정책이 문서에만 있으면 안 지켜짐 |
| D9 | **모델 기반 골든셋 샘플 선택 금지** | 참조 모델의 귀납 편향이 골든셋에 박히면, A/B 편차가 Agent 차이인지 편향인지 구분 불가 |
| D10 | 난이도 조준은 **입력 열화만** (혼동 가중 없음) | D9의 귀결 |
| D11 | **M25(위반 거절 데모)가 대회 Must** | 유일한 진짜 변별점. 구현 비용 ≈ 0 (SQL 스크립트) |
| D12 | Changelog는 `docs/history/CHANGELOG.md` 단독 | README는 대회 심사용 5분 기동 안내 전용 |
| D13 | 커밋 계정 = **gncorpseo-commits** | 전역 CLAUDE.md의 jangsejong 아님 |
| D14 | 문서는 `docs/{guide,error,history,design,spec,ops,research}` + `docs/INDEX.md` | 전역 파일 순번 금지. 진입은 INDEX |
| D15 | Provenance by Design. 사슬은 Capability → Agent → `weights_sha256`만 (Model Identifier 금지). 완료 = `assignment` + 해시 + `gate_run` 사슬. `audit_log` 실패 ≠ 무조건 FAILED | 기획서 v4.5. UI가 아니라 DB 증적 |

---

## 2. 검증·함정 (본문은 error/)

- **PG 위반 14종 실측:** [`error/pg-violations.md`](./error/pg-violations.md) — M25 재현 원본
- **구현 함정** (`INSERT … SELECT`, 게이트 사슬, tier 정렬, claim, 훅, Wiki 하이픈): [`error/pitfalls.md`](./error/pitfalls.md)

---

## 3. 골든셋 요점

상세: [`spec/golden/image-classify-v1.md`](./spec/golden/image-classify-v1.md).

- 계약: `image.classify@1`, closed-set 10라벨, 32×32 RGB
- 데이터: EuroSAT **RGB 배포판**, Zenodo `7711810`, MIT
- **게이트 통과 조건은 AND**: `min_accuracy` ∧ `min_macro_f1` ∧ `max_invalid_rate`
- 채점 규칙: 부분 점수 없음 · 스키마 위반 = 오답 · **유사도 매칭 금지**
- `confidence`는 채점에 쓰지 않는다
- 케이스 수: **대회 데모 N=30–50**, 본편 통계 판정 n=300 이상
  - n=50이면 SE ≈ 0.05로 편차 임계값과 같아 **판정 불가**. 보고서에 명시
- Sanity floor 3종(상수·난수·스키마 위반)이 전부 FAILED여야 골든셋을 신뢰

---

## 4. 대회 범위 (Contest v0.3)

전문: [`ops/Contest_MVP_2026.md`](./ops/Contest_MVP_2026.md) · 체크리스트: [`ops/contest-submission-checklist.md`](./ops/contest-submission-checklist.md)

- 출품 ~**8/27**. 2차에 **라이선스 검증**
- Must: M1–M13, M15–M21, **M25**
- Non-goal: UI · tenant/public · 자동 재할당 · **사전학습 가중치**
- 밀리면 버려도 됨: A/B → WS→폴링 → heartbeat → sanity 축소
- **절대 안 버림: M25 · M4(단일 demo) · M11(게이트 사슬)**

---

## 5. 미결 항목

| # | 내용 | 기한 |
|---|------|------|
| 1 | `contest@oss.kr` 문의 (배점·소스 제출 형식) | 회신 무관 진행 |
| 2 | EuroSAT 핀 + N=40 + scratch 실게이트 실측(acc≈0.70). 임계 0.68/0.65 보정 | 실측 완료 |
| 3 | `min_accuracy` — **0.68** (가정 0.75는 실측 위였음) | 보정됨 |
| 4 | A/B Must **실측 Within**(diff≈0.047) · 문서·영상에 epoch/SE 한계 명시 (SD-001 closed) | 반영 중 |
| 5 | 전역 `~/.claude/CLAUDE.md`의 GitHub 계정 정정 | 급하지 않음 |

---

## 6. 이 문서 쓰는 법

- **자동 로드 금지.** `CLAUDE.md`는 짧게, 이 파일은 `@docs/context-handoff.md`
- 결정이 바뀌면 §1만 고친다. 위반·함정은 `docs/error/`만 고친다
- 세션 상태 = `STATE.md`, 이력 = `docs/history/CHANGELOG.md`, 지도 = `docs/INDEX.md`
