#Requires -Version 5.1
# Fleet shim: delegates to the canonical pack pipeline so fixes reach every repo at once.
# See mcp-central-docs/scripts/fleet-mcpb-pack.ps1 (MCPB_PACKAGING_STANDARDS.md section 2.5).
param([string]$RepoRoot)
if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent $PSScriptRoot }
& (Join-Path $RepoRoot '..\mcp-central-docs\scripts\fleet-mcpb-pack.ps1') -RepoRoot $RepoRoot
