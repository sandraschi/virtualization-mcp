@echo off
rem Run-NakedTest.cmd - logon payload for automated naked-install tests.
rem Expects C:\Assets (sandbox payloads) and C:\Job (spec.json in, RESULT.json out).
setlocal EnableExtensions
set "LOG=%USERPROFILE%\Desktop\naked-test-launch.log"

echo ======================================== >> "%LOG%" 2>&1
echo   Naked install test starting >> "%LOG%" 2>&1
echo   See full progress: type C:\Job\RESULT.json when finished >> "%LOG%" 2>&1
echo ======================================== >> "%LOG%" 2>&1

set "RETRY_COUNT=0"
:wait_job_loop
if exist "C:\Job\spec.json" goto job_ready
set /a RETRY_COUNT+=1
if %RETRY_COUNT% gtr 20 goto job_missing
ping -n 3 127.0.0.1 >nul
goto wait_job_loop

:job_missing
echo [%date% %time%] ERROR: C:\Job\spec.json NOT FOUND after 40s >> "%LOG%"
echo ERROR: spec.json missing - naked test cannot start.
pause
exit /b 2

:job_ready
if not exist "C:\Assets\Invoke-NakedTest.ps1" (
    echo [%date% %time%] ERROR: C:\Assets\Invoke-NakedTest.ps1 NOT FOUND >> "%LOG%"
    echo ERROR: test payload missing from mapped assets.
    pause
    exit /b 3
)
echo [%date% %time%] spec found, starting Invoke-NakedTest.ps1 >> "%LOG%"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\Assets\Invoke-NakedTest.ps1" >> "%LOG%" 2>&1
echo [%date% %time%] Invoke-NakedTest.ps1 exit %ERRORLEVEL% >> "%LOG%"

start "" cmd.exe /c "title Naked Test Log & powershell -NoExit -Command Get-Content -Wait '%LOG%'"
echo Done. RESULT.json is in C:\Job (mapped back to host job dir).
pause
