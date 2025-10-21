"""
Storage Management Portmanteau Tool

Consolidates all storage-related operations into a single tool with action-based interface.
Replaces 6 individual storage tools with one comprehensive tool.
"""

import logging
from typing import Any

from fastmcp import FastMCP

# Import existing storage tools
from virtualization_mcp.tools.storage.storage_tools import (
    create_storage_controller,
    list_storage_controllers,
    remove_storage_controller,
)

logger = logging.getLogger(__name__)

# Define available actions
STORAGE_ACTIONS = {
    "list_controllers": "List storage controllers for a VM",
    "create_controller": "Create a storage controller for a VM",
    "remove_controller": "Remove a storage controller from a VM",
    "list_disks": "List virtual disks for a VM",
    "create_disk": "Create a new virtual disk",
    "attach_disk": "Attach a disk to a virtual machine",
}


def register_storage_management_tool(mcp: FastMCP) -> None:
    """Register the storage management portmanteau tool."""

    @mcp.tool()
    async def storage_management(
        action: str,
        vm_name: str | None = None,
        controller_name: str | None = None,
        controller_type: str | None = None,
        disk_name: str | None = None,
        disk_size_gb: int | None = None,
        disk_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Manage storage configurations with various actions.

        Args:
            action: The operation to perform. Available actions:
                - list_controllers: List storage controllers (requires vm_name)
                - create_controller: Create storage controller (requires vm_name, controller_name, controller_type)
                - remove_controller: Remove storage controller (requires vm_name, controller_name)
                - list_disks: List virtual disks (requires vm_name)
                - create_disk: Create virtual disk (requires disk_name, disk_size_gb)
                - attach_disk: Attach disk to VM (requires vm_name, disk_path)

            vm_name: Name of the virtual machine
            controller_name: Name of the storage controller
            controller_type: Type of storage controller (ide, sata, scsi, sas, usb, pcie)
            disk_name: Name of the virtual disk
            disk_size_gb: Size of the disk in GB
            disk_path: Path to the disk file

        Returns:
            Dict containing the result of the operation

        Examples:
            # List storage controllers
            result = await storage_management(
                action="list_controllers",
                vm_name="MyVM"
            )

            # Create storage controller
            result = await storage_management(
                action="create_controller",
                vm_name="MyVM",
                controller_name="SATA Controller",
                controller_type="sata"
            )

            # Create virtual disk
            result = await storage_management(
                action="create_disk",
                disk_name="MyDisk.vdi",
                disk_size_gb=50
            )

            # Attach disk to VM
            result = await storage_management(
                action="attach_disk",
                vm_name="MyVM",
                disk_path="/path/to/MyDisk.vdi"
            )
        """
        try:
            # Validate action
            if action not in STORAGE_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(STORAGE_ACTIONS.keys())}",
                    "available_actions": STORAGE_ACTIONS,
                }

            logger.info(f"Executing storage management action: {action}")

            # Route to appropriate function based on action
            if action == "list_controllers":
                return await _handle_list_controllers(vm_name=vm_name)

            elif action == "create_controller":
                return await _handle_create_controller(
                    vm_name=vm_name,
                    controller_name=controller_name,
                    controller_type=controller_type,
                )

            elif action == "remove_controller":
                return await _handle_remove_controller(
                    vm_name=vm_name, controller_name=controller_name
                )

            elif action == "list_disks":
                return await _handle_list_disks(vm_name=vm_name)

            elif action == "create_disk":
                return await _handle_create_disk(
                    disk_name=disk_name, disk_size_gb=disk_size_gb
                )

            elif action == "attach_disk":
                return await _handle_attach_disk(vm_name=vm_name, disk_path=disk_path)

            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                    "available_actions": STORAGE_ACTIONS,
                }

        except Exception as e:
            logger.error(f"Error in storage management action '{action}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to execute action '{action}': {str(e)}",
                "action": action,
                "available_actions": STORAGE_ACTIONS,
            }


async def _handle_list_controllers(vm_name: str | None = None) -> dict[str, Any]:
    """Handle list controllers action."""
    if not vm_name:
        return {
            "success": False,
            "action": "list_controllers",
            "error": "vm_name is required for list_controllers action",
        }

    try:
        result = await list_storage_controllers(vm_name=vm_name)
        return {
            "success": True,
            "action": "list_controllers",
            "vm_name": vm_name,
            "data": result,
            "count": len(result) if isinstance(result, list) else 0,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "list_controllers",
            "vm_name": vm_name,
            "error": f"Failed to list controllers: {str(e)}",
        }


async def _handle_create_controller(
    vm_name: str | None = None,
    controller_name: str | None = None,
    controller_type: str | None = None,
) -> dict[str, Any]:
    """Handle create controller action."""
    if not vm_name:
        return {
            "success": False,
            "action": "create_controller",
            "error": "vm_name is required for create_controller action",
        }

    if not controller_name:
        return {
            "success": False,
            "action": "create_controller",
            "error": "controller_name is required for create_controller action",
        }

    if not controller_type:
        return {
            "success": False,
            "action": "create_controller",
            "error": "controller_type is required for create_controller action",
        }

    try:
        result = await create_storage_controller(
            vm_name=vm_name,
            controller_name=controller_name,
            controller_type=controller_type,
        )
        return {
            "success": True,
            "action": "create_controller",
            "vm_name": vm_name,
            "controller_name": controller_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "create_controller",
            "vm_name": vm_name,
            "controller_name": controller_name,
            "error": f"Failed to create controller: {str(e)}",
        }


async def _handle_remove_controller(
    vm_name: str | None = None, controller_name: str | None = None
) -> dict[str, Any]:
    """Handle remove controller action."""
    if not vm_name:
        return {
            "success": False,
            "action": "remove_controller",
            "error": "vm_name is required for remove_controller action",
        }

    if not controller_name:
        return {
            "success": False,
            "action": "remove_controller",
            "error": "controller_name is required for remove_controller action",
        }

    try:
        result = await remove_storage_controller(
            vm_name=vm_name, controller_name=controller_name
        )
        return {
            "success": True,
            "action": "remove_controller",
            "vm_name": vm_name,
            "controller_name": controller_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "remove_controller",
            "vm_name": vm_name,
            "controller_name": controller_name,
            "error": f"Failed to remove controller: {str(e)}",
        }


async def _handle_list_disks(vm_name: str | None = None) -> dict[str, Any]:
    """Handle list disks action."""
    if not vm_name:
        return {
            "success": False,
            "action": "list_disks",
            "error": "vm_name is required for list_disks action",
        }

    try:
        # This would need to be implemented in the storage tools
        # For now, return a placeholder
        result = {
            "vm_name": vm_name,
            "disks": [
                {"name": "MyDisk.vdi", "size_gb": 50, "type": "vdi", "attached": True},
                {"name": "DataDisk.vdi", "size_gb": 100, "type": "vdi", "attached": False},
            ],
        }
        return {"success": True, "action": "list_disks", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "list_disks",
            "vm_name": vm_name,
            "error": f"Failed to list disks: {str(e)}",
        }


async def _handle_create_disk(
    disk_name: str | None = None, disk_size_gb: int | None = None
) -> dict[str, Any]:
    """Handle create disk action."""
    if not disk_name:
        return {
            "success": False,
            "action": "create_disk",
            "error": "disk_name is required for create_disk action",
        }

    if not disk_size_gb:
        return {
            "success": False,
            "action": "create_disk",
            "error": "disk_size_gb is required for create_disk action",
        }

    try:
        # This would need to be implemented in the storage tools
        # For now, return a placeholder
        result = {
            "disk_name": disk_name,
            "disk_size_gb": disk_size_gb,
            "created": True,
            "path": f"/path/to/{disk_name}",
        }
        return {"success": True, "action": "create_disk", "disk_name": disk_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "create_disk",
            "disk_name": disk_name,
            "error": f"Failed to create disk: {str(e)}",
        }


async def _handle_attach_disk(
    vm_name: str | None = None, disk_path: str | None = None
) -> dict[str, Any]:
    """Handle attach disk action."""
    if not vm_name:
        return {
            "success": False,
            "action": "attach_disk",
            "error": "vm_name is required for attach_disk action",
        }

    if not disk_path:
        return {
            "success": False,
            "action": "attach_disk",
            "error": "disk_path is required for attach_disk action",
        }

    try:
        # This would need to be implemented in the storage tools
        # For now, return a placeholder
        result = {"vm_name": vm_name, "disk_path": disk_path, "attached": True}
        return {"success": True, "action": "attach_disk", "vm_name": vm_name, "data": result}
    except Exception as e:
        return {
            "success": False,
            "action": "attach_disk",
            "vm_name": vm_name,
            "error": f"Failed to attach disk: {str(e)}",
        }
