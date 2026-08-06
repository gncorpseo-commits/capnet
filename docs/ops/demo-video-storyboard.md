# CapNet 3분 시연 영상 스토리보드

**상태:** 촬영 전 체크리스트. 정본 타임라인은 [`Contest_MVP_2026.md`](./Contest_MVP_2026.md) §7.  
**갱신:** 2026-08-06

## 촬영 규칙

| # | 규칙 | 이유 |
|---|------|------|
| V1 | **자막 번인**(한국어) | 심사 환경에서 음소거 재생 가능 |
| V2 | 터미널 폰트 **18pt 이상** | M25 증거는 **제약 이름 문자열** |
| V3 | 첫 10초에 “무엇을 볼 것인지” 한 줄 | 3분 중 첫 인상 |
| V4 | mp4 / H.264 / 1080p / **200MB 이하** | 업로드 실패 방지 |
| V5 | 파일 + 비공개 링크 **둘 다** 준비 | 제출 방식 미확정 대비 |

## 타임라인 (180초)

| 초 | 화면 | 자막·내레이션 |
|----|------|----------------|
| 0–10 | CapNet 로고 + 한 줄 | “같은 AI 이름 뒤에 다른 구현이 숨을 수 있습니다. CapNet은 DB가 막습니다.” |
| 10–20 | 문제 슬라이드 | “스토어가 아니라 **채점 가능한 Capability 계약**” |
| 20–45 | `docker compose up` + health | “Postgres + Core + Node 3대. 제약은 스키마에 baked-in.” |
| 45–75 | `scripts/demo.ps1` 터미널 | “scratch 실게이트 PASSED (acc≈0.70, dummy=false). sanity는 FAILED.” |
| 75–105 | Task 완주 출력 | “User는 Agent를 몰라도 Task가 완료됩니다.” |
| **105–135** | **`demo_violations` 1–3종** | **team→public · 게이트 미통과 · L→S** — `NOTICE REJECTED:` 줄 천천히 |
| **135–150** | **4–6종 결과 표** | lease 강등 · 가중치 교체 · gate_run 강등 — **FK 이름** 보이게 |
| 150–170 | 게이트 사슬 다이agram (보고서 §3) | “PASSED는 team gate-runner 실측 run만 인정.” |
| 170–180 | GitHub + README | “CapNet OSS — compose로 5분 재현.” |

## 촬영 전 확인

- [ ] `docker compose down -v && docker compose up --build -d` 깨끗한 1회
- [ ] `scripts/train_scratch.ps1` 완료 · `eurosat_scratch.safetensors` 존재
- [ ] `demo.ps1` → PASSED · `sanity.ps1` → 전부 FAILED
- [ ] `demo_violations.ps1` → 6종 REJECTED
- [ ] 터미널 배경 어두운 테마 · 스크롤 속도 느리게

## A/B 미구현 시

150–170초는 UC-7 A/B 대신 **게이트 사슬 다이agram**을 쓴다 (Contest v0.3 §7 확정).
