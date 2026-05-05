# Opens after dev-infra setup: read log without Notepad (often missing in Sandbox 24H2+).
$p = Join-Path $env:USERPROFILE 'Desktop\dev-infra-launch.log'
Write-Host "=== $p ===" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $p)) {
  Write-Host '(Log file not found yet.)' -ForegroundColor Yellow
} else {
  Get-Content -LiteralPath $p -Tail 300 -ErrorAction SilentlyContinue
}
Write-Host ''
Write-Host 'Window left open on purpose. Close when done.' -ForegroundColor DarkGray
