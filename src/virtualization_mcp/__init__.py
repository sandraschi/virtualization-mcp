"""
Virtualization MCP Server - Complete Implementation
"""

__version__ = "1.0.1b1"

# Ensure the src directory is in the Python path
import os
import sys

# Add the src directory to the Python path
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Core exports
__all__ = [
    "__version__",
    "get_version",
    "create_mcp_instance",
    "get_mcp_instance",
    "main",
    "main_async",
]

# Lazy imports to avoid circular imports
import importlib  # noqa: E402


def _lazy_import():
    """Lazily import the server functions to avoid circular imports."""
    from .all_tools_server import main, start_mcp_server

    return start_mcp_server, start_mcp_server, main


# Create lazy-loaded functions
def create_mcp_instance(*args, **kwargs):
    """Create a new MCP server instance."""
    return _lazy_import()[0](*args, **kwargs)


def get_mcp_instance(*args, **kwargs):
    """Get or create an MCP server instance."""
    return _lazy_import()[1](*args, **kwargs)


def main(*args, **kwargs):
    """Run the main entry point."""
    return _lazy_import()[2](*args, **kwargs)


# For backward compatibility
main_async = main


def get_version() -> str:
    """Return the current version of the virtualization_mcp package."""
    return __version__


# Initialize logging when the package is imported
import logging  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("virtualization_mcp")
logger.debug(f"virtualization_mcp {__version__} initialized")
