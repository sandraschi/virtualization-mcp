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
