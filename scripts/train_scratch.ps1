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
# 최종 G2: 학습 컨테이너의 핀은 런타임과 같은 정본에서 읽는다 (.sh 와 같다)
$dockerfile = Get-Content (Join-Path $root "apps\node\Dockerfile")
$torchVer = ($dockerfile | Select-String "^ARG TORCH_VERSION=(.+)$").Matches.Groups[1].Value
$tvVer    = ($dockerfile | Select-String "^ARG TORCHVISION_VERSION=(.+)$").Matches.Groups[1].Value
$reqs = Get-Content (Join-Path $root "apps\node\requirements.txt")
$sfVer = ($reqs | Select-String "^safetensors==(.+)$").Matches.Groups[1].Value
$plVer = ($reqs | Select-String "^pillow==(.+)$").Matches.Groups[1].Value
if (-not $torchVer -or -not $tvVer -or -not $sfVer -or -not $plVer) { throw "런타임 핀을 못 읽었다 (Dockerfile ARG / requirements.txt)" }
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
    bash -lc "pip install -q \"torch==$torchVer\" \"torchvision==$tvVer\" --index-url https://download.pytorch.org/whl/cpu && pip install -q \"safetensors==$sfVer\" \"pillow==$plVer\" && python /train/train_scratch.py"
