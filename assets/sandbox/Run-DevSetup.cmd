@echo off
set "LOG=%USERPROFILE%\Desktop\dev-setup.log"
echo [%DATE% %TIME%] Run-DevSetup.cmd starting > "%LOG%"
if exist "C:\Assets\Run-DevSetup.cmd" ( echo [%DATE% %TIME%] C:\Assets mapped OK >> "%LOG%" ) else ( echo [%DATE% %TIME%] C:\Assets NOT MAPPED >> "%LOG%" )
dir "C:\Assets" >> "%LOG%" 2>&1
echo [%DATE% %TIME%] Waiting 5s... >> "%LOG%"
ping -n 6 127.0.0.1 > nul
if exist "C:\Assets\Setup-DevSandbox.ps1" (
    echo [%DATE% %TIME%] Starting Setup-DevSandbox.ps1 >> "%LOG%"
    powershell -ExecutionPolicy Bypass -File "C:\Assets\Setup-DevSandbox.ps1" >> "%LOG%" 2>&1
    echo [%DATE% %TIME%] Exit code %ERRORLEVEL% >> "%LOG%"
) else (
    echo [%DATE% %TIME%] ERROR: Setup-DevSandbox.ps1 NOT FOUND >> "%LOG%"
)
echo @echo off > "%USERPROFILE%\Desktop\View Setup Log.cmd"
echo type "%LOG%" >> "%USERPROFILE%\Desktop\View Setup Log.cmd"
echo echo. >> "%USERPROFILE%\Desktop\View Setup Log.cmd"
echo pause >> "%USERPROFILE%\Desktop\View Setup Log.cmd"
start "" cmd.exe /c "title Dev Setup Log & powershell -NoExit -Command Get-Content -Wait '%LOG%'"
