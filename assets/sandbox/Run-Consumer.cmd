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

set "RETRY_COUNT=0"
:wait_assets_loop
if exist "C:\Assets\Setup-ConsumerSandbox.ps1" (
    echo [%date% %time%] C:\Assets mapped and setup script found >> "%LOG%"
    goto assets_ready
)
set /a RETRY_COUNT+=1
if %RETRY_COUNT% gtr 15 (
    echo [%date% %time%] ERROR: C:\Assets\Setup-ConsumerSandbox.ps1 NOT FOUND after 30s >> "%LOG%"
    echo ERROR: Setup script not found in mapped folder within 30s!
    goto assets_failed
)
echo [%date% %time%] Waiting for C:\Assets folder mount (attempt %RETRY_COUNT%/15)... >> "%LOG%"
ping -n 3 127.0.0.1 >nul
goto wait_assets_loop

:assets_ready
echo [%date% %time%] Starting Setup-ConsumerSandbox.ps1 >> "%LOG%"
echo Running consumer setup (winget bootstrap only)...
powershell.exe -NoLogo -NoProfile -WindowStyle Normal -ExecutionPolicy Bypass -File "C:\Assets\Setup-ConsumerSandbox.ps1" >> "%LOG%" 2>&1
echo [%date% %time%] powershell exit %ERRORLEVEL% >> "%LOG%"
:assets_failed

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
