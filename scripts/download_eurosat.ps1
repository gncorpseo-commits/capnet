$ErrorActionPreference = "Stop"
$expected = "b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90"
$url = "https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1"
$destDir = Join-Path $PSScriptRoot "..\data\eurosat"
$dest = Join-Path $destDir "EuroSAT_RGB.zip"

New-Item -ItemType Directory -Force -Path $destDir | Out-Null

if (-not (Test-Path $dest)) {
    Write-Host "GET $url"
    curl.exe -L --retry 3 -o $dest $url
}

$actual = (Get-FileHash -Algorithm SHA256 $dest).Hash.ToLower()
Write-Host "sha256 $actual"
if ($actual -ne $expected) {
    throw "archive_sha256 mismatch. expected $expected"
}
Write-Host "EuroSAT RGB pin OK -> $dest"
