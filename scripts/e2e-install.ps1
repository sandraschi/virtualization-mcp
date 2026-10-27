# Install Playwright E2E prerequisites (webapp/frontend/e2e + playwright.config.ts).
# - Ensures node/npm exist (fail loud otherwise).
# - Ensures @playwright/test resolves WITHOUT mutating package.json
#   (npm install --no-save). To pin it properly, run:
#     cd webapp/frontend; npm install -D @playwright/test
# - Installs the chromium browser (user-scope, no elevation).
#   OS dependencies (--with-deps) are intentionally skipped: needs admin.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $Root "webapp\frontend"
Set-Location $FrontendDir

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "node not found. Install Node.js LTS (winget: OpenJS.NodeJS.LTS), then retry."
    exit 1
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "npm not found (ships with Node.js). Reinstall Node.js LTS, then retry."
    exit 1
}

$pwBin = Join-Path $FrontendDir "node_modules\.bin\playwright.cmd"
if (-not (Test-Path -LiteralPath $pwBin)) {
    Write-Host "Installing @playwright/test (--no-save, package.json untouched)..." -ForegroundColor Cyan
    npm install --no-save @playwright/test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    if (-not (Test-Path -LiteralPath $pwBin)) {
        Write-Error "Playwright install did not land node_modules/.bin/playwright.cmd - aborting."
        exit 1
    }
}

Write-Host "Installing chromium browser for Playwright..." -ForegroundColor Cyan
& $pwBin install chromium
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "E2E prerequisites ready. Run: just e2e" -ForegroundColor Green
Write-Host "(needs backend :10701 + frontend :10700 up - start with .\\webapp\\start.ps1)" -ForegroundColor DarkGray
