$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$core = "http://127.0.0.1:8000"
$node = "http://127.0.0.1:8001"
$capId = "00000000-0000-4000-8000-000000000010"
$runnerId = "00000000-0000-4000-8000-000000000030"

Write-Host "GET /health"
$h = Invoke-RestMethod "$core/health"
if (-not $h.ok) { throw "core health failed" }
$nh = Invoke-RestMethod "$node/health"
$scratch = @($nh.weights | Where-Object { $_.path -match "eurosat_scratch" -and -not $_.placeholder })
if ($scratch.Count -lt 1) {
    throw "scratch weights missing on node-m-team. train: scripts/train_scratch.ps1 then compose up --build"
}
$sha = $scratch[0].sha256
Write-Host "scratch sha256=$sha"

Write-Host "register scratch agent"
$ver = "0.1.0-scratch-" + (Get-Date -Format "yyyyMMddHHmmss")
$agent = Invoke-RestMethod -Method Post "$core/v1/agents" -ContentType "application/json" -Body (@{
    name = "eurosat-scratch"
    version = $ver
    manifest_hash = "eurosat-scratch-tiny"
    weights_uri = "file:///weights/eurosat_scratch.safetensors"
    weights_sha256 = $sha
} | ConvertTo-Json)

Write-Host "score golden set on gate-runner container (not dummy)"
$raw = docker compose --project-directory $root exec -T node-m-team `
    python -m app.score_gate --mode scratch --weights /weights/eurosat_scratch.safetensors `
    --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02
if ($LASTEXITCODE -notin 0, 2) { throw "score_gate failed rc=$LASTEXITCODE" }
$score = $raw | ConvertFrom-Json
Write-Host ("score status={0} acc={1:N4} f1={2:N4} inv={3:N4}" -f `
    $score.status, $score.golden_score, $score.macro_f1, $score.invalid_rate)

Write-Host "start + finish real gate dummy=false"
$gr = Invoke-RestMethod -Method Post "$core/v1/internal/gate-runs" -ContentType "application/json" -Body (@{
    agent_id = $agent.id
    capability_id = $capId
    runner_node_id = $runnerId
} | ConvertTo-Json)

$finishBody = @{
    status = $score.status
    dummy = $false
    golden_score = $score.golden_score
    cases_total = $score.cases_total
    cases_passed = $score.cases_passed
    macro_f1 = $score.macro_f1
    invalid_rate = $score.invalid_rate
    golden_set_sha256 = $gr.golden_set_sha256
    note = "golden-set-v1 scratch TinyEuroSAT"
} | ConvertTo-Json
try {
    $fin = Invoke-RestMethod -Method Post "$core/v1/internal/gate-runs/$($gr.id)/finish" `
        -ContentType "application/json" -Body $finishBody
} catch {
    throw "real gate finish rejected: $($_.Exception.Message)"
}
$summary = $fin.result_summary
if ($summary -is [string]) { $summary = $summary | ConvertFrom-Json }
if ($summary.dummy) { throw "finish marked dummy — not a real gate" }
if ($score.status -ne "PASSED") {
    Write-Host "REAL GATE FAILED (honest). Task not started. dummy plumbing PASSED와 혼동 금지."
    exit 2
}
if (-not $fin.chain_minted) { throw "PASSED chain not minted" }

Write-Host "bind READY + task + claim + scratch execute"
$bind = Invoke-RestMethod -Method Post "$core/v1/agents/$($agent.id)/bindings" -ContentType "application/json" -Body (@{
    node_id = $runnerId
    weights_sha256_seen = $sha
} | ConvertTo-Json)
if (-not $bind.ready) { throw "bind not READY" }

$t = Invoke-RestMethod -Method Post "$core/v1/tasks" -ContentType "application/json" -Body (@{
    datasetId = "eurosat-rgb"
    caseId = "ic1-0001"
    requestedAgentId = $agent.id
} | ConvertTo-Json)
$c = Invoke-RestMethod -Method Post "$core/v1/internal/claim" -ContentType "application/json" -Body (@{
    task_id = $t.id
} | ConvertTo-Json)
$e = Invoke-RestMethod -Method Post "$node/v1/execute" -ContentType "application/json" -Body (@{
    id = $c.id
    weights_sha256 = $c.weights_sha256
    input_ref = $c.input_ref
} | ConvertTo-Json)
if ($e.dummy) { throw "execute was dummy — scratch path not used" }
$got = Invoke-RestMethod "$core/v1/tasks/$($t.id)"
if ($got.status -ne "COMPLETED") { throw "task $($got.status)" }
Write-Host "demo OK - real gate PASSED + scratch task COMPLETED"
Write-Host ("label={0} assignment={1}" -f $e.label, $got.assignment.status)
