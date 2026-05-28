<#
.SYNOPSIS
  Launch Windows Sandbox for nearly-naked INSTALL.md testing (winget only, no dev stack).

.DESCRIPTION
  Maps assets\sandbox to C:\Assets and runs Run-Consumer.cmd at logon.
  Unlike Launch-DevInfraSandbox.ps1, does NOT install git, node, python, just, ruff, or biome.

.PARAMETER InstallClaudeDesktop
  Set CONSUMER_INSTALL_CLAUDE=1 so Setup-ConsumerSandbox.ps1 installs Claude Desktop MSIX
  (fixture for Option A drag-and-drop .mcpb tests).

.PARAMETER Plain
  Launch minimal sandbox with no logon script (pure stock Win11 session).

.EXAMPLE
  .\scripts\Launch-ConsumerSandbox.ps1
  .\scripts\Launch-ConsumerSandbox.ps1 -InstallClaudeDesktop
#>

param(
    [switch]$InstallClaudeDesktop,
    [switch]$Plain
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$hostAssets = Join-Path $repoRoot 'assets\sandbox'

$sandboxExe = Join-Path $env:WINDIR 'System32\WindowsSandbox.exe'
if (-not (Test-Path -LiteralPath $sandboxExe)) {
    throw 'WindowsSandbox.exe not found. Enable the Windows Sandbox optional feature.'
}

$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$tempWsb = Join-Path $env:TEMP ("virtualization-mcp-Consumer-{0}.wsb" -f $stamp)
$utf8Bom = New-Object System.Text.UTF8Encoding $true

if ($Plain) {
    $wsbXml = @"
<Configuration>
  <VGpu>Enable</VGpu>
  <Networking>Enable</Networking>
  <MemoryInMB>8192</MemoryInMB>
</Configuration>
"@
    [System.IO.File]::WriteAllText($tempWsb, $wsbXml, $utf8Bom)
    Write-Host "Starting plain consumer sandbox (no logon script): $tempWsb" -ForegroundColor Cyan
    Start-Process -FilePath $sandboxExe -ArgumentList "`"$tempWsb`""
    return
}

$required = @(
    'Setup-ConsumerSandbox.ps1',
    'Run-Consumer.cmd',
    'Show-ConsumerLog.ps1',
    'lib\Winget-Bootstrap.ps1'
)
foreach ($rel in $required) {
    $full = Join-Path $hostAssets $rel
    if (-not (Test-Path -LiteralPath $full)) {
        throw "Missing $full"
    }
}

$escapedHost = [System.Security.SecurityElement]::Escape($hostAssets)
$logonCmd = 'C:\Assets\Run-Consumer.cmd'
if ($InstallClaudeDesktop) {
    $logonCmd = 'cmd.exe /c "set CONSUMER_INSTALL_CLAUDE=1&& C:\Assets\Run-Consumer.cmd"'
}

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
    <Command>$logonCmd</Command>
  </LogonCommand>
</Configuration>
"@

[System.IO.File]::WriteAllText($tempWsb, $wsbXml, $utf8Bom)
Write-Host "Starting consumer sandbox: $tempWsb" -ForegroundColor Cyan
if ($InstallClaudeDesktop) {
    Write-Host 'Claude Desktop MSIX will be installed as test fixture.' -ForegroundColor DarkGray
}
Start-Process -FilePath $sandboxExe -ArgumentList "`"$tempWsb`""
