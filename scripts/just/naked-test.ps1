<#
.SYNOPSIS
  Run automated naked install test for a fleet repo in Windows Sandbox.

.DESCRIPTION
  Enforces NAKED_PC_INSTALL_STANDARD:
  1. Boots ephemeral Windows Sandbox with assets/sandbox and job dir mapped.
  2. Harness (winget -> git + just only) installs inside sandbox.
  3. Clones target repo.
  4. Smoke gate: just --list (halts immediately if invalid).
  5. Runs start.bat under observation and tests health endpoint.
  6. Outputs color-coded step results and exits 0 on PASS, 1 on FAIL.

.PARAMETER Repo
  Repository name (e.g. 'sandraschi/virtualization-mcp' or 'virtualization-mcp') or full https URL.

.PARAMETER Branch
  Git branch to test (default: 'main').

.PARAMETER ObserveSec
  Seconds to observe start.bat and health endpoint (default: 90).

.PARAMETER HealthUrl
  Optional health URL to probe (e.g. 'http://localhost:10701/health').

.EXAMPLE
  just naked-test repo=virtualization-mcp
  just naked-test repo=sandraschi/calibre-mcp observe=120
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Repo,
    [string]$Branch = "main",
    [int]$ObserveSec = 90,
    [string]$HealthUrl = ""
)

$ErrorActionPreference = "Stop"

# Clean positional prefix if user typed key=val
if ($Repo -match '^repo=(.+)$') { $Repo = $matches[1].Trim() }
if ($Branch -match '^branch=(.+)$') { $Branch = $matches[1].Trim() }
if ($HealthUrl -match '^health=(.+)$') { $HealthUrl = $matches[1].Trim() }

$repoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$assetsFolder = Join-Path $repoRoot "assets\sandbox"
$runsRoot = Join-Path (Split-Path -Parent $repoRoot) "_sandbox_runs"

# Normalize repo URL and inspect local repo if present
$repoClean = $Repo.Trim()
$localRepoPath = Join-Path (Split-Path -Parent $repoRoot) $repoClean
if (Test-Path -LiteralPath (Join-Path $localRepoPath ".git\config")) {
    try {
        $gitConfig = Get-Content -LiteralPath (Join-Path $localRepoPath ".git\config") -Raw
        if ($gitConfig -match 'url\s*=\s*([^\r\n]+)') {
            $repoUrl = $matches[1].Trim()
        }
        if ($Branch -eq "main" -and $gitConfig -match '\[branch\s+"([^"]+)"\]') {
            $Branch = $matches[1].Trim()
        }
    } catch { }
}
if (-not $repoUrl) {
    if ($repoClean -notlike "http*") {
        if ($repoClean -notlike "*/*") {
            $repoUrl = "https://github.com/sandraschi/$repoClean.git"
        } else {
            $repoUrl = "https://github.com/$repoClean.git"
        }
    } else {
        $repoUrl = $repoClean
    }
}
if (-not $HealthUrl -and (Test-Path -LiteralPath (Join-Path $localRepoPath "fleet-start.config.ps1"))) {
    try {
        $cfg = . (Join-Path $localRepoPath "fleet-start.config.ps1")
        if ($cfg.BackendPort -and $cfg.HealthPath) {
            $HealthUrl = "http://127.0.0.1:$($cfg.BackendPort)$($cfg.HealthPath)"
        }
    } catch { }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "  NAKED INSTALL TEST - FLEET HARNESS" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "  Target Repo  : $repoUrl" -ForegroundColor White
Write-Host "  Branch       : $Branch" -ForegroundColor White
Write-Host "  Observation  : ${ObserveSec}s" -ForegroundColor White
if ($HealthUrl) {
    Write-Host "  Health URL   : $HealthUrl" -ForegroundColor White
}
Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray

# Preflight check
$sandboxExe = Join-Path $env:WINDIR "System32\WindowsSandbox.exe"
if (-not (Test-Path -LiteralPath $sandboxExe)) {
    Write-Error "WindowsSandbox.exe not found! Windows Sandbox must be enabled in Windows Features."
    exit 2
}

if (-not (Test-Path -LiteralPath $assetsFolder)) {
    Write-Error "Sandbox assets directory not found at $assetsFolder"
    exit 2
}

# Ensure runs directory
if (-not (Test-Path -LiteralPath $runsRoot)) {
    New-Item -ItemType Directory -Path $runsRoot -Force | Out-Null
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$safeRepo = ($repoUrl.Split('/')[-1] -replace '\.git$', '') -replace '[^a-zA-Z0-9_\-]', '-'
$jobId = "naked-$safeRepo-$stamp"
$jobDir = Join-Path $runsRoot $jobId
New-Item -ItemType Directory -Path $jobDir -Force | Out-Null

$localRepoInSandbox = ""
if ($localRepoPath -and (Test-Path -LiteralPath (Join-Path $localRepoPath ".git"))) {
    $bareGitPath = Join-Path $jobDir "repo.git"
    Write-Host "Creating local bare clone of $localRepoPath into $bareGitPath..." -ForegroundColor Cyan
    & cmd.exe /c "git clone --bare --no-local `"$localRepoPath`" `"$bareGitPath`" >nul 2>&1"
    if (Test-Path -LiteralPath $bareGitPath) {
        $localRepoInSandbox = "C:\Job\repo.git"
        Write-Host "  Local bare clone ready ($localRepoInSandbox)." -ForegroundColor Green
    } else {
        Write-Warning "Failed to create local bare clone at $bareGitPath"
    }
}

$spec = [ordered]@{
    repo_url    = $repoUrl
    local_repo  = $localRepoInSandbox
    branch      = $Branch
    observe_sec = $ObserveSec
    health_url  = $HealthUrl
}
$spec | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $jobDir "spec.json") -Encoding UTF8

# Build WSB
$escapedAssets = [System.Security.SecurityElement]::Escape($assetsFolder)
$escapedJob = [System.Security.SecurityElement]::Escape($jobDir)
$wsbXml = @"
<Configuration>
<MappedFolders>
  <MappedFolder>
    <HostFolder>$escapedAssets</HostFolder>
    <SandboxFolder>C:\Assets</SandboxFolder>
    <ReadOnly>false</ReadOnly>
  </MappedFolder>
  <MappedFolder>
    <HostFolder>$escapedJob</HostFolder>
    <SandboxFolder>C:\Job</SandboxFolder>
    <ReadOnly>false</ReadOnly>
  </MappedFolder>
</MappedFolders>
<VGpu>Enable</VGpu>
<Networking>Enable</Networking>
<MemoryInMB>8192</MemoryInMB>
<LogonCommand>
  <Command>cmd.exe /c C:\Assets\Run-NakedTest.cmd</Command>
</LogonCommand>
</Configuration>
"@

$tempWsb = Join-Path $env:TEMP "$jobId.wsb"
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($tempWsb, $wsbXml, $utf8Bom)

$sbProcs = Get-Process -Name "WindowsSandboxServer", "WindowsSandboxRemoteSession", "WindowsSandboxClient", "WindowsSandbox" -ErrorAction SilentlyContinue
if ($sbProcs) {
    Write-Host "Closing existing Windows Sandbox instances to ensure fresh boot..." -ForegroundColor Yellow
    & cmd.exe /c "taskkill /F /IM WindowsSandboxServer.exe /IM WindowsSandboxRemoteSession.exe /IM WindowsSandboxClient.exe /IM WindowsSandbox.exe >nul 2>&1"
    for ($i = 0; $i -lt 20; $i++) {
        $p = Get-Process -Name "WindowsSandboxServer", "WindowsSandboxRemoteSession", "WindowsSandboxClient", "WindowsSandbox" -ErrorAction SilentlyContinue
        if (-not $p) { break }
        Start-Sleep -Milliseconds 500
    }
    Start-Sleep -Seconds 3
}

Write-Host "Starting Windows Sandbox instance [$jobId]..." -ForegroundColor Cyan
& cmd.exe /c "`"$sandboxExe`" `"$tempWsb`""

Write-Host "Waiting for Sandbox to boot and report progress..." -ForegroundColor DarkGray

$resultPath = Join-Path $jobDir "RESULT.json"
$logPath = Join-Path $jobDir "naked-test-launch.log"
$startLogPath = Join-Path $jobDir "start-bat.log"
$progressPath = Join-Path $jobDir "PROGRESS.json"
$deadline = (Get-Date).AddSeconds($ObserveSec + 600)
$lastLogLine = 0
$lastStartLogLine = 0
$lastGate = ""

while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $resultPath) {
        break
    }

    # Stream new lines from launch log if present
    if (Test-Path -LiteralPath $logPath) {
        try {
            $lines = @(Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue)
            if ($lines.Count -gt $lastLogLine) {
                for ($i = $lastLogLine; $i -lt $lines.Count; $i++) {
                    Write-Host "  [sandbox] $($lines[$i])" -ForegroundColor Gray
                }
                $lastLogLine = $lines.Count
            }
        } catch { }
    }

    # Stream new lines from start.bat log if present
    if (Test-Path -LiteralPath $startLogPath) {
        try {
            $slines = @(Get-Content -LiteralPath $startLogPath -ErrorAction SilentlyContinue)
            if ($slines.Count -gt $lastStartLogLine) {
                for ($i = $lastStartLogLine; $i -lt $slines.Count; $i++) {
                    Write-Host "  [start.bat] $($slines[$i])" -ForegroundColor DarkCyan
                }
                $lastStartLogLine = $slines.Count
            }
        } catch { }
    }

    # Check progress updates
    if (Test-Path -LiteralPath $progressPath) {
        try {
            $prog = Get-Content -LiteralPath $progressPath -Raw | ConvertFrom-Json
            if ($prog.last_step -and $prog.last_step -ne $lastGate) {
                $lastGate = $prog.last_step
                Write-Host "  -> Gate completed: $lastGate" -ForegroundColor Yellow
            }
        } catch { }
    }

    # Check if sandbox has completely terminated
    $sbProcs = Get-Process -Name "WindowsSandboxServer", "WindowsSandboxRemoteSession", "WindowsSandboxClient", "WindowsSandbox" -ErrorAction SilentlyContinue
    if (-not $sbProcs -and (Test-Path -LiteralPath $resultPath)) {
        break
    }

    Start-Sleep -Seconds 3
    if ($lastLogLine -eq 0) {
        Write-Host -NoNewline "."
    }
}
Write-Host ""

function Cleanup-Sandbox {
    try {
        & cmd.exe /c "taskkill /F /IM WindowsSandboxServer.exe /IM WindowsSandboxRemoteSession.exe /IM WindowsSandboxClient.exe /IM WindowsSandbox.exe >nul 2>&1"
    } catch { }
}

if (-not (Test-Path -LiteralPath $resultPath)) {
    Cleanup-Sandbox
    Write-Host "TIMEOUT: Sandbox did not write RESULT.json within deadline." -ForegroundColor Red
    Write-Host "Job directory preserved at: $jobDir" -ForegroundColor DarkGray
    exit 3
}

try {
    $rawResult = Get-Content -LiteralPath $resultPath -Raw -Encoding UTF8
    $res = $rawResult | ConvertFrom-Json
} catch {
    Cleanup-Sandbox
    Write-Host "ERROR: Could not parse RESULT.json : $($_.Exception.Message)" -ForegroundColor Red
    exit 4
}

Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "  TEST RESULTS" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Magenta

foreach ($s in $res.steps) {
    $name = $s.name
    $code = $s.exit
    $ms = $s.ms
    $note = $s.note
    if ($code -eq 0) {
        Write-Host "  [PASS] Step: $($name.PadRight(12)) Exit: 0   Duration: $($ms)ms" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Step: $($name.PadRight(12)) Exit: $code   Duration: $($ms)ms" -ForegroundColor Red
        if ($note) {
            Write-Host "         Note: $note" -ForegroundColor Yellow
        }
    }
}

Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray
Cleanup-Sandbox
if ($res.pass -eq $true) {
    Write-Host "  FINAL STATUS: PASS" -ForegroundColor Green
    if ($res.note) { Write-Host "  Note: $($res.note)" -ForegroundColor DarkGray }
    exit 0
} else {
    Write-Host "  FINAL STATUS: FAIL (Failed at: $($res.failed_step))" -ForegroundColor Red
    if ($res.note) { Write-Host "  Note: $($res.note)" -ForegroundColor Red }
    if ($res.log_tail -and $res.log_tail.Count -gt 0) {
        Write-Host ""
        Write-Host "--- Log Tail (Desktop\naked-test-launch.log) ---" -ForegroundColor Yellow
        $res.log_tail | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    }
    exit 1
}
