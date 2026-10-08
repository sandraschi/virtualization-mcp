# FleetStartMode.ps1 - vendored per-repo copy (no mcp-central-docs required at runtime)
# Canonical upstream: mcp-central-docs/scripts/FleetStartMode.ps1 (private fleet docs)

# FleetStartMode.ps1 - shared launch modes for webapp/start.ps1 launchers
# Canonical upstream: mcp-central-docs/scripts/FleetStartMode.ps1
# Port clearing uses port-scoped netstat+findstr; Session 0 checks protect Windows services.

function Get-FleetStartModeBoundParameters {
    param([hashtable]$BoundParameters)

    $filtered = @{}
    foreach ($key in @('Headless', 'BackendOnly', 'FrontendOnly', 'NoBrowser', 'SkipRestart')) {
        if ($BoundParameters.ContainsKey($key)) {
            $filtered[$key] = $BoundParameters[$key]
        }
    }
    return $filtered
}

function Initialize-FleetStartMode {
    param(
        [switch]$Headless,
        [switch]$BackendOnly,
        [switch]$FrontendOnly,
        [switch]$NoBrowser
    )

    if ($FrontendOnly -and $BackendOnly) {
        Write-Error "Cannot combine -FrontendOnly and -BackendOnly."
        exit 1
    }

    $runBackend = -not $FrontendOnly
    $probeRun = ($env:FLEET_PROBE_RUN -eq '1')
    $runFrontend = (-not $BackendOnly) -and ($FrontendOnly -or (-not $Headless) -or $probeRun)
    $skipBrowser = $NoBrowser -or $Headless -or $BackendOnly

    return [pscustomobject]@{
        RunBackend  = $runBackend
        RunFrontend = $runFrontend
        SkipBrowser = $skipBrowser
        WindowStyle = if ($Headless) { "Hidden" } else { "Normal" }
    }
}

function Enter-FleetHeadlessConsole {
    param(
        [switch]$Headless,
        [switch]$BackendOnly,
        [switch]$FrontendOnly,
        [string]$StartScriptPath = ''
    )

    if ($env:FLEET_PROBE_RUN -eq '1') { return }
    if (-not $Headless) { return }

    if ($env:FLEET_HEADLESS_REENTERED -eq '1') { return }
    $env:FLEET_HEADLESS_REENTERED = '1'

    $scriptPath = $StartScriptPath
    if (-not $scriptPath -or -not (Test-Path -LiteralPath $scriptPath)) {
        Write-Host "ERROR: Headless launcher script not found: $scriptPath" -ForegroundColor Red
        exit 1
    }

    $spawnArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $scriptPath,
        '-Headless'
    )
    if ($FrontendOnly) {
        $spawnArgs += '-FrontendOnly'
    } elseif ($BackendOnly) {
        $spawnArgs += '-BackendOnly'
    }
    Start-Process powershell.exe -ArgumentList $spawnArgs -WindowStyle Hidden
    exit
}

function Get-FleetPortListenerPids {
    param([Parameter(Mandatory)][int]$Port)

    $pids = [System.Collections.Generic.HashSet[int]]::new()
    $portNeedle = ":$Port "
    $raw = cmd /c "netstat -ano -p TCP 2>nul | findstr LISTENING | findstr `"$portNeedle`""
    if (-not $raw) { return @() }

    $lines = if ($raw -is [System.Array]) { @($raw) } else { @($raw -split "`r?`n") }
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = ($line.Trim() -split '\s+')
        if ($parts.Count -lt 5) { continue }
        $localAddr = $parts[1]
        if ($localAddr -notmatch ':(\d+)$') { continue }
        if ([int]$Matches[1] -ne $Port) { continue }
        $procId = 0
        if ([int]::TryParse($parts[-1], [ref]$procId) -and $procId -gt 4) {
            [void]$pids.Add($procId)
        }
    }
    return @($pids)
}

$script:FleetProtectedPidResults = @{}

function Clear-FleetProtectedServicePidCache {
    $script:FleetProtectedPidResults = @{}
}

function Test-FleetProcessProtectedByService {
    param([Parameter(Mandatory)][int]$ProcessId)

    if ($ProcessId -le 4) { return $false }
    if ($script:FleetProtectedPidResults.ContainsKey($ProcessId)) {
        return [bool]$script:FleetProtectedPidResults[$ProcessId]
    }

    # On Windows, all Windows Services (and their spawned children) execute in Session 0.
    # Standard user dev processes execute in interactive Session > 0.
    $isService = $false
    try {
        $proc = Get-Process -Id $ProcessId -ErrorAction Stop
        $isService = ($proc.SessionId -eq 0)
    } catch {
        $isService = $false
    }

    $script:FleetProtectedPidResults[$ProcessId] = $isService
    return $isService
}

function Test-FleetPortHeldByService {
    param([Parameter(Mandatory)][int]$Port)

    foreach ($procId in @(Get-FleetPortListenerPids -Port $Port)) {
        if (Test-FleetProcessProtectedByService -ProcessId $procId) {
            return $true
        }
    }
    return $false
}

function Get-FleetPortsStillListening {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [switch]$ExcludeProtectedServiceProcesses
    )

    $still = @{}
    foreach ($port in @($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)) {
        $pids = @(Get-FleetPortListenerPids -Port $port)
        if ($ExcludeProtectedServiceProcesses) {
            $pids = @($pids | Where-Object { -not (Test-FleetProcessProtectedByService -ProcessId $_) })
        }
        if ($pids.Count -gt 0) {
            $still[$port] = $pids
        }
    }
    return $still
}

function Get-FleetProcessBrief {
    param([Parameter(Mandatory)][int]$ProcessId)

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) { return $null }

    return [pscustomobject]@{
        Id        = $ProcessId
        Name      = $proc.ProcessName
        SessionId = $proc.SessionId
        ParentId  = 0
    }
}

function Test-FleetHttpOk {
    param(
        [Parameter(Mandatory)][string]$Url,
        [int]$TimeoutSec = 3
    )

    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500)
    } catch {
        return $false
    }
}

function Stop-FleetProcessId {
    param(
        [Parameter(Mandatory)][int]$ProcessId,
        [switch]$Elevated
    )

    if ($ProcessId -le 4 -or $ProcessId -eq $PID) {
        return [pscustomobject]@{ Ok = $true; Skipped = $true }
    }

    $before = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $before) {
        return [pscustomobject]@{ Ok = $true; Gone = $true }
    }

    # Session 0 holds real Windows services AND orphaned dev remnants.
    # Direct kills stay forbidden; orphans go through one UAC prompt.
    if ($before.SessionId -eq 0) {
        if ($Elevated -and (Test-FleetProcessOrphanKillable -ProcessId $ProcessId)) {
            $ok = Invoke-FleetElevatedTaskkill -ProcessIds @($ProcessId) -Label 'fleet'
            return [pscustomobject]@{ Ok = $ok; Name = $before.ProcessName; SessionId = 0; Elevated = $true }
        }
        return [pscustomobject]@{ Ok = $false; Name = $before.ProcessName; SessionId = 0; Error = 'Windows Service process (Session 0)' }
    }

    # Terminate process tree directly using taskkill /F /T
    $null = Start-Process -FilePath "taskkill.exe" -ArgumentList @("/F", "/T", "/PID", "$ProcessId") `
        -Wait -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue

    Start-Sleep -Milliseconds 80
    $after = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($after) {
        try { Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue } catch { }
        Start-Sleep -Milliseconds 50
        $after = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    }

    return [pscustomobject]@{ Ok = ($null -eq $after) }
}

function Test-FleetProcessOrphanKillable {
    param([Parameter(Mandatory)][int]$ProcessId)

    # $true ONLY for session-0 processes with no Windows service behind them
    # whose image is a known dev runtime. Everything else stays untouchable.
    #
    # Two negative proofs are required because NSSM runs the REAL backend as
    # a CHILD of nssm.exe: Win32_Service maps only nssm.exe itself, so a
    # direct PID check calls every service worker an orphan (2026-10-08:
    # nearly killed arxiv-mcp's live worker). Hence the ancestor walk.
    if ($ProcessId -le 4 -or $ProcessId -eq $PID) { return $false }
    $chain = @($ProcessId)
    try {
        $id = $ProcessId
        for ($i = 0; $i -lt 6 -and $id -gt 4; $i++) {
            $w = Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction Stop
            $id = $w.ParentProcessId
            if ($id -and $id -gt 4 -and $id -ne $PID) { $chain += $id }
        }
    } catch { }
    try {
        foreach ($cid in $chain) {
            $svc = Get-CimInstance Win32_Service -Filter "ProcessId=$cid" -ErrorAction Stop
            if ($svc) { return $false }
            $img = (Get-CimInstance Win32_Process -Filter "ProcessId=$cid" -ErrorAction SilentlyContinue).Name
            if ($img -ieq 'nssm.exe') { return $false }
        }
    } catch { }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc -or $proc.SessionId -ne 0) { return $false }
    $name = $proc.ProcessName.ToLower()
    if ($name -in @('python', 'pythonw', 'uv', 'node', 'bun', 'bunx', 'npm', 'vite', 'tsc')) { return $true }
    if ($name -like '*-mcp') { return $true }  # frozen fleet backends (git-github-mcp.exe)
    return $false
}

function Get-FleetOrphanTree {
    param([Parameter(Mandatory)][int[]]$ProcessIds)

    # Walk UP from port holders to orphan-killable ancestors (uv -> frozen
    # exe -> workers), so one UAC prompt clears the whole orphan tree.
    # Stops at system PIDs, the current shell, non-session-0, or depth 5.
    $all = @(); $seen = @{}; $queue = @($ProcessIds); $depth = 0
    while ($queue.Count -gt 0 -and $depth -lt 5) {
        $depth++; $next = @()
        foreach ($id in $queue) {
            if ($id -le 4 -or $id -eq $PID -or $seen.ContainsKey($id)) { continue }
            $seen[$id] = $true
            if (-not (Test-FleetProcessOrphanKillable -ProcessId $id)) { continue }
            $all += $id
            try {
                $par = (Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction Stop).ParentProcessId
                if ($par -and $par -gt 4 -and $par -ne $PID) { $next += $par }
            } catch { }
        }
        $queue = $next
    }
    return @($all | Sort-Object -Unique)
}

function Invoke-FleetElevatedTaskkill {
    param(
        [Parameter(Mandatory)][int[]]$ProcessIds,
        [string]$Label = "fleet"
    )

    # One UAC prompt for the whole set. Denial (exit 1223) is a refusal,
    # not a hang - report it and let the caller decide.
    $targets = @($ProcessIds | Where-Object { $_ -gt 4 } | Sort-Object -Unique)
    if ($targets.Count -eq 0) { return $false }
    $taskArgs = @('/F', '/T') + @($targets | ForEach-Object { @('/PID', "$_") })
    Write-Host "[$Label] requesting elevation (UAC) to stop session-0 orphan(s): $($targets -join ', ') ..." -ForegroundColor Cyan
    try {
        $p = Start-Process -FilePath "taskkill.exe" -ArgumentList $taskArgs `
            -Verb RunAs -Wait -PassThru -WindowStyle Hidden -ErrorAction Stop
    } catch {
        Write-Host "[$Label] elevation refused or failed - orphan(s) still holding the port." -ForegroundColor Yellow
        return $false
    }
    Start-Sleep -Milliseconds 800
    $remaining = @($targets | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue })
    if ($remaining.Count -eq 0) {
        Write-Host "[$Label] orphan(s) cleared." -ForegroundColor Green
        return $true
    }
    Write-Host "[$Label] still holding port after elevated kill: $($remaining -join ', ')" -ForegroundColor Red
    return $false
}

function Stop-FleetPortSquatters {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet",
        [switch]$ElevatedFallback
    )

    $uniquePorts = @($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)
    if ($uniquePorts.Count -eq 0) { return }

    $killedAny = $false
    foreach ($port in $uniquePorts) {
        $pids = @(Get-FleetPortListenerPids -Port $port)
        foreach ($procId in $pids) {
            if (Test-FleetProcessProtectedByService -ProcessId $procId) {
                $brief = Get-FleetProcessBrief -ProcessId $procId
                $name = if ($brief) { $brief.Name } else { 'process' }
                Write-Host "[$Label] skip PID $procId ($name) on port $port - Windows/NSSM service" -ForegroundColor DarkCyan
                continue
            }
            Write-Host "[$Label] Stopping stale PID $procId on port $port ..." -ForegroundColor DarkGray
            $res = Stop-FleetProcessId -ProcessId $procId
            if ($res.Ok) { $killedAny = $true }
        }
    }
    if ($ElevatedFallback) {
        # Holders can churn between enumeration and kill (supervisor loops,
        # reload workers). Retry enumeration; attempt elevation at most once
        # (a refused UAC prompt must not re-prompt in a loop). No silent
        # path: every outcome logs.
        for ($round = 1; $round -le 3; $round++) {
            $holders = @()
            foreach ($port in $uniquePorts) { $holders += @(Get-FleetPortListenerPids -Port $port) }
            $killable = @($holders | Sort-Object -Unique | Where-Object { Test-FleetProcessOrphanKillable -ProcessId $_ })
            if ($killable.Count -eq 0) {
                if ($holders.Count -gt 0) {
                    Write-Host "[$Label] port holder(s) present but not orphan-killable - leaving alone." -ForegroundColor DarkGray
                }
                break
            }
            $tree = @(Get-FleetOrphanTree -ProcessIds $killable)
            if ($tree.Count -eq 0) {
                Write-Host "[$Label] holders churned before kill (round $round) - re-enumerating ..." -ForegroundColor DarkGray
                Start-Sleep -Milliseconds 500
                continue
            }
            if (Invoke-FleetElevatedTaskkill -ProcessIds $tree -Label $Label) { $killedAny = $true }
            break
        }
    }
    if ($killedAny) {
        Start-Sleep -Milliseconds 150
    }
}

function Stop-FleetPortListeners {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet"
    )

    Stop-FleetPortSquatters -Ports $Ports -Label $Label
    $still = Get-FleetPortsStillListening -Ports $Ports
    if ($still.Count -eq 0) {
        Write-Host "[$Label] Ports clear: $($Ports -join ', ')" -ForegroundColor Green
        return $true
    }

    $details = @()
    foreach ($entry in $still.GetEnumerator()) {
        foreach ($procId in $entry.Value) {
            $brief = Get-FleetProcessBrief -ProcessId $procId
            $name = if ($brief) { $brief.Name } else { 'process' }
            $svcNote = if (Test-FleetProcessProtectedByService -ProcessId $procId) { ' (Windows service)' } else { '' }
            $details += "port $($entry.Key) $name PID $procId$svcNote"
        }
    }
    Write-Host "[$Label] Ports still active: $($details -join '; ')" -ForegroundColor Yellow
    return ($still.Count -eq 0)
}

# LEGACY SHIM (kept for 5 pre-convergence start.ps1 callers: blender, yahboom,
# worldlabs, notebooklm-fleet, podman). New launchers must use the unified
# convergence engine in Invoke-FleetWebappStart.ps1 (Start-FleetWebapp) instead:
# per-component health-check-then-reuse, never a whole-stack verdict.
# This shim NEVER returns ReuseHealthy for a port it did not health-verify
# (unverified service-held ports report ReuseUnverified + Reuse=$false).
function Resolve-FleetPortConflict {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet",
        [hashtable]$HealthChecks = @{},
        [switch]$AllowReuse,
        [switch]$ForceRestart
    )

    # 1. Clear killable non-service listeners
    Stop-FleetPortSquatters -Ports $Ports -Label $Label

    # 2. Inspect remaining listeners
    $stillAll = Get-FleetPortsStillListening -Ports $Ports
    $stillDev = Get-FleetPortsStillListening -Ports $Ports -ExcludeProtectedServiceProcesses

    if ($stillAll.Count -eq 0) {
        return [pscustomobject]@{ Action = 'Cleared'; Reuse = $false }
    }

    # If dev processes still occupy the ports after kill attempt, report blocked
    if ($stillDev.Count -gt 0) {
        $blockers = @()
        foreach ($entry in $stillDev.GetEnumerator()) {
            foreach ($pidVal in $entry.Value) {
                $blockers += "port $($entry.Key) PID $pidVal"
            }
        }
        Write-Host "[$Label] ERROR: ports still held: $($blockers -join '; ')" -ForegroundColor Red
        return [pscustomobject]@{ Action = 'Blocked'; Reuse = $false }
    }

    # All remaining listeners are Windows Services (Session 0).
    # A port counts as verified ONLY if it has a HealthChecks entry that passes.
    # Listening without verification is NOT reuse - it is an unverified squat.
    $allVerified = $true
    $allListening = $true
    foreach ($p in $Ports) {
        if ($p -le 0) { continue }
        $pInt = [int]$p
        if (-not $stillAll.ContainsKey($pInt)) {
            $allListening = $false
            continue
        }
        if ($HealthChecks.ContainsKey($pInt)) {
            if (-not (Test-FleetHttpOk -Url $HealthChecks[$pInt])) {
                Write-Host "[$Label] ERROR: port $pInt held by Windows service but health check failed." -ForegroundColor Red
                Write-Host "Restart the service (services.msc / nssm restart $Label)." -ForegroundColor Yellow
                return [pscustomobject]@{ Action = 'Blocked'; Reuse = $false }
            }
        } else {
            $allVerified = $false
        }
    }

    # If ALL configured ports are listening AND every one passed a health check,
    # the entire stack is reusable. Otherwise NEVER claim ReuseHealthy.
    if ($allListening -and $allVerified) {
        Write-Host "[$Label] All ports active and health-verified - reusing existing stack." -ForegroundColor Green
        return [pscustomobject]@{ Action = 'ReuseHealthy'; Reuse = $true }
    }

    if ($allListening -and -not $allVerified) {
        $unverified = @($Ports | Where-Object { $_ -gt 0 -and $stillAll.ContainsKey([int]$_) -and -not $HealthChecks.ContainsKey([int]$_) })
        Write-Host "[$Label] Port(s) $($unverified -join ', ') held by a Windows service WITHOUT a passing health check - refusing blind reuse." -ForegroundColor Yellow
        Write-Host "[$Label] Remedy: re-run with health checks, or migrate this launcher to Start-FleetWebapp (per-component convergence)." -ForegroundColor Yellow
        return [pscustomobject]@{ Action = 'ReuseUnverified'; Reuse = $false }
    }

    # Partial service (e.g. backend service healthy, frontend free to start)
    Write-Host "[$Label] Service port(s) healthy; remaining port(s) free to start." -ForegroundColor Green
    return [pscustomobject]@{ Action = 'Cleared'; Reuse = $false }
}

function Assert-FleetPortsAvailable {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet",
        [hashtable]$HealthChecks = @{},
        [switch]$AllowReuse,
        [switch]$ForceRestart
    )

    $resolved = Resolve-FleetPortConflict -Ports $Ports -Label $Label -HealthChecks $HealthChecks `
        -AllowReuse:$AllowReuse -ForceRestart:$ForceRestart
    return ($resolved.Action -ne 'Blocked')
}

function Start-FleetDetachedShell {
    param(
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][string]$Exe,
        [Parameter(Mandatory)][string[]]$Args,
        [string]$WorkingDirectory = "",
        [string]$WindowStyle = "Normal"
    )

    $probeRun = ($env:FLEET_PROBE_RUN -eq '1')
    if ($probeRun) {
        $logDir = if ($env:FLEET_PROBE_LOG_DIR) { $env:FLEET_PROBE_LOG_DIR } else { $env:TEMP }
        if (-not (Test-Path -LiteralPath $logDir)) {
            New-Item -ItemType Directory -Force -Path $logDir | Out-Null
        }
        $outLog = Join-Path $logDir "$Label.stdout.log"
        $errLog = Join-Path $logDir "$Label.stderr.log"
        $psi = @{
            FilePath               = $Exe
            ArgumentList           = $Args
            PassThru               = $true
            NoNewWindow            = $true
            RedirectStandardOutput = $outLog
            RedirectStandardError  = $errLog
        }
        if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
        return Start-Process @psi
    }

    # R8: title detached consoles from -Label so taskbar / taskkill can
    # identify backend vs frontend without remembering ports. Probe runs
    # use NoNewWindow + redirect, title is irrelevant there (early return).
    $titledArgs = @($Args)
    $cmdIdx = [Array]::IndexOf($titledArgs, '-Command')
    if ($cmdIdx -ge 0 -and ($cmdIdx + 1) -lt $titledArgs.Count) {
        $safe = ($Label -replace "'", "''")
        $titledArgs[$cmdIdx + 1] = "`$Host.UI.RawUI.WindowTitle='$safe'; " + $titledArgs[$cmdIdx + 1]
    }

    $normal = @{
        FilePath     = $Exe
        ArgumentList = $titledArgs
        PassThru     = $true
        WindowStyle  = $WindowStyle
    }
    if ($WorkingDirectory) { $normal.WorkingDirectory = $WorkingDirectory }
    return Start-Process @normal
}
