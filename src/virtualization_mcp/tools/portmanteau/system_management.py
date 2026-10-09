"""
System Management Portmanteau Tool

Consolidates all system-related operations into a single tool with action-based interface.
Replaces 5 individual system tools with one comprehensive tool.
"""

import logging
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

# Import existing system tools
from virtualization_mcp.tools.system.system_tools import (
    get_system_info,
    get_vbox_version,
    get_vm_metrics,
    list_ostypes,
    take_vm_screenshot,
)

logger = logging.getLogger(__name__)

# Define available actions
SYSTEM_ACTIONS = {
    "host_info": "Get host system information",
    "vbox_version": "Get VirtualBox version information",
    "ostypes": "List available OS types",
    "metrics": "Get VM performance metrics",
    "screenshot": "Take a screenshot of a running VM",
}


def register_system_management_tool(mcp: FastMCP) -> None:
    """Register the system management portmanteau tool."""

    @mcp.tool()
    async def system_management(
        action: Annotated[
            Literal["host_info", "vbox_version", "ostypes", "metrics", "screenshot"],
            Field(description="System operation to perform."),
        ],
        vm_name: Annotated[str | None, Field(description="VM name (metrics and screenshot only).")] = None,
        output_file: Annotated[str | None, Field(description="Screenshot output path (screenshot).")] = None,
        width: Annotated[int | None, Field(description="Screenshot width (screenshot).")] = None,
        height: Annotated[int | None, Field(description="Screenshot height (screenshot).")] = None,
    ) -> dict[str, Any]:
        """Comprehensive system management portmanteau tool.

        Consolidates system information and diagnostics operations into a single
        interface. Most actions need no `vm_name`.

        ## Return Format

        Dict with `success` (bool), human-readable `message`, the `action` performed,
        and operation data (system info, version, OS types, metrics, screenshot path).
        Failures carry a human-readable `error`.

        ## Examples

        ```python
        await system_management(action="host_info")
        await system_management(action="vbox_version")
        await system_management(action="ostypes")
        await system_management(action="metrics", vm_name="MyVM")
        await system_management(action="screenshot", vm_name="MyVM")
        ```
        """
        try:
            # Validate action
            if action not in SYSTEM_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(SYSTEM_ACTIONS.keys())}",
                    "available_actions": SYSTEM_ACTIONS,
                }

            logger.info(f"Executing system management action: {action}")

            # Route to appropriate function based on action
            if action == "host_info":
                return await _handle_host_info()

            elif action == "vbox_version":
                return await _handle_vbox_version()

            elif action == "ostypes":
                return await _handle_ostypes()

            elif action == "metrics":
                return await _handle_metrics(vm_name=vm_name)

            elif action == "screenshot":
                return await _handle_screenshot(vm_name=vm_name, output_file=output_file, width=width, height=height)

            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                    "available_actions": SYSTEM_ACTIONS,
                }

        except Exception as e:
            logger.error(f"Error in system management action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute action '{action}': {e!s}",
                "action": action,
                "available_actions": SYSTEM_ACTIONS,
            }


async def _handle_host_info() -> dict[str, Any]:
    """Handle host info action."""
    try:
        result = await get_system_info()
        return {"success": True, "action": "host_info", "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "host_info",
            "error": f"Failed to get host info: {e!s}",
        }


async def _handle_vbox_version() -> dict[str, Any]:
    """Handle vbox version action."""
    try:
        result = await get_vbox_version()
        return {"success": True, "action": "vbox_version", "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "vbox_version",
            "error": f"Failed to get VirtualBox version: {e!s}",
        }


async def _handle_ostypes() -> dict[str, Any]:
    """Handle ostypes action."""
    try:
        result = await list_ostypes()
        return {
            "success": True,
            "action": "ostypes",
            "data": result,
            "count": len(result) if isinstance(result, list) else 0,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "ostypes",
            "error": f"Failed to list OS types: {e!s}",
        }


async def _handle_metrics(vm_name: str | None = None) -> dict[str, Any]:
    """Handle metrics action."""
    if not vm_name:
        return {
            "success": False,
            "action": "metrics",
            "error": "vm_name is required for metrics action",
        }

    try:
        result = await get_vm_metrics(vm_name=vm_name)
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "metrics",
            "vm_name": vm_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "metrics",
            "vm_name": vm_name,
            "error": f"Failed to get metrics: {e!s}",
        }


async def _handle_screenshot(
    vm_name: str | None = None,
    output_file: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> dict[str, Any]:
    """Handle screenshot action."""
    if not vm_name:
        return {
            "success": False,
            "action": "screenshot",
            "error": "vm_name is required for screenshot action",
        }

    try:
        result = await take_vm_screenshot(vm_name=vm_name, output_file=output_file, width=width, height=height)
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "screenshot",
            "vm_name": vm_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "screenshot",
            "vm_name": vm_name,
            "error": f"Failed to take screenshot: {e!s}",
        }
