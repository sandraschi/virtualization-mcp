@echo off
setlocal EnableExtensions
set "LOG=%USERPROFILE%\Desktop\consumer-sandbox-launch.log"

echo ========================================
echo   Virtualization-MCP Consumer Sandbox
echo   (nearly naked - no dev stack)
echo ========================================
echo.
echo Log: %LOG%
echo.

echo [%date% %time%] Run-Consumer.cmd starting > "%LOG%"
if defined CONSUMER_INSTALL_CLAUDE (
    echo [%date% %time%] CONSUMER_INSTALL_CLAUDE=%CONSUMER_INSTALL_CLAUDE% >> "%LOG%"
)

if exist "C:\Assets\Run-Consumer.cmd" (
    echo [%date% %time%] C:\Assets mapped OK >> "%LOG%"
) else (
    echo [%date% %time%] C:\Assets NOT MAPPED >> "%LOG%"
)
dir "C:\Assets" >> "%LOG%" 2>&1

echo [%date% %time%] Waiting 5s for folder to stabilize... >> "%LOG%"
ping -n 6 127.0.0.1 >nul

if exist "C:\Assets\Setup-ConsumerSandbox.ps1" (
    echo [%date% %time%] Starting Setup-ConsumerSandbox.ps1 >> "%LOG%"
    echo Running consumer setup (winget bootstrap only)...
    powershell.exe -NoLogo -NoProfile -WindowStyle Normal -ExecutionPolicy Bypass -File "C:\Assets\Setup-ConsumerSandbox.ps1" >> "%LOG%" 2>&1
    echo [%date% %time%] powershell exit %ERRORLEVEL% >> "%LOG%"
) else (
    echo [%date% %time%] ERROR: Setup-ConsumerSandbox.ps1 NOT FOUND >> "%LOG%"
    echo ERROR: Setup script not found in mapped folder!
)

echo.
echo ========================================
echo   Consumer setup finished. See log.
echo ========================================

echo @echo off > "%USERPROFILE%\Desktop\View Consumer Log.cmd"
echo type "%LOG%" >> "%USERPROFILE%\Desktop\View Consumer Log.cmd"
echo echo. >> "%USERPROFILE%\Desktop\View Consumer Log.cmd"
echo pause >> "%USERPROFILE%\Desktop\View Consumer Log.cmd"

start "" cmd.exe /c "title Consumer Log & powershell -NoExit -Command Get-Content -Wait '%LOG%'"

if exist "C:\Assets\Show-ConsumerLog.ps1" (
    start "" powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\Assets\Show-ConsumerLog.ps1"
)
