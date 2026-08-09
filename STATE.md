# STATE — 현재 작업 상태

> **갱신: 2026-08-08** · 종착점 = **Phase 3+ 전체** (D16) · README는 상태 비보유(링크만)

---

## 대회 정보

팀명 **지엔** · 접수번호 **915**  
일정·제출 정본: [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md)

---

## 지금 어디인가

**Phase 1 판정 = 보류(HOLD). Phase 2 착수 불가.**  
판정 리포트: [`docs/ops/phase1-verdict.md`](docs/ops/phase1-verdict.md) · 계단: [`docs/design/roadmap.md`](docs/design/roadmap.md)

> 두 판정 축은 형식상 Go였다 (편차 **0.046667** · 통과율 **75.0%** 6/8).  
> 그런데 **골든셋 40/40 · 300/300 케이스가 학습셋 안에 있다** (SD-008).  
> 홀드아웃이 없어 게이트가 능력이 아니라 **학습 데이터 재현**을 잰다 → 판정 자격 미달.  
> 검증: `python3 scripts/check_golden_leakage.py` (exit 2)

**단기 순서는 그대로다.** 출품 패키지가 1순위이고, 체크리스트 §5.1 "미완이면 본편 중단"은 유지한다.  
SD-008은 **제출을 막지 않는다** — 영향받는 건 모델 품질 주장뿐이고 M25·게이트 사슬은 무관하다.

| 트랙 | 상태 |
|------|------|
| **출품 (1순위)** | 양식 이식 ✅ · **촬영 2026-08-23 확정** · 편집·업로드 8/24 · Release/포털 미완 |
| **Phase 1** | P1-1~P1-4 완료 · 판정 **보류** · **P1-5(홀드아웃 재측정)** 이 관문 |
| **Phase 2+** | **차단** — §7.2 Go 없이 코드 금지 (기획서 §13) |
| **문서 위생** | README stable-only · 일정 정본 = checklist |
| **역할** | finn · toma · **pl**(동급) · master(merge) — [`github-team-guide`](docs/guide/github-team-guide.md) v1.3 |

### Phase 1 §7.1 좌표 (2026-08-08 실측)

| # | 증명 대상 | 상태 |
|---|-----------|------|
| 1 | `image.classify@1` + 골든셋 | ✅ |
| 2 | Agent **A, B** PASSED | ✅ 사슬 위 실측 (`dummy=false`) |
| 3 | 증명 모드 A/B 교체 할당 | ✅ `honored=true` · assignment 2건 SUCCEEDED |
| 4 | 편차 < 0.05 | ❌ **미판정** — 값은 재현됐으나 학습셋 위 측정 |
| 5 | Product Track Agent 선택 없음 | ✅ |

실측 (전부 **학습 데이터 위** — SD-008):

| 항목 | 결과 |
|------|------|
| N=40 A / B | 0.7000 / 0.8250 · 둘 다 PASSED |
| n=300 A / B | 0.8800 / 0.9267 |
| paired | abs_diff **0.046667** · SE 0.01876 · WITHIN |
| label_agreement | **0.8933** — 300건 중 32건은 라벨이 다르다 |
| 통과율 (8후보 사다리) | **6/8 = 75.0%** — 밴드 안 |
| sanity floor 3종 | 전부 FAILED (0.100 / 0.025 / 0.000) |
| M25 위반 6종 | 전부 REJECTED |

## 체크리스트

6. [ ] 양식·영상·포털 ← **지금 여기**
13. [x] A/B n300 Within · 사슬 위 교체 할당
14. [x] Phase 1 판정 리포트 → **보류(HOLD)**
15. [~] P1-5 진행 중 — **H1·H2 완료** (분할 도입 · 홀드아웃 골든 겹침 0/300) · H3 재학습 중

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 0 | **촬영 8/23** — 영상이 보고서를 막는다 (YouTube URL이 양식 필수 칸) | **확정** |
| 1 | 중복수혜 팀 확인 | 제출 전 |
| 2 | **H1–H4를 8/27 전에 할지** (CPU 3–4h · 출품 트랙과 경합) | master |
| 3 | A/B를 보고서 Must로 승격할지 (SD-001) | master |
| 4 | 마이그레이션 체계 (SD-007) — Phase 2 선결 | Phase 2 착수 전 |
| 5 | 실험 가중치 `.meta.json` gitignore 처리 | 잡무 |
