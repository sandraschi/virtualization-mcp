# virtualization-mcp MCPB Package Build Script
# Builds and packages the virtualization-mcp extension for Claude Desktop

param(
    [switch]$Help,
    [switch]$NoSign,
    [string]$OutputDir = "dist"
)

# Show help if requested
if ($Help) {
    Write-Host @"
virtualization-mcp MCPB Package Build Script

USAGE:
    .\scripts\build-mcpb-package.ps1 [OPTIONS]

OPTIONS:
    -Help          Show this help message
    -NoSign        Build without signing (for development/testing)
    -OutputDir     Specify custom output directory (default: dist)

EXAMPLES:
    .\scripts\build-mcpb-package.ps1                    # Build and sign package
    .\scripts\build-mcpb-package.ps1 -NoSign           # Build without signing
    .\scripts\build-mcpb-package.ps1 -OutputDir "C:\builds"  # Custom output directory

DESCRIPTION:
    This script builds a complete MCPB package for the virtualization-mcp extension.
    It validates the manifest, builds the package, and optionally signs it.
    
    The resulting .mcpb file can be installed in Claude Desktop by dragging
    it to the application window.

REQUIREMENTS:
    - Node.js with MCPB CLI installed: npm install -g @anthropic-ai/mcpb
    - Python 3.10+ with required dependencies
    - Valid mcpb/manifest.json file
"@
    exit 0
}

# Set error handling
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "🚀 virtualization-mcp MCPB Package Builder" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Change to project root
Set-Location $ProjectRoot
Write-Host "📁 Working directory: $ProjectRoot" -ForegroundColor Green

# Check if MCPB CLI is installed
Write-Host "🔍 Checking MCPB CLI installation..." -ForegroundColor Yellow
try {
    $mcpbVersion = mcpb --version
    Write-Host "✅ MCPB CLI version: $mcpbVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ MCPB CLI not found. Please install it with:" -ForegroundColor Red
    Write-Host "   npm install -g @anthropic-ai/mcpb" -ForegroundColor Red
    exit 1
}

# Check if manifest exists
$manifestPath = "mcpb/manifest.json"
if (-not (Test-Path $manifestPath)) {
    Write-Host "❌ Manifest file not found: $manifestPath" -ForegroundColor Red
    exit 1
}

# Validate manifest
Write-Host "🔍 Validating manifest..." -ForegroundColor Yellow
try {
    mcpb validate $manifestPath
    Write-Host "✅ Manifest validation passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Manifest validation failed" -ForegroundColor Red
    exit 1
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "📁 Created output directory: $OutputDir" -ForegroundColor Green
}

# Build the package
Write-Host "🔨 Building MCPB package..." -ForegroundColor Yellow
try {
    $packageName = "virtualization-mcp-v1.0.0.mcpb"
    $packagePath = Join-Path $OutputDir $packageName
    
    # Change to mcpb directory and build
    Set-Location "mcpb"
    mcpb pack . "../$packagePath"
    Set-Location ".."
    
    Write-Host "✅ Package built successfully: $packagePath" -ForegroundColor Green
} catch {
    Write-Host "❌ Package build failed" -ForegroundColor Red
    exit 1
}

# Sign the package (unless NoSign is specified)
if (-not $NoSign) {
    Write-Host "🔐 Signing package..." -ForegroundColor Yellow
    try {
        # For now, we'll skip signing as it's not currently used in our workflow
        Write-Host "⚠️  Package signing skipped (not currently configured)" -ForegroundColor Yellow
    } catch {
        Write-Host "❌ Package signing failed" -ForegroundColor Red
        exit 1
}
} else {
    Write-Host "⚠️  Package signing skipped (NoSign flag)" -ForegroundColor Yellow
}

# Verify the package
Write-Host "🔍 Verifying package..." -ForegroundColor Yellow
try {
    mcpb verify $packagePath
    Write-Host "✅ Package verification passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Package verification failed" -ForegroundColor Red
    exit 1
}

# Get package info
Write-Host "📋 Package information:" -ForegroundColor Yellow
try {
    mcpb info $packagePath
} catch {
    Write-Host "⚠️  Could not retrieve package info" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "🎉 Build completed successfully!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "📦 Package: $packagePath" -ForegroundColor White
Write-Host "📏 Size: $((Get-Item $packagePath).Length / 1MB) MB" -ForegroundColor White
Write-Host ""
Write-Host "📥 Installation:" -ForegroundColor Cyan
Write-Host "   1. Open Claude Desktop" -ForegroundColor White
Write-Host "   2. Drag the .mcpb file to Claude Desktop" -ForegroundColor White
Write-Host "   3. Follow the configuration prompts" -ForegroundColor White
Write-Host "   4. Restart Claude Desktop" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Configuration:" -ForegroundColor Cyan
Write-Host "   - VirtualBox Installation Directory: C:\\Program Files\\Oracle\\VirtualBox" -ForegroundColor White
Write-Host "   - VirtualBox User Home: %USERPROFILE%\\VirtualBox VMs" -ForegroundColor White
Write-Host "   - Debug Mode: false (recommended)" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation: https://github.com/sandraschi/virtualization-mcp" -ForegroundColor Cyan



