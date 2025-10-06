"""
VBox Package - VirtualBox Management for MCP
Comprehensive VirtualBox operations through MCP protocol
"""

# Import the appropriate implementation based on Python version
import sys

if sys.version_info >= (3, 13):
    # Use our compatibility adapter for Python 3.13+
    from .compat_adapter import VBoxManager, VBoxManagerError, get_vbox_manager
else:
    # Use the original implementation for older Python versions
    from .manager import VBoxManager, VBoxManagerError
    
    def get_vbox_manager():
        """Get a VBoxManager instance (for compatibility)."""
        return VBoxManager()

from .vm_operations import VMOperations
from .snapshots import SnapshotManager
from .templates import TemplateManager

__version__ = "1.0.0"
__author__ = "VirtualBox MCP Team"

# Package-level exports
__all__ = [
    "VBoxManager",
    "VBoxManagerError",
    "get_vbox_manager",
    "VMOperations",
    "SnapshotManager",
    "TemplateManager"
]

# Package metadata
PACKAGE_INFO = {
    "name": "virtualization-mcp",
    "version": __version__,
    "description": "VirtualBox MCP Server - FastMCP-based VM management",
    "author": __author__,
    "requires": [
        "fastmcp>=2.11.3",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0"
    ]
}



