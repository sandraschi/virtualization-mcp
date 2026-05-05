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

rem Verify mapped folder exists
if exist "C:\Assets\Run-DevInfra.cmd" (
    echo [%date% %time%] C:\Assets mapped OK >> "%LOG%"
) else (
    echo [%date% %time%] C:\Assets NOT MAPPED - folder missing >> "%LOG%"
)
dir "C:\Assets" >> "%LOG%" 2>&1

rem Mapped C:\Assets can lag slightly right after logon; brief wait before running setup.
echo [%date% %time%] Waiting 5s for folder to stabilize... >> "%LOG%"
ping -n 6 127.0.0.1 >nul

if exist "C:\Assets\Setup-DevInfraSandbox.ps1" (
    echo [%date% %time%] Starting Setup-DevInfraSandbox.ps1 >> "%LOG%"
    echo Running setup script, this may take several minutes...
    powershell.exe -NoLogo -NoProfile -WindowStyle Normal -ExecutionPolicy Bypass -File "C:\Assets\Setup-DevInfraSandbox.ps1" >> "%LOG%" 2>&1
    echo [%date% %time%] powershell exit %ERRORLEVEL% >> "%LOG%"
) else (
    echo [%date% %time%] ERROR: Setup-DevInfraSandbox.ps1 NOT FOUND in C:\Assets >> "%LOG%"
    echo ERROR: Setup script not found in mapped folder!
)

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
