"""
Info Tools Portmanteau Tool

Consolidates help, status, and tool discovery tools into one interface.
This is SEPARATE from MCP protocol's native tools/list - these are
application-specific help and introspection tools.
"""

import logging
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from virtualization_mcp.config import settings
from virtualization_mcp.tools.portmanteau.network_management import NETWORK_ACTIONS
from virtualization_mcp.tools.portmanteau.snapshot_management import SNAPSHOT_ACTIONS
from virtualization_mcp.tools.portmanteau.storage_management import STORAGE_ACTIONS
from virtualization_mcp.tools.portmanteau.system_management import SYSTEM_ACTIONS
from virtualization_mcp.tools.portmanteau.vm_management import VM_ACTIONS

logger = logging.getLogger(__name__)

# Define available actions
INFO_ACTIONS = {
    "list_tools": "List all available virtualization-mcp tools",
    "tool_info": "Get detailed information about a specific tool",
    "tool_schema": "Get JSON schema for a tool's parameters",
    "help": "Get help information",
}


def register_info_tools_tool(mcp: FastMCP) -> None:
    """Register the info tools portmanteau tool."""

    @mcp.tool()
    async def info_tools(
        action: Annotated[
            Literal["list_tools", "tool_info", "tool_schema", "help"],
            Field(description="Discovery operation to perform."),
        ],
        tool_name: Annotated[str | None, Field(description="Tool name (tool_info, tool_schema).")] = None,
        category: Annotated[
            str | None,
            Field(
                description="Category filter: vm, network, snapshot, storage, system, discovery, hyperv (list_tools)."
            ),
        ] = None,
        search: Annotated[str | None, Field(description="Search term (list_tools).")] = None,
    ) -> dict[str, Any]:
        """Comprehensive tool discovery and help portmanteau tool.

        App-specific help and introspection (separate from MCP protocol's native
        tools/list — clients get schemas automatically; this is for users).

        ## Return Format

        Dict with `success` (bool), human-readable `message`, the `action` performed,
        and per-action data (`tools`+`count`, `info`, `help`). Failures carry a
        human-readable `error`.

        ## Examples

        ```python
        await info_tools(action="list_tools")
        await info_tools(action="list_tools", category="vm")
        await info_tools(action="tool_info", tool_name="vm_management")
        await info_tools(action="tool_schema", tool_name="snapshot_management")
        await info_tools(action="help")
        ```
        """
        try:
            # Validate action
            if action not in INFO_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(INFO_ACTIONS.keys())}",
                    "available_actions": INFO_ACTIONS,
                }

            logger.info(f"Executing info tools action: {action}")

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
            logger.error(f"Info tools error for action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Info tools operation failed: {e!s}",
                "action": action,
            }


async def _handle_list_tools(category: str | None = None, search: str | None = None) -> dict[str, Any]:
    """Handle list_tools action with runtime-derived operation lists."""
    try:
        portmanteau = [
            {"name": "vm_management", "operations": sorted(list(VM_ACTIONS.keys())), "category": "vm"},
            {"name": "network_management", "operations": sorted(list(NETWORK_ACTIONS.keys())), "category": "network"},
            {
                "name": "snapshot_management",
                "operations": sorted(list(SNAPSHOT_ACTIONS.keys())),
                "category": "snapshot",
            },
            {"name": "storage_management", "operations": sorted(list(STORAGE_ACTIONS.keys())), "category": "storage"},
            {"name": "system_management", "operations": sorted(list(SYSTEM_ACTIONS.keys())), "category": "system"},
            {"name": "info_tools", "operations": sorted(list(INFO_ACTIONS.keys())), "category": "discovery"},
            {"name": "hyperv_management", "operations": ["list", "get", "start", "stop"], "category": "hyperv"},
        ]
        items = portmanteau
        if category:
            items = [item for item in items if item["category"] == category.lower()]
        if search:
            needle = search.lower().strip()
            items = [
                item
                for item in items
                if needle in item["name"].lower() or any(needle in op.lower() for op in item["operations"])
            ]

        tools = {
            "portmanteau": items,
            "individual_tools_enabled": bool(settings.TOOL_MODE.lower() in ["testing", "all"]),
        }

        return {
            "success": True,
            "tools": tools,
            "count": len(items),
            "tool_mode": settings.TOOL_MODE,
            "note": "Set TOOL_MODE=testing or TOOL_MODE=all to expose individual legacy tools.",
        }

    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return {"success": False, "error": str(e)}


async def _handle_tool_info(tool_name: str | None = None) -> dict[str, Any]:
    """Handle tool_info action."""
    if not tool_name:
        return {"success": False, "error": "tool_name required for tool_info"}

    tool_info_map: dict[str, dict[str, Any]] = {
        "vm_management": {
            "type": "portmanteau",
            "operations": sorted(list(VM_ACTIONS.keys())),
            "description": "Complete VM lifecycle management",
        },
        "network_management": {
            "type": "portmanteau",
            "operations": sorted(list(NETWORK_ACTIONS.keys())),
            "description": "Network configuration",
        },
        "snapshot_management": {
            "type": "portmanteau",
            "operations": sorted(list(SNAPSHOT_ACTIONS.keys())),
            "description": "Snapshot management",
        },
        "storage_management": {
            "type": "portmanteau",
            "operations": sorted(list(STORAGE_ACTIONS.keys())),
            "description": "Storage management",
        },
        "system_management": {
            "type": "portmanteau",
            "operations": sorted(list(SYSTEM_ACTIONS.keys())),
            "description": "System information",
        },
        "info_tools": {
            "type": "portmanteau",
            "operations": sorted(list(INFO_ACTIONS.keys())),
            "description": "Runtime tool discovery and help surface",
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
        "note": "All portmanteau tools use Literal types for action enums in the schema",
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
                "testing": "60+ individual tools + portmanteau",
            },
            "portmanteau_tools": [
                "vm_management",
                "network_management",
                "snapshot_management",
                "storage_management",
                "system_management",
                "hyperv_management (Windows)",
            ],
            "documentation": "See docs/ directory for comprehensive guides",
            "quick_start": f"Current TOOL_MODE={settings.TOOL_MODE}. Use production for clean UI or testing/all for legacy individual tools.",
        },
    }
