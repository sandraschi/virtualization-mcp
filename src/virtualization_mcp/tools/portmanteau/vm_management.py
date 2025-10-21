"""
VM Management Portmanteau Tool

Consolidates all VM-related operations into a single tool with action-based interface.
Replaces 11 individual VM tools with one comprehensive tool.
"""

import logging
from typing import Any, Literal

from fastmcp import FastMCP

# Import existing VM tools
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

# Define available actions
VM_ACTIONS = {
    "list": "List all virtual machines",
    "create": "Create a new virtual machine",
    "start": "Start a virtual machine",
    "stop": "Stop a running virtual machine",
    "delete": "Delete a virtual machine",
    "clone": "Clone a virtual machine",
    "reset": "Reset a virtual machine",
    "pause": "Pause a virtual machine",
    "resume": "Resume a paused virtual machine",
    "info": "Get detailed information about a virtual machine",
}


def register_vm_management_tool(mcp: FastMCP) -> None:
    """Register the VM management portmanteau tool."""

    @mcp.tool()
    async def vm_management(
        action: Literal["list", "create", "start", "stop", "delete", "clone", "reset", "pause", "resume", "info"],
        vm_name: str | None = None,
        source_vm: str | None = None,
        new_vm_name: str | None = None,
        os_type: str | None = None,
        memory_mb: int | None = None,
        disk_size_gb: int | None = None,
    ) -> dict[str, Any]:
        """
        Manage virtual machines with various actions.

        Args:
            action: The operation to perform. Available actions:
                - list: List all VMs (no vm_name required)
                - create: Create a new VM (requires vm_name, os_type, memory_mb, disk_size_gb)
                - start: Start a VM (requires vm_name)
                - stop: Stop a VM (requires vm_name)
                - delete: Delete a VM (requires vm_name)
                - clone: Clone a VM (requires source_vm, new_vm_name)
                - reset: Reset a VM (requires vm_name)
                - pause: Pause a VM (requires vm_name)
                - resume: Resume a VM (requires vm_name)
                - info: Get VM information (requires vm_name)

            vm_name: Name of the virtual machine
            source_vm: Source VM name for cloning
            new_vm_name: New VM name for cloning
            os_type: Operating system type (e.g., "Windows10_64", "Ubuntu_64")
            memory_mb: Memory in MB for new VMs
            disk_size_gb: Disk size in GB for new VMs

        Returns:
            Dict containing the result of the operation

        Examples:
            # List all VMs
            result = await vm_management(action="list")

            # Create a new VM
            result = await vm_management(
                action="create",
                vm_name="MyVM",
                os_type="Windows10_64",
                memory_mb=4096,
                disk_size_gb=50
            )

            # Start a VM
            result = await vm_management(action="start", vm_name="MyVM")

            # Get VM info
            result = await vm_management(action="info", vm_name="MyVM")
        """
        try:
            # Validate action
            if action not in VM_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(VM_ACTIONS.keys())}",
                    "available_actions": VM_ACTIONS,
                }

            logger.info(f"Executing VM management action: {action}")

            # Route to appropriate function based on action
            if action == "list":
                return await _handle_list_vms()

            elif action == "create":
                return await _handle_create_vm(
                    vm_name=vm_name,
                    os_type=os_type,
                    memory_mb=memory_mb,
                    disk_size_gb=disk_size_gb,
                )

            elif action == "start":
                return await _handle_start_vm(vm_name=vm_name)

            elif action == "stop":
                return await _handle_stop_vm(vm_name=vm_name)

            elif action == "delete":
                return await _handle_delete_vm(vm_name=vm_name)

            elif action == "clone":
                return await _handle_clone_vm(
                    source_vm=source_vm, new_vm_name=new_vm_name
                )

            elif action == "reset":
                return await _handle_reset_vm(vm_name=vm_name)

            elif action == "pause":
                return await _handle_pause_vm(vm_name=vm_name)

            elif action == "resume":
                return await _handle_resume_vm(vm_name=vm_name)

            elif action == "info":
                return await _handle_get_vm_info(vm_name=vm_name)

            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                    "available_actions": VM_ACTIONS,
                }

        except Exception as e:
            logger.error(f"Error in VM management action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute action '{action}': {str(e)}",
                "action": action,
                "available_actions": VM_ACTIONS,
            }


async def _handle_list_vms() -> dict[str, Any]:
    """Handle list VMs action."""
    try:
        result = await list_vms()
        return {
            "success": True,
            "action": "list",
            "data": result,
            "count": len(result) if isinstance(result, list) else 0,
        }
    except Exception as e:
        return {"success": False, "action": "list", "error": f"Failed to list VMs: {str(e)}"}


async def _handle_create_vm(
    vm_name: str | None = None,
    os_type: str | None = None,
    memory_mb: int | None = None,
    disk_size_gb: int | None = None,
) -> dict[str, Any]:
    """Handle create VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "create",
            "error": "vm_name is required for create action",
        }

    if not os_type:
        return {
            "success": False,
            "action": "create",
            "error": "os_type is required for create action",
        }

    try:
        result = await create_vm(
            vm_name=vm_name,
            os_type=os_type,
            memory_mb=memory_mb or 1024,
            disk_size_gb=disk_size_gb or 20,
        )
        return {"success": True, "action": "create", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "create",
            "vm_name": vm_name,
            "error": f"Failed to create VM: {str(e)}",
        }


async def _handle_start_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle start VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "start",
            "error": "vm_name is required for start action",
        }

    try:
        result = await start_vm(vm_name=vm_name)
        return {"success": True, "action": "start", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "start",
            "vm_name": vm_name,
            "error": f"Failed to start VM: {str(e)}",
        }


async def _handle_stop_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle stop VM action."""
    if not vm_name:
        return {"success": False, "action": "stop", "error": "vm_name is required for stop action"}

    try:
        result = await stop_vm(vm_name=vm_name)
        return {"success": True, "action": "stop", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "stop",
            "vm_name": vm_name,
            "error": f"Failed to stop VM: {str(e)}",
        }


async def _handle_delete_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle delete VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "delete",
            "error": "vm_name is required for delete action",
        }

    try:
        result = await delete_vm(vm_name=vm_name)
        return {"success": True, "action": "delete", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "delete",
            "vm_name": vm_name,
            "error": f"Failed to delete VM: {str(e)}",
        }


async def _handle_clone_vm(
    source_vm: str | None = None, new_vm_name: str | None = None
) -> dict[str, Any]:
    """Handle clone VM action."""
    if not source_vm:
        return {
            "success": False,
            "action": "clone",
            "error": "source_vm is required for clone action",
        }

    if not new_vm_name:
        return {
            "success": False,
            "action": "clone",
            "error": "new_vm_name is required for clone action",
        }

    try:
        result = await clone_vm(source_vm=source_vm, new_vm_name=new_vm_name)
        return {
            "success": True,
            "action": "clone",
            "source_vm": source_vm,
            "new_vm_name": new_vm_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "clone",
            "source_vm": source_vm,
            "new_vm_name": new_vm_name,
            "error": f"Failed to clone VM: {str(e)}",
        }


async def _handle_reset_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle reset VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "reset",
            "error": "vm_name is required for reset action",
        }

    try:
        result = await reset_vm(vm_name=vm_name)
        return {"success": True, "action": "reset", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "reset",
            "vm_name": vm_name,
            "error": f"Failed to reset VM: {str(e)}",
        }


async def _handle_pause_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle pause VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "pause",
            "error": "vm_name is required for pause action",
        }

    try:
        result = await pause_vm(vm_name=vm_name)
        return {"success": True, "action": "pause", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "pause",
            "vm_name": vm_name,
            "error": f"Failed to pause VM: {str(e)}",
        }


async def _handle_resume_vm(vm_name: str | None = None) -> dict[str, Any]:
    """Handle resume VM action."""
    if not vm_name:
        return {
            "success": False,
            "action": "resume",
            "error": "vm_name is required for resume action",
        }

    try:
        result = await resume_vm(vm_name=vm_name)
        return {"success": True, "action": "resume", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "resume",
            "vm_name": vm_name,
            "error": f"Failed to resume VM: {str(e)}",
        }


async def _handle_get_vm_info(vm_name: str | None = None) -> dict[str, Any]:
    """Handle get VM info action."""
    if not vm_name:
        return {"success": False, "action": "info", "error": "vm_name is required for info action"}

    try:
        result = await get_vm_info(vm_name=vm_name)
        return {"success": True, "action": "info", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "info",
            "vm_name": vm_name,
            "error": f"Failed to get VM info: {str(e)}",
        }
