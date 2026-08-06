$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$zip = Join-Path $root "data\eurosat\EuroSAT_RGB.zip"
$out = Join-Path $root "data\golden-n300"
if (-not (Test-Path $zip)) {
    throw "EuroSAT zip missing. Run scripts/download_eurosat.ps1 first."
}
New-Item -ItemType Directory -Force -Path $out | Out-Null
docker run --rm `
    -v "${root}\data\eurosat:/data:ro" `
    -v "${out}:/out" `
    -v "${root}\scripts:/scripts:ro" `
    python:3.11-slim `
    python /scripts/extract_golden.py --n 300 --zip /data/EuroSAT_RGB.zip --out /out --cases-prefix ic1f
Write-Host "n=300 written under data/golden-n300 (gitignored). Score: score_gate --manifest ... --cases ..."
