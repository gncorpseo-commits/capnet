# 골든셋 산출물

| 경로 | N | 용도 | 저장소 |
|------|---|------|--------|
| `manifest-image-classify-v1.json` + `cases/` | 40 | 대회 데모·실게이트 | **커밋** |
| `data/golden-n300/` (스크립트 생성) | 300 | 본편 통계 판정용 골격 | **gitignore** |

생성:

```text
scripts/extract_golden_n300.ps1   # 또는 .sh
# → data/golden-n300/manifest-image-classify-n300.json + cases/
```

채점 (compose node-m-team에 마운트하거나 로컬 torch 환경):

```text
python -m app.score_gate \
  --manifest /path/to/manifest-image-classify-n300.json \
  --cases /path/to/cases \
  --weights /weights/eurosat_scratch.safetensors
```

n=300 추출만으로 대체가능성(편차 0.05)이 **확정되지는 않는다**. A/B Must는 여전히 미결.
