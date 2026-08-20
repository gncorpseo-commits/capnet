# UC-7 증명 모드 교차 실행 — proof_ab.sh 의 PowerShell 판.
# Agent A·B를 각각 실게이트로 통과시킨 뒤, 동일 caseId를 requestedAgentId로
# 교차 할당해 게이트 사슬 위에서 비교한다.
#
# 사슬 밖 오프라인 비교(scripts/compare_ab)와 다르다. 여기는 전부 DB를 거친다.
#
# 사전 조건: docker compose up -d · apps/node/weights/ 에 A·B safetensors
# 촬영: Windows 본편에서 pwsh -File scripts\proof_ab.ps1 (WSL 전환 불필요)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$core = if ($env:CORE_URL) { $env:CORE_URL } else { "http://127.0.0.1:8000" }
$node = if ($env:NODE_URL) { $env:NODE_URL } else { "http://127.0.0.1:8001" }
$capId = "00000000-0000-4000-8000-000000000010"
$runnerId = "00000000-0000-4000-8000-000000000030"
$caseId = if ($env:CASE_ID) { $env:CASE_ID } else { "ic1-0001" }
$stamp = Get-Date -Format "yyyyMMddHHmmss"

function Invoke-CapNet {
    param(
        [Microsoft.PowerShell.Commands.WebRequestMethod]$Method = "Get",
        [Parameter(Mandatory = $true)][string]$Uri,
        [string]$Body
    )
    $headers = @{}
    if ($env:CAPNET_API_KEY) {
        $headers["Authorization"] = "CapNet-Key $($env:CAPNET_API_KEY)"
    }
    $params = @{
        Method = $Method
        Uri = $Uri
        Headers = $headers
    }
    if ($PSBoundParameters.ContainsKey("Body") -and $null -ne $Body) {
        $params["ContentType"] = "application/json"
        $params["Body"] = $Body
    }
    Invoke-RestMethod @params
}

function Get-WeightInfo {
    param(
        [Parameter(Mandatory = $true)]$NodeHealth,
        [Parameter(Mandatory = $true)][string]$FileName
    )
    $hits = @($NodeHealth.weights | Where-Object {
        $_.path -and $_.path.EndsWith($FileName) -and -not $_.placeholder
    })
    if ($hits.Count -lt 1) {
        throw "weights missing on node: $FileName"
    }
    if (-not $hits[0].arch) {
        throw "arch unknown on node: $FileName"
    }
    return $hits[0]
}

# 이름·가중치로 Agent를 등록하고 실게이트를 통과시킨다. 반환 = agentId
function Register-GatedAgent {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$WeightFile,
        [Parameter(Mandatory = $true)][string]$Sha,
        [Parameter(Mandatory = $true)][string]$Arch
    )

    $agent = Invoke-CapNet -Method Post -Uri "$core/v1/agents" -Body (@{
        name = $Label
        version = "0.1.0-$stamp"
        manifest_hash = "$Label-manifest"
        weights_uri = "file:///weights/$WeightFile"
        weights_sha256 = $Sha
        arch = $Arch
    } | ConvertTo-Json)

    $raw = docker compose --project-directory $root exec -T node-m-team `
        python -m app.score_gate --mode scratch --weights "/weights/$WeightFile" `
        --min-accuracy 0.68 --min-macro-f1 0.65 --max-invalid-rate 0.02
    if ($LASTEXITCODE -notin 0, 2) {
        throw "score_gate failed rc=$LASTEXITCODE ($Label)"
    }
    $score = $raw | ConvertFrom-Json
    Write-Host ("  {0,-22} status={1} acc={2:N4} f1={3:N4}" -f `
        $Label, $score.status, $score.golden_score, $score.macro_f1)

    $gr = Invoke-CapNet -Method Post -Uri "$core/v1/internal/gate-runs" -Body (@{
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
        min_per_class_recall = $score.min_per_class_recall
        golden_set_sha256 = $gr.golden_set_sha256
        note = "golden-set-v1 scratch $Label"
    } | ConvertTo-Json

    Invoke-CapNet -Method Post -Uri "$core/v1/internal/gate-runs/$($gr.id)/finish" `
        -Body $finishBody | Out-Null

    if ($score.status -ne "PASSED") {
        Write-Host "  ${Label}: 실게이트 FAILED — 교차 실행 대상에서 제외 (정직)"
        throw "gate FAILED for $Label"
    }

    Invoke-CapNet -Method Post -Uri "$core/v1/agents/$($agent.id)/bindings" -Body (@{
        node_id = $runnerId
        weights_sha256_seen = $Sha
    } | ConvertTo-Json) | Out-Null

    return [string]$agent.id
}

# 지정 Agent로 동일 case를 실행하고 label을 돌려준다. Core 중개만.
function Invoke-ProofCase {
    param([Parameter(Mandatory = $true)][string]$AgentId)

    $task = Invoke-CapNet -Method Post -Uri "$core/v1/tasks" -Body (@{
        datasetId = "eurosat-rgb"
        caseId = $caseId
        requestedAgentId = $AgentId
    } | ConvertTo-Json)

    $got = $null
    for ($i = 0; $i -lt 60; $i++) {
        $got = Invoke-CapNet -Uri "$core/v1/tasks/$($task.id)"
        if ($got.status -eq "COMPLETED" -or $got.status -eq "FAILED") { break }
        Start-Sleep -Seconds 1
    }
    if ($null -eq $got) { throw "task poll returned nothing" }
    if ($got.status -ne "COMPLETED") { throw "task not completed: $($got.status)" }
    if (-not $got.assignment) { throw "assignment missing" }
    if ([string]$got.assignment.agent_id -ne $AgentId) {
        throw "requestedAgentId 무시됨: 요청=$AgentId 할당=$($got.assignment.agent_id)"
    }

    $res = $got.result_ref
    if ($res -is [string]) { $res = $res | ConvertFrom-Json }
    if ($res.dummy) { throw "execute was dummy" }
    return [string]$res.label
}

$h = Invoke-CapNet -Uri "$core/health"
if (-not $h.ok) { throw "core health failed" }
$nh = Invoke-CapNet -Uri "$node/health"

$infoA = Get-WeightInfo -NodeHealth $nh -FileName "eurosat_scratch.safetensors"
$infoB = Get-WeightInfo -NodeHealth $nh -FileName "eurosat_scratch_b.safetensors"
$shaA = [string]$infoA.sha256
$shaB = [string]$infoB.sha256
if ($shaA -eq $shaB) {
    throw "A와 B의 weights_sha256이 같다 — 교체 비교가 무의미하다"
}

Write-Host "== 실게이트 (team gate-runner) =="
$agentA = Register-GatedAgent -Label "proof-agent-a" -WeightFile "eurosat_scratch.safetensors" `
    -Sha $shaA -Arch ([string]$infoA.arch)
$agentB = Register-GatedAgent -Label "proof-agent-b" -WeightFile "eurosat_scratch_b.safetensors" `
    -Sha $shaB -Arch ([string]$infoB.arch)

Write-Host "== 교차 할당 (동일 case=$caseId) =="
$labelA = Invoke-ProofCase -AgentId $agentA
$labelB = Invoke-ProofCase -AgentId $agentB
Write-Host "  A($agentA) → $labelA"
Write-Host "  B($agentB) → $labelB"

if ($labelA -eq $labelB) {
    Write-Host "AGREE — 사슬 위에서 Agent를 교체해도 같은 라벨"
} else {
    Write-Host "DISAGREE — 같은 계약을 통과했으나 라벨이 다름 (case 1건은 판정 근거가 아니다)"
}

Write-Host ""
Write-Host "주의: 이 스크립트는 case 1건의 교차 실행이다. 편차 수치·등가 보장은 여기서 말하지 않는다."
Write-Host "여기서 증명되는 것은 「게이트를 통과한 두 Agent가 사슬 위에서 교체 가능하다」는 배관 사실이다."
Write-Host "촬영 자막은 shoot-day-runbook.md §2-A 두 줄만 쓴다 (같은 답이라고 말하지 않는다)."
