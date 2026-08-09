# 촬영일 런북 (3분 영상)

**목적:** 스토리보드([`demo-video-storyboard.md`](./demo-video-storyboard.md))를 **명령 순서**로 고정.  
**갱신:** 2026-08-07  
**촬영일: 2026-08-23 (확정).** 8/24 편집·업로드 → URL 확보. 밀 수 없다 — 영상이 보고서를 막는다.  
**A/B: UC-7 촬영 가능해졌다** (2026-08-08 `scripts/proof_ab.sh`). Agent A·B가 각각 실게이트를 통과했고, 동일 case를 `requestedAgentId`로 교차 배정해 둘 다 완결됐다. 150–170초를 A/B 교체 화면으로 쓴다. **자막에 "학습 데이터 기준" 병기 필수** — 골든셋이 학습셋 안이다(SD-008).

---

## 0. 촬영 30분 전

```powershell
cd C:\Users\wjsto\pjt\capnet
docker compose down
docker compose up --build -d
# health
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8001/health
```

- 터미널: 어두운 테마 · 폰트 **18pt+** · 창 가로로 넓게  
- OBS/클립챔프: 1080p · 자막 레이어 준비  
- `apps/node/weights/eurosat_scratch.safetensors` 존재 확인

---

## 1. 타임라인 ↔ 명령

| 초 | 보여줄 것 | 명령 / 화면 |
|----|-----------|-------------|
| 0–10 | 로고·한 줄 | 슬라이드 (녹화 시작) |
| 10–20 | 문제 한 장 | 슬라이드 |
| 20–45 | compose 기동 | 위 `compose up` 로그 또는 이미 Up인 health JSON |
| 45–75 | 실게이트 | `powershell -ExecutionPolicy Bypass -File scripts/demo.ps1` — **PASSED · dummy=false** 줄 정지 |
| (컷) | sanity | `scripts/sanity.ps1` — 3종 FAILED (짧게 잘라 넣기 가능) |
| 75–105 | Task 완주 | `demo.ps1` 후반 Task 성공 출력 |
| 105–135 | 위반 1–3 | `scripts/demo_violations.ps1` — `NOTICE REJECTED` / 제약명 **천천히** |
| 135–150 | 위반 4–6 | 같은 스크립트 나머지 · 표 슬라이드 병치 |
| 150–170 | **A/B 교체 (UC-7)** | `bash scripts/proof_ab.sh` — 같은 case, Agent 두 개, 둘 다 완결. `honored=true` 강조 |
| 170–180 | GitHub | https://github.com/gncorpseo-commits/capnet · README 5분 기동 |

---

## 2. 자막 번인 문장 (복붙)

1. 같은 AI 이름 뒤에 다른 구현이 숨을 수 있습니다. CapNet은 DB가 막습니다.  
2. 스토어가 아니라 채점 가능한 Capability 계약.  
3. scratch 실게이트 PASSED · sanity는 FAILED.  
4. User는 Agent를 몰라도 Task가 완료됩니다.  
5. 위반은 앱 if가 아니라 PostgreSQL이 REJECTED.  
6. CapNet OSS — compose로 재현.

---

## 3. 촬영 후

- [ ] mp4 H.264 1080p · ≤200MB · ≤3분  
- [ ] 음소거로 1회 재생해 자막만으로 이해되는지 확인  
- [ ] YouTube **비공개** 업로드 → URL을 `contest-report-form-draft.md` `[TODO: YouTube URL]`에 기입  
- [ ] 원본 파일도 로컬 보관 (포털이 파일 요구할 때)

---

## 4. 양식 이식 (영상과 병렬 가능)

1. 주최 양식 `…결과보고서_접수번호(팀명).docx|hwp` 열기  
2. 회색 가이드 페이지 삭제  
3. [`contest-report-form-draft.md`](./contest-report-form-draft.md) 문장 복사 (본문 ≤5p)  
4. 붙임1 SBOM · 붙임2 유형3 + raw 가중치 URL  
5. PDF 동시 저장 → 포털 zip
