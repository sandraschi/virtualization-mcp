"""
Portmanteau Tools Module

Consolidates multiple related tools into single, action-based tools to reduce
the tool explosion problem and improve MCP client usability.

Production mode: 6-7 portmanteau tools (33+ operations)
Testing mode: Individual tools also available
"""

import sys
import logging
from fastmcp import FastMCP

from .discovery_management import register_discovery_management_tool
from .network_management import register_network_management_tool
from .snapshot_management import register_snapshot_management_tool
from .storage_management import register_storage_management_tool
from .system_management import register_system_management_tool
from .vm_management import register_vm_management_tool

logger = logging.getLogger(__name__)


def register_all_portmanteau_tools(mcp: FastMCP) -> None:
    """Register all portmanteau tools with the FastMCP server.

    Args:
        mcp: The FastMCP instance to register tools with
    """
    # Core VirtualBox portmanteau tools (5 tools - always registered)
    register_vm_management_tool(mcp)
    register_network_management_tool(mcp)
    register_snapshot_management_tool(mcp)
    register_storage_management_tool(mcp)
    register_system_management_tool(mcp)
    
    # Help/Status/Discovery portmanteau (consolidates app-specific help tools)
    register_discovery_management_tool(mcp)
    
    # Platform-specific portmanteau tools
    if sys.platform == "win32":
        try:
            from .hyperv_management import register_hyperv_management_tool
            register_hyperv_management_tool(mcp)
            logger.info("Hyper-V management tool registered (Windows platform)")
        except ImportError as e:
            logger.debug(f"Hyper-V tools not available: {e}")

    logger.info("All portmanteau tools registered successfully")


# Export the registration function
__all__ = ["register_all_portmanteau_tools"]
