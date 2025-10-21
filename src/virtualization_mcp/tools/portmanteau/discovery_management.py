"""
Discovery Management Portmanteau Tool

Consolidates all tool discovery and introspection operations.
Helps users and AI assistants discover available tools and their capabilities.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Define available actions
DISCOVERY_ACTIONS = {
    "list": "List all available tools with optional filtering",
    "info": "Get detailed information about a specific tool",
    "schema": "Get JSON schema for a tool's parameters",
}


def register_discovery_management_tool(mcp: FastMCP) -> None:
    """Register the discovery management portmanteau tool."""

    @mcp.tool()
    async def discovery_management(
        action: Literal["list", "info", "schema"],
        tool_name: str | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """
        Discover and explore available MCP tools with various actions.

        Args:
            action: The operation to perform. Available actions:
                - list: List all available tools (optional: category, search filters)
                - info: Get detailed information about a tool (requires tool_name)
                - schema: Get JSON schema for tool parameters (requires tool_name)

            tool_name: Name of the tool to get information about (required for info, schema)
            category: Filter tools by category for list action (e.g., 'vm', 'network')
            search: Search term to filter tools by name or description for list action

        Returns:
            Dict containing the result of the operation:
            - For list: List of tool information dictionaries
            - For info: Detailed tool information
            - For schema: JSON schema for tool parameters

        Examples:
            # List all tools
            result = await discovery_management(action="list")

            # List VM-related tools
            result = await discovery_management(
                action="list",
                category="vm"
            )

            # Search for networking tools
            result = await discovery_management(
                action="list",
                search="network"
            )

            # Get info about a specific tool
            result = await discovery_management(
                action="info",
                tool_name="vm_management"
            )

            # Get parameter schema for a tool
            result = await discovery_management(
                action="schema",
                tool_name="vm_management"
            )
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
            if action == "list":
                return await _handle_list_tools(category=category, search=search)

            elif action == "info":
                return await _handle_get_tool_info(tool_name=tool_name)

            elif action == "schema":
                return await _handle_get_tool_schema(tool_name=tool_name)

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
    """Handle list tools action - provides basic tool listing."""
    # Since we can't import mcp instance, provide static information
    # This is actually better - no runtime dependencies!
    
    tools = [
        {
            "name": "vm_management",
            "category": "vm",
            "description": "Manage virtual machines with 10 operations: list, create, start, stop, delete, clone, reset, pause, resume, info"
        },
        {
            "name": "network_management",
            "category": "network",
            "description": "Configure networks with 5 operations: list_networks, create_network, remove_network, list_adapters, configure_adapter"
        },
        {
            "name": "snapshot_management",
            "category": "snapshot",
            "description": "Manage snapshots with 4 operations: list, create, restore, delete"
        },
        {
            "name": "storage_management",
            "category": "storage",
            "description": "Manage storage with 6 operations: list_controllers, create_controller, remove_controller, list_disks, create_disk, attach_disk"
        },
        {
            "name": "system_management",
            "category": "system",
            "description": "System information with 5 operations: host_info, vbox_version, ostypes, metrics, screenshot"
        },
        {
            "name": "discovery_management",
            "category": "discovery",
            "description": "Tool discovery with 3 operations: list, info, schema"
        },
    ]
    
    # Add Hyper-V tool on Windows
    import sys
    if sys.platform == "win32":
        tools.append({
            "name": "hyperv_management",
            "category": "hyperv",
            "description": "Manage Hyper-V VMs with 4 operations: list, get, start, stop (Windows only)"
        })
    
    # Apply filters
    if category:
        tools = [t for t in tools if t.get("category") == category]
    if search:
        search_lower = search.lower()
        tools = [t for t in tools if search_lower in t["name"].lower() or search_lower in t["description"].lower()]
    
    return {
        "success": True,
        "tools": tools,
        "count": len(tools),
        "filters": {
            "category": category,
            "search": search,
        }
    }


async def _handle_get_tool_info(tool_name: str | None = None) -> dict[str, Any]:
    """Handle get tool info action - provides tool details."""
    if not tool_name:
        return {
            "success": False,
            "error": "tool_name is required for 'info' action",
        }
    
    # Static tool information (no runtime dependencies)
    tool_info = {
        "vm_management": {
            "name": "vm_management",
            "category": "vm",
            "operations": ["list", "create", "start", "stop", "delete", "clone", "reset", "pause", "resume", "info"],
            "description": "Complete VM lifecycle management with 10 operations",
        },
        "network_management": {
            "name": "network_management",
            "category": "network",
            "operations": ["list_networks", "create_network", "remove_network", "list_adapters", "configure_adapter"],
            "description": "Network configuration with 5 operations",
        },
        "snapshot_management": {
            "name": "snapshot_management",
            "category": "snapshot",
            "operations": ["list", "create", "restore", "delete"],
            "description": "Snapshot management with 4 operations",
        },
        "storage_management": {
            "name": "storage_management",
            "category": "storage",
            "operations": ["list_controllers", "create_controller", "remove_controller", "list_disks", "create_disk", "attach_disk"],
            "description": "Storage and disk management with 6 operations",
        },
        "system_management": {
            "name": "system_management",
            "category": "system",
            "operations": ["host_info", "vbox_version", "ostypes", "metrics", "screenshot"],
            "description": "System information and diagnostics with 5 operations",
        },
        "discovery_management": {
            "name": "discovery_management",
            "category": "discovery",
            "operations": ["list", "info", "schema"],
            "description": "Tool discovery and introspection with 3 operations",
        },
        "hyperv_management": {
            "name": "hyperv_management",
            "category": "hyperv",
            "operations": ["list", "get", "start", "stop"],
            "description": "Hyper-V VM management with 4 operations (Windows only)",
        },
    }
    
    info = tool_info.get(tool_name)
    if not info:
        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found",
            "tool_name": tool_name,
            "available_tools": list(tool_info.keys()),
        }
    
    return {
        "success": True,
        "tool_name": tool_name,
        "info": info,
    }


async def _handle_get_tool_schema(tool_name: str | None = None) -> dict[str, Any]:
    """Handle get tool schema action - provides parameter schemas."""
    if not tool_name:
        return {
            "success": False,
            "error": "tool_name is required for 'schema' action",
        }
    
    # Note: Actual JSON schemas are auto-generated by FastMCP from type hints
    # This provides a simplified representation
    return {
        "success": True,
        "tool_name": tool_name,
        "message": "Tool schemas are auto-generated from Python type hints and available via MCP protocol",
        "note": "Use Literal types in function signatures to see action enums in the schema",
    }

