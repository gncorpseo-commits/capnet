# CapNet CycloneDX SBOM 생성기
# 호스트 Python 3.12+ 필요 (WindowsApps Store stub 금지)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$out = Join-Path $root "sbom.json"

$candidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
)
$py = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $py) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notmatch "WindowsApps") { $py = $cmd.Source }
}
if (-not $py) {
    throw "Python 3.11+ not found. Install: winget install Python.Python.3.12"
}

Write-Host "python=$py"
& $py --version
& $py -m pip install -q cyclonedx-bom

# torch 버전은 Dockerfile 의 ARG 가 정본이다 — 여기에 다시 적으면 둘이 어긋난다.
$dockerfile = Get-Content (Join-Path $root "apps\node\Dockerfile")
$torchVer = ($dockerfile | Select-String "^ARG TORCH_VERSION=(.+)$").Matches.Groups[1].Value
$tvVer    = ($dockerfile | Select-String "^ARG TORCHVISION_VERSION=(.+)$").Matches.Groups[1].Value
if (-not $torchVer -or -not $tvVer) { throw "apps/node/Dockerfile 에서 torch 핀을 읽지 못했다" }

$req = Join-Path $env:TEMP "capnet-sbom-reqs.txt"
$core = Get-Content (Join-Path $root "apps\core\requirements.txt")
$node = Get-Content (Join-Path $root "apps\node\requirements.txt")
# capreq 는 pyproject.toml 로 선언한다 — .sh 와 같은 목록을 넣는다 (큐 #86: 여기만 빠져 있었다).
$capreq = & $py -c "import sys,tomllib; d=tomllib.load(open(sys.argv[1],'rb'))['project']; s=list(d.get('dependencies',[])); [s.extend(v) for v in d.get('optional-dependencies',{}).values()]; print('\n'.join(s))" (Join-Path $root "capreq\pyproject.toml")
if ($LASTEXITCODE -ne 0 -or -not $capreq) { throw "capreq/pyproject.toml 에서 의존성을 못 읽었다" }
# 같은 이름이 여러 자리에 있으면(fastapi 가 core·node·capreq) 첫 것만 — .sh 의 awk 와 같다.
$seen = @{}
@($core + $node + $capreq + @("torch==$torchVer", "torchvision==$tvVer")) |
    Where-Object { $_ -and $_ -notmatch "^\s*#" } |
    ForEach-Object { $n = ($_ -split '[=<>!~;\[]')[0].Trim(); if (-not $seen.ContainsKey($n)) { $seen[$n] = $true; $_ } } |
    Set-Content -Path $req -Encoding utf8

$raw = Join-Path $env:TEMP "capnet-sbom-raw.json"
$env:PYTHONIOENCODING = "utf-8"
& $py -m cyclonedx_py requirements $req -o $raw --of JSON
if ($LASTEXITCODE -ne 0) { throw "cyclonedx_py failed" }

& $py (Join-Path $PSScriptRoot "enrich_sbom.py") $raw $out
if ($LASTEXITCODE -ne 0) { throw "enrich_sbom.py failed" }
Write-Host "OK $out"
