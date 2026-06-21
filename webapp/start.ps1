param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$ReuseIfRunning)

$WebPort = 10700
$BackendPort = 10701
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly

$portResolve = @{
    Ports      = @($WebPort, $BackendPort)
    Label      = "virtualization-mcp"
    AllowReuse = $ReuseIfRunning
}
if ($ReuseIfRunning) {
    $portResolve.HealthChecks = @{
        $WebPort = "http://127.0.0.1:$WebPort/"
        $BackendPort = "http://127.0.0.1:$BackendPort/api/v1/health"
    }
}
$portState = Resolve-FleetPortConflict @portResolve
if ($portState.Action -eq 'Blocked') { exit 1 }
if ($portState.Reuse) { return }

# 2. Setup
Set-Location $PSScriptRoot
if (Test-Path "frontend") { Set-Location "frontend" }
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start the Python backend (Background)
Write-Host "Starting Python backend on port $BackendPort ..." -ForegroundColor Cyan

# uv --project finds package; CWD stays webapp (no repo-root run).
$backendCmd = "Set-Location '$PSScriptRoot'; uv run --project '$ProjectRoot' uvicorn virtualization_mcp.web.app:app --host 127.0.0.1 --port $BackendPort --log-level info"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 4. Wait for backend to be listening (avoid ECONNREFUSED when frontend loads)
$healthUrl = "http://127.0.0.1:$BackendPort/api/v1/health"
$maxAttempts = 15
$attempt = 0
Write-Host "Waiting for backend at $healthUrl ..." -ForegroundColor Cyan
while ($attempt -lt $maxAttempts) {
    try {
        $null = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "Backend is up." -ForegroundColor Green
        break
    } catch {
        $attempt++
        if ($attempt -ge $maxAttempts) {
            Write-Host "Backend did not respond after ${maxAttempts} attempts. Starting frontend anyway." -ForegroundColor Yellow
            break
        }
        Start-Sleep -Seconds 2
    }
}

if (-not $FleetStart.RunFrontend) { return }

# 5. Run server (Vite dev)
if (-not $FleetStart.RunFrontend) { return }

Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green
if (Test-Path "frontend") { Set-Location "frontend" }

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
if (-not $FleetStart.RunFrontend) { return }
npm run dev -- --port $WebPort --host







