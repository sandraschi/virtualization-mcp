"""
Virtualization MCP Server - Complete Implementation
"""

__version__ = "1.2.0"

# Ensure the src directory is in the Python path
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Core exports
__all__ = [
    "__version__",
    "create_mcp_instance",
    "get_mcp_instance",
    "get_version",
    "main",
    "main_async",
]

# Lazy imports to avoid circular imports


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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger("virtualization_mcp")
logger.debug(f"virtualization_mcp {__version__} initialized")
