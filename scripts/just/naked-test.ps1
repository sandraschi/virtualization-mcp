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

$repoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$assetsFolder = Join-Path $repoRoot "assets\sandbox"
$runsRoot = Join-Path (Split-Path -Parent $repoRoot) "_sandbox_runs"

# Normalize repo URL
$repoUrl = $Repo.Trim()
if ($repoUrl -notlike "http*") {
    if ($repoUrl -notlike "*/*") {
        $repoUrl = "https://github.com/sandraschi/$repoUrl.git"
    } else {
        $repoUrl = "https://github.com/$repoUrl.git"
    }
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

$spec = [ordered]@{
    repo_url    = $repoUrl
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
  <Command>C:\Assets\Run-NakedTest.cmd</Command>
</LogonCommand>
</Configuration>
"@

$tempWsb = Join-Path $env:TEMP "$jobId.wsb"
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($tempWsb, $wsbXml, $utf8Bom)

Write-Host "Starting Windows Sandbox instance [$jobId]..." -ForegroundColor Cyan
Start-Process -FilePath $sandboxExe -ArgumentList "`"$tempWsb`""

Write-Host "Waiting for Sandbox to boot and report progress..." -ForegroundColor DarkGray

$resultPath = Join-Path $jobDir "RESULT.json"
$deadline = (Get-Date).AddSeconds($ObserveSec + 600)
$lastStepCount = 0

while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $resultPath) {
        break
    }
    # Check if sandbox is still running
    $sbProcs = Get-Process -Name "WindowsSandboxClient", "WindowsSandbox" -ErrorAction SilentlyContinue
    if (-not $sbProcs -and (Test-Path -LiteralPath $resultPath)) {
        break
    }
    Start-Sleep -Seconds 5
    Write-Host -NoNewline "."
}
Write-Host ""

if (-not (Test-Path -LiteralPath $resultPath)) {
    Write-Host "TIMEOUT: Sandbox did not write RESULT.json within deadline." -ForegroundColor Red
    Write-Host "Job directory preserved at: $jobDir" -ForegroundColor DarkGray
    exit 3
}

try {
    $rawResult = Get-Content -LiteralPath $resultPath -Raw -Encoding UTF8
    $res = $rawResult | ConvertFrom-Json
} catch {
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
