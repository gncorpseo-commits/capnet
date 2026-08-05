$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8000"

Write-Host "GET /health"
$h = Invoke-RestMethod "$base/health"
$h | ConvertTo-Json -Compress
if (-not $h.ok) { throw "health failed" }
if (-not $h.capability) { throw "image.classify@1 missing" }

Write-Host "POST /v1/tasks bad datasetId (expect 400)"
try {
    Invoke-RestMethod -Method Post "$base/v1/tasks" -ContentType "application/json" `
        -Body '{"datasetId":"not-allowed","caseId":"x"}'
    throw "allowlist should reject"
} catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 400) { throw }
}

Write-Host "POST /v1/internal/claim"
$c = Invoke-RestMethod -Method Post "$base/v1/internal/claim" -ContentType "application/json" -Body "{}"
$c | ConvertTo-Json -Compress
if ($c.status -ne "LEASED") { throw "claim status $($c.status)" }

Write-Host "W1 smoke OK"
