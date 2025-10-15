#!/usr/bin/env python3
"""Script to update imports in plugin files after moving to server_v2/plugins."""

from pathlib import Path

# Directory containing the plugin files
plugins_dir = Path("src/virtualization-mcp/server_v2/plugins")

# List of plugin files to update (excluding __init__.py and base_plugin.py)
plugin_files = [
    "ai_security_analyzer.py",
    "backup.py",
    "documentation.py",
    "hyperv_manager.py",
    "malware_analyzer.py",
    "monitoring.py",
    "network_analyzer.py",
    "security_testing.py",
    "windows_sandbox.py",
]

# Update imports in each file
for filename in plugin_files:
    filepath = plugins_dir / filename
    if not filepath.exists():
        print(f"Warning: File not found: {filepath}")
        continue

    # Read the file content
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # Update import statements
    updated_content = content.replace(
        "from .base import BasePlugin",
        "from virtualization-mcp.server_v2.plugins.base import BasePlugin",
    ).replace(
        "from . import register_plugin",
        "from virtualization-mcp.server_v2.plugins import register_plugin",
    )

    # Write the updated content back to the file
    if updated_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Updated imports in {filename}")
    else:
        print(f"No import updates needed for {filename}")

print("\nAll plugin imports have been updated.")
