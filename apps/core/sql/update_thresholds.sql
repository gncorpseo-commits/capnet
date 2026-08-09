-- 실측 보정 (스키마 변경 없음).
-- TinyEuroSAT scratch N=40 실측 acc≈0.70–0.725 → 가정 0.75/0.72는 위.
-- 통과율 20–80% 조준으로 0.68/0.65. sanity floor는 여전히 FAILED.
UPDATE capability
   SET golden_metrics = '{"primary_metric":"accuracy","min_accuracy":0.68,"min_macro_f1":0.65,"max_invalid_rate":0.02,"combine":"AND","guarantee":"floor_only","equivalence_observed":{"metric":"accuracy","comparison":"paired_same_cases","note":"observation only; not a pass condition (SD-009, plan v4.6)"},"scoring_version":1,"threshold_basis":{"agent":"TinyEuroSAT","n":40,"measured_accuracy_range":[0.70,0.725],"note":"assumed 0.75/0.72 was above scratch baseline; calibrated for 20-80% pass band"},"dataset":{"id":"eurosat-rgb","zenodo_record":"7711810","archive":"EuroSAT_RGB.zip","archive_sha256":"b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90","zip_root":"EuroSAT_RGB","native_hw":[64,64],"contract_resize_hw":[32,32]}}'::jsonb
 WHERE code = 'image.classify' AND version = 1;

SELECT golden_metrics->>'min_accuracy' AS min_acc,
       golden_metrics->>'min_macro_f1' AS min_f1
  FROM capability
 WHERE code = 'image.classify' AND version = 1;
