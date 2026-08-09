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
| 45–75 | 실게이트 + **사이클** | `bash scripts/demo.sh` — **PASSED · dummy=false** 정지. **사용자는 Core만 호출한다** — 노드 주소가 명령 어디에도 없다는 점을 짚는다 |
| (컷) | sanity | `scripts/sanity.ps1` — 3종 FAILED (짧게 잘라 넣기 가능) |
| 75–105 | Task 완주 | `demo.ps1` 후반 Task 성공 출력 |
| 105–135 | 위반 1–3 | `scripts/demo_violations.ps1` — `NOTICE REJECTED` / 제약명 **천천히** |
| 135–150 | 위반 4–6 | 같은 스크립트 나머지 · 표 슬라이드 병치 |
| 150–160 | **A/B 교체 (UC-7)** | `bash scripts/proof_ab.sh` — 같은 case, Agent 두 개, 둘 다 완결. 자막: "같은 답"이 아니라 **"계약 하한이 유지된다"** |
| **160–170** | **증적 (신설)** | `demo.sh` 마지막 줄 또는 `GET /v1/tasks/{id}` — **assignment · node · agent · status**가 화면에. 이게 없으면 증적은 주장으로 남는다 |
| 170–180 | GitHub | https://github.com/gncorpseo-commits/capnet · README 5분 기동 |

---

## 2. 자막 번인 문장 (복붙)

1. 능력만 요구하면 됩니다. 어떤 AI가, 어느 기계에서 도는지는 몰라도 됩니다.  
2. 그런데 "몰라도 된다"는 "아무 데서나 돈다"가 아닙니다.  
3. 승인하지 않은 신뢰 도메인으로는 **DB가 라우팅을 거절**합니다.  
4. 사용자는 Core만 호출합니다. 노드 주소를 알지 못하고, 알 필요도 없습니다.  
5. 노드도 Core가 배정하지 않은 일은 거부합니다.  
6. 그리고 누가·무엇으로·언제 실행했는지 **증적이 남습니다**.  
7. 위반은 앱 if가 아니라 PostgreSQL이 REJECTED.  
8. CapNet OSS — compose로 재현.

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
