$ErrorActionPreference = "Stop"
# 주소를 환경에서 받는다 — `clean_room.sh`·`prod_room.sh` 가 격리 포트로 같은
# 스크립트를 돌린다. 박아 두면 격리 방을 띄워 놓고도 **운영 스택**을 친다.
# `.sh` 짝과 `proof_ab.ps1` 은 이미 이렇게 받는다.
$core = if ($env:CORE_URL) { $env:CORE_URL } else { "http://127.0.0.1:8000" }
$node = if ($env:NODE_URL) { $env:NODE_URL } else { "http://127.0.0.1:8001" }
$capId = "00000000-0000-4000-8000-000000000010"
$runnerId = "00000000-0000-4000-8000-000000000030"

function Get-StatusCode {
    param($Err)
    return [int]$Err.Exception.Response.StatusCode.value__
}

Write-Host "GET /health (core)"
$h = Invoke-RestMethod "$core/health"
$h | ConvertTo-Json -Compress
if (-not $h.ok) { throw "health failed" }
if (-not $h.capability) { throw "image.classify@1 missing" }

Write-Host "GET /health (node)"
$nh = Invoke-RestMethod "$node/health"
$nh | ConvertTo-Json -Compress
if (-not $nh.ok) { throw "node placeholder weights missing" }

Write-Host "GET /v1/agents + /v1/nodes"
$agents = Invoke-RestMethod "$core/v1/agents"
$nodes = Invoke-RestMethod "$core/v1/nodes"
if ($agents.items.Count -lt 1) { throw "seed agent missing" }
if ($nodes.items.Count -lt 1) { throw "seed node missing" }

Write-Host "POST /v1/capabilities (+ duplicate 409, mvp check 400)"
$capBody = @{
    code = "image.classify.smoke"
    version = 1
    name = "smoke-cap"
    description = "runtime register smoke"
    input_schema = @{ type = "object" }
    output_schema = @{ type = "object" }
    output_kind = "closed_set_labels"
    compute_tier = "M"
    trust_domain_min = "team"
    mvp_eligible = $true
    golden_set_ref = "smoke://manifest"
    golden_set_sha256 = ("a" * 64)
    golden_set_size = 10
    golden_metrics = @{ min_accuracy = 0.5; min_macro_f1 = 0.4; max_invalid_rate = 0.1 }
} | ConvertTo-Json -Depth 6
$capNew = Invoke-RestMethod -Method Post "$core/v1/capabilities" -ContentType "application/json" -Body $capBody
if (-not $capNew.id) { throw "capability create missing id" }
try {
    Invoke-RestMethod -Method Post "$core/v1/capabilities" -ContentType "application/json" -Body $capBody
    throw "duplicate capability should 409"
} catch {
    if ((Get-StatusCode $_) -ne 409) { throw }
}
try {
    $badBody = @{
        code = "image.classify.smoke-bad"
        version = 1
        name = "smoke-bad"
        input_schema = @{ type = "object" }
        output_schema = @{ type = "object" }
        output_kind = "freeform"
        compute_tier = "M"
        trust_domain_min = "team"
        mvp_eligible = $true
        golden_set_ref = "smoke://bad"
        golden_set_sha256 = ("b" * 64)
        golden_set_size = 10
        golden_metrics = @{ min_accuracy = 0.5 }
    } | ConvertTo-Json -Depth 6
    Invoke-RestMethod -Method Post "$core/v1/capabilities" -ContentType "application/json" -Body $badBody
    throw "mvp+freeform should 400"
} catch {
    if ((Get-StatusCode $_) -ne 400) { throw }
}

Write-Host "POST /v1/agents rejects .pth"
try {
    Invoke-RestMethod -Method Post "$core/v1/agents" -ContentType "application/json" -Body (@{
        name = "bad-pt"
        version = "0"
        manifest_hash = "x"
        weights_uri = "file:///tmp/model.pth"
        weights_sha256 = $nh.weights_sha256
        weights_format = "safetensors"
        arch = "TinyEuroSAT"
    } | ConvertTo-Json)
    throw "pth should reject"
} catch {
    if ((Get-StatusCode $_) -ne 400) { throw }
}

Write-Host "POST /v1/agents"
$agent = Invoke-RestMethod -Method Post "$core/v1/agents" -ContentType "application/json" -Body (@{
    name = "smoke-agent"
    version = "0.0.1-smoke"
    manifest_hash = "smoke-manifest"
    weights_uri = "file:///weights/placeholder.safetensors"
    weights_sha256 = $nh.weights_sha256
    arch = "TinyEuroSAT"
} | ConvertTo-Json)
$agentId = $agent.id

Write-Host "POST /v1/nodes (public S, not runner)"
$pub = Invoke-RestMethod -Method Post "$core/v1/nodes" -ContentType "application/json" -Body (@{
    name = "smoke-public-s"
    device_type = "PHONE"
    trust_domain = "public"
    compute_tier_max = "S"
    is_gate_runner = $false
} | ConvertTo-Json)
$pubId = $pub.id

Write-Host "POST gate-run on non-runner (expect 409)"
try {
    Invoke-RestMethod -Method Post "$core/v1/internal/gate-runs" -ContentType "application/json" -Body (@{
        agent_id = $agentId
        capability_id = $capId
        runner_node_id = $pubId
    } | ConvertTo-Json)
    throw "non-runner gate should reject"
} catch {
    if ((Get-StatusCode $_) -ne 409) { throw }
}

Write-Host "POST bind wrong hash (ready false)"
$badBind = Invoke-RestMethod -Method Post "$core/v1/agents/$agentId/bindings" -ContentType "application/json" -Body (@{
    node_id = $runnerId
    weights_sha256_seen = ("0" * 64)
} | ConvertTo-Json)
if ($badBind.ready) { throw "mismatch must not be READY" }

Write-Host "POST bind matching hash"
$okBind = Invoke-RestMethod -Method Post "$core/v1/agents/$agentId/bindings" -ContentType "application/json" -Body (@{
    node_id = $runnerId
    weights_sha256_seen = $nh.weights_sha256
} | ConvertTo-Json)
if (-not $okBind.ready) { throw "matching hash should be READY" }

Write-Host "POST gate-run + dummy PASSED (not golden-set scoring)"
$gr = Invoke-RestMethod -Method Post "$core/v1/internal/gate-runs" -ContentType "application/json" -Body (@{
    agent_id = $agentId
    capability_id = $capId
    runner_node_id = $runnerId
} | ConvertTo-Json)
if ($gr.status -ne "RUNNING") { throw "gate start $($gr.status)" }

Write-Host "POST gate finish wrong golden_set_sha256 (expect 400, S3)"
try {
    Invoke-RestMethod -Method Post "$core/v1/internal/gate-runs/$($gr.id)/finish" -ContentType "application/json" -Body (@{
        status = "PASSED"
        dummy = $true
        golden_score = 0.8
        cases_total = 40
        cases_passed = 32
        golden_set_sha256 = ("0" * 64)
        note = "s3 mismatch"
    } | ConvertTo-Json)
    throw "sha256 mismatch should reject"
} catch {
    if ((Get-StatusCode $_) -ne 400) { throw }
}

$fin = Invoke-RestMethod -Method Post "$core/v1/internal/gate-runs/$($gr.id)/finish" -ContentType "application/json" -Body (@{
    status = "PASSED"
    dummy = $true
    golden_score = 0.8
    cases_total = 40
    cases_passed = 32
    note = "smoke plumbing only"
} | ConvertTo-Json)
if (-not $fin.chain_minted) { throw "PASSED chain not minted" }

Write-Host "GET /openapi.yaml"
$code = curl.exe -s -o "$env:TEMP\capnet-openapi.yaml" -w "%{http_code}" "$core/openapi.yaml"
if ($code -ne "200") { throw "openapi.yaml HTTP $code" }
$head = Get-Content "$env:TEMP\capnet-openapi.yaml" -TotalCount 1
if ($head -notmatch "^openapi:") { throw "openapi.yaml not yaml" }

$gotAgent = Invoke-RestMethod "$core/v1/agents/$agentId"
$passed = @($gotAgent.capabilities | Where-Object { $_.gate_status -eq "PASSED" })
if ($passed.Count -lt 1) { throw "agent capability PASSED missing" }

Write-Host "POST /v1/tasks bad datasetId (expect 400)"
try {
    Invoke-RestMethod -Method Post "$core/v1/tasks" -ContentType "application/json" `
        -Body '{"datasetId":"not-allowed","caseId":"x"}'
    throw "allowlist should reject"
} catch {
    if ((Get-StatusCode $_) -ne 400) { throw }
}

Write-Host "POST /v1/tasks + claim + dummy execute"
$t = Invoke-RestMethod -Method Post "$core/v1/tasks" -ContentType "application/json" -Body (@{
    datasetId = "eurosat-rgb"
    caseId = "ic1-dummy-e2e"
    requestedAgentId = $agentId
} | ConvertTo-Json)
$taskId = $t.id

$c = Invoke-RestMethod -Method Post "$core/v1/internal/claim" -ContentType "application/json" -Body (@{
    task_id = $taskId
} | ConvertTo-Json)
if ($c.status -ne "LEASED") { throw "claim status $($c.status)" }
if ($c.agent_id -ne $agentId) { throw "claim agent $($c.agent_id)" }
if ($nh.weights_sha256 -ne $c.weights_sha256) {
    throw "DB agent hash != placeholder file. docker compose down -v 후 다시 up (옛 seed 볼륨)"
}

$e = Invoke-RestMethod -Method Post "$node/v1/execute" -ContentType "application/json" -Body (@{
    id = $c.id
    weights_sha256 = $c.weights_sha256
    input_ref = $c.input_ref
} | ConvertTo-Json)
if (-not $e.dummy) { throw "expected dummy=true" }
if ($e.core.task_status -ne "COMPLETED") { throw "task_status $($e.core.task_status)" }

$got = Invoke-RestMethod "$core/v1/tasks/$taskId"
if ($got.status -ne "COMPLETED") { throw "task $($got.status)" }
if ($got.assignment.status -ne "SUCCEEDED") { throw "assignment $($got.assignment.status)" }
if (-not $got.result_ref) { throw "missing result_ref (min certificate)" }

Write-Host "W1 smoke OK (crud + dummy gate chain + e2e)"
