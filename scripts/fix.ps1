# Autofix entry for `just fix` / `just fmt`.
# Single source of truth lives in lint.ps1 -Fix; this stays a thin wrapper
# so the justfile keeps its lint/fix split.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
& (Join-Path $Root "scripts\lint.ps1") -Fix
exit $LASTEXITCODE
