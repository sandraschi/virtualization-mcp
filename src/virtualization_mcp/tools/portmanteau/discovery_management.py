"""
Discovery Management Portmanteau Tool

Consolidates all tool discovery and introspection operations.
Helps users and AI assistants discover available tools and their capabilities.
"""

import logging
from typing import Any

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
        action: str,
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
    """Handle list tools action."""
    try:
        from virtualization_mcp.mcp_tools import MCPToolDiscovery
        from virtualization_mcp.all_tools_server import mcp
        
        discovery = MCPToolDiscovery(mcp)
        tools = discovery.list_tools(category=category, search=search)
        
        return {
            "success": True,
            "tools": tools,
            "count": len(tools),
            "filters": {
                "category": category,
                "search": search,
            }
        }
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def _handle_get_tool_info(tool_name: str | None = None) -> dict[str, Any]:
    """Handle get tool info action."""
    if not tool_name:
        return {
            "success": False,
            "error": "tool_name is required for 'info' action",
        }
    
    try:
        from virtualization_mcp.mcp_tools import MCPToolDiscovery
        from virtualization_mcp.all_tools_server import mcp
        
        discovery = MCPToolDiscovery(mcp)
        info = discovery.get_tool_info(tool_name)
        
        return {
            "success": True,
            "tool_name": tool_name,
            "info": info,
        }
    except Exception as e:
        logger.error(f"Failed to get tool info for '{tool_name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
        }


async def _handle_get_tool_schema(tool_name: str | None = None) -> dict[str, Any]:
    """Handle get tool schema action."""
    if not tool_name:
        return {
            "success": False,
            "error": "tool_name is required for 'schema' action",
        }
    
    try:
        from virtualization_mcp.mcp_tools import MCPToolDiscovery
        from virtualization_mcp.all_tools_server import mcp
        
        discovery = MCPToolDiscovery(mcp)
        schema = discovery.get_tool_schema(tool_name)
        
        return {
            "success": True,
            "tool_name": tool_name,
            "schema": schema,
        }
    except Exception as e:
        logger.error(f"Failed to get tool schema for '{tool_name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
        }

