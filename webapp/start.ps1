$ErrorActionPreference = "Stop"

# Configuration
$FRONTEND_PORT = 10760
$BACKEND_PORT = 10761
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$SrcPath = Join-Path $ProjectRoot "src"

Write-Host "Starting Virtualization MCP Webapp (Dual Interface)..." -ForegroundColor Cyan

# 1. Start Backend (FastAPI Proxy)
Write-Host "Starting Backend on port $BACKEND_PORT..." -ForegroundColor Yellow
$backendDir = Join-Path $PSScriptRoot "backend"
if (-not (Test-Path $backendDir)) {
    Write-Error "Backend directory not found: $backendDir"
}

$env:PYTHONPATH = "$SrcPath"
$backendCmd = "Set-Location '$backendDir'; `$env:PYTHONPATH='$SrcPath'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT"
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru
Write-Host "Backend started (PID: $($backendProcess.Id))" -ForegroundColor Green

# 2. Wait for Backend to initialize
Start-Sleep -Seconds 3

# 3. Start Frontend (Vite)
Write-Host "Starting Frontend on port $FRONTEND_PORT..." -ForegroundColor Yellow
$frontendDir = Join-Path $PSScriptRoot "frontend"
if (Test-Path "$frontendDir\package.json") {
    $frontendCmd = "Set-Location '$frontendDir'; `$env:VITE_API_URL='http://localhost:$BACKEND_PORT'; npm run dev -- --port $FRONTEND_PORT"
    $frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru
    Write-Host "Frontend started (PID: $($frontendProcess.Id))" -ForegroundColor Green
}
else {
    Write-Error "package.json not found in $frontendDir - Did you scaffold the frontend?"
}

# 4. Cleanup Instructions
Write-Host "Close the opened PowerShell windows to stop the servers." -ForegroundColor Red
