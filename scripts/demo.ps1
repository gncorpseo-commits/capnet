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

# demo.sh 와 동일 — 계약이 min_per_class_recall 을 선언하면 finish 에 필수 (없으면 400).
$finishBody = @{
    status = $score.status
    dummy = $false
    golden_score = $score.golden_score
    cases_total = $score.cases_total
    cases_passed = $score.cases_passed
    macro_f1 = $score.macro_f1
    invalid_rate = $score.invalid_rate
    min_per_class_recall = $score.min_per_class_recall
    golden_set_sha256 = $gr.golden_set_sha256
    note = "golden-set-v1 scratch TinyEuroSAT"
} | ConvertTo-Json
try {
    $fin = Invoke-RestMethod -Method Post "$core/v1/internal/gate-runs/$($gr.id)/finish" `
        -ContentType "application/json" -Body $finishBody
} catch {
    $detail = $_.ErrorDetails.Message
    if (-not $detail) { $detail = $_.Exception.Message }
    throw "real gate finish rejected: $detail"
}
$summary = $fin.result_summary
if ($summary -is [string]) { $summary = $summary | ConvertFrom-Json }
if ($summary.dummy) { throw "finish marked dummy — not a real gate" }
if ($score.status -ne "PASSED") {
    Write-Host "REAL GATE FAILED (honest). Task not started. dummy plumbing PASSED와 혼동 금지."
    exit 2
}
if (-not $fin.chain_minted) { throw "PASSED chain not minted" }

Write-Host "bind READY + task (Core 중개 — Node 주소로 실행하지 않는다)"
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

# Core 워커가 배정하고, Node 가 자기 lease 를 가져와 실행한다. demo.sh 와 같은 사이클.
$got = $null
for ($i = 0; $i -lt 60; $i++) {
    $got = Invoke-RestMethod "$core/v1/tasks/$($t.id)"
    if ($got.status -eq "COMPLETED" -or $got.status -eq "FAILED") { break }
    Start-Sleep -Seconds 1
}
if ($null -eq $got) { throw "task poll returned nothing" }
if ($got.status -ne "COMPLETED") { throw "task not completed: $($got.status)" }

$res = $got.result_ref
if ($res -is [string]) { $res = $res | ConvertFrom-Json }
if ($res.dummy) { throw "execute was dummy — scratch path not used" }
if (-not $got.assignment) { throw "assignment missing on completed task" }

Write-Host "demo OK - real gate PASSED + scratch task COMPLETED (Core 중개)"
Write-Host ("label={0}" -f $res.label)
Write-Host ("증적: assignment={0} node={1} agent={2} status={3}" -f `
    $got.assignment.id, $got.assignment.node_id, $got.assignment.agent_id, $got.assignment.status)
Write-Host ("경계: 신뢰도메인 task={0} -> node={1} · 티어 capability={2} <= node_max={3}" -f `
    $got.assignment.task_trust_domain, $got.assignment.node_trust_domain, `
    $got.assignment.capability_tier, $got.assignment.node_tier_max)
