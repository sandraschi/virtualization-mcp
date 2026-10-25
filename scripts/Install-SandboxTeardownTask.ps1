#Requires -RunAsAdministrator
<#
.SYNOPSIS
  One-time admin setup: installs the constrained SYSTEM teardown task for
  virtualization-mcp Windows Sandbox runs.

.DESCRIPTION
  The virtualization-mcp backend runs medium-integrity, so it cannot kill
  vmmemWindowsSandbox.exe (SYSTEM/Hyper-V owned) when graceful close fails.
  This registers a kill-only scheduled task (SYSTEM, highest privileges) that
  the backend triggers on demand via 'schtasks /Run'. Run this script ONCE
  from an elevated PowerShell; the backend never needs elevation itself.

  The task payload is deliberately constrained: it only force-stops the five
  Windows Sandbox processes, nothing else.

.PARAMETER Uninstall
  Removes the task instead of installing it.
#>
param([switch]$Uninstall)

$ErrorActionPreference = 'Stop'
$TaskName = 'virtualization-mcp-sandbox-teardown'
$KillNames = @(
    'WindowsSandbox',
    'WindowsSandboxClient',
    'WindowsSandboxServer',
    'WindowsSandboxRemoteSession',
    'vmmemWindowsSandbox'
)
# Authenticated Users: read + execute (run on demand). SYSTEM/Admins: full.
$TaskSddl = 'D:(A;;GRGX;;;AU)(A;;GA;;;SY)(A;;GA;;;BA)'

if ($Uninstall) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "Removed task '$TaskName'." -ForegroundColor Green
    } catch {
        Write-Host "No task '$TaskName' to remove (or removal failed: $($_.Exception.Message))." -ForegroundColor Yellow
    }
    exit 0
}

$KillExpr = ($KillNames | ForEach-Object {
    "Get-Process -Name '$_' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
}) -join '; '
# Belt and braces: a Session-0 ghost mid-transition can survive Stop-Process
# but answer to taskkill (proven 2026-10-25: second trigger cleared a ghost
# the first pass missed). taskkill deny/fail lines are noise - swallow rc.
$KillExpr += '; ' + ($KillNames | ForEach-Object {
    "taskkill /F /IM $_.exe 2>`$null | Out-Null"
}) -join '; '
$Arguments = "-NoProfile -ExecutionPolicy Bypass -Command `"$KillExpr`""

$registered = $false
try {
    $svc = New-Object -ComObject Schedule.Service
    $svc.Connect()
    $def = $svc.NewTask(0)
    $def.RegistrationInfo.Description = 'virtualization-mcp last-resort Windows Sandbox kill (SYSTEM, trigger on demand only).'
    $def.Principal.UserId = 'SYSTEM'
    $def.Principal.LogonType = 5
    $def.Principal.RunLevel = 1
    $def.Settings.AllowDemandStart = $true
    $def.Settings.DisallowStartIfOnBatteries = $false
    $act = $def.Actions.Create(0)
    $act.Path = 'powershell.exe'
    $act.Arguments = $Arguments
    $folder = $svc.GetFolder('\')
    $folder.RegisterTaskDefinition($TaskName, $def, 6, 'SYSTEM', $null, 5, $TaskSddl) | Out-Null
    $registered = $true
    Write-Host "Registered '$TaskName' with on-demand SDDL for Authenticated Users." -ForegroundColor Green
} catch {
    Write-Host "COM registration with custom SDDL failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host 'Falling back to Register-ScheduledTask (default ACL - on-demand run may need manual grant).' -ForegroundColor Yellow
}

if (-not $registered) {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $Arguments
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartOnDemand
    Register-ScheduledTask -TaskName $TaskName -Action $action -Principal $principal -Settings $settings -Force | Out-Null
    Write-Host "Registered '$TaskName' with default ACL." -ForegroundColor Yellow
    Write-Host 'If the backend logs trigger-denied, grant run permission once via Task Scheduler GUI:' -ForegroundColor Yellow
    Write-Host "  Task Scheduler Library > '$TaskName' > Properties > Security > allow Authenticated Users Read+Execute." -ForegroundColor Yellow
}

$query = schtasks /Query /TN $TaskName 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Verification FAILED - task not queryable: $query" -ForegroundColor Red
    exit 1
}
Write-Host 'Verification: task is queryable. Next, test on-demand trigger from a NON-elevated shell:' -ForegroundColor Cyan
Write-Host "  schtasks /Run /TN $TaskName" -ForegroundColor Cyan
Write-Host 'Expected: SUCCESS, and any running sandbox disappears within ~45s.' -ForegroundColor Cyan
