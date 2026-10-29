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
    # Re-read Machine+User PATH, then append well-known winget shim dirs that
    # exist on disk but are not yet in the registry in the SAME session.
    # Without this, uv (WinGet Links) and npm (nodejs + roaming npm) do not
    # resolve until a new window opens - which kills naked-pc start.bat chains.
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
    $extraPaths = @(
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps'),
        (Join-Path $env:APPDATA 'npm'),
        'C:\Program Files\nodejs',
        'C:\Program Files\Git\cmd',
        'C:\Program Files\Git\bin',
        'C:\Program Files\Python312',
        'C:\Program Files\Python312\Scripts',
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\Scripts'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Just'),
        'C:\Program Files\Just',
        (Join-Path $env:USERPROFILE '.cargo\bin')
    )
    foreach ($ep in $extraPaths) {
        if ((Test-Path -LiteralPath $ep) -and ($env:Path -notlike "*$ep*")) {
            $env:Path = "$ep;$($env:Path)"
        }
    }
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

function Repair-WsbWingetSource {
    # 0x8a15000f "Data required by the source is missing": the msstore/winget
    # source index failed to initialize (cold boot, CDN hiccup, stale cache).
    # The error message itself suggests 'source reset' - do that plus a fresh
    # update, then let the caller retry once. Harmless when the failure had
    # another cause (reset restores stock sources; update is idempotent).
    Write-Host 'Repairing winget sources (reset to defaults + update)...' -ForegroundColor Yellow
    try { Invoke-WsbWingetExe @('source', 'reset', '--force') 2>&1 | Out-Null } catch { }
    try { Invoke-WsbWingetExe @('source', 'update') 2>&1 | Out-Null } catch { }
}

function Install-WsbWingetViaMsix {
    Write-WsbStep 'Installing winget (Desktop App Installer)'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

    # Fast path: check local cache in C:\Assets\cache\winget
    $cacheDir = 'C:\Assets\cache\winget'
    $bundlePath = $null
    $depsDir = $null
    if (Test-Path -LiteralPath $cacheDir) {
        $cachedBundle = Get-ChildItem -Path $cacheDir -Filter 'Microsoft.DesktopAppInstaller_*.msixbundle' | Select-Object -First 1
        if ($cachedBundle) {
            $bundlePath = $cachedBundle.FullName
        }
        if (Test-Path -LiteralPath (Join-Path $cacheDir 'deps')) {
            $depsDir = Join-Path $cacheDir 'deps'
        }
    }

    if (-not $bundlePath -or -not $depsDir) {
        Write-WsbStep 'Fetching winget from GitHub release (cache miss)'
        $work = Join-Path $env:TEMP ('winget-bootstrap-' + [Guid]::NewGuid().ToString('N'))
        $null = New-Item -ItemType Directory -Path $work -Force

        $release = $null
        for ($retry = 1; $retry -le 3; $retry++) {
            try {
                $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' -UseBasicParsing -ErrorAction Stop
                break
            } catch {
                if ($retry -eq 3) { throw $_ }
                Write-Warning "GitHub release query failed (attempt $retry). Retrying in 3s..."
                Start-Sleep -Seconds 3
            }
        }

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
                break
            }
        }
    } else {
        Write-Host "Using cached winget packages from $cacheDir" -ForegroundColor Green
    }

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

    Write-WsbStep "Installing App Installer bundle: $(Split-Path $bundlePath -Leaf)"
    Add-AppxPackage -Path $bundlePath
    Write-Host "  Installed winget bundle successfully" -ForegroundColor Green

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
