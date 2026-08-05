$ErrorActionPreference = "Stop"
$core = "http://127.0.0.1:8000"
$node = "http://127.0.0.1:8001"

Write-Host "GET /health (core)"
$h = Invoke-RestMethod "$core/health"
$h | ConvertTo-Json -Compress
if (-not $h.ok) { throw "health failed" }
if (-not $h.capability) { throw "image.classify@1 missing" }

Write-Host "GET /health (node)"
$nh = Invoke-RestMethod "$node/health"
$nh | ConvertTo-Json -Compress
if (-not $nh.ok) { throw "node placeholder weights missing" }

Write-Host "POST /v1/tasks bad datasetId (expect 400)"
try {
    Invoke-RestMethod -Method Post "$core/v1/tasks" -ContentType "application/json" `
        -Body '{"datasetId":"not-allowed","caseId":"x"}'
    throw "allowlist should reject"
} catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 400) { throw }
}

Write-Host "POST /v1/tasks"
$t = Invoke-RestMethod -Method Post "$core/v1/tasks" -ContentType "application/json" `
    -Body '{"datasetId":"eurosat-rgb","caseId":"ic1-dummy-e2e"}'
$t | ConvertTo-Json -Compress
$taskId = $t.id

Write-Host "POST /v1/internal/claim"
$claimBody = (@{ task_id = $taskId } | ConvertTo-Json)
$c = Invoke-RestMethod -Method Post "$core/v1/internal/claim" -ContentType "application/json" -Body $claimBody
$c | ConvertTo-Json -Compress
if ($c.status -ne "LEASED") { throw "claim status $($c.status)" }
if (-not $c.weights_sha256) { throw "claim missing weights_sha256" }
if ($nh.weights_sha256 -ne $c.weights_sha256) {
    throw "DB agent hash != placeholder file. docker compose down -v 후 다시 up (옛 seed 볼륨)"
}

Write-Host "POST node /v1/execute (dummy, not scratch train)"
$execBody = (@{
    id = $c.id
    weights_sha256 = $c.weights_sha256
    input_ref = $c.input_ref
} | ConvertTo-Json)
$e = Invoke-RestMethod -Method Post "$node/v1/execute" -ContentType "application/json" -Body $execBody
$e | ConvertTo-Json -Compress -Depth 6
if (-not $e.dummy) { throw "expected dummy=true" }
if ($e.core.task_status -ne "COMPLETED") { throw "task_status $($e.core.task_status)" }
if ($e.core.status -ne "SUCCEEDED") { throw "assignment $($e.core.status)" }

Write-Host "GET /v1/tasks/$taskId"
$got = Invoke-RestMethod "$core/v1/tasks/$taskId"
$got | ConvertTo-Json -Compress -Depth 5
if ($got.status -ne "COMPLETED") { throw "task $($got.status)" }
if ($got.assignment.status -ne "SUCCEEDED") { throw "assignment $($got.assignment.status)" }
if (-not $got.result_ref) { throw "missing result_ref (min certificate)" }

Write-Host "W1 smoke OK (claim + dummy e2e)"
