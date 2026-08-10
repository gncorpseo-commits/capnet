# 골든셋 산출물

| 경로 | N | 용도 | 저장소 |
|------|---|------|--------|
| `manifest-image-classify-v1.json` + `cases/` | 40 | 대회 데모·실게이트 | **커밋** · **holdout** |
| `data/golden-n300-holdout/` (스크립트 생성) | 300 | 본편 통계·A/B (홀드아웃) | **gitignore** |
| `data/golden-n300/` (구·또는 train split) | 300 | 비교·재현용 | **gitignore** |

생성:

```text
# 데모 N=40 (홀드아웃 · 커밋 대상)
python scripts/extract_golden.py --n 40 --zip data/eurosat/EuroSAT_RGB.zip \
  --out /tmp/golden-demo --cases-prefix ic1 --split holdout
# → cases/ + manifest를 docs/spec/golden/ 로 옮기고 파일명을 manifest-image-classify-v1.json

# 본편 N=300
scripts/extract_golden_n300.ps1   # 또는 .sh · extract 기본 split=holdout
# → data/golden-n300/manifest-image-classify-n300.json + cases/
```

누출 검사:

```text
python scripts/check_golden_leakage.py
# 데모·홀드아웃 매니페스트는 clean 이어야 한다 (학습셋 = HOLDOUT=1 가정)
```

채점 (N=300 · 결과는 `artifacts/` · gitignore):

```text
scripts/score_n300.ps1
# GOLDEN=data/golden-n300-holdout 권장
# Agent B: scripts/score_n300.ps1 -Weights eurosat_scratch_b.safetensors
```

A/B (Contest Must **아님**):

```text
scripts/compare_ab.ps1
```

**주의:** 커밋된 `eurosat_scratch.safetensors` 메타는 `train_images=27000`(전수).  
홀드아웃 골든이 clean이어도, 그 가중치는 홀드아웃 이미지를 학습에 썼을 수 있다.  
일반화 주장은 `HOLDOUT=1` 재학습 가중치 + 홀드아웃 골든 조합에서만 한다.

**홀드아웃 n300 실측 (2026-08-09):** A/B 최선 쌍 abs_diff≈0.097 → EXCEEDS.  
구 누출 골든 Within(≈0.047)는 무효.
