<#
.SYNOPSIS
  Launch Windows Sandbox with virtualization-mcp dev-infra setup (winget + git, gh, npm, Python, ruff, just, biome).

.DESCRIPTION
  Writes a temporary .wsb whose HostFolder points at this repo's assets\sandbox (no manual path edit).
  Then starts WindowsSandbox.exe. Requires Windows Sandbox optional feature.
#>

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$hostAssets = Join-Path $repoRoot 'assets\sandbox'
$scriptInAssets = Join-Path $hostAssets 'Setup-DevInfraSandbox.ps1'
$cmdInAssets = Join-Path $hostAssets 'Run-DevInfra.cmd'
$showLog = Join-Path $hostAssets 'Show-DevInfraLog.ps1'

if (-not (Test-Path -LiteralPath $scriptInAssets)) {
  throw "Missing $scriptInAssets"
}
if (-not (Test-Path -LiteralPath $cmdInAssets)) {
  throw "Missing $cmdInAssets"
}
if (-not (Test-Path -LiteralPath $showLog)) {
  throw "Missing $showLog"
}

$sandboxExe = Join-Path $env:WINDIR 'System32\WindowsSandbox.exe'
if (-not (Test-Path -LiteralPath $sandboxExe)) {
  throw 'WindowsSandbox.exe not found. Enable the Windows Sandbox optional feature.'
}

$existingProcs = Get-Process -Name 'WindowsSandboxClient', 'WindowsSandbox' -ErrorAction SilentlyContinue
if ($existingProcs) {
  Write-Host 'Terminating active Windows Sandbox instance (singleton constraint)...' -ForegroundColor Yellow
  $existingProcs | Stop-Process -Force -ErrorAction SilentlyContinue
  # HARDENED 2026-09-17: was a blind Start-Sleep -Seconds 2 - Windows Sandbox
  # teardown (tearing down its VM) can genuinely exceed 2s, and launching a new
  # sandbox while the old one is still shutting down violates the singleton
  # constraint this code exists to enforce (TRAPS_AND_PITFALLS.md #36). Poll.
  $sandboxKillWaitSec = 20
  $sandboxKillElapsed = 0
  while ($sandboxKillElapsed -lt $sandboxKillWaitSec -and (Get-Process -Name 'WindowsSandboxClient', 'WindowsSandbox' -ErrorAction SilentlyContinue)) {
    Start-Sleep -Milliseconds 500
    $sandboxKillElapsed += 0.5
  }
  if (Get-Process -Name 'WindowsSandboxClient', 'WindowsSandbox' -ErrorAction SilentlyContinue) {
    Write-Host "  WARNING: old Windows Sandbox still alive after ${sandboxKillWaitSec}s" -ForegroundColor DarkYellow
  }
}

$escapedHost = [System.Security.SecurityElement]::Escape($hostAssets)
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$tempWsb = Join-Path $env:TEMP ("virtualization-mcp-DevInfra-{0}.wsb" -f $stamp)

$wsbXml = @"
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$escapedHost</HostFolder>
      <SandboxFolder>C:\Assets</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <VGpu>Enable</VGpu>
  <Networking>Enable</Networking>
  <MemoryInMB>8192</MemoryInMB>
  <LogonCommand>
    <Command>C:\Assets\Run-DevInfra.cmd</Command>
  </LogonCommand>
</Configuration>
"@

$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($tempWsb, $wsbXml, $utf8Bom)
Write-Host "Starting sandbox with: $tempWsb" -ForegroundColor Cyan
Start-Process -FilePath $sandboxExe -ArgumentList "`"$tempWsb`""
