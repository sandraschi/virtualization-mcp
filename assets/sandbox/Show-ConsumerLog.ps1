$p = Join-Path $env:USERPROFILE 'Desktop\consumer-sandbox-launch.log'
Write-Host "=== $p ===" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $p)) {
    Write-Host '(Log file not found yet.)' -ForegroundColor Yellow
} else {
    Get-Content -LiteralPath $p -Tail 300 -ErrorAction SilentlyContinue
}
Write-Host ''
Write-Host 'Nearly-naked test: follow Desktop\consumer-install-test-checklist.txt' -ForegroundColor DarkGray
Write-Host 'Window left open on purpose. Close when done.' -ForegroundColor DarkGray
