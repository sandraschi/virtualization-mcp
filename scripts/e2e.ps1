# Run the Playwright E2E smoke suite (webapp/frontend/e2e, playwright.config.ts).
# Prerequisites (fail loud, no side effects):
# - backend on http://127.0.0.1:10701 (/health) and frontend on
#   http://127.0.0.1:10700 - start them first with .\webapp\start.ps1.
#   This script never starts servers itself (no orphaned dev processes).
# - Playwright installed - run `just e2e-install` first if missing.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $Root "webapp\frontend"
Set-Location $FrontendDir

$BackendUrl = "http://127.0.0.1:10701"
$FrontendUrl = "http://127.0.0.1:10700"

try {
    $r = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 5
    if ([int]$r.StatusCode -ne 200) { throw "status $($r.StatusCode)" }
} catch {
    Write-Error "Backend not healthy at $BackendUrl/health ($($_.Exception.Message)). Start it with .\\webapp\\start.ps1, then retry."
    exit 1
}

try {
    $r = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -TimeoutSec 5
    if ([int]$r.StatusCode -ne 200) { throw "status $($r.StatusCode)" }
} catch {
    Write-Error "Frontend not reachable at $FrontendUrl ($($_.Exception.Message)). Start it with .\\webapp\\start.ps1, then retry."
    exit 1
}

$pwBin = Join-Path $FrontendDir "node_modules\.bin\playwright.cmd"
if (-not (Test-Path -LiteralPath $pwBin)) {
    Write-Error "Playwright not installed (no node_modules/.bin/playwright.cmd). Run ``just e2e-install`` first, then retry."
    exit 1
}

Write-Host "Backend + frontend up. Running Playwright suite..." -ForegroundColor Cyan
& $pwBin test
exit $LASTEXITCODE
