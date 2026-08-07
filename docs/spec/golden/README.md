# 골든셋 산출물

| 경로 | N | 용도 | 저장소 |
|------|---|------|--------|
| `manifest-image-classify-v1.json` + `cases/` | 40 | 대회 데모·실게이트 | **커밋** |
| `data/golden-n300/` (스크립트 생성) | 300 | 본편 통계·A/B 측정용 | **gitignore** |

생성:

```text
scripts/extract_golden_n300.ps1   # 또는 .sh
# → data/golden-n300/manifest-image-classify-n300.json + cases/
```

채점 (N=300 · 결과는 `artifacts/` · gitignore):

```text
scripts/score_n300.ps1
# Agent B 가중치가 있으면:
scripts/score_n300.ps1 -Weights eurosat_scratch_b.safetensors
```

A/B 골격 (Contest Must **아님** · SD-001 미결):

```text
# B 학습 (장시간): scripts/train_scratch.ps1 -Arch TinyEuroSATB -OutName eurosat_scratch_b.safetensors
scripts/compare_ab.ps1
# n<300 → verdict=INCONCLUSIVE_N_TOO_SMALL · Must 승격 전
```

n=300 추출·채점만으로 대체가능성(편차 0.05)이 **확정되지는 않는다**.  

**2026-08-08 실측:** A(80ep)≈0.880 · B(40ep)≈0.927 · abs_diff≈0.0467 → `WITHIN_THRESHOLD`.  
A/B를 Contest Must로 쓸 때 **epoch 불일치·SE≈임계**를 보고서에 같이 적는다 (SD-001).
