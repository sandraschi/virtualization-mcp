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

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Test-CommandExists {
  param([string]$Name)
  $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-WingetExe {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Arguments
  )
  $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
  if ($null -ne $wingetCmd) {
    & $wingetCmd.Source @Arguments
    return
  }
  $candidate = Join-Path $env:LocalAppData 'Microsoft\WindowsApps\winget.exe'
  if (Test-Path -LiteralPath $candidate) {
    & $candidate @Arguments
    return
  }
  throw 'winget executable not found on PATH or in WindowsApps after install.'
}

function Sync-PathFromRegistry {
  $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $user = [Environment]::GetEnvironmentVariable('Path', 'User')
  $env:Path = "$machine;$user"
}

function Install-WingetViaMsix {
  Write-Step 'Installing winget (Desktop App Installer) from GitHub release'

  $work = Join-Path $env:TEMP ('winget-bootstrap-' + [Guid]::NewGuid().ToString('N'))
  $null = New-Item -ItemType Directory -Path $work -Force

  $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' -UseBasicParsing

  # 1) Download all dependencies zip (contains VCLibs, UI.Xaml, WindowsAppRuntime, etc.)
  Write-Step 'Downloading dependencies bundle'
  $depsAsset = $null
  foreach ($a in $release.assets) {
    if ($a.name -eq 'DesktopAppInstaller_Dependencies.zip') { $depsAsset = $a; break }
  }
  if ($null -eq $depsAsset) { throw 'Could not find DesktopAppInstaller_Dependencies.zip in release.' }
  $depsPath = Join-Path $work $depsAsset.name
  Invoke-WebRequest -Uri $depsAsset.browser_download_url -OutFile $depsPath -UseBasicParsing
  $depsDir = Join-Path $work 'deps'
  Expand-Archive -Path $depsPath -DestinationPath $depsDir -Force
  Write-Host "Extracted $($depsAsset.name)" -ForegroundColor Green

  # 2) Install all dependencies (VCLibs, UI.Xaml, WindowsAppRuntime)
  Write-Step 'Installing dependencies (VCLibs, UI.Xaml, WindowsAppRuntime)'
  # Install dependency MSIX files (frameworks). The deps zip contains
  # .msix and .msixbundle files that provide the required frameworks.
  $depFiles = Get-ChildItem -Path $depsDir -Include '*.msix','*.msixbundle' -Recurse | Sort-Object Name
  foreach ($dep in $depFiles) {
    try {
      Add-AppxPackage -Path $dep.FullName -ErrorAction Stop
      Write-Host "  OK: $($dep.Name)" -ForegroundColor Green
    } catch {
      Write-Host "  Skip: $($dep.Name) - $($_.Exception.Message)" -ForegroundColor Yellow
    }
  }

  # 3) Find and install the App Installer bundle
  Write-Step 'Installing App Installer bundle'
  $bundleName = $null
  foreach ($a in $release.assets) {
    if ($a.name -like 'Microsoft.DesktopAppInstaller_*.msixbundle') { $bundleName = $a.name; break }
  }
  if ([string]::IsNullOrWhiteSpace($bundleName)) {
    throw 'Could not find Microsoft.DesktopAppInstaller msixbundle in release.'
  }
  foreach ($a in $release.assets) {
    if ($a.name -eq $bundleName) {
      $bundlePath = Join-Path $work $a.name
      Invoke-WebRequest -Uri $a.browser_download_url -OutFile $bundlePath -UseBasicParsing
      Add-AppxPackage -Path $bundlePath
      Write-Host "  Installed: $(Split-Path $a.name -Leaf)" -ForegroundColor Green
      break
    }
  }

  Sync-PathFromRegistry
}

Write-Step 'Checking for existing winget'
$haveWinget = $false
try {
  $null = Invoke-WingetExe @('--version')
  $haveWinget = $true
} catch {
  $haveWinget = $false
}

if (-not $haveWinget) {
  Install-WingetViaMsix
  $null = Invoke-WingetExe @('--version')
}

Write-Step 'Installing packages via winget (this can take several minutes)'
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
  Invoke-WingetExe @(
    'install',
    '-e',
    '--id',
    $id,
    '--accept-source-agreements',
    '--accept-package-agreements',
    '--disable-interactivity'
  )
}

Sync-PathFromRegistry

Write-Step 'Verify versions (new shells will see the same PATH)'
$checks = @('git', 'gh', 'node', 'npm', 'python', 'ruff', 'just', 'biome')
foreach ($c in $checks) {
  if (Test-CommandExists $c) {
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

Write-Step 'Done'
Write-Host 'Tip: If a command is missing in this window, close it and open a new PowerShell window.'
