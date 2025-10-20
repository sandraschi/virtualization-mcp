"""
VM Snapshot Management Module

This module provides functionality for managing VM snapshots.
"""

import logging
from typing import Any

from ...vbox.compat_adapter import VBoxManagerError

logger = logging.getLogger(__name__)


class VMSnapshotMixin:
    """Mixin class providing VM snapshot management methods."""

    def __init__(self, vm_service):
        """Initialize with a reference to the parent VMService."""
        self.vm_service = vm_service
        self.vbox_manager = vm_service.vbox_manager
        self.vm_operations = vm_service.vm_operations

    def create_snapshot(
        self, vm_name: str, snapshot_name: str, description: str = ""
    ) -> dict[str, Any]:
        """
        Create a snapshot of a virtual machine.

        This function creates a snapshot of the specified VM, capturing its current state,
        including memory, settings, and disk state. Snapshots are useful for creating
        restore points before making significant changes to a VM.

        Args:
            vm_name: Name of the VM to snapshot
            snapshot_name: Name for the new snapshot
            description: Optional description for the snapshot

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "snapshot_name": str,  # Name of the created snapshot
                "description": str,  # Description of the snapshot
                "timestamp": str,  # When the snapshot was taken
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> create_snapshot("my-vm", "before-update", "Pre-update state")
            {
                "status": "success",
                "vm_name": "my-vm",
                "snapshot_name": "before-update",
                "description": "Pre-update state",
                "timestamp": "2023-07-15T14:30:00Z",
                "message": "✓ Snapshot 'before-update' created for VM 'my-vm'",
                "troubleshooting": [
                    "Use list_snapshots('my-vm') to view all snapshots",
                    "Restore this snapshot with restore_snapshot('my-vm', 'before-update')"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Create the snapshot using VMOperations
            result = self.vm_operations.create_snapshot(
                vm_name=vm_name, snapshot_name=snapshot_name, description=description
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error creating snapshot")
                raise VBoxManagerError(error_msg)

            # Prepare response
            snapshot_info = result.get("snapshot_info", {})
            response = {
                "status": "success",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "description": description,
                "timestamp": snapshot_info.get("created", ""),
                "message": f"✓ Snapshot '{snapshot_name}' created for VM '{vm_name}'",
                "troubleshooting": [
                    f"Use list_snapshots('{vm_name}') to view all snapshots",
                    f"Restore this snapshot with restore_snapshot('{vm_name}', '{snapshot_name}')",
                    "Regularly delete old snapshots to save disk space",
                ],
            }

            # Add any warnings from the operation
            if "warnings" in result:
                response["warnings"] = result["warnings"]

            return response

        except VBoxManagerError as e:
            logger.error(f"Failed to create snapshot for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "error": str(e),
                "message": f"Failed to create snapshot for VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Ensure the VM is not in a transitional state",
                    "Check if there's enough disk space for the snapshot",
                    "Verify VirtualBox has sufficient permissions to create snapshots",
                ],
            }

    def restore_snapshot(
        self, vm_name: str, snapshot_name: str, start_vm: bool = False
    ) -> dict[str, Any]:
        """
        Restore a virtual machine to a previous snapshot.

        This function restores the specified VM to the state it was in when the
        snapshot was taken. All changes made after the snapshot was taken will be lost.

        Args:
            vm_name: Name of the VM to restore
            snapshot_name: Name of the snapshot to restore to
            start_vm: If True, starts the VM after restoration (default: False)

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "snapshot_name": str,  # Name of the restored snapshot
                "started": bool,  # Whether the VM was started after restoration
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> restore_snapshot("my-vm", "clean-install")
            {
                "status": "success",
                "vm_name": "my-vm",
                "snapshot_name": "clean-install",
                "started": False,
                "message": "✓ VM 'my-vm' restored to snapshot 'clean-install'",
                "troubleshooting": [
                    "The VM is now in a powered-off state",
                    "Start the VM with start_vm('my-vm')",
                    "Check the VM's state with get_vm_info('my-vm')"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Get current VM state
            vm_info = self.vbox_manager.get_vm_info(vm_name)
            vm_info.get("VMState", "").lower()

            # Restore the snapshot using VMOperations
            result = self.vm_operations.restore_snapshot(
                vm_name=vm_name, snapshot_name=snapshot_name
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error restoring snapshot")
                raise VBoxManagerError(error_msg)

            # Start the VM if requested
            started = False
            if start_vm:
                start_result = self.vm_operations.start_vm(name=vm_name, headless=True)
                started = start_result.get("success", False)

                if not started:
                    logger.warning(f"Failed to start VM '{vm_name}' after snapshot restoration")

            # Prepare response
            response = {
                "status": "success",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "started": started,
                "message": (
                    f"✓ VM '{vm_name}' restored to snapshot '{snapshot_name}'"
                    + (" and started" if started else "")
                ),
                "troubleshooting": [
                    f"The VM is now in a {started and 'running' or 'powered-off'} state",
                    "Check the VM's state with list_vms()" if not started else "",
                ],
            }

            # Add any warnings from the operation
            if "warnings" in result:
                response["warnings"] = result["warnings"]

            return response

        except VBoxManagerError as e:
            logger.error(f"Failed to restore snapshot for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "started": False,
                "error": str(e),
                "message": f"Failed to restore VM '{vm_name}' to snapshot '{snapshot_name}': {e}",
                "troubleshooting": [
                    "Verify the VM and snapshot exist",
                    "Check if the VM is in a state that allows restoration",
                    "Ensure there's enough disk space for the operation",
                ],
            }

    def delete_snapshot(self, vm_name: str, snapshot_name: str) -> dict[str, Any]:
        """
        Delete a snapshot from a virtual machine.

        This function permanently removes the specified snapshot from the VM's
        snapshot tree. The state of the VM is not affected by this operation.

        Args:
            vm_name: Name of the VM that owns the snapshot
            snapshot_name: Name of the snapshot to delete

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "snapshot_name": str,  # Name of the deleted snapshot
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> delete_snapshot("my-vm", "old-backup")
            {
                "status": "success",
                "vm_name": "my-vm",
                "snapshot_name": "old-backup",
                "message": "✓ Snapshot 'old-backup' deleted from VM 'my-vm'",
                "troubleshooting": [
                    "The snapshot has been permanently removed",
                    "Use list_snapshots('my-vm') to verify the snapshot was removed"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Delete the snapshot using VMOperations
            result = self.vm_operations.delete_snapshot(
                vm_name=vm_name, snapshot_name=snapshot_name
            )

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error deleting snapshot")
                raise VBoxManagerError(error_msg)

            # Prepare response
            response = {
                "status": "success",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "message": f"✓ Snapshot '{snapshot_name}' deleted from VM '{vm_name}'",
                "troubleshooting": [
                    "The snapshot has been permanently removed",
                    f"Use list_snapshots('{vm_name}') to verify the snapshot was removed",
                ],
            }

            # Add any warnings from the operation
            if "warnings" in result:
                response["warnings"] = result["warnings"]

            return response

        except VBoxManagerError as e:
            logger.error(f"Failed to delete snapshot for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "snapshot_name": snapshot_name,
                "error": str(e),
                "message": f"Failed to delete snapshot '{snapshot_name}' from VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify both the VM and snapshot exist",
                    "Check if the snapshot is currently in use",
                    "Ensure you have sufficient permissions to delete snapshots",
                ],
            }

    def list_snapshots(self, vm_name: str) -> dict[str, Any]:
        """
        List all snapshots for a virtual machine.

        This function retrieves information about all snapshots associated with
        the specified VM, including the snapshot tree structure.

        Args:
            vm_name: Name of the VM to list snapshots for

        Returns:
            Dict[str, Any]: {
                "status": "success"|"error",
                "vm_name": str,  # Name of the VM
                "snapshot_count": int,  # Total number of snapshots
                "current_snapshot": Optional[Dict],  # Current snapshot details if any
                "snapshots": List[Dict],  # List of snapshot details
                "message": str,  # Human-readable status message
                "error": Optional[str],  # Error message if status is "error"
                "troubleshooting": List[str]  # Help for common issues
            }

        Example:
            >>> list_snapshots("my-vm")
            {
                "status": "success",
                "vm_name": "my-vm",
                "snapshot_count": 3,
                "current_snapshot": {
                    "name": "after-updates",
                    "description": "After applying all updates",
                    "created": "2023-07-10T14:30:00Z",
                    "online": true
                },
                "snapshots": [
                    {
                        "name": "clean-install",
                        "description": "Fresh OS installation",
                        "created": "2023-06-15T10:00:00Z",
                        "online": false,
                        "children": [
                            {
                                "name": "after-updates",
                                "description": "After applying all updates",
                                "created": "2023-07-10T14:30:00Z",
                                "online": true,
                                "children": []
                            }
                        ]
                    }
                ],
                "message": "Found 3 snapshots for VM 'my-vm'",
                "troubleshooting": [
                    "Use create_snapshot() to create a new snapshot",
                    "Use restore_snapshot() to restore to a previous state"
                ]
            }
        """
        try:
            # Check if VM exists
            if not self.vbox_manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' does not exist")

            # Get snapshots using VMOperations
            result = self.vm_operations.list_snapshots(vm_name=vm_name)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error listing snapshots")
                raise VBoxManagerError(error_msg)

            snapshots = result.get("snapshots", [])
            current_snapshot = result.get("current_snapshot")

            # Prepare response
            response = {
                "status": "success",
                "vm_name": vm_name,
                "snapshot_count": len(snapshots),
                "current_snapshot": current_snapshot,
                "snapshots": snapshots,
                "message": f"Found {len(snapshots)} snapshots for VM '{vm_name}'",
                "troubleshooting": [
                    f"Use create_snapshot('{vm_name}', 'name') to create a new snapshot",
                    f"Use restore_snapshot('{vm_name}', 'name') to restore to a previous state",
                ],
            }

            # Add any warnings from the operation
            if "warnings" in result:
                response["warnings"] = result["warnings"]

            return response

        except VBoxManagerError as e:
            logger.error(f"Failed to list snapshots for VM {vm_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "vm_name": vm_name,
                "snapshot_count": 0,
                "snapshots": [],
                "error": str(e),
                "message": f"Failed to list snapshots for VM '{vm_name}': {e}",
                "troubleshooting": [
                    "Verify the VM exists and is accessible",
                    "Check VirtualBox logs for more detailed error information",
                ],
            }
