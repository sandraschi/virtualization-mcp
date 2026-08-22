@echo off
setlocal EnableExtensions
set "LOG=%USERPROFILE%\Desktop\dev-infra-launch.log"

echo ========================================
echo     Virtualization-MCP Dev Infra Setup
echo ========================================
echo.
echo Log: %LOG%
echo.

echo [%date% %time%] Run-DevInfra.cmd starting > "%LOG%"

set "RETRY_COUNT=0"
:wait_assets_loop
if exist "C:\Assets\Setup-DevInfraSandbox.ps1" (
    echo [%date% %time%] C:\Assets mapped and setup script found >> "%LOG%"
    goto assets_ready
)
set /a RETRY_COUNT+=1
if %RETRY_COUNT% gtr 15 (
    echo [%date% %time%] ERROR: C:\Assets\Setup-DevInfraSandbox.ps1 NOT FOUND after 30s >> "%LOG%"
    echo ERROR: Setup script not found in mapped folder within 30s!
    goto assets_failed
)
echo [%date% %time%] Waiting for C:\Assets folder mount (attempt %RETRY_COUNT%/15)... >> "%LOG%"
ping -n 3 127.0.0.1 >nul
goto wait_assets_loop

:assets_ready
echo [%date% %time%] Starting Setup-DevInfraSandbox.ps1 >> "%LOG%"
echo Running setup script, this may take several minutes...
powershell.exe -NoLogo -NoProfile -WindowStyle Normal -ExecutionPolicy Bypass -File "C:\Assets\Setup-DevInfraSandbox.ps1" >> "%LOG%" 2>&1
echo [%date% %time%] powershell exit %ERRORLEVEL% >> "%LOG%"
:assets_failed

echo.
echo ========================================
echo     Setup finished. Check the log above.
echo ========================================

rem Create desktop shortcut to view log
echo @echo off > "%USERPROFILE%\Desktop\View Setup Log.cmd"
echo type "%LOG%" >> "%USERPROFILE%\Desktop\View Setup Log.cmd"
echo echo. >> "%USERPROFILE%\Desktop\View Setup Log.cmd"
echo pause >> "%USERPROFILE%\Desktop\View Setup Log.cmd"

rem Also try to open a live log viewer (may fail on some builds, hence the shortcut above)
start "" cmd.exe /c "title DevInfra Log & powershell -NoExit -Command Get-Content -Wait '%LOG%'"

rem Fallback: also try opening with notepad if available
if exist "%windir%\notepad.exe" (
    start "" notepad "%LOG%"
)
