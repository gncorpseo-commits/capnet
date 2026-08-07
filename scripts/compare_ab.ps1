# paired A/B 비교 골격. N<300 → INCONCLUSIVE. Contest Must 아님.
param(
    [string]$ScoreA = "artifacts/score-n300-eurosat_scratch.json",
    [string]$ScoreB = "artifacts/score-n300-eurosat_scratch_b.json",
    [double]$MaxDeviation = 0.05,
    [int]$MinN = 300
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$a = Join-Path $root $ScoreA
$b = Join-Path $root $ScoreB
if (-not (Test-Path $a)) { throw "missing $a — run score_n300.ps1 first" }
if (-not (Test-Path $b)) { throw "missing $b — train B + score_n300 -Weights eurosat_scratch_b.safetensors" }

Set-Location $root
python "$root\scripts\compare_ab.py" `
    --score-a $a --score-b $b `
    --max-deviation $MaxDeviation --min-n $MinN
$rc = $LASTEXITCODE
if ($rc -eq 3) {
    Write-Host "EXCEEDS_THRESHOLD (exit 3). Still not Contest Must."
}
exit $rc
