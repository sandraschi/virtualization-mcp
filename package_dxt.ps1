<#
.SYNOPSIS
    Packages the virtualization-mcp MCP server into a DXT file using FastMCP tools.
.DESCRIPTION
    This script packages the virtualization-mcp MCP server into a DXT file with all dependencies,
    following FastMCP 2.11 packaging standards.
#>

# Stop on first error
$ErrorActionPreference = "Stop"

# Configuration
$ProjectRoot = $PSScriptRoot
$DxtDir = Join-Path -Path $ProjectRoot -ChildPath "dxt"
$DistDir = Join-Path -Path $ProjectRoot -ChildPath "dist"
$OutputFile = Join-Path -Path $DistDir -ChildPath "virtualization-mcp.dxt"

# Create dist directory if it doesn't exist
if (-not (Test-Path -Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir | Out-Null
}

# Clean up previous builds
Write-Host "[1/4] Cleaning up previous builds..."
if (Test-Path -Path $OutputFile) {
    Remove-Item -Path $OutputFile -Force -ErrorAction SilentlyContinue
}

# Validate the DXT package
Write-Host "[2/4] Validating DXT package..."
$validationResult = dxt validate $DxtDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "DXT validation failed:"
    Write-Error $validationResult
    exit 1
}

# Install dependencies
Write-Host "[3/4] Installing dependencies..."
$requirementsFile = Join-Path -Path $DxtDir -ChildPath "requirements.txt"
if (Test-Path -Path $requirementsFile) {
    pip install -r $requirementsFile --target (Join-Path -Path $DxtDir -ChildPath "site-packages") --quiet
}

# Package the DXT
Write-Host "[4/4] Creating DXT package..."
dxt pack --input $DxtDir --output $OutputFile
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create DXT package"
    exit 1
}

# Verify the package was created
if (Test-Path -Path $OutputFile) {
    $fileSize = (Get-Item -Path $OutputFile).Length / 1MB
    Write-Host "✅ DXT package created successfully!" -ForegroundColor Green
    Write-Host "   Output: $OutputFile"
    Write-Host "   Size: $([math]::Round($fileSize, 2)) MB"
    Write-Host "`nYou can now install this package in Claude Desktop using the DXT CLI." -ForegroundColor Green
} else {
    Write-Error "Failed to create DXT package: Output file not found"
    exit 1
}



