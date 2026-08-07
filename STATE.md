# STATE — 현재 작업 상태

> 세션 인계용 단기 상태판. 결정·미결은 `docs/context-handoff.md`, 이력은 `docs/history/CHANGELOG.md`, 지도는 `docs/INDEX.md`.
> **갱신: 2026-08-08**

---

## 대회 정보

팀명 **지엔** · 팀장 **서우석** · 접수번호 **915**
자유과제 / 세부과제 **인공지능** · 사회문제해결 항목 공란
출품작 제출 **8/27(목) 18:00**, 1차 평가 9.3, 멘토링 9.18–10.9, 2차 10.12–10.28, 시상식 12.4

전체 일정: `docs/ops/contest-submission-checklist.md` · https://osscontest.kr/notice/39

---

## 지금 어디인가

**출품 1순위** (양식·영상·포털). 본편 A/B **실측 완료 · Must 아님**.

| 트랙 | 상태 |
|------|------|
| **출품** | 런북·양식 초안 있음. **docx/hwp 이식 · 촬영 · YouTube · 포털** 남음 |
| **본편** | B 학습·n300·compare 끝. `|acc_A−acc_B|=0.07 > 0.05` → **EXCEEDS** · Must 승격 **비권장** |

실측 (과장 금지):

| 항목 | 결과 |
|------|------|
| scratch N=40 A | acc=0.70 · f1≈0.688 · PASSED |
| sanity | 3종 FAILED |
| 임계 | 0.68 / 0.65 |
| n=300 A (`TinyEuroSAT`, ~40ep) | acc≈0.817 · f1≈0.814 · PASSED |
| n=300 B (`TinyEuroSATB`, 20ep) | acc≈0.887 · f1≈0.887 · PASSED |
| paired n=300 | **abs_diff=0.07 · EXCEEDS_THRESHOLD** · Must 아님 |
| 비고 | epoch 수 A/B 불일치(40 vs 20). 공정 재실험 시 epoch 맞출 것 |

## 체크리스트

1–5, 7–11. [x] (기존)
6. [ ] 시연 영상 YouTube · 공식 양식 이식 · PDF · 포털
12. [x] Agent B 학습 · n300 · compare_ab 기록 (Must 아님)

## 아직 아닌 것

- A/B **Must** (실측이 임계 초과 · SD-001 유지)
- `node_credential` DDL · WS/만료 스캐너
- 공식 양식·PDF·유튜브·포털 zip
- epoch 정렬 재학습 (선택)

## 열려 있는 판단

| # | 내용 | 기한 |
|---|------|------|
| 1 | A/B Must — **실측 EXCEEDS → 출품 Must 올리지 말 것** (SD-001) | 8/11 확정 권고 |
| 2 | 중복수혜 팀 확인 | 제출 전 |

## 함정

`@docs/error/pitfalls.md` · INSERT…SELECT · team runner만 · safetensors만
