# Create a minimal DXT package for testing
$tempDir = ".\minimal_dxt_temp"
$outputFile = ".\dist\vbox-mcp-minimal.dxt"

# Clean up any existing files
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
if (Test-Path $outputFile) { Remove-Item -Force $outputFile }

# Create directory structure
New-Item -ItemType Directory -Path "$tempDir\vbox-mcp" | Out-Null
New-Item -ItemType Directory -Path "$tempDir\vbox-mcp\vbox" | Out-Null

# Create minimal files
@'
{
  "name": "vbox-mcp",
  "version": "0.1.0",
  "description": "Minimal test package for vbox-mcp",
  "entry_point": "vboxmcp.server:app"
}
'@ | Out-File -FilePath "$tempDir\manifest.json" -Encoding utf8

# Create empty __init__.py
Set-Content -Path "$tempDir\vbox-mcp\__init__.py" -Value "" -Encoding utf8

# Create minimal server.py
@'"""Minimal server for testing DXT package."""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "vbox-mcp is running"}
'@ | Out-File -FilePath "$tempDir\vbox-mcp\server.py" -Encoding utf8

# Create empty vbox/__init__.py
Set-Content -Path "$tempDir\vbox-mcp\vbox\__init__.py" -Value "" -Encoding utf8

# Create the zip file
Compress-Archive -Path "$tempDir\*" -DestinationPath $outputFile -Force

# Clean up
Remove-Item -Recurse -Force $tempDir

Write-Host "Created minimal DXT package: $outputFile"
