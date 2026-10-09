"""
Storage Management Portmanteau Tool

Consolidates all storage-related operations into a single tool with action-based interface.
Replaces 6 individual storage tools with one comprehensive tool.
"""

import logging
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from virtualization_mcp.schemas.vbox_types import STORAGE_CONTROLLER_TYPE

# Import existing storage tools
from virtualization_mcp.tools.storage.storage_tools import (
    attach_disk as attach_disk_tool,
)
from virtualization_mcp.tools.storage.storage_tools import (
    create_disk as create_disk_tool,
)
from virtualization_mcp.tools.storage.storage_tools import (
    create_storage_controller,
    list_disks,
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
        action: Annotated[
            Literal[
                "list_controllers", "create_controller", "remove_controller", "list_disks", "create_disk", "attach_disk"
            ],
            Field(description="Storage operation to perform."),
        ],
        vm_name: Annotated[
            str | None,
            Field(
                description="VM name (list_controllers, create_controller, remove_controller, list_disks, attach_disk)."
            ),
        ] = None,
        controller_name: Annotated[
            str | None, Field(description="Controller name (create_controller, remove_controller).")
        ] = None,
        controller_type: Annotated[
            STORAGE_CONTROLLER_TYPE | None,
            Field(description="Controller type (create_controller): ide|sata|scsi|sas|usb|pcie."),
        ] = None,
        disk_name: Annotated[str | None, Field(description="Disk file name (create_disk).")] = None,
        disk_size_gb: Annotated[int | None, Field(description="Disk size in GB (create_disk).")] = None,
        disk_path: Annotated[str | None, Field(description="Disk file path (attach_disk).")] = None,
        limit: Annotated[int, Field(description="Max items for list actions.")] = 100,
        offset: Annotated[int, Field(description="Offset for list pagination.")] = 0,
    ) -> dict[str, Any]:
        """Comprehensive storage management portmanteau tool.

        Consolidates all storage operations into a single interface. Use the `action`
        parameter to specify which operation to perform.

        ## Return Format

        Dict with `success` (bool), human-readable `message`, the `action` performed,
        and operation data (`controllers`, `disks`, `result`). Failures carry a
        human-readable `error`.

        ## Examples

        ```python
        await storage_management(action="list_controllers", vm_name="MyVM")
        await storage_management(action="create_controller", vm_name="MyVM", controller_name="SATA Controller", controller_type="sata")
        await storage_management(action="create_disk", disk_name="MyDisk.vdi", disk_size_gb=50)
        await storage_management(action="attach_disk", vm_name="MyVM", disk_path="/path/to/MyDisk.vdi")
        await storage_management(action="remove_controller", vm_name="MyVM", controller_name="SATA Controller")
        ```
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
                return await _handle_list_controllers(vm_name=vm_name, limit=limit, offset=offset)

            elif action == "create_controller":
                return await _handle_create_controller(
                    vm_name=vm_name,
                    controller_name=controller_name,
                    controller_type=controller_type,
                )

            elif action == "remove_controller":
                return await _handle_remove_controller(vm_name=vm_name, controller_name=controller_name)

            elif action == "list_disks":
                return await _handle_list_disks(vm_name=vm_name, limit=limit, offset=offset)

            elif action == "create_disk":
                return await _handle_create_disk(disk_name=disk_name, disk_size_gb=disk_size_gb)

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
                "error": f"Failed to execute action '{action}': {e!s}",
                "action": action,
                "available_actions": STORAGE_ACTIONS,
            }


def _paginate(items: list[dict[str, Any]], limit: int, offset: int) -> dict[str, Any]:
    lim = max(1, min(int(limit), 500))
    off = max(0, int(offset))
    page = items[off : off + lim]
    return {
        "items": page,
        "count": len(page),
        "total": len(items),
        "limit": lim,
        "offset": off,
        "has_more": off + len(page) < len(items),
    }


async def _handle_list_controllers(vm_name: str | None = None, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """Handle list controllers action."""
    if not vm_name:
        return {
            "success": False,
            "action": "list_controllers",
            "error": "vm_name is required for list_controllers action",
        }

    try:
        result = await list_storage_controllers(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        controllers = result.get("controllers", []) if isinstance(result, dict) else []
        page = _paginate(controllers if isinstance(controllers, list) else [], limit, offset)
        return {
            "success": ok,
            "action": "list_controllers",
            "vm_name": vm_name,
            "data": result,
            "count": page["count"],
            "total": page["total"],
            "limit": page["limit"],
            "offset": page["offset"],
            "has_more": page["has_more"],
            "items": page["items"],
        }
    except Exception as e:
        return {
            "success": False,
            "action": "list_controllers",
            "vm_name": vm_name,
            "error": f"Failed to list controllers: {e!s}",
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
            "success": isinstance(result, dict) and result.get("status") == "success",
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
            "error": f"Failed to create controller: {e!s}",
        }


async def _handle_remove_controller(vm_name: str | None = None, controller_name: str | None = None) -> dict[str, Any]:
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
        result = await remove_storage_controller(vm_name=vm_name, controller_name=controller_name)
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
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
            "error": f"Failed to remove controller: {e!s}",
            "recovery_options": [
                "Detach all media from this controller before removal",
                "List controllers with list_controllers to match controller_name exactly",
                "Power off the VM before storage changes",
            ],
        }


async def _handle_list_disks(vm_name: str | None = None, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """Handle list disks action."""
    if not vm_name:
        return {
            "success": False,
            "action": "list_disks",
            "error": "vm_name is required for list_disks action",
        }

    try:
        result = await list_disks(vm_name=vm_name)
        ok = isinstance(result, dict) and result.get("status") == "success"
        disks = result.get("disks", []) if isinstance(result, dict) else []
        page = _paginate(disks if isinstance(disks, list) else [], limit, offset)
        return {
            "success": ok,
            "action": "list_disks",
            "vm_name": vm_name,
            "data": result,
            "count": page["count"],
            "total": page["total"],
            "limit": page["limit"],
            "offset": page["offset"],
            "has_more": page["has_more"],
            "items": page["items"],
        }
    except Exception as e:
        return {
            "success": False,
            "action": "list_disks",
            "vm_name": vm_name,
            "error": f"Failed to list disks: {e!s}",
        }


async def _handle_create_disk(disk_name: str | None = None, disk_size_gb: int | None = None) -> dict[str, Any]:
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
        result = await create_disk_tool(
            disk_path=disk_name, size_mb=int(disk_size_gb) * 1024, disk_format="VDI", variant="Standard"
        )
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "create_disk",
            "disk_name": disk_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "create_disk",
            "disk_name": disk_name,
            "error": f"Failed to create disk: {e!s}",
        }


async def _handle_attach_disk(vm_name: str | None = None, disk_path: str | None = None) -> dict[str, Any]:
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
        result = await attach_disk_tool(
            vm_name=vm_name,
            controller_name="SATA Controller",
            port=0,
            device=0,
            disk_type="hdd",
            medium=disk_path,
            disk_format="normal",
        )
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "attach_disk",
            "vm_name": vm_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "attach_disk",
            "vm_name": vm_name,
            "error": f"Failed to attach disk: {e!s}",
        }
