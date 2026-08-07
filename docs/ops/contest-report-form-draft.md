# 결과보고서·붙임 초안 문장 (공식 양식 이식용)

**용도:** `2026 오픈소스 개발자대회 결과보고서_접수번호(팀명).docx|hwp`에 **복사해 넣을 검정 문장**.  
**파일명 예:** `2026 오픈소스 개발자대회 결과보고서_915(지엔)`  
**주의:** 양식의 회색 가이드·안내 1페이지는 **삭제**. 본문 **5페이지 이내**. 맑은고딕 10pt·여백 유지.  
**갱신:** 2026-08-07  
**준수 근거:** [`regulation-compliance.md`](./regulation-compliance.md)

시연 영상 URL은 촬영·업로드 후 `[TODO: YouTube URL]`을 교체한다.

---

## 표지·개요 (양식 상단)

| 칸 | 기재 |
|----|------|
| 팀명 | 지엔 |
| 팀 인원(팀장 포함) | (접수와 동일 숫자) |
| 참가부문 | (접수: 학생/일반) |
| 과제유형 | 자유과제 |
| 프로젝트명 | CapNet |
| 프로젝트 등록 URL | https://github.com/gncorpseo-commits/capnet |
| 시연영상 | [TODO: YouTube URL] |

**프로젝트 소개 (1~2줄)**  
채점 가능한 Capability 계약을 PostgreSQL 제약으로 강제하고, EuroSAT scratch 모델을 team gate-runner에서 실측 게이트한 뒤 Task를 완결하는 오픈소스 실행 계층이다.

---

## 개발배경 및 목적

같은 능력 이름을 내건 Agent라도 구현·시점이 다르면 호출자는 대체 가능성을 알기 어렵다. CapNet은 Capability를 **이름 문자열이 아니라 계약**(스키마·골든셋·통과 기준)으로 두고, 게이트·할당 규칙을 애플리케이션 `if`가 아니라 **DB 제약**으로 막아 “불가능한 상태를 표현할 수 없게” 만드는 것을 목표로 한다. 대회 MVP는 팀 플릿에서 이 추상화가 성립함을 재현 가능한 스크립트로 증명한다.

---

## 개발환경

- HW: 팀 노트북(CPU) · Docker Desktop  
- SW: Python 3.11(컨테이너) · PostgreSQL 16 · FastAPI · PyTorch(CPU, gate-runner Node만)  
- 도구: Docker Compose · PowerShell/bash 스크립트 · GitHub  
- 데이터: EuroSAT RGB(Zenodo 7711810, MIT) — 원본 zip 미동봉, 데모 골든 N=40만 레포 포함  
- 가중치: safetensors만 · 사전학습 가중치 미사용  

---

## 시스템 구성 및 아키텍처

- **postgres**: 스키마 v4.4(복합 FK·호환 행렬·게이트 사슬)  
- **core** (:8000): Capability/Agent/Node/Task API · claim(`INSERT … SELECT`) · gate-run  
- **node-m-team** (:8001): team gate-runner · scratch 추론·채점(torch)  
- **node-s-team / node-s-public**: 티어·도메인 위반 데모용  
- 흐름: Capability 계약 → gate_run(PASSED, team runner) → agent_capability_passed → assignment → 추론 완료  
- Node는 자기 trust_domain·compute_tier_max를 **주장하지 않음**(Core/시드 부여)

---

## 프로젝트 상세 내용 (주요 기능)

1. **Capability 계약** `image.classify@1`: closed-set 10라벨 · 입력 64×64→**32×32** · 임계 AND(acc≥0.68 · macro_f1≥0.65 · invalid≤0.02, N=40 실측 보정)  
2. **실게이트**: TinyEuroSAT scratch · `dummy=false` · golden_set_sha256 스냅샷 일치 강제(S3)  
3. **M25**: 위반 6종을 DB가 REJECTED (게이트 미통과 할당, team→public, L→S, lease 중 강등, READY 중 가중치 교체, PASSED 사후 무효화)  
4. **Sanity floor**: 상수·난수·스키마 위반 Agent는 전부 FAILED  
5. 재현: `docker compose up --build` → `scripts/demo` · `sanity` · `demo_violations`

실측(과장 금지): scratch N=40 acc≈0.70 · f1≈0.688 · PASSED. seed dummy PASSED ≠ 실게이트.

---

## 구동 및 시연

```
git clone https://github.com/gncorpseo-commits/capnet.git
cd capnet
docker compose up --build -d
# Windows: scripts/demo.ps1 → sanity.ps1 → demo_violations.ps1
```

가중치가 없으면 `scripts/train_scratch.ps1` 후 compose 재기동.  
기대: demo PASSED·Task 완료 · sanity 전부 FAILED · violations에 `NOTICE REJECTED` 6건.  
OpenAPI: `GET http://127.0.0.1:8000/openapi.yaml`

---

## 향후 확장성 및 기대효과

테넌트 거주지·공공 유휴 Node는 Phase 이후. 단기에는 n≥300 통계 판정·A/B(S2) 승격 여부 결정·`node_credential` DDL(승인 후). 시장성은 “스토어 UI”가 아니라 **계약 런타임·실행 증적**에 둔다.

---

## 혁신성 및 차별성

라우팅 불변식을 앱이 아니라 **PostgreSQL이 거절**한다. 위반 14종 실측·M25 6종 스크립트. 게이트는 team runner만. 사전학습 없이 scratch+safetensors로 2차 라이선스 검증에 맞춤.

---

## 한계점 및 향후 발전 로드맵

- 데모 N=40으로는 대체가능성 편차 0.05 **통계 판정 불가**(본편 n≥300).  
- A/B Must는 미결·미구현.  
- WS·lease 만료 스캐너는 Should.  
- 임계는 가정 0.75가 아니라 실측 보정 0.68/0.65(정직).  

로드맵: 출품 재현 고정 → (승격 시) A/B·n300 → credential·테넌트.

---

## 소감 및 후기

제약을 끄지 않고 `INSERT … SELECT`·게이트 사슬을 지키며 막힐 때마다 DB를 믿도록 팀 규칙을 고정한 것이 가장 큰 학습이었다. 임계를 조작하지 않고 바를 낮춘 결정을 보고서에 남긴 것도 같은 맥락이다.

---

## 붙임1 SBOM (서식 표에 그대로)

우선순위: LGPL 먼저 → 핵심 → 프레임워크. 직접 의존성만. AI 모델은 붙임2.

| 번호 | 라이브러리명 | 버전 | 라이선스 | 공식 저장소 URL | 사용 목적 및 주요 기능 |
|------|--------------|------|----------|-----------------|------------------------|
| 1 | psycopg | 3.2.9 | LGPL-3.0 | https://github.com/psycopg/psycopg | PostgreSQL 드라이버 / 라이브러리로 불러 씀 |
| 2 | FastAPI | 0.116.1 | MIT | https://github.com/tiangolo/fastapi | Core·Node HTTP API / 라이브러리로 불러 씀 |
| 3 | uvicorn | 0.35.0 | BSD-3-Clause | https://github.com/encode/uvicorn | ASGI 서버 / 라이브러리로 불러 씀 |
| 4 | pydantic-settings | 2.10.1 | MIT | https://github.com/pydantic/pydantic-settings | 환경변수 설정 / 라이브러리로 불러 씀 |
| 5 | safetensors | 0.8.0 | Apache-2.0 | https://github.com/huggingface/safetensors | 가중치 로드(pickle 거부) / 라이브러리로 불러 씀 |
| 6 | numpy | 2.4.6 | BSD-3-Clause | https://github.com/numpy/numpy | 텐서·배열 백엔드 / 라이브러리로 불러 씀 |
| 7 | Pillow | 12.3.0 | HPND-derived (MIT-CMU) | https://github.com/python-pillow/Pillow | 골든셋 JPEG 로드 / 라이브러리로 불러 씀 |
| 8 | torch | (CPU wheel, Dockerfile) | BSD-3-Clause | https://github.com/pytorch/pytorch | scratch 학습·추론(node-m-team) / 라이브러리로 불러 씀 |
| 9 | torchvision | (CPU wheel, Dockerfile) | BSD-3-Clause | https://github.com/pytorch/vision | 32×32 변환 / 라이브러리로 불러 씀 |
| 10 | PostgreSQL | 16 | PostgreSQL License | https://github.com/postgres/postgres | DB·제약 강제(compose 이미지) / 실행 환경 |

기계 가독 전체: 저장소 루트 `sbom.json` (`scripts/generate_sbom.ps1`). 사람용 표: `THIRD-PARTY-LICENSES.md`.

---

## 붙임2 AI 모델 활용 및 라이선스 기술 명세서

### 1. AI 모델 활용 유형

- □ 유형 1  
- □ 유형 2  
- **▣ 유형 3: 자체 개발 모델** (기반 모델 없이 처음부터 전체 학습)

### 2. 기반(베이스) 모델 정보

**해당 없음** (기반 모델을 사용하지 않고 TinyEuroSAT 가중치를 EuroSAT RGB로 자체 학습함)

### 3. 데이터셋 정보 및 가중치 배포 명세

**학습 데이터셋 정보 (출처 및 규모)**  
EuroSAT RGB 배포판 · Zenodo record 7711810 · DOI 10.5281/zenodo.7711810 · 라이선스 MIT · `EuroSAT_RGB.zip` 27,000장(10클래스) · 원본 64×64 JPEG. 원본 zip은 저장소 미동봉(`scripts/download_eurosat` + `archive_sha256` 핀). 게이트·제품 계약은 **32×32** resize.

**데이터 정제/가공 방법 요약**  
개인정보 없음(원격탐사 타일). 클래스 균등 스트라이드로 데모 골든 N=40 추출(모델 기반 샘플 선택 금지). 학습은 전체 27,000장 · seed 20260806 · 최대 40 epoch(CPU).

**새로 생성된 가중치 공개 저장소 URL**  
https://github.com/gncorpseo-commits/capnet/blob/main/apps/node/weights/eurosat_scratch.safetensors  

직접 다운로드(승인 절차 없음):  
https://raw.githubusercontent.com/gncorpseo-commits/capnet/main/apps/node/weights/eurosat_scratch.safetensors  

**가중치 파일 정보 및 배포방식**  
파일명: `eurosat_scratch.safetensors` / 전체 가중치(TinyEuroSAT) / 약 370KB / sha256 `0c5b16cef57d11e26c58319d80cd47a41a8b8d740ba3470c1d801e7fb9356b5b` / pretrained=false · 메타: `apps/node/weights/eurosat_scratch.meta.json`

### 4. 소스코드 라이선스 및 개발 환경 정보

| 칸 | 기재 |
|----|------|
| 직접 작성한 코드의 오픈소스 라이선스 | Apache License 2.0 |
| 학습/추론 소스코드 공개 저장소 URL | https://github.com/gncorpseo-commits/capnet (`apps/train/train_scratch.py`, `apps/node/app/infer.py`, `apps/node/app/score_gate.py`) |
| 상용 AI 보조도구 활용 여부 및 범위 | 코드 작성·디버깅·문서 정리 보조로 Cursor(Claude 등)를 사용함. 스키마 제약·게이트 사슬·채점 규칙은 팀이 설계·검증했으며, AI 생성 코드는 동작 원리를 팀이 이해·수정한 뒤 반영함. |

---

## 이식 체크리스트

- [ ] 안내 페이지 삭제  
- [ ] 위 문장을 양식 칸에 붙여넣기 · 5P 맞춤(도식은 [`gate-chain-slide.md`](./gate-chain-slide.md))
- [ ] 촬영: [`shoot-day-runbook.md`](./shoot-day-runbook.md) → YouTube URL 기입
- [ ] PDF 저장 · 포털 zip (원본 hwp/docx + PDF)  
- [ ] 시연 URL 교체  
- [ ] 붙임1·2 채움  
- [ ] PDF 변환 · 파일명 `_915(지엔)`  
- [ ] 포털 zip 제출 · 제출 완료·메일  
