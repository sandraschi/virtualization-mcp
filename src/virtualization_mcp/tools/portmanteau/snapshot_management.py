"""
Snapshot Management Portmanteau Tool

Consolidates all snapshot-related operations into a single tool with action-based interface.
Replaces 4 individual snapshot tools with one comprehensive tool.
"""

import logging
from typing import Any

from fastmcp import FastMCP

# Import existing snapshot tools
from virtualization_mcp.tools.snapshot.snapshot_tools import (
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)

logger = logging.getLogger(__name__)

# Define available actions
SNAPSHOT_ACTIONS = {
    "list": "List all snapshots for a VM",
    "create": "Create a snapshot of a VM",
    "restore": "Restore a VM to a snapshot",
    "delete": "Delete a snapshot from a VM",
}


def register_snapshot_management_tool(mcp: FastMCP) -> None:
    """Register the snapshot management portmanteau tool."""

    @mcp.tool()
    async def snapshot_management(
        action: str,
        vm_name: str,
        snapshot_name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Manage VM snapshots with various actions.

        Args:
            action: The operation to perform. Available actions:
                - list: List all snapshots for a VM
                - create: Create a snapshot (requires snapshot_name)
                - restore: Restore to a snapshot (requires snapshot_name)
                - delete: Delete a snapshot (requires snapshot_name)

            vm_name: Name of the virtual machine (required for all actions)
            snapshot_name: Name of the snapshot (required for create, restore, delete)
            description: Description for the snapshot (optional for create)

        Returns:
            Dict containing the result of the operation

        Examples:
            # List all snapshots
            result = await snapshot_management(
                action="list",
                vm_name="MyVM"
            )

            # Create a snapshot
            result = await snapshot_management(
                action="create",
                vm_name="MyVM",
                snapshot_name="BeforeUpdate",
                description="Snapshot before system update"
            )

            # Restore to a snapshot
            result = await snapshot_management(
                action="restore",
                vm_name="MyVM",
                snapshot_name="BeforeUpdate"
            )

            # Delete a snapshot
            result = await snapshot_management(
                action="delete",
                vm_name="MyVM",
                snapshot_name="OldSnapshot"
            )
        """
        try:
            # Validate action
            if action not in SNAPSHOT_ACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Available actions: {list(SNAPSHOT_ACTIONS.keys())}",
                    "available_actions": SNAPSHOT_ACTIONS,
                }

            # Validate vm_name (required for all actions)
            if not vm_name:
                return {
                    "success": False,
                    "error": "vm_name is required for all snapshot management actions",
                    "available_actions": SNAPSHOT_ACTIONS,
                }

            logger.info(f"Executing snapshot management action: {action} for VM: {vm_name}")

            # Route to appropriate function based on action
            if action == "list":
                return await _handle_list_snapshots(vm_name=vm_name)

            elif action == "create":
                return await _handle_create_snapshot(
                    vm_name=vm_name, snapshot_name=snapshot_name, description=description
                )

            elif action == "restore":
                return await _handle_restore_snapshot(
                    vm_name=vm_name, snapshot_name=snapshot_name
                )

            elif action == "delete":
                return await _handle_delete_snapshot(
                    vm_name=vm_name, snapshot_name=snapshot_name
                )

            else:
                return {
                    "success": False,
                    "error": f"Action '{action}' not implemented",
                    "available_actions": SNAPSHOT_ACTIONS,
                }

        except Exception as e:
            logger.error(
                f"Error in snapshot management action '{action}' for VM '{vm_name}': {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "error": f"Failed to execute action '{action}': {str(e)}",
                "action": action,
                "vm_name": vm_name,
                "available_actions": SNAPSHOT_ACTIONS,
            }


async def _handle_list_snapshots(vm_name: str) -> dict[str, Any]:
    """Handle list snapshots action."""
    try:
        result = await list_snapshots(vm_name=vm_name)
        return {
            "success": True,
            "action": "list",
            "vm_name": vm_name,
            "data": result,
            "count": len(result) if isinstance(result, list) else 0,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "list",
            "vm_name": vm_name,
            "error": f"Failed to list snapshots: {str(e)}",
        }


async def _handle_create_snapshot(
    vm_name: str, snapshot_name: str | None = None, description: str | None = None
) -> dict[str, Any]:
    """Handle create snapshot action."""
    if not snapshot_name:
        return {
            "success": False,
            "action": "create",
            "vm_name": vm_name,
            "error": "snapshot_name is required for create action",
        }

    try:
        result = await create_snapshot(
            vm_name=vm_name, snapshot_name=snapshot_name, description=description
        )
        return {
            "success": True,
            "action": "create",
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "create",
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "error": f"Failed to create snapshot: {str(e)}",
        }


async def _handle_restore_snapshot(
    vm_name: str, snapshot_name: str | None = None
) -> dict[str, Any]:
    """Handle restore snapshot action."""
    if not snapshot_name:
        return {
            "success": False,
            "action": "restore",
            "vm_name": vm_name,
            "error": "snapshot_name is required for restore action",
        }

    try:
        result = await restore_snapshot(vm_name=vm_name, snapshot_name=snapshot_name)
        return {
            "success": True,
            "action": "restore",
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "restore",
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "error": f"Failed to restore snapshot: {str(e)}",
        }


async def _handle_delete_snapshot(
    vm_name: str, snapshot_name: str | None = None
) -> dict[str, Any]:
    """Handle delete snapshot action."""
    if not snapshot_name:
        return {
            "success": False,
            "action": "delete",
            "vm_name": vm_name,
            "error": "snapshot_name is required for delete action",
        }

    try:
        result = await delete_snapshot(vm_name=vm_name, snapshot_name=snapshot_name)
        return {
            "success": True,
            "action": "delete",
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "delete",
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "error": f"Failed to delete snapshot: {str(e)}",
        }
