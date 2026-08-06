# CapNet × 2026 오픈소스 개발자대회 운영규정 준수 근거

**문서 목적:** 운영규정(2026.06) 조항과 CapNet 출품 상태를 대조하고, **준수 근거(어디에 보이는지)**를 남긴다.  
**근거 규정:** 2026년 오픈소스 개발자대회 운영규정  
**출품명:** CapNet · 팀 **지엔** · 접수번호 **915** · 자유과제(인공지능)  
**저장소:** https://github.com/gncorpseo-commits/capnet  
**갱신:** 2026-08-07  
**상태 범례:** ✅ 충족 · ⚠️ 제출 전 마무리 필요 · N/A 해당 없음

> 과장 금지. “충족”은 저장소·문서에 **검증 가능한 산출물**이 있을 때만 쓴다.  
> 서식 초안 문장: [`contest-report-form-draft.md`](./contest-report-form-draft.md)

---

## 1. 요약 판정

| 영역 | 판정 | 한 줄 |
|------|------|--------|
| 제8조 소스 라이선스 | ✅ | Apache-2.0 + NOTICE + THIRD-PARTY + sbom |
| 제9조 AI 모델 | ✅* | 유형 3 · 로컬 추론 · 가중치 raw URL **승인 없이 200 OK** · 붙임2는 양식에 이식 |
| 제10조 소스 공개 | ✅ | Public GitHub · compose 재현 |
| 제11–12조 제출·정보 | ⚠️ | 양식·영상·포털 제출 진행 중 |
| 제13–15조 결격·중복수혜 | N/A/팀 | 부정 없음(자체) · 정부지원은 팀 확인 |
| 상용 API 전용 | ✅ | 해당 없음 |

\*가중치 공개 URL 실측: 2026-08-07 `curl -I` → HTTP 200 · Content-Length 378784. 붙임2 서식란에 동일 URL을 옮기면 제9조②-3 충족.

---

## 2. 조항별 대조

### 제7조 — 저작권

| 요건 | 판정 | 근거 |
|------|------|------|
| 저작권 참가자 귀속 | ✅ | `LICENSE` · `NOTICE` Copyright 2026 CapNet Contributors |

### 제8조 — OSI 라이선스

| 요건 | 판정 | 근거 |
|------|------|------|
| 직접 작성 코드 OSI | ✅ | `LICENSE` = Apache-2.0 |
| 비상업·학술 전용 금지 | ✅ | 프로젝트 Apache-2.0 · EuroSAT MIT · **사전학습 미사용**(D6) |
| 제3자 출처·라이선스 | ✅ | `THIRD-PARTY-LICENSES.md` · `NOTICE` · `sbom.json` · 붙임1 초안 |

### 제9조 — AI 모델

| 요건 | 판정 | 근거 |
|------|------|------|
| 오픈웨이트 이상 | ✅ | 자체 scratch 가중치 공개 |
| **유형 3** 자체 학습 | ✅ | TinyEuroSAT · `apps/train/train_scratch.py` · 기반 모델 없음 |
| 가중치 전체 · 승인 없이 공개 | ✅ | 아래 URL · HTTP 200 실측 |
| 학습·추론 코드 OSI | ✅ | train/infer/score_gate + Apache-2.0 |
| 상용 API 단순 연결 금지 | ✅ | Node 로컬 torch · compose 내부 HTTP |
| 붙임2 제출 | ⚠️ | [`contest-report-form-draft.md`](./contest-report-form-draft.md) §붙임2 → 공식 양식 이식 |
| 상용 AI 보조(§5) | 기재 | 붙임2 §4 초안 · 유형 체크 대상 아님 |

**가중치 공개 URL (제9조②-3):**

- HTML: https://github.com/gncorpseo-commits/capnet/blob/main/apps/node/weights/eurosat_scratch.safetensors  
- Raw(다운로드): https://raw.githubusercontent.com/gncorpseo-commits/capnet/main/apps/node/weights/eurosat_scratch.safetensors  
- sha256: `0c5b16cef57d11e26c58319d80cd47a41a8b8d740ba3470c1d801e7fb9356b5b` (`eurosat_scratch.meta.json`)  
- 용량: 378,784 bytes · 형식: safetensors · 아키텍처: TinyEuroSAT · pretrained: false  

### 제10조 — 소스 공개

| 요건 | 판정 | 근거 |
|------|------|------|
| 전체 소스·심사 가능 | ✅ | Public · `README` 5분 기동 · `scripts/demo` |
| 수상 시 5년 Public | 운영 약속 | 수상 시 유지 |

### 제11–12조

| 요건 | 판정 | 근거 |
|------|------|------|
| 마감 내 제출 | ⚠️ | ~2026-08-27 18:00 |
| 정부지원 이력 | 팀 확인 | 해당 시 중복수혜 확인서 |

### 제13–16조

| 요건 | 판정 | 근거 |
|------|------|------|
| 저작권 침해·대리개발 결격 | 방어 | 자체 구현 · 출처 명시 |
| 주제 정합 | ✅ | 인공지능 · Capability 계약 OSS |

---

## 3. 별표 2 체크리스트

| 항목 | 판정 |
|------|------|
| 가중치 무상·대중 공개 | ✅ (raw URL 200) |
| 라이선스·약관 충돌 없음 | ✅ |
| 독립 구동(로컬) | ✅ compose |
| Closed API 전용 아님 | ✅ |
| 학습·추론 OSI | ✅ |
| 붙임2 | ⚠️ 양식 이식 |

---

## 4. 내부 절대 규칙과의 정합

| 내부 | 규정 |
|------|------|
| D5 safetensors만 | 가중치 형식 |
| D6 사전학습 금지 · EuroSAT scratch | 유형 3 · 제8조③ 회피 |
| D4 team gate-runner만 | 게이팅 무력화 방지 |
| schema 약화 금지 | 재현·검증 |

---

## 5. 미완 (⚠️만)

1. 공식 양식 ≤5P + 붙임1·2 이식 (초안은 `contest-report-form-draft.md`)  
2. 시연 ≤3분 YouTube  
3. PDF · 포털 zip · 제출 완료·메일  
4. (해당 시) 중복수혜 확인서  

---

## 6. 검토

| 역할 | 일자 | 확인 |
|------|------|------|
| 초안 | 2026-08-07 | 가중치 URL HTTP 200 실측 |
| 팀장 검토 | | |
