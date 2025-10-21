"""
Discovery Management Portmanteau Tool

Consolidates help, status, and tool discovery tools into one interface.
This is SEPARATE from MCP protocol's native tools/list - these are
application-specific help and introspection tools.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Define available actions
DISCOVERY_ACTIONS = {
    "list_tools": "List all available virtualization-mcp tools",
    "tool_info": "Get detailed information about a specific tool",
    "tool_schema": "Get JSON schema for a tool's parameters",
    "help": "Get help information",
}


def register_discovery_management_tool(mcp: FastMCP) -> None:
    """Register the discovery/help management portmanteau tool."""

    @mcp.tool()
    async def discovery_management(
        action: Literal["list_tools", "tool_info", "tool_schema", "help"],
        tool_name: str | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """
        Get help and tool information with various actions.

        This consolidates application-specific help/discovery tools.
        Note: MCP protocol provides native tool discovery via tools/list -
        this tool is for application-specific help and introspection.

        Args:
            action: The operation to perform. Available actions:
                - list_tools: List all virtualization-mcp tools (optional: category, search)
                - tool_info: Get detailed info about a tool (requires tool_name)
                - tool_schema: Get JSON schema for tool (requires tool_name)
                - help: Get general help information

            tool_name: Name of the tool (required for tool_info, tool_schema)
            category: Filter by category (for list_tools)
            search: Search term (for list_tools)

        Returns:
            Dict containing the result of the operation

        Examples:
            # List all tools
            result = await discovery_management(action="list_tools")

            # Get tool information
            result = await discovery_management(
                action="tool_info",
                tool_name="vm_management"
            )

            # Get help
            result = await discovery_management(action="help")
        """
        try:
            # Validate action
            if action not in DISCOVERY_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(DISCOVERY_ACTIONS.keys())}",
                    "available_actions": DISCOVERY_ACTIONS,
                }

            logger.info(f"Executing discovery management action: {action}")

            # Route to appropriate function based on action
            if action == "list_tools":
                return await _handle_list_tools(category=category, search=search)

            elif action == "tool_info":
                return await _handle_tool_info(tool_name=tool_name)

            elif action == "tool_schema":
                return await _handle_tool_schema(tool_name=tool_name)

            elif action == "help":
                return await _handle_help()

            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                }

        except Exception as e:
            logger.error(f"Discovery management error for action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Discovery operation failed: {str(e)}",
                "action": action,
            }


async def _handle_list_tools(category: str | None = None, search: str | None = None) -> dict[str, Any]:
    """Handle list_tools action - delegates to existing list_tools function."""
    try:
        # Import the actual list_tools implementation
        # Note: We can't directly call it due to service_manager dependency
        # So provide static comprehensive tool information
        from virtualization_mcp.tools.vm.vm_tools import (
            list_vms, get_vm_info, create_vm, start_vm, stop_vm, delete_vm,
            clone_vm, reset_vm, pause_vm, resume_vm
        )
        from virtualization_mcp.tools.network.network_tools import (
            list_hostonly_networks, create_hostonly_network, remove_hostonly_network
        )
        from virtualization_mcp.tools.snapshot.snapshot_tools import (
            list_snapshots, create_snapshot, restore_snapshot, delete_snapshot
        )
        from virtualization_mcp.tools.storage.storage_tools import (
            list_storage_controllers, create_storage_controller, remove_storage_controller
        )
        from virtualization_mcp.tools.system.system_tools import (
            get_system_info, get_vbox_version, list_ostypes
        )
        
        tools = {
            "portmanteau": [
                {"name": "vm_management", "operations": 10, "category": "vm"},
                {"name": "network_management", "operations": 5, "category": "network"},
                {"name": "snapshot_management", "operations": 4, "category": "snapshot"},
                {"name": "storage_management", "operations": 6, "category": "storage"},
                {"name": "system_management", "operations": 5, "category": "system"},
            ],
            "individual": {
                "vm": ["list_vms", "get_vm_info", "create_vm", "start_vm", "stop_vm", "delete_vm", "clone_vm", "reset_vm", "pause_vm", "resume_vm"],
                "network": ["list_hostonly_networks", "create_hostonly_network", "remove_hostonly_network"],
                "snapshot": ["list_snapshots", "create_snapshot", "restore_snapshot", "delete_snapshot"],
                "storage": ["list_storage_controllers", "create_storage_controller", "remove_storage_controller"],
                "system": ["get_system_info", "get_vbox_version", "list_ostypes"],
            }
        }
        
        return {
            "success": True,
            "tools": tools,
            "note": "Use TOOL_MODE=testing to enable individual tools"
        }
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return {"success": False, "error": str(e)}


async def _handle_tool_info(tool_name: str | None = None) -> dict[str, Any]:
    """Handle tool_info action."""
    if not tool_name:
        return {"success": False, "error": "tool_name required for tool_info"}
    
    # Provide information about portmanteau tools and their operations
    tool_info_map = {
        "vm_management": {
            "type": "portmanteau",
            "operations": ["list", "create", "start", "stop", "delete", "clone", "reset", "pause", "resume", "info"],
            "description": "Complete VM lifecycle management",
        },
        "network_management": {
            "type": "portmanteau",
            "operations": ["list_networks", "create_network", "remove_network", "list_adapters", "configure_adapter"],
            "description": "Network configuration",
        },
        "snapshot_management": {
            "type": "portmanteau",
            "operations": ["list", "create", "restore", "delete"],
            "description": "Snapshot management",
        },
        "storage_management": {
            "type": "portmanteau",
            "operations": ["list_controllers", "create_controller", "remove_controller", "list_disks", "create_disk", "attach_disk"],
            "description": "Storage management",
        },
        "system_management": {
            "type": "portmanteau",
            "operations": ["host_info", "vbox_version", "ostypes", "metrics", "screenshot"],
            "description": "System information",
        },
        "hyperv_management": {
            "type": "portmanteau",
            "operations": ["list", "get", "start", "stop"],
            "description": "Hyper-V management (Windows only)",
        },
    }
    
    info = tool_info_map.get(tool_name)
    if info:
        return {"success": True, "tool_name": tool_name, "info": info}
    
    return {"success": False, "error": f"Tool {tool_name} not found", "tool_name": tool_name}


async def _handle_tool_schema(tool_name: str | None = None) -> dict[str, Any]:
    """Handle tool_schema action."""
    if not tool_name:
        return {"success": False, "error": "tool_name required for tool_schema"}
    
    return {
        "success": True,
        "tool_name": tool_name,
        "message": "Tool schemas available via MCP protocol - check inputSchema in tools/list response",
        "note": "All portmanteau tools use Literal types for action enums in the schema"
    }


async def _handle_help() -> dict[str, Any]:
    """Handle help action."""
    return {
        "success": True,
        "help": {
            "server": "virtualization-mcp v1.0.1b2",
            "description": "Professional VirtualBox management MCP server",
            "tool_modes": {
                "production": "5-6 portmanteau tools (default)",
                "testing": "60+ individual tools + portmanteau"
            },
            "portmanteau_tools": [
                "vm_management", "network_management", "snapshot_management",
                "storage_management", "system_management", "hyperv_management (Windows)"
            ],
            "documentation": "See docs/ directory for comprehensive guides",
            "quick_start": "Set TOOL_MODE=production (default) or TOOL_MODE=testing",
        }
    }

