# 입력은 allowlist된 datasetId만. 자유 업로드 경로를 만들지 않는다.
ALLOWED_DATASET_IDS = frozenset({"eurosat-rgb"})


def assert_dataset_id(dataset_id: str) -> None:
    if dataset_id not in ALLOWED_DATASET_IDS:
        raise ValueError(f"datasetId not allowlisted: {dataset_id}")
