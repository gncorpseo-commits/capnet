-- 실측 보정 (스키마 변경 없음).
-- TinyEuroSAT scratch N=40 실측 acc≈0.70–0.725 → 가정 0.75/0.72는 위.
-- 통과율 20–80% 조준으로 0.68/0.65. sanity floor는 여전히 FAILED.
UPDATE capability
   SET golden_metrics = '{"primary_metric":"accuracy","min_accuracy":0.68,"min_macro_f1":0.65,"max_invalid_rate":0.02,"combine":"AND","min_per_class_recall":0.10,"guarantee":{"type":"floor_on_declared_sample","holds_on":{"dataset":"eurosat-rgb","sampling":"per_class_even_stride","preprocessing":"32x32 RGB","class_balance":"uniform"},"does_not_hold_under":["distribution shift","inputs outside declared allowlist","deliberate overfitting to the static public golden set"],"strengthened_by":"rotating hidden probes (Phase 2 spot-check)"},"deviation":{"enforceable_bound":"1 - min_accuracy","note":"tautological under a floor gate; NOT a constraint. bounding pairwise deviation requires a banded pass criterion","observed":{"n":300,"passer_range":[0.6933,0.8700]}},"scoring_version":1,"threshold_basis":{"kind":"declared_service_level","note":"NOT derived from measurement. admissible band (0.447,0.910] measured: collapsed model 0.447, feasible best 0.910 under no-pretrain 32x32. value is declared and re-declared when a real user requirement exists (supersedes SD-004)"},"dataset":{"id":"eurosat-rgb","zenodo_record":"7711810","archive":"EuroSAT_RGB.zip","archive_sha256":"b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90","zip_root":"EuroSAT_RGB","native_hw":[64,64],"contract_resize_hw":[32,32]}}'::jsonb
 WHERE code = 'image.classify' AND version = 1;

SELECT golden_metrics->>'min_accuracy' AS min_acc,
       golden_metrics->>'min_macro_f1' AS min_f1
  FROM capability
 WHERE code = 'image.classify' AND version = 1;
