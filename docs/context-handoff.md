# CapNet 컨텍스트 핸드오프

> 세션 인계용 **결정·미결** 요약. 상세 위반·함정은 `docs/error/`에 둔다 (중복 금지).
> 자동 로드되지 않는다. 필요할 때 `@docs/context-handoff.md`로 부른다.
>
> 문서 지도: [`INDEX.md`](./INDEX.md) · 주간 상태: [`../STATE.md`](../STATE.md)  
> 최종 갱신: 2026-08-10 · 일정 정본은 checklist (이 파일에 날짜 표 두지 않음)

---

## 1. 확정된 결정과 근거

바꾸려면 근거를 먼저 반박해야 하는 것들이다.

| # | 결정 | 근거 |
|---|------|------|
| D1 | ~~MVP 증명 대상 = Capability 추상화 성립~~ → **D17로 개정 (2026-08-09)** | 원문 근거는 유효하나 "대체 가능한가"가 홀드아웃에서 반증됐다 |
| D17 | **증명 대상 = Capability 계약이 품질 하한을 보장하는가.** 등가성은 계약 조건이 아니라 **관측값**이다 | 2026-08-09. 하한형 게이트는 쌍별 편차를 유계로 만들 수 없다(SD-009). 기획서 v4.6 §7.1. **기준을 실패한 뒤 바꾼 변경이며 그 사실을 기록한다** — 대신 4번을 약화하지 않고 반증 가능한 새 조건으로 교체했다 |
| D18 | **Capability = 인터페이스 계약** (스키마·전처리·실행조건). 골든셋 게이트는 **선택적 품질 프로파일**. 제품 주장은 «능력만 요구 → 승인 도메인 안 라우팅 → 실행 증적» | 2026-08-09. **근거는 실패가 아니라 기획서 §1 원래 취지**다. 채점 기계가 서사를 점령했던 것을 되돌린 것. 기획서 v4.7 §1·§4.4. 골든셋 3구멍(표본·분포·게이밍)이 계약 핵심에서 부속 한계로 내려감 |
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
| D16 | **프로젝트 종착점 = Phase 3+ 로드맵 전체** (기획서 §9). Contest MVP는 Phase 1의 슬라이스이며 **종료 지점이 아니다**. 8/27은 그 슬라이스의 외부 마감일 | 2026-08-08 결정. 실행 계단·진입조건은 [`design/roadmap.md`](./design/roadmap.md). 단 §7.2 Go 없이 Phase 2 코드 금지(§13)는 그대로 |
| D19 | **제품 유통 목표** = Open Agent + (선택) Open Compute + **User-defined Trust Domain**. 경제는 **선택·비기초**. 1호 유통 = 초대 team/tenant · 저민감 public만. Private Community ≠ 데이터 안전. 세대·금지는 [`design/product-distribution.md`](./design/product-distribution.md) | 2026-08-10. 기획서 §8·스키마 `trust_domain`과 정합. “아무 데이터·아무 Node” 공개 SaaS는 이 세대 밖 |

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

- **일정·제출 정본:** [`ops/contest-submission-checklist.md`](./ops/contest-submission-checklist.md) (공지 39 인용 포함)
- **시나리오·UC 정본:** [`ops/Contest_MVP_2026.md`](./ops/Contest_MVP_2026.md)
- Must / Non-goal / 버릴 순서: Contest_MVP §4 · §3.2 (날짜는 checklist만)

---

## 5. 미결 항목

| # | 내용 | 기한 |
|---|------|------|
| 1 | `contest@oss.kr` 문의 (배점·소스 제출 형식) | 회신 무관 진행 |
| 2 | EuroSAT 핀 + N=40 + scratch 실게이트 실측(acc≈0.70). 임계 0.68/0.65 보정 | 실측 완료 |
| 3 | `min_accuracy` — **0.68** (가정 0.75는 실측 위였음) | 보정됨 |
| 4 | A/B: 누출 골든 Within(≈0.047)는 **무효**. 홀드아웃 n300은 EXCEEDS(≈0.097). Must 승격 보류 · 한계 명시 (SD-001) | 문서 반영 |
| 5 | 전역 `~/.claude/CLAUDE.md`의 GitHub 계정 정정 | 급하지 않음 |
| 6 | **Phase 1 완주 잔여 3건** — Agent B 실게이트 PASSED · 증명 모드 교체 할당(M14/UC-7) · 통과율 20–80% 실측 → §7.2 판정 리포트 | 대회 제출 후 ([`design/roadmap.md`](./design/roadmap.md) §2) |
| 7 | ~~마이그레이션 체계 부재~~ → **해소 2026-08-10.** 순방향 러너·원장·정적 검사. [`guide/migrations.md`](./guide/migrations.md). 실 볼륨 적용은 승인 대기 | 승인 후 즉시 |
| 8 | **제품 유통 v제품-0→1** — SD-007 ✅ → 다음은 **P2-1(tenant 운용)**. 단 `image.classify@1` 은 `trust_domain_min='team'` 이라 tenant task 를 원천 차단한다 — tenant 유통엔 `trust_domain_min='tenant'` capability(+골든셋)가 선행 | 출품 후 · Phase 2 |
| 9 | **SD-013 골든셋 sha 3중 불일치** — 매니페스트 `c21d9ef7…` / 문서 `0341d121…` / seed `c8254bcb…`. 새 볼륨 capability 가 리포에 없는 골든셋을 가리킨다 (D15) | **촬영 8/23 전** |

---

## 6. 이 문서 쓰는 법

- **자동 로드 금지.** `CLAUDE.md`는 짧게, 이 파일은 `@docs/context-handoff.md`
- 결정이 바뀌면 §1만 고친다. 위반·함정은 `docs/error/`만 고친다
- 세션 상태 = `STATE.md`, 이력 = `docs/history/CHANGELOG.md`, 지도 = `docs/INDEX.md`
