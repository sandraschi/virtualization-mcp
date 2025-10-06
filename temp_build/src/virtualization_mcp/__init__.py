"""
VirtualBox MCP Server - FastMCP 2.10.1 Implementation

This package provides a FastMCP-compliant interface for managing VirtualBox VMs.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import and expose key components
from .vbox.manager import VBoxManager, VBoxManagerError
from .vbox.templates import TemplateManager
from .vbox.vm_operations import VMOperations
from .vbox.snapshots import SnapshotManager
from .vbox.networking import NetworkManager

# Make these available at the package level
__all__ = [
    'VBoxManager',
    'VBoxManagerError',
    'TemplateManager',
    'VMOperations',
    'SnapshotManager',
    'NetworkManager',
    'logger'
]

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

__version__ = "0.1.0"

# Import key components to make them available at the package level
from .server import main, setup_logging
from .vbox.vm_operations import VMOperations
from .vbox.snapshots import SnapshotManager
from .vbox.networking import NetworkManager
from .vbox.manager import VBoxManager, VBoxManagerError
from .vbox.templates import TemplateManager

# Define __all__ to control what gets imported with 'from virtualization-mcp import *'
__all__ = [
    'main',
    'setup_logging',
    'VMOperations',
    'SnapshotManager',
    'NetworkManager',
    'VBoxManager',
    'VBoxManagerError',
    'TemplateManager',
]

# Set up logging by default
setup_logging(debug=os.getenv('VBOXMCP_DEBUG', '').lower() in ('1', 'true', 'yes'))
