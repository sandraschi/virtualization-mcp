# Shared winget bootstrap for Windows Sandbox bringup scripts.
# Dot-source from Setup-DevInfraSandbox.ps1 and Setup-ConsumerSandbox.ps1.

function Write-WsbStep {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Test-WsbCommandExists {
    param([string]$Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Sync-WsbPathFromRegistry {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Invoke-WsbWingetExe {
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

function Install-WsbWingetViaMsix {
    Write-WsbStep 'Installing winget (Desktop App Installer) from GitHub release'

    $work = Join-Path $env:TEMP ('winget-bootstrap-' + [Guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $work -Force

    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' -UseBasicParsing

    Write-WsbStep 'Downloading dependencies bundle'
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

    Write-WsbStep 'Installing dependencies (VCLibs, UI.Xaml, WindowsAppRuntime)'
    $depFiles = Get-ChildItem -Path $depsDir -Include '*.appx', '*.msix', '*.msixbundle' -Recurse | Sort-Object Name
    foreach ($dep in $depFiles) {
        try {
            Add-AppxPackage -Path $dep.FullName -ErrorAction Stop
            Write-Host "  OK: $($dep.Name)" -ForegroundColor Green
        } catch {
            Write-Host "  Skip: $($dep.Name) - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    Write-WsbStep 'Installing App Installer bundle'
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

    Sync-WsbPathFromRegistry
}

function Ensure-WsbWingetAvailable {
    Write-WsbStep 'Checking for existing winget'
    $haveWinget = $false
    try {
        $null = Invoke-WsbWingetExe @('--version')
        $haveWinget = $true
    } catch {
        $haveWinget = $false
    }

    if (-not $haveWinget) {
        Install-WsbWingetViaMsix
        $null = Invoke-WsbWingetExe @('--version')
    }

    $version = Invoke-WsbWingetExe @('--version')
    Write-Host "winget ready: $version" -ForegroundColor Green
}
