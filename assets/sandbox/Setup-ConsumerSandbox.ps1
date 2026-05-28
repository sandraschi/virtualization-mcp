<#
.SYNOPSIS
  Nearly-naked Windows Sandbox: winget bootstrap only, optional Claude Desktop fixture.

.DESCRIPTION
  For validating fleet INSTALL.md Options A-C without pre-installing git, uv, node, just, etc.
  Mapped as C:\Assets via Launch-ConsumerSandbox.ps1 or webapp consumer_setup.

  Set CONSUMER_INSTALL_CLAUDE=1 before Run-Consumer.cmd to install Claude Desktop MSIX.

.NOTES
  Do not use global $ErrorActionPreference = 'Stop' (winget returns benign non-zero codes).
#>

$ProgressPreference = 'SilentlyContinue'
$lib = Join-Path $PSScriptRoot 'lib\Winget-Bootstrap.ps1'
if (-not (Test-Path -LiteralPath $lib)) {
    throw "Missing winget bootstrap library: $lib"
}
. $lib

$installClaude = $env:CONSUMER_INSTALL_CLAUDE -eq '1'

function Write-ConsumerChecklist {
    param([string]$DesktopPath)
    $lines = @(
        'Nearly-naked install test checklist'
        '==================================='
        ''
        'Baseline (should all fail before you run INSTALL.md steps):'
        '  where.exe git'
        '  where.exe uv'
        '  where.exe node'
        '  python --version'
        ''
        'Option A: GitHub Releases -> download .mcpb -> drag into Claude Desktop'
        'Option B: winget install OpenJS.NodeJS -> reopen terminal -> npx @anthropic-ai/mcpb install ...'
        'Option C: winget uv + git -> clone -> uv sync -> claude_desktop_config.json'
        ''
        'Fleet standard: mcp-central-docs/standards/NAKED_INSTALL_TESTING.md'
    )
    $dest = Join-Path $DesktopPath 'consumer-install-test-checklist.txt'
    Set-Content -LiteralPath $dest -Value $lines -Encoding UTF8
    Write-Host "Wrote $dest" -ForegroundColor Green
}

function Install-ConsumerClaudeDesktop {
    Write-WsbStep 'Installing Claude Desktop (MSIX fixture for Option A tests)'
    $url = 'https://claude.ai/api/desktop/win32/x64/msix/latest/redirect'
    $msix = Join-Path $env:TEMP 'Claude.msix'
    try {
        Invoke-WebRequest -Uri $url -OutFile $msix -UseBasicParsing
        Add-AppxPackage -Path $msix -ErrorAction Stop
        Write-Host 'Claude Desktop installed.' -ForegroundColor Green
    } catch {
        Write-Warning "Claude Desktop install failed: $($_.Exception.Message)"
        Write-Host 'Install manually from https://claude.ai/download' -ForegroundColor Yellow
    }
}

function Test-ConsumerNakedBaseline {
    Write-WsbStep 'Nearly-naked baseline (dev tools must be absent)'
    $devTools = @('git', 'gh', 'uv', 'node', 'npm', 'python', 'just', 'ruff', 'biome')
    $found = @()
    foreach ($tool in $devTools) {
        if (Test-WsbCommandExists $tool) {
            $found += $tool
        }
    }
    if ($found.Count -gt 0) {
        Write-Warning ("Unexpected dev tools on PATH: {0}" -f ($found -join ', '))
    } else {
        Write-Host 'OK: no dev tools on PATH' -ForegroundColor Green
    }
}

Ensure-WsbWingetAvailable
Test-ConsumerNakedBaseline

if ($installClaude) {
    Install-ConsumerClaudeDesktop
}

Write-ConsumerChecklist -DesktopPath ([Environment]::GetFolderPath('Desktop'))

Write-WsbStep 'Consumer sandbox ready'
Write-Host 'Run INSTALL.md steps manually. Close sandbox when done (session resets).' -ForegroundColor Cyan
