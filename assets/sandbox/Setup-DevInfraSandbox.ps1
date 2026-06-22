<#
.SYNOPSIS
  virtualization-mcp: bootstrap winget in Windows Sandbox, then install git, gh, npm (Node LTS), Python, ruff, just, biome.

.DESCRIPTION
  Intended to run from the mapped folder as C:\Assets (see DevInfra.wsb or scripts/Launch-DevInfraSandbox.ps1).
  Uses GitHub MSIX assets for winget (no Microsoft Store / no PSGallery Repair-WinGetPackageManager path).

.NOTES
  Do not use #Requires -RunAsAdministrator: Windows Sandbox LogonCommand often runs in a context where that
  directive aborts the script before any output, so installs never start. The container user is already admin.

  Requires outbound HTTPS. If winget is already present, skips MSIX bootstrap.
  After setup, Run-DevInfra.cmd opens Show-DevInfraLog.ps1 in PowerShell (Notepad is often absent in Sandbox).
#>

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$lib = Join-Path $PSScriptRoot 'lib\Winget-Bootstrap.ps1'
if (-not (Test-Path -LiteralPath $lib)) {
    throw "Missing winget bootstrap library: $lib"
}
. $lib

Ensure-WsbWingetAvailable

Write-WsbStep 'Installing packages via winget (this can take several minutes)'
$ids = @(
  'Git.Git',
  'GitHub.cli',
  'OpenJS.NodeJS.LTS',
  'Python.Python.3.12',
  'astral-sh.ruff',
  'Casey.Just',
  'BiomeJS.Biome'
)

foreach ($id in $ids) {
  Write-Host "winget install $id"
  Invoke-WsbWingetExe @(
    'install', '-e', '--id', $id,
    '--source', 'winget',
    '--accept-source-agreements',
    '--accept-package-agreements',
    '--disable-interactivity'
  )
}

Sync-WsbPathFromRegistry

Write-WsbStep 'Verify versions'
$checks = @('git', 'gh', 'node', 'npm', 'python', 'ruff', 'just', 'biome')
foreach ($c in $checks) {
  if (Test-WsbCommandExists $c) {
    try {
      $verOut = & (Get-Command $c -ErrorAction Stop).Source @('--version') 2>&1
    } catch {
      $verOut = '(failed to read version)'
    }
    $firstLine = $verOut
    if ($verOut -is [System.Array]) {
      $firstLine = $verOut[0]
    }
    Write-Host ("OK  {0} -> {1}" -f $c, $firstLine)
  } else {
    Write-Warning "Missing on PATH: $c (open a new PowerShell window and try again)"
  }
}

Write-WsbStep 'Done'
Write-Host 'Tip: If a command is missing in this window, close it and open a new PowerShell window.'
