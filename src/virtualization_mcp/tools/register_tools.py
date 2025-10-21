"""
FastMCP Tool Registration for virtualization-mcp

This module registers all virtualization-mcp tools with FastMCP.
"""

import logging

from fastmcp import FastMCP

# Import backup tools
from virtualization_mcp.tools.backup.backup_tools import (
    create_backup_legacy,
    delete_backup,
    list_backups,
)
from virtualization_mcp.tools.example_tools import analyze_file, get_counter, greet
from virtualization_mcp.tools.network.network_tools import (
    create_hostonly_network,
    list_hostonly_networks,
    remove_hostonly_network,
)
from virtualization_mcp.tools.snapshot.snapshot_tools import (
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)
from virtualization_mcp.tools.storage.storage_tools import (
    create_storage_controller,
    list_storage_controllers,
    remove_storage_controller,
)
from virtualization_mcp.tools.system.system_tools import (
    get_system_info,
    get_vbox_version,
    list_ostypes,
)

# Import tools directly from their modules to avoid circular imports
from virtualization_mcp.tools.vm.vm_tools import (
    clone_vm,
    create_vm,
    delete_vm,
    get_vm_info,
    list_vms,
    pause_vm,
    reset_vm,
    resume_vm,
    start_vm,
    stop_vm,
)

logger = logging.getLogger(__name__)


def register_all_tools(mcp: FastMCP) -> None:
    """Register all virtualization-mcp tools with the FastMCP server.

    Args:
        mcp: The FastMCP instance to register tools with
    """
    # Register portmanteau tools first (consolidated tools)
    from virtualization_mcp.tools.portmanteau import register_all_portmanteau_tools

    register_all_portmanteau_tools(mcp)
    logger.info("Portmanteau tools registered successfully")

    # Register individual tools for backward compatibility
    # VM Tools - using function docstrings automatically
    mcp.tool(list_vms)
    mcp.tool(get_vm_info)
    mcp.tool(start_vm)
    mcp.tool(stop_vm)
    mcp.tool(create_vm)
    mcp.tool(delete_vm)
    mcp.tool(clone_vm)
    mcp.tool(reset_vm)
    mcp.tool(pause_vm)
    mcp.tool(resume_vm)

    # Storage Tools - using function docstrings automatically
    mcp.tool(list_storage_controllers)
    mcp.tool(create_storage_controller)
    mcp.tool(remove_storage_controller)

    # Network Tools - using function docstrings automatically
    mcp.tool(list_hostonly_networks)
    mcp.tool(create_hostonly_network)
    mcp.tool(remove_hostonly_network)

    # Snapshot Tools - using function docstrings automatically
    mcp.tool(list_snapshots)
    mcp.tool(create_snapshot)
    mcp.tool(restore_snapshot)
    mcp.tool(delete_snapshot)

    # System Tools - using function docstrings automatically
    mcp.tool(get_system_info)
    mcp.tool(get_vbox_version)
    mcp.tool(list_ostypes)

    # Example Tools
    mcp.tool(greet)
    mcp.tool(get_counter)
    mcp.tool(analyze_file)

    # Backup Tools - using function docstrings automatically
    mcp.tool(create_backup_legacy)
    mcp.tool(list_backups)
    mcp.tool(delete_backup)

    logger.info(
        "All virtualization-mcp tools registered successfully (including portmanteau tools)"
    )


async def initialize_services():
    """Initialize services that need async initialization."""
    # Initialize any services that need async setup
    pass
