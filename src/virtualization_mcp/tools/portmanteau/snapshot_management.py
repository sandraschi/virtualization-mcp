"""
Snapshot Management Portmanteau Tool

Consolidates all snapshot-related operations into a single tool with action-based interface.
Replaces 4 individual snapshot tools with one comprehensive tool.
"""

import logging
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

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
        action: Annotated[
            Literal["list", "create", "restore", "delete"], Field(description="Snapshot operation to perform.")
        ],
        vm_name: Annotated[str, Field(description="Virtual machine name (all actions).")],
        snapshot_name: Annotated[str | None, Field(description="Snapshot name (create, restore, delete).")] = None,
        description: Annotated[str | None, Field(description="Optional description (create only).")] = None,
        limit: Annotated[int, Field(description="Max items for list.")] = 100,
        offset: Annotated[int, Field(description="Offset for list pagination.")] = 0,
    ) -> dict[str, Any]:
        """Comprehensive snapshot management portmanteau tool.

        Consolidates all VM snapshot operations into a single interface. All actions
        require `vm_name`; create/restore/delete also require `snapshot_name`.

        ## Return Format

        Dict with `success` (bool), human-readable `message`, the `action` performed,
        `vm_name`, `snapshot_name`, and operation data. Failures carry a
        human-readable `error`.

        ## Examples

        ```python
        await snapshot_management(action="list", vm_name="MyVM")
        await snapshot_management(action="create", vm_name="MyVM", snapshot_name="BeforeUpdate", description="Before system update")
        await snapshot_management(action="restore", vm_name="MyVM", snapshot_name="BeforeUpdate")
        await snapshot_management(action="delete", vm_name="MyVM", snapshot_name="BeforeUpdate")
        ```
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
                return await _handle_list_snapshots(vm_name=vm_name, limit=limit, offset=offset)

            elif action == "create":
                return await _handle_create_snapshot(
                    vm_name=vm_name, snapshot_name=snapshot_name, description=description
                )

            elif action == "restore":
                return await _handle_restore_snapshot(vm_name=vm_name, snapshot_name=snapshot_name)

            elif action == "delete":
                return await _handle_delete_snapshot(vm_name=vm_name, snapshot_name=snapshot_name)

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
                "error": f"Failed to execute action '{action}': {e!s}",
                "action": action,
                "vm_name": vm_name,
                "available_actions": SNAPSHOT_ACTIONS,
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


async def _handle_list_snapshots(vm_name: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """Handle list snapshots action."""
    try:
        result = await list_snapshots(vm_name=vm_name)
        snapshots = result.get("snapshots", []) if isinstance(result, dict) else []
        page = _paginate(snapshots if isinstance(snapshots, list) else [], limit, offset)
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
            "action": "list",
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
            "action": "list",
            "vm_name": vm_name,
            "error": f"Failed to list snapshots: {e!s}",
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
        result = await create_snapshot(vm_name=vm_name, snapshot_name=snapshot_name, description=description)
        return {
            "success": isinstance(result, dict) and result.get("status") == "success",
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
            "error": f"Failed to create snapshot: {e!s}",
        }


async def _handle_restore_snapshot(vm_name: str, snapshot_name: str | None = None) -> dict[str, Any]:
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
            "success": isinstance(result, dict) and result.get("status") == "success",
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
            "error": f"Failed to restore snapshot: {e!s}",
        }


async def _handle_delete_snapshot(vm_name: str, snapshot_name: str | None = None) -> dict[str, Any]:
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
            "success": isinstance(result, dict) and result.get("status") == "success",
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
            "error": f"Failed to delete snapshot: {e!s}",
        }
