# Unified lint: Ruff (Python: src + webapp/backend) + Biome (webapp/frontend).
# Check-only: exits nonzero on the first failure. Use fix.ps1 to autofix.
# Python scope intentionally omits tests/ and scripts/ (ruff-excluded in
# pyproject.toml: auto-generated tests carry S110 try-except-pass).

param(
    [switch]$Fix
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ruffScope = @("src", "webapp/backend")

if ($Fix) {
    Write-Host "==> ruff check --fix ($($ruffScope -join ', '))" -ForegroundColor Cyan
    uv run ruff check --fix @ruffScope
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "==> ruff format ($($ruffScope -join ', '))" -ForegroundColor Cyan
    uv run ruff format @ruffScope
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    if (Test-Path "webapp/frontend/package.json") {
        Write-Host "==> biome check --write (webapp/frontend)" -ForegroundColor Cyan
        Push-Location webapp/frontend
        try {
            npm run biome
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "==> ruff check ($($ruffScope -join ', '))" -ForegroundColor Cyan
    uv run ruff check @ruffScope
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "==> ruff format --check ($($ruffScope -join ', '))" -ForegroundColor Cyan
    uv run ruff format --check @ruffScope
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    if (Test-Path "webapp/frontend/package.json") {
        Write-Host "==> biome ci (webapp/frontend)" -ForegroundColor Cyan
        Push-Location webapp/frontend
        try {
            npm run biome:ci
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        } finally {
            Pop-Location
        }
    }
}

Write-Host "Lint passed." -ForegroundColor Green
