"""VBoxMCP Server v2 - Refactored implementation.

This package contains the refactored implementation of the VBoxMCP server,
featuring a modular architecture with a clear separation of concerns.

Modules:
    - core: Core server implementation
    - plugins: Plugin system for extending functionality
    - services: Service layer for business logic
    - utils: Utility functions and helpers
"""

# Core exports
from .core.server import VBoxMCPServer
from .config import ServerConfig, load_config

# Version information
__version__ = "2.11.2"

def get_version() -> str:
    """Get the current version of the VBoxMCP server."""
    return __version__

__all__ = [
    'VBoxMCPServer',
    'ServerConfig',
    'load_config',
    'get_version',
    '__version__',
]
