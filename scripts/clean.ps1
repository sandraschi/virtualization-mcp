# Safe-tier cleanup: regenerable build/test artifacts only.
# NEVER touches .venv, node_modules, target/ (expensive rebuilds) or sources.
# Everything removed is gitignored. CI-friendly: no prompts, exit 0.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$removedBytes = 0
$removedCount = 0

function Remove-TreeIfPresent {
    param([string]$Path)
    $full = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $Root $Path }
    if (Test-Path -LiteralPath $full) {
        try {
            $bytes = (Get-ChildItem -LiteralPath $full -Recurse -Force -ErrorAction SilentlyContinue |
                Measure-Object -Property Length -Sum).Sum
            if ($bytes) { $script:removedBytes += $bytes }
        } catch { }
        Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction Stop
        $script:removedCount++
        $display = if ($full.StartsWith($Root)) { $full.Substring($Root.Length + 1) } else { $full }
        Write-Host "  removed $display" -ForegroundColor DarkGray
    }
}

function Remove-FilesIfPresent {
    param([string]$Dir, [string]$Pattern)
    Get-ChildItem -LiteralPath (Join-Path $Root $Dir) -Filter $Pattern -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            $script:removedBytes += $_.Length
            $script:removedCount++
            Remove-Item -LiteralPath $_.FullName -Force
            Write-Host "  removed $($_.FullName.Substring($Root.Length + 1))" -ForegroundColor DarkGray
        }
}

Write-Host "Cleaning regenerable artifacts..." -ForegroundColor Cyan

# Build outputs (all gitignored)
Remove-TreeIfPresent "dist"
Remove-TreeIfPresent "build"
Remove-TreeIfPresent "webapp/frontend/dist"
Remove-TreeIfPresent "webapp/frontend/test-results"
Remove-TreeIfPresent "webapp/frontend/playwright-report"
Remove-TreeIfPresent "webapp/frontend/.auth"

# Coverage + test reports (gitignored)
Remove-FilesIfPresent "." "coverage.xml"
Remove-FilesIfPresent "." "coverage.json"
Remove-FilesIfPresent "." ".coverage"
Remove-TreeIfPresent "junit"
Remove-TreeIfPresent ".pytest_cache"
Remove-TreeIfPresent ".ruff_cache"

# Python bytecode caches (top two levels; deeper ones die with their dist)
Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-TreeIfPresent (Join-Path $_.Name "__pycache__")
        Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Remove-TreeIfPresent (Join-Path $_.FullName "__pycache__") }
    }

$mb = [math]::Round($removedBytes / 1MB, 1)
Write-Host "Clean done: $removedCount paths, ${mb} MB reclaimed." -ForegroundColor Green
Write-Host "Kept: .venv, node_modules, target/ (use manual removal for a full nuke)." -ForegroundColor DarkGray
