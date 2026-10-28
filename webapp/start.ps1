# Fleet unified launcher - do not edit logic here.
# Change fleet-start.config.ps1 at the repo root instead.
param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$ReuseIfRunning
)

$ErrorActionPreference = 'Stop'
$ReposRoot = if ($env:FLEET_REPOS_ROOT) { $env:FLEET_REPOS_ROOT } else { 'D:\Dev\repos' }
$EnginePath = Join-Path $ReposRoot 'mcp-central-docs\scripts\Invoke-FleetWebappStart.ps1'

$configCandidates = @(
    (Join-Path $PSScriptRoot 'fleet-start.config.ps1'),
    (Join-Path (Split-Path -Parent $PSScriptRoot) 'fleet-start.config.ps1')
)
$configPath = $null
foreach ($candidate in $configCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $configPath = $candidate
        break
    }
}
if (-not $configPath) {
    Write-Host 'ERROR: Missing fleet-start.config.ps1 (repo root or beside start.ps1).' -ForegroundColor Red
    exit 1
}

# Mode 1: Central Fleet Engine (when mcp-central-docs is available)
if (Test-Path -LiteralPath $EnginePath) {
    . $EnginePath
    Start-FleetWebapp @PSBoundParameters -ConfigPath $configPath -LauncherRoot $PSScriptRoot
    exit 0
}

# Mode 2: Standalone Fallback (Naked install on new machine / public user clone)
Write-Host "Central fleet engine not found ($EnginePath) - starting in standalone mode." -ForegroundColor Yellow

$cfg = . $configPath
$repoRoot = Split-Path -Parent $PSScriptRoot
if (Test-Path (Join-Path $PSScriptRoot 'pyproject.toml')) { $repoRoot = $PSScriptRoot }

$backendPort = if ($cfg.BackendPort) { [int]$cfg.BackendPort } else { 10720 }
$frontendPort = if ($cfg.FrontendPort) { [int]$cfg.FrontendPort } else { 10721 }

$webRel = if ($cfg.WebRoot) { $cfg.WebRoot } else { 'webapp\frontend' }
$webRoot = if ([System.IO.Path]::IsPathRooted($webRel)) { $webRel } else { Join-Path $repoRoot $webRel }
if (-not (Test-Path -LiteralPath $webRoot)) { $webRoot = $PSScriptRoot }

# NAKED_PC_INSTALL_STANDARD sec. 1: prereq guard via winget.
# uv covers Python implicitly (auto-fetched); Node.js ships npm.
# The rig only guarantees git + just - everything else MUST come from here,
# or a naked box fails with "'npm'/'uv' is not recognized" (speech-mcp 2026-10-28).
function Require-Command {
    param([string]$Cmd, [string]$WingetId, [string]$Label)
    if (Get-Command $Cmd -ErrorAction SilentlyContinue) { return }
    Write-Host "  $Label not found - installing via winget ..." -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: winget unavailable. Install $Label manually ($WingetId)." -ForegroundColor Red
        exit 1
    }
    winget install --id $WingetId --source winget --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: winget install $WingetId failed with exit code $LASTEXITCODE." -ForegroundColor Red
        exit 1
    }
    # Re-read registry PATH, then append well-known shim dirs that land
    # after this session began (WinGet Links for uv, nodejs, npm roaming).
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
    foreach ($ep in @((Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'), (Join-Path $env:APPDATA 'npm'), 'C:\Program Files\nodejs')) {
        if ((Test-Path -LiteralPath $ep) -and ($env:Path -notlike "*$ep*")) { $env:Path = "$ep;$($env:Path)" }
    }
    if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) {
        Write-Host "Installed $Label but '$Cmd' still not in PATH. Reopen PowerShell and retry." -ForegroundColor Red
        exit 1
    }
    Write-Host "  $Label ready." -ForegroundColor Green
}
Require-Command "uv" "astral-sh.uv" "uv (Python package manager)"
Require-Command "node" "OpenJS.NodeJS.LTS" "Node.js LTS (includes npm)"

# Frontend deps (naked clones have no node_modules; the lockfile pins versions).
if (-not $BackendOnly -and $frontendPort -gt 0 -and (Test-Path -LiteralPath (Join-Path $webRoot 'package.json'))) {
    if (-not (Test-Path -LiteralPath (Join-Path $webRoot 'node_modules'))) {
        Push-Location $webRoot
        try {
            if (Test-Path -LiteralPath (Join-Path $webRoot 'package-lock.json')) {
                Write-Host "Installing frontend dependencies (npm ci)..." -ForegroundColor Cyan
                npm ci
            } else {
                Write-Host "WARNING: no package-lock.json in $webRoot - running npm install instead." -ForegroundColor Yellow
                npm install
            }
            if ($LASTEXITCODE -ne 0) { throw "frontend npm install failed with exit code $LASTEXITCODE" }
        } finally {
            Pop-Location
        }
    }
}

# Child-process logs (repo-local, gitignored). Windows stay open for live
# view; these files persist for forensics - the naked-test harness exfiltrates
# $repoRoot\logs\* to the host job dir (see docs/NAKED_TEST_RECIPE.md).
$logsDir = Join-Path $repoRoot 'logs'
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

# 1. Start Backend
if (-not $FrontendOnly -and $backendPort -gt 0 -and $cfg.Backend.Kind -ne 'none') {
    Write-Host "Starting backend on :$backendPort ... (log: logs\backend.log)" -ForegroundColor Cyan
    $bWorkDir = if ($cfg.Backend.WorkDir) {
        if ([System.IO.Path]::IsPathRooted($cfg.Backend.WorkDir)) { $cfg.Backend.WorkDir } else { Join-Path $repoRoot $cfg.Backend.WorkDir }
    } else { $repoRoot }

    $pyPath = if ($cfg.Backend.PythonPath) {
        $parts = $cfg.Backend.PythonPath -split ';' | ForEach-Object {
            if ([System.IO.Path]::IsPathRooted($_)) { $_ } else { Join-Path $repoRoot $_ }
        }
        $parts -join ';'
    } else { "$repoRoot;$repoRoot\src" }

    $backendExec = if ($cfg.Backend.Kind -eq 'module-serve') {
        $mod = if ($cfg.Backend.Module) { $cfg.Backend.Module } else { $cfg.Name }
        $args = if ($cfg.Backend.ServeArgs) { $cfg.Backend.ServeArgs } else { '--serve' }
        "python -m $mod $args"
    } elseif ($cfg.Backend.Kind -eq 'cli-serve') {
        $mod = if ($cfg.Backend.Module) { $cfg.Backend.Module } else { $cfg.Name }
        "$mod --serve --port $backendPort"
    } else {
        $target = if ($cfg.Backend.UvicornTarget) { $cfg.Backend.UvicornTarget } else { 'app.main:app' }
        "uvicorn $target --host 127.0.0.1 --port $backendPort"
    }

    $bCmd = "`$env:PYTHONPATH = '$pyPath'; `$env:WEB_PORT = '$backendPort'; Set-Location '$bWorkDir'; uv run --project '$repoRoot' $backendExec"
    Start-Process powershell.exe -ArgumentList @('-NoProfile', '-NoExit', '-Command', $bCmd) -WorkingDirectory $bWorkDir `
        -RedirectStandardOutput (Join-Path $logsDir 'backend.log') -RedirectStandardError (Join-Path $logsDir 'backend.err.log')
}

# 2. Start Frontend
if (-not $BackendOnly -and $frontendPort -gt 0 -and (Test-Path -LiteralPath $webRoot)) {
    Write-Host "Starting frontend on :$frontendPort ... (log: logs\frontend.log)" -ForegroundColor Cyan
    if ($cfg.Frontend.PortEnvVar) { Set-Item -Path "Env:$($cfg.Frontend.PortEnvVar)" -Value "$frontendPort" }
    if ($cfg.Frontend.ApiTargetEnv) { Set-Item -Path "Env:$($cfg.Frontend.ApiTargetEnv)" -Value "http://127.0.0.1:$backendPort" }

    $cmdFlag = if ($Headless) { '/c' } else { '/k' }
    if ($cfg.Frontend.Kind -eq 'next') {
        Start-Process cmd.exe -ArgumentList @($cmdFlag, "npm run dev -- -p $frontendPort -H 127.0.0.1") -WorkingDirectory $webRoot `
            -RedirectStandardOutput (Join-Path $logsDir 'frontend.log') -RedirectStandardError (Join-Path $logsDir 'frontend.err.log')
    } else {
        Start-Process cmd.exe -ArgumentList @($cmdFlag, "npm run dev -- --port $frontendPort --host 127.0.0.1") -WorkingDirectory $webRoot `
            -RedirectStandardOutput (Join-Path $logsDir 'frontend.log') -RedirectStandardError (Join-Path $logsDir 'frontend.err.log')
    }
}

# 3. Open Browser
if (-not $NoBrowser -and -not $Headless -and -not $BackendOnly -and $frontendPort -gt 0) {
    Start-Process "http://127.0.0.1:$frontendPort/"
}
