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
# arch 는 등록 필수다 (G5). sha 와 **같은 증언**에서 뽑는다 — Node 가 들고 있는 파일의 학습 기록.
$arch = $scratch[0].arch
if (-not $arch) { throw "node does not know arch for eurosat_scratch (<weights>.meta.json)" }
Write-Host "scratch sha256=$sha arch=$arch"

Write-Host "register scratch agent"
$ver = "0.1.0-scratch-" + (Get-Date -Format "yyyyMMddHHmmss")
$agent = Invoke-RestMethod -Method Post "$core/v1/agents" -ContentType "application/json" -Body (@{
    name = "eurosat-scratch"
    version = $ver
    manifest_hash = "eurosat-scratch-tiny"
    weights_uri = "file:///weights/eurosat_scratch.safetensors"
    weights_sha256 = $sha
    arch = $arch
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
# 배정 시점 스냅샷 — .sh 와 같은 줄을 찍는다. 촬영은 PowerShell 이고,
# 검증 3종은 .sh 만 만지므로 여기가 뒤처지면 촬영일에야 드러난다 (G5 회귀 전례).
Write-Host ("경계: 신뢰도메인 task={0} -> node={1} · 티어 capability={2} <= node_max={3}" -f `
    $got.assignment.task_trust_domain, $got.assignment.node_trust_domain, `
    $got.assignment.capability_tier, $got.assignment.node_tier_max)
