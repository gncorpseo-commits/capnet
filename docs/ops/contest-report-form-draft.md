# 결과보고서·붙임 초안 문장 (공식 양식 이식용)

**용도:** `2026 오픈소스 개발자대회 결과보고서_접수번호(팀명).docx|hwp`에 **복사해 넣을 검정 문장**.  
**파일명 예:** `2026 오픈소스 개발자대회 결과보고서_915(지엔)`  
**갱신:** 2026-08-08 (공식 예시본 대조 반영)  
**준수 근거:** [`regulation-compliance.md`](./regulation-compliance.md)

## 공식 양식 구조 (예시본 실측)

원본은 **한글(HWP 2024)** 로 작성돼 있다. 총 5쪽이며 구성은 고정이다.

| 쪽 | 내용 | 방향 |
|----|------|------|
| 1–2 | **본문** — 아래 5개 칸으로 된 표 | 세로 |
| 3 | 붙임1 SBOM | **가로** |
| 4–5 | 붙임2 AI 모델 활용 및 라이선스 기술 명세서 | 세로 |

**본문은 2쪽 고정 표다.** 자유 서술 5쪽이 아니다 — 칸마다 들어갈 분량이 정해져 있으므로
아래 문장을 그대로 붙이지 말고 **칸 크기에 맞춰 줄인다.** 개조식 지시가 있는 칸은 개조식으로 쓴다.

양식의 칸 이름과 이 문서의 절이 1:1로 대응한다.

| 양식 칸 | 칸 안 소제목 | 이 문서 |
|---------|--------------|---------|
| (상단 표) | 팀명 · 팀 인원(팀장 포함) · 참가부문 · 과제유형 | 표지·개요 |
| 프로젝트 개요 | 프로젝트명 · 프로젝트 등록 URL · 시연 영상 · 프로젝트 소개 | 표지·개요 |
| 프로젝트 세부 내용 | 개발 배경 및 목적 · **개발 환경**(개조식) · **시스템 구성 및 아키텍처**(개조식) | 동명 절 |
| **프로젝트 주요 기능** | 프로젝트 상세 내용 · 구동 및 시연 | 두 절이 **한 칸**에 들어간다 |
| **기대효과 및 활용 분야** | 향후 확장성 및 기대효과 | 동명 절 |
| **기타** | 프로젝트의 혁신성 및 차별성 · 한계점 및 향후 발전 로드맵 · 소감 및 후기 | 세 절이 **한 칸**에 들어간다 |

**삭제할 것:** 회색 예시 문장 전부 · 빨간 안내 콜아웃 박스 전부 · 붙임2 해당 없을 때는 붙임2 영역 통째로
(우리는 유형3이므로 **유지**한다).

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

실측(과장 금지): scratch N=40 **acc 0.7000 · macro_f1 0.6982 · PASSED**(`dummy=false`). seed dummy PASSED ≠ 실게이트. **이 점수는 학습 데이터에 대한 재현 점수다** — 한계점 절 참조.

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

라우팅 불변식을 앱이 아니라 **PostgreSQL이 거절**한다. 위반 14종 실측·M25 6종 스크립트. 게이트는 team runner만. 서로 다른 scratch 백본 A/B를 n=300에서 `|Δacc|≤0.05`로 맞춰 Capability 대체를 실측했다(epoch·SE 한계는 한계 절).

---

## 한계점 및 향후 발전 로드맵

- **골든셋이 학습셋 안에 있다(홀드아웃 없음).** 데모 40/40 · 본편 300/300 케이스가 학습에 쓰인 이미지다
  (`scripts/check_golden_leakage.py`로 검증). 따라서 본 보고서의 게이트 점수는 **학습 데이터 재현 점수**이며
  일반화 성능이 아니다. 게이트 사슬·위반 거절·sanity floor는 모델 품질과 무관한 DB 불변식이므로 영향받지 않는다.
- 데모 N=40과 본편 n=300을 분리한다. n=300 paired `|Δacc| = 0.0467 ≤ 0.05`(Within).
  단 **train epoch A80≠B40** · **SE≈0.019로 임계와 가깝다** · 위 홀드아웃 한계가 함께 붙는다.
- **label_agreement 0.8933** — A·B는 300건 중 32건에서 다른 라벨을 낸다.
  "교체해도 계약 품질 수준이 유지된다"는 말할 수 있으나 "같은 답이 나온다"는 아니다.
- N=40은 SE≈0.072라, 임계를 0.02 차이로 통과한 후보의 합격/불합격은 통계적으로 견고하지 않다.
- WS·lease 만료 스캐너는 Should. 임계는 실측 보정 0.68/0.65(정직).

로드맵: **홀드아웃 도입 → 골든 재추출 → 후보 재학습 → 재측정**(Phase 1 판정 해소) → credential·테넌트.

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

- □ 유형 1: 외부 모델 그대로 활용  
- □ 유형 2: 외부 모델 파인튜닝  
- **▣ 유형 3: 자체 개발 모델** (기반 모델 없이 참가팀이 처음부터 가중치를 직접 전체 학습시킨 경우)

판정 근거 (부록2 Ⅲ 확인 질문 ①): 기반 모델 없이 EuroSAT RGB만으로 가중치를 처음부터 학습했다 → 유형 3.
부록2 Ⅱ의 세 관문도 함께 충족한다 — 관문1·2는 외부 기반 모델을 쓰지 않아 해당 없음이며 추론은
로컬 컨테이너(`node-m-team`)에서 torch로 직접 구동하므로 **외부 상용 API 의존이 없다**. 관문3은 Apache-2.0.

### 2. 기반(베이스) 모델 정보

**해당 없음** (기반 모델을 사용하지 않고 TinyEuroSAT 가중치를 EuroSAT RGB로 자체 학습함)

### 3. 데이터셋 정보 및 가중치 배포 명세

**학습 데이터셋 정보 (출처 및 규모)**  
EuroSAT RGB 배포판 · Zenodo record 7711810 · DOI 10.5281/zenodo.7711810 · 라이선스 MIT · `EuroSAT_RGB.zip` 27,000장(10클래스) · 원본 64×64 JPEG. 원본 zip은 저장소 미동봉(`scripts/download_eurosat` + `archive_sha256` 핀). 게이트·제품 계약은 **32×32** resize.

**데이터 정제/가공 방법 요약**  
개인정보 없음(원격탐사 타일). 클래스 균등 스트라이드로 데모 골든 N=40 추출(모델 기반 샘플 선택 금지). 학습은 전체 27,000장 · seed 20260806 · Agent A 80 epoch · Agent B 40 epoch(CPU, scratch).

**새로 생성된 가중치 공개 저장소 URL**  
https://github.com/gncorpseo-commits/capnet/blob/main/apps/node/weights/eurosat_scratch.safetensors  
https://github.com/gncorpseo-commits/capnet/blob/main/apps/node/weights/eurosat_scratch_b.safetensors  

직접 다운로드(승인 절차 없음):  
https://raw.githubusercontent.com/gncorpseo-commits/capnet/main/apps/node/weights/eurosat_scratch.safetensors  
https://raw.githubusercontent.com/gncorpseo-commits/capnet/main/apps/node/weights/eurosat_scratch_b.safetensors  

**가중치 파일 정보 및 배포방식**  
부록2 예시 형식(파일명 / 배포 형태 · 아키텍처 · 파라미터 수 / 용량)에 맞춰 기재한다.

- 파일명 `eurosat_scratch.safetensors` / **전체 가중치 배포** (TinyEuroSAT CNN, **94,538 파라미터**) / 용량 370KB  
  sha256 `74ca92224ff93f6cfab56265466d2c8ed11e0add4581c45a98169e92fb797b43` · 80 epoch · pretrained=false
- 파일명 `eurosat_scratch_b.safetensors` / **전체 가중치 배포** (TinyEuroSATB CNN, **24,685 파라미터**) / 용량 98KB  
  sha256 `3fbdde549459ba1e895ab8221ba1455b7840e1641b36b202c96420d410343b24` · 40 epoch · pretrained=false

LoRA 어댑터가 아니라 **전체 가중치**다 (유형 3 요건). 메타는 각 `*.meta.json`.
n=300 paired `|Δacc| = 0.0467 ≤ 0.05` — 단 학습셋 위 측정(한계점 절).

### 4. 소스코드 라이선스 및 개발 환경 정보

| 칸 | 기재 |
|----|------|
| 직접 작성한 코드의 오픈소스 라이선스 | Apache License 2.0 |
| 학습/추론 소스코드 공개 저장소 URL | https://github.com/gncorpseo-commits/capnet (`apps/train/train_scratch.py`, `apps/node/app/infer.py`, `apps/node/app/score_gate.py`) |
| 상용 AI 보조도구 활용 여부 및 범위 | 코드 작성·디버깅·문서 정리 보조로 Cursor 및 Claude Code를 활용함. **[TODO: 전체 비율 확정]** 참고 실측 — 저장소 코드 5,054줄(py/sh/ps1/sql/yaml) 중 2026-08-08 세션에서 추가된 검증 스크립트 3종이 390줄(약 8%). 스키마 제약·게이트 사슬·채점 규칙·판정 기준은 팀이 설계했고, AI 생성 코드는 팀이 동작 원리를 확인하고 실행 검증한 뒤 반영함. |

---

## 이식 체크리스트

- [ ] 회색 예시 문장·빨간 안내 콜아웃 **전부 삭제**
- [ ] 위 문장을 양식 칸에 붙여넣기 — **본문 2쪽 고정 표**에 맞춰 압축 (도식은 [`gate-chain-slide.md`](./gate-chain-slide.md))
- [ ] 개발 환경 · 시스템 구성 칸은 **개조식**으로
- [ ] 붙임1은 **가로 쪽** · 최대 10행 · LGPL 계열(psycopg)을 1번에 유지
- [ ] 붙임2 §4 상용 AI 보조도구 **비율 확정** (현재 TODO)
- [ ] 촬영: [`shoot-day-runbook.md`](./shoot-day-runbook.md) → YouTube URL 기입
- [ ] PDF 저장 · 포털 zip (원본 hwp/docx + PDF)  
- [ ] 시연 URL 교체  
- [ ] 붙임1·2 채움  
- [ ] PDF 변환 · 파일명 `_915(지엔)`  
- [ ] 포털 zip 제출 · 제출 완료·메일

## 부록2 Ⅶ 제출 전 최종 확인 (원문 9항목)

부록2가 "대부분의 반려 사유는 이 단계에서 미리 걸러진다"고 적은 목록이다. 그대로 옮긴다.

| 확인 | 점검 항목 | CapNet 현황 |
|------|-----------|-------------|
| [ ] | 사용한 모델의 가중치가 승인 절차 없이 누구나 내려받을 수 있는 상태인가 | raw URL HTTP 200 실측 (EA-003) |
| [ ] | 모델의 라이선스와 이용 약관을 직접 열어 제한 조항을 확인했는가 | 기반 모델 없음 (유형 3) — 해당 없음 |
| [ ] | 외부 상용 API 없이도 핵심 기능이 작동하는 독립 구동 경로를 갖추었는가 | 로컬 torch 추론만. 외부 AI API 호출 **0건** |
| [ ] | 직접 작성한 학습·추론 코드에 OSI 인증 라이선스 파일을 포함했는가 | Apache-2.0 `LICENSE` |
| [ ] | 유형 2·3인 경우, 새로 만든 가중치를 공개 저장소에 올리고 접근을 확인했는가 | main 브랜치 2종 공개 |
| [ ] | 사용한 오픈소스 라이브러리와 모델의 출처·라이선스를 모두 밝혔는가 | 붙임1 · `THIRD-PARTY-LICENSES.md` · `sbom.json` |
| [ ] | 붙임2의 모든 항목을 작성했고, 해당 없는 항목은 **"해당 없음"으로 표기**했는가 | 빈칸 금지 — 누락과 구분되지 않는다 |
| [ ] | 상용 AI 보조도구를 사용했다면 그 범위를 4번 항목에 기재했는가 | **비율 TODO** |
| [ ] | 소스코드 저장소가 공개(Public) 상태인가 | PUBLIC ✅ — **수상 시 수상일로부터 5년간 공개 유지 의무** |

마지막 항목의 **5년 공개 유지 의무**는 수상 시 발생한다. 저장소를 비공개로 돌리거나 삭제할 수 없다.  
