"""
FastMCP Tool Registration for virtualization-mcp

This module registers all virtualization-mcp tools with FastMCP.
"""
import sys
from typing import Dict, Any, List, Optional
import logging
from fastmcp import FastMCP

# Import tools directly from their modules to avoid circular imports
from virtualization_mcp.tools.vm.vm_tools import (
    list_vms, get_vm_info, start_vm, stop_vm, create_vm, delete_vm,
    clone_vm, modify_vm, reset_vm, pause_vm, resume_vm
)

from virtualization_mcp.tools.storage.storage_tools import (
    list_storage_controllers, create_storage_controller, remove_storage_controller
)

from virtualization_mcp.tools.network.network_tools import (
    list_hostonly_networks, create_hostonly_network, remove_hostonly_network
)

from virtualization_mcp.tools.snapshot.snapshot_tools import (
    list_snapshots, create_snapshot, restore_snapshot, delete_snapshot
)

from virtualization_mcp.tools.system.system_tools import (
    get_system_info, get_vbox_version, list_ostypes
)

from virtualization_mcp.tools.example_tools import (
    greet, get_counter, analyze_file
)

# Import backup tools
from virtualization_mcp.tools.backup.backup_tools import (
    create_backup_legacy, list_backups, delete_backup
)

logger = logging.getLogger(__name__)

def register_all_tools(mcp: FastMCP) -> None:
    """Register all virtualization-mcp tools with the FastMCP server.
    
    Args:
        mcp: The FastMCP instance to register tools with
    """
    # VM Tools
    mcp.tool(list_vms, name="list_vms", description="List all available VirtualBox VMs")
    mcp.tool(get_vm_info, name="get_vm_info", description="Get detailed information about a VM")
    mcp.tool(start_vm, name="start_vm", description="Start a virtual machine")
    mcp.tool(stop_vm, name="stop_vm", description="Stop a running virtual machine")
    mcp.tool(create_vm, name="create_vm", description="Create a new virtual machine")
    mcp.tool(delete_vm, name="delete_vm", description="Delete a virtual machine")
    mcp.tool(clone_vm, name="clone_vm", description="Clone a virtual machine")
    # mcp.tool(modify_vm, name="modify_vm", description="Modify VM settings")  # Disabled due to **kwargs
    mcp.tool(reset_vm, name="reset_vm", description="Reset a virtual machine")
    mcp.tool(pause_vm, name="pause_vm", description="Pause a virtual machine")
    mcp.tool(resume_vm, name="resume_vm", description="Resume a paused virtual machine")
    
    # Storage Tools
    mcp.tool(list_storage_controllers, name="list_storage_controllers", description="List storage controllers for a VM")
    mcp.tool(create_storage_controller, name="create_storage_controller", description="Create a storage controller for a VM")
    mcp.tool(remove_storage_controller, name="remove_storage_controller", description="Remove a storage controller from a VM")
    
    # Network Tools
    mcp.tool(list_hostonly_networks, name="list_hostonly_networks", description="List all host-only networks")
    mcp.tool(create_hostonly_network, name="create_hostonly_network", description="Create a host-only network")
    mcp.tool(remove_hostonly_network, name="remove_hostonly_network", description="Remove a host-only network")
    
    # Snapshot Tools
    mcp.tool(list_snapshots, name="list_snapshots", description="List snapshots for a VM")
    mcp.tool(create_snapshot, name="create_snapshot", description="Create a snapshot of a VM")
    mcp.tool(restore_snapshot, name="restore_snapshot", description="Restore a VM to a snapshot")
    mcp.tool(delete_snapshot, name="delete_snapshot", description="Delete a snapshot")
    
    # System Tools
    mcp.tool(get_system_info, name="get_system_info", description="Get system information")
    mcp.tool(get_vbox_version, name="get_vbox_version", description="Get VirtualBox version information")
    mcp.tool(list_ostypes, name="list_ostypes", description="List available OS types")
    
    # Example Tools
    mcp.tool(greet, name="example_greet", description="A simple example tool that greets someone")
    mcp.tool(get_counter, name="get_counter", description="Get the current counter value")
    mcp.tool(analyze_file, name="analyze_file", description="Analyze a file for potential malware")
    
    # Backup Tools
    mcp.tool(create_backup_legacy, name="create_vm_backup", description="Create a backup of a virtual machine")
    mcp.tool(list_backups, name="list_vm_backups", description="List all VM backups")
    mcp.tool(delete_backup, name="delete_vm_backup", description="Delete a VM backup")
    
    logger.info("All virtualization-mcp tools registered successfully")

async def initialize_services():
    """Initialize services that need async initialization."""
    # Initialize any services that need async setup
    pass


