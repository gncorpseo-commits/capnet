# n=300 골든셋 채점. A/B Must 아님. 결과는 artifacts/ 에 JSON 저장.
param(
    [string]$Weights = "eurosat_scratch.safetensors",
    [string]$OutName = ""
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$golden = Join-Path $root "data\golden-n300"
$manifest = Join-Path $golden "manifest-image-classify-n300.json"
$cases = Join-Path $golden "cases"
$weightsHost = Join-Path $root "apps\node\weights\$Weights"

if (-not (Test-Path $manifest)) {
    throw "n=300 missing. Run scripts/extract_golden_n300.ps1 first."
}
if (-not (Test-Path $weightsHost)) {
    throw "weights missing: $weightsHost"
}

$stem = [IO.Path]::GetFileNameWithoutExtension($Weights)
if (-not $OutName) { $OutName = "score-n300-$stem.json" }
$art = Join-Path $root "artifacts"
New-Item -ItemType Directory -Force -Path $art | Out-Null
$outPath = Join-Path $art $OutName

Set-Location $root
# compose 기본 마운트는 N=40뿐 → 일회성 컨테이너에 n300·weights·앱 코드 마운트
$raw = docker compose --project-directory $root run --rm --no-deps `
    -v "${golden}:/golden-n300:ro" `
    -v "${root}\apps\node\weights:/weights:ro" `
    -v "${root}\apps\node\app:/app/app:ro" `
    node-m-team `
    python -m app.score_gate `
        --mode scratch `
        --weights "/weights/$Weights" `
        --manifest /golden-n300/manifest-image-classify-n300.json `
        --cases /golden-n300/cases `
        --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02

if ($LASTEXITCODE -notin 0, 2) { throw "score_gate n300 rc=$LASTEXITCODE" }
[System.IO.File]::WriteAllText($outPath, ($raw -join "`n") + "`n")
$score = $raw | ConvertFrom-Json
Write-Host ("n300 status={0} acc={1:N4} f1={2:N4} n={3} → {4}" -f `
    $score.status, $score.golden_score, $score.macro_f1, $score.cases_total, $outPath)
Write-Host "A/B Must remains open. Compare: scripts/compare_ab.ps1"
