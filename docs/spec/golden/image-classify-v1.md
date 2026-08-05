# CapNet 골든셋 정의서 — `image.classify@1`

**문서 버전:** v0.3 · 2026-08-06  
**파일:** `docs/spec/golden/image-classify-v1.md` (영문 파일명 · zip/리눅스 제출 대비)  
**정본:** 이 파일 + 아카이브 핀 [`eurosat-rgb.json`](./eurosat-rgb.json). (구 v0.1 한글·중복 파일 폐기)

대상 계약: `image.classify@1` (`output_kind = closed_set_labels`, `compute_tier = M`)  
근거: [capnet-plan.md](../../design/capnet-plan.md) v4.5 §4.3 · [schema.sql](../schema.sql) v4.4 · [Contest_MVP_2026.md](../../ops/Contest_MVP_2026.md)  
작성일: 2026-07-31 · 패치: 2026-08-06 (EuroSAT RGB `archive_sha256` 실측)

> **대회 데모:** N=30–50 ([Contest §9](../../ops/Contest_MVP_2026.md)).  
> **본편 통계 판정:** 본 문서 §5의 n=300/500. 숫자를 섞지 말 것.

---

## 0. 이 문서가 정하는 것

`capability` 테이블의 네 칸을 채웁니다.

```sql
golden_set_ref      TEXT   -- 케이스 묶음의 위치
golden_set_sha256   TEXT   -- 무결성
golden_set_size     INT    -- 케이스 수
golden_metrics      JSONB  -- 통과 임계값
```

---

## 1. 골든셋의 두 용도

| 용도 | 질문 | 필요한 성질 |
|------|------|-------------|
| **게이트** | 이 Agent를 라우팅해도 되는가 | 못 만든 Agent를 걸러낼 만큼 **어려울 것** |
| **대체가능성 측정** | Agent A와 B가 서로 바꿔도 되는가 | 두 Agent의 차이가 **드러날 만큼 민감할 것** |

기획서 §4.3 **게이트 통과율 20–80%** KPI가 난이도를 감시한다.  
**통과율 분모:** 동일 계약·동일 골든셋으로 게이트를 시도한 **후보 Agent 집합**(데모에서는 sanity 실패분 + 실 Agent). 단일 성공 1건을 100%로 읽지 말 것.

---

## 2. 계약 확정

### 2.1 라벨 집합 (closed set)

10개 클래스, 소문자 스네이크, 순서 고정.

```json
["annual_crop","forest","herbaceous_vegetation","highway","industrial",
 "pasture","permanent_crop","residential","river","sea_lake"]
```

EuroSAT 폴더명 → 계약 라벨 매핑:

| EuroSAT (원본) | CapNet label |
|----------------|--------------|
| AnnualCrop | annual_crop |
| Forest | forest |
| HerbaceousVegetation | herbaceous_vegetation |
| Highway | highway |
| Industrial | industrial |
| Pasture | pasture |
| PermanentCrop | permanent_crop |
| Residential | residential |
| River | river |
| SeaLake | sea_lake |

### 2.2 입출력 스키마

```jsonc
// input_schema
{ "type":"object", "required":["datasetId","caseId"],
  "properties": { "datasetId":{"type":"string"}, "caseId":{"type":"string"} } }

// output_schema
{ "type":"object", "required":["label"],
  "properties": {
    "label":      {"type":"string","enum":[/* §2.1 10개 */]},
    "confidence": {"type":"number","minimum":0,"maximum":1}
  },
  "additionalProperties": false }
```

`confidence`는 **채점에 쓰지 않는다.**

### 2.3 전처리 = 제품 계약 (게이트와 동일)

Gate · Product · Proof **모두** 동일 전처리:

- 입력: EuroSAT **RGB** 배포판 (원본 **64×64** JPEG)  
- `resize` → **32×32** (계약 열화. 원본 64를 그대로 돌리면 계약 위반)  
- 게이트만 열화하고 제품은 원본으로 돌리는 것 **금지**

---

## 3. 데이터셋 — EuroSAT RGB

| 항목 | 값 |
|------|-----|
| 출처 | EuroSAT RGB (Sentinel-2 토지 이용 분류) |
| 파일 | `EuroSAT_RGB.zip` (MS zip 아님) |
| Zenodo | record **`7711810`** · DOI `10.5281/zenodo.7711810` |
| `archive_sha256` | `b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90` |
| `archive_md5` | `f46e308c4d50d4bf32fedad2d3d62f3b` (Zenodo 표기와 일치) |
| 바이트 | 94,658,721 |
| zip 루트 | `EuroSAT_RGB/` |
| 클래스 디렉터리 | `AnnualCrop` `Forest` `HerbaceousVegetation` `Highway` `Industrial` `Pasture` `PermanentCrop` `Residential` `River` `SeaLake` |
| 장수 | 27,000 (클래스별 3000/3000/3000/2500/2500/2000/2500/3000/2500/3000) |
| 원본 픽셀 | **64×64** RGB JPEG (10클래스×3장 + 무작위 20장 = 50장 실측, 전부 일치. 전수 스캔은 아직 안 함) |
| 계약 입력 | resize **32×32** RGB |
| 라이선스 | **MIT** (원 저장소). Sentinel 원천은 Copernicus 공개 데이터 |
| 로컬 경로 | `data/eurosat/` (**gitignore**, 원본 미동봉) |
| 받기 | `scripts/download_eurosat.ps1` / `scripts/download_eurosat.sh` |

기계 핀: [`eurosat-rgb.json`](./eurosat-rgb.json).  
**아직 아닌 것:** 데모 N=40 케이스 manifest · `golden_set_sha256` · scratch 학습.

기획서 **§5.2** 데이터 정책(개인정보 미포함, allowlist만)을 데이터 성질로 만족한다.

Imagenette 등 ImageNet 하위셋은 **비상업 연구 조건 승계** 위험이 있어 게이트 기준으로 쓰지 않는다.

> Copernicus Sentinel 이용약관을 사용 전 확인하고, 보고서·NOTICE에 한 줄 인용한다.

---

## 4. 난이도 조준

EuroSAT 원본은 강한 모델이 **98%+** 를 낸다 → 통과율·편차 판정이 공허해진다.

| 방법 | 방식 | 판정 |
|------|------|------|
| **A. 입력 열화** | 32×32 RGB (계약 §2.3) | **권장·채택** |
| B. 혼동 클래스 가중 | 참조 모델로 “어려운” 샘플 고르기 | **금지** — 백본 편향이 A/B(S2)를 오염 |
| C. 학습 예산 제한 | Agent 쪽 규약 | 계약 밖. 비권장 |
| D. 임계만 상향 | min_accuracy≈0.96 | 비권장 |

**권장: A만.** 클래스 **균등** 샘플링. 모델 기반 샘플 선택 금지.

본편 임계·난이도 미세조정은 베이스라인 실측 후(주 3–4). 대회 데모는 A + N=30–50로 충분하다.

---

## 5. 케이스 수 (본편 vs 대회)

정확도 SE (이항): `SE = √(p(1-p)/n)`.

| n | p=0.70 | p=0.85 | p=0.95 |
|---|--------|--------|--------|
| 50 | 0.0648 | 0.0505 | 0.0308 |
| **300** | 0.0265 | **0.0206** | 0.0126 |
| 500 | 0.0205 | 0.0160 | 0.0097 |

편차 0.05 판정에는 SE≲0.025가 필요하다 → **본편 `golden_set_size = 300` 최소, 500 권장.**  
클래스 균등(각 30 또는 50장). paired 동일 케이스로 A/B 비교.

> **대회 데모는 N=30–50** ([Contest M7](../../ops/Contest_MVP_2026.md)).  
> 그 N으로는 대체가능성 **통계 판정 불가** — 보고서에 명시. 본 절 300/500은 본편용.

---

## 6. 채점 함수

결정적. 부분 점수 없음. 스키마 위반 = 오답. 퍼지·유사도 매칭 금지.  
정규화: `strip` + `lower`만. 타임아웃·무응답 = 오답 (`invalid`로 관측).

---

## 7. `golden_metrics`

```json
{
  "primary_metric": "accuracy",
  "min_accuracy": 0.75,
  "min_macro_f1": 0.72,
  "max_invalid_rate": 0.02,
  "combine": "AND",
  "equivalence": {
    "metric": "accuracy",
    "max_deviation": 0.05,
    "comparison": "paired_same_cases"
  },
  "scoring_version": 1
}
```

게이트 통과는 `min_accuracy` **AND** `min_macro_f1` **AND** `max_invalid_rate` 모두 충족.  
`min_*` 숫자는 가정 — 본편 주 3–4에 실측으로 확정.  
`scoring_version` 변경 시 해당 계약 Agent 전원 재게이트.

---

## 8. 무결성·매니페스트

`golden_set_sha256` = **manifest.json 하나**의 해시.

```jsonc
{
  "capability": "image.classify@1",
  "dataset": "eurosat-rgb",
  "zenodo_record": "7711810",
  "archive_sha256": "b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90",
  "preprocessing": { "resize": [32, 32], "bands": "RGB" },
  "scoring_version": 1,
  "labels": [/* §2.1 */],
  "cases": [
    { "caseId": "ic1-0001", "sha256": "<img>", "expected": "forest" }
  ]
}
```

전처리는 §2.3 계약과 동일해야 한다. 케이스 변경 = 계약 버전 bump + 재게이트.

---

## 9. Sanity floor

| 더미 | 기대 | 통과하면 |
|------|------|----------|
| 상수(`forest`) | ≈0.10 | 임계 재설정 |
| 난수 | ≈0.10 | 위와 동일 |
| 스키마 위반 | 0.00 | 채점기 버그 |

세 종 모두 FAILED여야 한다 (Contest M21).

---

## 10. 게이트 실행 (기획서 §7.1 · 위협 모델)

골든셋 N건을 Task로 만들어 `is_gate_runner=true` team Node에 할당.  
별도 실행 경로 없음. Kill 판정 표는 기획서 **§7.2**(본편) — 게이트 절차와 혼동하지 말 것.

```text
gate → gate_run → 채점 → PASSED면 gate_run_passed → agent_capability PASSED
```

데모 N건 / 본편 300건. v4.4가 사슬을 강제한다.

---

## 11. 일정

| 시점 | 산출 |
|------|------|
| Contest W0–W1 | 본 문서 v0.3, Zenodo·`archive_sha256` 고정. **데모 N 추출·sanity는 미완** |
| 본편 주 3–4 | n=300 세트·임계 확정, 통과율 20–80% |
| 본편 주 8–9 | A/B 편차 판정 |

---

## 12. 확정 사항 (Contest와 정합)

1. **데이터셋:** EuroSAT RGB · Zenodo `7711810`  
2. **본편 n:** 300 최소 / 데모 n: 30–50  
3. **난이도:** **A만** (모델 기반 샘플 선택 금지)  
4. **베이스라인 A/B:** 서로 다른 **소형 백본**, 둘 다 **EuroSAT scratch 학습** (사전학습·ImageNet 가중치 금지). Contest S2·§9와 동일  

---

### 참고

- EuroSAT: https://github.com/phelber/EuroSAT · Zenodo `7711810`  
- 논문: https://arxiv.org/pdf/1709.00029  
- Contest MVP: [../../ops/Contest_MVP_2026.md](../../ops/Contest_MVP_2026.md)

## 문서 이력

| 버전 | 내용 |
|------|------|
| v0.1 | 초안 (Downloads) |
| v0.2 | Contest 정합: A만, scratch, 데모 N, Zenodo/RGB, 전처리 계약, AND, 라벨 매핑, §7.1, 단일 정본·영문 파일명 |
| v0.3 | `EuroSAT_RGB.zip` 실측 핀: sha256·64×64·Pascal 폴더명. 케이스 manifest 없음 |
