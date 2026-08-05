$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$sql = Join-Path $PSScriptRoot "demo_violations.sql"
Get-Content -Raw $sql | docker compose --project-directory $root exec -T postgres `
    psql -U capnet -d capnet -v ON_ERROR_STOP=1
if ($LASTEXITCODE -ne 0) { throw "demo_violations psql failed" }
Write-Host "demo_violations finished (expect 6 REJECTED notices)"
