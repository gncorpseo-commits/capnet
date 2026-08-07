# Agent A 기본 · B: .\train_scratch.ps1 -Arch TinyEuroSATB -OutName eurosat_scratch_b.safetensors
param(
    [string]$Arch = "TinyEuroSAT",
    [string]$OutName = "eurosat_scratch.safetensors",
    [string]$ExtraEpochs = "20"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$zip = Join-Path $root "data\eurosat\EuroSAT_RGB.zip"
if (-not (Test-Path $zip)) {
    throw "EuroSAT zip missing. Run scripts/download_eurosat.ps1 first."
}

Set-Location $root
docker run --rm `
    -v "${root}\data\eurosat:/data:ro" `
    -v "${root}\apps\node\weights:/out" `
    -v "${root}\apps\train:/train:ro" `
    -v "${root}\apps\node:/nodepkg:ro" `
    -e PYTHONPATH=/nodepkg `
    -e ARCH=$Arch `
    -e OUT_NAME=$OutName `
    -e EXTRA_EPOCHS=$ExtraEpochs `
    python:3.11-slim `
    bash -lc "pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu && pip install -q safetensors pillow && python /train/train_scratch.py"
