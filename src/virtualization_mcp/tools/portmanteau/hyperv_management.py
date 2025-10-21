"""
Hyper-V Management Portmanteau Tool

Consolidates all Hyper-V related operations into a single tool.
Provides Windows Hyper-V VM management capabilities.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Define available actions
HYPERV_ACTIONS = {
    "list": "List all Hyper-V virtual machines",
    "get": "Get detailed information about a Hyper-V VM",
    "start": "Start a Hyper-V virtual machine",
    "stop": "Stop a Hyper-V virtual machine",
}


def register_hyperv_management_tool(mcp: FastMCP) -> None:
    """Register the Hyper-V management portmanteau tool."""

    @mcp.tool()
    async def hyperv_management(
        action: Literal["list", "get", "start", "stop"],
        vm_name: str | None = None,
        force: bool = False,
        wait: bool = False,
    ) -> dict[str, Any]:
        """
        Manage Hyper-V virtual machines with various actions (Windows only).

        Args:
            action: The operation to perform. Available actions:
                - list: List all Hyper-V VMs (no vm_name required)
                - get: Get detailed info about a VM (requires vm_name)
                - start: Start a VM (requires vm_name, optional: wait)
                - stop: Stop a VM (requires vm_name, optional: force, wait)

            vm_name: Name of the Hyper-V virtual machine (required for get, start, stop)
            force: Force stop without graceful shutdown (for stop action)
            wait: Wait for operation to complete before returning

        Returns:
            Dict containing the result of the operation

        Examples:
            # List all Hyper-V VMs
            result = await hyperv_management(action="list")

            # Get VM information
            result = await hyperv_management(
                action="get",
                vm_name="MyHyperVVM"
            )

            # Start a VM
            result = await hyperv_management(
                action="start",
                vm_name="MyHyperVVM",
                wait=True
            )

            # Stop a VM gracefully
            result = await hyperv_management(
                action="stop",
                vm_name="MyHyperVVM",
                wait=True
            )

            # Force stop a VM
            result = await hyperv_management(
                action="stop",
                vm_name="MyHyperVVM",
                force=True
            )
        """
        try:
            # Validate action
            if action not in HYPERV_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(HYPERV_ACTIONS.keys())}",
                    "available_actions": HYPERV_ACTIONS,
                }

            logger.info(f"Executing Hyper-V management action: {action}")

            # Route to appropriate function based on action
            if action == "list":
                return await _handle_list_vms()

            elif action == "get":
                return await _handle_get_vm(vm_name=vm_name)

            elif action == "start":
                return await _handle_start_vm(vm_name=vm_name, wait=wait)

            elif action == "stop":
                return await _handle_stop_vm(vm_name=vm_name, force=force, wait=wait)

            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                }

        except Exception as e:
            logger.error(f"Hyper-V management error for action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Hyper-V operation failed: {str(e)}",
                "action": action,
            }


async def _handle_list_vms() -> dict[str, Any]:
    """Handle list VMs action."""
    try:
        from virtualization_mcp.tools.vm.hyperv_tools import list_hyperv_vms
        
        vms = await list_hyperv_vms()
        
        return {
            "success": True,
            "action": "list",
            "vms": vms,
            "count": len(vms),
        }
    except Exception as e:
        logger.error(f"Failed to list Hyper-V VMs: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def _handle_get_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle get VM action."""
    if not vm_name:
        return {
            "success": False,
            "error": "vm_name is required for 'get' action",
        }
    
    try:
        from virtualization_mcp.tools.vm.hyperv_tools import get_hyperv_vm
        
        vm_info = await get_hyperv_vm(vm_name)
        
        if vm_info is None:
            return {
                "success": False,
                "error": f"Hyper-V VM '{vm_name}' not found",
                "vm_name": vm_name,
            }
        
        return {
            "success": True,
            "action": "get",
            "vm_name": vm_name,
            "vm_info": vm_info,
        }
    except Exception as e:
        logger.error(f"Failed to get Hyper-V VM '{vm_name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": vm_name,
        }


async def _handle_start_vm(vm_name: str | None = None, wait: bool = False) -> dict[str, Any]:
    """Handle start VM action."""
    if not vm_name:
        return {
            "success": False,
            "error": "vm_name is required for 'start' action",
        }
    
    try:
        from virtualization_mcp.tools.vm.hyperv_tools import start_hyperv_vm
        
        result = await start_hyperv_vm(vm_name, wait=wait)
        
        return {
            "success": True,
            "action": "start",
            "vm_name": vm_name,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Failed to start Hyper-V VM '{vm_name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": vm_name,
        }


async def _handle_stop_vm(vm_name: str | None = None, force: bool = False, wait: bool = False) -> dict[str, Any]:
    """Handle stop VM action."""
    if not vm_name:
        return {
            "success": False,
            "error": "vm_name is required for 'stop' action",
        }
    
    try:
        from virtualization_mcp.tools.vm.hyperv_tools import stop_hyperv_vm
        
        result = await stop_hyperv_vm(vm_name, force=force, wait=wait)
        
        return {
            "success": True,
            "action": "stop",
            "vm_name": vm_name,
            "force": force,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Failed to stop Hyper-V VM '{vm_name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "vm_name": vm_name,
        }

