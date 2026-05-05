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

  $arch = $env:PROCESSOR_ARCHITECTURE
  if ($arch -eq 'ARM64') {
    $vcUri = 'https://aka.ms/Microsoft.VCLibs.arm64.14.00.Desktop.appx'
  } else {
    $vcUri = 'https://aka.ms/Microsoft.VCLibs.x64.14.00.Desktop.appx'
  }

  $work = Join-Path $env:TEMP ('winget-bootstrap-' + [Guid]::NewGuid().ToString('N'))
  $null = New-Item -ItemType Directory -Path $work -Force

  # 1) VC++ libs
  $vcPath = Join-Path $work 'Microsoft.VCLibs.Desktop.appx'
  Invoke-WebRequest -Uri $vcUri -OutFile $vcPath -UseBasicParsing
  Add-AppxPackage -Path $vcPath

  $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' -UseBasicParsing
  $bundleName = $null
  foreach ($a in $release.assets) {
    if ($a.name -like 'Microsoft.DesktopAppInstaller_*.msixbundle') {
      $bundleName = $a.name
      break
    }
  }

  if ([string]::IsNullOrWhiteSpace($bundleName)) {
    throw 'Could not find Microsoft.DesktopAppInstaller msixbundle in latest winget-cli release.'
  }

  # 2) UI.Xaml (dependency for AppInstaller)
  $xamlAsset = $null
  foreach ($a in $release.assets) {
    if ($a.name -notlike 'Microsoft.UI.Xaml*') { continue }
    if ($a.name -notlike '*.appx') { continue }
    if ($arch -eq 'ARM64') {
      if ($a.name -match '\.arm64\.appx$') { $xamlAsset = $a; break }
    } else {
      if ($a.name -match '\.x64\.appx$') { $xamlAsset = $a; break }
    }
  }
  if ($null -ne $xamlAsset) {
    $xamlPath = Join-Path $work $xamlAsset.name
    Invoke-WebRequest -Uri $xamlAsset.browser_download_url -OutFile $xamlPath -UseBasicParsing
    Add-AppxPackage -Path $xamlPath
  }

  # 3) WindowsAppRuntime (required for AppInstaller on fresh images)
  Write-Step 'Installing WindowsAppRuntime framework'
  $runtimeOk = $false
  $runtimeUrls = @(
    'https://aka.ms/windowsappsdk/1.8/latest/Microsoft.WindowsAppRuntime.1.8_x64__8wekyb3d8bbwe.msix'
    'https://aka.ms/windowsappsdk/1.7/latest/Microsoft.WindowsAppRuntime.1.7_x64__8wekyb3d8bbwe.msix'
  )
  foreach ($url in $runtimeUrls) {
    try {
      $rtPath = Join-Path $work 'WindowsAppRuntime.msix'
      Invoke-WebRequest -Uri $url -OutFile $rtPath -UseBasicParsing -ErrorAction Stop
      Add-AppxPackage -Path $rtPath -ErrorAction Stop
      Write-Host "Installed: $url" -ForegroundColor Green
      $runtimeOk = $true
      break
    } catch {
      Write-Host "Failed: $url - $($_.Exception.Message)" -ForegroundColor Yellow
    }
  }
  if (-not $runtimeOk) {
    throw 'Could not install WindowsAppRuntime. Winget install will fail.'
  }

  # 4) App Installer bundle
  foreach ($a in $release.assets) {
    if ($a.name -eq $bundleName) {
      $bundlePath = Join-Path $work $a.name
      Invoke-WebRequest -Uri $a.browser_download_url -OutFile $bundlePath -UseBasicParsing
      Add-AppxPackage -Path $bundlePath
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
