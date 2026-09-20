<#
.SYNOPSIS
  Automated naked-install test inside Windows Sandbox (fail-loud doctrine).

.DESCRIPTION
  Reads C:\Job\spec.json {repo_url, branch, observe_sec, health_url},
  installs the rig (git + just via winget - the test harness, like CI),
  clones the target, runs the just --list smoke gate, then launches the
  target start.bat under observation. Writes C:\Job\RESULT.json for the
  host to poll. Everything else (uv, node, npm, vite) MUST come from the
  target repo itself - that is what is under test.

  Per NAKED_PC_INSTALL_STANDARD 7b: just --list failure stops the run
  immediately. No improvising past a failed gate.

.NOTES
  Do not use global $ErrorActionPreference = 'Stop' (winget returns benign
  non-zero codes). Steps record their own exit codes into RESULT.json.
#>

$ProgressPreference = 'SilentlyContinue'
$JobDir = 'C:\Job'
$TestRoot = 'C:\Test'
$ResultPath = Join-Path $JobDir 'RESULT.json'

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== naked-test: $Message ===" -ForegroundColor Cyan
}

function Write-Result {
    param([array]$Steps, [bool]$Pass, [string]$FailedStep, [string]$Note)
    $tail = @()
    try {
        $logCandidates = @(
            "$JobDir\start-bat.log",
            "$JobDir\naked-test-launch.log",
            "$env:USERPROFILE\Desktop\naked-test-launch.log"
        )
        foreach ($cand in $logCandidates) {
            if (Test-Path -LiteralPath $cand) {
                $tail = @(Get-Content -LiteralPath $cand -Tail 50 | ForEach-Object { "$_" })
                break
            }
        }
    } catch { }
    $result = [ordered]@{
        finished_utc = (Get-Date).ToUniversalTime().ToString('o')
        repo         = $script:Spec.repo_url
        branch       = $script:Spec.branch
        pass         = $Pass
        failed_step  = $FailedStep
        note         = $Note
        steps        = $Steps
        log_tail     = $tail
    }
    $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ResultPath -Encoding UTF8
}

function Add-Step {
    param([System.Collections.ArrayList]$Steps, [string]$Name, [int]$Exit, [long]$Ms, [string]$Note = '')
    $null = $Steps.Add([ordered]@{ name = $Name; exit = $Exit; ms = $Ms; note = $Note })
    try {
        $prog = [ordered]@{
            repo        = $script:Spec.repo_url
            branch      = $script:Spec.branch
            last_step   = $Name
            steps       = $Steps
            updated_utc = (Get-Date).ToUniversalTime().ToString('o')
        }
        $prog | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $JobDir 'PROGRESS.json') -Encoding UTF8
    } catch { }
}

$steps = New-Object System.Collections.ArrayList

$specPath = Join-Path $JobDir 'spec.json'
$deadlineSpec = (Get-Date).AddSeconds(45)
while ((Get-Date) -lt $deadlineSpec -and -not (Test-Path -LiteralPath $specPath)) {
    Start-Sleep -Milliseconds 500
}

try {
    $script:Spec = Get-Content -LiteralPath $specPath -Raw | ConvertFrom-Json
} catch {
    Write-Host "ERROR: cannot read C:\Job\spec.json : $($_.Exception.Message)" -ForegroundColor Red
    Write-Result $steps $false 'spec' "Cannot read spec.json: $($_.Exception.Message)"
    exit 2
}
if ([string]::IsNullOrWhiteSpace($script:Spec.repo_url)) {
    Write-Host 'ERROR: spec.json has no repo_url' -ForegroundColor Red
    Write-Result $steps $false 'spec' 'spec.json has no repo_url'
    exit 2
}
$branch = if ($script:Spec.branch) { $script:Spec.branch } else { 'main' }
$observeSec = if ($script:Spec.observe_sec) { [int]$script:Spec.observe_sec } else { 90 }
$healthUrl = $script:Spec.health_url

$lib = 'C:\Assets\lib\Winget-Bootstrap.ps1'
if (-not (Test-Path -LiteralPath $lib)) { throw "Missing winget bootstrap library: $lib" }
. $lib

# ---- step 1: rig (git + just are harness, like CI) ----
Write-Step 'rig: winget -> git + just'
$sw = [System.Diagnostics.Stopwatch]::StartNew()
Ensure-WsbWingetAvailable
Sync-WsbPathFromRegistry
foreach ($pkg in @('Git.Git', 'Casey.Just')) {
    Write-Step "rig: installing $pkg via winget"
    try {
        Invoke-WsbWingetExe @('install', '--id', $pkg, '--source', 'winget', '--silent',
            '--accept-source-agreements', '--accept-package-agreements', '--disable-interactivity')
    } catch {
        Write-Warning "winget install $pkg error: $($_.Exception.Message)"
    }
}
Sync-WsbPathFromRegistry
$extraPaths = @(
    'C:\Program Files\Git\cmd',
    'C:\Program Files\Git\bin',
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links",
    "$env:LOCALAPPDATA\Programs\Just",
    'C:\Program Files\Just'
)
foreach ($ep in $extraPaths) {
    if ((Test-Path -LiteralPath $ep) -and ($env:Path -notlike "*$ep*")) {
        $env:Path = "$ep;$($env:Path)"
    }
}
$sw.Stop()
$rigOk = (Test-WsbCommandExists 'git') -and (Test-WsbCommandExists 'just')
Write-Host "Rig check: git=$(Test-WsbCommandExists 'git'), just=$(Test-WsbCommandExists 'just')" -ForegroundColor Cyan
$rigExit = if ($rigOk) { 0 } else { 1 }
Add-Step $steps 'rig' $rigExit $sw.ElapsedMilliseconds 'git + just via winget'
if (-not $rigOk) {
    Write-Result $steps $false 'rig' 'Harness installs failed - host/winget problem, not target repo.'
    exit 10
}

# ---- step 2: clone ----
$targetSource = if ($script:Spec.local_repo -and (Test-Path -LiteralPath $script:Spec.local_repo)) {
    $script:Spec.local_repo
} else {
    $script:Spec.repo_url
}
Write-Step "clone $targetSource [$branch]"
$sw.Restart()
if (-not (Test-Path -LiteralPath $TestRoot)) {
    $null = New-Item -ItemType Directory -Path $TestRoot -Force
}
$cloneName = ($script:Spec.repo_url -split '/')[-1] -replace '\.git$', ''
$cloneDir = Join-Path $TestRoot $cloneName

$cloneArgs = @('clone')
if ($targetSource -like 'http*') {
    $cloneArgs += @('--depth', '1')
}
$cloneArgs += @('--branch', $branch, $targetSource, $cloneDir)
& git @cloneArgs 2>&1 | Write-Host
$cloneExit = $LASTEXITCODE
if ($cloneExit -ne 0) {
    Write-Host "Branch '$branch' not found or clone failed. Retrying with default branch..." -ForegroundColor Yellow
    $fallbackArgs = @('clone')
    if ($targetSource -like 'http*') {
        $fallbackArgs += @('--depth', '1')
    }
    $fallbackArgs += @($targetSource, $cloneDir)
    & git @fallbackArgs 2>&1 | Write-Host
    $cloneExit = $LASTEXITCODE
}
$sw.Stop()
Add-Step $steps 'clone' $cloneExit $sw.ElapsedMilliseconds $cloneDir
if ($cloneExit -ne 0) {
    Write-Result $steps $false 'clone' 'git clone failed - URL/branch/network.'
    exit 11
}

# ---- step 3: just-list smoke gate (fail-loud, no improvising past this) ----
Write-Step 'smoke gate: just --list'
$sw.Restart()
Push-Location $cloneDir
& just --list 2>&1 | Write-Host
$listExit = $LASTEXITCODE
Pop-Location
$sw.Stop()
Add-Step $steps 'just-list' $listExit $sw.ElapsedMilliseconds 'NAKED_PC_INSTALL_STANDARD 7/7b'
if ($listExit -ne 0) {
    Write-Result $steps $false 'just-list' 'Smoke gate failed - file the issue, do not improvise.'
    exit 12
}

# ---- step 4: launch start.bat under observation ----
$startBat = Join-Path $cloneDir 'start.bat'
if (-not (Test-Path -LiteralPath $startBat)) {
    Add-Step $steps 'start' 1 0 'no start.bat at repo root'
    Write-Result $steps $false 'start' 'Target has no start.bat - nothing to launch.'
    exit 13
}
Write-Step "observe start.bat for ${observeSec}s"
$startLog = Join-Path $JobDir 'start-bat.log'
$sw.Restart()
# Headless launch: pass only switches the target's start.ps1 actually
# declares (fleet template has -NoBrowser/-Headless; minimal scripts may
# have neither - unrecognized switches would fail the run). Prefer
# -NoBrowser: it suppresses the dashboard popup while keeping stdio
# attached so start-bat.log stays informative. -Headless only as
# fallback - several launchers relaunch hidden on -Headless, which
# detaches stdout into the void.
$startFlags = @()
try {
    $startPs1 = Join-Path $cloneDir 'start.ps1'
    if (Test-Path -LiteralPath $startPs1) {
        $startPs1Text = Get-Content -LiteralPath $startPs1 -Raw
        if ($startPs1Text -match '\$NoBrowser') { $startFlags += '-NoBrowser' }
        elseif ($startPs1Text -match '\$Headless') { $startFlags += '-Headless' }
    }
} catch { }
$flagStr = ($startFlags -join ' ').Trim()
if ($flagStr) { Write-Host "start flags: $flagStr" -ForegroundColor DarkGray }
$proc = Start-Process -FilePath 'cmd.exe' -ArgumentList "/c `"`"$startBat`" $flagStr >> `"$startLog`" 2>&1`"" `
    -WorkingDirectory $cloneDir -PassThru -WindowStyle Minimized
$deadline = (Get-Date).AddSeconds($observeSec)
$healthOk = $false
while ((Get-Date) -lt $deadline) {
    if ($healthUrl) {
        try {
            $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
            if ([int]$r.StatusCode -eq 200) { $healthOk = $true; break }
        } catch { }
    } else {
        if ($proc.HasExited) { break }
    }
    Start-Sleep -Seconds 3
}
$sw.Stop()
if ($healthUrl) {
    if ($healthOk) {
        Add-Step $steps 'start' 0 $sw.ElapsedMilliseconds "health 200 at $healthUrl"
        # Show the webapp: Edge by executable path. A bare Start-Process URL
        # pops the http-association dialog on fresh sandboxes instead.
        try {
            $frontUrl = $script:Spec.frontend_url
            $edgeExe = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
            if ($frontUrl -and (Test-Path -LiteralPath $edgeExe)) {
                Write-Host "Opening webapp at $frontUrl ..." -ForegroundColor Green
                Start-Process -FilePath $edgeExe -ArgumentList $frontUrl
            }
        } catch { }
        Write-Result $steps $true '' "Servers healthy within ${observeSec}s window."
        exit 0
    } else {
        Add-Step $steps 'start' 1 $sw.ElapsedMilliseconds "health check failed at $healthUrl"
        Write-Result $steps $false 'start' "Health check did not return 200 within ${observeSec}s window."
        exit 14
    }
}
if ($proc.HasExited -and $proc.ExitCode -eq 0) {
    Add-Step $steps 'start' 0 $sw.ElapsedMilliseconds 'start.bat exited 0 (script-style repo)'
    Write-Result $steps $true '' 'start.bat completed cleanly.'
    exit 0
}
if ($proc.HasExited) {
    Add-Step $steps 'start' $proc.ExitCode $sw.ElapsedMilliseconds 'start.bat exited nonzero'
    Write-Result $steps $false 'start' "start.bat died fast (exit $($proc.ExitCode)) - see log tail."
    exit 14
}
Add-Step $steps 'start' 0 $sw.ElapsedMilliseconds "alive at +${observeSec}s, no health_url given"
Write-Result $steps $true '' "Process alive at end of window. Sandbox is ephemeral - closing ends it."
exit 0
