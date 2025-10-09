"""
Portmanteau Tools Module

Consolidates multiple related tools into single, action-based tools to reduce
the tool explosion problem and improve MCP client usability.

This module replaces 83+ individual tools with 8-12 logical portmanteau tools.
"""

from fastmcp import FastMCP
from .vm_management import register_vm_management_tool
from .network_management import register_network_management_tool
from .storage_management import register_storage_management_tool
from .snapshot_management import register_snapshot_management_tool
from .system_management import register_system_management_tool

def register_all_portmanteau_tools(mcp: FastMCP) -> None:
    """Register all portmanteau tools with the FastMCP server.
    
    Args:
        mcp: The FastMCP instance to register tools with
    """
    # Register all portmanteau tools
    register_vm_management_tool(mcp)
    register_network_management_tool(mcp)
    register_storage_management_tool(mcp)
    register_snapshot_management_tool(mcp)
    register_system_management_tool(mcp)
    
    # Log successful registration
    import logging
    logger = logging.getLogger(__name__)
    logger.info("All portmanteau tools registered successfully")

# Export the registration function
__all__ = ['register_all_portmanteau_tools']

