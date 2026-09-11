@echo off
setlocal EnableExtensions
set "LOG=C:\Job\naked-test-launch.log"
set "DESKLOG=%USERPROFILE%\Desktop\naked-test-launch.log"

set "RETRY_COUNT=0"
:wait_assets_loop
if exist "C:\Assets\Invoke-NakedTest.ps1" goto assets_ready
set /a RETRY_COUNT+=1
if %RETRY_COUNT% gtr 30 goto assets_missing
ping -n 2 127.0.0.1 >nul
goto wait_assets_loop

:assets_missing
echo [%date% %time%] ERROR: C:\Assets\Invoke-NakedTest.ps1 NOT FOUND after 30 retries > "%DESKLOG%"
echo {"finished_utc":"%date% %time%","repo":"","branch":"","pass":false,"failed_step":"assets","note":"C:\Assets not mounted inside sandbox","steps":[],"log_tail":["assets missing"]} > "C:\Job\RESULT.json"
exit /b 3

:assets_ready
set "RETRY_COUNT=0"
:wait_job_loop
if exist "C:\Job\spec.json" goto job_ready
set /a RETRY_COUNT+=1
if %RETRY_COUNT% gtr 30 goto job_missing
ping -n 2 127.0.0.1 >nul
goto wait_job_loop

:job_missing
echo [%date% %time%] ERROR: C:\Job\spec.json NOT FOUND after 30 retries > "%DESKLOG%"
echo {"finished_utc":"%date% %time%","repo":"","branch":"","pass":false,"failed_step":"job_spec","note":"C:\Job\spec.json not found inside sandbox","steps":[],"log_tail":["spec.json missing"]} > "C:\Job\RESULT.json"
exit /b 2

:job_ready
echo [%date% %time%] Assets and Job folders ready. Initializing test... > "%LOG%"
>> "%LOG%" 2>&1 (
    echo ========================================
    echo   Naked install test starting
    echo   Sandbox Time: %date% %time%
    echo ========================================
    echo [%date% %time%] spec found:
    type "C:\Job\spec.json"
    echo.
)

if not exist "C:\Assets\Invoke-NakedTest.ps1" (
    echo [%date% %time%] ERROR: C:\Assets\Invoke-NakedTest.ps1 NOT FOUND >> "%LOG%" 2>&1
    echo {"finished_utc":"%date% %time%","repo":"","branch":"","pass":false,"failed_step":"harness","note":"C:\Assets\Invoke-NakedTest.ps1 missing","steps":[],"log_tail":["Invoke-NakedTest.ps1 missing"]} > "C:\Job\RESULT.json"
    exit /b 3
)

echo [%date% %time%] starting Invoke-NakedTest.ps1 >> "%LOG%" 2>&1
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\Assets\Invoke-NakedTest.ps1" >> "%LOG%" 2>&1
set "PS_EXIT=%ERRORLEVEL%"
echo [%date% %time%] Invoke-NakedTest.ps1 finished with exit code %PS_EXIT% >> "%LOG%" 2>&1

if %PS_EXIT% neq 0 (
    if not exist "C:\Job\RESULT.json" (
        echo {"finished_utc":"%date% %time%","repo":"","branch":"","pass":false,"failed_step":"ps_error","note":"Invoke-NakedTest.ps1 failed (exit %PS_EXIT%)","steps":[],"log_tail":["See naked-test-launch.log for error details"]} > "C:\Job\RESULT.json"
    )
)

copy /y "%LOG%" "%DESKLOG%" >nul 2>&1
echo Done. >> "%LOG%" 2>&1
exit /b 0
