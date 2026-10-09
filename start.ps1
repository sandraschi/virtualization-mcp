param([switch]$Headless)

# --- SOTA Headless Standard ---
# Skip the hidden relaunch when stdout is redirected (sandbox harness /
# log capture): detaching would send all output into the void.
$redirected = $false
try { $redirected = [Console]::IsOutputRedirected } catch { }
if ($Headless -and -not $redirected -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process powershell -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

$env:FASTMCP_LOG_LEVEL = 'WARNING'

# NAKED_PC_INSTALL_STANDARD sec. 1: prereq guard via winget.
# uv covers Python implicitly (auto-fetched); never bare-call it.
function Require-Command {
    param([string]$Cmd, [string]$WingetId, [string]$Label)
    if (Get-Command $Cmd -ErrorAction SilentlyContinue) { return }
    Write-Host "  $Label not found - installing via winget ..." -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: winget unavailable. Install $Label manually ($WingetId)." -ForegroundColor Red
        exit 1
    }
    winget install --id $WingetId --source winget --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("PATH","User")
    if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) {
        Write-Host "Installed $Label but '$Cmd' still not in PATH. Reopen PowerShell and retry." -ForegroundColor Yellow
        exit 1
    }
}
Require-Command "uv" "astral-sh.uv" "uv (Python package manager)"
$uvExe = (Get-Command uv).Source

# Clear fleet ports (10700 frontend, 10701 backend, 10702 MCP HTTP) before binding
@(10700, 10701, 10702) | ForEach-Object {
    Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Write-Host 'Starting virtualization-mcp...' -ForegroundColor Cyan

& $uvExe run virtualization-mcp
