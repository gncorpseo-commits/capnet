# STATE — 현재 작업 상태

> **갱신: 2026-08-08** · 종착점 = **Phase 3+ 전체** (D16) · README는 상태 비보유(링크만)

---

## 대회 정보

팀명 **지엔** · 접수번호 **915**  
일정·제출 정본: [`docs/ops/contest-submission-checklist.md`](docs/ops/contest-submission-checklist.md)

---

## 지금 어디인가

**종착점을 Phase 3+ 로드맵 전체로 확장**(D16 · SD-006). Contest MVP는 종료가 아니라 Phase 1 슬라이스.  
계단·진입조건: [`docs/design/roadmap.md`](docs/design/roadmap.md)

**단기 순서는 그대로다.** 출품 패키지(양식·영상·포털)가 1순위 병목이고, 체크리스트 §5.1의 "미완이면 본편 중단"은 유지한다.

| 트랙 | 상태 |
|------|------|
| **출품 (1순위)** | 양식 이식 · 영상 · YouTube · Release/포털 — **전부 미완** |
| **Phase 1 완주** | 잔여 3건 (아래) → §7.2 판정 리포트. 대회 제출 후 착수 |
| **Phase 2+** | §7.2 **Go 전에는 코드 금지** (기획서 §13) |
| **문서 위생** | README stable-only · 일정 정본 = checklist |
| **역할** | finn · toma · **pl**(동급) · master(merge) — [`github-team-guide`](docs/guide/github-team-guide.md) v1.3 |

### Phase 1 §7.1 좌표 (2026-08-08 코드 실측)

| # | 증명 대상 | 상태 |
|---|-----------|------|
| 1 | `image.classify@1` + 골든셋 | ✅ |
| 2 | Agent **A, B** PASSED | ⚠️ **A만** — B는 DB 증서 없음 |
| 3 | 증명 모드 A/B 교체 할당 | ⚠️ **미실행** — 배관(`requested_agent_id`)은 있음, B가 없어 못 돌림 |
| 4 | 편차 < 0.05 | ✅ 0.0467 — **사슬 밖 측정** |
| 5 | Product Track Agent 선택 없음 | ✅ |

실측:

| 항목 | 결과 |
|------|------|
| N=40 A | acc=0.70 · f1≈0.698 · PASSED |
| n=300 A (80ep) | acc=0.880 · f1≈0.880 |
| n=300 B (40ep) | acc=0.927 · f1≈0.927 |
| paired | **abs_diff≈0.0467 · WITHIN_THRESHOLD** |
| 주의 | epoch 불일치 · SE≈0.019 ≈ 임계 근처 · **`gate_run` 사슬 미경유** |
| 통과율 20–80% | **미실측** (모집단 1) |

## 체크리스트

6. [ ] 양식·영상·포털 ← **지금 여기**
13. [x] A/B n300 Within (사슬 밖 실측)
14. [ ] Phase 1 완주 3건 → 판정 리포트 (제출 후)

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 1 | 중복수혜 팀 확인 | 제출 전 |
| 2 | (선택) epoch 맞춘 재실험으로 SE 여유 확보 | 본편 |
| 3 | 마이그레이션 체계 (SD-007) — Phase 2 선결 | Phase 2 착수 전 |
