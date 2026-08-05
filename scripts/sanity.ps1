$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Write-Host "sanity floor: constant / random / invalid must FAILED"
foreach ($mode in @("constant", "random", "invalid")) {
    $raw = docker compose --project-directory $root exec -T node-m-team `
        python -m app.score_gate --mode $mode --weights /weights/eurosat_scratch.safetensors `
        --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02
    if ($LASTEXITCODE -notin 0, 2) { throw "score_gate $mode rc=$LASTEXITCODE" }
    $score = $raw | ConvertFrom-Json
    Write-Host ("  {0}: status={1} acc={2:N4} f1={3:N4} inv={4:N4}" -f `
        $mode, $score.status, $score.golden_score, $score.macro_f1, $score.invalid_rate)
    if ($score.status -ne "FAILED") {
        throw "sanity $mode must FAILED (got $($score.status))"
    }
}
Write-Host "sanity OK (floors FAILED). A/B Must remains open / not implemented."
