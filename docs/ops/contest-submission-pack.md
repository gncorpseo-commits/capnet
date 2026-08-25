# CapNet 출품 제출 패킷 (915 · 지엔)

> **한 파일에 모은 제출 체크리스트.** 정본 일정·규칙은 [`contest-submission-checklist.md`](./contest-submission-checklist.md).  
> **최종 마감 2026-08-27** · 내부 마감 **2026-08-26 12:00**  
> 갱신: 2026-08-25

---

## 0. 팀·접수

| 항목 | 값 |
|------|-----|
| 팀명 | **지엔** |
| 접수번호 | **915** |
| 프로젝트명 | **CapNet** |
| 저장소 | https://github.com/gncorpseo-commits/capnet |
| 제출물 (F1) | **결과보고서 · 시연영상(≤3분) · 소스코드** |

---

## 1. 시연 영상 — ✅ 편집 완료 (2026-08-23)

### 로컬 파일 (정본)

| 항목 | 값 |
|------|-----|
| 경로 | `C:\Users\wjsto\AppData\Local\CapCut\Videos\GN_2026오픈소스개발자대회_출품작_CAPNET.mp4` |
| 길이 | **약 2분 53초** (172.9초) — ≤3분 ✅ |
| 용량 | **약 38 MB** — ≤200MB ✅ |
| 해상도 | **1920×1080** |
| 코덱 | H.264 + AAC |

> 동일 용량의 `…CAPNET  - 복사본.mp4`가 옆에 있을 수 있음. **제출·업로드는 공백 없는 `…CAPNET.mp4`만** 사용.

### YouTube (일부 공개)

| 항목 | 값 |
|------|-----|
| URL | **https://youtu.be/RjFiGpmLTbk** |
| 업로드 | 2026-08-23 · 일부 공개 · 아동용 아님 |

### 아직 할 일

- [ ] **음소거 1회** 재생 — 자막만으로 이해되는지
- [x] YouTube **일부 공개** 업로드 → URL 기입 ✅
- [x] URL을 [`contest-report-form-draft.md`](./contest-report-form-draft.md) 반영 ✅
- [ ] 포털 제출용 **mp4 파일**도 함께 준비 (링크만 vs 파일 업로드 — 둘 다 대비)

### 제출 요건 (V1–V5)

- [x] 자막 번인 (한국어)
- [x] ≤3분 · 1080p · H.264 · ≤200MB
- [x] **일부 공개 링크** ✅ · [ ] mp4 파일 (포털 대비)

---

## 2. 결과보고서 — ✅ docx 이식 완료 · PDF 남음

### 원고·붙여넣기

| 자료 | 경로 |
|------|------|
| 양식용 압축 문장 | [`contest-report-form-draft.md`](./contest-report-form-draft.md) |
| 상세 보조 | [`contest-report-draft.md`](./contest-report-draft.md) |
| 게이트 다이어그램 | [`gate-chain-slide.md`](./gate-chain-slide.md) |
| 위반 표 | [`docs/error/pg-violations.md`](../error/pg-violations.md) |

### 공식 양식

| 항목 | 값 |
|------|-----|
| 파일명 예 | `2026 오픈소스 개발자대회 결과보고서_915(지엔).pdf` (hwp/docx 원본 + PDF) |
| 본문 | **2쪽 고정 표** — 칸 크기에 맞춰 압축 |
| 붙임1 | SBOM · **가로** · 최대 10행 |
| 붙임2 | AI 모델·라이선스 (유형 3) |

### 채워 둔 파일

| 항목 | 경로 |
|------|------|
| docx (제출용) | [`2026 오픈소스 개발자대회 결과보고서_915(지엔).docx`](./2026%20오픈소스%20개발자대회%20결과보고서_915(지엔).docx) · Downloads 동명 파일도 갱신됨 |
| 빈 양식 백업 | Downloads `…_빈양식백업.docx` |

### 체크리스트

- [x] 회색 예시·빨간 안내 비움 · 본문·붙임1·2 이식 (2026-08-25)
- [x] 시연 영상 URL 기입
- [x] 붙임2 §4 상용 AI 보조 **약 30%**
- [ ] **팀 인원·참가부문** Word에서 접수와 대조 (현재 초안: 3명 · 일반)
- [ ] PDF 저장 · 포털 zip

### 표지 필수 칸

| 칸 | 기재 |
|----|------|
| 프로젝트 등록 URL | https://github.com/gncorpseo-commits/capnet |
| 시연영상 | https://youtu.be/RjFiGpmLTbk |

---

## 3. 소스코드 — ❌ Release·zip 미발행

### Release (8/25–26)

```bash
# 태그 (main 머지·검증 후)
git tag v0.1.0-contest
git push origin v0.1.0-contest

# zip (.git 제외)
git archive --format=zip --prefix=capnet/ v0.1.0-contest -o capnet-v0.1.0-contest.zip
```

- [ ] GitHub **Release** `v0.1.0-contest` 발행 (URL + zip)
- [ ] zip **≤50MB** · 압축 해제 후 파일 확인
- [ ] `bash scripts/check_release.sh` (태그 또는 HEAD)

### 저장소에 있어야 함

- [x] `LICENSE` · `NOTICE` · `README` · `THIRD-PARTY-LICENSES.md` · `sbom.json`
- [x] 데모 가중치 **5종** + `placeholder` (삭제 금지)

### 넣지 않음

- EuroSAT 원본 zip · 실험 가중치(`*_ho*`) · `.env` · 캐시

---

## 4. 라이선스 방어 팩 (보고서·Release와 함께)

| # | 파일 | 상태 |
|---|------|------|
| L1 | `NOTICE` | ✅ |
| L2 | `THIRD-PARTY-LICENSES.md` | ✅ |
| L3 | `sbom.json` | ✅ |
| L4 | 보고서 9절 — 사전학습 미사용·scratch만 | 🔶 |
| L5 | EuroSAT RGB Zenodo 7711810 · 원본 미동봉 | ✅ |

---

## 5. 제출 직전 기계 점검

```powershell
cd C:\Users\wjsto\pjt\capnet
docker compose down -v
docker compose up --build -d
pwsh -File scripts\demo.ps1
pwsh -File scripts\sanity.ps1
pwsh -File scripts\demo_violations.ps1
```

```bash
# WSL — Release 직전
bash scripts/run_tests.sh
bash scripts/clean_room.sh
bash scripts/prod_room.sh
python3 scripts/check_submission.py
bash scripts/check_release.sh
```

- [ ] `check_submission.py` 통과 (워킹트리 깨끗할 때)
- [ ] `acc=0.8500` · 위반 6× REJECTED · sanity 3× FAILED

> 영상·포털 업로드는 `check_submission` **밖**이다.

---

## 6. 부록2 Ⅶ — 제출 전 9항목

| # | 점검 | CapNet |
|---|------|--------|
| 1 | 가중치 공개 다운로드 가능 | raw URL HTTP 200 |
| 2 | 기반 모델 라이선스 확인 | **해당 없음** (유형 3) |
| 3 | 외부 상용 AI API 없이 동작 | 로컬 torch만 |
| 4 | OSI 라이선스 파일 | Apache-2.0 `LICENSE` |
| 5 | 유형2·3 가중치 공개·접근 확인 | main 2종+ |
| 6 | OSS·모델 출처·라이선스 | 붙임1 · THIRD-PARTY · sbom |
| 7 | 붙임2 전 항목 · 없으면 「해당 없음」 | 빈칸 금지 |
| 8 | 상용 AI 보조도구 범위 (§4) | ✅ 약 30% |
| 9 | 저장소 Public | ✅ · 수상 시 **5년 공개** |

---

## 7. 제출 순서 (직렬 — 영상 URL이 보고서를 막음)

| 순서 | 날짜 | 할 일 |
|------|------|--------|
| 1 | ✅ 8/23 | 촬영 · CapCut 편집 완료 |
| 2 | **지금** | 양식 이식 · PDF · AI 비율 확정 |
| 3 | 8/24–25 | 양식 이식 · PDF · AI 비율 확정 |
| 4 | 8/25–26 | `v0.1.0-contest` Release · zip · `check_*` |
| 5 | **8/26 12:00** | 포털 zip · 내부 마감 |
| 6 | 8/27 | 최종 제출 (예비일) |

---

## 8. 포털 zip에 넣을 것 (확인 후 체크)

- [ ] 결과보고서 PDF (`_915(지엔)`)
- [ ] (요구 시) hwp/docx 원본
- [ ] 시연 mp4 **또는** URL만 (주최 안내에 따름 — **둘 다 준비**)
- [ ] (요구 시) 소스 zip 또는 repo URL

---

## 9. 관련 문서

| 문서 | 용도 |
|------|------|
| [`contest-submission-checklist.md`](./contest-submission-checklist.md) | 정본·갭·일정 |
| [`contest-report-form-draft.md`](./contest-report-form-draft.md) | 보고서 붙여넣기 |
| [`shoot-day-runbook.md`](./shoot-day-runbook.md) | 촬영·자막 §2 |
| [`capcut-edit-guide.md`](./capcut-edit-guide.md) | CapCut 가이드 |
| [`regulation-compliance.md`](./regulation-compliance.md) | 대회 규정 대응 |

---

## 10. 한 페이지 요약 — 아직 ❌

| # | 항목 | 상태 |
|---|------|------|
| G7 | 보고서 PDF/hwp | 🔶 | docx ✅ · **PDF만** 남음 |
| G8 | YouTube ≤3분 | ✅ | https://youtu.be/RjFiGpmLTbk · mp4 로컬 보관 |
| G9 | Release + 포털 zip | ❌ |

**다음 액션:** Word에서 PDF 저장 · `v0.1.0-contest` Release · 포털.
