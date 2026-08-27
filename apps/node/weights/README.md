# Node 가중치

- `placeholder.safetensors` — dummy E2E 배관용. 분류 품질이 아니다.
- `eurosat_scratch.safetensors` — EuroSAT RGB **scratch** TinyEuroSAT. 사전학습 가중치 없음. 게이트 실측용.
- `rule_ner.safetensors` — `text.ner` 자리표시자. **파라미터 0** (규칙 정규식이 추론한다).

`.pt` / `.pth` / pickle 로드 경로는 없다.
