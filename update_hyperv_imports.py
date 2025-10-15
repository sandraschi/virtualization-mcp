#!/usr/bin/env python3
"""
Update imports and registrations for Hyper-V and Sandbox plugins.
"""

import sys
from pathlib import Path

# Define files to update
FILES_TO_UPDATE = [
    "src/virtualization-mcp/all_tools_server.py",
    "src/virtualization-mcp/tools/register_tools.py",
]


def update_file(file_path):
    """Update imports in a file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Update import paths
        updated = content.replace(
            "from virtualization-mcp.server_v2.plugins.hyperv_manager import HyperVManagerPlugin",
            "from virtualization-mcp.plugins.hyperv import HyperVManagerPlugin",
        )
        updated = updated.replace(
            "from virtualization-mcp.server_v2.plugins.windows_sandbox import WindowsSandboxHelper",
            "from virtualization-mcp.plugins.sandbox import WindowsSandboxHelper",
        )

        if updated != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated)
            print(f"Updated: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """Main function to update all files."""
    repo_root = Path(__file__).parent
    updated = 0

    for rel_path in FILES_TO_UPDATE:
        abs_path = repo_root / rel_path
        if abs_path.exists():
            if update_file(abs_path):
                updated += 1
        else:
            print(f"File not found: {abs_path}", file=sys.stderr)

    print(f"\nUpdated {updated} files.")


if __name__ == "__main__":
    main()
